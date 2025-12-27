import aiomysql
from typing import AsyncGenerator
from app.config import settings

# 全局数据库连接池
db_pool: aiomysql.Pool = None


async def init_db():
    """初始化数据库连接池"""
    global db_pool
    db_pool = await aiomysql.create_pool(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DATABASE,
        autocommit=True,
        maxsize=10,
        minsize=1,
        charset='utf8mb4'
    )
    print(f"Database connection pool initialized: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")


async def close_db():
    """关闭数据库连接池"""
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        print("Database connection pool closed")


async def get_db() -> AsyncGenerator:
    """
    获取数据库连接（用于 FastAPI 依赖注入）

    Usage:
        @app.get("/users")
        async def get_users(conn = Depends(get_db)):
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users")
                result = await cursor.fetchall()
            return result
    """
    async with db_pool.acquire() as conn:
        try:
            yield conn
        finally:
            pass  # 连接会自动归还到连接池
