"""
家宽代理池 API 路由
提供 Agent 管理、代理获取、WebSocket 通信等接口
"""

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    Header,
)
from typing import Optional, Dict
import logging
import json

from app.schemas.common import APIResponse
from app.proxy_pool.models import (
    ProxyAgentCreate,
    ProxyAgentUpdate,
    ProxyAgent,
    AgentListResponse,
    ProxyGetResponse,
    ProxyPoolStats,
    AgentCommand,
    HeartbeatData,
    AgentStatus,
)
from app.proxy_pool.service import ProxyPoolService
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket 连接管理
active_connections: Dict[str, WebSocket] = {}


def get_proxy_service(conn=Depends(get_db)) -> ProxyPoolService:
    """获取代理池服务实例"""
    from app.db.session import pg_pool

    return ProxyPoolService(pg_pool)


@router.post("/agents", response_model=APIResponse[ProxyAgent])
async def create_agent(
    agent_data: ProxyAgentCreate, service: ProxyPoolService = Depends(get_proxy_service)
):
    """
    创建新的 Agent

    注册一个新的家宽代理 Agent 节点
    """
    try:
        agent = await service.create_agent(agent_data)
        return APIResponse(code=0, message="Agent created successfully", data=agent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/agents", response_model=APIResponse[AgentListResponse])
async def list_agents(
    status: Optional[AgentStatus] = Query(None, description="过滤状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: ProxyPoolService = Depends(get_proxy_service),
):
    """
    获取 Agent 列表

    支持按状态过滤和分页
    """
    try:
        offset = (page - 1) * page_size
        agents, total = await service.list_agents(
            status=status, limit=page_size, offset=offset
        )

        return APIResponse(
            code=0, message="success", data=AgentListResponse(total=total, items=agents)
        )
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/agents/{agent_id}", response_model=APIResponse[ProxyAgent])
async def get_agent(
    agent_id: str, service: ProxyPoolService = Depends(get_proxy_service)
):
    """
    获取 Agent 详情

    根据 agent_id 获取单个 Agent 的详细信息
    """
    try:
        agent = await service.get_agent_by_agent_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return APIResponse(code=0, message="success", data=agent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.put("/agents/{agent_id}", response_model=APIResponse[ProxyAgent])
async def update_agent(
    agent_id: str,
    update_data: ProxyAgentUpdate,
    service: ProxyPoolService = Depends(get_proxy_service),
):
    """
    更新 Agent

    更新 Agent 的配置信息
    """
    try:
        agent = await service.update_agent(agent_id, update_data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return APIResponse(code=0, message="Agent updated successfully", data=agent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/agents/{agent_id}", response_model=APIResponse[dict])
async def delete_agent(
    agent_id: str, service: ProxyPoolService = Depends(get_proxy_service)
):
    """
    删除 Agent

    删除指定的 Agent 节点
    """
    try:
        success = await service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        # 如果 Agent 在线，关闭 WebSocket 连接
        if agent_id in active_connections:
            await active_connections[agent_id].close()
            del active_connections[agent_id]

        return APIResponse(
            code=0, message="Agent deleted successfully", data={"agent_id": agent_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@router.post("/agents/{agent_id}/command", response_model=APIResponse[dict])
async def send_command(
    agent_id: str,
    command: AgentCommand,
    service: ProxyPoolService = Depends(get_proxy_service),
):
    """
    向 Agent 发送指令

    支持的指令:
    - enable_proxy: 启用代理
    - disable_proxy: 禁用代理
    - restart_proxy: 重启代理
    - update_config: 更新配置
    """
    try:
        # 检查 Agent 是否存在
        agent = await service.get_agent_by_agent_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # 检查 WebSocket 连接
        if agent_id not in active_connections:
            raise HTTPException(status_code=400, detail="Agent is not connected")

        # 发送指令
        websocket = active_connections[agent_id]
        await websocket.send_json(command.model_dump())

        return APIResponse(
            code=0,
            message="Command sent successfully",
            data={"agent_id": agent_id, "action": command.action},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send command: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send command: {str(e)}")


@router.get("/proxy/get", response_model=APIResponse[ProxyGetResponse])
async def get_proxy(service: ProxyPoolService = Depends(get_proxy_service)):
    """
    获取一个可用的代理

    从代理池中随机选择一个可用的代理返回

    业务方调用此接口获取代理进行使用
    """
    try:
        proxy = await service.get_proxy()
        if not proxy:
            raise HTTPException(status_code=503, detail="No available proxy")

        return APIResponse(code=0, message="success", data=proxy)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get proxy: {str(e)}")


@router.post("/proxy/mark_failed", response_model=APIResponse[dict])
async def mark_proxy_failed(
    agent_id: str,
    error_msg: Optional[str] = None,
    service: ProxyPoolService = Depends(get_proxy_service),
):
    """
    标记代理失败

    业务方在使用代理失败后调用此接口上报失败信息
    """
    try:
        await service.mark_proxy_failed(agent_id, error_msg)

        return APIResponse(
            code=0, message="Proxy marked as failed", data={"agent_id": agent_id}
        )
    except Exception as e:
        logger.error(f"Failed to mark proxy failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to mark proxy failed: {str(e)}"
        )


@router.get("/stats", response_model=APIResponse[ProxyPoolStats])
async def get_stats(service: ProxyPoolService = Depends(get_proxy_service)):
    """
    获取代理池统计信息

    返回代理池的各项统计数据
    """
    try:
        stats = await service.get_stats()

        return APIResponse(code=0, message="success", data=stats)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.websocket("/agent/ws")
async def websocket_endpoint(
    websocket: WebSocket, authorization: Optional[str] = Header(None)
):
    """
    WebSocket 端点

    Agent 通过此接口连接到中控服务器
    """
    from app.db.session import pg_pool

    service = ProxyPoolService(pg_pool)

    # 验证 Token
    if not authorization or not authorization.startswith("Bearer "):
        await websocket.close(code=1008, reason="Missing or invalid authorization")
        return

    token = authorization.replace("Bearer ", "")

    # 接受连接
    await websocket.accept()

    agent_id = None

    try:
        # 等待第一条消息（应该是心跳或注册消息）
        data = await websocket.receive_text()
        message = json.loads(data)

        # 验证 Agent
        if message.get("action") == "heartbeat":
            agent_id = message.get("agent_id")

            # 验证 Token
            if not await service.verify_token(agent_id, token):
                await websocket.close(code=1008, reason="Invalid token")
                return

            # 保存连接
            active_connections[agent_id] = websocket
            logger.info(f"Agent {agent_id} connected")

            # 处理心跳
            heartbeat = HeartbeatData(**message)
            await service.update_heartbeat(heartbeat)

            # 发送确认消息
            await websocket.send_json(
                {"action": "connected", "message": "Connected successfully"}
            )

            # 持续接收消息
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                action = message.get("action")

                if action == "heartbeat":
                    # 更新心跳
                    heartbeat = HeartbeatData(**message)
                    await service.update_heartbeat(heartbeat)
                    logger.debug(f"Heartbeat received from {agent_id}")

                elif action == "command_response":
                    # Agent 对指令的响应
                    logger.info(f"Command response from {agent_id}: {message}")

                else:
                    logger.warning(f"Unknown action from {agent_id}: {action}")

        else:
            await websocket.close(code=1008, reason="Expected heartbeat message")

    except WebSocketDisconnect:
        logger.info(f"Agent {agent_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 清理连接
        if agent_id and agent_id in active_connections:
            del active_connections[agent_id]
            logger.info(f"Agent {agent_id} connection cleaned up")


@router.get("/token/generate", response_model=APIResponse[dict])
async def generate_token(service: ProxyPoolService = Depends(get_proxy_service)):
    """
    生成认证 Token

    用于创建新 Agent 时使用的认证 Token
    """
    try:
        token = await service.generate_auth_token()

        return APIResponse(
            code=0, message="Token generated successfully", data={"token": token}
        )
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate token: {str(e)}"
        )
