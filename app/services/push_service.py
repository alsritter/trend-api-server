from typing import List, Dict, Any
import logging
from app.db.session import pg_pool
from app.schemas.push import (
    PushQueueItem,
    PushStatus,
)

logger = logging.getLogger(__name__)


class PushService:
    """推送服务类 - 负责管理商业报告的推送队列"""

    def __init__(self):
        """初始化推送服务"""
        pass

    async def add_to_push_queue(self, hotspot_id: int) -> Dict[str, Any]:
        """
        添加到推送队列

        参数:
            hotspot_id: 热点ID

        返回:
            包含 success, push_id, message 的字典

        异常:
            ValueError: 如果热点不存在
        """
        async with pg_pool.acquire() as conn:
            # 检查热点是否存在
            hotspot = await conn.fetchrow(
                """
                SELECT id FROM hotspots WHERE id = $1
                """,
                hotspot_id,
            )

            if not hotspot:
                raise ValueError(f"Hotspot not found: hotspot_id={hotspot_id}")

            # 检查是否已经在队列中
            existing = await conn.fetchrow(
                """
                SELECT id FROM push_queue WHERE hotspot_id = $1
                """,
                hotspot_id,
            )

            if existing:
                return {
                    "success": True,
                    "push_id": existing["id"],
                    "message": "Already in push queue",
                }

            # 插入推送队列
            push_id = await conn.fetchval(
                """
                INSERT INTO push_queue (hotspot_id, status)
                VALUES ($1, $2)
                RETURNING id
                """,
                hotspot_id,
                PushStatus.PENDING.value,
            )

            logger.info(
                f"Added to push queue - push_id: {push_id}, hotspot_id: {hotspot_id}"
            )

            return {
                "success": True,
                "push_id": push_id,
                "message": "Successfully added to push queue",
            }

    async def get_pending_push_items(self, limit: int = 10) -> List[PushQueueItem]:
        """
        获取待推送的报告

        参数:
            limit: 返回数量限制

        返回:
            待推送项列表
        """
        async with pg_pool.acquire() as conn:
            # 获取待推送项
            rows = await conn.fetch(
                """
                SELECT id, hotspot_id, status, created_at, updated_at
                FROM push_queue
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                PushStatus.PENDING.value,
                limit,
            )

            items = [
                PushQueueItem(
                    id=row["id"],
                    hotspot_id=row["hotspot_id"],
                    status=PushStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

            logger.info(f"Found {len(items)} pending push items")
            return items

    async def update_push_status(self, push_id: int, status: PushStatus) -> Dict[str, Any]:
        """
        更新推送状态

        参数:
            push_id: 推送队列项ID
            status: 新的推送状态

        返回:
            包含 success, message, old_status, new_status 的字典

        异常:
            ValueError: 如果推送项不存在
        """
        async with pg_pool.acquire() as conn:
            # 获取当前状态
            current = await conn.fetchrow(
                """
                SELECT status FROM push_queue WHERE id = $1
                """,
                push_id,
            )

            if not current:
                raise ValueError(f"Push item not found: push_id={push_id}")

            old_status = PushStatus(current["status"])

            # 更新状态
            await conn.execute(
                """
                UPDATE push_queue 
                SET status = $1
                WHERE id = $2
                """,
                status.value,
                push_id,
            )

            logger.info(
                f"Updated push status - push_id: {push_id}, "
                f"old: {old_status.value}, new: {status.value}"
            )

            return {
                "success": True,
                "message": f"Status updated from {old_status.value} to {status.value}",
                "old_status": old_status,
                "new_status": status,
            }


# 全局单例
push_service = PushService()
