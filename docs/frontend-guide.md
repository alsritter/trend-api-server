# 家宽代理池前端管理页面实现指南

## 一、页面结构

### 路由设置

在 trend-admin-web 中添加新的路由：

```javascript
// router/index.js
{
  path: '/proxy-pool',
  component: Layout,
  meta: { title: '代理管理', icon: 'network' },
  children: [
    {
      path: 'agents',
      component: () => import('@/views/proxy-pool/agents'),
      name: 'ProxyAgents',
      meta: { title: '代理节点', icon: 'server' }
    },
    {
      path: 'stats',
      component: () => import('@/views/proxy-pool/stats'),
      name: 'ProxyStats',
      meta: { title: '统计信息', icon: 'chart' }
    },
    {
      path: 'logs',
      component: () => import('@/views/proxy-pool/logs'),
      name: 'ProxyLogs',
      meta: { title: '使用日志', icon: 'document' }
    }
  ]
}
```

---

## 二、API 接口

### 基础 URL

```
http://localhost:8000/api/v1/home-proxy
```

### 主要接口列表

#### 1. 获取 Agent 列表

```http
GET /agents?status={status}&page={page}&page_size={page_size}
```

**参数：**
- `status` (可选): online, offline, disabled
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "agent_id": "uuid",
        "agent_name": "home-proxy-01",
        "public_ip": "1.2.3.4",
        "city": "Shanghai",
        "isp": "China Telecom",
        "proxy_type": "both",
        "proxy_port": 1080,
        "status": "online",
        "latency": 120,
        "last_heartbeat": "2026-01-22T10:00:00"
      }
    ]
  }
}
```

#### 2. 创建 Agent

```http
POST /agents
Content-Type: application/json

{
  "agent_id": "uuid",
  "agent_name": "home-proxy-01",
  "auth_token": "token",
  "proxy_type": "both",
  "proxy_port": 1080
}
```

#### 3. 更新 Agent

```http
PUT /agents/{agent_id}
Content-Type: application/json

{
  "status": "disabled",
  "proxy_port": 1081
}
```

#### 4. 删除 Agent

```http
DELETE /agents/{agent_id}
```

#### 5. 发送控制指令

```http
POST /agents/{agent_id}/command
Content-Type: application/json

