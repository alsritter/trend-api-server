# 时区处理使用指南

## 概述

本项目统一使用 **Asia/Shanghai (UTC+8)** 时区。为了确保时间数据的一致性，提供了 `app.utils.timezone` 工具模块。

## 主要修复

### 1. MySQL 连接时区配置

在 `app/db/session.py` 中，MySQL 连接池已配置时区参数：

```python
db_pool = await aiomysql.create_pool(
    # ... 其他参数 ...
    init_command="SET time_zone='+08:00'",  # 设置为东8区
)
```

这确保：
- 从数据库读取的 `DATETIME` 值会被正确解释为东8区时间
- 写入数据库的 `DATETIME` 值会被正确存储为东8区时间

### 2. 时区工具函数

导入方式：

```python
from app.utils import timezone as tz
```

## 使用场景

### 场景 1：获取当前时间（用于 API 响应）

**推荐使用带时区的 datetime**：

```python
from app.utils import timezone as tz

# ✅ 推荐：获取带时区的当前时间
current_time = tz.now()  # datetime with tzinfo=UTC+8
# 序列化结果: "2025-01-01T12:30:45+08:00"
```

**不推荐的方式**（会导致前端误解时区）：

```python
# ❌ 不推荐：无时区信息
current_time = datetime.now()
# 序列化结果: "2025-01-01T12:30:45" （前端无法知道是哪个时区）
```

### 场景 2：数据库操作（DATETIME 列）

由于数据库连接已设置时区，可以直接使用 naive datetime：

```python
from app.utils import timezone as tz

# 获取不带时区的当前时间（用于数据库 DATETIME 列）
current_time = tz.now_naive()

# 写入数据库
await cursor.execute(
    "INSERT INTO tasks (started_at) VALUES (%s)",
    (current_time,)
)

# 从数据库读取后，可以转换为带时区的 datetime
await cursor.execute("SELECT started_at FROM tasks WHERE id = %s", (task_id,))
row = await cursor.fetchone()

# 为读取的时间添加时区信息
started_at = tz.to_china_tz(row['started_at'])
```

### 场景 3：Unix 时间戳转换

```python
from app.utils import timezone as tz

# 时间戳转 datetime（毫秒级）
timestamp_ms = 1704096645000
dt = tz.timestamp_to_datetime(timestamp_ms, is_milliseconds=True)
# 结果: datetime with Asia/Shanghai timezone

# datetime 转时间戳（毫秒级）
dt = tz.now()
timestamp_ms = tz.datetime_to_timestamp(dt, in_milliseconds=True)
```

### 场景 4：Pydantic Schema 中的时间字段

**方式 1：使用带时区的 datetime（推荐用于 API 响应）**

```python
from datetime import datetime
from pydantic import BaseModel, Field
from app.utils import timezone as tz

class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    created_at: datetime = Field(default_factory=tz.now)  # 带时区
    started_at: Optional[datetime] = None

    class Config:
        # Pydantic v2 自动序列化为 ISO 8601 格式
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
```

API 响应示例：
```json
{
    "task_id": "abc123",
    "created_at": "2025-01-01T12:30:45+08:00",  // ✅ 包含时区信息
    "started_at": null
}
```

**方式 2：使用字符串类型（当前项目中的常见方式）**

```python
from pydantic import BaseModel
from app.utils import timezone as tz

class TaskCreateResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: str
    created_at: str  # ISO 8601 字符串

# 在 API 端点中使用
@router.post("/create")
async def create_task():
    task_id = generate_id()
    return TaskCreateResponse(
        task_id=task_id,
        status="pending",
        created_at=tz.now().isoformat()  # "2025-01-01T12:30:45+08:00"
    )
```

### 场景 5：时区转换

```python
from datetime import datetime, timezone
from app.utils import timezone as tz

# UTC 时间转东8区
utc_time = datetime.now(timezone.utc)
china_time = tz.utc_to_china(utc_time)

# 任意时区的 datetime 转东8区
some_dt = datetime.now()  # naive datetime
china_dt = tz.to_china_tz(some_dt)
```

