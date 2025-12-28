# Trend API Server

MediaCrawlerPro API Server - 多平台社交媒体数据采集 HTTP API 服务

## 项目简介

Trend API Server 是对 MediaCrawlerPro-Python 爬虫的 HTTP API 封装，提供异步任务调度、账号管理、内容查询等功能。

## 依赖管理

本项目使用 [uv](https://docs.astral.sh/uv/) 作为依赖管理工具，相比传统的 pip，uv 提供：
- ⚡ 10-100倍更快的安装速度
- 🔒 更可靠的依赖解析
- 📦 统一的 pyproject.toml 配置

### 安装 uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**或使用 Homebrew:**
```bash
brew install uv
```

详细迁移说明请参考 [UV_MIGRATION.md](UV_MIGRATION.md)

## Git 子模块管理

本项目使用 git 子模块 (submodules) 来管理依赖项目：

- `MediaCrawlerPro-Python` - 多平台社交媒体爬虫核心
- `MediaCrawlerPro-SignSrv` - 签名服务

### 首次克隆项目

```bash
# 克隆项目并同时初始化子模块
git clone --recurse-submodules <your-repo-url>

# 或者先克隆，再初始化子模块
git clone <your-repo-url>
cd trend-api-server
git submodule update --init --recursive
```

### 更新子模块

```bash
# 更新所有子模块到最新版本
git submodule update --remote --merge

# 或者进入子模块目录手动更新
cd MediaCrawlerPro-Python
git pull origin main
cd ..
git add MediaCrawlerPro-Python
git commit -m "Update MediaCrawlerPro-Python submodule"
```

### 查看子模块状态

```bash
# 查看子模块状态
git submodule status

# 查看子模块配置
cat .gitmodules
```

## 主要功能

- **Web 管理界面**：基于 React + Ant Design 的前端管理系统
  - 仪表盘：系统健康监控、数据统计图表
  - 账号管理：爬虫账号增删改查
  - IP 池管理：代理配置、IP 列表查看、验证
  - 任务管理：创建任务、查看进度、停止任务
  - 数据查看：多平台内容数据查询和筛选
- **异步任务管理**：通过 Celery 异步执行爬虫任务，支持任务状态查询和停止
- **账号配置管理**：通过 API 管理爬虫账号 Cookies 和状态
- **内容查询**：查询已爬取的内容（笔记/视频）、评论、创作者信息
- **系统监控**：监控系统健康状态、Celery 队列、数据库统计
- **IP 代理管理**：配置和管理代理 IP 池

## 技术栈

**后端**：
- **Web 框架**：FastAPI 0.109.0
- **异步任务队列**：Celery 5.3.4 + Redis
- **数据库**：MySQL 8.0（共享 MediaCrawlerPro-Python 数据库）
- **进程管理**：Supervisor
- **容器化**：Docker + Docker Compose

**前端**：
- **框架**：React 18 + TypeScript
- **UI 组件库**：Ant Design 5.x
- **路由**：React Router v6
- **状态管理**：TanStack Query (React Query) + Zustand
- **HTTP 客户端**：Axios
- **图表库**：ECharts
- **构建工具**：Vite

## 支持的平台

- 小红书 (xhs)
- 抖音 (dy)
- 快手 (ks)
- B站 (bili)
- 微博 (wb)
- 百度贴吧 (tieba)
- 知乎 (zhihu)

## 快速开始

### 本地开发环境

1. **克隆项目（包含子模块）**

```bash
git clone --recurse-submodules <your-repo-url>
cd trend-api-server
```

2. **安装依赖**

使用 Makefile（推荐）：
```bash
make install
```

或直接使用 uv：
```bash
# uv sync 会自动创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

3. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接信息
```

4. **启动依赖服务**（使用 MediaCrawlerPro-Python 的 docker-compose）

```bash
cd MediaCrawlerPro-Python
docker-compose up -d db redis signsrv
```

5. **初始化数据库**（如果还没初始化）

```bash
cd MediaCrawlerPro-Python
python db.py
```

6. **启动 API 服务**

```bash
cd ..  # 返回 trend-api-server 目录
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **启动 Celery Worker**（新终端）

```bash
celery -A app.celery_app.celery worker --loglevel=info -Q crawler_queue,control_queue
```

8. **访问 Web 管理界面**

打开浏览器访问: [http://localhost:8000](http://localhost:8000)

9. **访问 API 文档**

打开浏览器访问: [http://localhost:8000/docs](http://localhost:8000/docs)

### Docker 部署

1. **构建并启动所有服务**

```bash
cd trend-api-server
docker build -t trend-api-server .
# 前端会在 Docker 构建过程中自动编译并集成到镜像中
```

2. **访问服务**

- Web 管理界面: [http://localhost:8000](http://localhost:8000)
- API 文档: [http://localhost:8000/docs](http://localhost:8000/docs)

3. **查看日志**

```bash
docker logs -f <container-id>
```

4. **停止服务**

```bash
docker stop <container-id>
```

## API 接口文档

启动服务后，访问以下地址查看完整的 API 文档：

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 核心 API 端点

#### 1. 任务管理

- `POST /api/v1/tasks` - 创建爬虫任务
- `GET /api/v1/tasks/{task_id}` - 查询任务状态
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `GET /api/v1/tasks` - 查询任务列表

#### 2. 账号管理

- `POST /api/v1/accounts` - 创建账号
- `GET /api/v1/accounts` - 查询账号列表
- `GET /api/v1/accounts/{id}` - 查询单个账号
- `PUT /api/v1/accounts/{id}` - 更新账号
- `DELETE /api/v1/accounts/{id}` - 删除账号

#### 3. 内容查询

- `GET /api/v1/contents/{platform}/notes` - 查询内容列表
- `GET /api/v1/contents/{platform}/comments` - 查询评论
- `GET /api/v1/contents/{platform}/creators/{user_id}` - 查询创作者信息

#### 4. 系统监控

- `GET /api/v1/health` - 健康检查
- `GET /api/v1/system/health` - 系统状态
- `GET /api/v1/system/celery/stats` - Celery 队列状态
- `GET /api/v1/system/database/stats` - 数据库统计

#### 5. IP 代理管理

- `GET /api/v1/proxy/config` - 获取代理配置
- `PUT /api/v1/proxy/config` - 更新代理配置
- `GET /api/v1/proxy/ips` - 获取 IP 池列表
- `POST /api/v1/proxy/validate` - 验证单个 IP
- `DELETE /api/v1/proxy/ips` - 清空 IP 池
- `GET /api/v1/proxy/stats` - 获取 IP 统计

## 使用示例

### 创建爬虫任务

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xhs",
    "crawler_type": "search",
    "keywords": "AI,ChatGPT",
    "enable_checkpoint": true,
    "max_notes_count": 10,
    "enable_comments": true
  }'
```

响应：

```json
{
  "code": 0,
  "message": "Task created successfully",
  "data": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "PENDING",
    "created_at": "2025-12-27T10:00:00Z"
  }
}
```

### 查询任务状态

```bash
curl "http://localhost:8000/api/v1/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### 创建账号

```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "xhs_account_1",
    "platform_name": "xhs",
    "cookies": "session=xxx; token=yyy"
  }'
