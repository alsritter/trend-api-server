from fastapi import APIRouter
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return APIResponse(
        code=0,
        message="success",
        data={"status": "healthy"}
    )
