from app.db.session import get_db

# 导出依赖注入函数，供 API 路由使用
__all__ = ["get_db"]