## 迁移指南

### 需要修改的代码模式

#### 1. API 响应中的时间字段

**修改前：**
```python
return {
    "created_at": datetime.now().isoformat()  # 无时区信息
}
```

**修改后：**
```python
from app.utils import timezone as tz

return {
    "created_at": tz.now().isoformat()  # 带时区信息: +08:00
}
```

#### 2. 数据库时间操作

**修改前：**
```python
from datetime import datetime

started_at = datetime.now()
await cursor.execute(
    "UPDATE tasks SET started_at = %s WHERE id = %s",
    (started_at, task_id)
)
```

**修改后：**
```python
from app.utils import timezone as tz

# 使用 now_naive() 与数据库 DATETIME 兼容
started_at = tz.now_naive()
await cursor.execute(
    "UPDATE tasks SET started_at = %s WHERE id = %s",
    (started_at, task_id)
)
```

#### 3. Celery 任务中的时间处理

**修改前：**
```python
from datetime import datetime

await cursor.execute(
    "UPDATE tasks SET finished_at = %s WHERE task_id = %s",
    (datetime.now(), task_id)
)
```

**修改后：**
```python
from app.utils import timezone as tz

await cursor.execute(
    "UPDATE tasks SET finished_at = %s WHERE task_id = %s",
    (tz.now_naive(), task_id)
)
```

## 测试时区配置

可以通过以下 API 端点测试时区是否正确：

```bash
# 获取当前服务器时间
curl http://localhost:8000/api/v1/health

# 查看任务的时间字段
curl http://localhost:8000/api/v1/tasks/list

# 查看热点的时间字段
curl http://localhost:8000/api/v1/hotspots/list
```

检查返回的时间字符串是否包含 `+08:00` 时区标识。

## 常见问题

### Q1: 为什么有些地方用 `now()`，有些地方用 `now_naive()`？

**A:**
- `tz.now()` 返回带时区的 datetime，用于 **API 响应**（让前端知道准确时区）
- `tz.now_naive()` 返回不带时区的 datetime，用于 **数据库操作**（MySQL DATETIME 类型不存储时区信息）

### Q2: 数据库中的 DATETIME 如何保证是东8区？

**A:** 通过 MySQL 连接的 `init_command="SET time_zone='+08:00'"` 参数，确保：
1. 写入的 naive datetime 被解释为东8区时间
2. 读取的 DATETIME 值返回为东8区时间

### Q3: 前端如何处理带时区的时间字符串？

**A:** 前端收到如 `"2025-01-01T12:30:45+08:00"` 的时间字符串后：

```javascript
// JavaScript 自动解析 ISO 8601 时间
const date = new Date("2025-01-01T12:30:45+08:00");

// 转换为用户本地时区显示
console.log(date.toLocaleString());  // 自动转换为用户时区

// 或使用 dayjs/moment.js
import dayjs from 'dayjs';
const formatted = dayjs("2025-01-01T12:30:45+08:00").format("YYYY-MM-DD HH:mm:ss");
```

### Q4: Celery 的时区配置还需要吗？

**A:** 需要保留。Celery 配置中的 `timezone="Asia/Shanghai"` 确保：
- Celery Beat 调度任务的时间正确
- ETA（预计执行时间）计算正确
- 任务日志的时间戳正确

## 总结

- ✅ **Docker 环境变量**: `ENV TZ=Asia/Shanghai`
- ✅ **MySQL 连接**: `init_command="SET time_zone='+08:00'"`
- ✅ **Celery 配置**: `timezone="Asia/Shanghai"`
- ✅ **API 响应**: 使用 `tz.now()` 返回带时区的 datetime
- ✅ **数据库操作**: 使用 `tz.now_naive()` 与 DATETIME 类型兼容
- ✅ **时间戳转换**: 使用 `tz.timestamp_to_datetime()` 和 `tz.datetime_to_timestamp()`

遵循这些规范，可以确保整个系统的时间数据一致性，避免时区混乱。
