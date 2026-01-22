"""
心跳管理器
负责定期向中控服务器上报 Agent 状态
"""
import asyncio
import logging
import time
from typing import Optional
from .utils import get_public_ip, get_location_info, get_hostname

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """心跳管理器"""

    def __init__(self, config: dict, agent_id: str, websocket_client, proxy_manager):
        """
        初始化心跳管理器

        Args:
            config: 配置字典
            agent_id: Agent ID
            websocket_client: WebSocket 客户端实例
            proxy_manager: 代理管理器实例
        """
        self.config = config
        self.agent_id = agent_id
        self.websocket_client = websocket_client
        self.proxy_manager = proxy_manager

        self.interval = config["heartbeat"]["interval"]
        self.timeout = config["heartbeat"]["timeout"]

        # 缓存的信息
        self.public_ip: Optional[str] = None
        self.location_info: Optional[dict] = None
        self.last_ip_update = 0
        self.ip_update_interval = 300  # 5分钟更新一次 IP 信息

        # 心跳任务
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def _update_ip_info(self):
        """更新 IP 和位置信息"""
        current_time = time.time()

        # 如果距离上次更新时间不到指定间隔，则跳过
        if self.public_ip and (current_time - self.last_ip_update) < self.ip_update_interval:
            return

        try:
            logger.debug("Updating public IP information")

            # 获取公网 IP
            new_ip = await asyncio.to_thread(get_public_ip)

            if new_ip and new_ip != self.public_ip:
                logger.info(f"Public IP updated: {self.public_ip} -> {new_ip}")
                self.public_ip = new_ip

                # 获取位置信息
                self.location_info = await asyncio.to_thread(get_location_info, new_ip)
                if self.location_info:
                    logger.info(f"Location: {self.location_info.get('city')}, {self.location_info.get('isp')}")

            self.last_ip_update = current_time

        except Exception as e:
            logger.error(f"Failed to update IP info: {e}")

    def _build_heartbeat_message(self) -> dict:
        """
        构建心跳消息

        Returns:
            dict: 心跳消息
        """
        # 获取代理状态
        proxy_status = self.proxy_manager.get_status()

        # 获取 Agent 名称
        agent_name = self.config["agent"].get("name") or get_hostname()

        # 构建消息
        message = {
            "action": "heartbeat",
            "agent_id": self.agent_id,
            "hostname": agent_name,
            "public_ip": self.public_ip,
            "proxy": {
                "type": self.proxy_manager.proxy_type,
                "port": self.proxy_manager.proxy_port,
                "running": proxy_status["running"],
            },
            "status": "online" if proxy_status["running"] else "offline",
        }

        # 添加位置信息
        if self.location_info:
            message["city"] = self.location_info.get("city")
            message["isp"] = self.location_info.get("isp")

        # 如果是 both 模式，添加 SOCKS5 端口
        if self.proxy_manager.proxy_type == "both":
            message["proxy"]["socks5_port"] = self.proxy_manager.proxy_port + 1

        return message

    async def send_heartbeat(self) -> bool:
        """
        发送心跳

        Returns:
            bool: 是否发送成功
        """
        try:
            # 更新 IP 信息
            await self._update_ip_info()

            # 构建心跳消息
            message = self._build_heartbeat_message()

            # 发送消息
            success = await self.websocket_client.send_message(message)

            if success:
                logger.debug("Heartbeat sent successfully")
            else:
                logger.warning("Failed to send heartbeat")

            return success

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False

    async def run(self):
        """
        运行心跳循环
        """
        self.running = True
        logger.info(f"Heartbeat manager started (interval: {self.interval}s)")

        # 初始化时立即发送一次心跳
        await self.send_heartbeat()

        while self.running:
            try:
                # 等待指定的间隔时间
                await asyncio.sleep(self.interval)

                # 发送心跳
                await self.send_heartbeat()

            except asyncio.CancelledError:
                logger.info("Heartbeat manager cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                # 出错后继续运行，但稍作延迟
                await asyncio.sleep(5)

        self.running = False
        logger.info("Heartbeat manager stopped")

    def start(self):
        """启动心跳管理器"""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run())
            logger.info("Heartbeat manager task created")

    async def stop(self):
        """停止心跳管理器"""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat manager stopped")
