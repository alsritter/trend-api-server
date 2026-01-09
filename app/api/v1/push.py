from fastapi import APIRouter, HTTPException, Query
import logging
import traceback
from app.services.push_service import push_service
from app.schemas.push import (
    AddToPushQueueRequest,
    AddToPushQueueResponse,
    GetPendingPushResponse,
    UpdatePushStatusRequest,
    UpdatePushStatusResponse,
    PushQueueItem,
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/queue", response_model=AddToPushQueueResponse)
async def add_to_push_queue(request: AddToPushQueueRequest):
    """
    添加到推送队列

    用于第三阶段：
    - 将商业报告加入推送队列
    - 自动设置优先级和分数

    参数：
    - hotspot_id: 热点ID
    - report_id: 报告ID
    - channels: 推送渠道列表（默认为 ["email"]）

    返回：
    - success: 是否成功
    - push_id: 推送队列项ID
    - message: 消息

    异常：
    - 404: 报告不存在
    - 500: 服务器错误
    """
    try:
        result = await push_service.add_to_push_queue(
            hotspot_id=request.hotspot_id,
            report_id=request.report_id,
            channels=request.channels,
        )
        return AddToPushQueueResponse(
            success=result["success"],
            push_id=result["push_id"],
            message=result["message"],
        )
    except ValueError as e:
        logger.error(
            f"添加到推送队列失败(未找到) - hotspot_id: {request.hotspot_id}, "
            f"report_id: {request.report_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"添加到推送队列时发生错误 - hotspot_id: {request.hotspot_id}, "
            f"report_id: {request.report_id}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/pending", response_model=GetPendingPushResponse)
async def get_pending_push_items(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
):
    """
    获取待推送的报告

    返回按优先级和分数排序的待推送项
    自动检查推送间隔（>=2小时）

    参数：
    - limit: 返回数量限制（1-50）

    返回：
    - success: 是否成功
    - items: 待推送项列表
    - count: 返回的项数

    说明：
    - 如果距离上次推送不足2小时，返回空列表
    - 按优先级（high > medium > low）和分数排序
    """
    try:
        items = await push_service.get_pending_push_items(limit)
        return GetPendingPushResponse(success=True, items=items, count=len(items))
    except Exception as e:
        logger.error(
            f"获取待推送项时发生错误 - limit: {limit}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/queue/{push_id}/status", response_model=UpdatePushStatusResponse)
async def update_push_status(push_id: int, request: UpdatePushStatusRequest):
    """
    更新推送状态

    用于标记推送的完成状态或失败信息

    参数：
    - push_id: 推送队列项ID
    - status: 新的推送状态（pending, sent, failed）
    - error_message: 错误信息（如果失败）

    返回：
    - success: 是否成功
    - message: 消息
    - old_status: 旧的状态
    - new_status: 新的状态

    异常：
    - 404: 推送项不存在
    - 500: 服务器错误

    说明：
    - 状态为 sent 时，自动记录 sent_at 时间
    - 状态为 failed 时，自动增加 retry_count
    """
    try:
        result = await push_service.update_push_status(
            push_id=push_id,
            status=request.status,
            error_message=request.error_message,
        )
        return UpdatePushStatusResponse(
            success=result["success"],
            message=result["message"],
            old_status=result["old_status"],
            new_status=result["new_status"],
        )
    except ValueError as e:
        logger.error(
            f"更新推送状态失败(未找到) - push_id: {push_id}, "
            f"new_status: {request.status}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"更新推送状态时发生错误 - push_id: {push_id}, "
            f"new_status: {request.status}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/{push_id}", response_model=PushQueueItem)
async def get_push_item(push_id: int):
    """
    获取推送队列项详情

    参数：
    - push_id: 推送队列项ID

    返回：
    - 推送队列项的完整信息（包含关联的热点关键词和商业报告）

    异常：
    - 404: 推送项不存在
    - 500: 服务器错误
    """
    try:
        item = await push_service.get_push_item(push_id)
        return item
    except ValueError as e:
        logger.error(
            f"获取推送项详情失败(未找到) - push_id: {push_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"获取推送项详情时发生错误 - push_id: {push_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))
