from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.services.vector_service import vector_service

router = APIRouter()


# ==================== 请求/响应模型 ====================
class AddVectorRequest(BaseModel):
    """添加向量请求"""

    text: str = Field(..., description="要向量化的文本")
    collection_id: str = Field(..., description="集合ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据（JSON格式）")


class AddVectorResponse(BaseModel):
    """添加向量响应"""

    success: bool
    vector_id: int
    message: str


class SearchVectorRequest(BaseModel):
    """向量搜索请求"""

    query_text: str = Field(..., description="查询文本")
    collection_id: Optional[str] = Field(None, description="集合ID过滤")
    top_k: int = Field(10, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="相似度阈值（0-1）"
    )


class VectorSearchResult(BaseModel):
    """向量搜索结果"""

    id: int
    collection_id: str
    content: Optional[str]
    metadata: Optional[Dict[str, Any]]
    similarity: float
    createtime: str


class SearchVectorResponse(BaseModel):
    """向量搜索响应"""

    success: bool
    results: List[VectorSearchResult]
    count: int


class DeleteVectorResponse(BaseModel):
    """删除向量响应"""

    success: bool
    message: str


class VectorInfo(BaseModel):
    """向量信息"""

    id: int
    content: Optional[str]
    metadata: Optional[Dict[str, Any]]
    createtime: str


class CollectionInfo(BaseModel):
    """集合信息"""

    collection_id: str
    count: int
    vectors: List[VectorInfo]


class ListCollectionsResponse(BaseModel):
    """集合列表响应"""

    success: bool
    collections: List[CollectionInfo]


# ==================== API 端点 ====================


@router.post("/add", response_model=AddVectorResponse)
async def add_vector(request: AddVectorRequest):
    """
    添加向量

    将文本转换为向量并存储到数据库中
    """
    try:
        vector_id = await vector_service.add_vector(
            text=request.text,
            collection_id=request.collection_id,
            metadata=request.metadata,
        )
        return AddVectorResponse(
            success=True,
            vector_id=vector_id,
            message=f"Vector added successfully with ID: {vector_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchVectorResponse)
async def search_vectors(request: SearchVectorRequest):
    """
    向量召回（相似性搜索）

    根据查询文本找到最相似的向量
    """
    try:
        results = await vector_service.search_vectors(
            query_text=request.query_text,
            collection_id=request.collection_id,
            top_k=request.top_k,
            threshold=request.threshold,
        )
        return SearchVectorResponse(
            success=True, results=results, count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{vector_id}", response_model=DeleteVectorResponse)
async def delete_vector(vector_id: int):
    """
    删除指定ID的向量
    """
    try:
        success = await vector_service.delete_vector(vector_id)
        if success:
            return DeleteVectorResponse(
                success=True, message=f"Vector {vector_id} deleted successfully"
            )
        else:
            return DeleteVectorResponse(
                success=False, message=f"Vector {vector_id} not found"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection/{collection_id}", response_model=DeleteVectorResponse)
async def delete_collection(collection_id: str):
    """
    删除指定集合的所有向量
    """
    try:
        deleted_count = await vector_service.delete_vectors_by_collection(collection_id)
        return DeleteVectorResponse(
            success=True,
            message=f"Deleted {deleted_count} vectors from collection '{collection_id}'",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{vector_id}")
async def get_vector(vector_id: int):
    """
    获取指定ID的向量信息
    """
    try:
        vector_info = await vector_service.get_vector_by_id(vector_id)
        if vector_info:
            return {"success": True, "data": vector_info}
        else:
            raise HTTPException(status_code=404, detail=f"Vector {vector_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections", response_model=ListCollectionsResponse)
async def list_collections():
    """
    列出所有集合及其向量数量
    """
    try:
        collections = await vector_service.list_collections()
        return ListCollectionsResponse(success=True, collections=collections)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
