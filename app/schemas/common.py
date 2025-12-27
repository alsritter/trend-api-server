from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

DataT = TypeVar('DataT')


class APIResponse(BaseModel, Generic[DataT]):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[DataT] = None


class PaginationResponse(BaseModel, Generic[DataT]):
    """分页响应"""
    total: int
    page: int
    page_size: int
    items: list[DataT]
