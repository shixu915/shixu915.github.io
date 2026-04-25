"""集成测试 - 测试完整分析流程（含升级后模型）"""

import sys
import os
import unittest
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# 确保项目根目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_test_df(periods=200, start="2022-01-01"):
    """创建测试用 DataFrame"""
    dates = pd.date_range(start=start, periods=periods, freq="B")
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "nav": np.linspace(1.0, 1.5, periods) + np.random.normal(0, 0.01, periods),
    })


class TestDataModels(unittest.TestCase):
    """测试数据模型"""

    def test_prediction_result_creation(self):
        from src.models.data_models import PredictionResult
        result = PredictionResult(
            fund_code="000001",
            dates=["2024-01-01"],
            values=[1.5],
            upper_bound=[1.6],
            lower_bound=[1.4],
            model_type="Prophet",
        )
        self.assertEqual(result.fund_code, "000001")
        self.assertEqual(result.model_type, "Prophet")
        self.assertIn("不确定性", result.uncertainty_note)

    def test_strategy_advice_creation(self):
        from src.models.data_models import StrategyAdvice
        advice = StrategyAdvice(
            fund_code="000001",
            action="买入",
            reason="预测上涨",
        )
        self.assertEqual(advice.action, "买入")
        self.assertIn("投资有风险", advice.disclaimer)

    def test_fund_info_creation(self):
        from src.models.data_models import FundInfo
        info = FundInfo(code="000001", name="华夏成长", current_nav=1.234)
        self.assertEqual(info.code, "000001")
        self.assertEqual(info.current_nav, 1.234)


class TestDataCleaner(unittest.TestCase):
    """测试数据清洗模块"""

    def setUp(self):
        from src.cleaner.fund_cleaner import FundDataCleaner
        self.cleaner = FundDataCleaner()
        self.test_df = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=100, freq="B"),
            "nav": np.linspace(1.0, 1.5, 100),
            "acc_nav": np.linspace(1.0, 1.8, 100),
        })

    def test_clean_valid_data(self):
        result = self.cleaner.clean(self.test_df)
        self.assertGreaterEqual(len(result), 30)
        self.assertIn("daily_return", result.columns)
        self.assertIn("is_outlier", result.columns)

    def test_fill_missing_values(self):
        df = self.test_df.copy()
        df.loc[5, "nav"] = np.nan
        df.loc[10, "nav"] = np.nan
        result = self.cleaner.fill_missing_values(df)
        self.assertFalse(result["nav"].isna().any())

    def test_detect_outliers(self):
        df = self.test_df.copy()
        df.loc[50, "nav"] = df.loc[50, "nav"] * 1.5
        result = self.cleaner.detect_outliers(df)
        self.assertTrue(result["is_outlier"].any())

    def test_insufficient_data(self):
        small_df = self.test_df.head(10)
        with self.assertRaises(ValueError):
            self.cleaner.clean(small_df)


class TestMAPredictor(unittest.TestCase):
    """测试 MA 预测模型"""

    def setUp(self):
        from src.predictor.ma_predictor import MAPredictor
        self.predictor = MAPredictor()
        self.test_df = _make_test_df()

    def test_predict(self):
        result = self.predictor.predict(self.test_df, days=30)
        self.assertEqual(len(result.values), 30)
        self.assertEqual(result.model_type, "MA")

    def test_confidence_interval(self):
        result = self.predictor.predict(self.test_df, days=30)
        for i in range(len(result.values)):
            self.assertGreaterEqual(result.upper_bound[i], result.values[i])
            self.assertLessEqual(result.lower_bound[i], result.values[i])

    def test_backtest(self):
        result = self.predictor.backtest(self.test_df)
        self.assertGreater(len(result.actual_values), 0)
        self.assertGreaterEqual(result.mape, 0)


