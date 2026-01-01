import aiomysql
import aiofiles
import os
from typing import AsyncGenerator
from app.config import settings

# 全局数据库连接池
db_pool: aiomysql.Pool = None


async def init_table_schema():
    """
    初始化数据库表结构

    参考 MediaCrawlerPro-Python 的数据库初始化逻辑，
    检查表是否已存在，如果不存在则创建所有表结构。
    """
    global db_pool

    if db_pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")

    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 检查是否已经初始化过表结构
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()

            # 如果数据库中已有表，则只检查 crawler_tasks 表是否存在
            table_names = [list(t.values())[0] for t in tables]
            if "crawler_tasks" not in table_names:
                print("[init_table_schema] Creating crawler_tasks table")

                # 读取任务表的 SQL 文件
                task_sql_file = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "app",
                    "db",
                    "task_schema.sql",
                )

                if os.path.exists(task_sql_file):
                    async with aiofiles.open(
                        task_sql_file, mode="r", encoding="utf-8"
                    ) as f:
                        task_sql = await f.read()
                        await cursor.execute(task_sql)
                        print(
                            "[init_table_schema] crawler_tasks table created successfully"
                        )
                else:
                    print(
                        f"[init_table_schema] Task SQL file not found: {task_sql_file}"
                    )

            # 如果数据库完全为空，则初始化 MediaCrawlerPro 的表结构
            if len(tables) == 0:
                # 读取 MediaCrawlerPro-Python 的 SQL 文件
                sql_file_path = os.path.join(
                    settings.CRAWLER_BASE_PATH, "schema", "tables.sql"
                )

                if not os.path.exists(sql_file_path):
                    print(f"[init_table_schema] SQL file not found: {sql_file_path}")
                    print("[init_table_schema] Skip table initialization")
                    return

                # 读取并执行 SQL 文件
                async with aiofiles.open(
                    sql_file_path, mode="r", encoding="utf-8"
                ) as f:
                    schema_sql = await f.read()

                # 分割多个 SQL 语句并执行
                # SQL 文件包含多个 CREATE TABLE 和 DROP TABLE 语句
                sql_statements = schema_sql.split(";")

                for statement in sql_statements:
                    statement = statement.strip()
                    if statement:  # 忽略空语句
                        try:
                            await cursor.execute(statement)
                        except Exception as e:
                            print(
                                f"[init_table_schema] Error executing SQL: {str(e)[:100]}"
                            )
                            # 继续执行其他语句
                            continue

                print(
                    "[init_table_schema] Database table schema initialized successfully"
                )


async def init_db():
    """初始化数据库连接池和表结构"""
    global db_pool
    db_pool = await aiomysql.create_pool(
        host=settings.RELATION_DB_HOST,
        port=settings.RELATION_DB_PORT,
        user=settings.RELATION_DB_USER,
        password=settings.RELATION_DB_PWD,
        db=settings.RELATION_DB_NAME,
        autocommit=True,
        maxsize=10,
        minsize=1,
        charset="utf8mb4",
        init_command="SET time_zone='+08:00'",  # 设置 MySQL 连接时区为东8区
    )
    print(
        f"Database connection pool initialized: {settings.RELATION_DB_HOST}:{settings.RELATION_DB_PORT}/{settings.RELATION_DB_NAME}"
    )

    # 初始化表结构
    await init_table_schema()


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
