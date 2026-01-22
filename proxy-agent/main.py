#!/usr/bin/env python3
"""
Proxy Agent 主程序
家宽代理池 Agent 端入口
"""

import asyncio
import sys
import signal
import logging
import yaml
from pathlib import Path
from logging.handlers import RotatingFileHandler

from agent import (
    ProxyManager,
    WebSocketClient,
    HeartbeatManager,
    generate_agent_id,
    get_hostname,
)


class ProxyAgent:
    """代理 Agent 主类"""

    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化 Agent

        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_file)

        # 设置日志
        self._setup_logging()

        # 生成或加载 Agent ID
        self.agent_id = self._get_or_create_agent_id()
        logging.info(f"Agent ID: {self.agent_id}")

        # 初始化组件
        self.proxy_manager = ProxyManager(self.config)
        self.websocket_client = WebSocketClient(self.config, self.proxy_manager)
        self.heartbeat_manager = HeartbeatManager(
            self.config, self.agent_id, self.websocket_client, self.proxy_manager
        )

        # 注册 WebSocket 消息处理器
        self.websocket_client.register_default_handlers()

        # 运行标志
        self.running = False

    def _load_config(self, config_file: str) -> dict:
        """
        加载配置文件

        Args:
            config_file: 配置文件路径

        Returns:
            dict: 配置字典
        """
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_file}")
            sys.exit(1)

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "agent.log")
        max_size = log_config.get("max_size", 10) * 1024 * 1024  # MB to bytes
        backup_count = log_config.get("backup_count", 5)

        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(log_level)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件处理器（带日志轮转）
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    def _get_or_create_agent_id(self) -> str:
        """
        获取或创建 Agent ID

        Returns:
            str: Agent ID
        """
        agent_id_file = Path(".agent_id")

        # 如果文件存在，读取 ID
        if agent_id_file.exists():
            with open(agent_id_file, "r", encoding="utf-8") as f:
                agent_id = f.read().strip()
                if agent_id:
                    return agent_id

        # 否则生成新的 ID
        agent_id = generate_agent_id()

        # 保存到文件
        with open(agent_id_file, "w", encoding="utf-8") as f:
            f.write(agent_id)

        return agent_id

    async def start(self):
        """启动 Agent"""
        logging.info("=" * 60)
        logging.info("Proxy Agent Starting...")
        logging.info(f"Agent ID: {self.agent_id}")
        logging.info(
            f"Agent Name: {self.config['agent'].get('name') or get_hostname()}"
        )
        logging.info(f"Master Server: {self.config['server']['master_url']}")
        logging.info("=" * 60)

        self.running = True

        # 启动代理服务
        logging.info("Starting proxy service...")
        if self.proxy_manager.start():
            logging.info("Proxy service started successfully")
        else:
            logging.error("Failed to start proxy service")
            return

        # 创建任务
        tasks = [
            asyncio.create_task(self.websocket_client.run(), name="websocket"),
            asyncio.create_task(self.heartbeat_manager.run(), name="heartbeat"),
        ]

        logging.info("Agent started successfully")

        # 等待任务完成（或被取消）
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logging.info("Agent tasks cancelled")

    async def stop(self):
        """停止 Agent"""
        logging.info("Stopping Proxy Agent...")

        self.running = False

        # 停止心跳管理器
        await self.heartbeat_manager.stop()

        # 断开 WebSocket 连接
        await self.websocket_client.disconnect()

        # 停止代理服务
        self.proxy_manager.stop()

        logging.info("Proxy Agent stopped")

    def run(self):
        """运行 Agent（阻塞）"""

        # 设置信号处理
        def signal_handler(sig, frame):
            logging.info(f"Received signal {sig}, shutting down...")
            # 创建一个新的事件循环来运行停止协程
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop())
            loop.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 运行主循环
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logging.info("Received KeyboardInterrupt")
        except Exception as e:
            logging.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            # 确保清理资源
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop())
            loop.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Proxy Agent - 家宽代理节点")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="配置文件路径 (default: config.yaml)",
    )
    parser.add_argument(
        "-v", "--version", action="version", version="Proxy Agent v1.0.0"
    )

    args = parser.parse_args()

    # 创建并运行 Agent
    agent = ProxyAgent(config_file=args.config)
    agent.run()


if __name__ == "__main__":
    main()
