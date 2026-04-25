"""市场数据获取模块 - 获取市场指数等辅助特征数据

多变量输入可显著提升预测精度：
- 沪深300指数：市场整体趋势
- 中证500指数：中小盘风格
- 10年期国债收益率：无风险利率/估值锚
"""

import time
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_HISTORY_DAYS = 365


class MarketDataFetcher:
    """市场数据获取器，获取指数和利率等辅助数据"""

    MAX_RETRIES = 3
    RETRY_DELAY = 5

    def fetch_index_history(
        self,
        symbol: str = "000300",
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取指数历史数据

        Args:
            symbol: 指数代码，默认沪深300
                "000300" - 沪深300
                "000905" - 中证500
                "000001" - 上证指数
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            DataFrame，包含 date, close, volume 列
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=DEFAULT_HISTORY_DAYS)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        logger.info(f"获取指数 {symbol} 数据: {start_date} ~ {end_date}")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                import akshare as ak

                df = ak.index_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                )

                if df is None or df.empty:
                    logger.warning(f"指数 {symbol} 暂无数据")
                    return pd.DataFrame()

                # 统一列名
                col_map = {}
                for col in df.columns:
                    col_str = str(col)
                    if "日期" in col_str:
                        col_map[col] = "date"
                    elif "收盘" in col_str:
                        col_map[col] = "close"
                    elif "成交量" in col_str:
                        col_map[col] = "volume"

                df = df.rename(columns=col_map)

                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date").reset_index(drop=True)

                logger.info(f"指数 {symbol} 获取到 {len(df)} 条数据")
                return df

            except Exception as e:
                logger.error(f"获取指数 {symbol} 数据失败 (第{attempt}次): {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)

        return pd.DataFrame()

    def fetch_bond_yield(
        self,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取10年期国债收益率

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame，包含 date, yield 列
        """
        logger.info("获取10年期国债收益率数据")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                import akshare as ak

                # 尝试获取中国国债收益率曲线
                df = ak.bond_china_yield(start_date="20230101", end_date=datetime.now().strftime("%Y%m%d"))

                if df is not None and not df.empty:
                    # 筛选10年期
                    for col in df.columns:
                        if "10" in str(col) and "年" in str(col):
                            result = pd.DataFrame({
                                "date": pd.to_datetime(df.iloc[:, 0]),
                                "yield": df[col].astype(float),
                            })
                            result = result.sort_values("date").reset_index(drop=True)
                            logger.info(f"获取到 {len(result)} 条国债收益率数据")
                            return result

                logger.warning("国债收益率数据获取失败，返回空数据")
                return pd.DataFrame()

            except Exception as e:
                logger.error(f"获取国债收益率失败 (第{attempt}次): {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)

        return pd.DataFrame()

    def fetch_multi_features(
        self,
        fund_nav_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        获取多变量特征并合并到基金净值数据中

        Args:
            fund_nav_df: 基金净值 DataFrame（需包含 date, nav 列）

        Returns:
            合并后的 DataFrame，新增列：
            - hs300_close: 沪深300收盘价
            - zz500_close: 中证500收盘价
            - hs300_return: 沪深300日收益率
            - zz500_return: 中证500日收益率
            - bond_yield_10y: 10年期国债收益率（可能缺失）
        """
        if fund_nav_df.empty:
            return fund_nav_df

        result_df = fund_nav_df.copy()

        # 确定日期范围
        dates = pd.to_datetime(result_df["date"])
        start_date = dates.min().strftime("%Y%m%d")
        end_date = dates.max().strftime("%Y%m%d")

        # 获取沪深300
        hs300 = self.fetch_index_history("000300", start_date, end_date)
        if not hs300.empty and "close" in hs300.columns:
            hs300_feat = hs300[["date", "close"]].rename(columns={"close": "hs300_close"})
            hs300_feat["hs300_return"] = hs300_feat["hs300_close"].pct_change()
            result_df["date"] = pd.to_datetime(result_df["date"])
            result_df = result_df.merge(hs300_feat, on="date", how="left")
            result_df["hs300_close"] = result_df["hs300_close"].ffill().bfill()
            result_df["hs300_return"] = result_df["hs300_return"].ffill().fillna(0)

        # 获取中证500
        zz500 = self.fetch_index_history("000905", start_date, end_date)
        if not zz500.empty and "close" in zz500.columns:
            zz500_feat = zz500[["date", "close"]].rename(columns={"close": "zz500_close"})
            zz500_feat["zz500_return"] = zz500_feat["zz500_close"].pct_change()
            if "date" not in result_df.columns or not pd.api.types.is_datetime64_any_dtype(result_df["date"]):
                result_df["date"] = pd.to_datetime(result_df["date"])
            result_df = result_df.merge(zz500_feat, on="date", how="left")
            result_df["zz500_close"] = result_df["zz500_close"].ffill().bfill()
            result_df["zz500_return"] = result_df["zz500_return"].ffill().fillna(0)

        # 获取国债收益率
        bond = self.fetch_bond_yield(start_date, end_date)
        if not bond.empty and "yield" in bond.columns:
            bond_feat = bond[["date", "yield"]].rename(columns={"yield": "bond_yield_10y"})
            if not pd.api.types.is_datetime64_any_dtype(result_df["date"]):
                result_df["date"] = pd.to_datetime(result_df["date"])
            result_df = result_df.merge(bond_feat, on="date", how="left")
            result_df["bond_yield_10y"] = result_df["bond_yield_10y"].ffill().bfill()

        # 恢复日期格式
        result_df["date"] = result_df["date"].dt.strftime("%Y-%m-%d")

        feature_cols = [c for c in result_df.columns if c not in fund_nav_df.columns]
        logger.info(f"多变量特征合并完成，新增特征: {feature_cols}")
        return result_df
