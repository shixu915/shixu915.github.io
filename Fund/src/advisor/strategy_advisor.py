"""策略建议模块 - 基于预测结果生成买卖建议"""

import numpy as np
import pandas as pd

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, StrategyAdvice

logger = setup_logger(__name__)

# 免责声明
DISCLAIMER = "投资有风险，决策需谨慎，本建议不构成投资指导"

# 建议判定阈值
TREND_THRESHOLD = 0.03    # 涨跌幅阈值 3%
VALUATION_LOW = 0.30      # 低估值分位数
VALUATION_HIGH = 0.70     # 高估值分位数


class FundStrategyAdvisor:
    """基金策略建议生成器"""

    def generate_advice(
        self,
        prediction_result: PredictionResult,
        current_nav: float,
        history_df: pd.DataFrame = None,
    ) -> StrategyAdvice:
        """
        生成策略建议

        Args:
            prediction_result: 预测结果
            current_nav: 当前净值
            history_df: 历史数据（用于估值评估）

        Returns:
            StrategyAdvice
        """
        fund_code = prediction_result.fund_code

        # 检查预测数据有效性
        if not prediction_result.values or not prediction_result.dates:
            logger.warning(f"基金 {fund_code} 预测数据异常，无法生成策略建议")
            return StrategyAdvice(
                fund_code=fund_code,
                action="持有",
                reason="预测数据异常，无法生成有效建议，建议持有观望。",
                disclaimer=DISCLAIMER,
            )

        # 检查 NaN
        if any(np.isnan(v) for v in prediction_result.values):
            logger.warning(f"基金 {fund_code} 预测数据包含 NaN，无法生成策略建议")
            return StrategyAdvice(
                fund_code=fund_code,
                action="持有",
                reason="预测数据异常，无法生成有效建议，建议持有观望。",
                disclaimer=DISCLAIMER,
            )

        # 评估趋势
        trend = self._evaluate_trend(prediction_result, current_nav)

        # 评估估值
        valuation = self._evaluate_valuation(current_nav, history_df)

        # 生成建议
        action, reason = self._decide_action(trend, valuation, current_nav, prediction_result)

        advice = StrategyAdvice(
            fund_code=fund_code,
            action=action,
            reason=reason,
            disclaimer=DISCLAIMER,
        )

        logger.info(f"基金 {fund_code} 策略建议: {action}")
        return advice

    def _evaluate_trend(self, prediction_result: PredictionResult, current_nav: float) -> str:
        """
        评估趋势方向

        Args:
            prediction_result: 预测结果
            current_nav: 当前净值

        Returns:
            "上涨" / "下跌" / "震荡"
        """
        if current_nav <= 0:
            return "震荡"

        # 计算预测期末净值相对当前净值的涨跌幅
        final_pred_nav = prediction_result.values[-1]
        change_rate = (final_pred_nav - current_nav) / current_nav

        if change_rate > TREND_THRESHOLD:
            return "上涨"
        elif change_rate < -TREND_THRESHOLD:
            return "下跌"
        else:
            return "震荡"

    def _evaluate_valuation(self, current_nav: float, history_df: pd.DataFrame = None) -> str:
        """
        评估估值水平

        Args:
            current_nav: 当前净值
            history_df: 历史数据

        Returns:
            "偏高" / "偏低" / "适中"
        """
        if history_df is None or history_df.empty or "nav" not in history_df.columns:
            return "适中"

        hist_nav = history_df["nav"].values
        if len(hist_nav) == 0:
            return "适中"

        # 计算当前净值在历史分布中的分位数
        percentile = np.sum(hist_nav <= current_nav) / len(hist_nav)

        if percentile < VALUATION_LOW:
            return "偏低"
        elif percentile > VALUATION_HIGH:
            return "偏高"
        else:
            return "适中"

    def _decide_action(
        self,
        trend: str,
        valuation: str,
        current_nav: float,
        prediction_result: PredictionResult,
    ) -> tuple:
        """
        判定建议类型和理由

        Returns:
            (action, reason) 元组
        """
        final_pred_nav = prediction_result.values[-1]
        change_rate = (final_pred_nav - current_nav) / current_nav * 100 if current_nav > 0 else 0

        if trend == "上涨" and valuation == "偏低":
            action = "买入"
            reason = (
                f"预测未来30个交易日净值上涨约 {change_rate:.2f}%，"
                f"当前净值处于历史较低水平（估值偏低），"
                f"具备上涨空间，建议买入。"
            )
        elif trend == "下跌" and valuation == "偏高":
            action = "卖出"
            reason = (
                f"预测未来30个交易日净值下跌约 {abs(change_rate):.2f}%，"
                f"当前净值处于历史较高水平（估值偏高），"
                f"存在回调风险，建议卖出。"
            )
        elif trend == "上涨":
            action = "持有"
            reason = (
                f"预测未来30个交易日净值上涨约 {change_rate:.2f}%，"
                f"但当前估值适中，建议持有观望，待估值回落后再考虑加仓。"
            )
        elif trend == "下跌":
            action = "持有"
            reason = (
                f"预测未来30个交易日净值下跌约 {abs(change_rate):.2f}%，"
                f"但当前估值适中，建议持有观望，注意控制仓位。"
            )
        else:
            action = "持有"
            reason = (
                f"预测未来30个交易日净值震荡（变化约 {change_rate:.2f}%），"
                f"趋势不明确，建议持有观望。"
            )

        # 限制理由长度
        if len(reason) > 200:
            reason = reason[:197] + "..."

        return action, reason
