"""
代理健康检查调度器
定期检查所有代理的可用性
"""
import asyncio
import logging
import httpx
import time
from datetime import datetime, timedelta
from typing import Optional

from .service import ProxyPoolService
from .models import ProxyAgent

logger = logging.getLogger(__name__)


class ProxyHealthChecker:
    """代理健康检查器"""

    def __init__(self, service: ProxyPoolService, check_interval: int = 60):
        """
        初始化健康检查器

        Args:
            service: 代理池服务实例
            check_interval: 检查间隔（秒）
        """
        self.service = service
        self.check_interval = check_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None

        # 检查配置
        self.test_url = "https://www.baidu.com"
        self.timeout = 10

    async def check_agent(self, agent: ProxyAgent) -> tuple[bool, Optional[int], Optional[str]]:
        """
        检查单个 Agent 的可用性

        Args:
            agent: Agent 对象

        Returns:
            tuple: (是否可用, 延迟(ms), 错误信息)
        """
        # 构建代理 URL
        if agent.proxy_username and agent.proxy_password:
            proxy_url = f"http://{agent.proxy_username}:{agent.proxy_password}@{agent.public_ip}:{agent.proxy_port}"
        else:
            proxy_url = f"http://{agent.public_ip}:{agent.proxy_port}"

        try:
            start_time = time.time()

            async with httpx.AsyncClient(proxy=proxy_url, timeout=self.timeout) as client:
                response = await client.get(self.test_url)

            elapsed_time = int((time.time() - start_time) * 1000)  # 转换为毫秒

            if response.status_code == 200:
                return True, elapsed_time, None
            else:
                return False, elapsed_time, f"HTTP {response.status_code}"

        except Exception as e:
            return False, None, str(e)

    async def check_all_agents(self):
        """检查所有在线的 Agent"""
        try:
            logger.info("Starting health check for all agents")

            # 获取所有在线的 Agent
            agents, _ = await self.service.list_agents(status=None)

            if not agents:
                logger.debug("No agents to check")
                return

            logger.info(f"Checking {len(agents)} agents")

            # 并发检查所有 Agent
            tasks = []
            for agent_simple in agents:
                # 获取完整的 Agent 信息
                agent = await self.service.get_agent_by_agent_id(agent_simple.agent_id)
                if agent and agent.public_ip:
                    tasks.append(self._check_and_log(agent))

            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Health check completed")

        except Exception as e:
            logger.error(f"Error in check_all_agents: {e}")

    async def _check_and_log(self, agent: ProxyAgent):
        """检查并记录结果"""
        try:
            is_available, latency, error_msg = await self.check_agent(agent)

            # 记录检查结果
            await self.service.log_health_check(
                agent_id=agent.agent_id,
                is_available=is_available,
                latency=latency,
                error_message=error_msg,
                check_type="auto"
            )

            if is_available:
                logger.debug(f"Agent {agent.agent_id} is available (latency: {latency}ms)")
            else:
                logger.warning(f"Agent {agent.agent_id} is unavailable: {error_msg}")

        except Exception as e:
            logger.error(f"Error checking agent {agent.agent_id}: {e}")

    async def check_offline_agents(self):
        """
        检查离线的 Agent
        如果 Agent 超过一定时间没有心跳，标记为 offline
        """
        try:
            # 超时时间：5 分钟
            timeout_threshold = datetime.now() - timedelta(minutes=5)

            async with self.service.db_pool.acquire() as conn:
                # 更新超时的在线 Agent 为离线
                result = await conn.execute(
                    """
                    UPDATE proxy_agents
                    SET status = 'offline'
                    WHERE status = 'online'
                      AND (last_heartbeat IS NULL OR last_heartbeat < $1)
                    """,
                    timeout_threshold,
                )

                # result 格式为 "UPDATE N"，N 是更新的行数
                affected_rows = int(result.split()[-1]) if result else 0
                if affected_rows > 0:
                    logger.info(f"Marked {affected_rows} agents as offline due to timeout")

        except Exception as e:
            logger.error(f"Error in check_offline_agents: {e}")

    async def run(self):
        """运行健康检查循环"""
        self.running = True
        logger.info(f"Proxy health checker started (interval: {self.check_interval}s)")

        while self.running:
            try:
                # 检查所有 Agent
                await self.check_all_agents()

                # 检查离线 Agent
                await self.check_offline_agents()

                # 等待下一次检查
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                logger.info("Health checker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                # 出错后稍作延迟
                await asyncio.sleep(10)

        self.running = False
        logger.info("Proxy health checker stopped")

    def start(self):
        """启动健康检查器"""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run())
            logger.info("Health checker task created")

    async def stop(self):
        """停止健康检查器"""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Health checker stopped")
