"""激进型预测策略 - 基于 LSTM 深度学习模型"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

MIN_HISTORY_DAYS = 60
DEFAULT_PREDICT_DAYS = 30
SEQUENCE_LENGTH = 60  # 输入序列长度


class LSTMPredictor:
    """激进型预测器 - LSTM 深度学习"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self._torch_available = self._check_torch()

    def _check_torch(self) -> bool:
        """检查 PyTorch 是否可用"""
        try:
            import torch
            return True
        except ImportError:
            logger.warning("PyTorch 未安装，LSTM 模型不可用，将降级为 MA 模型")
            return False

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行 LSTM 预测

        Args:
            df: 清洗后的历史数据
            days: 预测天数

        Returns:
            PredictionResult

        Raises:
            ValueError: 数据不足或 PyTorch 不可用
            RuntimeError: 模型训练失败
        """
        if not self._torch_available:
            raise RuntimeError("PyTorch 未安装，LSTM 模型不可用")

        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        import torch
        import torch.nn as nn

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        # 数据归一化
        data_min = nav_values.min()
        data_max = nav_values.max()
        data_range = data_max - data_min if data_max != data_min else 1.0
        normalized = (nav_values - data_min) / data_range

        # 构建训练数据
        X_train, y_train = self._build_sequences(normalized)

        # 训练模型
        try:
            model = self._train_model(X_train, y_train)
        except Exception as e:
            logger.error(f"LSTM 模型训练失败: {e}")
            raise RuntimeError(f"LSTM 模型训练失败: {e}")

        # 预测
        predictions = self._forecast(model, normalized, days, data_min, data_range)

        # 计算置信区间（Monte Carlo Dropout）
        upper_bound, lower_bound = self._compute_confidence(
            model, normalized, days, data_min, data_range
        )

        # 生成预测日期
        pred_dates = self._generate_future_dates(dates[-1], days)

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in predictions],
            upper_bound=[round(v, 4) for v in upper_bound],
            lower_bound=[round(max(v, 0.0001), 4) for v in lower_bound],
            model_type="LSTM",
        )

        logger.info(f"LSTM 预测完成，预测 {days} 个交易日")
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
            logger.error(f"LSTM 回测预测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="LSTM")

        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="LSTM",
        )

        logger.info(f"LSTM 回测完成，MAPE: {mape:.2f}%")
        return result

    def _build_sequences(self, data: np.ndarray):
        """构建 LSTM 输入序列"""
        import torch

        X, y = [], []
        for i in range(len(data) - SEQUENCE_LENGTH):
            X.append(data[i:i + SEQUENCE_LENGTH])
            y.append(data[i + SEQUENCE_LENGTH])

        X = np.array(X).reshape(-1, SEQUENCE_LENGTH, 1)
        y = np.array(y)

        return (
            torch.FloatTensor(X),
            torch.FloatTensor(y),
        )

    def _train_model(self, X_train, y_train, epochs=100, patience=10):
        """训练 LSTM 模型"""
        import torch
        import torch.nn as nn

        class LSTMModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm1 = nn.LSTM(input_size=1, hidden_size=64, num_layers=2, batch_first=True, dropout=0.2)
                self.fc = nn.Linear(64, 1)

            def forward(self, x):
                out, _ = self.lstm1(x)
                out = self.fc(out[:, -1, :])
                return out

        model = LSTMModel()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # 划分训练集和验证集
        val_split = int(len(X_train) * 0.8)
        X_val = X_train[val_split:]
        y_val = y_train[val_split:]
        X_tr = X_train[:val_split]
        y_tr = y_train[:val_split]

        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            output = model(X_tr)
            loss = criterion(output.squeeze(), y_tr)
            loss.backward()
            optimizer.step()

            # 验证
            model.eval()
            with torch.no_grad():
                val_output = model(X_val)
                val_loss = criterion(val_output.squeeze(), y_val).item()

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break

        if best_state is not None:
            model.load_state_dict(best_state)

        model.eval()
        self.model = model
        return model

    def _forecast(self, model, normalized_data, days, data_min, data_range):
        """使用训练好的模型进行预测"""
        import torch

        predictions = []
        current_seq = normalized_data[-SEQUENCE_LENGTH:].copy()

        with torch.no_grad():
            for _ in range(days):
                x = torch.FloatTensor(current_seq).reshape(1, SEQUENCE_LENGTH, 1)
                pred = model(x).item()
                predictions.append(pred * data_range + data_min)
                current_seq = np.append(current_seq[1:], pred)

        return predictions

    def _compute_confidence(self, model, normalized_data, days, data_min, data_range, n_samples=50):
        """Monte Carlo Dropout 计算置信区间"""
        import torch

        all_predictions = []
        current_seq = normalized_data[-SEQUENCE_LENGTH:].copy()

        # 启用 dropout 进行多次前向传播
        model.train()  # train 模式启用 dropout
        for _ in range(n_samples):
            preds = []
            seq = current_seq.copy()
            with torch.no_grad():
                for _ in range(days):
                    x = torch.FloatTensor(seq).reshape(1, SEQUENCE_LENGTH, 1)
                    pred = model(x).item()
                    preds.append(pred * data_range + data_min)
                    seq = np.append(seq[1:], pred)
            all_predictions.append(preds)

        all_predictions = np.array(all_predictions)
        mean_pred = np.mean(all_predictions, axis=0)
        std_pred = np.std(all_predictions, axis=0)

        upper = mean_pred + 2 * std_pred
        lower = mean_pred - 2 * std_pred

        return list(upper), list(lower)

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
