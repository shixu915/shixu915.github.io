"""数据清洗模块 - 处理缺失值、异常值、格式统一"""

import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 最少有效数据条数
MIN_DATA_ROWS = 30


class FundDataCleaner:
    """基金数据清洗器"""

    def clean(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        执行完整清洗流程

        Args:
            raw_df: 原始数据 DataFrame

        Returns:
            清洗后的 DataFrame

        Raises:
            ValueError: 有效数据不足时
        """
        if raw_df is None or raw_df.empty:
            raise ValueError("输入数据为空，无法清洗")

        df = raw_df.copy()

        # 1. 按日期排序
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

        # 2. 填充缺失值
        df = self.fill_missing_values(df)

        # 3. 检测异常值
        df = self.detect_outliers(df)

        # 4. 统一格式
        df = self.unify_formats(df)

        # 5. 校验数据量
        valid_count = len(df)
        if valid_count < MIN_DATA_ROWS:
            raise ValueError(
                f"有效数据不足 {MIN_DATA_ROWS} 条（实际 {valid_count} 条），无法进行分析"
            )

        logger.info(f"数据清洗完成，有效数据 {valid_count} 条")
        return df

    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        前值填充缺失值

        Args:
            df: 输入 DataFrame

        Returns:
            填充后的 DataFrame
        """
        if "nav" in df.columns:
            missing_count = df["nav"].isna().sum()
            if missing_count > 0:
                logger.info(f"检测到 {missing_count} 个缺失净值，使用前值填充")
                df["nav"] = df["nav"].ffill()

        if "acc_nav" in df.columns:
            df["acc_nav"] = df["acc_nav"].ffill()

        return df

    def detect_outliers(self, df: pd.DataFrame, threshold: float = 0.2) -> pd.DataFrame:
        """
        检测日涨跌幅超过阈值的异常值

        Args:
            df: 输入 DataFrame
            threshold: 涨跌幅阈值，默认 20%

        Returns:
            添加了 daily_return 和 is_outlier 列的 DataFrame
        """
        df["daily_return"] = np.nan
        df["is_outlier"] = False

        if "nav" in df.columns and len(df) > 1:
            df["daily_return"] = df["nav"].pct_change()
            df["is_outlier"] = df["daily_return"].abs() > threshold

            outlier_count = df["is_outlier"].sum()
            if outlier_count > 0:
                logger.warning(
                    f"检测到 {outlier_count} 个异常值（日涨跌幅超过 {threshold:.0%}）"
                )

        return df

    def unify_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        统一日期格式和数值精度

        Args:
            df: 输入 DataFrame

        Returns:
            格式统一后的 DataFrame
        """
        # 日期格式统一为 YYYY-MM-DD
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        # 净值保留 4 位小数
        if "nav" in df.columns:
            df["nav"] = df["nav"].round(4)

        if "acc_nav" in df.columns:
            df["acc_nav"] = df["acc_nav"].round(4)

        # 日涨跌幅保留 2 位小数
        if "daily_return" in df.columns:
            df["daily_return"] = df["daily_return"].round(4)

        return df
