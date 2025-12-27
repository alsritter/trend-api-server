import os
import subprocess
from celery import Task
from celery.utils.log import get_task_logger
from app.celery_app.celery import celery_app
from app.config import settings

logger = get_task_logger(__name__)


class CrawlerTask(Task):
    """自定义 Celery Task 类，支持进度更新"""

    def update_progress(self, current, total):
        """更新任务进度"""
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'percentage': int((current / total) * 100) if total > 0 else 0
            }
        )


@celery_app.task(bind=True, base=CrawlerTask, name="tasks.run_crawler")
def run_crawler(
    self,
    platform: str,
    crawler_type: str,
    keywords: str = "",
    enable_checkpoint: bool = True,
    checkpoint_id: str = "",
    max_notes_count: int = 100,
    enable_comments: bool = True,
    enable_sub_comments: bool = False
):
    """
    执行爬虫任务

    Args:
        platform: 平台名称 (xhs|dy|ks|bili|wb|tieba|zhihu)
        crawler_type: 爬虫类型 (search|detail|creator|homefeed)
        keywords: 搜索关键词（逗号分隔）
        enable_checkpoint: 是否启用断点续爬
        checkpoint_id: 指定检查点ID
        max_notes_count: 最大爬取数量
        enable_comments: 是否爬取评论
        enable_sub_comments: 是否爬取二级评论
    """
    logger.info(f"Starting crawler task: platform={platform}, type={crawler_type}, keywords={keywords}")

    # 构建命令行参数
    cmd = [
        settings.CRAWLER_PYTHON_PATH,
        settings.CRAWLER_MAIN_PATH,
        "--platform", platform,
        "--type", crawler_type
    ]

    if keywords:
        cmd.extend(["--keywords", keywords])

    if enable_checkpoint:
        cmd.append("--enable_checkpoint")
    else:
        cmd.append("--no-enable_checkpoint")

    if checkpoint_id:
        cmd.extend(["--checkpoint_id", checkpoint_id])

    # 设置环境变量（配置参数）
    env = os.environ.copy()
    env.update({
        "RELATION_DB_HOST": settings.MYSQL_HOST,
        "RELATION_DB_PORT": str(settings.MYSQL_PORT),
        "RELATION_DB_USER": settings.MYSQL_USER,
        "RELATION_DB_PWD": settings.MYSQL_PASSWORD,
        "RELATION_DB_NAME": settings.MYSQL_DATABASE,
        "REDIS_DB_HOST": settings.REDIS_HOST,
        "REDIS_DB_PORT": str(settings.REDIS_PORT),
        "REDIS_DB_PWD": settings.REDIS_PASSWORD,
        "REDIS_DB_NUM": str(settings.REDIS_DB),
        "SIGN_SRV_HOST": settings.SIGN_SRV_HOST,
        "SIGN_SRV_PORT": str(settings.SIGN_SRV_PORT),
        "CRAWLER_MAX_NOTES_COUNT": str(max_notes_count),
        "ENABLE_GET_COMMENTS": "True" if enable_comments else "False",
        "ENABLE_GET_SUB_COMMENTS": "True" if enable_sub_comments else "False",
        "SAVE_DATA_OPTION": "db",  # 强制使用数据库存储
        "ACCOUNT_POOL_SAVE_TYPE": "mysql",  # 使用 MySQL 账号池
    })

    try:
        # 执行爬虫命令（使用 subprocess）
        logger.info(f"Executing command: {' '.join(cmd)}")
        logger.info(f"Working directory: {settings.CRAWLER_BASE_PATH}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=settings.CRAWLER_BASE_PATH,
            text=True,
            bufsize=1
        )

        # 实时读取输出并更新进度
        stdout_lines = []
        stderr_lines = []

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                stdout_lines.append(line)
                logger.info(f"Crawler output: {line}")

                # 尝试从日志中解析进度（假设爬虫会输出进度信息）
                # 例如: "Progress: 50/100" 或其他格式
                if "Progress:" in line:
                    try:
                        parts = line.split("Progress:")[1].strip().split("/")
                        current = int(parts[0])
                        total = int(parts[1])
                        self.update_progress(current, total)
                    except Exception as e:
                        logger.debug(f"Failed to parse progress: {e}")

        # 读取剩余的 stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            stderr_lines.append(stderr_output)
            logger.error(f"Crawler stderr: {stderr_output}")

        return_code = process.poll()

        if return_code == 0:
            logger.info(f"Crawler task completed successfully")
            return {
                "status": "success",
                "platform": platform,
                "crawler_type": crawler_type,
                "keywords": keywords,
                "stdout": "\n".join(stdout_lines[-50:]),  # 只保留最后50行
                "message": "Crawler task completed successfully"
            }
        else:
            error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
            logger.error(f"Crawler task failed with code {return_code}: {error_msg}")
            raise Exception(f"Crawler failed with return code {return_code}: {error_msg}")

    except Exception as e:
        logger.error(f"Crawler task error: {str(e)}")
        raise


@celery_app.task(name="tasks.stop_crawler")
def stop_crawler(task_id: str):
    """停止正在运行的爬虫任务"""
    logger.info(f"Stopping crawler task: {task_id}")
    celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
    return {"status": "terminated", "task_id": task_id}
