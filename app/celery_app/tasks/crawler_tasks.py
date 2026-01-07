import os
import subprocess
import asyncio
from datetime import datetime
from celery import Task
from celery.utils.log import get_task_logger
from app.celery_app.celery import celery_app
from app.config import settings
from app.utils.crawler_config import merge_task_config
from app.db.task_repo import TaskRepository

logger = get_task_logger(__name__)


def parse_crawler_progress(line: str, platform: str) -> dict:
    """
    解析爬虫日志中的进度信息

    Args:
        line: 日志行
        platform: 平台名称 (xhs|dy|ks|bili|wb|tieba|zhihu)

    Returns:
        dict: 包含进度信息的字典，可能包含以下字段:
            - type: 进度类型 (keyword|page|count|max|finished)
            - keyword: 当前关键词
            - page: 当前页码
            - count: 已处理数量
            - message: 进度消息
    """
    result = {}

    # 通用模式 - 适用于所有平台
    # 1. 检测当前搜索关键词
    if "Current search keyword:" in line or "当前搜索关键词:" in line:
        parts = line.split(
            "Current search keyword:"
            if "Current search keyword:" in line
            else "当前搜索关键词:"
        )
        if len(parts) > 1:
            result["type"] = "keyword"
            result["keyword"] = parts[1].strip()
            result["message"] = f"Searching keyword '{result['keyword']}'"

    # 2. 检测搜索页码 - 适配多种平台格式
    elif any(
        pattern in line
        for pattern in [
            "page:",
            "页码:",
            "第",
            "Page:",
            "search xhs keyword:",
            "search douyin keyword:",
            "search bilibili keyword:",
            "search weibo keyword:",
            "search tieba keyword:",
            "search kuaishou keyword:",
            "search zhihu keyword:",
        ]
    ):
        # 尝试提取页码
        import re

        page_patterns = [
            r"page[:\s]+(\d+)",
            r"页码[:\s]+(\d+)",
            r"第\s*(\d+)\s*页",
            r"Page[:\s]+(\d+)",
        ]
        for pattern in page_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                result["type"] = "page"
                result["page"] = int(match.group(1))
                break

    # 3. 检测搜索结果数量 - 适配多种平台格式
    elif any(
        pattern in line
        for pattern in [
            "Search notes res count:",
            "Search video res count:",
            "Search content res count:",
            "搜索结果数量:",
            "res count:",
            "results count:",
        ]
    ):
        import re

        # 提取数字
        count_patterns = [
            r"count[:\s]+(\d+)",
            r"数量[:\s]+(\d+)",
        ]
        for pattern in count_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                result["type"] = "count"
                result["count"] = int(match.group(1))
                break

    # 4. 检测达到最大数量
    elif any(
        pattern in line for pattern in ["Reached max", "达到最大", "maximum", "已完成"]
    ):
        result["type"] = "max"
        result["message"] = "Reached maximum crawl count"

    # 5. 检测完成状态
    elif any(
        pattern in line
        for pattern in [
            "Crawler finished",
            "finished ...",
            "crawl completed",
            "爬取完成",
            "任务完成",
        ]
    ):
        result["type"] = "finished"
        result["message"] = "Crawler task finishing"

    # 6. 检测详情页爬取 (detail 模式)
    elif "Get note detail" in line or "获取详情" in line:
        result["type"] = "detail"
        result["message"] = "Processing detail page"

    # 7. 检测评论爬取进度
    elif "comments" in line.lower() and ("count" in line.lower() or "数量" in line):
        import re

        match = re.search(r"(\d+)", line)
        if match:
            result["type"] = "comments"
            result["count"] = int(match.group(1))
            result["message"] = f"Processing comments: {result['count']}"

    return result



async def update_task_status_async(task_id: str, **kwargs):
    """异步更新任务状态到数据库"""
    try:
        # 动态导入 db_pool，避免导入时的快照问题
        from app.db import session

        if session.db_pool is None:
            logger.warning("Database pool not initialized, skip task status update")
            return

        async with session.db_pool.acquire() as conn:
            repo = TaskRepository(conn)
            await repo.update_task_status(task_id, **kwargs)
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")


def update_task_status_sync(task_id: str, **kwargs):
    """同步方式更新任务状态（在 Celery worker 中调用）"""
    try:
        asyncio.run(update_task_status_async(task_id, **kwargs))
    except Exception as e:
        logger.error(f"tasks.run_crawler[{task_id}]: Failed to update task status: {e}")


