from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import logging
from app.db import session
from app.schemas.push import (
    PushQueueItem,
    Priority,
    PushStatus,
)
from app.schemas.hotspot import BusinessReportContent

logger = logging.getLogger(__name__)


class PushService:
    """推送服务类 - 负责管理商业报告的推送队列"""

    def __init__(self):
        """初始化推送服务"""
        pass

    async def add_to_push_queue(
        self, hotspot_id: int, report_id: int, channels: List[str]
    ) -> Dict[str, Any]:
        """
        添加到推送队列

        Args:
            hotspot_id: 热点ID
            report_id: 报告ID
            channels: 推送渠道

        Returns:
            包含 success, push_id, message 的字典

        Raises:
            ValueError: 如果报告不存在
        """
        async with session.pg_pool.acquire() as conn:
            # 获取报告的优先级和分数
            report = await conn.fetchrow(
                "SELECT priority, score FROM business_reports WHERE id = $1", report_id
            )

            if not report:
                raise ValueError(f"报告 {report_id} 不存在")

            # 插入推送队列
            push_id = await conn.fetchval(
                """
                INSERT INTO push_queue (
                    hotspot_id, report_id, priority, score, channels, scheduled_at
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                hotspot_id,
                report_id,
                report["priority"],
                report["score"],
                json.dumps(channels),
            )

            logger.info(
                f"添加到推送队列成功 - push_id: {push_id}, hotspot_id: {hotspot_id}, "
                f"report_id: {report_id}, channels: {channels}"
            )

            return {
                "success": True,
                "push_id": push_id,
                "message": f"已添加到推送队列 (ID: {push_id})",
            }

    async def get_pending_push_items(self, limit: int = 10) -> List[PushQueueItem]:
        """
        获取待推送的报告（按优先级和分数排序）

        Args:
            limit: 返回数量限制

        Returns:
            推送队列项列表
        """
        async with session.pg_pool.acquire() as conn:
            # 获取上次推送时间，确保间隔 >= 2小时
            last_push = await conn.fetchval(
                """
                SELECT MAX(sent_at)
                FROM push_queue
                WHERE status = 'sent'
                """
            )

            two_hours_ago = datetime.now() - timedelta(hours=2)
            can_push = last_push is None or last_push < two_hours_ago

            if not can_push:
                logger.info(
                    f"推送间隔未达标 - last_push: {last_push}, "
                    f"需要等待到 {last_push + timedelta(hours=2) if last_push else 'N/A'}"
                )
                return []

            # 查询待推送项
            records = await conn.fetch(
                """
                SELECT
                    pq.*,
                    h.keyword,
                    br.report
                FROM push_queue pq
                JOIN hotspots h ON pq.hotspot_id = h.id
                JOIN business_reports br ON pq.report_id = br.id
                WHERE pq.status = 'pending'
                ORDER BY
                    CASE pq.priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    pq.score DESC
                LIMIT $1
                """,
                limit,
            )

            items = [
                PushQueueItem(
                    id=r["id"],
                    hotspot_id=r["hotspot_id"],
                    report_id=r["report_id"],
                    priority=Priority(r["priority"]),
                    score=float(r["score"]),
                    status=PushStatus(r["status"]),
                    channels=json.loads(r["channels"])
                    if isinstance(r["channels"], str)
                    else r["channels"],
                    scheduled_at=r["scheduled_at"],
                    sent_at=r["sent_at"],
                    retry_count=r["retry_count"],
                    error_message=r["error_message"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    keyword=r["keyword"],
                    report=BusinessReportContent(**json.loads(r["report"]))
                    if r["report"]
                    else None,
                )
                for r in records
            ]

            logger.info(f"获取待推送项 - 数量: {len(items)}, limit: {limit}")
            return items

    async def update_push_status(
        self,
        push_id: int,
        status: PushStatus,
        error_message: str = None,
    ) -> Dict[str, Any]:
        """
        更新推送状态

        Args:
            push_id: 推送队列项ID
            status: 新的推送状态
            error_message: 错误信息（如果失败）

        Returns:
            包含 success, message, old_status, new_status 的字典

        Raises:
            ValueError: 如果推送项不存在
        """
        async with session.pg_pool.acquire() as conn:
            # 获取当前状态
            current = await conn.fetchrow(
                "SELECT status FROM push_queue WHERE id = $1", push_id
            )

            if not current:
                raise ValueError(f"推送队列项 {push_id} 不存在")

            old_status = PushStatus(current["status"])

            # 更新状态
            if status == PushStatus.SENT:
                await conn.execute(
                    """
                    UPDATE push_queue
                    SET status = $1,
                        sent_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP,
                        error_message = NULL
                    WHERE id = $2
                    """,
                    status.value,
                    push_id,
                )
            elif status == PushStatus.FAILED:
                await conn.execute(
                    """
                    UPDATE push_queue
                    SET status = $1,
                        retry_count = retry_count + 1,
                        updated_at = CURRENT_TIMESTAMP,
                        error_message = $2
                    WHERE id = $3
                    """,
                    status.value,
                    error_message,
                    push_id,
                )
            else:
                await conn.execute(
                    """
                    UPDATE push_queue
                    SET status = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    """,
                    status.value,
                    push_id,
                )

            logger.info(
                f"更新推送状态 - push_id: {push_id}, {old_status.value} -> {status.value}"
            )

            return {
                "success": True,
                "message": f"推送状态已更新为 {status.value}",
                "old_status": old_status,
                "new_status": status,
            }

    async def get_push_item(self, push_id: int) -> PushQueueItem:
        """
        获取推送队列项详情

        Args:
            push_id: 推送队列项ID

        Returns:
            推送队列项

        Raises:
            ValueError: 如果推送项不存在
        """
        async with session.pg_pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                SELECT
                    pq.*,
                    h.keyword,
                    br.report
                FROM push_queue pq
                JOIN hotspots h ON pq.hotspot_id = h.id
                JOIN business_reports br ON pq.report_id = br.id
                WHERE pq.id = $1
                """,
                push_id,
            )

            if not record:
                raise ValueError(f"推送队列项 {push_id} 不存在")

            return PushQueueItem(
                id=record["id"],
                hotspot_id=record["hotspot_id"],
                report_id=record["report_id"],
                priority=Priority(record["priority"]),
                score=float(record["score"]),
                status=PushStatus(record["status"]),
                channels=json.loads(record["channels"])
                if isinstance(record["channels"], str)
                else record["channels"],
                scheduled_at=record["scheduled_at"],
                sent_at=record["sent_at"],
                retry_count=record["retry_count"],
                error_message=record["error_message"],
                created_at=record["created_at"],
                updated_at=record["updated_at"],
                keyword=record["keyword"],
                report=BusinessReportContent(**json.loads(record["report"]))
                if record["report"]
                else None,
            )


# 全局单例
push_service = PushService()
