# 家宽代理池系统 - 部署和使用指南

## 目录

- [系统架构](#系统架构)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [中控服务器部署](#中控服务器部署)
- [Agent 节点部署](#agent-节点部署)
- [业务对接](#业务对接)
- [运维管理](#运维管理)
- [故障排查](#故障排查)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     中控服务器                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ FastAPI App  │  │ MySQL数据库   │  │ 健康检查器    │   │
│  │ (app)        │  │              │  │              │   │
│  └──────────────┘  └───────────���──┘  └──────────────┘   │
│         │                                                 │
│         │ WebSocket + HTTP API                           │
└─────────┼─────────────────────────────────────────────────┘
          │
    ┌─────┴─────┬─────────┬─────────┬─────────┐
    │           │         │         │         │
┌───▼───┐  ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Agent 1│  │Agent 2│ │Agent 3│ │Agent 4│ │Agent N│
│家宽IP1│  │家宽IP2│ │家宽IP3│ ���家宽IP4│ │家宽IPN│
└───────┘  └───────┘ └───────┘ └───────┘ └───────┘
   │          │         │         │         │
   └──────────┴─────────┴─────────┴─────────┘
              │
              ▼
      ┌───────────────┐
      │  3proxy 服务  │
      │ HTTP / SOCKS5 │
      └───────────────┘
              │
              ▼
      ┌───────────────┐
      │ 业务爬虫服务   │
      │MediaCrawlerPro│
      └───────────────┘
```

---

## 前置要求

### 中控服务器

- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+)
- **Python**: 3.8+
- **数据库**: MySQL 5.7+ 或 PostgreSQL 12+
- **内存**: 2GB+
- **磁盘**: 20GB+

### Agent 节点

- **操作系统**: Windows 10+ / Linux
- **Python**: 3.8+
- **网络**: 家宽 IP（非数据中心 IP）
- **内存**: 512MB+
- **磁盘**: 5GB+

---

## 快速开始

### 一、初始化数据库

```bash
# 1. 创建数据库
mysql -u root -p

CREATE DATABASE trend_collector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trend_collector;

# 2. 导入表结构
source docs/migrations/home_proxy_pool_schema.sql;
```

### 二、启动中控服务器

```bash
cd /path/to/trend-api-server

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（.env 文件）
# 确保数据库连接信息正确

# 3. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用 systemd 服务（推荐）
sudo systemctl start trend-api-server
```

### 三、部署 Agent 节点

```bash
cd /path/to/trend-api-server/proxy-agent

# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载 3proxy
# Windows: 下载 3proxy.exe 放到 3proxy/ 目录
# Linux:
wget https://github.com/3proxy/3proxy/releases/download/0.9.4/3proxy-0.9.4.x86_64.deb
sudo dpkg -i 3proxy-0.9.4.x86_64.deb

# 3. 配置 config.yaml
# - 设置中控服务器地址
# - 设置认证 Token（从中控服务器生成）

# 4. 启动 Agent
python main.py
```

---

## 中控服务器部署

### 1. 系统配置

#### 创建系统用户

```bash
sudo useradd -m -s /bin/bash trend
sudo su - trend
```

#### 安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server -y

# CentOS/RHEL
sudo yum install python3 python3-pip mysql-server -y
```

### 2. 项目部署

```bash
# 克隆项目
cd /home/trend
git clone <your-repo-url> trend-api-server
cd trend-api-server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置文件

创建 `.env` 文件：

```env
# 数据库配置
RELATION_DB_HOST=localhost
RELATION_DB_PORT=3306
RELATION_DB_USER=trend
RELATION_DB_PWD=your-password
RELATION_DB_NAME=trend_collector

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# Redis 配置（如果使用）
REDIS_DB_HOST=localhost
REDIS_DB_PORT=6379
REDIS_DB_PWD=
REDIS_DB_NUM=0

# 其他配置...
```

### 4. 数据库初始化

```bash
# 连接 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE trend_collector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'trend'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON trend_collector.* TO 'trend'@'localhost';
FLUSH PRIVILEGES;

# 导入表结构
USE trend_collector;
source docs/migrations/home_proxy_pool_schema.sql;
```

### 5. Systemd 服务配置

创建 `/etc/systemd/system/trend-api-server.service`：

```ini
[Unit]
Description=Trend API Server
After=network.target mysql.service

[Service]
Type=simple
User=trend
Group=trend
WorkingDirectory=/home/trend/trend-api-server
Environment="PATH=/home/trend/trend-api-server/venv/bin"
ExecStart=/home/trend/trend-api-server/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable trend-api-server
sudo systemctl start trend-api-server
sudo systemctl status trend-api-server
```

### 6. Nginx 反向代理（可选）

创建 `/etc/nginx/sites-available/trend-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/trend-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Agent 节点部署

### 1. Windows 部署

#### 安装 Python

下载并安装 Python 3.8+：
https://www.python.org/downloads/

#### 部署 Agent

```powershell
# 1. 复制 proxy-agent 目录到本地
# 例如: C:\proxy-agent

# 2. 打开 PowerShell，进入目录
cd C:\proxy-agent

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载 3proxy
# 从 https://github.com/3proxy/3proxy/releases 下载 Windows 版本
# 解压后将 3proxy.exe 放到 3proxy\ 目录

# 5. 编辑配置文件 config.yaml
notepad config.yaml

# 6. 运行测试
python main.py

# 7. 安装为 Windows 服务（可选）
python install_service.py install
python install_service.py start
```

#### Windows 服务管理

```powershell
# 启动服务
python install_service.py start

# 停止服务
python install_service.py stop

# 查看状态
python install_service.py status

# 卸载服务
python install_service.py remove
```

### 2. Linux 部署

#### 安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip -y

# CentOS/RHEL
sudo yum install python3 python3-pip -y
```

#### 安装 3proxy

```bash
# Ubuntu/Debian
wget https://github.com/3proxy/3proxy/releases/download/0.9.4/3proxy-0.9.4.x86_64.deb
sudo dpkg -i 3proxy-0.9.4.x86_64.deb

# 或从源码编译
git clone https://github.com/3proxy/3proxy.git
cd 3proxy
make -f Makefile.Linux
sudo cp bin/3proxy /usr/local/bin/
```

#### 部署 Agent

```bash
# 1. 复制 proxy-agent 目录
cd /opt
sudo git clone <repo-url>/proxy-agent
cd proxy-agent

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置
sudo nano config.yaml

# 4. 创建 systemd 服务
sudo nano /etc/systemd/system/proxy-agent.service
```

创建服务文件：

```ini
[Unit]
Description=Proxy Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/proxy-agent
ExecStart=/usr/bin/python3 /opt/proxy-agent/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable proxy-agent
sudo systemctl start proxy-agent
sudo systemctl status proxy-agent
```

### 3. Agent 配置详解

编辑 `config.yaml`：

```yaml
server:
  # 中控服务器 WebSocket 地址
  master_url: "ws://your-server.com:8000/api/v1/home-proxy/agent/ws"
  # 认证 Token（从中控服务器生成）
  auth_token: "your-generated-token-here"
  # 重连配置
  reconnect_interval: 5
  max_reconnect: 0  # 0 表示无限重连

agent:
  # Agent 名称（可选，默认使用主机名）
  name: "home-proxy-01"
  # 代理类型: http, socks5, both
  proxy_type: "both"
  # 代理端口
  proxy_port: 1080
  # 代理认证（可选，建议配置）
  proxy_username: "proxy_user"
  proxy_password: "secure_password"

heartbeat:
  # 心跳间隔（秒）
  interval: 30
  # 心跳超时（秒）
  timeout: 10

logging:
  level: "INFO"
  file: "agent.log"
  max_size: 10  # MB
  backup_count: 5

3proxy:
  executable: ""  # 留空自动检测
  config_file: "3proxy.cfg"
  log_file: "3proxy.log"
  auto_download: true
```

---

## 业务对接

### 1. MediaCrawlerPro 配置

编辑 MediaCrawlerPro 的配置文件（`config/base_config.py` 或 `.env`）：

```python
# 启用代理
ENABLE_IP_PROXY = True

# 使用家宽代理池
IP_PROXY_PROVIDER_NAME = "home_proxy_pool"

# 代理池大小
IP_PROXY_POOL_COUNT = 5
```

### 2. 使用示例

```python
from pkg.proxy.proxy_ip_pool import create_ip_pool

# 创建代理池
proxy_pool = await create_ip_pool(
    ip_pool_count=5,
    enable_validate_ip=True,
    ip_provider="home_proxy_pool"
)

# 获取代理
proxy_info = await proxy_pool.get_proxy()
print(f"代理地址: {proxy_info.ip}:{proxy_info.port}")

# 使用代理发起请求
proxy_url = proxy_info.format_httpx_proxy()
async with httpx.AsyncClient(proxy=proxy_url) as client:
    response = await client.get("https://example.com")

# 如果代理失败，标记为无效
if response.status_code != 200:
    await proxy_pool.mark_ip_invalid(proxy_info)
```

### 3. 直接调用 API

```python
import httpx

# 获取代理
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://your-server.com:8000/api/v1/home-proxy/proxy/get"
    )
    data = response.json()
    proxy_url = data["data"]["proxy"]
    agent_id = data["data"]["agent_id"]

# 使用代理
async with httpx.AsyncClient(proxy=proxy_url) as client:
    response = await client.get("https://example.com")

# 标记失败（如果需要）
if response.status_code != 200:
    await client.post(
        "http://your-server.com:8000/api/v1/home-proxy/proxy/mark_failed",
        params={"agent_id": agent_id}
    )
```

---

## 运维管理

### 1. 日常监控

#### 检查中控服务器状态

```bash
# 查看服务状态
sudo systemctl status trend-api-server

# 查看日志
sudo journalctl -u trend-api-server -f

# 查看 API 健康状态
curl http://localhost:8000/api/v1/health
```

#### 检查 Agent 状态

```bash
# Linux
sudo systemctl status proxy-agent
sudo journalctl -u proxy-agent -f

# Windows
python install_service.py status

# 查看日志
tail -f agent.log
```

#### 通过 API 查看状态

```bash
# 获取统计信息
curl http://your-server.com:8000/api/v1/home-proxy/stats

# 获取 Agent 列表
curl http://your-server.com:8000/api/v1/home-proxy/agents
```

### 2. 数据库维护

```sql
-- 清理旧的健康检查日志（保留最近 7 天）
DELETE FROM proxy_health_log
WHERE check_time < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 清理旧的使用日志（保留最近 30 天）
DELETE FROM proxy_usage_log
WHERE used_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 查看代理使用统计
SELECT
    agent_id,
    COUNT(*) as total_requests,
    SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) as success_count,
    ROUND(SUM(CASE WHEN is_success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM proxy_usage_log
WHERE used_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY agent_id;
```

### 3. 备份和恢复

```bash
# 备份数据库
mysqldump -u trend -p trend_collector > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u trend -p trend_collector < backup_20260122.sql

# 定时备份（crontab）
0 2 * * * mysqldump -u trend -p'password' trend_collector > /backup/trend_$(date +\%Y\%m\%d).sql
```

---

## 故障排查

### 问题 1: Agent 无法连接到中控服务器

**症状**: Agent 日志显示连接失败

**排查步骤**:
1. 检查网络连接: `ping your-server.com`
2. 检查端口是否开放: `telnet your-server.com 8000`
3. 检查防火墙规则
4. 检查 `config.yaml` 中的 `master_url` 是否正确
5. 检查认证 Token 是否有效

**解决方案**:
```bash
# 开放防火墙端口（中控服务器）
sudo ufw allow 8000/tcp

# 测试 WebSocket 连接
wscat -c ws://your-server.com:8000/api/v1/home-proxy/agent/ws
```

### 问题 2: 3proxy 启动失败

**症状**: Agent 日志显示 3proxy 启动失败

**排查步骤**:
1. 检查 3proxy 是否存在: `ls -la 3proxy/`
2. 检查执行权限 (Linux): `chmod +x 3proxy/3proxy`
3. 检查端口是否被占用: `netstat -tuln | grep 1080`
4. 查看 3proxy 日志: `cat 3proxy.log`

**解决方案**:
```bash
# Linux: 授予执行权限
chmod +x 3proxy/3proxy

# 检查端口占用
sudo lsof -i :1080
# 如果被占用，修改 config.yaml 中的 proxy_port

# 手动测试 3proxy
./3proxy/3proxy 3proxy.cfg
```

### 问题 3: 代理连接不稳定

**症状**: 业务方使用代理经常失败

**排查步骤**:
1. 检查 Agent 心跳是否正常
2. 检查网络延迟: `ping -c 10 agent-ip`
3. 查看健康检查日志
4. 检查家宽网络是否稳定

**解决方案**:
```bash
# 增加心跳频率（config.yaml）
heartbeat:
  interval: 15  # 改为 15 秒

# 查看健康检查记录
mysql> SELECT * FROM proxy_health_log
       WHERE agent_id = 'xxx'
       ORDER BY check_time DESC LIMIT 10;
```

### 问题 4: 数据库连接池耗尽

**症状**: API 响应缓慢或超时

**解决方案**:
```python
# 增加数据库连接池大小（app/db/session.py）
db_pool = await aiomysql.create_pool(
    ...
    maxsize=20,  # 增加到 20
    minsize=5,   # 增加最小连接数
    ...
)
```

### 问题 5: WebSocket 连接频繁断开

**症状**: Agent 日志显示频繁重连

**排查步骤**:
1. 检查网络稳定性
2. 检查中控服务器负载
3. 查看中控服务器日志

**解决方案**:
```yaml
# 调整 WebSocket 配置（agent/websocket_client.py）
self.websocket = await websockets.connect(
    self.master_url,
    extra_headers=headers,
    ping_interval=30,  # 增加 ping 间隔
    ping_timeout=20,   # 增加 ping 超时
)
```

---

## 安全建议

1. **使用强认证 Token**
   - 使用 32+ 字符的随机 Token
   - 定期轮换 Token

2. **启用代理认证**
   - 配置 `proxy_username` 和 `proxy_password`
   - 使用强密码

3. **限制访问**
   - 使用防火墙限制只允许特定 IP 访问
   - 使用 VPN 或专用网络

4. **启用 HTTPS/WSS**
   - 使用 Nginx 配置 SSL 证书
   - WebSocket 使用 WSS 协议

5. **监控异常流量**
   - 监控代理使用量
   - 设置异常告警

---

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_agent_status ON proxy_agents(status);
CREATE INDEX idx_last_heartbeat ON proxy_agents(last_heartbeat);
CREATE INDEX idx_health_agent_time ON proxy_health_log(agent_id, check_time);

-- 定期优化表
OPTIMIZE TABLE proxy_agents;
OPTIMIZE TABLE proxy_health_log;
OPTIMIZE TABLE proxy_usage_log;
```

### 2. 连接池优化

```python
# 增加数据库连接池
maxsize=20

# 增加 Agent 数量上限
# 根据服务器性能调整
```

### 3. 健康检查优化

```python
# 调整检查间隔（app/main.py）
proxy_health_checker = ProxyHealthChecker(
    proxy_service,
    check_interval=120  # 改为 2 分钟
)
```

---

## 附录

### A. API 文档

完整 API 文档：http://your-server.com:8000/docs

### B. 常用命令

```bash
# 中控服务器
systemctl status trend-api-server
systemctl restart trend-api-server
journalctl -u trend-api-server -f

# Agent
systemctl status proxy-agent
systemctl restart proxy-agent
journalctl -u proxy-agent -f

# 数据库
mysql -u trend -p trend_collector
SHOW TABLES;
SELECT COUNT(*) FROM proxy_agents;
```

### C. 配置文件模板

所有配置文件模板位于：
- 中控服务器: `.env.example`
- Agent: `proxy-agent/config.yaml.example`

---

## 联系支持

如有问题，请联系：
- 技术支持: support@example.com
- GitHub Issues: https://github.com/your-repo/issues

---

**版本**: v1.0.0
**更新时间**: 2026-01-22
**作者**: Trend Collector Team