async def update_hotspot_status_async(hotspot_id: str):
    """异步更新热点状态为 crawled"""
    try:
        # 动态导入，避免循环依赖
        from app.db import vector_session
        from app.schemas.hotspot import HotspotStatus

        if vector_session.pg_pool is None:
            logger.warning(
                "PostgreSQL pool not initialized, skip hotspot status update"
            )
            return

        # 将 hotspot_id 转换为整数
        hotspot_id_int = int(hotspot_id)

        async with vector_session.pg_pool.acquire() as conn:
            # 检查当前该热点的所有任务是否都完成
            from app.db import session as mysql_session

            if mysql_session.db_pool is None:
                logger.warning("MySQL pool not initialized, skip hotspot status check")
                return

            async with mysql_session.db_pool.acquire() as mysql_conn:
                repo = TaskRepository(mysql_conn)
                tasks = await repo.get_tasks_by_hotspot_id(hotspot_id_int)

                # 检查是否所有任务都已完成
                all_completed = all(
                    task.status in ["SUCCESS", "FAILURE"] for task in tasks
                )

                if not all_completed:
                    logger.info(
                        f"Not all tasks completed for hotspot {hotspot_id_int}, "
                        "status will be updated when all tasks finish"
                    )
                    return

            # 所有任务都完成，更新热点状态为 crawled
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    last_crawled_at = CURRENT_TIMESTAMP,
                    crawl_count = crawl_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                HotspotStatus.CRAWLED.value,
                hotspot_id_int,
            )
            logger.info(
                f"Successfully updated hotspot {hotspot_id_int} status to crawled"
            )
    except Exception as e:
        logger.error(f"Failed to update hotspot status: {e}")


