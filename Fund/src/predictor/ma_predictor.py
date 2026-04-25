"""保守型预测策略 - 基于移动平均线（MA）"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

# 历史数据最低要求
MIN_HISTORY_DAYS = 60
# 预测天数
DEFAULT_PREDICT_DAYS = 30
# 移动平均线周期
MA_PERIODS = [5, 10, 20, 60]
# 移动平均线权重（近期权重更高）
MA_WEIGHTS = [0.4, 0.3, 0.2, 0.1]


class MAPredictor:
    """保守型预测器 - 移动平均线加权外推"""

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行 MA 预测

        Args:
            df: 清洗后的历史数据，需包含 date 和 nav 列
            days: 预测天数，默认 30

        Returns:
            PredictionResult 预测结果

        Raises:
            ValueError: 历史数据不足时
        """
        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        # 计算各周期移动平均线
        ma_values = {}
        for period in MA_PERIODS:
            if len(nav_values) >= period:
                ma_values[period] = np.mean(nav_values[-period:])
            else:
                ma_values[period] = np.mean(nav_values)

        # 加权外推预测
        last_nav = nav_values[-1]
        predictions = []
        current_value = last_nav

        # 计算历史波动率
        returns = np.diff(nav_values) / nav_values[:-1]
        volatility = np.std(returns)

        for i in range(1, days + 1):
            # 加权移动平均趋势
            weighted_ma = sum(
                w * ma_values[p] for w, p in zip(MA_WEIGHTS, MA_PERIODS) if p in ma_values
            )

            # 趋势外推：基于 MA 均值偏离度和波动率
            trend = (weighted_ma - last_nav) / last_nav
            # 衰减因子：越远的天预测越保守
            decay = np.exp(-0.05 * i)
            predicted = current_value * (1 + trend * decay)

            predictions.append(predicted)
            current_value = predicted

        # 计算置信区间
        upper_bound = []
        lower_bound = []
        for i, pred in enumerate(predictions):
            # 置信区间 = 预测值 ± 2 × 历史波动率 × √天数
            margin = 2 * volatility * pred * np.sqrt(i + 1)
            upper_bound.append(pred + margin)
            lower_bound.append(max(pred - margin, 0.0001))

        # 生成预测日期（跳过周末）
        pred_dates = self._generate_future_dates(dates[-1], days)

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in predictions],
            upper_bound=[round(v, 4) for v in upper_bound],
            lower_bound=[round(v, 4) for v in lower_bound],
            model_type="MA",
        )

        logger.info(f"MA 预测完成，预测 {days} 个交易日")
        return result

    def backtest(self, df: pd.DataFrame) -> BacktestResult:
        """
        执行历史回测

        用前 80% 数据预测后 20%，与实际值对比

        Args:
            df: 清洗后的历史数据

        Returns:
            BacktestResult 回测结果
        """
        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日，无法回测")

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        # 前 80% 作为训练，后 20% 作为验证
        split_idx = int(len(nav_values) * 0.8)
        train_data = nav_values[:split_idx]
        test_data = nav_values[split_idx:]
        test_dates = dates[split_idx:]

        # 用训练数据预测
        train_df = pd.DataFrame({
            "date": dates[:split_idx],
            "nav": train_data,
        })

        predict_days = len(test_data)
        try:
            pred_result = self.predict(train_df, days=predict_days)
            predicted_values = pred_result.values
        except Exception as e:
            logger.error(f"回测预测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="MA")

        # 计算 MAPE
        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="MA",
        )

        logger.info(f"MA 回测完成，MAPE: {mape:.2f}%")
        return result

    def _generate_future_dates(self, last_date_str: str, days: int) -> list:
        """
        生成未来交易日日期（跳过周末）

        Args:
            last_date_str: 最后一个历史日期
            days: 需要生成的天数

        Returns:
            日期字符串列表
        """
        try:
            last_date = pd.to_datetime(last_date_str)
        except Exception:
            last_date = datetime.now()

        future_dates = []
        current = last_date + timedelta(days=1)

        while len(future_dates) < days:
            # 跳过周末
            if current.weekday() < 5:
                future_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return future_dates
