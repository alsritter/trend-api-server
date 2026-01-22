# 家宽代理池系统

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-NON--COMMERCIAL-red)](LICENSE)

一套完整的**家宽代理池管理系统**，用于管理多个家宽 IP 节点，提供统一的代理服务。

## ✨ 特性

- ✅ **中控服务器**：统一管理所有代理节点
- ✅ **Agent 节点**：基于 3proxy 的高性能代理服务
- ✅ **WebSocket 通信**：实时心跳和指令下发
- ✅ **健康检查**：自动检测代理可用性
- ✅ **负载均衡**：智能分配代理请求
- ✅ **跨平台支持**：Windows / Linux
- ✅ **Web 管理界面**：可视化管理代理节点
- ✅ **无���对接**：与 MediaCrawlerPro 完美集成

## 📊 系统架构

```
中控服务器 (FastAPI)
    ├── API 服务 (HTTP/WebSocket)
    ├── 代理池管理
    ├── 健康检查调度器
    └── MySQL 数据存储

Agent 节点 (Python + 3proxy)
    ├── WebSocket 客户端
    ├── 心跳管理器
    ├── 代理服务 (HTTP/SOCKS5)
    └── 3proxy 进程管理

业务系统 (MediaCrawlerPro)
    └── 代理池接口对接
```

## 🚀 快速开始

### 1. 部署中控服务器

```bash
# 初始化数据库
mysql -u root -p < docs/migrations/home_proxy_pool_schema.sql

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 API 文档: http://localhost:8000/docs

### 2. 部署 Agent 节点

```bash
cd proxy-agent

# 安装依赖
pip install -r requirements.txt

# 配置
cp config.yaml.example config.yaml
# 编辑 config.yaml:
# - 设置 master_url (中控服务器地址)
# - 设置 auth_token (从中控服务器生成)

# 下载 3proxy (Windows 用户需手动下载)
# Linux: apt install 3proxy

# 启动
python main.py
```

### 3. 业务对接

在 MediaCrawlerPro 中配置：

```python
# config/base_config.py
ENABLE_IP_PROXY = True
IP_PROXY_PROVIDER_NAME = "home_proxy_pool"
IP_PROXY_POOL_COUNT = 5
```

## 📚 文档

- [部署和使用指南](docs/deployment-guide.md) - 完整的部署教程
- [前端实现指南](docs/frontend-guide.md) - 前端页面开发文档
- [API 文档](http://localhost:8000/docs) - 在线 API 文档

## 📁 项目结构

```
trend-api-server/
├── app/                          # 中控服务器代码
│   ├── proxy_pool/              # 代理池管理模块
│   │   ├── models.py           # 数据模型
│   │   ├── service.py          # 业务逻辑
│   │   ├── scheduler.py        # 健康检查
│   │   └── __init__.py
│   ├── api/v1/
│   │   └── home_proxy.py       # API 路由
│   └── main.py                  # 主程序
│
├── proxy-agent/                  # Agent 节点代码
│   ├── agent/                   # Agent 核心模块
│   │   ├── proxy_manager.py    # 3proxy 管理
│   │   ├── websocket_client.py # WebSocket 客户端
│   │   ├── heartbeat.py        # 心跳管理
│   │   └── utils.py            # 工具函数
│   ├── main.py                  # 主程序
│   ├── config.yaml              # 配置文件
│   └── README.md
│
├── MediaCrawlerPro-Python/       # 业务系统对接
│   └── pkg/proxy/providers/
│       └── home_proxy_pool.py   # 家宽代理提供商
│
├── docs/                         # 文档
│   ├── deployment-guide.md      # 部署指南
│   ├── frontend-guide.md        # 前端指南
│   └── migrations/
│       └── home_proxy_pool_schema.sql  # 数据库表结构
│
└── README.md                     # 本文件
```

## 🔧 配置说明

### 中控服务器配置 (.env)

```env
# 数据库配置
RELATION_DB_HOST=localhost
RELATION_DB_PORT=3306
RELATION_DB_USER=trend
RELATION_DB_PWD=password
RELATION_DB_NAME=trend_collector

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
```

### Agent 配置 (proxy-agent/config.yaml)

```yaml
server:
  master_url: "ws://localhost:8000/api/v1/home-proxy/agent/ws"
  auth_token: "your-token-here"

