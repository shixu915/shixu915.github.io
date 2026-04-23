#!/bin/bash

echo "========================================"
echo "  小鲁班抢票助手 - 一键启动"
echo "========================================"
echo ""

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "[错误] 未检测到Node.js，请先安装Node.js"
    echo "下载地址: https://nodejs.org/"
    exit 1
fi

# 检查npm是否可用
if ! command -v npm &> /dev/null; then
    echo "[错误] npm不可用"
    exit 1
fi

# 运行环境检查脚本
node scripts/check-environment.js
