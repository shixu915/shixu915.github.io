"""主界面模块 - PyQt5 主窗口，协调所有模块"""

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QTabWidget, QFileDialog, QMessageBox, QStatusBar, QSplitter,
    QGroupBox, QProgressBar,
)
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QFont, QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import pandas as pd

from src.ui.analysis_worker import AnalysisWorker
from src.ui.progress_dialog import ProgressDialog
from src.chart.chart_generator import FundChartGenerator
from src.models.data_models import PredictionResult, BacktestResult, StrategyAdvice, FundInfo
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

VERSION = "2.0.0"


class FundPredictorMainWindow(QMainWindow):
    """基金趋势预测工具主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"基金趋势预测工具 v{VERSION}")
        self.setMinimumSize(1100, 750)

        # 数据存储
        self.history_data = {}       # {fund_code: DataFrame}
        self.prediction_data = {}    # {fund_code: PredictionResult}
        self.backtest_data = {}      # {fund_code: BacktestResult}
        self.advice_data = {}        # {fund_code: StrategyAdvice}
        self.fund_info_data = {}     # {fund_code: FundInfo}

        self.chart_generator = FundChartGenerator()
        self.worker = None

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ===== 顶部输入区域 =====
        input_group = QGroupBox("分析设置")
        input_layout = QHBoxLayout(input_group)

        # 基金代码输入
        input_layout.addWidget(QLabel("基金代码:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("输入6位基金代码，多个用逗号分隔，如 000001,110011")
        self.code_input.setMinimumWidth(350)
        input_layout.addWidget(self.code_input)

        # 模型选择
        input_layout.addWidget(QLabel("预测模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "集成 (Ensemble)",       # 推荐：加权组合多模型
            "保守型 (Prophet)",      # Prophet：趋势+季节性
            "统计型 (ARIMA)",        # ARIMA：经典统计
            "激进型 (LSTM)",         # LSTM：深度学习
            "多变量 (MultiVar-LSTM)",# 多变量LSTM：含市场指数
            "基础型 (MA)",           # MA：移动平均线
        ])
        self.model_combo.setCurrentIndex(0)  # 默认集成
        input_layout.addWidget(self.model_combo)

        # 开始分析按钮
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #BDBDBD; }"
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        input_layout.addWidget(self.analyze_btn)

        main_layout.addWidget(input_group)

        # ===== 中部结果区域 =====
        splitter = QSplitter(Qt.Vertical)

        # 图表选项卡
        self.tab_widget = QTabWidget()
        self.trend_tab = self._create_chart_tab()
        self.backtest_tab = self._create_chart_tab()
        self.flow_tab = self._create_chart_tab()

        self.tab_widget.addTab(self.trend_tab, "趋势预测图")
        self.tab_widget.addTab(self.backtest_tab, "回测对比图")
        self.tab_widget.addTab(self.flow_tab, "资金流向图")

        splitter.addWidget(self.tab_widget)

        # 策略建议区域
        advice_group = QGroupBox("策略建议")
        advice_layout = QVBoxLayout(advice_group)

        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        self.advice_text.setFont(QFont("Microsoft YaHei", 11))
        self.advice_text.setPlaceholderText("分析完成后，策略建议将显示在此处...")
        advice_layout.addWidget(self.advice_text)

        # 导出按钮
        export_layout = QHBoxLayout()
        self.export_png_btn = QPushButton("导出 PNG")
        self.export_png_btn.clicked.connect(lambda: self._on_export("png"))
        self.export_jpg_btn = QPushButton("导出 JPG")
        self.export_jpg_btn.clicked.connect(lambda: self._on_export("jpg"))
        export_layout.addWidget(self.export_png_btn)
        export_layout.addWidget(self.export_jpg_btn)
        export_layout.addStretch()
        advice_layout.addLayout(export_layout)

        splitter.addWidget(advice_group)
        splitter.setSizes([500, 200])

        main_layout.addWidget(splitter, stretch=1)

        # ===== 状态栏 =====
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 版本号标签
        version_label = QLabel(f"v{VERSION}")
        version_label.setStyleSheet("color: gray;")
        self.status_bar.addPermanentWidget(version_label)

    def _create_chart_tab(self) -> QWidget:
        """创建图表选项卡页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 占位 Figure
        fig = Figure(figsize=(12, 6), dpi=100)
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        widget.canvas = canvas
        widget.figure = fig
        widget.toolbar = toolbar

        return widget

    def _on_analyze(self):
        """点击开始分析按钮"""
        # 解析基金代码
        code_text = self.code_input.text().strip()
        if not code_text:
            QMessageBox.warning(self, "提示", "请输入基金代码")
            return

        # 支持逗号、空格、中文逗号分隔
        fund_codes = []
        for code in code_text.replace("，", ",").replace(" ", ",").split(","):
            code = code.strip()
            if code:
                if not code.isdigit() or len(code) != 6:
                    QMessageBox.warning(
                        self, "提示",
                        f"基金代码格式错误: {code}\n请输入6位数字代码"
                    )
                    return
                fund_codes.append(code)

        if not fund_codes:
            QMessageBox.warning(self, "提示", "请输入有效的基金代码")
            return

        # 获取模型类型
        model_type_map = {
            0: "Ensemble",
            1: "Prophet",
            2: "ARIMA",
            3: "LSTM",
            4: "MultiVar-LSTM",
            5: "MA",
        }
        model_type = model_type_map.get(self.model_combo.currentIndex(), "Ensemble")

        # 清空之前的结果
        self.history_data.clear()
        self.prediction_data.clear()
        self.backtest_data.clear()
        self.advice_data.clear()
        self.fund_info_data.clear()
        self.advice_text.clear()

        # 禁用分析按钮
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("分析中...")

        # 创建进度对话框
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.show()

        # 启动工作线程
        self.worker = AnalysisWorker(fund_codes, model_type)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.data_fetched.connect(self._on_data_fetched)
        self.worker.prediction_done.connect(self._on_prediction_done)
        self.worker.backtest_done.connect(self._on_backtest_done)
        self.worker.advice_done.connect(self._on_advice_done)
        self.worker.fund_info_ready.connect(self._on_fund_info_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.analysis_finished.connect(self._on_analysis_finished)
        self.worker.start()

    def _on_progress(self, message: str, percent: int):
        """进度更新"""
        self.progress_dialog.update_progress(message, percent)
        self.status_bar.showMessage(message)

    def _on_data_fetched(self, fund_code: str, df):
        """数据获取完成"""
        self.history_data[fund_code] = df
        logger.info(f"UI: 基金 {fund_code} 数据已接收")

    def _on_prediction_done(self, fund_code: str, result: PredictionResult):
        """预测完成 - 更新趋势图"""
        self.prediction_data[fund_code] = result

        if fund_code in self.history_data:
            fig = self.chart_generator.generate_trend_chart(
                self.history_data[fund_code], result
            )
            self._update_chart_tab(self.trend_tab, fig)

    def _on_backtest_done(self, fund_code: str, result: BacktestResult):
        """回测完成 - 更新回测图"""
        self.backtest_data[fund_code] = result

        fig = self.chart_generator.generate_backtest_chart(result)
        self._update_chart_tab(self.backtest_tab, fig)

    def _on_advice_done(self, fund_code: str, advice: StrategyAdvice):
        """建议完成 - 更新建议文本"""
        self.advice_data[fund_code] = advice

        # 获取基金名称
        fund_name = ""
        if fund_code in self.fund_info_data and self.fund_info_data[fund_code]:
            fund_name = self.fund_info_data[fund_code].name

        display_name = f"{fund_name} ({fund_code})" if fund_name else fund_code

        text = f"【{display_name}】\n"
        text += f"建议: {advice.action}\n"
        text += f"理由: {advice.reason}\n"
        text += f"\n⚠️ {advice.disclaimer}\n"
        text += "─" * 50 + "\n\n"

        # 追加到文本框
        current_text = self.advice_text.toPlainText()
        self.advice_text.setPlainText(current_text + text)

    def _on_fund_info_ready(self, fund_code: str, info: FundInfo):
        """基金信息就绪"""
        if info:
            self.fund_info_data[fund_code] = info

            # 更新资金流向图
            if fund_code in self.history_data:
                fig = self.chart_generator.generate_flow_chart(self.history_data[fund_code])
                self._update_chart_tab(self.flow_tab, fig)

    def _on_error(self, fund_code: str, error_msg: str):
        """错误处理"""
        logger.error(f"基金 {fund_code} 分析错误: {error_msg}")
        self.status_bar.showMessage(f"基金 {fund_code}: {error_msg}")

        # 追加错误信息到建议文本
        current_text = self.advice_text.toPlainText()
        self.advice_text.setPlainText(
            current_text + f"❌ 基金 {fund_code}: {error_msg}\n" + "─" * 50 + "\n\n"
        )

    def _on_analysis_finished(self):
        """全部分析完成"""
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("开始分析")
        self.progress_dialog.update_progress("分析完成", 100)
        self.progress_dialog.accept()
        self.status_bar.showMessage("分析完成")

    def _update_chart_tab(self, tab_widget, fig: Figure):
        """更新图表选项卡"""
        tab_widget.figure.clear()
        # 将新 figure 的内容复制到 tab 的 figure
        new_fig = fig
        tab_widget.figure = new_fig
        tab_widget.canvas.figure = new_fig
        tab_widget.canvas.draw()

    def _on_export(self, format: str):
        """导出当前图表"""
        current_tab = self.tab_widget.currentTab()
        if current_tab is None:
            return

        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())

        filter_str = "PNG 图片 (*.png)" if format == "png" else "JPG 图片 (*.jpg)"
        default_ext = ".png" if format == "png" else ".jpg"

        filepath, _ = QFileDialog.getSaveFileName(
            self, f"导出 {tab_name}", f"{tab_name}{default_ext}", filter_str
        )

        if filepath:
            success = self.chart_generator.export_chart(
                current_tab.figure, filepath, format
            )
            if success:
                QMessageBox.information(self, "导出成功", f"图表已保存至:\n{filepath}")
            else:
                QMessageBox.warning(self, "导出失败", "图表导出失败，请检查文件路径权限")
