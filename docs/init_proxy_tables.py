#!/usr/bin/env python3
"""
代理池表结构初始化脚本
在 PostgreSQL 数据库中创建代理池所需的表结构
"""

import asyncio
import asyncpg
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


async def init_proxy_tables():
    """初始化代理池表结构"""
    print("=" * 60)
    print("代理池表结构初始化")
    print("=" * 60)
    
    # 连接到 PostgreSQL
    print(f"\n正在连接到数据库...")
    print(f"Host: {settings.PGVECTOR_HOST}")
    print(f"Port: {settings.PGVECTOR_PORT}")
    print(f"Database: {settings.PGVECTOR_DB}")
    
    try:
        conn = await asyncpg.connect(
            host=settings.PGVECTOR_HOST,
            port=settings.PGVECTOR_PORT,
            user=settings.PGVECTOR_USER,
            password=settings.PGVECTOR_PASSWORD,
            database=settings.PGVECTOR_DB,
        )
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

    # 读取 SQL 文件
    sql_file = os.path.join(
        os.path.dirname(__file__),
        "migrations",
        "home_proxy_pool_schema_pg.sql"
    )
    
    print(f"\n正在读取 SQL 文件: {sql_file}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print("✓ SQL 文件读取成功")
    except FileNotFoundError:
        print(f"✗ SQL 文件不存在: {sql_file}")
        await conn.close()
        return False
    except Exception as e:
        print(f"✗ 读取 SQL 文件失败: {e}")
        await conn.close()
        return False

    # 执行 SQL
    print("\n正在创建表结构...")
    
    try:
        # 分割并执行 SQL 语句
        # 注意：PostgreSQL 的 COMMENT 和 CREATE TABLE 需要分开执行
        await conn.execute(sql_content)
        print("✓ 表结构创建成功")
        
        # 验证表是否创建成功
        print("\n验证表结构...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name IN ('proxy_agents', 'proxy_health_log', 'proxy_usage_log')
            ORDER BY table_name
        """)
        
        if len(tables) == 3:
            print("✓ 所有表创建成功:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print(f"⚠ 只创建了 {len(tables)}/3 个表")
            for table in tables:
                print(f"  - {table['table_name']}")
        
        # 检查索引
        print("\n检查索引...")
        indexes = await conn.fetch("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
              AND tablename IN ('proxy_agents', 'proxy_health_log', 'proxy_usage_log')
            ORDER BY tablename, indexname
        """)
        
        print(f"✓ 创建了 {len(indexes)} 个索引")
        
    except Exception as e:
        print(f"✗ 执行 SQL 失败: {e}")
        await conn.close()
        return False
    
    # 关闭连接
    await conn.close()
    print("\n" + "=" * 60)
    print("初始化完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(init_proxy_tables())
    sys.exit(0 if success else 1)
