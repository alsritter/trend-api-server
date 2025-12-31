"""
热点数据库会话管理

使用与 vector_session 相同的连接池，因为它们使用同一个 PostgreSQL 数据库
"""

from app.db import vector_session
from typing import AsyncGenerator


async def get_hotspot_db() -> AsyncGenerator:
    """
    获取热点数据库连接（用于 FastAPI 依赖注入）

    Usage:
        @app.get("/hotspots")
        async def get_hotspots(conn = Depends(get_hotspot_db)):
            result = await conn.fetch("SELECT * FROM hotspots LIMIT 10")
            return result
    """
    async with vector_session.pg_pool.acquire() as conn:
        try:
            yield conn
        finally:
            pass  # 连接会自动归还到连接池
