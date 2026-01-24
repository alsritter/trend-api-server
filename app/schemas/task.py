from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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
    max_comments_count: int = Field(3, ge=1, le=500, description="每条内容最大评论数量")
    hotspot_id: Optional[int] = Field(None, description="关联的热点ID（触发式爬虫）")
    
    # 平台特定的指定ID/URL列表
    xhs_note_url_list: Optional[List[str]] = Field(None, description="小红书笔记URL列表")
    xhs_creator_url_list: Optional[List[str]] = Field(None, description="小红书创作者URL列表")
    weibo_specified_id_list: Optional[List[str]] = Field(None, description="微博指定帖子ID列表")
    weibo_creator_id_list: Optional[List[str]] = Field(None, description="微博创作者ID列表")
    tieba_specified_id_list: Optional[List[str]] = Field(None, description="贴吧指定帖子ID列表")
    tieba_name_list: Optional[List[str]] = Field(None, description="贴吧名称列表")
    tieba_creator_url_list: Optional[List[str]] = Field(None, description="贴吧创作者URL列表")
    bili_creator_id_list: Optional[List[str]] = Field(None, description="B站创作者ID列表")
    bili_specified_id_list: Optional[List[str]] = Field(None, description="B站视频BVID列表")
    dy_specified_id_list: Optional[List[str]] = Field(None, description="抖音指定视频ID列表")
    dy_creator_id_list: Optional[List[str]] = Field(None, description="抖音创作者ID列表(sec_id)")
    ks_specified_id_list: Optional[List[str]] = Field(None, description="快手指定视频ID列表")
    ks_creator_id_list: Optional[List[str]] = Field(None, description="快手创作者ID列表")
    zhihu_creator_url_list: Optional[List[str]] = Field(None, description="知乎创作者URL列表")
    zhihu_specified_id_list: Optional[List[str]] = Field(None, description="知乎指定内容URL列表")


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


class TaskDB(BaseModel):
    """数据库任务模型"""
    id: Optional[int] = None
    task_id: str
    platform: str
    crawler_type: str
    keywords: Optional[str] = None
    status: str
    progress_current: int = 0
    progress_total: int = 0
    progress_percentage: int = 0
    result: Optional[str] = None  # JSON string
    error: Optional[str] = None
    config: Optional[str] = None  # JSON string
    hotspot_id: Optional[int] = None  # 关联的热点ID
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
