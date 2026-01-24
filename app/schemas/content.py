from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class StructuredComment(BaseModel):
    """结构化评论模型 - 统一不同平台的评论数据"""

    platform: str = Field(..., description="平台代码")
    comment_id: str = Field(..., description="评论ID")
    content: Optional[str] = Field(None, description="评论内容")

    # 用户信息
    user_id: str = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    ip_location: Optional[str] = Field(None, description="IP归属地")

    # 互动数据
    liked_count: Optional[int] = Field(None, description="点赞数")
    sub_comment_count: Optional[int] = Field(None, description="子评论数")

    # 时间信息
    create_time: Optional[datetime] = Field(None, description="创建时间")
    add_ts: Optional[int] = Field(None, description="添加时间戳")
    last_modify_ts: Optional[int] = Field(None, description="最后修改时间戳")

    # 平台特有字段
    platform_specific: dict = Field(default_factory=dict, description="平台特有字段")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StructuredContent(BaseModel):
    """结构化内容模型 - 统一不同平台的内容数据"""

    platform: str = Field(..., description="平台代码")
    content_id: str = Field(..., description="内容ID")
    title: Optional[str] = Field(None, description="标题")
    desc: Optional[str] = Field(None, description="描述")
    content_text: Optional[str] = Field(None, description="内容文本")

    # 用户信息
    user_id: str = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    ip_location: Optional[str] = Field(None, description="IP归属地")

    # 互动数据
    liked_count: Optional[int] = Field(None, description="点赞数")
    collected_count: Optional[int] = Field(None, description="收藏数")
    comment_count: Optional[int] = Field(None, description="评论数")
    share_count: Optional[int] = Field(None, description="分享数")
    view_count: Optional[int] = Field(None, description="浏览数")

    # 时间信息
    time: Optional[str] = Field(None, description="时间字符串")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    add_ts: Optional[int] = Field(None, description="添加时间戳")
    last_modify_ts: Optional[int] = Field(None, description="最后修改时间戳")

    # 平台特有字段
    platform_specific: dict = Field(default_factory=dict, description="平台特有字段")

    # 关联数据
    comments: List[StructuredComment] = Field(default_factory=list, description="评论列表")
    hotspot_id: Optional[int] = Field(None, description="关联的热点ID")
    hotspot_keyword: Optional[str] = Field(None, description="关联的热点关键词")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


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
