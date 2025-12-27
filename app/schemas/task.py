from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """创建爬虫任务请求"""
    platform: str = Field(..., description="平台名称", pattern="^(xhs|dy|ks|bili|wb|tieba|zhihu)$")
    crawler_type: str = Field(..., description="爬虫类型", pattern="^(search|detail|creator|homefeed)$")
    keywords: Optional[str] = Field(None, description="搜索关键词（逗号分隔）")
    enable_checkpoint: bool = Field(True, description="是否启用断点续爬")
    checkpoint_id: Optional[str] = Field(None, description="指定检查点ID")
    max_notes_count: int = Field(10, ge=1, le=1000, description="最大爬取数量")
    enable_comments: bool = Field(True, description="是否爬取评论")
    enable_sub_comments: bool = Field(False, description="是否爬取二级评论")
    max_comments_count: int = Field(20, ge=1, le=500, description="每条内容最大评论数量")


class TaskCreateResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: str
    created_at: str


class TaskProgress(BaseModel):
    """任务进度"""
    current: int = 0
    total: int = 0
    percentage: int = 0


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: Optional[TaskProgress] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class TaskListItem(BaseModel):
    """任务列表项"""
    task_id: str
    platform: str
    crawler_type: str
    status: str
    created_at: str


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    page: int
    page_size: int
    items: list[TaskListItem]
