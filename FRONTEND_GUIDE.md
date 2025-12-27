# Trend API Server - 前端管理系统开发指南

## 项目状态

### ✅ 已完成

#### 后端 API (100%)
- ✅ IP 代理配置管理工具 ([app/utils/config_manager.py](app/utils/config_manager.py))
- ✅ IP 代理 Schema ([app/schemas/proxy.py](app/schemas/proxy.py))
- ✅ IP 代理 API 端点 ([app/api/v1/proxy.py](app/api/v1/proxy.py))
  - `GET /api/v1/proxy/config` - 获取代理配置
  - `PUT /api/v1/proxy/config` - 更新代理配置
  - `GET /api/v1/proxy/ips` - 获取 IP 池列表
  - `POST /api/v1/proxy/validate` - 验证单个 IP
  - `DELETE /api/v1/proxy/ips` - 清空 IP 池
  - `GET /api/v1/proxy/stats` - 获取 IP 统计
- ✅ FastAPI 静态文件服务配置 ([app/main.py](app/main.py:54))
- ✅ 环境变量配置 ([.env.example](.env.example:31-42))

#### 前端基础架构 (70%)
- ✅ 项目配置 (package.json, tsconfig.json, vite.config.ts)
- ✅ API 客户端完整封装 (src/api/)
- ✅ 布局组件 (Layout, Sidebar, Header)
- ✅ 路由配置 (React Router v6)
- ✅ TypeScript 类型定义
- ✅ 工具函数库

#### 功能页面
- ✅ **仪表盘** (100%) - 系统健康监控、数据统计
- ✅ **账号管理** (100%) - CRUD 完整功能
- 🚧 **IP 池管理** (20%) - 占位符页面
- 🚧 **任务管理** (20%) - 占位符页面
- 🚧 **数据查看** (20%) - 占位符页面

### 🚧 待完成

- IP 池管理详细功能 (优先级: P0)
- 任务管理详细功能 (优先级: P1)
- 数据查看详细功能 (优先级: P1)
- Dockerfile 更新 (优先级: P1)

## 快速开始

### 1. 安装前端依赖

```bash
cd trend-admin-web
npm install
```

### 2. 启动开发服务器

**方式一：分离启动（推荐用于开发）**

终端 1 - 启动后端:
```bash
# 在 trend-api-server 目录
uvicorn app.main:app --reload --port 8000
```

终端 2 - 启动前端:
```bash
# 在 trend-admin-web 目录
npm run dev
```

访问: http://localhost:3000

**方式二：生产模式**

```bash
# 1. 构建前端
cd trend-admin-web
npm run build

# 2. 启动后端（会自动serve前端）
cd ..
uvicorn app.main:app --port 8000
```

访问: http://localhost:8000

### 3. 测试后端 API

访问 Swagger UI: http://localhost:8000/docs

测试新增的 IP 代理 API：
1. `GET /api/v1/proxy/config` - 获取当前配置
2. `GET /api/v1/proxy/stats` - 查看 IP 统计

## API 文档

所有 API 都有完整的 OpenAPI 文档，访问 `/docs` 查看。

### 新增的 IP 代理 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/proxy/config` | 获取代理配置 |
| PUT | `/api/v1/proxy/config` | 更新代理配置 |
| GET | `/api/v1/proxy/ips` | 获取 IP 池列表（分页）|
| POST | `/api/v1/proxy/validate` | 验证单个 IP |
| DELETE | `/api/v1/proxy/ips` | 清空 IP 池 |
| GET | `/api/v1/proxy/stats` | 获取 IP 统计 |

## 前端开发指南

详细的前端开发指南请查看 [trend-admin-web/README.md](trend-admin-web/README.md)

### 核心技术栈
- React 18 + TypeScript
- Ant Design 5.x
- React Router v6
- TanStack Query (React Query)
- Axios
- Vite

### 项目结构

```
trend-admin-web/
├── src/
│   ├── api/           # ✅ API 客户端（完整）
│   ├── components/    # ✅ 布局组件（完整）
│   ├── pages/         # 🚧 页面组件（部分完成）
│   ├── types/         # ✅ TypeScript 类型
│   ├── utils/         # ✅ 工具函数
│   ├── App.tsx        # ✅ 主应用
│   ├── main.tsx       # ✅ 入口文件
│   └── routes.tsx     # ✅ 路由配置
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 下一步开发建议

### 优先级 P0：完成 IP 池管理页面

这是最核心的新功能，建议创建以下文件：

```
src/pages/Proxy/
├── index.tsx           # 主页面布局
├── ProxyConfig.tsx     # 配置表单组件
├── ProxyList.tsx       # IP 列表组件
└── ProxyStats.tsx      # 统计卡片组件
```

参考实现请查看 [trend-admin-web/README.md](trend-admin-web/README.md#1-完成-ip-池管理页面-优先级-p0)

### 优先级 P1：完成任务管理和数据查看

参考已完成的账号管理页面实现模式。

### 优先级 P1：更新 Dockerfile

添加前端构建步骤到 Docker 镜像构建流程。

## 常见问题

### 1. 如何测试 IP 代理 API？

```bash
# 1. 获取配置
curl http://localhost:8000/api/v1/proxy/config

# 2. 更新配置
curl -X PUT http://localhost:8000/api/v1/proxy/config \
  -H "Content-Type: application/json" \
  -d '{"enable_ip_proxy": true, "ip_proxy_pool_count": 10}'

# 3. 获取 IP 统计
curl http://localhost:8000/api/v1/proxy/stats
```

### 2. 如何添加新的 API 端点？

1. 在 `app/schemas/` 创建 Schema
2. 在 `app/api/v1/` 创建 API 路由
3. 在 `app/main.py` 注册路由
4. 在前端 `src/api/` 创建对应的 API 调用函数

### 3. 前端如何调用新的 API？

```typescript
import { useQuery } from '@tanstack/react-query'
import { proxyApi } from '@/api/proxy'

const { data, isLoading } = useQuery({
  queryKey: ['proxyConfig'],
  queryFn: proxyApi.getConfig,
})
```

## 文件清单

### 后端新增文件 (3)
- [app/utils/config_manager.py](app/utils/config_manager.py) - 配置管理工具
- [app/schemas/proxy.py](app/schemas/proxy.py) - IP 代理 Schema
- [app/api/v1/proxy.py](app/api/v1/proxy.py) - IP 代理 API

### 后端修改文件 (2)
- [app/main.py](app/main.py) - 添加静态文件服务和 proxy 路由
- [.env.example](.env.example) - 添加 IP 代理配置

### 前端新增文件 (约 30+)
完整列表请查看 [trend-admin-web/](trend-admin-web/)

## License

MIT License
