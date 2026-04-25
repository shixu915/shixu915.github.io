# 基金趋势预测工具 - 开发任务清单

## 任务总览

基于 spec.md 需求规格和 design.md 技术设计，将开发工作拆解为以下增量式任务，按依赖顺序排列。

---

## Task 1: 项目骨架与依赖管理

**目标**：创建项目目录结构、依赖配置文件和入口脚本

**具体步骤**：
1. 创建项目目录结构：
   ```
   Fund/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py              # 应用入口
   │   ├── ui/                   # 界面模块
   │   │   └── __init__.py
   │   ├── fetcher/              # 数据获取模块
   │   │   └── __init__.py
   │   ├── cleaner/              # 数据清洗模块
   │   │   └── __init__.py
   │   ├── predictor/            # 趋势预测模块
   │   │   └── __init__.py
   │   ├── chart/                # 图表生成模块
   │   │   └── __init__.py
   │   ├── advisor/              # 策略建议模块
   │   │   └── __init__.py
   │   ├── env/                  # 环境检测模块
   │   │   └── __init__.py
   │   └── models/               # 数据模型
   │       └── __init__.py
   ├── logs/                     # 日志目录
   ├── output/                   # 导出图片目录
   ├── requirements.txt
   └── README.md
   ```
2. 创建 `requirements.txt`，包含所有依赖：
   - akshare
   - pandas
   - numpy
   - matplotlib
   - PyQt5
   - torch (PyTorch，用于 LSTM)
   - scikit-learn
3. 创建 `src/models/data_models.py`，定义所有 dataclass：PredictionResult、BacktestResult、StrategyAdvice、FundInfo
4. 创建 `src/env/env_checker.py`，实现 EnvironmentChecker 类（check_and_install、check_package、install_package）
5. 创建 `src/main.py` 入口脚本，启动时调用 EnvChecker 检测环境

**验收标准**：
- 项目目录结构完整
- `requirements.txt` 包含所有依赖
- dataclass 模型可正常实例化
- EnvChecker 能检测依赖缺失并尝试自动安装

---

## Task 2: 日志服务

**目标**：实现统一日志服务，供所有模块使用

**具体步骤**：
1. 创建 `src/utils/logger.py`
2. 实现 `setup_logger(name, level)` 函数：
   - 日志输出到 `logs/` 目录下的文件，文件名包含日期
   - 同时输出到控制台
   - 日志格式：`[时间戳] [级别] [模块名] 消息内容`
   - API 密钥等敏感信息脱敏处理
3. 各模块通过 `setup_logger(__name__)` 获取 logger 实例

**验收标准**：
- 日志文件正确写入 `logs/` 目录
- 日志格式包含时间戳、级别、模块名
- 敏感信息脱敏

---

## Task 3: 数据获取模块

**目标**：实现 FundDataFetcher，从 AkShare 获取基金历史数据

**具体步骤**：
1. 创建 `src/fetcher/fund_fetcher.py`
2. 实现 `FundDataFetcher` 类：
   - `validate_fund_code(code) -> bool`：校验 6 位数字格式
   - `fetch_nav_history(fund_code, start_date, end_date) -> pd.DataFrame`：获取历史净值
   - `fetch_fund_info(fund_code) -> FundInfo`：获取基金基本信息
   - `fetch_batch(fund_codes, start_date, end_date) -> dict[str, pd.DataFrame]`：批量获取
3. 封装 AkShare API 调用：
   - `ak.fund_etf_hist_em()` 获取 ETF 基金数据
   - `ak.fund_open_fund_info_em()` 获取开放式基金数据
4. 实现异常处理：
   - 网络超时 30 秒，重试 3 次
   - 基金代码不存在返回空 DataFrame
   - API 限流自动等待重试
5. 所有操作记录日志

**验收标准**：
- 输入有效基金代码能返回 DataFrame，包含 date、nav、acc_nav 列
- 输入无效代码返回空 DataFrame 并记录日志
- 网络异常时友好提示而非崩溃
- 支持多基金代码批量获取

---

## Task 4: 数据清洗模块

**目标**：实现 FundDataCleaner，确保数据质量

**具体步骤**：
1. 创建 `src/cleaner/fund_cleaner.py`
2. 实现 `FundDataCleaner` 类：
   - `clean(raw_df) -> pd.DataFrame`：执行完整清洗流程
   - `fill_missing_values(df) -> pd.DataFrame`：前值填充缺失值
   - `detect_outliers(df, threshold=0.2) -> pd.DataFrame`：检测异常值（涨跌幅 > 20%）
   - `unify_formats(df) -> pd.DataFrame`：统一日期格式和数值精度
