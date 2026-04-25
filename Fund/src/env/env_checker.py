"""环境检测模块 - 启动时检查依赖完整性并自动安装"""

import importlib
import subprocess
import sys
from pathlib import Path


class EnvironmentChecker:
    """环境检测与依赖自动安装"""

    # 核心依赖列表 (包名, import名)
    REQUIRED_PACKAGES = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("PyQt5", "PyQt5"),
        ("akshare", "akshare"),
        ("sklearn", "sklearn"),
        ("statsmodels", "statsmodels"),
    ]

    # 可选依赖 (Prophet/LSTM 等高级模型需要)
    OPTIONAL_PACKAGES = [
        ("torch", "torch"),
        ("prophet", "prophet"),
    ]

    def __init__(self):
        self.missing_packages = []
        self.installed_packages = []
        self.failed_packages = []

    def check_package(self, package_name: str, import_name: str = None) -> bool:
        """检测单个包是否已安装"""
        import_name = import_name or package_name
        try:
            importlib.import_module(import_name)
            return True
        except ImportError:
            return False

    def install_package(self, package_name: str) -> bool:
        """自动安装单个包"""
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def check_and_install(self) -> bool:
        """检测所有依赖，缺失则自动安装。返回是否全部就绪"""
        # 检查核心依赖
        for pkg_name, import_name in self.REQUIRED_PACKAGES:
            if not self.check_package(pkg_name, import_name):
                self.missing_packages.append(pkg_name)

        # 检查可选依赖
        for pkg_name, import_name in self.OPTIONAL_PACKAGES:
            if not self.check_package(pkg_name, import_name):
                self.missing_packages.append(pkg_name)

        if not self.missing_packages:
            return True

        # 尝试自动安装缺失的依赖
        for pkg_name in self.missing_packages:
            if self.install_package(pkg_name):
                self.installed_packages.append(pkg_name)
            else:
                self.failed_packages.append(pkg_name)

        return len(self.failed_packages) == 0

    def get_install_command(self) -> str:
        """获取手动安装命令"""
        req_file = Path(__file__).parent.parent.parent / "requirements.txt"
        return f'pip install -r "{req_file}"'

    def get_status_message(self) -> str:
        """获取环境状态描述"""
        if not self.missing_packages:
            return "所有依赖已就绪"

        parts = []
        if self.installed_packages:
            parts.append(f"已自动安装: {', '.join(self.installed_packages)}")
        if self.failed_packages:
            parts.append(
                f"安装失败: {', '.join(self.failed_packages)}\n"
                f"请手动执行: {self.get_install_command()}"
            )
        return "\n".join(parts)
