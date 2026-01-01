"""
时区工具模块

提供统一的时区处理函数，确保所有时间操作都使用 Asia/Shanghai (UTC+8) 时区
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 定义中国时区（东8区）
CHINA_TZ = timezone(timedelta(hours=8))


def now() -> datetime:
    """
    获取当前时间（带时区信息）

    Returns:
        datetime: 带有 Asia/Shanghai 时区信息的当前时间
    """
    return datetime.now(CHINA_TZ)


def now_naive() -> datetime:
    """
    获取当前时间（不带时区信息，用于与数据库 DATETIME 类型兼容）

    注意：数据库连接已配置为 Asia/Shanghai 时区，
    所以这里返回的本地时间会被正确处理为东8区时间

    Returns:
        datetime: 不带时区信息的当前本地时间
    """
    return datetime.now()


def to_china_tz(dt: datetime) -> datetime:
    """
    将 datetime 对象转换为 Asia/Shanghai 时区

    Args:
        dt: datetime 对象（可以是带时区或不带时区的）

    Returns:
        datetime: 带有 Asia/Shanghai 时区信息的 datetime 对象
    """
    if dt.tzinfo is None:
        # 如果没有时区信息，假定为东8区本地时间
        return dt.replace(tzinfo=CHINA_TZ)
    else:
        # 如果有时区信息，转换到东8区
        return dt.astimezone(CHINA_TZ)


def utc_to_china(utc_dt: datetime) -> datetime:
    """
    将 UTC 时间转换为 Asia/Shanghai 时区时间

    Args:
        utc_dt: UTC 时间的 datetime 对象

    Returns:
        datetime: Asia/Shanghai 时区的 datetime 对象
    """
    if utc_dt.tzinfo is None:
        # 如果没有时区信息，假定为 UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(CHINA_TZ)


def timestamp_to_datetime(ts: int, is_milliseconds: bool = True) -> datetime:
    """
    将时间戳转换为带时区的 datetime 对象

    Args:
        ts: Unix 时间戳
        is_milliseconds: 是否为毫秒级时间戳（默认 True）

    Returns:
        datetime: 带有 Asia/Shanghai 时区信息的 datetime 对象
    """
    if is_milliseconds:
        ts = ts / 1000.0

    # 从 UTC 时间戳创建，然后转换为东8区
    utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return utc_dt.astimezone(CHINA_TZ)


def datetime_to_timestamp(dt: datetime, in_milliseconds: bool = True) -> int:
    """
    将 datetime 对象转换为时间戳

    Args:
        dt: datetime 对象
        in_milliseconds: 是否返回毫秒级时间戳（默认 True）

    Returns:
        int: Unix 时间戳
    """
    timestamp = dt.timestamp()
    if in_milliseconds:
        return int(timestamp * 1000)
    return int(timestamp)


def format_iso8601(dt: datetime) -> str:
    """
    将 datetime 格式化为 ISO 8601 字符串（带时区信息）

    Args:
        dt: datetime 对象

    Returns:
        str: ISO 8601 格式的时间字符串，例如 "2025-01-01T12:30:45+08:00"
    """
    # 确保有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CHINA_TZ)
    return dt.isoformat()
