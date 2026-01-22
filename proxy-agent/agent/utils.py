"""
工具函数模块
"""

import socket
import uuid
import platform
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_hostname() -> str:
    """
    获取主机名

    Returns:
        str: 主机名
    """
    try:
        return socket.gethostname()
    except Exception as e:
        logger.error(f"Failed to get hostname: {e}")
        return f"unknown-{uuid.uuid4().hex[:8]}"


def generate_agent_id() -> str:
    """
    生成 Agent ID

    Returns:
        str: Agent ID (UUID)
    """
    return str(uuid.uuid4())


def get_public_ip() -> Optional[str]:
    """
    获取公网 IP 地址

    尝试多个 IP 查询服务，返回第一个成功的结果

    Returns:
        Optional[str]: 公网 IP 地址，获取失败返回 None
    """
    # IP 查询服务列表
    services = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ipinfo.io/ip",
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                # 处理不同的响应格式
                text = response.text.strip()
                if service.endswith("format=json"):
                    import json

                    data = json.loads(text)
                    return data.get("ip")
                return text
        except Exception as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    logger.warning("Failed to get public IP from all services")
    return None


def get_system_info() -> dict:
    """
    获取系统信息

    Returns:
        dict: 系统信息
    """
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": get_hostname(),
    }


def get_location_info(ip: str) -> Optional[dict]:
    """
    根据 IP 获取地理位置信息

    Args:
        ip: IP 地址

    Returns:
        Optional[dict]: 地理位置信息 {"city": "城市", "isp": "运营商"}
    """
    if not ip:
        return None

    try:
        # 使用 ip-api.com 免费服务
        response = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "city": data.get("city", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "region": data.get("regionName", "Unknown"),
                }
    except Exception as e:
        logger.debug(f"Failed to get location info for {ip}: {e}")

    return None


def test_proxy(
    proxy_host: str,
    proxy_port: int,
    proxy_type: str = "http",
    username: str = None,
    password: str = None,
    test_url: str = "http://www.google.com",
    timeout: int = 10,
) -> tuple[bool, Optional[float], Optional[str]]:
    """
    测试代理是否可用

    Args:
        proxy_host: 代理主机
        proxy_port: 代理端口
        proxy_type: 代理类型 (http/socks5)
        username: 代理用户名
        password: 代理密码
        test_url: 测试 URL
        timeout: 超时时间

    Returns:
        tuple: (是否可用, 响应时间(秒), 错误信息)
    """
    import time

    # 构建代理 URL
    if username and password:
        proxy_url = f"{proxy_type}://{username}:{password}@{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        start_time = time.time()
        response = requests.get(test_url, proxies=proxies, timeout=timeout)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            return True, elapsed_time, None
        else:
            return False, elapsed_time, f"HTTP {response.status_code}"
    except Exception as e:
        return False, None, str(e)
