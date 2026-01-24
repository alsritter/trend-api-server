from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from app.schemas.content import StructuredContent
class HotspotStatus(str, Enum):
    """热点状态枚举"""

    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"  # 第一阶段被拒绝（AI初筛）
    SECOND_STAGE_REJECTED = "second_stage_rejected"  # 第二阶段被拒绝（深度分析后）
    CRAWLING = "crawling"
    CRAWLED = "crawled"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"
    OUTDATED = "outdated"



# ==================== 热词价值判断相关 ====================
class ReasoningDetail(BaseModel):
    """推理细节"""

    keep: List[str] = Field(default_factory=list, description="保留原因列表")
    risk: List[str] = Field(default_factory=list, description="风险列表")


class KeywordAnalysis(BaseModel):
    """AI 返回的热词分析结构"""

    title: str = Field(..., description="热词标题")
    confidence: float = Field(..., ge=0, le=1, description="置信度 0-1")
    primary_category: str = Field(..., alias="primaryCategory", description="主要分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    reasoning: ReasoningDetail = Field(..., description="推理详情")
    opportunities: List[str] = Field(default_factory=list, description="商业机会")
    is_remove: bool = Field(..., alias="isRemove", description="是否移除")

    class Config:
        populate_by_name = True


# ==================== 热点相关 ====================
class PlatformInfo(BaseModel):
    """平台信息"""

    platform: str = Field(..., description="平台名称")
    rank: int = Field(..., description="排名")
    heat_score: Optional[int] = Field(None, description="热度分数")
    seen_at: str = Field(..., description="发现时间")


class PlatformDataInput(BaseModel):
    """平台原始数据输入（从外部接收的平台数据）"""

    type: str = Field(..., description="平台类型: xhs, dy, bili, ks, wb, tieba, zhihu")
    rank: Optional[int] = Field(None, description="排名")
    name: Optional[str] = Field(None, description="热词名称")
    viewnum: Optional[str] = Field(None, description="热度值（如 '541.2万'）")
    date: Optional[str] = Field(None, description="发现日期")
    url: Optional[str] = Field(None, description="平台URL链接")
    icon: Optional[str] = Field(None, description="图标URL")
    word_cover: Optional[dict] = Field(None, description="词封面信息")
    word_type: Optional[str] = Field(None, description="词类型")
    
    class Config:
        extra = "allow"  # 允许额外的字段，保持兼容性


class HotspotBase(BaseModel):
    """热点基础模型"""

    keyword: str = Field(..., description="原始热词")
    normalized_keyword: Optional[str] = Field(None, description="归一化关键词")
    platforms: List[PlatformInfo] = Field(default_factory=list, description="平台信息")


class AddHotspotKeywordRequest(BaseModel):
    """添加热词请求 - 用于第一阶段AI判断后的结果"""

    analysis: KeywordAnalysis = Field(..., description="AI分析结果")
    platform_data: Optional[PlatformDataInput] = Field(
        None, description="平台原始数据(包含 type, rank, viewnum, date, url 等)"
    )


class AddHotspotKeywordResponse(BaseModel):
    """添加热词响应"""

    success: bool
    hotspot_id: Optional[int] = None
    message: str
    action: str = Field(..., description="执行的操作: created/rejected/updated")


class CheckHotspotRequest(BaseModel):
    """检查热词是否存在请求"""

    keyword: str = Field(..., description="要检查的热词名称")


class SimilarHotspot(BaseModel):
    """相似热词信息"""

    id: int
    keyword: str
    normalized_keyword: str
    status: HotspotStatus
    first_seen_at: datetime
    last_seen_at: datetime
    appearance_count: int
    similarity: float = Field(..., description="相似度 0-1")
    cluster_id: Optional[int] = None


class CheckHotspotResponse(BaseModel):
    """检查热词响应"""

    exists: bool = Field(..., description="是否已存在")
    action: str = Field(..., description="建议的操作: skip/update/ask_llm")
    hotspot_id: Optional[int] = Field(None, description="如果已存在，返回热点ID")
    similar_hotspots: List[SimilarHotspot] = Field(
        default_factory=list, description="相似的热词列表"
    )
    message: str


# ==================== 热点管理相关 ====================
class HotspotDetail(BaseModel):
    """热点详细信息"""

    id: int
    keyword: str
    normalized_keyword: str
    embedding_model: Optional[str]
    cluster_id: Optional[int]
    first_seen_at: datetime
    last_seen_at: datetime
    appearance_count: int
    platforms: List[PlatformInfo]
    status: HotspotStatus
    last_crawled_at: Optional[datetime]
    crawl_count: int
    crawl_started_at: Optional[datetime]
    crawl_failed_count: int
    is_filtered: bool
    filter_reason: Optional[str]
    filtered_at: Optional[datetime]
    rejection_reason: Optional[str] = Field(None, description="第一阶段被拒绝的理由")
    rejected_at: Optional[datetime] = Field(None, description="第一阶段被拒绝的时间")
    second_stage_rejection_reason: Optional[str] = Field(None, description="第二阶段被拒绝的理由")
    second_stage_rejected_at: Optional[datetime] = Field(None, description="第二阶段被拒绝的时间")
    created_at: datetime
    updated_at: datetime
    # AI 分析详细信息
    tags: Optional[List[str]] = Field(None, description="标签列表")
    confidence: Optional[float] = Field(None, description="置信度 0-1")
    opportunities: Optional[List[str]] = Field(None, description="初筛可能的商业机会")
    reasoning_keep: Optional[List[str]] = Field(None, description="保留原因列表")
    reasoning_risk: Optional[List[str]] = Field(None, description="风险列表")
    platform_url: Optional[str] = Field(None, description="平台URL")
    primary_category: Optional[str] = Field(None, description="主要分类")
    word_cover: Optional[dict] = Field(None, description="词封面信息")


class ListHotspotsRequest(BaseModel):
    """列出热点请求"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: Optional[HotspotStatus] = Field(None, description="状态过滤")
    keyword: Optional[str] = Field(None, description="关键词搜索")


class ListHotspotsResponse(BaseModel):
    """列出热点响应"""

    success: bool
    total: int
    page: int
    page_size: int
    items: List[HotspotDetail]


class DeleteHotspotResponse(BaseModel):
    """删除热点响应"""

    success: bool
    message: str


class GetClusterHotspotsResponse(BaseModel):
    """获取同簇热点响应"""

    success: bool
    cluster_id: int
    items: List[HotspotDetail]
    count: int


class LinkHotspotRequest(BaseModel):
    """关联热点请求 - 复用已有热点信息创建新热点"""

    keyword: str = Field(..., description="新的关键词")
    hotspot_id: int = Field(..., description="要复用信息的热点ID")


class LinkHotspotResponse(BaseModel):
    """关联热点响应"""

    success: bool
    hotspot_id: int = Field(..., description="新创建的热点ID")
    cluster_id: Optional[int] = Field(None, description="关联的簇ID")
    message: str


# ==================== 聚簇管理相关 ====================
class PlatformStat(BaseModel):
    """平台统计信息"""

    platform: str = Field(..., description="平台名称")
    count: int = Field(..., description="该平台的热点数量")


class ClusterInfo(BaseModel):
    """聚簇信息"""

    id: int
    cluster_name: str
    keywords: List[str]
    selected_hotspot_id: Optional[int] = Field(
        None, description="被选中用于验证的热词ID"
    )
    member_count: int = Field(..., description="成员数量（动态计算）")
    created_at: datetime
    updated_at: datetime
    statuses: List[str] = Field(
        default_factory=list, description="聚簇中所有热点的状态列表"
    )
    last_hotspot_update: datetime = Field(..., description="聚簇中热点的最后更新时间")
    platforms: List[PlatformStat] = Field(
        default_factory=list, description="聚簇中包含的平台统计信息"
    )


class ListClustersResponse(BaseModel):
    """列出聚簇响应"""

    success: bool
    items: List[ClusterInfo]
    count: int


class CreateClusterRequest(BaseModel):
    """创建聚簇请求"""

    cluster_name: str = Field(..., description="聚簇名称")
    hotspot_ids: Optional[List[int]] = Field(None, description="初始热点ID列表（可选）")


class CreateClusterResponse(BaseModel):
    """创建聚簇响应"""

    success: bool
    cluster_id: int = Field(..., description="新创建的簇ID")
    message: str


class MergeClustersRequest(BaseModel):
    """合并聚簇请求"""

    source_cluster_ids: List[int] = Field(
        ..., min_length=2, description="要合并的源簇ID列表（至少2个）"
    )
    target_cluster_name: Optional[str] = Field(
        None, description="目标簇名称（可选，默认使用第一个簇的名称）"
    )


class MergeClustersResponse(BaseModel):
    """合并聚簇响应"""

    success: bool
    cluster_id: int = Field(..., description="合并后的簇ID")
    message: str


class SplitClusterRequest(BaseModel):
    """拆分聚簇请求"""

    hotspot_ids: List[int] = Field(..., min_length=1, description="要移出的热点ID列表")
    new_cluster_name: Optional[str] = Field(
        None, description="新簇名称（可选，默认使用第一个热点的名称）"
    )


class SplitClusterResponse(BaseModel):
    """拆分聚簇响应"""

    success: bool
    new_cluster_id: Optional[int] = Field(
        None, description="新创建的簇ID（如果创建了新簇）"
    )
    message: str


class UpdateClusterRequest(BaseModel):
    """更新聚簇请求"""

    cluster_name: str = Field(..., description="簇名称")


class UpdateClusterResponse(BaseModel):
    """更新聚簇响应"""

    success: bool
    message: str


class DeleteClusterResponse(BaseModel):
    """删除聚簇响应"""

    success: bool
    message: str


class RemoveHotspotFromClusterRequest(BaseModel):
    """从聚簇中移除热点请求"""

    hotspot_id: int = Field(..., description="热点ID")


class RemoveHotspotFromClusterResponse(BaseModel):
    """从聚簇中移除热点响应"""

    success: bool
    message: str


# ==================== 验证热词列表相关 ====================
class ValidatedHotspotItem(BaseModel):
    """验证热词列表项"""

    id: int
    keyword: str
    cluster_id: Optional[int]
    first_seen_at: datetime
    last_seen_at: datetime
    appearance_count: int
    platforms: List[PlatformInfo]
    created_at: datetime
    updated_at: datetime


class ListValidatedHotspotsResponse(BaseModel):
    """列出待验证热词响应"""

    success: bool
    total: int
    items: List[ValidatedHotspotItem]


class UpdateHotspotStatusRequest(BaseModel):
    """更新热词状态请求"""

    status: HotspotStatus = Field(..., description="新的状态")


class UpdateHotspotStatusResponse(BaseModel):
    """更新热词状态响应"""

    success: bool
    message: str
    old_status: str = Field(..., description="旧状态")
    new_status: str = Field(..., description="新状态")


class UpdateHotspotStatusAndSetRepresentativeRequest(BaseModel):
    """更新热词状态并设置为聚簇代表请求"""

    status: HotspotStatus = Field(..., description="新的状态")
    set_as_representative: bool = Field(
        default=True, description="是否设置为聚簇代表（如果有cluster_id）"
    )


class UpdateHotspotStatusAndSetRepresentativeResponse(BaseModel):
    """更新热词状态并设置为聚簇代表响应"""

    success: bool
    message: str
    old_status: str = Field(..., description="旧状态")
    new_status: str = Field(..., description="新状态")
    cluster_id: Optional[int] = Field(None, description="聚簇ID")
    is_cluster_representative: bool = Field(
        default=False, description="是否为聚簇代表"
    )


class MarkOutdatedHotspotsResponse(BaseModel):
    """标记过时热词响应"""

    success: bool
    message: str
    marked_count: int = Field(..., description="标记的热词数量")
    hotspot_ids: List[int] = Field(
        default_factory=list, description="被标记的热词ID列表"
    )


# ==================== 触发式爬虫相关 ====================
class TriggerCrawlRequest(BaseModel):
    """触发爬虫请求"""

    hotspot_id: int = Field(..., description="热点ID")
    platforms: List[str] = Field(
        ..., description="要爬取的平台列表", min_length=1, example=["xhs", "dy", "bili"]
    )
    crawler_type: str = Field(
        default="search",
        description="爬虫类型 (search|detail|creator|homefeed)",
        pattern="^(search|detail|creator|homefeed)$",
    )
    max_notes_count: int = Field(
        default=10, ge=1, le=1000, description="每个平台最大爬取数量"
    )
    enable_comments: bool = Field(default=True, description="是否爬取评论")
    enable_sub_comments: bool = Field(default=False, description="是否爬取二级评论")
    max_comments_count: int = Field(
        default=3, ge=1, le=500, description="每条内容最大评论数量"
    )


class TriggerCrawlResponse(BaseModel):
    """触发爬虫响应"""

    success: bool
    message: str
    hotspot_id: int
    task_ids: List[str] = Field(..., description="创建的爬虫任务ID列表")
    total_tasks: int = Field(..., description="创建的任务总数")


class CrawlTaskInfo(BaseModel):
    """爬虫任务信息"""

    task_id: str
    platform: str
    status: str
    progress_current: int = 0
    progress_total: int = 0
    progress_percentage: int = 0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


class GetHotspotCrawlStatusResponse(BaseModel):
    """获取热点爬取状态响应"""

    success: bool
    hotspot_id: int
    hotspot_keyword: str
    hotspot_status: HotspotStatus
    tasks: List[CrawlTaskInfo]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int


class CrawledHotspotItem(BaseModel):
    """已爬取热点列表项"""

    id: int
    keyword: str
    cluster_id: Optional[int]
    status: HotspotStatus
    last_seen_at: datetime
    last_crawled_at: Optional[datetime]
    crawl_count: int
    platforms: List[PlatformInfo]
    created_at: datetime
    updated_at: datetime


class ListCrawledHotspotsResponse(BaseModel):
    """列出已爬取热点响应"""

    success: bool
    total: int
    page: int
    page_size: int
    items: List[CrawledHotspotItem]


# ==================== 热点内容关联相关 ====================
class PlatformContents(BaseModel):
    """平台内容详情"""

    platform: str
    contents: List[StructuredContent] = Field(default_factory=list, description="结构化内容列表")
    total_contents: int
    total_comments: int


class GetHotspotContentsResponse(BaseModel):
    """获取热点关联内容响应"""

    success: bool
    message: str = Field(default="获取热点内容成功", description="响应消息")
    hotspot_id: int
    hotspot_keyword: str
    platforms: List[PlatformContents] = Field(..., description="各平台的完整内容和评论")
    total_contents: int = Field(..., description="所有平台的内容总数")
    total_comments: int = Field(..., description="所有平台的评论总数")


# ==================== 拒绝热词相关 ====================
class RejectHotspotRequest(BaseModel):
    """拒绝热词请求（第一阶段）"""

    rejection_reason: str = Field(..., description="拒绝原因", min_length=1, max_length=500)


class RejectHotspotResponse(BaseModel):
    """拒绝热词响应（第一阶段）"""

    success: bool
    message: str
    hotspot_id: int
    old_status: str = Field(..., description="旧状态")


class RejectSecondStageRequest(BaseModel):
    """拒绝热词请求（第二阶段）"""

    rejection_reason: str = Field(..., description="第二阶段拒绝原因", min_length=1, max_length=500)


class RejectSecondStageResponse(BaseModel):
    """拒绝热词响应（第二阶段）"""

    success: bool
    message: str
    hotspot_id: int
    old_status: str = Field(..., description="旧状态")


class RejectedHotspotItem(BaseModel):
    """被拒绝的热词列表项"""

    id: int
    keyword: str
    status: HotspotStatus
    rejection_reason: Optional[str]
    rejected_at: Optional[datetime]
    first_seen_at: datetime
    last_seen_at: datetime
    platforms: List[PlatformInfo]
    created_at: datetime
    updated_at: datetime
