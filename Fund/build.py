"""PyInstaller 打包配置脚本

使用方法:
    python build.py

将生成 dist/FundPredictor.exe 可执行文件
"""

import subprocess
import sys
from pathlib import Path


def build():
    project_root = Path(__file__).parent

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FundPredictor",
        "--onedir",                    # 单目录模式（启动更快）
        "--windowed",                  # 无控制台窗口
        "--noconfirm",                 # 不确认覆盖
        "--clean",                     # 清理临时文件

        # 添加数据文件
        f"--add-data={project_root / 'requirements.txt'};.",

        # 隐藏导入（动态加载的模块）
        "--hidden-import=akshare",
        "--hidden-import=torch",
        "--hidden-import=sklearn",
        "--hidden-import=PyQt5",
        "--hidden-import=matplotlib",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=prophet",
        "--hidden-import=statsmodels",
        "--hidden-import=statsmodels.tsa",
        "--hidden-import=statsmodels.tsa.statespace",
        "--hidden-import=statsmodels.tsa.arima",

        # 排除不需要的大模块
        "--exclude-module=tkinter",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",

        # 入口脚本
        str(project_root / "src" / "main.py"),
    ]

    print("开始打包 FundPredictor.exe ...")
    print(f"命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(project_root))

    if result.returncode == 0:
        print("\n打包成功！")
        print(f"可执行文件位于: {project_root / 'dist' / 'FundPredictor' / 'FundPredictor.exe'}")
    else:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    build()
