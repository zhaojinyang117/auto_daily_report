#!/bin/bash

# 安装uv（如果没有安装）
if ! command -v uv &> /dev/null; then
    echo "正在安装uv包管理器..."
    curl -fsSL https://astral.sh/uv/install.sh | bash
fi

# 创建虚拟环境并安装依赖
echo "正在创建虚拟环境并安装依赖..."
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 创建日志文件
touch email_logs.txt

echo "环境设置完成！请使用 'source .venv/bin/activate' 激活环境" 