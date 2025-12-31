import asyncpg
from typing import AsyncGenerator
from app.config import settings
from pgvector.asyncpg import register_vector

# 全局 PgVector 连接池
pg_pool: asyncpg.Pool = None


async def init_vector_db():
    """初始化 PgVector 数据库连接池和表结构"""
    global pg_pool
    pg_pool = await asyncpg.create_pool(
        host=settings.PGVECTOR_HOST,
        port=settings.PGVECTOR_PORT,
        user=settings.PGVECTOR_USER,
        password=settings.PGVECTOR_PASSWORD,
        database=settings.PGVECTOR_DB,
        min_size=1,
        max_size=10,
        init=register_vector,
    )
    print(
        f"PgVector connection pool initialized: {settings.PGVECTOR_HOST}:{settings.PGVECTOR_PORT}/{settings.PGVECTOR_DB}"
    )


async def close_vector_db():
    """关闭 PgVector 数据库连接池"""
    global pg_pool
    if pg_pool:
        await pg_pool.close()
        print("PgVector connection pool closed")


async def get_vector_db() -> AsyncGenerator:
    """
    获取 PgVector 数据库连接（用于 FastAPI 依赖注入）

    Usage:
        @app.get("/vectors")
        async def get_vectors(conn = Depends(get_vector_db)):
            result = await conn.fetch("SELECT * FROM modeldata LIMIT 10")
            return result
    """
    async with pg_pool.acquire() as conn:
        try:
            yield conn
        finally:
            pass  # 连接会自动归还到连接池
