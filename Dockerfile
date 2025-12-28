# 使用多阶段构建，从官方 Node.js 镜像获取 Node.js 和 npm
FROM node:18-slim AS nodejs

# 前端构建阶段
FROM node:18-slim AS frontend-builder
WORKDIR /app
COPY trend-admin-web ./trend-admin-web
WORKDIR /app/trend-admin-web
RUN npm ci
RUN npm run build

# Python 基础镜像
FROM python:3.11-slim

WORKDIR /app

# 从 Node.js 镜像复制 Node.js 和 npm（SignSrv 需要）
COPY --from=nodejs /usr/local/bin/node /usr/local/bin/
COPY --from=nodejs /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=nodejs /usr/local/bin/npm /usr/local/bin/
COPY --from=nodejs /usr/local/bin/npx /usr/local/bin/

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libffi-dev \
    supervisor \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制 MediaCrawlerPro-Python (从子模块)
COPY MediaCrawlerPro-Python /app/MediaCrawlerPro-Python

# 安装 MediaCrawlerPro-Python 依赖
WORKDIR /app/MediaCrawlerPro-Python
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制 MediaCrawlerPro-SignSrv (从子模块)
COPY MediaCrawlerPro-SignSrv /app/MediaCrawlerPro-SignSrv

# 安装 MediaCrawlerPro-SignSrv 依赖
WORKDIR /app/MediaCrawlerPro-SignSrv
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制 trend-api-server
COPY . /app/trend-api-server
WORKDIR /app/trend-api-server

# 安装 API Server 依赖
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制前端构建产物
COPY --from=frontend-builder /app/static/web /app/trend-api-server/static/web

# 创建日志目录
RUN mkdir -p /var/log/trend-api-server /var/log/supervisor

# 复制 supervisor 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 8000 8989

# 设置环境变量
ENV PYTHONPATH="/app/MediaCrawlerPro-Python:/app/MediaCrawlerPro-SignSrv:/app/trend-api-server"
ENV PYTHONUNBUFFERED=1

# 使用 supervisor 启动多进程
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
