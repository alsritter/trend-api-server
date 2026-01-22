#!/bin/bash
# Proxy Agent 启动脚本

# 使用 uv 运行
exec uv run python main.py "$@"
