from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class HotspotStatus(str, Enum):
    """热点状态枚举"""

    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    CRAWLING = "crawling"
    CRAWLED = "crawled"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"
    OUTDATED = "outdated"


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


class HotspotBase(BaseModel):
    """热点基础模型"""

    keyword: str = Field(..., description="原始热词")
    normalized_keyword: Optional[str] = Field(None, description="归一化关键词")
    platforms: List[PlatformInfo] = Field(default_factory=list, description="平台信息")


class AddHotspotKeywordRequest(BaseModel):
    """添加热词请求 - 用于第一阶段AI判断后的结果"""

    analysis: KeywordAnalysis = Field(..., description="AI分析结果")
    platform_data: Optional[dict] = Field(
        None, description="平台原始数据(包含 type, rank, viewnum, date 等)"
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

# ==================== 商业报告相关 ====================
class VirtualProductAnalysis(BaseModel):
    """虚拟产品分析"""

    opportunities: List[str] = Field(default_factory=list)
    feasibility_score: int = Field(..., ge=0, le=100)


class PhysicalProductAnalysis(BaseModel):
    """实体产品分析"""

    opportunities: List[str] = Field(default_factory=list)
    feasibility_score: int = Field(..., ge=0, le=100)


class BusinessReportContent(BaseModel):
    """商业报告内容"""

    summary: str = Field(..., description="简短总结")
    virtual_products: VirtualProductAnalysis = Field(..., description="虚拟产品机会")
    physical_products: PhysicalProductAnalysis = Field(..., description="实体产品机会")
    target_audience: List[str] = Field(default_factory=list, description="目标受众")
    market_size: str = Field(..., description="市场规模估算")
    recommendations: List[str] = Field(default_factory=list, description="建议")


class AddBusinessReportRequest(BaseModel):
    """添加商业报告请求"""

    hotspot_id: int = Field(..., description="热点ID")
    report: BusinessReportContent = Field(..., description="报告内容")
    score: float = Field(..., ge=0, le=100, description="可行性分数")
    priority: Priority = Field(default=Priority.MEDIUM, description="优先级")
    product_types: List[str] = Field(default_factory=list, description="商品类型")


class AddBusinessReportResponse(BaseModel):
    """添加商业报告响应"""

    success: bool
    report_id: int
    message: str


class BusinessReportInfo(BaseModel):
    """商业报告信息"""

    id: int
    hotspot_id: int
    report: BusinessReportContent
    score: float
    priority: Priority
    product_types: Optional[List[str]]
    analyzed_at: datetime
    created_at: datetime


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
    created_at: datetime
    updated_at: datetime


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
class ClusterInfo(BaseModel):
    """聚簇信息"""

    id: int
    cluster_name: str
    member_count: int
    keywords: List[str]
    selected_hotspot_id: Optional[int] = Field(None, description="被选中用于验证的热词ID")
    created_at: datetime
    updated_at: datetime
    statuses: List[str] = Field(default_factory=list, description="聚簇中所有热点的状态列表")
    last_hotspot_update: datetime = Field(..., description="聚簇中热点的最后更新时间")


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
    target_cluster_name: Optional[str] = Field(None, description="目标簇名称（可选，默认使用第一个簇的名称）")


class MergeClustersResponse(BaseModel):
    """合并聚簇响应"""

    success: bool
    cluster_id: int = Field(..., description="合并后的簇ID")
    message: str


class SplitClusterRequest(BaseModel):
    """拆分聚簇请求"""

    hotspot_ids: List[int] = Field(..., min_length=1, description="要移出的热点ID列表")
    new_cluster_name: Optional[str] = Field(None, description="新簇名称（可选，默认使用第一个热点的名称）")


class SplitClusterResponse(BaseModel):
    """拆分聚簇响应"""

    success: bool
    new_cluster_id: Optional[int] = Field(None, description="新创建的簇ID（如果创建了新簇）")
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


class MarkOutdatedHotspotsResponse(BaseModel):
    """标记过时热词响应"""

    success: bool
    message: str
    marked_count: int = Field(..., description="标记的热词数量")
    hotspot_ids: List[int] = Field(default_factory=list, description="被标记的热词ID列表")


# ==================== 触发式爬虫相关 ====================
class TriggerCrawlRequest(BaseModel):
    """触发爬虫请求"""

    hotspot_id: int = Field(..., description="热点ID")
    platforms: List[str] = Field(
        ...,
        description="要爬取的平台列表",
        min_length=1,
        example=["xhs", "dy", "bili"]
    )
    crawler_type: str = Field(
        default="search",
        description="爬虫类型 (search|detail|creator|homefeed)",
        pattern="^(search|detail|creator|homefeed)$"
    )
    max_notes_count: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="每个平台最大爬取数量"
    )
    enable_comments: bool = Field(
        default=True,
        description="是否爬取评论"
    )
    enable_sub_comments: bool = Field(
        default=False,
        description="是否爬取二级评论"
    )
    max_comments_count: int = Field(
        default=20,
        ge=1,
        le=500,
        description="每条内容最大评论数量"
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
    contents: List[dict] = Field(default_factory=list, description="内容列表")
    comments: List[dict] = Field(default_factory=list, description="评论列表")
    total_contents: int
    total_comments: int


class GetHotspotContentsResponse(BaseModel):
    """获取热点关联内容响应"""

    success: bool
    hotspot_id: int
    hotspot_keyword: str
    platforms: List[PlatformContents] = Field(..., description="各平台的完整内容和评论")
    total_contents: int = Field(..., description="所有平台的内容总数")
    total_comments: int = Field(..., description="所有平台的评论总数")
