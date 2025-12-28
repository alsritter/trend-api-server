import os
import subprocess
import asyncio
from datetime import datetime
from celery import Task
from celery.utils.log import get_task_logger
from app.celery_app.celery import celery_app
from app.config import settings
from app.utils.crawler_config import merge_task_config
from app.db.session import db_pool
from app.db.task_repo import TaskRepository

logger = get_task_logger(__name__)


def get_event_loop():
    """获取或创建事件循环"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def update_task_status_async(task_id: str, **kwargs):
    """异步更新任务状态到数据库"""
    try:
        if db_pool is None:
            logger.warning("Database pool not initialized, skip task status update")
            return

        async with db_pool.acquire() as conn:
            repo = TaskRepository(conn)
            await repo.update_task_status(task_id, **kwargs)
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")


def update_task_status_sync(task_id: str, **kwargs):
    """同步方式更新任务状态（在 Celery worker 中调用）"""
    loop = get_event_loop()
    loop.run_until_complete(update_task_status_async(task_id, **kwargs))


class CrawlerTask(Task):
    """自定义 Celery Task 类，支持进度更新"""

    def update_progress(self, current, total):
        """更新任务进度"""
        self.update_state(
            state="PROGRESS",
            meta={
                "current": current,
                "total": total,
                "percentage": int((current / total) * 100) if total > 0 else 0,
            },
        )


@celery_app.task(bind=True, base=CrawlerTask, name="tasks.run_crawler")
def run_crawler(
    self,
    platform: str,
    crawler_type: str,
    keywords: str = "",
    enable_checkpoint: bool = True,
    checkpoint_id: str = "",
    max_notes_count: int = 10,
    enable_comments: bool = True,
    enable_sub_comments: bool = False,
    max_comments_count: int = 20,
    # 平台特定的指定ID/URL列表
    xhs_note_url_list: list = None,
    xhs_creator_url_list: list = None,
    weibo_specified_id_list: list = None,
    weibo_creator_id_list: list = None,
    tieba_specified_id_list: list = None,
    tieba_name_list: list = None,
    tieba_creator_url_list: list = None,
    bili_creator_id_list: list = None,
    bili_specified_id_list: list = None,
    dy_specified_id_list: list = None,
    dy_creator_id_list: list = None,
    ks_specified_id_list: list = None,
    ks_creator_id_list: list = None,
    zhihu_creator_url_list: list = None,
    zhihu_specified_id_list: list = None,
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
        max_comments_count: 每条内容最大评论数量
        xhs_note_url_list: 小红书笔记URL列表
        xhs_creator_url_list: 小红书创作者URL列表
        weibo_specified_id_list: 微博指定帖子ID列表
        weibo_creator_id_list: 微博创作者ID列表
        tieba_specified_id_list: 贴吧指定帖子ID列表
        tieba_name_list: 贴吧名称列表
        tieba_creator_url_list: 贴吧创作者URL列表
        bili_creator_id_list: B站创作者ID列表
        bili_specified_id_list: B站视频BVID列表
        dy_specified_id_list: 抖音指定视频ID列表
        dy_creator_id_list: 抖音创作者ID列表
        ks_specified_id_list: 快手指定视频ID列表
        ks_creator_id_list: 快手创作者ID列表
        zhihu_creator_url_list: 知乎创作者URL列表
        zhihu_specified_id_list: 知乎指定内容URL列表
    """
    logger.info(
        f"Starting crawler task: platform={platform}, type={crawler_type}, keywords={keywords}"
    )

    # 更新任务状态为 STARTED
    update_task_status_sync(
        self.request.id,
        status="STARTED",
        started_at=datetime.now(),
    )

    # 构建命令行参数
    cmd = [
        settings.CRAWLER_PYTHON_PATH,
        settings.CRAWLER_MAIN_PATH,
        "--platform",
        platform,
        "--type",
        crawler_type,
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
        "max_comments_per_note": max_comments_count,
        "enable_checkpoint": enable_checkpoint,
        "checkpoint_id": checkpoint_id,
    }

    # 添加平台特定的ID/URL列表参数
    if xhs_note_url_list:
        task_params["xhs_note_url_list"] = xhs_note_url_list
    if xhs_creator_url_list:
        task_params["xhs_creator_url_list"] = xhs_creator_url_list
    if weibo_specified_id_list:
        task_params["weibo_specified_id_list"] = weibo_specified_id_list
    if weibo_creator_id_list:
        task_params["weibo_creator_id_list"] = weibo_creator_id_list
    if tieba_specified_id_list:
        task_params["tieba_specified_id_list"] = tieba_specified_id_list
    if tieba_name_list:
        task_params["tieba_name_list"] = tieba_name_list
    if tieba_creator_url_list:
        task_params["tieba_creator_url_list"] = tieba_creator_url_list
    if bili_creator_id_list:
        task_params["bili_creator_id_list"] = bili_creator_id_list
    if bili_specified_id_list:
        task_params["bili_specified_id_list"] = bili_specified_id_list
    if dy_specified_id_list:
        task_params["dy_specified_id_list"] = dy_specified_id_list
    if dy_creator_id_list:
        task_params["dy_creator_id_list"] = dy_creator_id_list
    if ks_specified_id_list:
        task_params["ks_specified_id_list"] = ks_specified_id_list
    if ks_creator_id_list:
        task_params["ks_creator_id_list"] = ks_creator_id_list
    if zhihu_creator_url_list:
        task_params["zhihu_creator_url_list"] = zhihu_creator_url_list
    if zhihu_specified_id_list:
        task_params["zhihu_specified_id_list"] = zhihu_specified_id_list

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
            bufsize=1,
        )

        # 实时读取输出并更新进度
        stdout_lines = []
        stderr_lines = []

        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
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
                        
                        # 更新数据库中的进度
                        update_task_status_sync(
                            self.request.id,
                            status="PROGRESS",
                            progress_current=current,
                            progress_total=total,
                            progress_percentage=int((current / total) * 100) if total > 0 else 0,
                        )
                    except Exception as e:
                        logger.debug(f"Failed to parse progress: {e}")

        # 读取剩余的 stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            stderr_lines.append(stderr_output)
            logger.error(f"Crawler stderr: {stderr_output}")

        return_code = process.poll()

        if return_code == 0:
            logger.info("Crawler task completed successfully")
            result = {
                "status": "success",
                "platform": platform,
                "crawler_type": crawler_type,
                "keywords": keywords,
                "stdout": "\n".join(stdout_lines[-50:]),  # 只保留最后50行
                "message": "Crawler task completed successfully",
            }
            
            # 更新任务状态为 SUCCESS
            update_task_status_sync(
                self.request.id,
                status="SUCCESS",
                result=result,
                finished_at=datetime.now(),
            )
            
            return result
        else:
            error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
            logger.error(f"Crawler task failed with code {return_code}: {error_msg}")
            
            # 更新任务状态为 FAILURE
            update_task_status_sync(
                self.request.id,
                status="FAILURE",
                error=f"Crawler failed with return code {return_code}: {error_msg}",
                finished_at=datetime.now(),
            )
            
            raise Exception(
                f"Crawler failed with return code {return_code}: {error_msg}"
            )

    except Exception as e:
        logger.error(f"Crawler task error: {str(e)}")
        
        # 更新任务状态为 FAILURE
        update_task_status_sync(
            self.request.id,
            status="FAILURE",
            error=str(e),
            finished_at=datetime.now(),
        )
        
        raise


@celery_app.task(name="tasks.stop_crawler")
def stop_crawler(task_id: str):
    """停止正在运行的爬虫任务"""
    logger.info(f"Stopping crawler task: {task_id}")
    celery_app.control.revoke(task_id, terminate=True, signal="SIGKILL")
    
    # 更新任务状态为 REVOKED
    update_task_status_sync(
        task_id,
        status="REVOKED",
        finished_at=datetime.now(),
    )
    
    return {"status": "terminated", "task_id": task_id}
