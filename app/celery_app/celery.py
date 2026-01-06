import asyncio
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from app.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "trend-api-server",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery_app.tasks.crawler_tasks"],
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


# Celery Worker 子进程初始化时初始化数据库连接池
# 注意：Celery 默认使用 prefork 模式（多进程池）
# worker_ready 只在主进程触发一次，而 worker_process_init 会在每个子进程初始化时触发
# 这样可以确保每个执行任务的子进程都有自己的数据库连接池
@worker_process_init.connect
def init_worker_db(**kwargs):
    """在 Celery worker 子进程启动时初始化数据库连接池"""
    from app.db.session import init_db
    from app.db.vector_session import init_vector_db

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # 初始化 MySQL 连接池
        loop.run_until_complete(init_db())
        print("[Celery Worker Process] MySQL pool initialized successfully")
        
        # 初始化 PostgreSQL 连接池
        loop.run_until_complete(init_vector_db())
        print("[Celery Worker Process] PostgreSQL pool initialized successfully")
    except Exception as e:
        print(f"[Celery Worker Process] Failed to initialize database pool: {e}")
        raise


# Celery Worker 子进程关闭时清理数据库连接池
@worker_process_shutdown.connect
def shutdown_worker_db(**kwargs):
    """在 Celery worker 子进程关闭时清理数据库连接池"""
    from app.db.session import close_db
    from app.db.vector_session import close_vector_db

    try:
        loop = asyncio.get_event_loop()
        # 关闭 MySQL 连接池
        loop.run_until_complete(close_db())
        print("[Celery Worker Process] MySQL pool closed successfully")
        
        # 关闭 PostgreSQL 连接池
        loop.run_until_complete(close_vector_db())
        print("[Celery Worker Process] PostgreSQL pool closed successfully")
    except Exception as e:
        print(f"[Celery Worker Process] Failed to close database pool: {e}")
