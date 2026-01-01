from fastapi import APIRouter, HTTPException
import logging
import traceback
from app.services.cluster_service import cluster_service
from app.schemas.hotspot import (
    ListClustersResponse,
    CreateClusterRequest,
    CreateClusterResponse,
    MergeClustersRequest,
    MergeClustersResponse,
    SplitClusterRequest,
    SplitClusterResponse,
    UpdateClusterRequest,
    UpdateClusterResponse,
    DeleteClusterResponse,
    RemoveHotspotFromClusterRequest,
    RemoveHotspotFromClusterResponse,
    ClusterInfo,
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=CreateClusterResponse)
async def create_cluster(request: CreateClusterRequest):
    """
    创建新聚簇

    功能：
    - 创建一个新的空聚簇或包含初始热点的聚簇
    - 如果提供了热点ID，将这些热点添加到新聚簇中
    """
    try:
        result = await cluster_service.create_cluster(
            cluster_name=request.cluster_name, hotspot_ids=request.hotspot_ids
        )
        return CreateClusterResponse(
            success=result["success"],
            cluster_id=result["cluster_id"],
            message=result["message"],
        )
    except ValueError as e:
        logger.error(f"创建聚簇失败(参数错误) - cluster_name: {request.cluster_name}, error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"创建聚簇时发生错误 - cluster_name: {request.cluster_name}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ListClustersResponse)
async def list_clusters():
    """
    列出所有聚簇

    返回所有聚簇的基本信息
    """
    try:
        items = await cluster_service.list_clusters()
        return ListClustersResponse(success=True, items=items, count=len(items))
    except Exception as e:
        logger.error(
            f"列出聚簇时发生错误 - error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}", response_model=ClusterInfo)
async def get_cluster(cluster_id: int):
    """
    获取聚簇详情

    返回聚簇的完整信息
    """
    try:
        cluster = await cluster_service.get_cluster_by_id(cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"聚簇 {cluster_id} 不存在")
        return cluster
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"获取聚簇详情时发生错误 - cluster_id: {cluster_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge", response_model=MergeClustersResponse)
async def merge_clusters(request: MergeClustersRequest):
    """
    合并多个聚簇

    功能：
    - 将多个聚簇合并为一个
    - 更新所有热点的cluster_id
    - 删除被合并的聚簇
    """
    try:
        result = await cluster_service.merge_clusters(
            source_cluster_ids=request.source_cluster_ids,
            target_cluster_name=request.target_cluster_name,
        )
        return MergeClustersResponse(
            success=result["success"],
            cluster_id=result["cluster_id"],
            message=result["message"],
        )
    except ValueError as e:
        logger.error(
            f"合并聚簇失败(未找到) - source_cluster_ids: {request.source_cluster_ids}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"合并聚簇时发生错误 - source_cluster_ids: {request.source_cluster_ids}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{cluster_id}/split", response_model=SplitClusterResponse)
async def split_cluster(cluster_id: int, request: SplitClusterRequest):
    """
    拆分聚簇

    功能：
    - 从指定聚簇中移出部分热点
    - 为移出的热点创建新聚簇（如果有多个）或清除cluster_id（如果只有一个）
    - 更新原聚簇的成员数量
    """
    try:
        result = await cluster_service.split_cluster(
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
        logger.error(
            f"拆分聚簇失败(未找到) - cluster_id: {cluster_id}, "
            f"hotspot_ids: {request.hotspot_ids}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"拆分聚簇时发生错误 - cluster_id: {cluster_id}, "
            f"hotspot_ids: {request.hotspot_ids}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{cluster_id}", response_model=UpdateClusterResponse)
async def update_cluster(cluster_id: int, request: UpdateClusterRequest):
    """
    更新聚簇信息

    功能：
    - 更新聚簇名称
    """
    try:
        result = await cluster_service.update_cluster(
            cluster_id=cluster_id, cluster_name=request.cluster_name
        )
        return UpdateClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        logger.error(
            f"更新聚簇失败(未找到) - cluster_id: {cluster_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"更新聚簇时发生错误 - cluster_id: {cluster_id}, "
            f"cluster_name: {request.cluster_name}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cluster_id}", response_model=DeleteClusterResponse)
async def delete_cluster(cluster_id: int):
    """
    删除聚簇

    功能：
    - 删除指定聚簇
    - 将所有相关热点的cluster_id设为NULL
    """
    try:
        result = await cluster_service.delete_cluster(cluster_id)
        return DeleteClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        logger.error(
            f"删除聚簇失败(未找到) - cluster_id: {cluster_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"删除聚簇时发生错误 - cluster_id: {cluster_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{cluster_id}/remove-hotspot",
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
        result = await cluster_service.remove_hotspot_from_cluster(
            cluster_id=cluster_id, hotspot_id=request.hotspot_id
        )
        return RemoveHotspotFromClusterResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        logger.error(
            f"从聚簇移除热点失败(未找到) - cluster_id: {cluster_id}, "
            f"hotspot_id: {request.hotspot_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"从聚簇移除热点时发生错误 - cluster_id: {cluster_id}, "
            f"hotspot_id: {request.hotspot_id}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))
