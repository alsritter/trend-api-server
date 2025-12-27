FROM python:3.9.19-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libffi-dev \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制 MediaCrawlerPro-Python (从子模块)
COPY MediaCrawlerPro-Python /app/MediaCrawlerPro-Python

# 安装 MediaCrawlerPro-Python 依赖
WORKDIR /app/MediaCrawlerPro-Python
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制 trend-api-server
COPY . /app/trend-api-server
WORKDIR /app/trend-api-server

# 安装 API Server 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 创建日志目录
RUN mkdir -p /var/log/trend-api-server /var/log/supervisor

# 复制 supervisor 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH="/app/MediaCrawlerPro-Python:/app/trend-api-server"
ENV PYTHONUNBUFFERED=1

# 使用 supervisor 启动多进程
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
