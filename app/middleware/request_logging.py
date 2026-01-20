"""请求日志中间件"""

import json
from fastapi import Request
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def log_request_body_middleware(request: Request, call_next):
    """记录请求体的中间件，特别是在出现验证错误时"""
    body_data = None

    # 只记录 POST/PUT/PATCH 请求
    if request.method in ["POST", "PUT", "PATCH"]:
        # 读取请求体
        body_bytes = await request.body()

        # 尝试解析 JSON
        try:
            if body_bytes:
                body_data = json.loads(body_bytes.decode("utf-8"))
                request.state.body_json = body_data
            else:
                request.state.body_json = None
        except Exception:
            request.state.body_json = None

        # 记录请求信息
        logger.info(
            f"Request - {request.method} {request.url.path} - "
            f"Body: {json.dumps(body_data, ensure_ascii=False) if body_data else 'None'}"
        )

    # 调用下一个中间件或路由处理器
    response = await call_next(request)

    # 如果响应状态码是 422，额外记录错误
    if response.status_code == 422:
        body_data = getattr(request.state, "body_json", None)
        logger.error(
            f"422 Unprocessable Entity - {request.method} {request.url.path} - "
            f"Body: {json.dumps(body_data, ensure_ascii=False) if body_data else 'None'}"
        )

    return response
