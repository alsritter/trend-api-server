from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.hotspot import (
    Priority,
    PushStatus,
    BusinessReportContent,
)


# ==================== 推送队列相关 ====================
class AddToPushQueueRequest(BaseModel):
    """添加到推送队列请求"""

    hotspot_id: int = Field(..., description="热点ID")
    report_id: int = Field(..., description="报告ID")
    channels: List[str] = Field(
        default_factory=lambda: ["email"], description="推送渠道"
    )


class AddToPushQueueResponse(BaseModel):
    """添加到推送队列响应"""

    success: bool
    push_id: int
    message: str


class PushQueueItem(BaseModel):
    """推送队列项"""

    id: int
    hotspot_id: int
    report_id: int
    priority: Priority
    score: float
    status: PushStatus
    channels: List[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    # 额外关联信息
    keyword: Optional[str] = None
    report: Optional[BusinessReportContent] = None


class GetPendingPushResponse(BaseModel):
    """获取待推送报告响应"""

    success: bool
    items: List[PushQueueItem]
    count: int


class UpdatePushStatusRequest(BaseModel):
    """更新推送状态请求"""

    status: PushStatus = Field(..., description="新的推送状态")
    error_message: Optional[str] = Field(None, description="错误信息（如果失败）")


class UpdatePushStatusResponse(BaseModel):
    """更新推送状态响应"""

    success: bool
    message: str
    old_status: PushStatus
    new_status: PushStatus
