from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountCreateRequest(BaseModel):
    """创建账号请求"""
    account_name: str = Field(..., description="账号名称", min_length=1, max_length=64)
    platform_name: str = Field(..., description="平台名称", pattern="^(xhs|dy|ks|bili|wb|tieba|zhihu)$")
    cookies: str = Field(..., description="登录 cookies")


class AccountUpdateRequest(BaseModel):
    """更新账号请求"""
    account_name: Optional[str] = Field(None, description="账号名称", min_length=1, max_length=64)
    cookies: Optional[str] = Field(None, description="登录 cookies")
    status: Optional[int] = Field(None, description="账号状态 (0:正常, -1:失效)")


class AccountResponse(BaseModel):
    """账号响应"""
    id: int
    account_name: str
    platform_name: str
    status: int
    invalid_timestamp: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """账号列表响应"""
    total: int
    page: int
    page_size: int
    items: list[AccountResponse]
