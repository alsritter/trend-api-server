"""
数据库会话管理模块

模块说明：
- session.py: 统一的数据库连接管理，包含：
  - 异步 MySQL 连接池（用于 FastAPI）
  - 异步 PostgreSQL + pgvector 连接池（用于 FastAPI）
  - 同步 MySQL/PostgreSQL 连接（用于 Celery worker）
- task_repo.py: 任务数据仓储层

使用场景：
- FastAPI 异步端点：使用 session.py 的异步连接池
- Celery worker：使用 session.py 的同步连接（避免 event loop 问题）
"""

from app.db import session

__all__ = [
    "session",
]