{
  "action": "restart_proxy"
}
```

**支持的指令：**
- `enable_proxy`: 启用代理
- `disable_proxy`: 禁用代理
- `restart_proxy`: 重启代理
- `update_config`: 更新配置

#### 6. 获取统计信息

```http
GET /stats
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_agents": 10,
    "online_agents": 8,
    "offline_agents": 2,
    "disabled_agents": 0,
    "total_requests": 1000,
    "failed_requests": 50,
    "success_rate": 95.0
  }
}
```

#### 7. 生成 Token

```http
GET /token/generate
```

---

## 三、页面功能实现

### 1. Agent 列表页面

**功能点：**

✅ Agent 列表展示（表格）
- 支持分页
- 支持按状态筛选
- 实时状态显示（在线/离线/禁用）

✅ 操作按钮
- 启用/禁用代理
- 重启代理
- 编辑配置
- 删除 Agent
- 查看详情

✅ 状态指示器
- 在线：绿色
- 离线：灰色
- 禁用：红色
- 延迟显示（颜色编码）

✅ 新增 Agent
- 弹窗表单
- 自动生成 Token
- 下载配置文件

**示例代码（Vue 3）：**

```vue
<template>
  <div class="proxy-agents">
    <!-- 顶部操作栏 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filter.status" placeholder="筛选状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon> 新增 Agent
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Agent 列表 -->
    <el-card class="table-card">
      <el-table :data="agents" stripe style="width: 100%">
        <!-- 状态列 -->
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- Agent 信息 -->
        <el-table-column prop="agent_name" label="名称" width="150" />
        <el-table-column prop="public_ip" label="公网 IP" width="150" />
        <el-table-column label="位置" width="200">
          <template #default="{ row }">
            {{ row.city }} - {{ row.isp }}
          </template>
        </el-table-column>

        <!-- 代理配置 -->
        <el-table-column label="代理类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.proxy_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="proxy_port" label="端口" width="80" />

        <!-- 性能指标 -->
        <el-table-column label="延迟" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getLatencyType(row.latency)"
              size="small"
            >
              {{ row.latency ? `${row.latency}ms` : 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 最后心跳 -->
        <el-table-column label="最后心跳" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_heartbeat) }}
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                size="small"
                @click="restartProxy(row)"
                :disabled="row.status !== 'online'"
              >
                重启
              </el-button>
              <el-button
                size="small"
                :type="row.status === 'disabled' ? 'success' : 'warning'"
                @click="toggleStatus(row)"
              >
                {{ row.status === 'disabled' ? '启用' : '禁用' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteAgent(row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchAgents"
        @current-change="fetchAgents"
      />
    </el-card>

    <!-- 新增 Agent 对话框 -->
    <el-dialog
      v-model="createDialog.visible"
      title="新增 Agent"
      width="600px"
    >
      <el-form :model="createDialog.form" label-width="120px">
        <el-form-item label="Agent 名称">
          <el-input v-model="createDialog.form.agent_name" />
        </el-form-item>
        <el-form-item label="代理类型">
          <el-select v-model="createDialog.form.proxy_type">
            <el-option label="HTTP" value="http" />
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="Both" value="both" />
          </el-select>
        </el-form-item>
        <el-form-item label="代理端口">
          <el-input-number v-model="createDialog.form.proxy_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="认证用户名">
          <el-input v-model="createDialog.form.proxy_username" />
        </el-form-item>
        <el-form-item label="认证密码">
          <el-input v-model="createDialog.form.proxy_password" type="password" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="createAgent">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/api/proxy'

// 数据
const agents = ref([])
const filter = reactive({ status: '' })
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 对话框
const createDialog = reactive({
  visible: false,
  form: {
    agent_name: '',
    proxy_type: 'both',
    proxy_port: 1080,
    proxy_username: '',
    proxy_password: ''
  }
})

// 获取 Agent 列表
const fetchAgents = async () => {
  try {
    const res = await api.getAgents({
      status: filter.status,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    agents.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('获取 Agent 列表失败')
  }
}

// 状态类型
const getStatusType = (status) => {
  const map = {
    online: 'success',
    offline: 'info',
    disabled: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    online: '在线',
    offline: '离线',
    disabled: '禁用'
  }
  return map[status] || status
}

// 延迟类型
const getLatencyType = (latency) => {
  if (!latency) return 'info'
  if (latency < 100) return 'success'
  if (latency < 300) return 'warning'
  return 'danger'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return 'N/A'
  return new Date(time).toLocaleString()
}

// 重启代理
const restartProxy = async (agent) => {
  try {
    await api.sendCommand(agent.agent_id, { action: 'restart_proxy' })
    ElMessage.success('重启指令已发送')
  } catch (error) {
    ElMessage.error('发送指令失败')
  }
}

// 切换状态
const toggleStatus = async (agent) => {
  const newStatus = agent.status === 'disabled' ? 'online' : 'disabled'
  try {
    await api.updateAgent(agent.agent_id, { status: newStatus })
    ElMessage.success('状态已更新')
    fetchAgents()
  } catch (error) {
    ElMessage.error('更新状态失败')
  }
}

// 删除 Agent
const deleteAgent = async (agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 Agent "${agent.agent_name}" 吗？`,
      '警告',
      { type: 'warning' }
    )
    await api.deleteAgent(agent.agent_id)
    ElMessage.success('删除成功')
    fetchAgents()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 显示创建对话框
const showCreateDialog = async () => {
  // 生成 Token
  try {
    const res = await api.generateToken()
    createDialog.form.auth_token = res.data.token
    createDialog.visible = true
  } catch (error) {
    ElMessage.error('生成 Token 失败')
  }
}

// 创建 Agent
const createAgent = async () => {
  try {
    await api.createAgent(createDialog.form)
    ElMessage.success('创建成功')
    createDialog.visible = false
    fetchAgents()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 初始化
onMounted(() => {
  fetchAgents()
  // 自动刷新（每 30 秒）
  setInterval(fetchAgents, 30000)
})
</script>
```

### 2. 统计信息页面

**功能点：**
- 实时统计数据
- 图表展示（ECharts）
- 成功率趋势
- 延迟分布

### 3. 使用日志页面

**功能点：**
- 日志列表
- 按 Agent 筛选
- 按平台筛选
- 导出日志

---

## 四、API 客户端实现

```javascript
// api/proxy.js
import request from '@/utils/request'

const BASE_URL = '/api/v1/home-proxy'

export default {
  // 获取 Agent 列表
  getAgents(params) {
    return request({
      url: `${BASE_URL}/agents`,
      method: 'get',
      params
    })
  },

  // 创建 Agent
  createAgent(data) {
    return request({
      url: `${BASE_URL}/agents`,
      method: 'post',
      data
    })
  },

  // 更新 Agent
  updateAgent(agentId, data) {
    return request({
      url: `${BASE_URL}/agents/${agentId}`,
      method: 'put',
      data
    })
  },

  // 删除 Agent
  deleteAgent(agentId) {
    return request({
      url: `${BASE_URL}/agents/${agentId}`,
      method: 'delete'
    })
  },

  // 发送指令
  sendCommand(agentId, data) {
    return request({
      url: `${BASE_URL}/agents/${agentId}/command`,
      method: 'post',
      data
    })
  },

  // 获取统计信息
  getStats() {
    return request({
      url: `${BASE_URL}/stats`,
      method: 'get'
    })
  },

  // 生成 Token
  generateToken() {
    return request({
      url: `${BASE_URL}/token/generate`,
      method: 'get'
    })
  }
}
```

---

## 五、部署和配置

### 1. 环境变量配置

在 `.env` 文件中添加：

```env
# 家宽代理池 API 地址
VITE_PROXY_POOL_API=http://localhost:8000/api/v1/home-proxy
```

### 2. 构建和部署

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产
npm run build

# 部署到服务器
npm run deploy
```

---

## 六、后续优化

1. WebSocket 实时推送（Agent 状态变化）
2. 代理健康度评分系统
3. 智能调度算法
4. 自动故障转移
5. 地域负载均衡
6. 使用统计分析
7. 告警通知系统
