from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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
    print(f"API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")
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
from app.api.v1 import tasks, accounts, contents, system

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(contents.router, prefix="/api/v1/contents", tags=["Contents"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Trend API Server",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False
    )
