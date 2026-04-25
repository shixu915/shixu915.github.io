"""进度对话框 - 展示分析流程各阶段进度"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt


class ProgressDialog(QDialog):
    """分析进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分析进度")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        # 状态标签
        self.status_label = QLabel("准备开始分析...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        self._cancelled = False

    def update_progress(self, message: str, percent: int):
        """更新进度"""
        self.status_label.setText(message)
        self.progress_bar.setValue(min(percent, 100))

        if percent >= 100:
            self.cancel_btn.setText("完成")

    def is_cancelled(self) -> bool:
        return self._cancelled
