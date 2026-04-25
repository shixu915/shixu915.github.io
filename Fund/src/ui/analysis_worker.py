"""分析工作线程 - 在子线程中执行分析流程，避免阻塞 UI"""

from PyQt5.QtCore import QThread, pyqtSignal

import pandas as pd

from src.fetcher.fund_fetcher import FundDataFetcher
from src.fetcher.market_fetcher import MarketDataFetcher
from src.cleaner.fund_cleaner import FundDataCleaner
from src.predictor.prediction_engine import PredictionEngine
from src.chart.chart_generator import FundChartGenerator
from src.advisor.strategy_advisor import FundStrategyAdvisor
from src.models.data_models import PredictionResult, BacktestResult, StrategyAdvice, FundInfo
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalysisWorker(QThread):
    """分析工作线程"""

    # 信号定义
    progress_updated = pyqtSignal(str, int)     # (阶段描述, 进度百分比)
    data_fetched = pyqtSignal(str, object)       # (基金代码, DataFrame)
    prediction_done = pyqtSignal(str, object)    # (基金代码, PredictionResult)
    backtest_done = pyqtSignal(str, object)      # (基金代码, BacktestResult)
    advice_done = pyqtSignal(str, object)        # (基金代码, StrategyAdvice)
    fund_info_ready = pyqtSignal(str, object)    # (基金代码, FundInfo)
    error_occurred = pyqtSignal(str, str)        # (基金代码, 错误信息)
    analysis_finished = pyqtSignal()             # 全部完成

    def __init__(self, fund_codes: list, model_type: str = "Ensemble"):
        super().__init__()
        self.fund_codes = fund_codes
        self.model_type = model_type

        self.fetcher = FundDataFetcher()
        self.market_fetcher = MarketDataFetcher()
        self.cleaner = FundDataCleaner()
        self.engine = PredictionEngine()
        self.chart_generator = FundChartGenerator()
        self.advisor = FundStrategyAdvisor()

    def run(self):
        """执行分析流程"""
        total = len(self.fund_codes)

        for idx, code in enumerate(self.fund_codes):
            try:
                base_progress = int(idx / total * 100)

                # 阶段1: 数据获取
                self.progress_updated.emit(f"正在获取基金 {code} 数据...", base_progress + 3)
                raw_df = self.fetcher.fetch_nav_history(code)

                if raw_df.empty:
                    self.error_occurred.emit(code, f"基金 {code} 数据获取失败或无数据")
                    continue

                # 获取基金基本信息
                fund_info = self.fetcher.fetch_fund_info(code)
                self.fund_info_ready.emit(code, fund_info)

                # 阶段2: 数据清洗
                self.progress_updated.emit(f"正在清洗基金 {code} 数据...", base_progress + 10)
                try:
                    clean_df = self.cleaner.clean(raw_df)
                except ValueError as e:
                    self.error_occurred.emit(code, str(e))
                    continue

                self.data_fetched.emit(code, clean_df)

                # 阶段2.5: 多变量特征获取（仅 MultiVar-LSTM 和 Ensemble 需要）
                analysis_df = clean_df
                if self.model_type in ("MultiVar-LSTM", "Ensemble"):
                    self.progress_updated.emit(f"正在获取市场特征数据...", base_progress + 18)
                    try:
                        analysis_df = self.market_fetcher.fetch_multi_features(clean_df)
                        logger.info(f"基金 {code} 多变量特征获取完成")
                    except Exception as e:
                        logger.warning(f"市场特征获取失败（不影响单变量预测）: {e}")
                        analysis_df = clean_df

                # 阶段3: 趋势预测
                self.progress_updated.emit(f"正在预测基金 {code} 趋势...", base_progress + 30)
                try:
                    pred_result = self.engine.predict(analysis_df, self.model_type)
                    pred_result.fund_code = code
                    self.prediction_done.emit(code, pred_result)
                except Exception as e:
                    self.error_occurred.emit(code, f"预测失败: {e}")
                    continue

                # 阶段4: 回测
                self.progress_updated.emit(f"正在回测基金 {code} 模型...", base_progress + 55)
                try:
                    backtest_result = self.engine.backtest(analysis_df, self.model_type)
                    backtest_result.fund_code = code
                    self.backtest_done.emit(code, backtest_result)
                except Exception as e:
                    logger.warning(f"基金 {code} 回测失败: {e}")

                # 阶段5: 策略建议
                self.progress_updated.emit(f"正在生成基金 {code} 建议...", base_progress + 75)
                current_nav = clean_df["nav"].iloc[-1] if not clean_df.empty else 0
                advice = self.advisor.generate_advice(pred_result, current_nav, clean_df)
                self.advice_done.emit(code, advice)

                self.progress_updated.emit(f"基金 {code} 分析完成", base_progress + 95)

            except Exception as e:
                logger.error(f"基金 {code} 分析异常: {e}")
                self.error_occurred.emit(code, f"分析异常: {e}")

        self.progress_updated.emit("全部分析完成", 100)
        self.analysis_finished.emit()
