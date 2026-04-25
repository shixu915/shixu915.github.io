"""集成预测方法 - 组合多个模型的预测结果

集成方法优势：
- 通常比单一模型更精确且更稳定
- 通过回测 MAPE 反向优化各模型权重
- 降低单一模型偏差风险
"""

import numpy as np
import pandas as pd

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult
from src.predictor.prophet_predictor import ProphetPredictor
from src.predictor.arima_predictor import ARIMAPredictor
from src.predictor.lstm_predictor import LSTMPredictor
from src.predictor.ma_predictor import MAPredictor

logger = setup_logger(__name__)

MIN_HISTORY_DAYS = 60
DEFAULT_PREDICT_DAYS = 30


class EnsemblePredictor:
    """集成预测器 - 加权组合多个模型"""

    # 可用模型及其默认权重
    MODEL_REGISTRY = {
        "Prophet": {"class": ProphetPredictor, "default_weight": 0.4},
        "ARIMA": {"class": ARIMAPredictor, "default_weight": 0.3},
        "LSTM": {"class": LSTMPredictor, "default_weight": 0.2},
        "MA": {"class": MAPredictor, "default_weight": 0.1},
    }

    def __init__(self):
        self._predictors = {}
        for name, config in self.MODEL_REGISTRY.items():
            try:
                self._predictors[name] = config["class"]()
            except Exception as e:
                logger.warning(f"模型 {name} 初始化失败: {e}")

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行集成预测

        策略：
        1. 使用所有可用模型分别预测
        2. 通过回测计算各模型权重（MAPE 越小权重越大）
        3. 加权平均得到最终预测
        4. 置信区间取各模型置信区间的加权平均

        Args:
            df: 清洗后的历史数据
            days: 预测天数

        Returns:
            PredictionResult
        """
        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        # 阶段1: 各模型分别预测
        predictions = {}
        for name, predictor in self._predictors.items():
            try:
                result = predictor.predict(df, days)
                predictions[name] = result
                logger.info(f"集成预测: {name} 模型预测成功")
            except Exception as e:
                logger.warning(f"集成预测: {name} 模型预测失败: {e}")

        if not predictions:
            raise RuntimeError("所有模型预测均失败，无法进行集成预测")

        # 阶段2: 计算各模型权重
        weights = self._compute_weights(df, predictions)

        # 阶段3: 加权平均
        ensemble_values = self._weighted_average_values(predictions, weights, days)
        ensemble_upper = self._weighted_average_bounds(predictions, weights, days, "upper_bound")
        ensemble_lower = self._weighted_average_bounds(predictions, weights, days, "lower_bound")

        # 阶段4: 使用第一个成功模型的日期
        first_pred = next(iter(predictions.values()))
        pred_dates = first_pred.dates[:days]

        # 确保数量一致
        actual_days = min(len(ensemble_values), len(pred_dates))
        ensemble_values = ensemble_values[:actual_days]
        ensemble_upper = ensemble_upper[:actual_days]
        ensemble_lower = [max(v, 0.0001) for v in ensemble_lower[:actual_days]]
        pred_dates = pred_dates[:actual_days]

        # 构建权重描述
        weight_desc = ", ".join(f"{k}:{v:.2f}" for k, v in weights.items() if k in predictions)

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in ensemble_values],
            upper_bound=[round(v, 4) for v in ensemble_upper],
            lower_bound=[round(v, 4) for v in ensemble_lower],
            model_type=f"Ensemble({weight_desc})",
        )

        logger.info(f"集成预测完成，使用 {len(predictions)} 个模型，预测 {actual_days} 个交易日")
        return result

    def backtest(self, df: pd.DataFrame) -> BacktestResult:
        """
        执行集成回测

        使用各模型回测的加权平均

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
            logger.error(f"集成回测预测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="Ensemble")

        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="Ensemble",
        )

        logger.info(f"集成回测完成，MAPE: {mape:.2f}%")
        return result

    def _compute_weights(self, df: pd.DataFrame, predictions: dict) -> dict:
        """
        通过回测计算各模型权重

        权重策略：MAPE 越小权重越大
        weight_i = (1/MAPE_i) / sum(1/MAPE_j)

        如果回测失败，使用默认权重
        """
        mapes = {}
        for name in predictions.keys():
            predictor = self._predictors.get(name)
            if predictor is None:
                continue
            try:
                bt = predictor.backtest(df)
                if bt.mape > 0 and bt.mape < float("inf"):
                    mapes[name] = bt.mape
                else:
                    mapes[name] = 100.0  # 回测异常，给高 MAPE
            except Exception:
                mapes[name] = 100.0

        # 基于逆 MAPE 计算权重
        if mapes:
            inv_mapes = {k: 1.0 / v for k, v in mapes.items()}
            total = sum(inv_mapes.values())
            if total > 0:
                weights = {k: v / total for k, v in inv_mapes.items()}
                logger.info(f"基于回测 MAPE 计算权重: {weights}")
                return weights

        # 回退到默认权重
        weights = {}
        total_default = sum(
            self.MODEL_REGISTRY[name]["default_weight"]
            for name in predictions.keys()
            if name in self.MODEL_REGISTRY
        )
        for name in predictions.keys():
            if name in self.MODEL_REGISTRY:
                weights[name] = self.MODEL_REGISTRY[name]["default_weight"] / total_default

        logger.info(f"使用默认权重: {weights}")
        return weights

    def _weighted_average_values(self, predictions: dict, weights: dict, days: int) -> list:
        """加权平均预测值"""
        result = np.zeros(days)
        total_weight = 0

        for name, pred in predictions.items():
            w = weights.get(name, 0)
            if w > 0 and len(pred.values) >= days:
                result += np.array(pred.values[:days]) * w
                total_weight += w

        if total_weight > 0:
            result /= total_weight

        return list(result)

    def _weighted_average_bounds(self, predictions: dict, weights: dict, days: int, bound_key: str) -> list:
        """加权平均置信区间边界"""
        result = np.zeros(days)
        total_weight = 0

        for name, pred in predictions.items():
            w = weights.get(name, 0)
            bound = getattr(pred, bound_key, None)
            if w > 0 and bound and len(bound) >= days:
                result += np.array(bound[:days]) * w
                total_weight += w

        if total_weight > 0:
            result /= total_weight

        return list(result)
