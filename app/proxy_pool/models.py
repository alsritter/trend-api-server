"""
代理池数据模型
Pydantic 模型，用于数据验证和序列化
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProxyType(str, Enum):
    """代理类型"""
    HTTP = "http"
    SOCKS5 = "socks5"
    BOTH = "both"


class AgentStatus(str, Enum):
    """Agent 状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    DISABLED = "disabled"


class ProxyAgentBase(BaseModel):
    """Agent 基础模型"""
    agent_id: str = Field(..., description="Agent 唯一标识")
    agent_name: str = Field(..., description="Agent 名称/主机名")
    public_ip: Optional[str] = Field(None, description="公网 IP 地址")
    city: Optional[str] = Field(None, description="城市")
    isp: Optional[str] = Field(None, description="运营商")
    proxy_type: ProxyType = Field(ProxyType.SOCKS5, description="代理类型")
    proxy_port: int = Field(1080, description="代理端口")
    proxy_username: Optional[str] = Field(None, description="代理用户名")
    proxy_password: Optional[str] = Field(None, description="代理密码")


class ProxyAgentCreate(ProxyAgentBase):
    """创建 Agent 请求"""
    auth_token: str = Field(..., description="认证 Token")


class ProxyAgentUpdate(BaseModel):
    """更新 Agent 请求"""
    agent_name: Optional[str] = None
    proxy_type: Optional[ProxyType] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    status: Optional[AgentStatus] = None


class ProxyAgent(ProxyAgentBase):
    """Agent 完整模型"""
    id: int
    auth_token: str
    status: AgentStatus
    latency: Optional[int] = None
    last_heartbeat: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProxyAgentSimple(BaseModel):
    """Agent 简化模型（用于列表）"""
    id: int
    agent_id: str
    agent_name: str
    public_ip: Optional[str]
    city: Optional[str]
    isp: Optional[str]
    proxy_type: ProxyType
    proxy_port: int
    status: AgentStatus
    latency: Optional[int]
    last_heartbeat: Optional[datetime]

    class Config:
        from_attributes = True


class HeartbeatData(BaseModel):
    """心跳数据"""
    action: str = "heartbeat"
    agent_id: str
    hostname: str
    public_ip: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    proxy: dict
    status: str
    latency: Optional[int] = None


class AgentCommand(BaseModel):
    """Agent 指令"""
    action: str = Field(..., description="指令类型: enable_proxy, disable_proxy, restart_proxy, update_config")
    config: Optional[dict] = Field(None, description="配置数据（用于 update_config）")


class ProxyHealthLog(BaseModel):
    """代理健康日志"""
    id: Optional[int] = None
    agent_id: str
    check_time: datetime
    is_available: bool
    latency: Optional[int] = None
    error_message: Optional[str] = None
    check_type: str = "auto"

    class Config:
        from_attributes = True


class ProxyUsageLog(BaseModel):
    """代理使用记录"""
    id: Optional[int] = None
    agent_id: str
    request_id: Optional[str] = None
    platform: Optional[str] = None
    is_success: bool
    error_msg: Optional[str] = None
    used_at: datetime

    class Config:
        from_attributes = True


class ProxyInfo(BaseModel):
    """代理信息（用于业务方获取）"""
    agent_id: str
    proxy_url: str = Field(..., description="代理 URL (格式: http://user:pass@ip:port)")
    proxy_type: ProxyType
    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class ProxyPoolStats(BaseModel):
    """代理池统计信息"""
    total_agents: int
    online_agents: int
    offline_agents: int
    disabled_agents: int
    total_requests: int
    failed_requests: int
    success_rate: float


class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    total: int
    items: List[ProxyAgentSimple]


class ProxyGetResponse(BaseModel):
    """获取代理响应"""
    proxy: str = Field(..., description="代理 URL")
    agent_id: str
    proxy_type: str