3. 清洗流程：排序 → 填充缺失值 → 检测异常值 → 统一格式 → 校验数据量
4. 清洗后 DataFrame 增加 `daily_return` 和 `is_outlier` 列
5. 有效数据不足 30 条时抛出异常

**验收标准**：
- 缺失值使用前值填充
- 涨跌幅超 20% 的记录标记 is_outlier=True
- 日期统一为 YYYY-MM-DD，净值保留 4 位小数
- 数据不足 30 条时抛出 ValueError

---

## Task 5: 趋势预测模块 - 保守型 MA 模型

**目标**：实现 MAPredictor 保守型预测策略

**具体步骤**：
1. 创建 `src/predictor/ma_predictor.py`
2. 实现 `MAPredictor` 类：
   - `predict(df, days=30) -> PredictionResult`：执行 MA 预测
   - `backtest(df) -> BacktestResult`：执行历史回测
3. 预测算法：
   - 计算 5 日、10 日、20 日、60 日移动平均线
   - 加权外推：近期均线权重更高
   - 置信区间 = 预测值 ± 2 × 历史波动率标准差 × √天数
4. 回测算法：
   - 用前 80% 数据预测后 20%
   - 计算 MAPE（平均绝对百分比误差）
5. 历史数据不足 60 条时抛出异常

**验收标准**：
- 输入有效 DataFrame 返回 PredictionResult，包含 30 个预测值和置信区间
- 置信上界 >= 预测值 >= 置信下界
- 回测结果包含 MAPE 指标
- 数据不足 60 条时抛出 ValueError

---

## Task 6: 趋势预测模块 - 激进型 LSTM 模型

**目标**：实现 LSTMPredictor 激进型预测策略

**具体步骤**：
1. 创建 `src/predictor/lstm_predictor.py`
2. 实现 `LSTMPredictor` 类：
   - `predict(df, days=30) -> PredictionResult`：执行 LSTM 预测
   - `backtest(df) -> BacktestResult`：执行历史回测
3. LSTM 网络结构：
   - 2 层 LSTM（64, 32 隐藏单元）+ 全连接层
   - 输入：过去 60 个交易日净值序列
   - 输出：未来 30 个交易日净值
4. 训练配置：
   - Adam 优化器，学习率 0.001
   - MSE 损失函数
   - 最多 100 轮，early stopping patience=10
   - 训练集/验证集 = 80%/20%
5. 置信区间：Monte Carlo Dropout（50 次前向传播取标准差）
6. 降级策略：训练失败自动回退到 MAPredictor

**验收标准**：
- 输入有效 DataFrame 返回 PredictionResult
- 训练失败时自动降级为 MA 模型并提示用户
- 置信区间合理（上界 >= 预测值 >= 下界）
- 回测结果包含 MAPE 指标

---

## Task 7: 趋势预测模块 - 预测引擎

**目标**：实现 PredictionEngine，统一调度 MA 和 LSTM 模型

**具体步骤**：
1. 创建 `src/predictor/prediction_engine.py`
2. 实现 `PredictionEngine` 类：
   - `predict(df, model_type, days=30) -> PredictionResult`：根据 model_type 分发到 MAPredictor 或 LSTMPredictor
   - `backtest(df, model_type) -> BacktestResult`：根据 model_type 执行回测
3. model_type 参数：`"MA"` 或 `"LSTM"`
4. 异常处理：LSTM 失败时自动降级为 MA

**验收标准**：
- model_type="MA" 调用 MAPredictor
- model_type="LSTM" 调用 LSTMPredictor
- LSTM 失败时自动降级并提示

---

## Task 8: 图表生成模块

**目标**：实现 FundChartGenerator，生成三类可视化图表

**具体步骤**：
1. 创建 `src/chart/chart_generator.py`
2. 实现 `FundChartGenerator` 类：
   - `generate_trend_chart(history_df, prediction_result) -> Figure`：历史走势+预测趋势图
   - `generate_backtest_chart(backtest_result) -> Figure`：回测对比图
   - `generate_flow_chart(fund_info_df) -> Figure`：资金流向图
   - `export_chart(figure, filepath, format) -> bool`：导出为 PNG/JPG
3. 图表规范：
   - 尺寸 12×6 英寸，DPI 150
   - 中文字体支持（SimHei 或 Microsoft YaHei）
   - 历史数据蓝色实线，预测红色虚线，置信区间红色半透明填充
   - 包含标题、坐标轴标签、图例、网格线
