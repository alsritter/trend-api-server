from pydantic import BaseModel
from typing import Optional, Any


class ContentItem(BaseModel):
    """通用内容项（用于不同平台的笔记/视频）"""
    # 这里使用动态字段，因为不同平台的字段不同
    # 实际响应将直接返回数据库查询结果
    pass


class ContentListResponse(BaseModel):
    """内容列表响应"""
    total: int
    page: int
    page_size: int
    items: list[dict]  # 使用 dict 以支持不同平台的不同字段


class CommentItem(BaseModel):
    """评论项"""
    pass


class CommentListResponse(BaseModel):
    """评论列表响应"""
    total: int
    page: int
    page_size: int
    items: list[dict]


class CreatorResponse(BaseModel):
    """创作者信息响应"""
    # 直接返回数据库查询结果
    pass
