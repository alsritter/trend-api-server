from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from celery.result import AsyncResult
from datetime import datetime
import json

from app.schemas.task import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskProgress,
    TaskListItem,
)
from app.schemas.common import APIResponse
from app.celery_app.tasks.crawler_tasks import run_crawler, stop_crawler
from app.celery_app.celery import celery_app
from app.db.session import get_db
from app.db.task_repo import TaskRepository

router = APIRouter()


@router.post("", response_model=APIResponse[TaskCreateResponse])
async def create_task(request: TaskCreateRequest, conn=Depends(get_db)):
    """
    创建爬虫任务

    - **platform**: 平台名称 (xhs|dy|ks|bili|wb|tieba|zhihu)
    - **crawler_type**: 爬虫类型 (search|detail|creator|homefeed)
    - **keywords**: 搜索关键词（逗号分隔，search类型时建议填写）
    - **enable_checkpoint**: 是否启用断点续爬
    - **max_notes_count**: 最大爬取数量（1-1000）
    - **enable_comments**: 是否爬取评论
    - **enable_sub_comments**: 是否爬取二级评论
    - **max_comments_count**: 每条内容最大评论数量（1-500）

    平台特定参数（根据 platform 和 crawler_type 选择）：
    - **xhs_note_url_list**: 小红书笔记URL列表（detail类型）
    - **xhs_creator_url_list**: 小红书创作者URL列表（creator类型）
    - **weibo_specified_id_list**: 微博指定帖子ID列表（detail类型）
    - **weibo_creator_id_list**: 微博创作者ID列表（creator类型）
    - **tieba_specified_id_list**: 贴吧指定帖子ID列表（detail类型）
    - **tieba_name_list**: 贴吧名称列表
    - **tieba_creator_url_list**: 贴吧创作者URL列表（creator类型）
    - **bili_creator_id_list**: B站创作者ID列表（creator类型）
    - **bili_specified_id_list**: B站视频BVID列表（detail类型）
    - **dy_specified_id_list**: 抖音指定视频ID列表（detail类型）
    - **dy_creator_id_list**: 抖音创作者ID列表（creator类型）
    - **ks_specified_id_list**: 快手指定视频ID列表（detail类型）
    - **ks_creator_id_list**: 快手创作者ID列表（creator类型）
    - **zhihu_creator_url_list**: 知乎创作者URL列表（creator类型）
    - **zhihu_specified_id_list**: 知乎指定内容URL列表（detail类型）
    """
    try:
        # 调用 Celery 任务
        task = run_crawler.apply_async(
            kwargs={
                "platform": request.platform,
                "crawler_type": request.crawler_type,
                "keywords": request.keywords or "",
                "enable_checkpoint": request.enable_checkpoint,
                "checkpoint_id": request.checkpoint_id or "",
                "max_notes_count": request.max_notes_count,
                "enable_comments": request.enable_comments,
                "enable_sub_comments": request.enable_sub_comments,
                "max_comments_count": request.max_comments_count,
                # 平台特定的ID/URL列表
                "xhs_note_url_list": request.xhs_note_url_list,
                "xhs_creator_url_list": request.xhs_creator_url_list,
                "weibo_specified_id_list": request.weibo_specified_id_list,
                "weibo_creator_id_list": request.weibo_creator_id_list,
                "tieba_specified_id_list": request.tieba_specified_id_list,
                "tieba_name_list": request.tieba_name_list,
                "tieba_creator_url_list": request.tieba_creator_url_list,
                "bili_creator_id_list": request.bili_creator_id_list,
                "bili_specified_id_list": request.bili_specified_id_list,
                "dy_specified_id_list": request.dy_specified_id_list,
                "dy_creator_id_list": request.dy_creator_id_list,
                "ks_specified_id_list": request.ks_specified_id_list,
                "ks_creator_id_list": request.ks_creator_id_list,
                "zhihu_creator_url_list": request.zhihu_creator_url_list,
                "zhihu_specified_id_list": request.zhihu_specified_id_list,
            }
        )

        # 保存任务到数据库
        repo = TaskRepository(conn)

        # 准备任务配置（用于保存到数据库）
        task_config = {
            "enable_checkpoint": request.enable_checkpoint,
            "checkpoint_id": request.checkpoint_id,
            "max_notes_count": request.max_notes_count,
            "enable_comments": request.enable_comments,
            "enable_sub_comments": request.enable_sub_comments,
            "max_comments_count": request.max_comments_count,
        }

        # 添加平台特定参数到配置中
        platform_params = {}
        for field_name in [
            "xhs_note_url_list",
            "xhs_creator_url_list",
            "weibo_specified_id_list",
            "weibo_creator_id_list",
            "tieba_specified_id_list",
            "tieba_name_list",
            "tieba_creator_url_list",
            "bili_creator_id_list",
            "bili_specified_id_list",
            "dy_specified_id_list",
            "dy_creator_id_list",
            "ks_specified_id_list",
            "ks_creator_id_list",
            "zhihu_creator_url_list",
            "zhihu_specified_id_list",
        ]:
            value = getattr(request, field_name)
            if value is not None:
                platform_params[field_name] = value

        if platform_params:
            task_config["platform_params"] = platform_params

        await repo.create_task(
            task_id=task.id,
            platform=request.platform,
            crawler_type=request.crawler_type,
            keywords=request.keywords,
            config=task_config,
            hotspot_id=request.hotspot_id,
        )

        return APIResponse(
            code=0,
            message="Task created successfully",
            data=TaskCreateResponse(
                task_id=task.id,
                status=task.status,
                created_at=datetime.now().isoformat(),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=APIResponse[TaskStatusResponse])
async def get_task_status(task_id: str, conn=Depends(get_db)):
    """
    查询任务状态

    - **task_id**: Celery 任务 ID

    返回状态：
    - PENDING: 待执行
    - STARTED: 执行中
    - PROGRESS: 进行中（带进度信息）
    - SUCCESS: 成功完成
    - FAILURE: 执行失败
    - RETRY: 重试中
    - REVOKED: 已取消
    """
    try:
        # 先从数据库获取任务信息
        repo = TaskRepository(conn)
        db_task = await repo.get_task_by_task_id(task_id)

        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 从 Celery 获取实时状态（优先使用）
        result = AsyncResult(task_id, app=celery_app)

        # 使用数据库记录的状态，除非 Celery 有更新的状态
        current_status = db_task.status
        if result.status in ["PROGRESS", "SUCCESS", "FAILURE", "STARTED", "RETRY"]:
            current_status = result.status

        response_data = TaskStatusResponse(
            task_id=task_id,
            status=current_status,
            progress=TaskProgress(
                current=db_task.progress_current,
                total=db_task.progress_total,
                percentage=db_task.progress_percentage,
            ),
            result=json.loads(db_task.result) if db_task.result else None,
            error=db_task.error,
            started_at=db_task.started_at.isoformat() if db_task.started_at else None,
            finished_at=db_task.finished_at.isoformat()
            if db_task.finished_at
            else None,
        )

        # 如果 Celery 有进度信息，优先使用
        if result.status == "PROGRESS" and isinstance(result.info, dict):
            response_data.progress = TaskProgress(**result.info)

        return APIResponse(code=0, message="success", data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """
    停止任务

    - **task_id**: Celery 任务 ID

    注意：停止任务可能需要几秒钟时间
    """
    try:
        stop_crawler.delay(task_id)
        return APIResponse(
            code=0,
            message="Task termination requested",
            data={"task_id": task_id, "status": "terminating"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[TaskListResponse])
async def list_tasks(
    platform: Optional[str] = Query(None, description="平台名称"),
    status: Optional[str] = Query(None, description="任务状态"),
    hotspot_id: Optional[int] = Query(None, description="热点ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    conn=Depends(get_db),
):
    """
    查询任务列表（分页）

    支持按平台、状态和热点ID筛选
    """
    try:
        repo = TaskRepository(conn)
        tasks, total = await repo.list_tasks(
            platform=platform,
            status=status,
            hotspot_id=hotspot_id,
            page=page,
            page_size=page_size,
        )

        items = [
            TaskListItem(
                task_id=task.task_id,
                platform=task.platform,
                crawler_type=task.crawler_type,
                status=task.status,
                created_at=task.created_at.isoformat(),
            )
            for task in tasks
        ]

        return APIResponse(
            code=0,
            message="success",
            data=TaskListResponse(
                total=total,
                page=page,
                page_size=page_size,
                items=items,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
