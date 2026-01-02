from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import asyncio
from datetime import datetime
from app.config import settings
from app.db.session import init_db, close_db
from app.db.vector_session import init_vector_db, close_vector_db
from app.api.v1 import health, tasks, accounts, contents, system, proxy, vectors, hotspots, clusters

# 全局任务控制
timeout_check_task = None
stop_timeout_check = False


async def check_timeout_tasks_background():
    """后台定期检查超时任务"""
    from app.db import session
    from app.db.task_repo import TaskRepository
    from app.celery_app.celery import celery_app

    global stop_timeout_check
    check_interval = 300  # 5分钟检查一次

    print(f"[Timeout Checker] Started background task (interval: {check_interval}s)")

    while not stop_timeout_check:
        try:
            await asyncio.sleep(check_interval)

            if stop_timeout_check:
                break

            # 检查数据库连接池是否可用
            if session.db_pool is None:
                print("[Timeout Checker] Database pool not initialized, skip check")
                continue

            print("[Timeout Checker] Checking for timeout tasks...")

            async with session.db_pool.acquire() as conn:
                repo = TaskRepository(conn)

                # 获取所有超时的任务
                timeout_tasks = await repo.get_timeout_tasks(settings.TASK_TIMEOUT_SECONDS)

                if not timeout_tasks:
                    print("[Timeout Checker] No timeout tasks found")
                    continue

                timeout_count = 0
                timeout_task_ids = []

                # 处理每个超时任务
                for task in timeout_tasks:
                    try:
                        # 计算任务已运行时间
                        elapsed_seconds = (datetime.now() - task.updated_at).total_seconds()

                        print(
                            f"[Timeout Checker] Task {task.task_id} timeout detected: "
                            f"status={task.status}, elapsed={elapsed_seconds}s, "
                            f"platform={task.platform}, type={task.crawler_type}"
                        )

                        # 更新任务状态为 FAILURE
                        await repo.update_task_status(
                            task.task_id,
                            status="FAILURE",
                            error=f"Task timeout after {elapsed_seconds:.0f} seconds (limit: {settings.TASK_TIMEOUT_SECONDS}s)",
                            finished_at=datetime.now(),
                        )

                        # 尝试终止 Celery 任务（如果还在运行）
                        try:
                            celery_app.control.revoke(
                                task.task_id, terminate=True, signal="SIGKILL"
                            )
                            print(f"[Timeout Checker] Revoked Celery task {task.task_id}")
                        except Exception as revoke_error:
                            print(
                                f"[Timeout Checker] Failed to revoke task {task.task_id}: {revoke_error}"
                            )

                        timeout_count += 1
                        timeout_task_ids.append(task.task_id)

                    except Exception as task_error:
                        print(
                            f"[Timeout Checker] Failed to process timeout task {task.task_id}: {task_error}"
                        )

                if timeout_count > 0:
                    print(
                        f"[Timeout Checker] Processed {timeout_count} timeout tasks: {', '.join(timeout_task_ids)}"
                    )

        except asyncio.CancelledError:
            print("[Timeout Checker] Task cancelled, stopping...")
            break
        except Exception as e:
            print(f"[Timeout Checker] Error during timeout check: {e}")
            # 继续运行，不因为单次错误而停止


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global timeout_check_task, stop_timeout_check

    # 启动时初始化数据库连接
    await init_db()
    await init_vector_db()

    # 启动后台超时检查任务
    stop_timeout_check = False
    timeout_check_task = asyncio.create_task(check_timeout_tasks_background())

    print("=" * 60)
    print("Trend API Server started successfully!")
    print(f"API Documentation: http://localhost:{settings.API_PORT}/docs")
    print(f"Frontend Path: http://localhost:{settings.API_PORT}/")
    print(f"Vector Management: http://localhost:{settings.API_PORT}/vectors.html")
    print(f"Timeout Checker: Running (interval: 5 minutes)")
    print("=" * 60)

    yield

    # 关闭时清理资源
    print("Shutting down Trend API Server...")

    # 停止后台超时检查任务
    stop_timeout_check = True
    if timeout_check_task:
        timeout_check_task.cancel()
        try:
            await timeout_check_task
        except asyncio.CancelledError:
            pass
        print("[Timeout Checker] Stopped")

    await close_db()
    await close_vector_db()
    print("Trend API Server shut down")


# 创建 FastAPI 应用
app = FastAPI(
    title="Trend API Server",
    description="MediaCrawlerPro API Server - 多平台社交媒体数据采集API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(contents.router, prefix="/api/v1/contents", tags=["Contents"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(proxy.router, prefix="/api/v1/proxy", tags=["Proxy"])
app.include_router(vectors.router, prefix="/api/v1/vectors", tags=["Vectors"])
app.include_router(hotspots.router, prefix="/api/v1/hotspots", tags=["Hotspots"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["Clusters"])


# 静态文件目录配置
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "web")

# 挂载静态资源（如果目录存在）
if os.path.exists(os.path.join(STATIC_DIR, "assets")):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
        name="assets",
    )


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
        "health": "/api/v1/health",
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Catch-all 路由：处理前端路由

    所有非 API 路径返回前端应用的 index.html，支持前端路由
    """
    # API 路径不处理（返回 404）
    if (
        full_path.startswith("api/")
        or full_path.startswith("docs")
        or full_path.startswith("redoc")
    ):
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
        "app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=False
    )
