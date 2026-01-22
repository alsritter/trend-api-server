"""
代理池服务层
处理业务逻辑和数据库操作
"""

import secrets
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import asyncpg

from .models import (
    ProxyAgentCreate,
    ProxyAgentUpdate,
    ProxyAgent,
    ProxyAgentSimple,
    HeartbeatData,
    ProxyPoolStats,
    ProxyGetResponse,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class ProxyPoolService:
    """代理池服务"""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        初始化服务

        Args:
            db_pool: 数据库连接池
        """
        self.db_pool = db_pool

    async def create_agent(self, agent_data: ProxyAgentCreate) -> ProxyAgent:
        """
        创建 Agent

        Args:
            agent_data: Agent 数据

        Returns:
            ProxyAgent: 创建的 Agent
        """
        async with self.db_pool.acquire() as conn:
            # 检查 agent_id 是否已存在
            existing = await conn.fetchrow(
                "SELECT id FROM proxy_agents WHERE agent_id = $1",
                agent_data.agent_id,
            )
            if existing:
                raise ValueError(f"Agent ID already exists: {agent_data.agent_id}")

            # 插入数据并返回完整行
            row = await conn.fetchrow(
                """
                INSERT INTO proxy_agents
                (agent_id, agent_name, auth_token, public_ip, city, isp,
                 proxy_type, proxy_port, proxy_username, proxy_password, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                agent_data.agent_id,
                agent_data.agent_name,
                agent_data.auth_token,
                agent_data.public_ip,
                agent_data.city,
                agent_data.isp,
                agent_data.proxy_type.value,
                agent_data.proxy_port,
                agent_data.proxy_username,
                agent_data.proxy_password,
                AgentStatus.OFFLINE.value,
            )

            return ProxyAgent(**dict(row))

    async def get_agent_by_id(self, agent_id: int) -> Optional[ProxyAgent]:
        """
        根据 ID 获取 Agent

        Args:
            agent_id: Agent 数据库 ID

        Returns:
            Optional[ProxyAgent]: Agent 对象
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM proxy_agents WHERE id = $1", agent_id
            )
            if row:
                return ProxyAgent(**dict(row))
            return None

    async def get_agent_by_agent_id(self, agent_id: str) -> Optional[ProxyAgent]:
        """
        根据 agent_id 获取 Agent

        Args:
            agent_id: Agent ID (UUID)

        Returns:
            Optional[ProxyAgent]: Agent 对象
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM proxy_agents WHERE agent_id = $1", agent_id
            )
            if row:
                return ProxyAgent(**dict(row))
            return None

    async def update_agent(
        self, agent_id: str, update_data: ProxyAgentUpdate
    ) -> Optional[ProxyAgent]:
        """
        更新 Agent

        Args:
            agent_id: Agent ID
            update_data: 更新数据

        Returns:
            Optional[ProxyAgent]: 更新后的 Agent
        """
        # 构建更新字段
        update_fields = []
        values = []
        param_index = 1

        if update_data.agent_name is not None:
            update_fields.append(f"agent_name = ${param_index}")
            values.append(update_data.agent_name)
            param_index += 1

        if update_data.proxy_type is not None:
            update_fields.append(f"proxy_type = ${param_index}")
            values.append(update_data.proxy_type.value)
            param_index += 1

        if update_data.proxy_port is not None:
            update_fields.append(f"proxy_port = ${param_index}")
            values.append(update_data.proxy_port)
            param_index += 1

        if update_data.proxy_username is not None:
            update_fields.append(f"proxy_username = ${param_index}")
            values.append(update_data.proxy_username)
            param_index += 1

        if update_data.proxy_password is not None:
            update_fields.append(f"proxy_password = ${param_index}")
            values.append(update_data.proxy_password)
            param_index += 1

        if update_data.status is not None:
            update_fields.append(f"status = ${param_index}")
            values.append(update_data.status.value)
            param_index += 1

        if not update_fields:
            # 没有更新字段
            return await self.get_agent_by_agent_id(agent_id)

        values.append(agent_id)

        async with self.db_pool.acquire() as conn:
            sql = f"UPDATE proxy_agents SET {', '.join(update_fields)} WHERE agent_id = ${param_index}"
            await conn.execute(sql, *values)

        return await self.get_agent_by_agent_id(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        """
        删除 Agent

        Args:
            agent_id: Agent ID

        Returns:
            bool: 是否删除成功
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM proxy_agents WHERE agent_id = $1", agent_id
            )
            # result 格式为 "DELETE N"，N 是删除的行数
            return int(result.split()[-1]) > 0

    async def list_agents(
        self, status: Optional[AgentStatus] = None, limit: int = 100, offset: int = 0
    ) -> tuple[List[ProxyAgentSimple], int]:
        """
        获取 Agent 列表

        Args:
            status: 过滤状态
            limit: 限制数量
            offset: 偏移量

        Returns:
            tuple: (Agent 列表, 总数)
        """
        async with self.db_pool.acquire() as conn:
            # 构建 WHERE 子句
            if status:
                where_clause = "WHERE status = $1"
                count_params = [status.value]
                list_params = [status.value, limit, offset]
                limit_offset_params = "$2 OFFSET $3"
            else:
                where_clause = ""
                count_params = []
                list_params = [limit, offset]
                limit_offset_params = "$1 OFFSET $2"

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM proxy_agents {where_clause}"
            total = await conn.fetchval(count_sql, *count_params)

            # 查询列表
            list_sql = f"""
                SELECT id, agent_id, agent_name, public_ip, city, isp,
                       proxy_type, proxy_port, status, latency, last_heartbeat
                FROM proxy_agents
                {where_clause}
                ORDER BY last_heartbeat DESC NULLS LAST, id DESC
                LIMIT {limit_offset_params}
            """
            rows = await conn.fetch(list_sql, *list_params)

            agents = [ProxyAgentSimple(**dict(row)) for row in rows]
            return agents, total

    async def update_heartbeat(self, heartbeat: HeartbeatData) -> bool:
        """
        更新心跳信息

        Args:
            heartbeat: 心跳数据

        Returns:
            bool: 是否更新成功
        """
        async with self.db_pool.acquire() as conn:
            # 更新 Agent 信息
            result = await conn.execute(
                """
                UPDATE proxy_agents
                SET public_ip = $1,
                    city = $2,
                    isp = $3,
                    status = $4,
                    latency = $5,
                    last_heartbeat = $6
                WHERE agent_id = $7
                """,
                heartbeat.public_ip,
                heartbeat.city,
                heartbeat.isp,
                heartbeat.status,
                heartbeat.latency,
                datetime.now(),
                heartbeat.agent_id,
            )

            return int(result.split()[-1]) > 0

    async def get_available_agents(self) -> List[ProxyAgent]:
        """
        获取所有可用的 Agent

        Returns:
            List[ProxyAgent]: 可用的 Agent 列表
        """
        async with self.db_pool.acquire() as conn:
            # 查询在线且最近有心跳的 Agent（5分钟内）
            rows = await conn.fetch(
                """
                SELECT * FROM proxy_agents
                WHERE status = 'online'
                  AND last_heartbeat >= $1
                ORDER BY failed_requests ASC, total_requests ASC
                """,
                datetime.now() - timedelta(minutes=5),
            )
            return [ProxyAgent(**dict(row)) for row in rows]

    async def get_proxy(self) -> Optional[ProxyGetResponse]:
        """
        获取一个可用的代理

        使用负载均衡策略选择代理

        Returns:
            Optional[ProxyGetResponse]: 代理信息
        """
        # 获取可用 Agent
        agents = await self.get_available_agents()

        if not agents:
            logger.warning("No available agents")
            return None

        # 随机选择一个 Agent（简单的负载均衡）
        agent = random.choice(agents)

        # 构建代理 URL
        if agent.proxy_username and agent.proxy_password:
            proxy_url = f"http://{agent.proxy_username}:{agent.proxy_password}@{agent.public_ip}:{agent.proxy_port}"
        else:
            proxy_url = f"http://{agent.public_ip}:{agent.proxy_port}"

        # 更新使用统计
        await self._increment_request_count(agent.agent_id)

        return ProxyGetResponse(
            proxy=proxy_url,
            agent_id=agent.agent_id,
            proxy_type=agent.proxy_type.value,
        )

    async def mark_proxy_failed(self, agent_id: str, error_msg: Optional[str] = None):
        """
        标记代理使用失败

        Args:
            agent_id: Agent ID
            error_msg: 错误信息
        """
        async with self.db_pool.acquire() as conn:
            # 增加失败计数
            await conn.execute(
                """
                UPDATE proxy_agents
                SET failed_requests = failed_requests + 1
                WHERE agent_id = $1
                """,
                agent_id,
            )

            # 记录使用日志
            await conn.execute(
                """
                INSERT INTO proxy_usage_log (agent_id, is_success, error_msg)
                VALUES ($1, $2, $3)
                """,
                agent_id,
                False,
                error_msg,
            )

    async def _increment_request_count(self, agent_id: str):
        """增加请求计数"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE proxy_agents
                SET total_requests = total_requests + 1
                WHERE agent_id = $1
                """,
                agent_id,
            )

    async def get_stats(self) -> ProxyPoolStats:
        """
        获取代理池统计信息

        Returns:
            ProxyPoolStats: 统计信息
        """
        async with self.db_pool.acquire() as conn:
            # 查询各状态的 Agent 数量
            result = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online,
                    SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline,
                    SUM(CASE WHEN status = 'disabled' THEN 1 ELSE 0 END) as disabled,
                    SUM(total_requests) as total_requests,
                    SUM(failed_requests) as failed_requests
                FROM proxy_agents
                """
            )

            total_requests = result["total_requests"] or 0
            failed_requests = result["failed_requests"] or 0
            success_rate = (
                (total_requests - failed_requests) / total_requests * 100
                if total_requests > 0
                else 0
            )

            return ProxyPoolStats(
                total_agents=result["total"] or 0,
                online_agents=result["online"] or 0,
                offline_agents=result["offline"] or 0,
                disabled_agents=result["disabled"] or 0,
                total_requests=total_requests,
                failed_requests=failed_requests,
                success_rate=round(success_rate, 2),
            )

    async def generate_auth_token(self) -> str:
        """
        生成认证 Token

        Returns:
            str: Token
        """
        return secrets.token_urlsafe(32)

    async def verify_token(self, agent_id: str, token: str) -> bool:
        """
        验证 Token

        Args:
            agent_id: Agent ID
            token: Token

        Returns:
            bool: 是否有效
        """
        agent = await self.get_agent_by_agent_id(agent_id)
        if not agent:
            return False
        return agent.auth_token == token

    async def log_health_check(
        self,
        agent_id: str,
        is_available: bool,
        latency: Optional[int] = None,
        error_message: Optional[str] = None,
        check_type: str = "auto",
    ):
        """
        记录健康检查日志

        Args:
            agent_id: Agent ID
            is_available: 是否可用
            latency: 延迟
            error_message: 错误信息
            check_type: 检查类型
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO proxy_health_log
                (agent_id, is_available, latency, error_message, check_type)
                VALUES ($1, $2, $3, $4, $5)
                """,
                agent_id,
                is_available,
                latency,
                error_message,
                check_type,
            )
