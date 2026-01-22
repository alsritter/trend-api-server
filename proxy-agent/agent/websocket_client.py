"""
WebSocket 客户端
负责与中控服务器建立 WebSocket 连接并处理通信
"""
import asyncio
import websockets
import json
import logging
from typing import Optional, Callable
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket 客户端"""

    def __init__(self, config: dict, proxy_manager):
        """
        初始化 WebSocket 客户端

        Args:
            config: 配置字典
            proxy_manager: 代理管理器实例
        """
        self.config = config
        self.proxy_manager = proxy_manager

        self.master_url = config["server"]["master_url"]
        self.auth_token = config["server"]["auth_token"]
        self.reconnect_interval = config["server"]["reconnect_interval"]
        self.max_reconnect = config["server"]["max_reconnect"]

        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_count = 0

        # 消息处理��调
        self.message_handlers = {}

    def register_handler(self, action: str, handler: Callable):
        """
        注册消息处理器

        Args:
            action: 消息动作
            handler: 处理函数
        """
        self.message_handlers[action] = handler
        logger.debug(f"Registered handler for action: {action}")

    async def connect(self) -> bool:
        """
        连接到中控服务器

        Returns:
            bool: 是否连接成功
        """
        try:
            logger.info(f"Connecting to master server: {self.master_url}")

            # 添加认证 Token 到连接头
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            self.websocket = await websockets.connect(
                self.master_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )

            self.connected = True
            self.reconnect_count = 0
            logger.info("Connected to master server successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to master server: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False
        logger.info("Disconnected from master server")

    async def send_message(self, message: dict) -> bool:
        """
        发送消息到中控服务器

        Args:
            message: 消息字典

        Returns:
            bool: 是否发送成功
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to master server")
            return False

        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message.get('action', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False

    async def receive_messages(self):
        """
        接收并处理消息

        这是一个长期运行的协程，会持续接收消息
        """
        while self.connected:
            try:
                message_str = await self.websocket.recv()
                message = json.loads(message_str)

                action = message.get("action")
                logger.debug(f"Received message: {action}")

                # 调用对应的处理器
                if action in self.message_handlers:
                    try:
                        await self.message_handlers[action](message)
                    except Exception as e:
                        logger.error(f"Error handling message {action}: {e}")
                else:
                    logger.warning(f"No handler for action: {action}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed by server")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                self.connected = False
                break

    async def run(self):
        """
        运行 WebSocket 客户端（包含自动重连）
        """
        while True:
            # 尝试连接
            if not self.connected:
                success = await self.connect()

                if success:
                    # 连接成功，开始接收消息
                    try:
                        await self.receive_messages()
                    except Exception as e:
                        logger.error(f"Error in receive loop: {e}")

                    # 连接断开
                    self.connected = False

                # 检查是否需要重连
                self.reconnect_count += 1
                if self.max_reconnect > 0 and self.reconnect_count > self.max_reconnect:
                    logger.error(f"Max reconnect attempts ({self.max_reconnect}) reached, giving up")
                    break

                # 等待一段时间后重连
                logger.info(f"Reconnecting in {self.reconnect_interval} seconds... (attempt {self.reconnect_count})")
                await asyncio.sleep(self.reconnect_interval)
            else:
                # 保持连接
                await asyncio.sleep(1)

    async def handle_enable_proxy(self, message: dict):
        """处理启用代理指令"""
        logger.info("Received enable_proxy command")
        success = self.proxy_manager.start()

        # 发送响应
        await self.send_message({
            "action": "command_response",
            "command": "enable_proxy",
            "success": success,
        })

    async def handle_disable_proxy(self, message: dict):
        """处理禁用代理指令"""
        logger.info("Received disable_proxy command")
        success = self.proxy_manager.stop()

        # 发送响应
        await self.send_message({
            "action": "command_response",
            "command": "disable_proxy",
            "success": success,
        })

    async def handle_restart_proxy(self, message: dict):
        """处理重启代理指令"""
        logger.info("Received restart_proxy command")
        success = self.proxy_manager.restart()

        # 发送响应
        await self.send_message({
            "action": "command_response",
            "command": "restart_proxy",
            "success": success,
        })

    async def handle_update_config(self, message: dict):
        """处理更新配置指令"""
        logger.info("Received update_config command")

        # 更新配置
        new_config = message.get("config", {})
        if "proxy_port" in new_config:
            self.proxy_manager.proxy_port = new_config["proxy_port"]

        # 重启代理服务以应用新配置
        success = self.proxy_manager.restart()

        # 发送响应
        await self.send_message({
            "action": "command_response",
            "command": "update_config",
            "success": success,
        })

    def register_default_handlers(self):
        """注册默认的消息处理器"""
        self.register_handler("enable_proxy", self.handle_enable_proxy)
        self.register_handler("disable_proxy", self.handle_disable_proxy)
        self.register_handler("restart_proxy", self.handle_restart_proxy)
        self.register_handler("update_config", self.handle_update_config)
