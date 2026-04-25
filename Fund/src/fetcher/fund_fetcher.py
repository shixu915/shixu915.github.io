"""数据获取模块 - 从 AkShare 获取基金历史数据"""

import re
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from src.utils.logger import setup_logger
from src.models.data_models import FundInfo

logger = setup_logger(__name__)

# 默认获取最近一年的数据
DEFAULT_HISTORY_DAYS = 365


class FundDataFetcher:
    """基金数据获取器，封装 AkShare API"""

    # 网络请求配置
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # 秒
    TIMEOUT = 30  # 秒

    def validate_fund_code(self, code: str) -> bool:
        """
        校验基金代码格式（6位数字）

        Args:
            code: 基金代码字符串

        Returns:
            是否为有效格式
        """
        return bool(re.match(r'^\d{6}$', str(code).strip()))

    def fetch_nav_history(
        self,
        fund_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取指定基金的历史净值数据

        Args:
            fund_code: 6位基金代码
            start_date: 开始日期 YYYY-MM-DD，默认为一年前
            end_date: 结束日期 YYYY-MM-DD，默认为今天

        Returns:
            DataFrame，包含 date, nav, acc_nav 列
        """
        if not self.validate_fund_code(fund_code):
            logger.warning(f"基金代码格式错误: {fund_code}")
            return pd.DataFrame()

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=DEFAULT_HISTORY_DAYS)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        logger.info(f"开始获取基金 {fund_code} 历史数据: {start_date} ~ {end_date}")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                import akshare as ak

                # 尝试获取开放式基金净值数据
                df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

                if df is None or df.empty:
                    # 尝试 ETF 基金数据
                    df = ak.fund_etf_hist_em(
                        symbol=fund_code,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq",
                    )

                if df is None or df.empty:
                    logger.warning(f"基金 {fund_code} 暂无历史数据")
                    return pd.DataFrame()

                # 统一列名
                df = self._normalize_columns(df, fund_code)

                # 按日期范围过滤
                df = self._filter_by_date(df, start_date, end_date)

                logger.info(f"基金 {fund_code} 获取到 {len(df)} 条历史数据")
                return df

            except Exception as e:
                logger.error(f"获取基金 {fund_code} 数据失败 (第{attempt}次): {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"基金 {fund_code} 数据获取最终失败，已重试 {self.MAX_RETRIES} 次")
                    return pd.DataFrame()

    def fetch_fund_info(self, fund_code: str) -> Optional[FundInfo]:
        """
        获取基金基本信息

        Args:
            fund_code: 6位基金代码

        Returns:
            FundInfo 对象，获取失败返回 None
        """
        if not self.validate_fund_code(fund_code):
            return None

        try:
            import akshare as ak

            info = FundInfo(code=fund_code)

            # 获取基金基本信息
            try:
                df = ak.fund_individual_basic_info_xq(symbol=fund_code)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        item = row.get("item", "")
                        value = row.get("value", "")
                        if "基金名称" in str(item) or "基金简称" in str(item):
                            info.name = str(value)
                        elif "基金类型" in str(item):
                            info.fund_type = str(value)
            except Exception:
                pass

            # 获取最新净值
            try:
                nav_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
                if nav_df is not None and not nav_df.empty:
                    last_row = nav_df.iloc[-1]
                    info.current_nav = float(last_row.iloc[1])
                    info.nav_date = str(last_row.iloc[0])
            except Exception:
                pass

            return info

        except Exception as e:
            logger.error(f"获取基金 {fund_code} 基本信息失败: {e}")
            return None

    def fetch_batch(
        self,
        fund_codes: list,
        start_date: str = None,
        end_date: str = None,
    ) -> dict:
        """
        批量获取多只基金数据

        Args:
            fund_codes: 基金代码列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: {基金代码: DataFrame}
        """
        results = {}
        for code in fund_codes:
            code = str(code).strip()
            if not self.validate_fund_code(code):
                logger.warning(f"基金代码格式错误，已跳过: {code}")
                continue

            df = self.fetch_nav_history(code, start_date, end_date)
            results[code] = df

        return results

    def _normalize_columns(self, df: pd.DataFrame, fund_code: str) -> pd.DataFrame:
        """统一 DataFrame 列名为标准格式"""
        # AkShare 开放式基金净值返回的列: 日期, 单位净值, 累计净值, 日涨跌幅
        # AkShare ETF 返回的列: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率

        col_map = {}
        for col in df.columns:
            col_str = str(col)
            if "日期" in col_str or col_str == "date":
                col_map[col] = "date"
            elif "单位净值" in col_str or "收盘" in col_str:
                col_map[col] = "nav"
            elif "累计净值" in col_str:
                col_map[col] = "acc_nav"

        df = df.rename(columns=col_map)

        # 如果没有 acc_nav 列，用 nav 填充
        if "acc_nav" not in df.columns and "nav" in df.columns:
            df["acc_nav"] = df["nav"]

        # 确保必要列存在
        required_cols = ["date", "nav"]
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"基金 {fund_code} 数据缺少必要列: {col}")
                return pd.DataFrame()

        return df

    def _filter_by_date(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """按日期范围过滤数据"""
        try:
            df["date"] = pd.to_datetime(df["date"])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df["date"] >= start) & (df["date"] <= end)]
            df = df.sort_values("date").reset_index(drop=True)
        except Exception as e:
            logger.warning(f"日期过滤失败: {e}")

        return df
