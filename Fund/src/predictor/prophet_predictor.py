"""Prophet 预测模型 - Facebook/Meta 开源时间序列预测

Prophet 优势：
- 自动捕捉趋势转折点（changepoint）
- 内置年度/周度季节性分解
- 对缺失值和异常值鲁棒
- 不确定性建模更合理（按分量分解置信区间）
- 参数少，不易过拟合，适合中小样本
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

MIN_HISTORY_DAYS = 60
DEFAULT_PREDICT_DAYS = 30


class ProphetPredictor:
    """Prophet 预测器 - 基于 Facebook Prophet"""

    def __init__(self):
        self._prophet_available = self._check_prophet()

    def _check_prophet(self) -> bool:
        """检查 Prophet 是否可用"""
        try:
            from prophet import Prophet
            return True
        except ImportError:
            try:
                from fbprophet import Prophet
                return True
            except ImportError:
                logger.warning("Prophet 未安装，请执行: pip install prophet")
                return False

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行 Prophet 预测

        Args:
            df: 清洗后的历史数据，需包含 date 和 nav 列
            days: 预测天数

        Returns:
            PredictionResult

        Raises:
            ValueError: 数据不足
            RuntimeError: Prophet 不可用或预测失败
        """
        if not self._prophet_available:
            raise RuntimeError("Prophet 未安装，请执行: pip install prophet")

        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        from prophet import Prophet

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        # 构建 Prophet 所需格式 (ds, y)
        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime(dates),
            "y": nav_values,
        })

        # 配置 Prophet 模型
        model = Prophet(
            changepoint_prior_scale=0.05,   # 趋势灵活性，基金数据不宜过大
            seasonality_prior_scale=10.0,   # 季节性强度
            seasonality_mode="multiplicative",  # 乘法季节性，适合金融数据
            yearly_seasonality=True,        # 年度季节性
            weekly_seasonality=False,       # 基金无周度季节性
            daily_seasonality=False,        # 无日度季节性
            interval_width=0.95,            # 95% 置信区间
        )

        # 添加中国法定节假日效应
        try:
            self._add_holidays(model)
        except Exception as e:
            logger.warning(f"添加节假日效应失败（不影响预测）: {e}")

        # 训练模型
        try:
            model.fit(prophet_df)
        except Exception as e:
            logger.error(f"Prophet 模型训练失败: {e}")
            raise RuntimeError(f"Prophet 模型训练失败: {e}")

        # 生成未来日期
        future = model.make_future_dataframe(periods=days, freq="B")  # B = 工作日

        # 预测
        forecast = model.predict(future)

        # 提取预测结果（仅取未来部分）
        pred_forecast = forecast.iloc[len(prophet_df):]

        # 过滤掉非工作日（Prophet 可能生成周末日期）
        pred_forecast = pred_forecast[pred_forecast["ds"].dt.weekday < 5]
        pred_forecast = pred_forecast.head(days)

        pred_dates = pred_forecast["ds"].dt.strftime("%Y-%m-%d").tolist()
        pred_values = pred_forecast["yhat"].tolist()
        upper_bound = pred_forecast["yhat_upper"].tolist()
        lower_bound = pred_forecast["yhat_lower"].tolist()

        # 确保下界不为负
        lower_bound = [max(v, 0.0001) for v in lower_bound]

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in pred_values],
            upper_bound=[round(v, 4) for v in upper_bound],
            lower_bound=[round(v, 4) for v in lower_bound],
            model_type="Prophet",
        )

        logger.info(f"Prophet 预测完成，预测 {len(pred_dates)} 个交易日")
        return result

    def backtest(self, df: pd.DataFrame) -> BacktestResult:
        """
        执行历史回测

        用前 80% 数据预测后 20%，与实际值对比

        Args:
            df: 清洗后的历史数据

        Returns:
            BacktestResult
        """
        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日，无法回测")

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        split_idx = int(len(nav_values) * 0.8)
        train_df = pd.DataFrame({
            "date": dates[:split_idx],
            "nav": nav_values[:split_idx],
        })

        test_data = nav_values[split_idx:]
        test_dates = dates[split_idx:]
        predict_days = len(test_data)

        try:
            pred_result = self.predict(train_df, days=predict_days)
            predicted_values = pred_result.values
        except Exception as e:
            logger.error(f"Prophet 回测预测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="Prophet")

        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="Prophet",
        )

        logger.info(f"Prophet 回测完成，MAPE: {mape:.2f}%")
        return result

    def _add_holidays(self, model):
        """添加中国主要法定节假日效应"""
        # Prophet 内置中国节假日支持
        model.add_country_holidays(country_name="China")
