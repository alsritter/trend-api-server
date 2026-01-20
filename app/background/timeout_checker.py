"""后台任务超时检查器"""

import asyncio
from datetime import datetime, timedelta
from app.config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# 全局停止标志
stop_timeout_check = False


async def check_timeout_tasks_background():
    """后台定期检查超时任务和过期的待验证热点"""
    from app.db import session
    from app.db.task_repo import TaskRepository
    from app.celery_app.celery import celery_app
    from app.services.hotspot_service import HotspotService
    from app.schemas.hotspot import HotspotStatus

    global stop_timeout_check
    check_interval = 300  # 5分钟检查一次
    hotspot_service = HotspotService()

    logger.info(
        f"[Timeout Checker] Started background task (interval: {check_interval}s)"
    )

    while not stop_timeout_check:
        try:
            await asyncio.sleep(check_interval)

            if stop_timeout_check:
                break

            # 检查数据库连接池是否可用
            if session.db_pool is None or session.pg_pool is None:
                logger.warning(
                    "[Timeout Checker] Database pool not initialized, skip check"
                )
                continue

            logger.info(
                "[Timeout Checker] Checking for timeout tasks and outdated pending_validation hotspots..."
            )

            # 使用 MySQL 连接池查询任务数据
            async with session.db_pool.acquire() as conn:
                repo = TaskRepository(conn)

                # ============ 1. 检查超时任务 ============
                timeout_tasks = await repo.get_timeout_tasks(
                    settings.TASK_TIMEOUT_SECONDS
                )

                if timeout_tasks:
                    timeout_count = 0
                    timeout_task_ids = []
                    updated_hotspot_ids = set()  # 记录已更新的热点ID

                    # 处理每个超时任务
                    for task in timeout_tasks:
                        try:
                            # 计算任务已运行时间
                            elapsed_seconds = (
                                datetime.now() - task.updated_at
                            ).total_seconds()

                            logger.info(
                                f"[Timeout Checker] Task {task.task_id} timeout detected: "
                                f"status={task.status}, elapsed={elapsed_seconds}s, "
                                f"platform={task.platform}, type={task.crawler_type}, "
                                f"hotspot_id={task.hotspot_id}"
                            )

                            # 更新任务状态为 FAILURE
                            await repo.update_task_status(
                                task.task_id,
                                status="FAILURE",
                                error=f"Task timeout after {elapsed_seconds:.0f} seconds (limit: {settings.TASK_TIMEOUT_SECONDS}s)",
                                finished_at=datetime.now(),
                            )

                            # 尝试终止 Celery 任务（如果还在运行）
                            try:
                                celery_app.control.revoke(
                                    task.task_id, terminate=True, signal="SIGKILL"
                                )
                                logger.info(
                                    f"[Timeout Checker] Revoked Celery task {task.task_id}"
                                )
                            except Exception as revoke_error:
                                logger.error(
                                    f"[Timeout Checker] Failed to revoke task {task.task_id}: {revoke_error}"
                                )

                            # 如果任务关联了热点，更新热点状态为 crawled
                            if (
                                task.hotspot_id
                                and task.hotspot_id not in updated_hotspot_ids
                            ):
                                try:
                                    # 检查该热点的所有爬虫任务是否都已完成（SUCCESS 或 FAILURE）
                                    all_tasks = await repo.get_tasks_by_hotspot_id(
                                        task.hotspot_id
                                    )
                                    all_finished = all(
                                        t.status in ("SUCCESS", "FAILURE")
                                        for t in all_tasks
                                    )

                                    if all_finished:
                                        # 更新热点状态为 crawled
                                        await hotspot_service.update_hotspot_status(
                                            task.hotspot_id, HotspotStatus.CRAWLED
                                        )
                                        updated_hotspot_ids.add(task.hotspot_id)
                                        logger.info(
                                            f"[Timeout Checker] Updated hotspot {task.hotspot_id} status to CRAWLED"
                                        )
                                except Exception as hotspot_error:
                                    logger.error(
                                        f"[Timeout Checker] Failed to update hotspot {task.hotspot_id}: {hotspot_error}"
                                    )

                            timeout_count += 1
                            timeout_task_ids.append(task.task_id)

                        except Exception as task_error:
                            logger.error(
                                f"[Timeout Checker] Failed to process timeout task {task.task_id}: {task_error}"
                            )

                    if timeout_count > 0:
                        logger.info(
                            f"[Timeout Checker] Processed {timeout_count} timeout tasks: {', '.join(timeout_task_ids)}"
                        )
                else:
                    logger.info("[Timeout Checker] No timeout tasks found")

            # ============ 2. 检查三天前仍为 pending_validation 的热点 ============
            try:
                three_days_ago = datetime.now() - timedelta(days=3)

                # 查询三天前创建的仍为 pending_validation 状态的热点
                outdated_count = (
                    await hotspot_service.update_outdated_pending_validation_hotspots(
                        three_days_ago
                    )
                )

                if outdated_count > 0:
                    logger.info(
                        f"[Timeout Checker] Updated {outdated_count} outdated pending_validation hotspots to rejected (超时未更新)"
                    )
                else:
                    logger.info(
                        "[Timeout Checker] No outdated pending_validation hotspots found"
                    )

            except Exception as outdated_error:
                logger.error(
                    f"[Timeout Checker] Failed to update outdated pending_validation hotspots: {outdated_error}"
                )

        except asyncio.CancelledError:
            logger.info("[Timeout Checker] Task cancelled, stopping...")
            break
        except Exception as e:
            logger.error(f"[Timeout Checker] Error during timeout check: {e}")
            # 继续运行，不因为单次错误而停止


def stop_checker():
    """停止后台检查任务"""
    global stop_timeout_check
    stop_timeout_check = True
    logger.info("[Timeout Checker] Stop signal received")
