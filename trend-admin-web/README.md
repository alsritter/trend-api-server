# Trend Admin Web - 前端管理系统

这是 Trend API Server 的前端管理界面，基于 React + Ant Design + TypeScript 构建。

## 技术栈

- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5.x
- **路由**: React Router v6
- **状态管理**: TanStack Query (React Query)
- **HTTP 客户端**: Axios
- **构建工具**: Vite
- **图表库**: ECharts

## 已完成的功能

### ✅ 完整功能
1. **项目基础架构**
   - Vite 配置
   - TypeScript 配置
   - 路由配置
   - API 客户端封装

2. **布局组件**
   - 主布局 (AppLayout)
   - 侧边栏导航 (Sidebar)
   - 顶部栏 (Header)

3. **仪表盘 (Dashboard)**
   - 系统健康状态监控
   - 数据统计展示
   - 平台数据详情

4. **账号管理 (Accounts)**
   - 账号列表展示
   - 新增账号
   - 删除账号
   - 状态管理

### 🚧 待完善的功能

以下功能已创建占位符，需要进一步开发：

1. **IP 池管理 (Proxy)** ⭐ 核心功能
   - 代理配置表单
   - IP 列表展示
   - IP 验证测试
   - 统计信息

2. **任务管理 (Tasks)**
   - 创建爬虫任务
   - 任务列表
   - 任务进度跟踪
   - 任务停止

3. **数据查看 (Contents)**
   - 平台切换
   - 内容列表
   - 数据筛选
   - 统计图表

## 快速开始

### 1. 安装依赖

```bash
cd trend-admin-web
npm install
```

### 2. 开发模式

```bash
npm run dev
```

访问: http://localhost:3000

前端会自动代理 `/api` 请求到 `http://localhost:8000`

### 3. 生产构建

```bash
npm run build
```

构建产物会输出到 `../static/web` 目录，可被 FastAPI 直接serve。

## 项目结构

```
src/
├── api/                    # API 调用层
│   ├── client.ts          # Axios 配置
│   ├── accounts.ts        # 账号 API
│   ├── proxy.ts           # IP 代理 API
│   ├── tasks.ts           # 任务 API
│   ├── system.ts          # 系统 API
│   └── contents.ts        # 内容 API
├── components/
│   └── Layout/            # 布局组件
│       ├── AppLayout.tsx
│       ├── Sidebar.tsx
│       └── Header.tsx
├── pages/                 # 页面组件
│   ├── Dashboard/         # ✅ 仪表盘
│   ├── Accounts/          # ✅ 账号管理
│   ├── Proxy/             # 🚧 IP 池管理
│   ├── Tasks/             # 🚧 任务管理
│   └── Contents/          # 🚧 数据查看
├── types/                 # TypeScript 类型
│   └── api.ts
├── utils/                 # 工具函数
│   ├── constants.ts
│   └── format.ts
├── App.tsx                # 应用根组件
├── main.tsx               # 应用入口
└── routes.tsx             # 路由配置
```

## 开发指南

### 添加新页面

1. 在 `src/pages/` 创建新页面目录
2. 创建 `index.tsx` 组件
3. 在 `src/routes.tsx` 中添加路由
4. 在 `src/components/Layout/Sidebar.tsx` 中添加菜单项

### 调用 API

使用 React Query 进行数据获取：

```typescript
import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'

const { data, isLoading } = useQuery({
  queryKey: ['accounts'],
  queryFn: () => accountsApi.list({ page: 1, page_size: 20 }),
})
```

### 路由导航

```typescript
import { useNavigate } from 'react-router-dom'

const navigate = useNavigate()
navigate('/accounts')
```

## 环境变量

- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

## 下一步开发建议

### 1. 完成 IP 池管理页面 (优先级: P0)

这是最核心的新功能，需要实现：

**组件结构**:
```
pages/Proxy/
├── index.tsx           # 主页面
├── ProxyConfig.tsx     # 配置表单组件
├── ProxyList.tsx       # IP 列表组件
└── ProxyStats.tsx      # 统计卡片组件
```

**主要功能**:
- [ ] 代理配置表单 (enable_ip_proxy, ip_proxy_pool_count, 快代理凭证)
- [ ] IP 列表展示 (表格 + 分页)
- [ ] IP 验证功能 (单个 IP 验证)
- [ ] IP 统计卡片 (总数、有效数、过期数)
- [ ] 清空 IP 池功能 (二次确认)

**参考代码**:
```typescript
// 获取配置
const { data: config } = useQuery({
  queryKey: ['proxyConfig'],
  queryFn: proxyApi.getConfig,
})

// 更新配置
const updateMutation = useMutation({
  mutationFn: proxyApi.updateConfig,
  onSuccess: () => {
    message.success('配置更新成功！请重启 Celery Worker')
    queryClient.invalidateQueries({ queryKey: ['proxyConfig'] })
  },
})
```

### 2. 完成任务管理页面 (优先级: P1)

**组件结构**:
```
pages/Tasks/
├── index.tsx          # 主页面
├── TaskList.tsx       # 任务列表
├── CreateTaskForm.tsx # 创建任务表单
└── TaskDetail.tsx     # 任务详情（可选）
```

**主要功能**:
- [ ] 创建任务表单 (platform, crawler_type, keywords, 配置项)
- [ ] 任务列表 (Table + 状态筛选)
- [ ] 任务进度实时更新 (useQuery + refetchInterval)
- [ ] 停止任务功能

**实时进度更新示例**:
```typescript
const { data: taskStatus } = useQuery({
  queryKey: ['taskStatus', taskId],
  queryFn: () => tasksApi.getStatus(taskId),
  refetchInterval: (data) => {
    const running = ['PENDING', 'STARTED', 'PROGRESS'].includes(data?.status)
    return running ? 3000 : false  // 运行中每 3 秒刷新
  },
  enabled: !!taskId,
})
```

### 3. 完成数据查看页面 (优先级: P1)

**组件结构**:
```
pages/Contents/
├── index.tsx         # 主页面
├── ContentList.tsx   # 内容列表
└── ContentFilter.tsx # 筛选器
```

**主要功能**:
- [ ] 平台切换 (Tabs)
- [ ] 内容列表展示 (动态列，根据平台不同)
- [ ] 关键词搜索
- [ ] 日期范围筛选
- [ ] 数据统计图表 (ECharts)

### 4. UI/UX 优化 (优先级: P2)

- [ ] 添加 Loading 状态
- [ ] 添加空状态占位
- [ ] 优化错误提示
- [ ] 添加确认对话框
- [ ] 响应式布局适配

### 5. 性能优化 (优先级: P2)

- [ ] 代码分割 (React.lazy)
- [ ] 路由懒加载
- [ ] 图片懒加载
- [ ] Bundle 分析优化

## 常见问题

### 1. API 请求跨域问题

开发环境已配置代理，生产环境需要确保 FastAPI 的 CORS 配置正确。

### 2. 构建失败

确保 Node.js 版本 >= 16，并且所有依赖已正确安装。

### 3. 类型错误

运行 `npm run build` 会进行类型检查，修复所有 TypeScript 错误。

## License

This project is licensed under the MIT License.
