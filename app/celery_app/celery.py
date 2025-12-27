from celery import Celery
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
