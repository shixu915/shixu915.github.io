"""基金趋势预测工具 - 应用入口"""

import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont


def show_error_box(title, message):
    """显示错误对话框（在 QApplication 之前也可用）"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
    except Exception:
        print(f"[ERROR] {title}: {message}")


def check_environment():
    """检测并安装依赖环境"""
    from src.env.env_checker import EnvironmentChecker

    checker = EnvironmentChecker()
    success = checker.check_and_install()

    if not success:
        msg = (
            f"部分依赖安装失败，可能影响功能使用。\n\n"
            f"{checker.get_status_message()}\n\n"
            f"是否继续启动？"
        )
        reply = QMessageBox.warning(
            None, "环境检测",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return False

    return True


def global_exception_handler(exc_type, exc_value, exc_tb):
    """全局异常处理"""
    from src.utils.logger import setup_logger
    logger = setup_logger("global")

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"未捕获异常:\n{error_msg}")

    # 非忽略的异常才弹窗
    if exc_type is not KeyboardInterrupt:
        try:
            QMessageBox.critical(
                None, "程序异常",
                f"程序发生未预期错误:\n{exc_value}\n\n详细信息已记录到日志文件。"
            )
        except Exception:
            pass


def main():
    """主入口函数"""
    # 设置高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 全局异常处理
    sys.excepthook = global_exception_handler

    # 显示启动画面
    splash = QSplashScreen()
    splash_pix = QPixmap(400, 200)
    splash_pix.fill(QColor("#2196F3"))
    painter = QPainter(splash_pix)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignCenter, "基金趋势预测工具\n正在启动...")
    painter.end()
    splash.setPixmap(splash_pix)
    splash.show()
    app.processEvents()

    # 环境检测
    try:
        if not check_environment():
            splash.close()
            sys.exit(0)
    except Exception as e:
        splash.close()
        show_error_box("启动失败", f"环境检测失败:\n{e}")
        sys.exit(1)

    # 导入并创建主窗口
    try:
        from src.ui.main_window import FundPredictorMainWindow
        window = FundPredictorMainWindow()
    except Exception as e:
        splash.close()
        show_error_box("启动失败", f"主界面创建失败:\n{e}\n\n请检查依赖是否完整安装。")
        sys.exit(1)

    splash.finish(window)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