class TestARIMAPredictor(unittest.TestCase):
    """测试 ARIMA 预测模型"""

    def setUp(self):
        from src.predictor.arima_predictor import ARIMAPredictor
        self.predictor = ARIMAPredictor()
        self.test_df = _make_test_df()

    def test_predict(self):
        if not self.predictor._statsmodels_available:
            self.skipTest("statsmodels 未安装")
        result = self.predictor.predict(self.test_df, days=30)
        self.assertGreater(len(result.values), 0)
        self.assertIn("ARIMA", result.model_type)

    def test_backtest(self):
        if not self.predictor._statsmodels_available:
            self.skipTest("statsmodels 未安装")
        result = self.predictor.backtest(self.test_df)
        self.assertGreaterEqual(result.mape, 0)


class TestProphetPredictor(unittest.TestCase):
    """测试 Prophet 预测模型"""

    def setUp(self):
        from src.predictor.prophet_predictor import ProphetPredictor
        self.predictor = ProphetPredictor()
        self.test_df = _make_test_df()

    def test_predict(self):
        if not self.predictor._prophet_available:
            self.skipTest("Prophet 未安装")
        result = self.predictor.predict(self.test_df, days=30)
        self.assertGreater(len(result.values), 0)
        self.assertEqual(result.model_type, "Prophet")

    def test_backtest(self):
        if not self.predictor._prophet_available:
            self.skipTest("Prophet 未安装")
        result = self.predictor.backtest(self.test_df)
        self.assertGreaterEqual(result.mape, 0)


class TestEnsemblePredictor(unittest.TestCase):
    """测试集成预测模型"""

    def setUp(self):
        from src.predictor.ensemble_predictor import EnsemblePredictor
        self.predictor = EnsemblePredictor()
        self.test_df = _make_test_df()

    def test_predict(self):
        result = self.predictor.predict(self.test_df, days=30)
        self.assertGreater(len(result.values), 0)
        self.assertIn("Ensemble", result.model_type)

    def test_backtest(self):
        result = self.predictor.backtest(self.test_df)
        self.assertGreaterEqual(result.mape, 0)


class TestMultiVarLSTMPredictor(unittest.TestCase):
    """测试多变量 LSTM 预测模型"""

    def setUp(self):
        from src.predictor.multivar_lstm_predictor import MultiVarLSTMPredictor
        self.predictor = MultiVarLSTMPredictor()
        # 创建含多特征的测试数据
        dates = pd.date_range(start="2022-01-01", periods=200, freq="B")
        self.test_df = pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "nav": np.linspace(1.0, 1.5, 200) + np.random.normal(0, 0.01, 200),
            "hs300_return": np.random.normal(0.001, 0.02, 200),
            "zz500_return": np.random.normal(0.001, 0.02, 200),
        })

    def test_predict(self):
        if not self.predictor._torch_available:
            self.skipTest("PyTorch 未安装")
        result = self.predictor.predict(self.test_df, days=30)
        self.assertGreater(len(result.values), 0)
        self.assertIn("MultiVar-LSTM", result.model_type)


class TestPredictionEngine(unittest.TestCase):
    """测试预测引擎（含所有模型）"""

    def setUp(self):
        from src.predictor.prediction_engine import PredictionEngine
        self.engine = PredictionEngine()
        self.test_df = _make_test_df()

    def test_available_models(self):
        models = self.engine.get_available_models()
        self.assertIn("MA", models)
        self.assertGreater(len(models), 1)

    def test_ma_predict(self):
        result = self.engine.predict(self.test_df, model_type="MA")
        self.assertIn("MA", result.model_type)
        self.assertEqual(len(result.values), 30)

    def test_prophet_predict_or_fallback(self):
        result = self.engine.predict(self.test_df, model_type="Prophet")
        self.assertGreater(len(result.values), 0)

    def test_arima_predict_or_fallback(self):
        result = self.engine.predict(self.test_df, model_type="ARIMA")
        self.assertGreater(len(result.values), 0)

    def test_ensemble_predict(self):
        result = self.engine.predict(self.test_df, model_type="Ensemble")
        self.assertGreater(len(result.values), 0)

    def test_lstm_fallback(self):
        result = self.engine.predict(self.test_df, model_type="LSTM")
        self.assertGreater(len(result.values), 0)

    def test_unknown_model_fallback(self):
        result = self.engine.predict(self.test_df, model_type="NonExistent")
        self.assertGreater(len(result.values), 0)


