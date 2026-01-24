from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class StructuredComment(BaseModel):
    """结构化评论模型 - 统一不同平台的评论数据"""

    # 通用字段
    comment_id: Optional[str] = Field(None, description="评论ID")
    content: Optional[str] = Field(None, description="评论内容")

    # 用户信息
    user_id: Optional[str] = Field(None, description="用户ID")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    ip_location: Optional[str] = Field(None, description="IP归属地")

    # 互动数据
    like_count: Optional[int] = Field(None, description="点赞数")
    sub_comment_count: Optional[int] = Field(None, description="子评论数")

    # 时间信息
    create_time: Optional[str] = Field(None, description="创建时间")
    add_ts: Optional[int] = Field(None, description="添加时间戳")
    last_modify_ts: Optional[int] = Field(None, description="最后修改时间戳")

    # 平台特有字段 - 小红书
    note_id: Optional[str] = Field(None, description="笔记ID (xhs)")
    note_url: Optional[str] = Field(None, description="笔记URL (xhs/wb/tieba)")
    pictures: Optional[list] = Field(None, description="图片列表 (xhs/dy)")
    parent_comment_id: Optional[str] = Field(None, description="父评论ID")
    target_comment_id: Optional[str] = Field(None, description="目标评论ID (xhs)")

    # B站
    video_id: Optional[str] = Field(None, description="视频ID (bili/ks)")

    # 抖音
    aweme_id: Optional[str] = Field(None, description="抖音视频ID (dy)")
    sec_uid: Optional[str] = Field(None, description="加密用户ID (dy)")
    short_user_id: Optional[str] = Field(None, description="短用户ID (dy)")
    user_unique_id: Optional[str] = Field(None, description="用户唯一ID (dy)")
    user_signature: Optional[str] = Field(None, description="用户签名 (dy)")
    reply_to_reply_id: Optional[str] = Field(None, description="回复的回复ID (dy)")

    # 微博
    gender: Optional[str] = Field(None, description="性别 (wb)")
    profile_url: Optional[str] = Field(None, description="用户主页URL (wb)")
    create_date_time: Optional[str] = Field(None, description="创建日期时间 (wb)")

    # 贴吧
    user_link: Optional[str] = Field(None, description="用户链接 (tieba)")
    tieba_id: Optional[str] = Field(None, description="贴吧ID (tieba)")
    tieba_name: Optional[str] = Field(None, description="贴吧名称 (tieba)")
    tieba_link: Optional[str] = Field(None, description="贴吧链接 (tieba)")
    publish_time: Optional[str] = Field(None, description="发布时间 (tieba)")

    # 知乎
    content_id: Optional[str] = Field(None, description="内容ID (zhihu)")
    content_type: Optional[str] = Field(None, description="内容类型 (zhihu)")
    dislike_count: Optional[int] = Field(None, description="踩数 (zhihu)")
    user_link: Optional[str] = Field(None, description="用户链接 (zhihu)")

    # 热点关联
    hotspot_id: Optional[int] = Field(None, description="关联的热点ID")
    id: Optional[int] = Field(None, description="数据库ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StructuredContent(BaseModel):
    """结构化内容模型 - 统一不同平台的内容数据"""

    # 通用字段
    title: Optional[str] = Field(None, description="标题")
    desc: Optional[str] = Field(None, description="描述")

    # 用户信息
    user_id: Optional[str] = Field(None, description="用户ID")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    ip_location: Optional[str] = Field(None, description="IP归属地")

    # 互动数据
    liked_count: Optional[int] = Field(None, description="点赞数")
    collected_count: Optional[int] = Field(None, description="收藏数")
    comment_count: Optional[int] = Field(None, description="评论数")
    share_count: Optional[int] = Field(None, description="分享数")

    # 时间信息
    time: Optional[str] = Field(None, description="时间字符串")
    add_ts: Optional[int] = Field(None, description="添加时间戳")
    last_modify_ts: Optional[int] = Field(None, description="最后修改时间戳")

    # 平台特有字段 - 小红书
    note_id: Optional[str] = Field(None, description="笔记ID (xhs)")
    note_url: Optional[str] = Field(None, description="笔记URL (xhs/wb/tieba)")
    type: Optional[str] = Field(None, description="类型 (xhs/bili/ks)")
    video_url: Optional[str] = Field(None, description="视频URL (xhs/wb/bili/ks)")
    last_update_time: Optional[str] = Field(None, description="最后更新时间 (xhs)")
    image_list: Optional[list] = Field(None, description="图片列表 (xhs/wb)")
    tag_list: Optional[list] = Field(None, description="标签列表 (xhs)")
    source_keyword: Optional[str] = Field(None, description="来源关键词")

    # B站
    video_id: Optional[str] = Field(None, description="视频ID (bili/ks)")
    bvid: Optional[str] = Field(None, description="B站BV号 (bili)")
    video_play_count: Optional[int] = Field(None, description="播放量 (bili)")
    video_danmaku: Optional[int] = Field(None, description="弹幕数 (bili)")
    video_cover_url: Optional[str] = Field(None, description="视频封面 (bili/ks)")
    duration: Optional[int] = Field(None, description="时长 (bili)")

    # 抖音
    aweme_id: Optional[str] = Field(None, description="抖音视频ID (dy)")
    aweme_type: Optional[str] = Field(None, description="抖音类型 (dy)")
    sec_uid: Optional[str] = Field(None, description="加密用户ID (dy)")
    short_user_id: Optional[str] = Field(None, description="短用户ID (dy)")
    user_unique_id: Optional[str] = Field(None, description="用户唯一ID (dy)")
    user_signature: Optional[str] = Field(None, description="用户签名 (dy)")
    aweme_url: Optional[str] = Field(None, description="抖音URL (dy)")
    cover_url: Optional[str] = Field(None, description="封面URL (dy)")
    video_download_url: Optional[str] = Field(None, description="视频下载URL (dy)")
    is_ai_generated: Optional[bool] = Field(None, description="是否AI生成 (dy)")

    # 快手
    video_play_url: Optional[str] = Field(None, description="播放URL (ks)")
    viewd_count: Optional[int] = Field(None, description="观看数 (ks)")

    # 微博
    content: Optional[str] = Field(None, description="内容文本 (wb)")
    gender: Optional[str] = Field(None, description="性别 (wb)")
    profile_url: Optional[str] = Field(None, description="用户主页URL (wb)")
    create_date_time: Optional[str] = Field(None, description="创建日期时间 (wb)")
    shared_count: Optional[int] = Field(None, description="分享数 (wb)")

    # 贴吧
    user_nickname: Optional[str] = Field(None, description="用户昵称 (tieba)")
    user_avatar: Optional[str] = Field(None, description="用户头像 (tieba)")
    user_link: Optional[str] = Field(None, description="用户链接 (tieba)")
    tieba_id: Optional[str] = Field(None, description="贴吧ID (tieba)")
    tieba_name: Optional[str] = Field(None, description="贴吧名称 (tieba)")
    tieba_link: Optional[str] = Field(None, description="贴吧链接 (tieba)")
    total_replay_num: Optional[int] = Field(None, description="回复总数 (tieba)")
    total_replay_page: Optional[int] = Field(None, description="回复总页数 (tieba)")
    publish_time: Optional[str] = Field(None, description="发布时间 (tieba/zhihu)")

    # 知乎
    content_text: Optional[str] = Field(None, description="内容文本 (zhihu)")
    content_id: Optional[str] = Field(None, description="内容ID (zhihu)")
    content_type: Optional[str] = Field(None, description="内容类型 (zhihu)")
    content_url: Optional[str] = Field(None, description="内容URL (zhihu)")
    question_id: Optional[str] = Field(None, description="问题ID (zhihu)")
    voteup_count: Optional[int] = Field(None, description="赞同数 (zhihu)")
    created_time: Optional[str] = Field(None, description="创建时间 (zhihu)")
    updated_time: Optional[str] = Field(None, description="更新时间 (zhihu)")
    user_url_token: Optional[str] = Field(None, description="用户URL token (zhihu)")

    # 关联数据
    comments: List[StructuredComment] = Field(default_factory=list, description="评论列表")
    hotspot_id: Optional[int] = Field(None, description="关联的热点ID")
    id: Optional[int] = Field(None, description="数据库ID")

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
