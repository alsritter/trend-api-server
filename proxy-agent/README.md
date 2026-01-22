# Proxy Agent - 家宽代理节点

家宽代理池系统的 Agent 端，运行在各个家宽服务器上，提供代理服务并向中控服务器上报状态。

## 功能特性

- ✅ 支持 HTTP 和 SOCKS5 代理
- ✅ 基于 3proxy 的高性能代理服务
- ✅ WebSocket 实时通信
- ✅ 自动心跳上报
- ✅ 跨平台支持（Windows / Linux）
- ✅ 自动获取公网 IP
- ✅ 远程控制（启停、重启）

## 系统要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- 3proxy（自动下载或手动安装）
- Windows 或 Linux 系统

## 快速开始

### 1. 安装依赖

使用 uv（推荐）：

```bash
# 安装 uv（如果还没有安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

或使用传统 pip：

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`：

```yaml
server:
  # 中控服务器地址
  master_url: "ws://your-master-server:8000/api/v1/proxy/agent/ws"
  # Agent 认证 Token（从中控服务器获取）
  auth_token: "your-auth-token-here"

agent:
  # Agent 名称（可选，默认使用主机名）
  name: "home-proxy-01"
  # 代理类型：http, socks5, both
  proxy_type: "both"
  # 代理端口
  proxy_port: 1080
  # 代理认证（可选）
  proxy_username: ""
  proxy_password: ""

heartbeat:
  # 心跳间隔（秒）
  interval: 30
```

### 3. 运行

使用 uv（推荐）：

```bash
# 前台运行
uv run python main.py

# 使用配置文件
uv run python main.py -c config.yaml

# 后台运行（Linux）
nohup uv run python main.py > agent.log 2>&1 &
```

或使用传统 python：

```bash
# 前台运行
python main.py

# 后台运行（Linux）
nohup python main.py > agent.log 2>&1 &

# Windows 服务方式（需要管理员权限）
python install_service.py
```

## 目录结构

```
proxy-agent/
├── main.py              # 主程序入口
├── config.yaml          # 配置文件
├── pyproject.toml       # 项目配置（uv）
├── uv.lock             # 依赖锁定文件
├── agent/               # Agent 核心模块
│   ├── __init__.py
│   ├── proxy_manager.py # 3proxy 管理器
│   ├── websocket_client.py # WebSocket 客户端
│   ├── heartbeat.py     # 心跳上报
│   └── utils.py         # 工具函数
├── 3proxy/              # 3proxy 可执行文件目录
│   ├── 3proxy.exe       # Windows 版本
│   └── 3proxy          # Linux 版本
└── requirements.txt     # Python 依赖（向后兼容）
```

## 命令说明

### 主程序命令

使用 uv：

```bash
# 使用默认配置启动
uv run python main.py

# 指定配置文件
uv run python main.py -c /path/to/config.yaml

# 查看版本
uv run python main.py -v
```

或使用传统 python：

```bash
# 启动 Agent
python main.py start

# 停止 Agent
python main.py stop

# 查看状态
python main.py status

# 测试代理
python main.py test
```

### Windows 服务命令

```bash
# 安装服务
python install_service.py install

# 启动服务
python install_service.py start

# 停止服务
python install_service.py stop

# 卸载服务
python install_service.py remove
```

## 代理配置

Agent 会自动生成 3proxy 配置文件 `3proxy.cfg`：

- HTTP 代理端口：与配置中的 `proxy_port` 相同
- SOCKS5 代理端口：与配置中的 `proxy_port` 相同
- 认证：支持用户名/密码认证（如果配置）

## 故障排查

### 1. 连接中控服务器失败

- 检查 `master_url` 是否正确
- 检查网络连接
- 检查防火墙设置
- 检查 `auth_token` 是否有效

### 2. 代理服务启动失败

- 检查端口是否被占用
- 检查 3proxy 是否有执行权限（Linux: `chmod +x 3proxy`）
- 查看 3proxy 日志文件

### 3. 心跳上报失败

- 检查 WebSocket 连接状态
- 查看 Agent 日志
- 检查中控服务器状态

## 日志文件

- Agent 日志：`agent.log`
- 3proxy 日志：`3proxy/3proxy.log`

## 安全建议

1. 使用强认证 Token
2. 启用代理用户名/密码认证
3. 限制代理访问的目标地址
4. 定期更新代理密码
5. 监控异常流量

## License

NON-COMMERCIAL LEARNING LICENSE 1.1
