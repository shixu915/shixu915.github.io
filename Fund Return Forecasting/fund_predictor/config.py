"""
基金收益趋势预测工具 - 配置文件
"""
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据配置
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# 确保目录存在
for dir_path in [DATA_DIR, MODEL_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 预测配置
PREDICTION_CONFIG = {
    'sequence_length': 60,  # 使用过去60天的数据预测
    'prediction_days': 30,  # 预测未来30天
    'train_test_split': 0.8,  # 训练集比例
    'random_state': 42
}

# 技术指标配置
INDICATOR_CONFIG = {
    'ma_periods': [5, 10, 20, 60],  # 移动平均线周期
    'rsi_period': 14,  # RSI周期
    'macd_fast': 12,  # MACD快线
    'macd_slow': 26,  # MACD慢线
    'macd_signal': 9   # MACD信号线
}

# 可视化配置
PLOT_CONFIG = {
    'figsize': (14, 8),
    'dpi': 100,
    'style': 'seaborn',
    'color_palette': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
}

# 模型配置
MODEL_CONFIG = {
    'lstm_units': 50,
    'lstm_dropout': 0.2,
    'dense_units': 25,
    'epochs': 50,
    'batch_size': 32,
    'learning_rate': 0.001
}
