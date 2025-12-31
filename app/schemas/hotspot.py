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
    created_at: datetime
    updated_at: datetime


class ListClustersResponse(BaseModel):
    """列出聚簇响应"""

    success: bool
    items: List[ClusterInfo]
    count: int


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

    cluster_id: int = Field(..., description="要拆分的簇ID")
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
