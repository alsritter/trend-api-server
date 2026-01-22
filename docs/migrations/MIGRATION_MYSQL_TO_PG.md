# 代理池数据库迁移指南

从 MySQL 迁移到 PostgreSQL

## 更新日期
2026-01-22

## 迁移概述

代理池系统已从 MySQL (`aiomysql`) 迁移到 PostgreSQL (`asyncpg`)，使用与向量数据库相同的 `pg_pool` 连接池。

## 已修改的文件

### 1. 服务层
- **文件**: `app/proxy_pool/service.py`
- **改动**:
  - 将 `import aiomysql` 改为 `import asyncpg`
  - 将 `aiomysql.Pool` 改为 `asyncpg.Pool`
  - 移除所有游标操作，改为直接查询
  - 将占位符从 `%s` 改为 `$1, $2, ...`
  - 使用 `dict(row)` 将 asyncpg.Record 转换为字典
  - 使用 `RETURNING *` 获取插入的完整行
  - 使用 `NULLS LAST` 处理 NULL 排序

### 2. 调度器
- **文件**: `app/proxy_pool/scheduler.py`
- **改动**:
  - 更新 `check_offline_agents` 方法，使用 PostgreSQL 语法
  - 从 `conn.execute()` 的返回值解析受影响的行数

### 3. API 路由
- **文件**: `app/api/v1/home_proxy.py`
- **改动**:
  - 将 `get_proxy_service` 中的 `db_pool` 改为 `pg_pool`
  - 将 WebSocket 端点中的 `db_pool` 改为 `pg_pool`

### 4. 数据库表结构
- **新文件**: `docs/migrations/home_proxy_pool_schema_pg.sql`
- **内容**: PostgreSQL 版本的表结构
  - `proxy_agents`: 代理节点表
  - `proxy_health_log`: 健康检查日志表
  - `proxy_usage_log`: 使用记录表

## 主要语法差异

### MySQL vs PostgreSQL

| 功能 | MySQL | PostgreSQL |
|------|-------|------------|
| 自增主键 | `BIGINT UNSIGNED AUTO_INCREMENT` | `BIGSERIAL` |
| 布尔值 | `TINYINT(1)` | `BOOLEAN` |
| 日期时间 | `DATETIME` | `TIMESTAMP` |
| 无符号整数 | `INT UNSIGNED` | `INTEGER` (无 UNSIGNED) |
| 占位符 | `%s` | `$1, $2, ...` |
| 返回插入值 | `lastrowid` | `RETURNING *` |
| 更新触发器 | `ON UPDATE CURRENT_TIMESTAMP` | 需创建触发器函数 |
| NULL 排序 | 默认行为 | 需显式指定 `NULLS LAST` |

### Python 代码差异

#### MySQL (aiomysql)
```python
async with conn.cursor(aiomysql.DictCursor) as cursor:
    await cursor.execute("SELECT * FROM table WHERE id = %s", (id,))
    row = await cursor.fetchone()
    return dict(row) if row else None
```

#### PostgreSQL (asyncpg)
```python
row = await conn.fetchrow("SELECT * FROM table WHERE id = $1", id)
return ProxyAgent(**dict(row)) if row else None
```

## 数据迁移步骤

### 1. 创建 PostgreSQL 表结构

```bash
# 连接到 PostgreSQL 数据库
psql -h localhost -U postgres -d your_database

# 执行表结构 SQL
\i docs/migrations/home_proxy_pool_schema_pg.sql
```

### 2. 迁移现有数据（如果需要）

如果你有现有的 MySQL 数据需要迁移，可以使用以下方法：

```bash
# 1. 从 MySQL 导出数据
mysqldump -u user -p --no-create-info --skip-triggers \
  database_name proxy_agents proxy_health_log proxy_usage_log > data.sql

# 2. 转换 SQL 语法（可能需要手动调整）
# - 将 AUTO_INCREMENT 改为 SERIAL
# - 调整数据类型
# - 修改日期格式

# 3. 导入到 PostgreSQL
psql -U user -d database_name -f data_converted.sql
```

### 3. 验证迁移

启动服务后检查：
- API 文档: http://localhost:8000/docs
- 测试代理池接口是否正常工作
- 检查日志中是否有数据库错误

## 配置检查

确保以下环境变量正确配置：

```env
# PostgreSQL 配置
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=your_password
PGVECTOR_DB=your_database
```

## 注意事项

1. **连接池**: 代理池现在使用 `pg_pool`，与向量数据库共享连接池
2. **并发**: asyncpg 的并发性能通常优于 aiomysql
3. **类型安全**: asyncpg 提供更严格的类型检查
4. **参数化查询**: 必须使用 `$1, $2` 而不是 `%s`
5. **NULL 处理**: PostgreSQL 对 NULL 的排序需要显式指定

## 回滚方案

如果需要回滚到 MySQL：

1. 恢复备份的 `service.py.bak` 文件
2. 修改 `app/api/v1/home_proxy.py` 中的 `pg_pool` 为 `db_pool`
3. 修改 `app/main.py` 中的初始化代码
4. 重启服务

## 测试清单

- [ ] 创建 Agent
- [ ] 获取 Agent 列表
- [ ] 更新 Agent
- [ ] 删除 Agent
- [ ] 获取代理
- [ ] 心跳更新
- [ ] 健康检查调度器
- [ ] WebSocket 连接
- [ ] 统计信息获取

## 相关文件

- `app/proxy_pool/service.py` - 服务层实现
- `app/proxy_pool/scheduler.py` - 健康检查调度器
- `app/api/v1/home_proxy.py` - API 路由
- `docs/migrations/home_proxy_pool_schema_pg.sql` - PostgreSQL 表结构
- `docs/migrations/home_proxy_pool_schema.sql` - MySQL 表结构（旧）