4. 导出功能：支持 PNG 和 JPG 格式

**验收标准**：
- 三类图表均能正确生成 matplotlib Figure 对象
- 图表包含标题、标签、图例、网格线
- 中文正常显示
- 导出 PNG/JPG 文件可正常打开

---

## Task 9: 策略建议模块

**目标**：实现 FundStrategyAdvisor，生成买卖建议

**具体步骤**：
1. 创建 `src/advisor/strategy_advisor.py`
2. 实现 `FundStrategyAdvisor` 类：
   - `generate_advice(prediction_result, current_nav, history_df) -> StrategyAdvice`
   - `_evaluate_trend(prediction_result) -> str`：评估趋势方向
   - `_evaluate_valuation(current_nav, history_df) -> str`：评估估值水平
3. 建议逻辑：
   - 计算预测期末涨跌幅
   - 计算当前净值在历史分布中的分位数
   - 涨跌幅 > 3% 且分位数 < 30% → 买入
   - 涨跌幅 < -3% 且分位数 > 70% → 卖出
   - 其他 → 持有
4. 生成理由文本（包含数据支撑）
5. 附加免责声明："投资有风险，决策需谨慎，本建议不构成投资指导"
6. 预测数据异常时返回无法生成建议的提示

**验收标准**：
- 返回 StrategyAdvice 包含 action、reason、disclaimer
- action 仅允许"买入"/"卖出"/"持有"
- disclaimer 为固定免责声明文本
- 预测异常时友好提示

---

## Task 10: 主界面模块

**目标**：实现 PyQt5 主界面，协调所有模块

**具体步骤**：
1. 创建 `src/ui/main_window.py`
2. 实现 `FundPredictorMainWindow(QMainWindow)`：
   - 顶部：基金代码输入框（QLineEdit）、模型选择下拉框（QComboBox：保守型/激进型）、开始分析按钮
   - 中部：QTabWidget（趋势图、回测对比、资金流向三个 Tab）
   - 底部：策略建议文本框（QTextEdit）、导出按钮、版本号标签
   - 状态栏：显示操作状态
3. 创建 `src/ui/analysis_worker.py`
4. 实现 `AnalysisWorker(QThread)`：
   - 在子线程中执行：数据获取 → 数据清洗 → 趋势预测 → 图表生成 → 策略建议
   - 通过信号槽传递进度和结果到主线程
5. 创建 `src/ui/progress_dialog.py`
6. 实现 `ProgressDialog`：展示分析各阶段进度
7. 图表嵌入：使用 matplotlib FigureCanvasQTAgg 后端
8. 导出功能：点击导出按钮弹出文件保存对话框，选择格式后保存

**验收标准**：
- 主界面正常显示，布局合理
- 输入基金代码点击分析后，子线程执行不阻塞 UI
- 三类图表在 Tab 中正确展示
- 策略建议文本正确显示
- 导出图片功能正常

---

## Task 11: 应用入口与打包配置

**目标**：完善入口脚本，配置 PyInstaller 打包

**具体步骤**：
1. 完善 `src/main.py`：
   - 启动时调用 EnvChecker 检测环境
   - 创建 QApplication 和 MainWindow
   - 异常捕获：全局异常处理，记录日志
2. 创建 `build.py` 或 `fund_predictor.spec`（PyInstaller 配置）：
   - 入口点：src/main.py
   - 输出：FundPredictor.exe
   - 单文件模式（--onefile）或单目录模式（--onedir）
   - 包含数据文件：中文字体等
   - 隐藏导入：akshare、torch 等动态加载的模块
3. 创建启动脚本 `run.bat`（开发环境直接运行）

**验收标准**：
- `python src/main.py` 能正常启动应用
- PyInstaller 打包生成 FundPredictor.exe
- 双击 .exe 能正常启动（无需手动安装 Python）

---

## Task 12: 集成测试与说明文档

**目标**：端到端测试，编写使用说明

**具体步骤**：
1. 创建 `tests/` 目录，编写集成测试：
   - 测试完整流程：输入基金代码 → 获取数据 → 清洗 → 预测 → 图表 → 建议
   - 测试异常场景：无效代码、网络中断、数据不足
2. 创建 `README.md` 使用说明：
   - 功能介绍
   - 安装与运行方式
   - 使用步骤（输入代码 → 选择模型 → 开始分析 → 查看结果 → 导出）
   - 常见问题解答
   - 风险提示免责声明
3. 验收标准逐项检查

**验收标准**：
- 完整流程测试通过
- 异常场景测试通过
- README.md 内容完整
