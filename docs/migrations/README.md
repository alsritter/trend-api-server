# 代理池 PostgreSQL 迁移

## 快速开始

### 1. 创建数据库表

使用 Python 脚本自动创建：

```bash
cd /Users/alsritter/Documents/projects/code/trend-collector.com/trend-api-server
python docs/init_proxy_tables.py
```

或者手动执行 SQL：

```bash
# 连接到 PostgreSQL
psql -h localhost -p 5432 -U postgres -d your_database

# 执行 SQL 文件
\i docs/migrations/home_proxy_pool_schema_pg.sql

# 验证表创建
\dt proxy_*
```

### 2. 确认配置

检查 `.env` 文件中的 PostgreSQL 配置：

```env
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=your_password
PGVECTOR_DB=your_database
```

### 3. 启动服务

```bash
# 启动 API 服务器
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload
```

### 4. 验证

访问 API 文档：http://localhost:8000/docs

测试代理池接口：
- GET `/api/v1/home-proxy/agents` - 获取 Agent 列表
- GET `/api/v1/home-proxy/stats` - 获取统计信息
- POST `/api/v1/home-proxy/agents` - 创建 Agent

## 已完成的迁移

✅ `app/proxy_pool/service.py` - 服务层
✅ `app/proxy_pool/scheduler.py` - 调度器
✅ `app/api/v1/home_proxy.py` - API 路由
✅ PostgreSQL 表结构创建

## 注意事项

1. 代理池现在使用 `pg_pool` (PostgreSQL) 而不是 `db_pool` (MySQL)
2. 所有数据库查询已从 `aiomysql` 语法改为 `asyncpg` 语法
3. 参数占位符从 `%s` 改为 `$1, $2, ...`
4. 数据类型已适配 PostgreSQL

## 详细文档

查看完整迁移文档：[MIGRATION_MYSQL_TO_PG.md](migrations/MIGRATION_MYSQL_TO_PG.md)
