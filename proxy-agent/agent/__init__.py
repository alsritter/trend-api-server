"""
Proxy Agent Package
家宽代理池 Agent 端核心模块
"""

__version__ = "1.0.0"
__author__ = "Trend Collector"

from .proxy_manager import ProxyManager
from .websocket_client import WebSocketClient
from .heartbeat import HeartbeatManager
from .utils import get_public_ip, get_hostname, generate_agent_id

__all__ = [
    "ProxyManager",
    "WebSocketClient",
    "HeartbeatManager",
    "get_public_ip",
    "get_hostname",
    "generate_agent_id",
]
