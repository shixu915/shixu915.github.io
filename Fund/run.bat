@echo off
chcp 65001 >nul
echo ========================================
echo   基金趋势预测工具 - 启动脚本
echo ========================================
echo.

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 安装依赖
echo [1/2] 检查并安装依赖...
pip install -r requirements.txt -q

REM 启动应用
echo [2/2] 启动应用...
python -m src.main

pause
