# 基金收益趋势预测工具

一个基于Python的基金收益趋势预测实用工具，提供数据获取、技术分析、趋势预测和可视化功能。

## 功能特性

- **数据获取**: 支持获取基金历史净值数据（当前使用模拟数据，可扩展为真实API）
- **技术分析**: 计算多种技术指标（MA、EMA、RSI、MACD、布林带等）
- **趋势预测**: 使用机器学习模型（线性回归、随机森林）预测未来趋势
- **可视化**: 提供丰富的图表展示功能
- **交易信号**: 基于技术指标生成买卖信号

## 项目结构

```
fund_predictor/
├── config.py              # 配置文件
├── data_fetcher.py        # 数据获取模块
├── technical_analysis.py  # 技术分析模块
├── predictor.py           # 趋势预测模块
├── visualizer.py          # 可视化模块
├── main.py                # 主程序入口
├── requirements.txt       # 依赖包列表
├── data/                  # 数据存储目录
├── models/                # 模型存储目录
└── output/                # 输出文件目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本使用

```bash
# 分析单个基金
python main.py 000001

# 分析多个基金
python main.py 000001 000002 000003
```

### 2. 对比分析

```bash
# 对比多个基金的表现
python main.py 000001 000002 --compare
```

### 3. 快速预测

```bash
# 使用简单模型快速预测
python main.py 000001 --quick
```

### 4. 自定义参数

```bash
# 使用180天历史数据
python main.py 000001 --days 180

# 预测未来60天
python main.py 000001 --predict-days 60

# 保存图表到文件
python main.py 000001 --save-plots

# 不显示图表（仅生成报告）
python main.py 000001 --no-plots
```

### 5. Python API使用

```python
from data_fetcher import FundDataFetcher
from technical_analysis import TechnicalAnalysis
from predictor import FundPredictor
from visualizer import FundVisualizer

# 获取数据
fetcher = FundDataFetcher()
df = fetcher.get_data('000001', days=365)

# 技术分析
ta = TechnicalAnalysis()
df = ta.calculate_all_indicators(df)
df = ta.generate_signals(df)

# 趋势预测
predictor = FundPredictor()
predictor.train(df, model_type='rf')
predictions = predictor.predict(df, days=30)

# 可视化
viz = FundVisualizer()
viz.plot_nav_history(df, '000001')
viz.plot_prediction(df, predictions, '000001')
```

## 技术指标说明

### 移动平均线 (MA)
- MA5: 5日移动平均线
- MA20: 20日移动平均线
- MA60: 60日移动平均线

### 相对强弱指标 (RSI)
- RSI > 70: 超买区域，可能回调
- RSI < 30: 超卖区域，可能反弹

### MACD指标
- MACD线: 快线与慢线的差值
- 信号线: MACD的移动平均
- 柱状图: MACD与信号线的差值

### 布林带 (Bollinger Bands)
- 上轨: 中轨 + 2倍标准差
- 中轨: 20日移动平均线
- 下轨: 中轨 - 2倍标准差

## 预测模型

### 随机森林模型
- 使用历史序列数据作为特征
- 预测未来净值走势
- 提供模型评估指标（MSE、MAE、R²）

### 简单预测模型
- 移动平均趋势外推
- 线性回归预测

## 输出文件

运行程序后会在相应目录生成以下文件：

- `data/`: 基金历史数据CSV文件
- `models/`: 训练好的模型文件
- `output/`: 可视化图表PNG文件

## 注意事项

1. 当前版本使用模拟数据进行演示，实际使用时需要接入真实数据源API
2. 预测结果仅供参考，不构成投资建议
3. 基金投资有风险，投资需谨慎
4. 建议结合多种分析方法和市场信息进行综合判断

## 扩展开发

### 接入真实数据源

修改 `data_fetcher.py` 中的数据获取方法，接入真实的基金数据API：

```python
def get_real_data(self, fund_code, start_date, end_date):
    """从真实API获取数据"""
    # 例如：使用tushare、akshare等库
    import akshare as ak
    df = ak.fund_etf_fund_info_em(fund=fund_code)
    # 数据处理...
    return df
```

### 添加新的技术指标

在 `technical_analysis.py` 中添加新的指标计算方法：

```python
def calculate_new_indicator(self, df, period=14):
    """计算新指标"""
    df = df.copy()
    # 指标计算逻辑...
    return df
```

### 使用深度学习模型

可以扩展 `predictor.py` 使用LSTM等深度学习模型：

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def build_lstm_model(self):
    """构建LSTM模型"""
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(60, 1)),
        LSTM(50),
        Dense(1)
    ])
    return model
```

## 版本历史

- v1.0.0: 初始版本，包含基本功能
  - 数据获取和模拟
  - 技术指标计算
  - 机器学习预测
  - 可视化展示

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎反馈。