agent:
  name: "home-proxy-01"
  proxy_type: "both"      # http, socks5, both
  proxy_port: 1080

heartbeat:
  interval: 30            # 心跳间隔（秒）
```

## 🎯 核心功能

### 1. Agent 管理

- 注册和认证
- 状态监控
- 远程控制（启停、重启）
- 配置更新

### 2. 代理服务

- HTTP 代理
- SOCKS5 代理
- 用户认证
- 自动负载均衡

### 3. 健康检查

- 定期可用性检测
- 延迟监控
- 失败统计
- 自动下线

### 4. 数据统计

- 代理使用量
- 成功率统计
- 性能指标
- 日志记录

## 🔌 API 接口

### 获取代理

```bash
curl http://localhost:8000/api/v1/home-proxy/proxy/get
```

响应:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "proxy": "http://user:pass@1.2.3.4:1080",
    "agent_id": "uuid",
    "proxy_type": "http"
  }
}
```

### 标记失败

```bash
curl -X POST "http://localhost:8000/api/v1/home-proxy/proxy/mark_failed?agent_id=uuid"
```

### Agent 列表

```bash
curl http://localhost:8000/api/v1/home-proxy/agents?page=1&page_size=20
```

### 统计信息

```bash
curl http://localhost:8000/api/v1/home-proxy/stats
```

更多接口请参考: http://localhost:8000/docs

## 🖥️ Web 管理界面

管理界面提供以下功能：

1. **代理节点管理**
   - 查看所有节点状态
   - 新增/编辑/删除节点
   - 启停/重启代理服务
   - 下载配置文件

2. **统计信息面板**
   - 实时状态统计
   - 使用量趋势图
   - 成功率分析
   - 延迟分布

3. **日志查询**
   - 使用日志
   - 健康检查日志
   - 按条件筛选和导出

详见 [前端实现指南](docs/frontend-guide.md)

## 📦 数据库表结构

### proxy_agents (代理节点表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| agent_id | VARCHAR | Agent UUID |
| agent_name | VARCHAR | Agent 名称 |
| public_ip | VARCHAR | 公网 IP |
| proxy_port | INT | 代理端口 |
| status | VARCHAR | 状态 (online/offline/disabled) |
| last_heartbeat | DATETIME | 最后心跳时间 |

### proxy_health_log (健康检查日志)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| agent_id | VARCHAR | Agent ID |
| is_available | TINYINT | 是否可用 |
| latency | INT | 延迟(ms) |
| check_time | DATETIME | 检查时间 |

### proxy_usage_log (使用记录)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| agent_id | VARCHAR | Agent ID |
| platform | VARCHAR | 平台 |
| is_success | TINYINT | 是否成功 |
| used_at | DATETIME | 使用时间 |

## 🔐 安全建议

1. 使用强 Token（32+ 字符）
2. 启用代理认证
3. 限制访问 IP
4. 使用 HTTPS/WSS
5. 定期轮换凭证
6. 监控异常流量

## 🐛 故障排查

### Agent 连接失败

```bash
# 检查网络
ping your-server.com

# 检查端口
telnet your-server.com 8000

# 查看 Agent 日志
tail -f proxy-agent/agent.log
```

### 3proxy 启动失败

```bash
# Linux: 授予执行权限
chmod +x proxy-agent/3proxy/3proxy

# 检查端口占用
sudo lsof -i :1080

# 手动测试
./proxy-agent/3proxy/3proxy proxy-agent/3proxy.cfg
```

更多问题请参考 [部署指南 - 故障排查](docs/deployment-guide.md#故障排查)

## 📊 性能指标

- **支持 Agent 数量**: 100+
- **单 Agent QPS**: 100+
- **心跳延迟**: < 5s
- **健康检查周期**: 60s
- **数据库并发**: 20 连接

## 🗺️ 路线图

- [ ] WebSocket 实时推送
- [ ] 智能调度算法
- [ ] 自动故障转移
- [ ] 地域负载均衡
- [ ] 告警通知系统
- [ ] 更多代理协议支持

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

NON-COMMERCIAL LEARNING LICENSE 1.1

仅供学习和研究使用，不得用于商业用途。

## 👥 作者

Trend Collector Team

## 📮 联系

- Email: support@example.com
- GitHub: https://github.com/your-repo

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
