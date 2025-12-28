from fastapi import APIRouter, Depends
import aiomysql
from app.schemas.common import APIResponse
from app.dependencies import get_db
from app.db.session import db_pool
from app.config import settings
import redis.asyncio as aioredis

router = APIRouter()

@router.get("/health")
async def system_health(conn: aiomysql.Connection = Depends(get_db)):
    """
    系统健康检查

    检查 API Server、MySQL、Redis、Celery 状态
    """
    health_status = {
        "api_server": "healthy",
        "mysql": "unknown",
        "redis": "unknown",
        "celery": "unknown"
    }

    # 检查 MySQL
    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            await cursor.fetchone()
        health_status["mysql"] = "healthy"
    except Exception as e:
        health_status["mysql"] = f"unhealthy: {str(e)}"

    # 检查 Redis
    try:
        if settings.REDIS_DB_PWD:
            redis_url = f"redis://:{settings.REDIS_DB_PWD}@{settings.REDIS_DB_HOST}:{settings.REDIS_DB_PORT}/{settings.REDIS_DB_NUM}"
        else:
            redis_url = f"redis://{settings.REDIS_DB_HOST}:{settings.REDIS_DB_PORT}/{settings.REDIS_DB_NUM}"

        redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"

    # 检查 Celery
    try:
        from app.celery_app.celery import celery_app
        inspect = celery_app.control.inspect(timeout=1.0)
        stats = inspect.stats()
        if stats and len(stats) > 0:
            health_status["celery"] = "healthy"
        else:
            health_status["celery"] = "unhealthy: no workers"
    except Exception as e:
        health_status["celery"] = f"unhealthy: {str(e)}"

    # 判断整体状态
    overall_healthy = all(status == "healthy" for status in health_status.values())

    return APIResponse(
        code=0 if overall_healthy else 1,
        message="healthy" if overall_healthy else "some services unhealthy",
        data=health_status
    )


@router.get("/celery/stats")
async def celery_stats():
    """
    Celery 队列状态

    注意：需要 Celery Worker 运行才能获取准确数据
    """
    from app.celery_app.celery import celery_app

    try:
        # 获取 Celery inspect 实例
        inspect = celery_app.control.inspect()

        # 获取活跃任务
        active_tasks = inspect.active()
        active_count = sum(len(tasks) for tasks in (active_tasks.values() if active_tasks else [])) if active_tasks else 0

        # 获取注册的任务
        registered = inspect.registered()

        # 获取统计信息
        stats = inspect.stats()

        return APIResponse(
            code=0,
            message="success",
            data={
                "active_tasks": active_count,
                "workers": len(stats) if stats else 0,
                "registered_tasks": len(list(registered.values())[0]) if registered and list(registered.values()) else 0,
                "stats": stats
            }
        )
    except Exception as e:
        return APIResponse(
            code=1,
            message=f"Failed to get celery stats: {str(e)}",
            data={"active_tasks": 0, "workers": 0}
        )


@router.get("/database/stats")
async def database_stats(conn: aiomysql.Connection = Depends(get_db)):
    """
    数据库统计信息

    返回各平台爬取的内容数量，按平台分组
    """
    try:
        stats = {}
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 小红书统计
            xhs_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM xhs_note")
                result = await cursor.fetchone()
                xhs_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM xhs_note_comment")
                result = await cursor.fetchone()
                xhs_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM xhs_creator")
                result = await cursor.fetchone()
                xhs_stats["creators"] = result['count']
            except Exception:
                pass
            stats["xhs"] = xhs_stats

            # 抖音统计
            dy_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM douyin_aweme")
                result = await cursor.fetchone()
                dy_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM douyin_aweme_comment")
                result = await cursor.fetchone()
                dy_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM dy_creator")
                result = await cursor.fetchone()
                dy_stats["creators"] = result['count']
            except Exception:
                pass
            stats["dy"] = dy_stats

            # 哔哩哔哩统计
            bili_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM bilibili_video")
                result = await cursor.fetchone()
                bili_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM bilibili_video_comment")
                result = await cursor.fetchone()
                bili_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM bilibili_up_info")
                result = await cursor.fetchone()
                bili_stats["creators"] = result['count']
            except Exception:
                pass
            stats["bili"] = bili_stats

            # 快手统计
            ks_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM kuaishou_video")
                result = await cursor.fetchone()
                ks_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM kuaishou_video_comment")
                result = await cursor.fetchone()
                ks_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM kuaishou_creator")
                result = await cursor.fetchone()
                ks_stats["creators"] = result['count']
            except Exception:
                pass
            stats["ks"] = ks_stats

            # 微博统计
            wb_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM weibo_note")
                result = await cursor.fetchone()
                wb_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM weibo_note_comment")
                result = await cursor.fetchone()
                wb_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM weibo_creator")
                result = await cursor.fetchone()
                wb_stats["creators"] = result['count']
            except Exception:
                pass
            stats["wb"] = wb_stats

            # 百度贴吧统计
            tieba_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM tieba_note")
                result = await cursor.fetchone()
                tieba_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM tieba_comment")
                result = await cursor.fetchone()
                tieba_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM tieba_creator")
                result = await cursor.fetchone()
                tieba_stats["creators"] = result['count']
            except Exception:
                pass
            stats["tieba"] = tieba_stats

            # 知乎统计
            zhihu_stats = {"notes": 0, "comments": 0, "creators": 0}
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM zhihu_content")
                result = await cursor.fetchone()
                zhihu_stats["notes"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM zhihu_comment")
                result = await cursor.fetchone()
                zhihu_stats["comments"] = result['count']
            except Exception:
                pass
            try:
                await cursor.execute("SELECT COUNT(*) as count FROM zhihu_creator")
                result = await cursor.fetchone()
                zhihu_stats["creators"] = result['count']
            except Exception:
                pass
            stats["zhihu"] = zhihu_stats

        return APIResponse(
            code=0,
            message="success",
            data=stats
        )
    except Exception as e:
        return APIResponse(
            code=1,
            message=f"Failed to get database stats: {str(e)}",
            data={}
        )
