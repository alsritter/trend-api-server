"""
统一数据库连接池管理

本模块提供异步和同步两种数据库连接方式：
- 异步连接：用于 FastAPI 的异步端点
- 同步连接：用于 Celery worker 等独立进程

支持的数据库：
- MySQL（异步: aiomysql, 同步: pymysql）
- PostgreSQL with pgvector（异步: asyncpg）
"""

import aiomysql
import aiofiles
import asyncpg
import pymysql
import psycopg2
import psycopg2.extras
import os
from typing import AsyncGenerator
from contextlib import contextmanager
from app.config import settings
from pgvector.asyncpg import register_vector

# ==================== 全局连接池 ====================
# MySQL 异步连接池
db_pool: aiomysql.Pool = None

# PostgreSQL 异步连接池（支持 pgvector）
pg_pool: asyncpg.Pool = None


# ==================== 异步 MySQL 连接池管理 ====================


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


# ==================== 异步 PostgreSQL 连接池管理 ====================


async def init_vector_db():
    """初始化 PgVector 数据库连接池"""
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


async def get_hotspot_db() -> AsyncGenerator:
    """
    获取热点数据库连接（用于 FastAPI 依赖注入）
    使用与 vector_db 相同的连接池，因为它们使用同一个 PostgreSQL 数据库

    Usage:
        @app.get("/hotspots")
        async def get_hotspots(conn = Depends(get_hotspot_db)):
            result = await conn.fetch("SELECT * FROM hotspots LIMIT 10")
            return result
    """
    async with pg_pool.acquire() as conn:
        try:
            yield conn
        finally:
            pass  # 连接会自动归还到连接池


# ==================== 同步连接管理（用于 Celery worker）====================


@contextmanager
def get_mysql_connection():
    """
    获取 MySQL 同步连接的上下文管理器

    Usage:
        with get_mysql_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                result = cursor.fetchall()
    """
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.RELATION_DB_HOST,
            port=settings.RELATION_DB_PORT,
            user=settings.RELATION_DB_USER,
            password=settings.RELATION_DB_PWD,
            database=settings.RELATION_DB_NAME,
            charset="utf8mb4",
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


@contextmanager
def get_postgres_connection():
    """
    获取 PostgreSQL 同步连接的上下文管理器（用于 Celery worker 等独立进程）

    注意：此函数创建独立连接，不使用全局连接池。
    适用于 Celery worker 等无法访问主进程连接池的场景。

    Usage:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE table SET col = %s WHERE id = %s", (value, id))
            conn.commit()
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.PGVECTOR_HOST,
            port=settings.PGVECTOR_PORT,
            user=settings.PGVECTOR_USER,
            password=settings.PGVECTOR_PASSWORD,
            database=settings.PGVECTOR_DB,
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