```

### 查询爬取结果

```bash
curl "http://localhost:8000/api/v1/contents/xhs/notes?keyword=AI&page=1&page_size=20"
```

## 项目结构

```
trend-api-server/
├── app/
│   ├── api/v1/              # API 路由
│   │   ├── tasks.py         # 任务管理
│   │   ├── accounts.py      # 账号管理
│   │   ├── contents.py      # 内容查询
│   │   ├── system.py        # 系统监控
│   │   ├── proxy.py         # IP 代理管理 (新)
│   │   └── health.py        # 健康检查
│   ├── celery_app/          # Celery 配置
│   │   ├── celery.py        # Celery 实例
│   │   └── tasks/           # 任务定义
│   │       └── crawler_tasks.py
│   ├── db/                  # 数据库层
│   │   └── session.py       # 会话管理
│   ├── schemas/             # Pydantic 模型
│   │   ├── task.py
│   │   ├── account.py
│   │   ├── content.py
│   │   ├── proxy.py         # IP 代理模型 (新)
│   │   └── common.py
│   ├── utils/               # 工具类
│   │   └── config_manager.py  # 配置管理 (新)
│   ├── config.py            # 配置管理
│   ├── dependencies.py      # 依赖注入
│   └── main.py              # 应用入口
├── trend-admin-web/         # 前端项目 (新)
│   ├── src/
│   │   ├── api/            # API 调用层
│   │   ├── components/     # 组件
│   │   │   ├── Layout/     # 布局组件
│   │   │   ├── Charts/     # 图表组件
│   │   │   └── Common/     # 通用组件
│   │   ├── pages/          # 页面
│   │   │   ├── Dashboard/  # 仪表盘
│   │   │   ├── Accounts/   # 账号管理
│   │   │   ├── Proxy/      # IP 池管理
│   │   │   ├── Tasks/      # 任务管理
│   │   │   └── Contents/   # 数据查看
│   │   ├── hooks/          # 自定义 Hooks
│   │   ├── store/          # 状态管理
│   │   ├── types/          # TypeScript 类型
│   │   ├── utils/          # 工具函数
│   │   └── App.tsx         # 应用入口
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── static/web/              # 前端构建产物 (自动生成)
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 镜像
├── .dockerignore            # Docker 忽略文件 (新)
├── supervisord.conf         # Supervisor 配置
├── .env.example             # 环境变量示例
└── README.md                # 项目文档
```

## 环境变量配置

参考 [.env.example](.env.example) 文件：

```env
# API Server 配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# MySQL 数据库配置
RELATION_DB_HOST=localhost
RELATION_DB_PORT=3307
RELATION_DB_USER=root
RELATION_DB_PWD=123456
RELATION_DB_NAME=media_crawler_pro

