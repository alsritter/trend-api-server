import os
import subprocess
from celery import Task
from celery.utils.log import get_task_logger
from app.celery_app.celery import celery_app
from app.config import settings
from app.utils.crawler_config import merge_task_config

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

    # 使用配置转换工具生成环境变量
    # 这样可以将 API 服务的配置传递给 MediaCrawlerPro-Python，无需修改其代码
    task_params = {
        "platform": platform,
        "crawler_type": crawler_type,
        "keywords": keywords,
        "max_notes": max_notes_count,
        "enable_comments": enable_comments,
        "enable_sub_comments": enable_sub_comments,
        "enable_checkpoint": enable_checkpoint,
        "checkpoint_id": checkpoint_id,
    }

    # 获取合并后的环境变量配置
    env_config = merge_task_config(task_params)

    # 更新当前环境变量
    env = os.environ.copy()
    env.update(env_config)

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
