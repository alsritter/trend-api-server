from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ProxyConfigResponse(BaseModel):
    """IP 代理配置响应"""
    enable_ip_proxy: bool = Field(..., description="是否启用 IP 代理")
    ip_proxy_pool_count: int = Field(..., description="IP 池大小")
    ip_proxy_provider_name: str = Field(..., description="IP 提供商名称")
    kdl_config: Optional[Dict[str, str]] = Field(None, description="快代理配置信息")


class ProxyConfigUpdateRequest(BaseModel):
    """更新 IP 代理配置请求"""
    enable_ip_proxy: Optional[bool] = Field(None, description="是否启用 IP 代理")
    ip_proxy_pool_count: Optional[int] = Field(None, ge=1, le=100, description="IP 池大小 (1-100)")
    ip_proxy_provider_name: Optional[str] = Field(None, description="IP 提供商名称")
    kdl_secert_id: Optional[str] = Field(None, description="快代理 Secret ID")
    kdl_signature: Optional[str] = Field(None, description="快代理 Signature")
    kdl_user_name: Optional[str] = Field(None, description="快代理用户名")
    kdl_user_pwd: Optional[str] = Field(None, description="快代理密码")


class ProxyIpInfo(BaseModel):
    """IP 信息"""
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., description="端口号")
    protocol: str = Field(..., description="协议类型 (http/https)")
    user: Optional[str] = Field(None, description="认证用户名")
    password: Optional[str] = Field(None, description="认证密码")
    expired_time_ts: int = Field(..., description="过期时间戳")
    is_valid: bool = Field(..., description="是否有效")
    ttl: Optional[int] = Field(None, description="剩余生存时间(秒)")


class ProxyIpListResponse(BaseModel):
    """IP 列表响应"""
    total: int = Field(..., description="IP 总数")
    items: List[ProxyIpInfo] = Field(..., description="IP 列表")


class ProxyValidateRequest(BaseModel):
    """IP 验证请求"""
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., description="端口号")
    user: Optional[str] = Field(None, description="认证用户名")
    password: Optional[str] = Field(None, description="认证密码")


class ProxyValidateResponse(BaseModel):
    """IP 验证响应"""
    is_valid: bool = Field(..., description="是否有效")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")
    error_message: Optional[str] = Field(None, description="错误信息")


class ProxyStatsResponse(BaseModel):
    """IP 统计响应"""
    total_ips: int = Field(..., description="总 IP 数")
    valid_ips: int = Field(..., description="有效 IP 数")
    expired_ips: int = Field(..., description="已过期 IP 数")
    provider_name: str = Field(..., description="提供商名称")