def update_hotspot_status_on_crawl_complete(hotspot_id: str):
    """同步方式更新热点状态（在 Celery worker 中调用）"""
    try:
        asyncio.run(update_hotspot_status_async(hotspot_id))
    except Exception as e:
        logger.error(f"tasks.run_crawler: Failed to update hotspot status: {e}")


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
    hotspot_id: str = "",  # 新增热点ID参数
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

    本函数使用 bind=True 装饰器参数，使得 self 参数指向当前 Celery 任务实例。
    通过 self.request.id 可以访问任务的唯一标识符（UUID），该 ID 由 Celery 在
    调用 apply_async() 时自动生成。

    任务 ID 的生成流程：
    1. 外部调用 run_crawler.apply_async(kwargs={...})
    2. Celery 生成 UUID 作为 task.id
    3. 任务发送到消息队列（Redis/RabbitMQ）
    4. Worker 拾取任务执行
    5. 在任务函数内部，self.request.id 即为该 UUID

    self.request 对象提供的属性：
    - self.request.id: 任务 ID（UUID 字符串）
    - self.request.args: 位置参数
    - self.request.kwargs: 关键字参数
    - self.request.retries: 重试次数

    外部调用方式：
    ```python
    task = run_crawler.apply_async(kwargs={
        "platform": "xhs",
        "crawler_type": "search",
        ...
    })
    task_id = task.id  # 获取任务 ID，用于后续状态查询
    ```

    参考文档：
    - https://docs.celeryq.dev/en/stable/userguide/tasks.html
    - https://docs.celeryq.dev/en/stable/reference/celery.app.task.html

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
        hotspot_id: 关联的热点ID（用于触发式爬虫）
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
        f"Starting crawler task: platform={platform}, type={crawler_type}, "
        f"keywords={keywords}, hotspot_id={hotspot_id}"
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
        "hotspot_id": hotspot_id,  # 热点ID参数
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
            stderr=subprocess.STDOUT,  # 将 stderr 重定向到 stdout，这样可以实时捕获所有日志
            env=env,
            cwd=settings.CRAWLER_BASE_PATH,
            text=True,
            bufsize=1,
        )

        # 实时读取输出
        stdout_lines = []

        # 进度跟踪变量
        notes_count = 0  # 已爬取的笔记数量
        max_notes = max_notes_count  # 最大爬取数量
        current_keyword = ""  # 当前关键词
        current_page = 0  # 当前页码

        # 启动后台轮询任务来检查 checkpoint 进度
        import threading

        stop_polling = threading.Event()

        def poll_checkpoint_progress():
            """后台轮询 checkpoint 进度的线程函数"""
            nonlocal notes_count, current_keyword, current_page

            try:
                import sys

                # 动态导入爬虫项目的模块
                if settings.CRAWLER_BASE_PATH not in sys.path:
                    sys.path.insert(0, settings.CRAWLER_BASE_PATH)

                from repo.checkpoint.checkpoint_store import (  # type: ignore
                    CheckpointRepoManager,
                    CheckpointRedisRepo,
                    CheckpointJsonFileRepo,
                )

                # 根据配置选择 checkpoint 存储类型
                checkpoint_storage_type = env.get(
                    "CRAWLER_CHECKPOINT_STORAGE_TYPE", "file"
                )
                if checkpoint_storage_type == "redis":
                    checkpoint_repo = CheckpointRedisRepo()
                else:
                    checkpoint_repo = CheckpointJsonFileRepo(
                        cache_dir=os.path.join(
                            settings.CRAWLER_BASE_PATH, "data/checkpoints"
                        )
                    )
            except ImportError as e:
                logger.error(f"Failed to import checkpoint modules: {e}")
                return

            checkpoint_manager = CheckpointRepoManager(checkpoint_repo)

            last_progress_log_time = 0
            poll_interval = 5  # 每5秒轮询一次

            while not stop_polling.is_set():
                try:
                    # 使用 asyncio.run() 加载 checkpoint
                    checkpoint = asyncio.run(
                        checkpoint_manager.load_checkpoint(
                            platform=platform,
                            mode=crawler_type,
                            checkpoint_id=checkpoint_id if checkpoint_id else None,
                        )
                    )

                    if checkpoint:
                        # 从 checkpoint 获取真实进度
                        crawled_notes = checkpoint.crawled_note_list or []
                        notes_count = len(crawled_notes)
                        current_keyword = checkpoint.current_search_keyword or ""
                        current_page = checkpoint.current_search_page or 0

                        # 计算进度百分比
                        percentage = (
                            min(int((notes_count / max_notes) * 100), 100)
                            if max_notes > 0
                            else 0
                        )

                        # 更新任务状态到数据库
                        update_task_status_sync(
                            self.request.id,
                            status="PROGRESS",
                            progress_current=notes_count,
                            progress_total=max_notes,
                            progress_percentage=percentage,
                        )

                        # 每30秒打印一次进度日志,避免刷屏
                        import time

                        current_time = time.time()
                        if current_time - last_progress_log_time >= 30:
                            logger.info(
                                f"[Checkpoint Progress] {notes_count}/{max_notes} items ({percentage}%) "
                                f"- Keyword: '{current_keyword}', Page: {current_page}"
                            )
                            last_progress_log_time = current_time

                except Exception as e:
                    logger.debug(f"Failed to poll checkpoint progress: {e}")

                # 等待下次轮询,但可以被 stop_polling 事件中断
                stop_polling.wait(poll_interval)

        # 启动后台轮询线程
        polling_thread = threading.Thread(target=poll_checkpoint_progress, daemon=True)
        polling_thread.start()
        logger.info("Started background checkpoint polling thread")

        # 读取爬虫输出日志(主要用于调试和记录)
        try:
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    stdout_lines.append(line)
                    logger.info(f"Crawler output: {line}")
        finally:
            # 停止后台轮询线程
            stop_polling.set()
            polling_thread.join(timeout=5)
            logger.info("Stopped background checkpoint polling thread")

        return_code = process.poll()

        if return_code == 0:
            logger.info("Crawler task completed successfully")
            result = {
                "status": "success",
                "platform": platform,
                "crawler_type": crawler_type,
                "keywords": keywords,
                "notes_crawled": notes_count,  # 实际爬取的笔记数量
                "max_notes": max_notes,  # 最大爬取数量
                "last_keyword": current_keyword,  # 最后处理的关键词
                "last_page": current_page,  # 最后处理的页码
                "stdout": "\n".join(stdout_lines[-50:]),  # 只保留最后50行
                "message": f"Crawler task completed successfully. Crawled {notes_count} notes.",
            }

            # 更新任务状态为 SUCCESS
            update_task_status_sync(
                self.request.id,
                status="SUCCESS",
                result=result,
                progress_current=notes_count,
                progress_total=max_notes,
                progress_percentage=100,
                finished_at=datetime.now(),
            )

            # 如果有 hotspot_id，更新热点状态为 crawled
            if hotspot_id:
                try:
                    update_hotspot_status_on_crawl_complete(hotspot_id)
                    logger.info(f"Updated hotspot {hotspot_id} status to crawled")
                except Exception as e:
                    logger.error(
                        f"Failed to update hotspot status for {hotspot_id}: {str(e)}"
                    )

            return result
        else:
            error_msg = (
                "\n".join(stdout_lines[-20:]) if stdout_lines else "Unknown error"
            )
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
