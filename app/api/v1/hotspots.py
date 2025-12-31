from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.hotspot_service import hotspot_service
from app.schemas.hotspot import (
    # 请求/响应模型
    AddHotspotKeywordRequest,
    AddHotspotKeywordResponse,
    CheckHotspotRequest,
    CheckHotspotResponse,
    AddBusinessReportRequest,
    AddBusinessReportResponse,
    AddToPushQueueRequest,
    AddToPushQueueResponse,
    GetPendingPushResponse,
    ListHotspotsResponse,
    DeleteHotspotResponse,
    GetClusterHotspotsResponse,
    LinkHotspotRequest,
    LinkHotspotResponse,
    HotspotStatus,
    HotspotDetail,
    # 聚簇管理
    ListClustersResponse,
    MergeClustersRequest,
    MergeClustersResponse,
    SplitClusterRequest,
    SplitClusterResponse,
    UpdateClusterRequest,
    UpdateClusterResponse,
    DeleteClusterResponse,
    RemoveHotspotFromClusterRequest,
    RemoveHotspotFromClusterResponse,
)

router = APIRouter()


# ==================== 核心业务接口 ====================


@router.post("/add-keyword", response_model=AddHotspotKeywordResponse)
async def add_keyword_from_analysis(request: AddHotspotKeywordRequest):
    """
    新增词的接口 - 根据AI分析结果添加热词

    用于第一阶段AI判断后：
    - 如果是低价值词（isRemove=true），添加到热点表，状态设为 rejected
    - 如果是有价值词（isRemove=false），添加到热点表，状态设为 pending_validation
    """
    try:
        result = await hotspot_service.add_keyword_from_analysis(
            request.analysis, request.platform_data
        )
        return AddHotspotKeywordResponse(
            success=True,
            hotspot_id=result["hotspot_id"],
            message=result["message"],
            action=result["action"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-exists", response_model=CheckHotspotResponse)
async def check_hotspot_exists(request: CheckHotspotRequest):
    """
    检查热词是否已存在

    多维度判断：
    1. 完全匹配 -> 返回 exists=True, action=skip
    2. 高相似度（>=90%）-> 返回 exists=True, action=update，并更新时间
    3. 中等相似度（75-90%）-> 返回 exists=False, action=ask_llm，返回相似词列表
    4. 无相似 -> 返回 exists=False, action=create
    """
    try:
        result = await hotspot_service.check_hotspot_exists(request.keyword)
        return CheckHotspotResponse(
            exists=result["exists"],
            action=result["action"],
            hotspot_id=result["hotspot_id"],
            similar_hotspots=result["similar_hotspots"],
            message=result["message"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-report", response_model=AddBusinessReportResponse)
async def add_business_report(request: AddBusinessReportRequest):
    """
    添加商业报告

    用于第三阶段：
    - 接收AI生成的商业分析报告
    - 自动更新热点状态为 analyzed
    """
    try:
        result = await hotspot_service.add_business_report(
            hotspot_id=request.hotspot_id,
            report=request.report,
            score=request.score,
            priority=request.priority,
            product_types=request.product_types,
        )
        return AddBusinessReportResponse(
            success=result["success"],
            report_id=result["report_id"],
            message=result["message"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push-queue", response_model=AddToPushQueueResponse)
async def add_to_push_queue(request: AddToPushQueueRequest):
    """
    添加到推送队列

    用于第三阶段：
    - 将商业报告加入推送队列
    - 自动设置优先级和分数
    """
    try:
        result = await hotspot_service.add_to_push_queue(
            hotspot_id=request.hotspot_id,
            report_id=request.report_id,
            channels=request.channels,
        )
        return AddToPushQueueResponse(
            success=result["success"],
            push_id=result["push_id"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/push-queue/pending", response_model=GetPendingPushResponse)
async def get_pending_push_items(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
):
    """
    获取待推送的报告

    返回按优先级和分数排序的待推送项
    自动检查推送间隔（>=2小时）
    """
    try:
        items = await hotspot_service.get_pending_push_items(limit)
        return GetPendingPushResponse(success=True, items=items, count=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 前端管理接口 ====================


@router.get("/list", response_model=ListHotspotsResponse)
async def list_hotspots(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=1000, description="每页数量"),
    status: Optional[HotspotStatus] = Query(None, description="状态过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
):
    """
    列出热点（分页、过滤、搜索）

    支持：
    - 分页
    - 按状态过滤
    - 关键词模糊搜索
    """
    try:
        result = await hotspot_service.list_hotspots(
            page=page, page_size=page_size, status=status, keyword=keyword
        )
        return ListHotspotsResponse(
            success=True,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            items=result["items"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/{cluster_id}/hotspots", response_model=GetClusterHotspotsResponse)
async def get_cluster_hotspots(cluster_id: int):
    """
    获取同簇的所有热点

    返回同一个簇中的所有相关热点
    """
    try:
        items = await hotspot_service.get_cluster_hotspots(cluster_id)
        return GetClusterHotspotsResponse(
            success=True, cluster_id=cluster_id, items=items, count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{hotspot_id}", response_model=DeleteHotspotResponse)
async def delete_hotspot(hotspot_id: int):
    """
    删除热点

    级联删除相关的商业报告和推送队列项
    """
    try:
        result = await hotspot_service.delete_hotspot(hotspot_id)
        return DeleteHotspotResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link", response_model=LinkHotspotResponse)
async def link_hotspot(request: LinkHotspotRequest):
    """
    关联热点 - 复用已有热点的分析信息创建新热点

    功能：
    - 复用指定热点的分析信息（状态、过滤信息、平台信息等）
    - 为新关键词生成新的向量
    - 创建新的热点记录
    - 自动将新热点添加到同一个聚簇中（如果源热点没有簇则创建新簇）
    """
    try:
        result = await hotspot_service.link_hotspot(
            keyword=request.keyword, source_hotspot_id=request.hotspot_id
        )
        return LinkHotspotResponse(
            success=result["success"],
            hotspot_id=result["hotspot_id"],
            cluster_id=result["cluster_id"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 聚簇管理接口 ====================


@router.get("/clusters", response_model=ListClustersResponse)
async def list_clusters():
    """
    列出所有聚簇

    返回所有聚簇的基本信息
    """
    try:
        items = await hotspot_service.list_clusters()
        return ListClustersResponse(success=True, items=items, count=len(items))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{hotspot_id}", response_model=HotspotDetail)
async def get_hotspot(hotspot_id: int):
    """
    获取热点详情

    返回热点的完整信息
    """
    try:
        hotspot = await hotspot_service.get_hotspot_by_id(hotspot_id)
        if not hotspot:
            raise HTTPException(status_code=404, detail=f"热点 {hotspot_id} 不存在")
        return hotspot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clusters/merge", response_model=MergeClustersResponse)
async def merge_clusters(request: MergeClustersRequest):
    """
    合并多个聚簇

    功能：
    - 将多个聚簇合并为一个
    - 更新所有热点的cluster_id
    - 删除被合并的聚簇
    """
    try:
        result = await hotspot_service.merge_clusters(
            source_cluster_ids=request.source_cluster_ids,
            target_cluster_name=request.target_cluster_name,
        )
        return MergeClustersResponse(
            success=result["success"],
            cluster_id=result["cluster_id"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clusters/{cluster_id}/split", response_model=SplitClusterResponse)
async def split_cluster(cluster_id: int, request: SplitClusterRequest):
    """
    拆分聚簇

    功能：
    - 从指定聚簇中移出部分热点
    - 为移出的热点创建新聚簇（如果有多个）或清除cluster_id（如果只有一个）
    - 更新原聚簇的成员数量
    """
    try:
        result = await hotspot_service.split_cluster(
            cluster_id=cluster_id,
            hotspot_ids=request.hotspot_ids,
            new_cluster_name=request.new_cluster_name,
        )
        return SplitClusterResponse(
            success=result["success"],
            new_cluster_id=result.get("new_cluster_id"),
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/clusters/{cluster_id}", response_model=UpdateClusterResponse)
async def update_cluster(cluster_id: int, request: UpdateClusterRequest):
    """
    更新聚簇信息

    功能：
    - 更新聚簇名称
    """
    try:
        result = await hotspot_service.update_cluster(
            cluster_id=cluster_id, cluster_name=request.cluster_name
        )
        return UpdateClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clusters/{cluster_id}", response_model=DeleteClusterResponse)
async def delete_cluster(cluster_id: int):
    """
    删除聚簇

    功能：
    - 删除指定聚簇
    - 将所有相关热点的cluster_id设为NULL
    """
    try:
        result = await hotspot_service.delete_cluster(cluster_id)
        return DeleteClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/clusters/{cluster_id}/remove-hotspot",
    response_model=RemoveHotspotFromClusterResponse,
)
async def remove_hotspot_from_cluster(
    cluster_id: int, request: RemoveHotspotFromClusterRequest
):
    """
    从聚簇中移除单个热点

    功能：
    - 将热点的cluster_id设为NULL
    - 更新聚簇的成员数量和关键词列表
    """
    try:
        result = await hotspot_service.remove_hotspot_from_cluster(
            cluster_id=cluster_id, hotspot_id=request.hotspot_id
        )
        return RemoveHotspotFromClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
