"""多变量 LSTM 预测器 - 使用市场指数等多维特征作为输入

多变量输入可显著提升预测精度（通常 15-30%）：
- 基金历史净值（主变量）
- 沪深300指数收益率（市场趋势）
- 中证500指数收益率（风格因子）
- 10年期国债收益率（利率因子）
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import setup_logger
from src.models.data_models import PredictionResult, BacktestResult

logger = setup_logger(__name__)

MIN_HISTORY_DAYS = 60
DEFAULT_PREDICT_DAYS = 30
SEQUENCE_LENGTH = 60

# 可用特征列
FEATURE_COLUMNS = ["nav", "hs300_return", "zz500_return", "bond_yield_10y"]


class MultiVarLSTMPredictor:
    """多变量 LSTM 预测器"""

    def __init__(self):
        self.model = None
        self._torch_available = self._check_torch()

    def _check_torch(self) -> bool:
        try:
            import torch
            return True
        except ImportError:
            logger.warning("PyTorch 未安装，多变量 LSTM 不可用")
            return False

    def predict(self, df: pd.DataFrame, days: int = DEFAULT_PREDICT_DAYS) -> PredictionResult:
        """
        执行多变量 LSTM 预测

        Args:
            df: 包含多特征的 DataFrame（至少包含 date, nav 列，
                可选 hs300_return, zz500_return, bond_yield_10y 列）
            days: 预测天数

        Returns:
            PredictionResult
        """
        if not self._torch_available:
            raise RuntimeError("PyTorch 未安装，多变量 LSTM 不可用")

        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日（实际 {len(df)} 个），无法进行预测"
            )

        import torch
        import torch.nn as nn

        # 确定可用特征
        available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
        if "nav" not in available_features:
            raise ValueError("数据缺少 nav 列")

        n_features = len(available_features)
        logger.info(f"多变量 LSTM 使用 {n_features} 个特征: {available_features}")

        # 提取特征矩阵
        feature_data = df[available_features].values.astype(float)

        # 处理 NaN：前值填充
        for col_idx in range(n_features):
            col_data = feature_data[:, col_idx]
            nan_mask = np.isnan(col_data)
            if nan_mask.any():
                col_data = pd.Series(col_data).ffill().bfill().values
                feature_data[:, col_idx] = col_data

        dates = df["date"].values

        # 归一化（每个特征独立归一化）
        data_min = feature_data.min(axis=0)
        data_max = feature_data.max(axis=0)
        data_range = np.where(data_max - data_min == 0, 1.0, data_max - data_min)
        normalized = (feature_data - data_min) / data_range

        # 构建训练数据
        X_train, y_train = self._build_sequences(normalized, n_features)

        if len(X_train) < 10:
            raise ValueError("构建的训练样本不足，需要更多历史数据")

        # 训练模型
        try:
            model = self._train_model(X_train, y_train, n_features)
        except Exception as e:
            logger.error(f"多变量 LSTM 训练失败: {e}")
            raise RuntimeError(f"多变量 LSTM 训练失败: {e}")

        # 预测（仅预测 nav，其他特征使用最后一个值保持不变）
        predictions = self._forecast(
            model, normalized, days, n_features,
            data_min[0], data_range[0],  # nav 的归一化参数
        )

        # 计算置信区间
        upper_bound, lower_bound = self._compute_confidence(
            model, normalized, days, n_features,
            data_min[0], data_range[0],
        )

        # 生成预测日期
        pred_dates = self._generate_future_dates(dates[-1], days)

        result = PredictionResult(
            fund_code="",
            dates=pred_dates,
            values=[round(v, 4) for v in predictions],
            upper_bound=[round(v, 4) for v in upper_bound],
            lower_bound=[round(max(v, 0.0001), 4) for v in lower_bound],
            model_type=f"MultiVar-LSTM({n_features}feat)",
        )

        logger.info(f"多变量 LSTM 预测完成，预测 {days} 个交易日")
        return result

    def backtest(self, df: pd.DataFrame) -> BacktestResult:
        """执行历史回测"""
        if len(df) < MIN_HISTORY_DAYS:
            raise ValueError(f"历史数据不足 {MIN_HISTORY_DAYS} 个交易日，无法回测")

        nav_values = df["nav"].values.astype(float)
        dates = df["date"].values

        split_idx = int(len(nav_values) * 0.8)
        train_df = df.iloc[:split_idx].copy()

        test_data = nav_values[split_idx:]
        test_dates = dates[split_idx:]
        predict_days = len(test_data)

        try:
            pred_result = self.predict(train_df, days=predict_days)
            predicted_values = pred_result.values
        except Exception as e:
            logger.error(f"多变量 LSTM 回测失败: {e}")
            return BacktestResult(fund_code="", mape=float("inf"), model_type="MultiVar-LSTM")

        actual = test_data[:len(predicted_values)]
        predicted = np.array(predicted_values[:len(actual)])
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        result = BacktestResult(
            fund_code="",
            actual_dates=list(test_dates[:len(actual)]),
            actual_values=[round(v, 4) for v in actual],
            predicted_values=[round(v, 4) for v in predicted],
            mape=round(mape, 2),
            model_type="MultiVar-LSTM",
        )

        logger.info(f"多变量 LSTM 回测完成，MAPE: {mape:.2f}%")
        return result

    def _build_sequences(self, data: np.ndarray, n_features: int):
        """构建多变量 LSTM 输入序列"""
        import torch

        X, y = [], []
        for i in range(len(data) - SEQUENCE_LENGTH):
            X.append(data[i:i + SEQUENCE_LENGTH])
            y.append(data[i + SEQUENCE_LENGTH, 0])  # 预测 nav（第0列）

        X = np.array(X).reshape(-1, SEQUENCE_LENGTH, n_features)
        y = np.array(y)

        return torch.FloatTensor(X), torch.FloatTensor(y)

    def _train_model(self, X_train, y_train, n_features, epochs=100, patience=10):
        """训练多变量 LSTM 模型"""
        import torch
        import torch.nn as nn

        class MultiVarLSTMModel(nn.Module):
            def __init__(self, n_feat):
                super().__init__()
                self.lstm1 = nn.LSTM(
                    input_size=n_feat, hidden_size=64,
                    num_layers=2, batch_first=True, dropout=0.2,
                )
                self.fc = nn.Linear(64, 1)

            def forward(self, x):
                out, _ = self.lstm1(x)
                out = self.fc(out[:, -1, :])
                return out

        model = MultiVarLSTMModel(n_features)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

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
        return model

    def _forecast(self, model, normalized_data, days, n_features, nav_min, nav_range):
        """多变量预测"""
        import torch

        predictions = []
        current_seq = normalized_data[-SEQUENCE_LENGTH:].copy()

        with torch.no_grad():
            for _ in range(days):
                x = torch.FloatTensor(current_seq).reshape(1, SEQUENCE_LENGTH, n_features)
                pred = model(x).item()
                # 反归一化 nav
                predictions.append(pred * nav_range + nav_min)
                # 更新序列：新行 = 最后一行（其他特征保持），nav 替换为预测值
                new_row = current_seq[-1].copy()
                new_row[0] = pred
                current_seq = np.vstack([current_seq[1:], new_row])

        return predictions

    def _compute_confidence(self, model, normalized_data, days, n_features, nav_min, nav_range, n_samples=50):
        """Monte Carlo Dropout 置信区间"""
        import torch

        all_predictions = []
        current_seq = normalized_data[-SEQUENCE_LENGTH:].copy()

        model.train()
        for _ in range(n_samples):
            preds = []
            seq = current_seq.copy()
            with torch.no_grad():
                for _ in range(days):
                    x = torch.FloatTensor(seq).reshape(1, SEQUENCE_LENGTH, n_features)
                    pred = model(x).item()
                    preds.append(pred * nav_range + nav_min)
                    new_row = seq[-1].copy()
                    new_row[0] = pred
                    seq = np.vstack([seq[1:], new_row])
            all_predictions.append(preds)

        all_predictions = np.array(all_predictions)
        mean_pred = np.mean(all_predictions, axis=0)
        std_pred = np.std(all_predictions, axis=0)

        upper = mean_pred + 2 * std_pred
        lower = mean_pred - 2 * std_pred

        return list(upper), list(lower)

    def _generate_future_dates(self, last_date_str: str, days: int) -> list:
        """生成未来交易日日期"""
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
