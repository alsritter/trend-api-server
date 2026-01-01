"""
任务仓储层
提供任务的数据库 CRUD 操作
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiomysql

from app.schemas.task import TaskDB


class TaskRepository:
    """任务数据库操作"""

    def __init__(self, conn: aiomysql.Connection):
        self.conn = conn

    async def create_task(
        self,
        task_id: str,
        platform: str,
        crawler_type: str,
        keywords: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        hotspot_id: Optional[int] = None,
    ) -> TaskDB:
        """创建新任务"""
        config_json = json.dumps(config, ensure_ascii=False) if config else None

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            sql = """
            INSERT INTO crawler_tasks
            (task_id, platform, crawler_type, keywords, status, config, hotspot_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            await cursor.execute(
                sql,
                (
                    task_id,
                    platform,
                    crawler_type,
                    keywords,
                    "PENDING",
                    config_json,
                    hotspot_id,
                ),
            )
            await self.conn.commit()

            # 获取插入的记录
            return await self.get_task_by_task_id(task_id)

    async def get_task_by_task_id(self, task_id: str) -> Optional[TaskDB]:
        """根据任务ID获取任务"""
        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            sql = "SELECT * FROM crawler_tasks WHERE task_id = %s"
            await cursor.execute(sql, (task_id,))
            row = await cursor.fetchone()
            if row:
                return TaskDB(**row)
            return None

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        progress_current: Optional[int] = None,
        progress_total: Optional[int] = None,
        progress_percentage: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> bool:
        """更新任务状态"""
        updates = ["status = %s", "updated_at = NOW()"]
        params = [status]

        if progress_current is not None:
            updates.append("progress_current = %s")
            params.append(progress_current)

        if progress_total is not None:
            updates.append("progress_total = %s")
            params.append(progress_total)

        if progress_percentage is not None:
            updates.append("progress_percentage = %s")
            params.append(progress_percentage)

        if result is not None:
            updates.append("result = %s")
            params.append(json.dumps(result, ensure_ascii=False))

        if error is not None:
            updates.append("error = %s")
            params.append(error)

        if started_at is not None:
            updates.append("started_at = %s")
            params.append(started_at)

        if finished_at is not None:
            updates.append("finished_at = %s")
            params.append(finished_at)

        params.append(task_id)

        async with self.conn.cursor() as cursor:
            sql = f"UPDATE crawler_tasks SET {', '.join(updates)} WHERE task_id = %s"
            await cursor.execute(sql, params)
            await self.conn.commit()
            return cursor.rowcount > 0

    async def list_tasks(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        hotspot_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[TaskDB], int]:
        """
        分页查询任务列表

        Returns:
            (任务列表, 总数)
        """
        conditions = []
        params = []

        if platform:
            conditions.append("platform = %s")
            params.append(platform)

        if status:
            conditions.append("status = %s")
            params.append(status)

        if hotspot_id is not None:
            conditions.append("hotspot_id = %s")
            params.append(hotspot_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        async with self.conn.cursor() as cursor:
            count_sql = f"SELECT COUNT(*) as total FROM crawler_tasks {where_clause}"
            await cursor.execute(count_sql, params)
            result = await cursor.fetchone()
            total = result[0] if result else 0

        # 查询分页数据
        offset = (page - 1) * page_size
        list_sql = f"""
        SELECT * FROM crawler_tasks
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(list_sql, params)
            rows = await cursor.fetchall()
            tasks = [TaskDB(**row) for row in rows]

        return tasks, total

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        async with self.conn.cursor() as cursor:
            sql = "DELETE FROM crawler_tasks WHERE task_id = %s"
            await cursor.execute(sql, (task_id,))
            await self.conn.commit()
            return cursor.rowcount > 0

    async def get_tasks_by_hotspot_id(self, hotspot_id: int) -> List[TaskDB]:
        """根据热点ID获取所有关联的任务"""
        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            sql = """
            SELECT * FROM crawler_tasks
            WHERE hotspot_id = %s
            ORDER BY created_at DESC
            """
            await cursor.execute(sql, (hotspot_id,))
            rows = await cursor.fetchall()
            return [TaskDB(**row) for row in rows]
