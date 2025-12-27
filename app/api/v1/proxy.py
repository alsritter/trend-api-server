from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import time
import httpx

from app.schemas.proxy import (
    ProxyConfigResponse,
    ProxyConfigUpdateRequest,
    ProxyIpListResponse,
    ProxyIpInfo,
    ProxyValidateRequest,
    ProxyValidateResponse,
    ProxyStatsResponse
)
from app.schemas.common import APIResponse
from app.utils.config_manager import ProxyConfigManager
from app.config import settings

router = APIRouter()


@router.get("/config", response_model=APIResponse[ProxyConfigResponse])
async def get_proxy_config():
    """
    获取代理配置

    返回当前的 IP 代理配置信息，包括是否启用、池大小和快代理凭证
    """
    try:
        config = ProxyConfigManager.get_config()

        return APIResponse(
            code=0,
            message="success",
            data=ProxyConfigResponse(**config)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proxy config: {str(e)}")


@router.put("/config", response_model=APIResponse[dict])
async def update_proxy_config(request: ProxyConfigUpdateRequest):
    """
    更新代理配置

    更新 IP 代理相关配置到 .env 文件。

    **注意**: 配置更新后，需要重启 Celery Worker 才能生效！

    可更新的配置项：
    - **enable_ip_proxy**: 是否启用 IP 代理
    - **ip_proxy_pool_count**: IP 池大小 (1-100)
    - **ip_proxy_provider_name**: IP 提供商名称
    - **kdl_secert_id**: 快代理 Secret ID
    - **kdl_signature**: 快代理 Signature
    - **kdl_user_name**: 快代理用户名
    - **kdl_user_pwd**: 快代理密码
    """
    try:
        # 构建更新参数（只更新非 None 的字段）
        update_params = {}
        for field, value in request.model_dump().items():
            if value is not None:
                update_params[field] = value

        if not update_params:
            raise HTTPException(status_code=400, detail="No fields to update")

        # 更新配置
        success = ProxyConfigManager.update_config(**update_params)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update config")

        return APIResponse(
            code=0,
            message="Config updated successfully. Please restart Celery Worker to apply changes.",
            data={"updated_fields": list(update_params.keys())}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update proxy config: {str(e)}")


@router.get("/ips", response_model=APIResponse[ProxyIpListResponse])
async def get_proxy_ips(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取 IP 池列表

    从 Redis 缓存中查询当前的代理 IP 列表

    支持分页查询，返回 IP 地址、端口、协议、过期时间等信息
    """
    try:
        # 从 Redis 获取 IP 池
        ip_list = await ProxyConfigManager.get_ip_pool_from_redis(
            redis_host=settings.REDIS_DB_HOST,
            redis_port=settings.REDIS_DB_PORT,
            redis_password=settings.REDIS_DB_PWD,
            redis_db=settings.REDIS_DB_NUM
        )

        # 分页处理
        total = len(ip_list)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_ips = ip_list[start_index:end_index]

        # 构建响应
        items = [ProxyIpInfo(**ip) for ip in paginated_ips]

        return APIResponse(
            code=0,
            message="success",
            data=ProxyIpListResponse(total=total, items=items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get IP list: {str(e)}")


@router.post("/validate", response_model=APIResponse[ProxyValidateResponse])
async def validate_proxy_ip(request: ProxyValidateRequest):
    """
    验证单个 IP

    测试指定 IP 代理是否可用

    通过发送 HTTP 请求到测试地址验证 IP 的有效性
    """
    try:
        # 构建代理 URL
        if request.user and request.password:
            proxy_url = f"http://{request.user}:{request.password}@{request.ip}:{request.port}"
        else:
            proxy_url = f"http://{request.ip}:{request.port}"

        # 验证 IP
        start_time = time.time()
        is_valid = False
        error_message = None

        try:
            async with httpx.AsyncClient(
                proxies={"http://": proxy_url, "https://": proxy_url},
                timeout=10.0
            ) as client:
                response = await client.get("https://echo.apifox.cn/")
                is_valid = response.status_code == 200
        except Exception as e:
            error_message = str(e)

        response_time = time.time() - start_time

        return APIResponse(
            code=0,
            message="Validation completed",
            data=ProxyValidateResponse(
                is_valid=is_valid,
                response_time=round(response_time, 2),
                error_message=error_message
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate IP: {str(e)}")


@router.delete("/ips", response_model=APIResponse[dict])
async def clear_proxy_ips():
    """
    清空 IP 池

    删除 Redis 中所有缓存的代理 IP

    **警告**: 此操作不可逆，请谨慎使用！
    """
    try:
        # 清空 Redis 中的 IP 池
        cleared_count = await ProxyConfigManager.clear_ip_pool(
            redis_host=settings.REDIS_DB_HOST,
            redis_port=settings.REDIS_DB_PORT,
            redis_password=settings.REDIS_DB_PWD,
            redis_db=settings.REDIS_DB_NUM
        )

        return APIResponse(
            code=0,
            message="IP pool cleared successfully",
            data={"cleared_count": cleared_count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear IP pool: {str(e)}")


@router.get("/stats", response_model=APIResponse[ProxyStatsResponse])
async def get_proxy_stats():
    """
    获取 IP 统计信息

    返回 IP 池的统计数据，包括总数、有效数、过期数等
    """
    try:
        # 获取配置
        config = ProxyConfigManager.get_config()

        # 从 Redis 获取 IP 池
        ip_list = await ProxyConfigManager.get_ip_pool_from_redis(
            redis_host=settings.REDIS_DB_HOST,
            redis_port=settings.REDIS_DB_PORT,
            redis_password=settings.REDIS_DB_PWD,
            redis_db=settings.REDIS_DB_NUM
        )

        # 统计信息
        total_ips = len(ip_list)
        valid_ips = sum(1 for ip in ip_list if ip.get("is_valid", False))
        expired_ips = total_ips - valid_ips

        return APIResponse(
            code=0,
            message="success",
            data=ProxyStatsResponse(
                total_ips=total_ips,
                valid_ips=valid_ips,
                expired_ips=expired_ips,
                provider_name=config.get("ip_proxy_provider_name", "unknown")
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proxy stats: {str(e)}")