class TestStrategyAdvisor(unittest.TestCase):
    """测试策略建议模块"""

    def setUp(self):
        from src.advisor.strategy_advisor import FundStrategyAdvisor
        self.advisor = FundStrategyAdvisor()
        self.history_df = _make_test_df()

    def test_buy_advice(self):
        from src.models.data_models import PredictionResult
        pred = PredictionResult(
            fund_code="000001",
            dates=[f"2024-01-{i:02d}" for i in range(1, 31)],
            values=[1.0 + i * 0.02 for i in range(30)],
            upper_bound=[1.0 + i * 0.025 for i in range(30)],
            lower_bound=[1.0 + i * 0.015 for i in range(30)],
        )
        advice = self.advisor.generate_advice(pred, current_nav=0.8, history_df=self.history_df)
        self.assertIn(advice.action, ["买入", "持有", "卖出"])
        self.assertIn("投资有风险", advice.disclaimer)

    def test_hold_advice(self):
        from src.models.data_models import PredictionResult
        pred = PredictionResult(
            fund_code="000001",
            dates=[f"2024-01-{i:02d}" for i in range(1, 31)],
            values=[1.25 + 0.001 * np.sin(i) for i in range(30)],
            upper_bound=[1.3] * 30,
            lower_bound=[1.2] * 30,
        )
        advice = self.advisor.generate_advice(pred, current_nav=1.25, history_df=self.history_df)
        self.assertEqual(advice.action, "持有")

    def test_empty_prediction(self):
        from src.models.data_models import PredictionResult
        pred = PredictionResult(fund_code="000001")
        advice = self.advisor.generate_advice(pred, current_nav=1.0)
        self.assertEqual(advice.action, "持有")


class TestFundFetcher(unittest.TestCase):
    """测试数据获取模块"""

    def test_validate_fund_code(self):
        from src.fetcher.fund_fetcher import FundDataFetcher
        fetcher = FundDataFetcher()
        self.assertTrue(fetcher.validate_fund_code("000001"))
        self.assertTrue(fetcher.validate_fund_code("110011"))
        self.assertFalse(fetcher.validate_fund_code("12345"))
        self.assertFalse(fetcher.validate_fund_code("abc123"))


class TestChartGenerator(unittest.TestCase):
    """测试图表生成模块"""

    def setUp(self):
        from src.chart.chart_generator import FundChartGenerator
        self.generator = FundChartGenerator()
        self.history_df = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=100, freq="B").strftime("%Y-%m-%d"),
            "nav": np.linspace(1.0, 1.5, 100),
        })

    def test_generate_trend_chart(self):
        from src.models.data_models import PredictionResult
        pred = PredictionResult(
            fund_code="000001",
            dates=[f"2024-01-{i:02d}" for i in range(1, 31)],
            values=[1.5 + i * 0.005 for i in range(30)],
            upper_bound=[1.6 + i * 0.005 for i in range(30)],
            lower_bound=[1.4 + i * 0.005 for i in range(30)],
        )
        fig = self.generator.generate_trend_chart(self.history_df, pred)
        self.assertIsNotNone(fig)

    def test_export_chart(self):
        import tempfile
        from src.models.data_models import PredictionResult
        pred = PredictionResult(
            fund_code="000001",
            dates=[f"2024-01-{i:02d}" for i in range(1, 31)],
            values=[1.5] * 30,
            upper_bound=[1.6] * 30,
            lower_bound=[1.4] * 30,
        )
        fig = self.generator.generate_trend_chart(self.history_df, pred)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            success = self.generator.export_chart(fig, f.name, "png")
            self.assertTrue(success)
            os.unlink(f.name)


class TestEnvChecker(unittest.TestCase):
    """测试环境检测模块"""

    def test_check_package(self):
        from src.env.env_checker import EnvironmentChecker
        checker = EnvironmentChecker()
        self.assertTrue(checker.check_package("pandas"))
        self.assertFalse(checker.check_package("nonexistent_package_xyz"))


if __name__ == "__main__":
    unittest.main()
