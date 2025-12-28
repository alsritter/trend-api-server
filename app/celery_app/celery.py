import asyncio
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from app.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "trend-api-server",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery_app.tasks.crawler_tasks"]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 2,  # 任务最长执行时间 2 小时
    task_soft_time_limit=3600 * 2 - 60,  # 软限制（提前 1 分钟警告）
    result_expires=3600 * 24,  # 结果保留 24 小时
    worker_prefetch_multiplier=1,  # 每次只预取 1 个任务
    worker_max_tasks_per_child=50,  # Worker 执行 50 个任务后重启（防止内存泄漏）
    broker_connection_retry_on_startup=True,  # Celery 6.0+ 需要显式设置
)

# 任务路由配置
celery_app.conf.task_routes = {
    "tasks.run_crawler": {"queue": "crawler_queue"},
    "tasks.stop_crawler": {"queue": "control_queue"},
}


# Celery Worker 启动时初始化数据库连接池
# 注意：FastAPI 和 Celery Worker 是两个独立的进程，不共享内存
# 即使 main.py 中初始化了数据库，Celery Worker 也需要单独初始化
@worker_ready.connect
def init_worker_db(**kwargs):
    """在 Celery worker 启动时初始化数据库连接池"""
    from app.db.session import init_db
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(init_db())
        print("[Celery Worker] Database pool initialized successfully")
    except Exception as e:
        print(f"[Celery Worker] Failed to initialize database pool: {e}")
        raise


# Celery Worker 关闭时清理数据库连接池
@worker_shutdown.connect
def shutdown_worker_db(**kwargs):
    """在 Celery worker 关闭时清理数据库连接池"""
    from app.db.session import close_db
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_db())
        print("[Celery Worker] Database pool closed successfully")
    except Exception as e:
        print(f"[Celery Worker] Failed to close database pool: {e}")