# Redis 配置
REDIS_DB_HOST=localhost
REDIS_DB_PORT=6378
REDIS_DB_PWD=123456
REDIS_DB_NUM=0

# MediaCrawlerPro-Python 路径配置
CRAWLER_BASE_PATH=/app/MediaCrawlerPro-Python
CRAWLER_PYTHON_PATH=python

# 签名服务配置
SIGN_SRV_HOST=localhost
SIGN_SRV_PORT=8989
```

## 常见问题

### 1. 如何查看 Celery 任务状态？

使用 Flower 监控工具：

```bash
uv add flower
# 或在虚拟环境中
celery -A app.celery_app.celery flower --port=5555
```

访问 [http://localhost:5555](http://localhost:5555)

### 2. 如何调试爬虫任务？

查看 Celery Worker 日志：

```bash
# Docker 环境
docker-compose logs -f trend-api-server | grep celery

# 本地环境
# 查看终端输出
```

### 3. 数据库连接失败？

检查环境变量配置和 MySQL 服务状态：

```bash
# 检查 MySQL 是否运行
docker ps | grep mysql

# 测试连接
mysql -h localhost -P 3307 -u root -p123456
```

### 4. Redis 连接失败？

检查 Redis 服务状态：

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 测试连接
redis-cli -h localhost -p 6378 -a 123456 ping
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目仅供学习和研究使用

## 相关项目

- [MediaCrawlerPro-Python](./MediaCrawlerPro-Python) - 多平台社交媒体爬虫（子模块）
- [MediaCrawlerPro-SignSrv](./MediaCrawlerPro-SignSrv) - 签名服务（子模块）
