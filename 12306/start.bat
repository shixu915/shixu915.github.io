@echo off
chcp 65001 >nul
title 小鲁班抢票助手

echo ========================================
echo   小鲁班抢票助手 - 一键启动
echo ========================================
echo.

REM 检查Node.js是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查npm是否可用
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] npm不可用
    pause
    exit /b 1
)

REM 运行环境检查脚本
node scripts\check-environment.js

pause
