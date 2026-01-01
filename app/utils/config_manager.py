"""
代理配置管理工具

管理 IP 代理相关配置的读写和 Redis IP 池查询
"""
import os
import json
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv, set_key, find_dotenv
import redis.asyncio as redis


class ProxyConfigManager:
    """代理配置管理器"""

    # 环境变量文件路径
    ENV_FILE = find_dotenv() or ".env"

    # 代理配置相关的环境变量键
    ENV_KEYS = {
        "enable_ip_proxy": "ENABLE_IP_PROXY",
        "ip_proxy_pool_count": "IP_PROXY_POOL_COUNT",
        "ip_proxy_provider_name": "IP_PROXY_PROVIDER_NAME",
        "kdl_secert_id": "KDL_SECERT_ID",
        "kdl_signature": "KDL_SIGNATURE",
        "kdl_user_name": "KDL_USER_NAME",
        "kdl_user_pwd": "KDL_USER_PWD",
    }

    @classmethod
    def get_config(cls) -> Dict[str, any]:
        """
        获取当前代理配置

        Returns:
            Dict: 代理配置字典
        """
        # 重新加载环境变量
        load_dotenv(override=True)

        config = {
            "enable_ip_proxy": os.getenv("ENABLE_IP_PROXY", "False").lower() == "true",
            "ip_proxy_pool_count": int(os.getenv("IP_PROXY_POOL_COUNT", "2")),
            "ip_proxy_provider_name": os.getenv("IP_PROXY_PROVIDER_NAME", "kuaidaili"),
            "kdl_config": {
                "kdl_secert_id": os.getenv("KDL_SECERT_ID", ""),
                "kdl_signature": os.getenv("KDL_SIGNATURE", ""),
                "kdl_user_name": os.getenv("KDL_USER_NAME", ""),
                "kdl_user_pwd": os.getenv("KDL_USER_PWD", ""),
            }
        }

        # 如果快代理配置为空，则不返回
        if not any(config["kdl_config"].values()):
            config["kdl_config"] = None

        return config

    @classmethod
    def update_config(cls, **kwargs) -> bool:
        """
        更新代理配置到 .env 文件

        Args:
            **kwargs: 要更新的配置项

        Returns:
            bool: 更新是否成功
        """
        try:
            # 确保 .env 文件存在
            if not os.path.exists(cls.ENV_FILE):
                with open(cls.ENV_FILE, 'w') as f:
                    f.write("# Trend API Server Configuration\n\n")

            # 更新环境变量到文件
            for key, value in kwargs.items():
                if key in cls.ENV_KEYS:
                    env_key = cls.ENV_KEYS[key]

                    # 布尔值转换为字符串
                    if isinstance(value, bool):
                        value = "True" if value else "False"

                    # 写入 .env 文件
                    set_key(cls.ENV_FILE, env_key, str(value))

            # 重新加载环境变量
            load_dotenv(override=True)

            return True
        except Exception as e:
            print(f"更新配置失败: {str(e)}")
            return False

    @classmethod
    async def get_ip_pool_from_redis(
        cls,
        redis_host: str = "localhost",
        redis_port: int = 6378,
        redis_password: str = "123456",
        redis_db: int = 0,
        provider_pattern: str = "kuaidaili_*"
    ) -> List[Dict[str, any]]:
        """
        从 Redis 中获取 IP 池列表

        Args:
            redis_host: Redis 主机
            redis_port: Redis 端口
            redis_password: Redis 密码
            redis_db: Redis 数据库编号
            provider_pattern: IP 提供商 key 匹配模式

        Returns:
            List[Dict]: IP 信息列表
        """
        ip_list = []
        redis_client = None

        try:
            # 连接 Redis (不使用 decode_responses，因为数据是 pickle 序列化的)
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=False  # 改为 False 以支持 pickle 二进制数据
            )

            # 获取所有匹配的 key
            keys = await redis_client.keys(provider_pattern.encode())

            current_time = int(time.time())

            # 遍历每个 key 获取 IP 信息
            for key in keys:
                try:
                    # 解码 key
                    key_str = key.decode() if isinstance(key, bytes) else key

                    # 获取 key 的值
                    value = await redis_client.get(key)
                    if not value:
                        continue

                    # 尝试反序列化 pickle 数据
                    import pickle
                    try:
                        ip_data = pickle.loads(value)
                        # 如果 ip_data 是字符串，尝试解析为 JSON
                        if isinstance(ip_data, str):
                            ip_data = json.loads(ip_data)
                    except (pickle.UnpicklingError, TypeError):
                        # 如果不是 pickle，尝试作为 JSON 解析
                        ip_data = json.loads(value.decode() if isinstance(value, bytes) else value)

                    # 从数据中直接获取 IP 和端口（优先使用数据中的值）
                    ip = ip_data.get("ip", "")
                    port = ip_data.get("port", 0)

                    # 如果数据中没有，则尝试从 key 中解析
                    # key 格式: {provider}_{ip}_{port}
                    if not ip or not port:
                        parts = key_str.split("_")
                        if len(parts) >= 3:
                            ip = ip or parts[-2]
                            port = port or int(parts[-1])

                    # 从 protocol 字段中提取协议类型（去除 ://)
                    protocol = ip_data.get("protocol", "https://")
                    # 去除协议后缀 :// 只保留协议名称
                    protocol = protocol.replace("://", "").lower()

                    # 获取 TTL
                    ttl = await redis_client.ttl(key)

                    # 构建 IP 信息
                    ip_info = {
                        "ip": ip,
                        "port": int(port) if isinstance(port, str) else port,
                        "protocol": protocol,
                        "user": ip_data.get("user", ""),
                        "password": ip_data.get("password", ""),
                        "expired_time_ts": ip_data.get("expired_time_ts", 0),
                        "is_valid": ip_data.get("expired_time_ts", 0) > current_time,
                        "ttl": ttl if ttl > 0 else 0
                    }

                    ip_list.append(ip_info)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"解析 IP 数据失败 (key={key_str}): {str(e)}")
                    continue

            return ip_list

        except Exception as e:
            print(f"从 Redis 获取 IP 池失败: {str(e)}")
            return []
        finally:
            if redis_client:
                await redis_client.close()

    @classmethod
    async def clear_ip_pool(
        cls,
        redis_host: str = "localhost",
        redis_port: int = 6378,
        redis_password: str = "123456",
        redis_db: int = 0,
        provider_pattern: str = "kuaidaili_*"
    ) -> int:
        """
        清空 Redis 中的 IP 池

        Args:
            redis_host: Redis 主机
            redis_port: Redis 端口
            redis_password: Redis 密码
            redis_db: Redis 数据库编号
            provider_pattern: IP 提供商 key 匹配模式

        Returns:
            int: 删除的 IP 数量
        """
        redis_client = None

        try:
            # 连接 Redis (不使用 decode_responses)
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=False
            )

            # 获取所有匹配的 key
            keys = await redis_client.keys(provider_pattern.encode())

            if not keys:
                return 0

            # 删除所有匹配的 key
            deleted_count = await redis_client.delete(*keys)

            return deleted_count

        except Exception as e:
            print(f"清空 IP 池失败: {str(e)}")
            return 0
        finally:
            if redis_client:
                await redis_client.close()
