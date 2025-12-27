from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from celery.result import AsyncResult
from datetime import datetime

from app.schemas.task import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskProgress,
    TaskListItem
)
from app.schemas.common import APIResponse
from app.celery_app.tasks.crawler_tasks import run_crawler, stop_crawler
from app.celery_app.celery import celery_app

router = APIRouter()


@router.post("", response_model=APIResponse[TaskCreateResponse])
async def create_task(request: TaskCreateRequest):
    """
    创建爬虫任务

    - **platform**: 平台名称 (xhs|dy|ks|bili|wb|tieba|zhihu)
    - **crawler_type**: 爬虫类型 (search|detail|creator|homefeed)
    - **keywords**: 搜索关键词（逗号分隔，search类型时建议填写）
    - **enable_checkpoint**: 是否启用断点续爬
    - **max_notes_count**: 最大爬取数量（1-1000）
    - **enable_comments**: 是否爬取评论
    - **enable_sub_comments**: 是否爬取二级评论
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
                "enable_sub_comments": request.enable_sub_comments
            }
        )

        return APIResponse(
            code=0,
            message="Task created successfully",
            data=TaskCreateResponse(
                task_id=task.id,
                status=task.status,
                created_at=datetime.now().isoformat()
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=APIResponse[TaskStatusResponse])
async def get_task_status(task_id: str):
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
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response_data = TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            progress=TaskProgress(current=0, total=0, percentage=0),
            result=None,
            error=None,
            started_at=None,
            finished_at=None
        )

        # 根据状态填充不同的信息
        if result.status == "PROGRESS":
            # 进行中，包含进度信息
            response_data.progress = TaskProgress(**result.info)
        elif result.status == "SUCCESS":
            # 成功完成
            response_data.result = result.result
            response_data.finished_at = datetime.now().isoformat()
        elif result.status == "FAILURE":
            # 执行失败
            response_data.error = str(result.info)
            response_data.finished_at = datetime.now().isoformat()

        return APIResponse(code=0, message="success", data=response_data)
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
            data={"task_id": task_id, "status": "terminating"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[TaskListResponse])
async def list_tasks(
    platform: Optional[str] = Query(None, description="平台名称"),
    status: Optional[str] = Query(None, description="任务状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    查询任务列表（分页）

    注意：当前版本返回空列表，需要实现任务持久化存储功能
    """
    # TODO: 从数据库或 Redis 中查询任务历史
    # 当前返回空列表
    return APIResponse(
        code=0,
        message="success",
        data=TaskListResponse(
            total=0,
            page=page,
            page_size=page_size,
            items=[]
        )
    )
