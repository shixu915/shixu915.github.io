"""
趋势预测模块
使用机器学习模型预测基金收益趋势
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from config import PREDICTION_CONFIG, MODEL_CONFIG, MODEL_DIR
import os


class FundPredictor:
    """基金趋势预测器"""
    
    def __init__(self):
        self.config = PREDICTION_CONFIG
        self.model_config = MODEL_CONFIG
        self.scaler = MinMaxScaler()
        self.model = None
        self.model_dir = MODEL_DIR
        
    def prepare_data(self, df, feature_col='nav'):
        """
        准备训练数据
        
        参数:
            df: 原始数据
            feature_col: 特征列名
            
        返回:
            tuple: (X, y) 训练数据
        """
        data = df[feature_col].values.reshape(-1, 1)
        data_scaled = self.scaler.fit_transform(data)
        
        sequence_length = self.config['sequence_length']
        X, y = [], []
        
        for i in range(len(data_scaled) - sequence_length):
            X.append(data_scaled[i:i+sequence_length, 0])
            y.append(data_scaled[i+sequence_length, 0])
        
        X, y = np.array(X), np.array(y)
        
        return X, y
    
    def train_linear_model(self, X, y):
        """训练线性回归模型"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=1-self.config['train_test_split'],
            random_state=self.config['random_state']
        )
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 评估
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"线性回归模型 - MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.6f}")
        
        return model, {'mse': mse, 'mae': mae, 'r2': r2}
    
    def train_rf_model(self, X, y):
        """训练随机森林模型"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=1-self.config['train_test_split'],
            random_state=self.config['random_state']
        )
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=self.config['random_state'],
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # 评估
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"随机森林模型 - MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.6f}")
        
        return model, {'mse': mse, 'mae': mae, 'r2': r2}
    
    def train(self, df, model_type='rf'):
        """
        训练模型
        
        参数:
            df: 训练数据
            model_type: 模型类型 ('linear' 或 'rf')
            
        返回:
            model: 训练好的模型
        """
        print(f"准备训练数据...")
        X, y = self.prepare_data(df)
        
        print(f"训练 {model_type} 模型...")
        if model_type == 'linear':
            self.model, self.metrics = self.train_linear_model(X, y)
        elif model_type == 'rf':
            self.model, self.metrics = self.train_rf_model(X, y)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        return self.model
    
    def predict(self, df, days=None):
        """
        预测未来趋势
        
        参数:
            df: 历史数据
            days: 预测天数
            
        返回:
            DataFrame: 预测结果
        """
        if self.model is None:
            raise ValueError("模型未训练，请先调用 train() 方法")
        
        if days is None:
            days = self.config['prediction_days']
        
        # 准备最后的数据作为预测输入
        sequence_length = self.config['sequence_length']
        last_data = df['nav'].values[-sequence_length:].reshape(-1, 1)
        last_data_scaled = self.scaler.transform(last_data).flatten()
        
        # 预测未来值
        predictions = []
        current_input = last_data_scaled.copy()
        
        for _ in range(days):
            # 预测下一个值
            pred = self.model.predict(current_input.reshape(1, -1))[0]
            predictions.append(pred)
            
            # 更新输入序列
            current_input = np.roll(current_input, -1)
            current_input[-1] = pred
        
        # 反归一化
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions).flatten()
        
        # 创建预测结果DataFrame
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='D')
        
        result_df = pd.DataFrame({
            'date': future_dates,
            'predicted_nav': predictions
        })
        result_df['date'] = pd.to_datetime(result_df['date'])
        result_df = result_df.set_index('date')
        
        # 计算预测收益率
        result_df['predicted_return'] = result_df['predicted_nav'].pct_change() * 100
        result_df['predicted_cumulative_return'] = (result_df['predicted_nav'] / df['nav'].iloc[-1] - 1) * 100
        
        return result_df
    
    def evaluate_trend(self, df, predictions):
        """
        评估趋势方向
        
        参数:
            df: 历史数据
            predictions: 预测结果
            
        返回:
            dict: 趋势评估结果
        """
        current_nav = df['nav'].iloc[-1]
        future_nav = predictions['predicted_nav'].iloc[-1]
        
        trend = '上涨' if future_nav > current_nav else '下跌'
        change_pct = (future_nav / current_nav - 1) * 100
        
        # 计算平均波动
        avg_volatility = predictions['predicted_return'].std()
        
        # 趋势强度（基于预测的一致性）
        returns = predictions['predicted_return'].dropna()
        positive_days = (returns > 0).sum()
        trend_strength = positive_days / len(returns) * 100
        
        result = {
            'current_nav': current_nav,
            'predicted_nav': future_nav,
            'trend': trend,
            'change_pct': change_pct,
            'avg_volatility': avg_volatility,
            'trend_strength': trend_strength,
            'model_metrics': self.metrics
        }
        
        return result
    
    def save_model(self, filename):
        """保存模型"""
        import joblib
        filepath = os.path.join(self.model_dir, filename)
        joblib.dump(self.model, filepath)
        print(f"模型已保存到: {filepath}")
    
    def load_model(self, filename):
        """加载模型"""
        import joblib
        filepath = os.path.join(self.model_dir, filename)
        self.model = joblib.load(filepath)
        print(f"模型已从 {filepath} 加载")


class SimplePredictor:
    """简单预测器（基于移动平均和趋势外推）"""
    
    def __init__(self):
        pass
    
    def predict_by_ma(self, df, days=30, ma_period=20):
        """
        基于移动平均的简单预测
        
        参数:
            df: 历史数据
            days: 预测天数
            ma_period: 移动平均周期
            
        返回:
            DataFrame: 预测结果
        """
        # 计算移动平均
        ma = df['nav'].rolling(window=ma_period).mean()
        
        # 计算趋势（移动平均的变化率）
        trend = (ma.iloc[-1] - ma.iloc[-ma_period]) / ma_period
        
        # 预测未来值
        last_value = df['nav'].iloc[-1]
        predictions = [last_value + trend * (i + 1) for i in range(days)]
        
        # 创建结果
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='D')
        
        result_df = pd.DataFrame({
            'date': future_dates,
            'predicted_nav': predictions
        })
        result_df['date'] = pd.to_datetime(result_df['date'])
        result_df = result_df.set_index('date')
        
        return result_df
    
    def predict_by_regression(self, df, days=30, lookback=60):
        """
        基于线性回归的预测
        
        参数:
            df: 历史数据
            days: 预测天数
            lookback: 回看天数
            
        返回:
            DataFrame: 预测结果
        """
        # 使用最近的数据进行线性拟合
        recent_data = df['nav'].iloc[-lookback:]
        X = np.arange(len(recent_data)).reshape(-1, 1)
        y = recent_data.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测未来值
        future_X = np.arange(len(recent_data), len(recent_data) + days).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # 创建结果
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='D')
        
        result_df = pd.DataFrame({
            'date': future_dates,
            'predicted_nav': predictions
        })
        result_df['date'] = pd.to_datetime(result_df['date'])
        result_df = result_df.set_index('date')
        
        return result_df


if __name__ == '__main__':
    # 测试预测模块
    from data_fetcher import FundDataFetcher
    
    # 获取数据
    fetcher = FundDataFetcher()
    df = fetcher.get_data('000001', days=365)
    
    # 训练模型
    predictor = FundPredictor()
    predictor.train(df, model_type='rf')
    
    # 预测
    predictions = predictor.predict(df, days=30)
    print("\n预测结果:")
    print(predictions.head())
    
    # 评估趋势
    evaluation = predictor.evaluate_trend(df, predictions)
    print("\n趋势评估:")
    for key, value in evaluation.items():
        print(f"{key}: {value}")
