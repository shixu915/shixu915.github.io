"""预测引擎 - 统一调度所有预测模型

支持的模型类型：
- "Prophet": Facebook Prophet（推荐保守型，替代 MA）
- "ARIMA": 经典统计模型（补充模型）
- "LSTM": 深度学习模型（激进型）
- "MultiVar-LSTM": 多变量 LSTM（需市场特征数据）
- "Ensemble": 集成方法（加权组合多模型，推荐）
- "MA": 移动平均线（最基础，作为兜底）
"""

import pandas as pd

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult
from src.predictor.ma_predictor import MAPredictor
from src.predictor.lstm_predictor import LSTMPredictor
from src.predictor.prophet_predictor import ProphetPredictor
from src.predictor.arima_predictor import ARIMAPredictor
from src.predictor.ensemble_predictor import EnsemblePredictor
from src.predictor.multivar_lstm_predictor import MultiVarLSTMPredictor

logger = setup_logger(__name__)

DEFAULT_PREDICT_DAYS = 30

# 模型类型 -> 显示名称映射
MODEL_DISPLAY_NAMES = {
    "Prophet": "保守型 (Prophet)",
    "ARIMA": "统计型 (ARIMA)",
    "LSTM": "激进型 (LSTM)",
    "MultiVar-LSTM": "多变量 (MultiVar-LSTM)",
    "Ensemble": "集成 (Ensemble)",
    "MA": "基础型 (MA)",
}


class PredictionEngine:
    """预测引擎，根据模型类型分发到具体策略"""

    def __init__(self):
        self.predictors = {}
        self._init_predictors()

    def _init_predictors(self):
        """初始化所有可用预测器"""
        predictor_classes = {
            "MA": MAPredictor,
            "Prophet": ProphetPredictor,
            "ARIMA": ARIMAPredictor,
            "LSTM": LSTMPredictor,
            "Ensemble": EnsemblePredictor,
            "MultiVar-LSTM": MultiVarLSTMPredictor,
        }

        for name, cls in predictor_classes.items():
            try:
                self.predictors[name] = cls()
                logger.info(f"预测器 {name} 初始化成功")
            except Exception as e:
                logger.warning(f"预测器 {name} 初始化失败: {e}")

    def get_available_models(self) -> list:
        """获取当前可用的模型列表"""
        return list(self.predictors.keys())

    def predict(
        self,
        df: pd.DataFrame,
        model_type: str = "Prophet",
        days: int = DEFAULT_PREDICT_DAYS,
    ) -> PredictionResult:
        """
        执行趋势预测

        Args:
            df: 清洗后的历史数据
            model_type: 模型类型，支持 Prophet/ARIMA/LSTM/MultiVar-LSTM/Ensemble/MA
            days: 预测天数

        Returns:
            PredictionResult

        Note:
            指定模型失败时，按优先级降级：Prophet -> ARIMA -> MA
        """
        # 降级链
        fallback_chain = {
            "Prophet": ["ARIMA", "MA"],
            "ARIMA": ["MA"],
            "LSTM": ["Prophet", "MA"],
            "MultiVar-LSTM": ["LSTM", "Prophet", "MA"],
            "Ensemble": ["Prophet", "ARIMA", "MA"],
            "MA": [],
        }

        # 尝试指定模型
        if model_type in self.predictors:
            try:
                result = self.predictors[model_type].predict(df, days)
                logger.info(f"使用 {model_type} 模型预测成功")
                return result
            except Exception as e:
                logger.warning(f"{model_type} 模型预测失败: {e}")

        # 按降级链尝试
        chain = fallback_chain.get(model_type, ["Prophet", "MA"])
        for fallback_model in chain:
            if fallback_model in self.predictors:
                try:
                    result = self.predictors[fallback_model].predict(df, days)
                    result.model_type = f"{fallback_model} (降级自{model_type})"
                    logger.info(f"降级使用 {fallback_model} 模型预测成功")
                    return result
                except Exception as e:
                    logger.warning(f"降级模型 {fallback_model} 也失败: {e}")

        # 最终兜底：MA
        if "MA" in self.predictors:
            result = self.predictors["MA"].predict(df, days)
            result.model_type = "MA (最终兜底)"
            return result

        raise RuntimeError("所有预测模型均不可用")

    def backtest(
        self,
        df: pd.DataFrame,
        model_type: str = "Prophet",
    ) -> BacktestResult:
        """
        执行历史回测

        Args:
            df: 清洗后的历史数据
            model_type: 模型类型

        Returns:
            BacktestResult
        """
        if model_type in self.predictors:
            try:
                return self.predictors[model_type].backtest(df)
            except Exception as e:
                logger.warning(f"{model_type} 回测失败: {e}")

        # 降级到 MA
        if "MA" in self.predictors:
            return self.predictors["MA"].backtest(df)

        return BacktestResult(mape=float("inf"))
