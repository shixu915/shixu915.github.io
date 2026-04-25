"""ARIMA 预测模型 - 经典统计时间序列模型

ARIMA 优势：
- 理论基础扎实，可解释性强
- SARIMA 可建模季节性（年度周期）
- 对短序列（60-200 个数据点）表现稳定，不易过拟合
- statsmodels 库原生支持，无需深度学习框架
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

MIN_HISTORY_DAYS = 60
DEFAULT_PREDICT_DAYS = 30


class ARIMAPredictor:
    """ARIMA 预测器 - 基于 statsmodels 的 SARIMA 模型"""

    def __init__(self):
        self._statsmodels_available = self._check_statsmodels()

    def _check_statsmodels(self) -> bool:
        """检查 statsmodels 是否可用"""
        try:
            import statsmodels
            return True
        except ImportError:
            logger.warning("statsmodels 未安装，请执行: pip install statsmodels")
            return False

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行 ARIMA 预测

        使用自动阶数选择（AIC 准则），并尝试 SARIMA（带季节性）

        Args:
            df: 清洗后的历史数据
            days: 预测天数

        Returns:
            PredictionResult
        """
        if not self._statsmodels_available:
            raise RuntimeError("statsmodels 未安装，请执行: pip install statsmodels")

        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        # 尝试 SARIMA（带年度季节性），失败则回退到 ARIMA
        try:
            pred_values, conf_int = self._fit_sarima(nav_values, days)
        except Exception as e:
            logger.warning(f"SARIMA 拟合失败: {e}，尝试 ARIMA")
            try:
                pred_values, conf_int = self._fit_arima(nav_values, days)
            except Exception as e2:
                logger.error(f"ARIMA 拟合也失败: {e2}")
                raise RuntimeError(f"ARIMA/SARIMA 拟合失败: {e2}")

        # 生成预测日期
        pred_dates = self._generate_future_dates(dates[-1], days)

        # 确保预测值数量与日期一致
        actual_days = min(len(pred_values), len(pred_dates))
        pred_values = pred_values[:actual_days]
        conf_int = conf_int[:actual_days]
        pred_dates = pred_dates[:actual_days]

        upper_bound = [ci[1] for ci in conf_int]
        lower_bound = [max(ci[0], 0.0001) for ci in conf_int]

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in pred_values],
            upper_bound=[round(v, 4) for v in upper_bound],
            lower_bound=[round(v, 4) for v in lower_bound],
            model_type="ARIMA",
        )

        logger.info(f"ARIMA 预测完成，预测 {actual_days} 个交易日")
        return result

    def backtest(self, df: pd.DataFrame) -> BacktestResult:
        """
        执行历史回测

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
            logger.error(f"ARIMA 回测预测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="ARIMA")

        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="ARIMA",
        )

        logger.info(f"ARIMA 回测完成，MAPE: {mape:.2f}%")
        return result

    def _fit_sarima(self, data: np.ndarray, days: int):
        """
        拟合 SARIMA 模型（带年度季节性）

        季节周期设为 20（约一个月交易日数），避免年度 252 周期导致参数过多
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        # SARIMA(p,d,q)(P,D,Q,s)
        # s=20: 月度季节性（约 20 个交易日）
        # 使用保守的阶数，避免过拟合
        order = (1, 1, 1)
        seasonal_order = (1, 0, 1, 20)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = SARIMAX(
                data,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            fitted = model.fit(disp=False, maxiter=100)

        forecast = fitted.get_forecast(steps=days)
        pred_values = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=0.05)

        return list(pred_values), list(conf_int)

    def _fit_arima(self, data: np.ndarray, days: int):
        """
        拟合 ARIMA 模型（无季节性）

        使用自动阶数选择
        """
        from statsmodels.tsa.arima.model import ARIMA

        # 尝试多个阶数，选择 AIC 最小的
        best_aic = float("inf")
        best_order = (1, 1, 1)
        best_model = None

        # 搜索空间
        p_range = range(0, 4)
        d_range = range(0, 2)
        q_range = range(0, 4)

        for p in p_range:
            for d in d_range:
                for q in q_range:
                    if p == 0 and q == 0:
                        continue
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            model = ARIMA(data, order=(p, d, q))
                            fitted = model.fit()
                            if fitted.aic < best_aic:
                                best_aic = fitted.aic
                                best_order = (p, d, q)
                                best_model = fitted
                    except Exception:
                        continue

        if best_model is None:
            # 回退到默认阶数
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(data, order=(1, 1, 1))
                best_model = model.fit()

        logger.info(f"ARIMA 最优阶数: {best_order}, AIC: {best_aic:.2f}")

        forecast = best_model.get_forecast(steps=days)
        pred_values = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=0.05)

        return list(pred_values), list(conf_int)

    def _generate_future_dates(self, last_date_str: str, days: int) -> list:
        """生成未来交易日日期（跳过周末）"""
        try:
            last_date = pd.to_datetime(last_date_str)
        except Exception:
            last_date = datetime.now()

        future_dates = []
        current = last_date + timedelta(days=1)

        while len(future_dates) < days:
            if current.weekday() < 5:
                future_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return future_dates
