from typing import List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ==================== 枚举定义 ====================
class Priority(str, Enum):
    """优先级枚举"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PushStatus(str, Enum):
    """推送状态枚举"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


# ==================== 推送队列相关 ====================

class AddToPushQueueRequest(BaseModel):
    """添加到推送队列请求"""

    hotspot_id: int = Field(..., description="热点ID")


class AddToPushQueueResponse(BaseModel):
    """添加到推送队列响应"""

    success: bool
    push_id: int
    message: str


class PushQueueItem(BaseModel):
    """推送队列项"""

    id: int
    hotspot_id: int
    status: PushStatus
    created_at: datetime
    updated_at: datetime


class GetPendingPushResponse(BaseModel):
    """获取待推送报告响应"""

    success: bool
    items: List[PushQueueItem]
    count: int


class UpdatePushStatusRequest(BaseModel):
    """更新推送状态请求"""

    status: PushStatus = Field(..., description="新的推送状态")


class UpdatePushStatusResponse(BaseModel):
    """更新推送状态响应"""

    success: bool
    message: str
    old_status: PushStatus
    new_status: PushStatus
