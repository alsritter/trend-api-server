from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from app.config import settings
from app.db.session import init_db, close_db
from app.api.v1 import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库连接
    await init_db()
    print("=" * 60)
    print("Trend API Server started successfully!")
    print(f"API Documentation: http://localhost:{settings.API_PORT}/docs")
    print(f"Frontend Path: http://localhost:{settings.API_PORT}/")
    print("=" * 60)
    yield
    # 关闭时清理资源
    await close_db()
    print("Trend API Server shut down")


# 创建 FastAPI 应用
app = FastAPI(
    title="Trend API Server",
    description="MediaCrawlerPro API Server - 多平台社交媒体数据采集API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api.v1 import tasks, accounts, contents, system, proxy

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(contents.router, prefix="/api/v1/contents", tags=["Contents"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(proxy.router, prefix="/api/v1/proxy", tags=["Proxy"])


# 静态文件目录配置
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "web")

# 挂载静态资源（如果目录存在）
if os.path.exists(os.path.join(STATIC_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")


@app.get("/")
async def root():
    """根路径"""
    # 如果前端存在，返回前端页面
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    # 否则返回 API 信息
    return {
        "message": "Welcome to Trend API Server",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Catch-all 路由：处理前端路由

    所有非 API 路径返回前端应用的 index.html，支持前端路由
    """
    # API 路径不处理（返回 404）
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
        return {"error": "Not found"}

    # 尝试直接返回文件
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # 返回 index.html（支持前端路由）
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    return {"error": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False
    )
