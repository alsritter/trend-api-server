from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
import traceback
import aiomysql
from app.services.hotspot_service import hotspot_service
from app.db.session import get_db
from app.db.task_repo import TaskRepository
from app.schemas.hotspot import (
    # 请求/响应模型
    AddHotspotKeywordRequest,
    AddHotspotKeywordResponse,
    CheckHotspotRequest,
    CheckHotspotResponse,
    AddBusinessReportRequest,
    AddBusinessReportResponse,
    AddToPushQueueRequest,
    AddToPushQueueResponse,
    GetPendingPushResponse,
    ListHotspotsResponse,
    DeleteHotspotResponse,
    GetClusterHotspotsResponse,
    LinkHotspotRequest,
    LinkHotspotResponse,
    ListValidatedHotspotsResponse,
    UpdateHotspotStatusRequest,
    UpdateHotspotStatusResponse,
    MarkOutdatedHotspotsResponse,
    TriggerCrawlRequest,
    TriggerCrawlResponse,
    ListCrawledHotspotsResponse,
    GetHotspotContentsResponse,
    PlatformContents,
    HotspotStatus,
    HotspotDetail,
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 平台内容表映射（从 contents.py 复用）
PLATFORM_CONTENT_TABLES = {
    "xhs": "xhs_note",
    "dy": "douyin_aweme",
    "ks": "kuaishou_video",
    "bili": "bilibili_video",
    "wb": "weibo_note",
    "tieba": "tieba_note",
    "zhihu": "zhihu_content",
}

# 平台评论表映射
PLATFORM_COMMENT_TABLES = {
    "xhs": "xhs_note_comment",
    "dy": "douyin_aweme_comment",
    "ks": "kuaishou_video_comment",
    "bili": "bilibili_video_comment",
    "wb": "weibo_note_comment",
    "tieba": "tieba_comment",
    "zhihu": "zhihu_comment",
}

# 平台内容ID字段映射
PLATFORM_CONTENT_ID_FIELDS = {
    "dy": "aweme_id",
    "bili": "video_id",
    "ks": "video_id",
    "zhihu": "content_id",
    "xhs": "note_id",
    "wb": "note_id",
    "tieba": "note_id",
}


# ==================== 核心业务接口 ====================


@router.post("/add-keyword", response_model=AddHotspotKeywordResponse)
async def add_keyword_from_analysis(request: AddHotspotKeywordRequest):
    """
    新增词的接口 - 根据AI分析结果添加热词

    用于第一阶段AI判断后：
    - 如果是低价值词（isRemove=true），添加到热点表，状态设为 rejected
    - 如果是有价值词（isRemove=false），添加到热点表，状态设为 pending_validation
    """
    try:
        result = await hotspot_service.add_keyword_from_analysis(
            request.analysis, request.platform_data
        )
        return AddHotspotKeywordResponse(
            success=True,
            hotspot_id=result["hotspot_id"],
            message=result["message"],
            action=result["action"],
        )
    except Exception as e:
        logger.error(
            f"添加关键词时发生错误 - analysis: {request.analysis}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-exists", response_model=CheckHotspotResponse)
async def check_hotspot_exists(request: CheckHotspotRequest):
    """
    检查热词是否已存在

    多维度判断：
    1. 完全匹配 -> 返回 exists=True, action=skip
    2. 高相似度（>=90%）-> 返回 exists=True, action=update，并更新时间
    3. 中等相似度（75-90%）-> 返回 exists=False, action=ask_llm，返回相似词列表
    4. 无相似 -> 返回 exists=False, action=create
    """
    try:
        result = await hotspot_service.check_hotspot_exists(request.keyword)
        return CheckHotspotResponse(
            exists=result["exists"],
            action=result["action"],
            hotspot_id=result["hotspot_id"],
            similar_hotspots=result["similar_hotspots"],
            message=result["message"],
        )
    except Exception as e:
        logger.error(
            f"检查热词存在性时发生错误 - keyword: {request.keyword}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-report", response_model=AddBusinessReportResponse)
async def add_business_report(request: AddBusinessReportRequest):
    """
    添加商业报告

    用于第三阶段：
    - 接收AI生成的商业分析报告
    - 自动更新热点状态为 analyzed
    """
    try:
        result = await hotspot_service.add_business_report(
            hotspot_id=request.hotspot_id,
            report=request.report,
            score=request.score,
            priority=request.priority,
            product_types=request.product_types,
        )
        return AddBusinessReportResponse(
            success=result["success"],
            report_id=result["report_id"],
            message=result["message"],
        )
    except Exception as e:
        logger.error(
            f"添加商业报告时发生错误 - hotspot_id: {request.hotspot_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push-queue", response_model=AddToPushQueueResponse)
async def add_to_push_queue(request: AddToPushQueueRequest):
    """
    添加到推送队列

    用于第三阶段：
    - 将商业报告加入推送队列
    - 自动设置优先级和分数
    """
    try:
        result = await hotspot_service.add_to_push_queue(
            hotspot_id=request.hotspot_id,
            report_id=request.report_id,
            channels=request.channels,
        )
        return AddToPushQueueResponse(
            success=result["success"],
            push_id=result["push_id"],
            message=result["message"],
        )
    except ValueError as e:
        logger.error(
            f"添加到推送队列失败(未找到) - hotspot_id: {request.hotspot_id}, "
            f"report_id: {request.report_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"添加到推送队列时发生错误 - hotspot_id: {request.hotspot_id}, "
            f"report_id: {request.report_id}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/push-queue/pending", response_model=GetPendingPushResponse)
async def get_pending_push_items(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
):
    """
    获取待推送的报告

    返回按优先级和分数排序的待推送项
    自动检查推送间隔（>=2小时）
    """
    try:
        items = await hotspot_service.get_pending_push_items(limit)
        return GetPendingPushResponse(success=True, items=items, count=len(items))
    except Exception as e:
        logger.error(
            f"获取待推送项时发生错误 - limit: {limit}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 前端管理接口 ====================


@router.get("/list", response_model=ListHotspotsResponse)
async def list_hotspots(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=1000, description="每页数量"),
    status: Optional[HotspotStatus] = Query(None, description="状态过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    similarity_search: Optional[str] = Query(None, description="相似度搜索关键词"),
    similarity_threshold: float = Query(
        default=0.7, ge=0.0, le=1.0, description="相似度阈值"
    ),
):
    """
    列出热点（分页、过滤、搜索）

    支持：
    - 分页
    - 按状态过滤
    - 关键词模糊搜索 (keyword)
    - 向量相似度搜索 (similarity_search)
    """
    try:
        result = await hotspot_service.list_hotspots(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword,
            similarity_search=similarity_search,
            similarity_threshold=similarity_threshold,
        )
        return ListHotspotsResponse(
            success=True,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            items=result["items"],
        )
    except Exception as e:
        logger.error(
            f"列出热点时发生错误 - page: {page}, page_size: {page_size}, "
            f"status: {status}, keyword: {keyword}, similarity_search: {similarity_search}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/{cluster_id}/hotspots", response_model=GetClusterHotspotsResponse)
async def get_cluster_hotspots(cluster_id: int):
    """
    获取同簇的所有热点

    返回同一个簇中的所有相关热点
    """
    try:
        items = await hotspot_service.get_cluster_hotspots(cluster_id)
        return GetClusterHotspotsResponse(
            success=True, cluster_id=cluster_id, items=items, count=len(items)
        )
    except Exception as e:
        logger.error(
            f"获取聚簇热点时发生错误 - cluster_id: {cluster_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{hotspot_id}", response_model=HotspotDetail)
async def get_hotspot(hotspot_id: int):
    """
    获取热点详情

    返回热点的完整信息
    """
    try:
        hotspot = await hotspot_service.get_hotspot_by_id(hotspot_id)
        if not hotspot:
            raise HTTPException(status_code=404, detail=f"热点 {hotspot_id} 不存在")
        return hotspot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"获取热点详情时发生错误 - hotspot_id: {hotspot_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{hotspot_id}", response_model=DeleteHotspotResponse)
async def delete_hotspot(hotspot_id: int):
    """
    删除热点

    级联删除相关的商业报告和推送队列项
    """
    try:
        result = await hotspot_service.delete_hotspot(hotspot_id)
        return DeleteHotspotResponse(
            success=result["success"], message=result["message"]
        )
    except ValueError as e:
        logger.error(
            f"删除热点失败(未找到) - hotspot_id: {hotspot_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"删除热点时发生错误 - hotspot_id: {hotspot_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link", response_model=LinkHotspotResponse)
async def link_hotspot(request: LinkHotspotRequest):
    """
    关联热点 - 复用已有热点的分析信息创建新热点

    功能：
    - 复用指定热点的分析信息（状态、过滤信息、平台信息等）
    - 为新关键词生成新的向量
    - 创建新的热点记录
    - 自动将新热点添加到同一个聚簇中（如果源热点没有簇则创建新簇）
    """
    try:
        result = await hotspot_service.link_hotspot(
            keyword=request.keyword, source_hotspot_id=request.hotspot_id
        )
        return LinkHotspotResponse(
            success=result["success"],
            hotspot_id=result["hotspot_id"],
            cluster_id=result["cluster_id"],
            message=result["message"],
        )
    except ValueError as e:
        logger.error(
            f"关联热点失败(未找到) - keyword: {request.keyword}, "
            f"source_hotspot_id: {request.hotspot_id}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"关联热点时发生错误 - keyword: {request.keyword}, "
            f"source_hotspot_id: {request.hotspot_id}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validated/list", response_model=ListValidatedHotspotsResponse)
async def list_validated_hotspots(
    hours: int = Query(
        default=24,
        ge=1,
        le=168,
        description="时间范围（小时），默认 24 小时，最大 7 天",
    ),
):
    """
    获取所有 validated 状态的热词列表

    功能：
    - 每个 cluster 只返回一个热词（根据 selected_hotspot_id）
    - 如果 cluster 没有 selected_hotspot_id，自动选择第一个并设置
    - 没有 cluster 的热词直接返回
    - 保证每次返回的都是同一个热词（通过 selected_hotspot_id 字段标识）
    - 支持时间范围过滤，默认返回最近 24 小时的数据

    参数：
    - hours: 时间范围（小时），默认 24 小时，最大 168 小时（7 天）
    """
    try:
        result = await hotspot_service.list_validated_hotspots(hours=hours)
        return ListValidatedHotspotsResponse(
            success=True,
            total=result["total"],
            items=result["items"],
        )
    except Exception as e:
        logger.error(
            f"获取待验证热词列表时发生错误 - hours: {hours}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{hotspot_id}/status", response_model=UpdateHotspotStatusResponse)
async def update_hotspot_status(hotspot_id: int, request: UpdateHotspotStatusRequest):
    """
    更新热词状态

    功能：
    - 手动更新热词的状态
    - 支持所有状态的更新：pending_validation, validated, rejected, crawling, crawled, analyzing, analyzed, archived

    参数：
    - hotspot_id: 热词ID
    - status: 新的状态

    常用场景：
    - 将 validated 改为 crawling（开始爬取）
    - 将 crawled 改为 analyzing（开始分析）
    - 将热词标记为 archived（归档）
    - 将错误状态的热词改回正确状态
    """
    try:
        result = await hotspot_service.update_hotspot_status(
            hotspot_id=hotspot_id, new_status=request.status
        )
        return UpdateHotspotStatusResponse(
            success=result["success"],
            message=result["message"],
            old_status=result["old_status"],
            new_status=result["new_status"],
        )
    except ValueError as e:
        logger.error(
            f"更新热词状态失败(未找到) - hotspot_id: {hotspot_id}, "
            f"new_status: {request.status}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"更新热词状态时发生错误 - hotspot_id: {hotspot_id}, "
            f"new_status: {request.status}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-outdated", response_model=MarkOutdatedHotspotsResponse)
async def mark_outdated_hotspots(
    days: int = Query(
        default=2,
        ge=1,
        le=30,
        description="天数阈值，默认 2 天，最大 30 天",
    ),
):
    """
    标记过时的热词（超过指定天数未更新的热词）

    功能：
    - 自动识别超过指定天数未更新（last_seen_at）的热词
    - 将这些热词的状态更新为 outdated
    - 不会标记已经是 rejected、archived、outdated 状态的热词
    - 返回被标记的热词ID列表

    参数：
    - days: 天数阈值，默认 2 天，最大 30 天

    使用场景：
    - 定时任务：每天运行一次，清理过时热词
    - 手动清理：管理员手动触发清理
    - 数据维护：保持热词库的时效性
    """
    try:
        result = await hotspot_service.mark_outdated_hotspots(days=days)
        return MarkOutdatedHotspotsResponse(
            success=result["success"],
            message=result["message"],
            marked_count=result["marked_count"],
            hotspot_ids=result["hotspot_ids"],
        )
    except Exception as e:
        logger.error(
            f"标记过时热词时发生错误 - days: {days}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-crawl", response_model=TriggerCrawlResponse)
async def trigger_crawl(request: TriggerCrawlRequest, conn=Depends(get_db)):
    """
    为指定热点触发爬虫任务

    功能：
    - 为热点在指定的平台上创建爬虫任务
    - 每个平台创建一个独立的爬虫任务
    - 自动将热点状态更新为 crawling
    - 任务完成后可以通过回调更新状态

    参数：
    - hotspot_id: 热点ID
    - platforms: 平台列表 (如 ['xhs', 'dy', 'bili'])
    - crawler_type: 爬虫类型 (search|detail|creator|homefeed)，默认 search
    - max_notes_count: 每个平台最大爬取数量，默认 50
    - enable_comments: 是否爬取评论，默认 True
    - enable_sub_comments: 是否爬取二级评论，默认 False
    - max_comments_count: 每条内容最大评论数量，默认 20

    使用场景：
    - 热点验证通过后，触发爬虫采集相关内容
    - 定时任务：定期为热点更新数据
    - 手动触发：管理员手动触发爬取
    """
    try:
        # 调用服务层创建爬虫任务
        result = await hotspot_service.trigger_crawl_for_hotspot(
            hotspot_id=request.hotspot_id,
            platforms=request.platforms,
            crawler_type=request.crawler_type,
            max_notes_count=request.max_notes_count,
            enable_comments=request.enable_comments,
            enable_sub_comments=request.enable_sub_comments,
            max_comments_count=request.max_comments_count,
        )

        # 保存任务到数据库
        repo = TaskRepository(conn)
        task_config = {
            "max_notes_count": request.max_notes_count,
            "enable_comments": request.enable_comments,
            "enable_sub_comments": request.enable_sub_comments,
            "max_comments_count": request.max_comments_count,
        }

        for i, task_id in enumerate(result["task_ids"]):
            platform = result["platforms"][i]
            await repo.create_task(
                task_id=task_id,
                platform=platform,
                crawler_type=request.crawler_type,
                keywords=result["keyword"],
                config=task_config,
                hotspot_id=request.hotspot_id,
            )

        return TriggerCrawlResponse(
            success=True,
            message=f"成功为热点 '{result['keyword']}' 创建 {result['total_tasks']} 个爬虫任务",
            hotspot_id=request.hotspot_id,
            task_ids=result["task_ids"],
            total_tasks=result["total_tasks"],
        )
    except ValueError as e:
        logger.error(
            f"触发爬虫失败(未找到) - hotspot_id: {request.hotspot_id}, "
            f"platforms: {request.platforms}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"触发爬虫时发生错误 - hotspot_id: {request.hotspot_id}, "
            f"platforms: {request.platforms}, error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawled/list", response_model=ListCrawledHotspotsResponse)
async def list_crawled_hotspots(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
):
    """
    获取已爬取状态的热点列表

    功能：
    - 查询所有状态为 crawled 的热点
    - 支持分页
    - 返回热点基本信息

    参数：
    - page: 页码
    - page_size: 每页数量

    返回：
    - 热点列表（ID、关键词、状态等）
    - 分页信息
    """
    try:
        result = await hotspot_service.list_crawled_hotspots(
            page=page, page_size=page_size
        )
        return ListCrawledHotspotsResponse(
            success=True,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            items=result["items"],
        )
    except Exception as e:
        logger.error(
            f"获取已爬取热点列表时发生错误 - page: {page}, page_size: {page_size}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{hotspot_id}/contents", response_model=GetHotspotContentsResponse)
async def get_hotspot_contents(
    hotspot_id: int, conn: aiomysql.Connection = Depends(get_db)
):
    """
    获取热点关联的所有内容和评论

    功能：
    - 直接查询各平台内容表中 hotspot_id 匹配的所有内容
    - 返回每个平台的完整内容列表和评论列表
    - 按平台分组展示数据

    参数：
    - hotspot_id: 热点ID

    返回：
    - 热点基本信息（ID、关键词）
    - 各平台的内容和评论列表
    - 统计信息（总内容数、总评论数）

    说明：
    - 直接通过内容表中的 hotspot_id 字段查询内容
    - 再根据内容ID查询对应的评论
    """
    try:
        # 1. 获取热点信息
        hotspot = await hotspot_service.get_hotspot_by_id(hotspot_id)
        if not hotspot:
            raise HTTPException(status_code=404, detail=f"热点 {hotspot_id} 不存在")

        keyword = hotspot.keyword

        # 2. 按平台分组获取内容和评论
        platforms_data = []
        total_contents_count = 0
        total_comments_count = 0

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            for platform, content_table in PLATFORM_CONTENT_TABLES.items():
                comment_table = PLATFORM_COMMENT_TABLES[platform]
                content_id_field = PLATFORM_CONTENT_ID_FIELDS.get(platform, "note_id")

                # 直接查询该平台下 hotspot_id 匹配的所有内容
                content_sql = f"""
                    SELECT * FROM {content_table}
                    WHERE hotspot_id = %s
                    ORDER BY add_ts DESC
                """
                await cursor.execute(content_sql, (hotspot_id,))
                contents = await cursor.fetchall()

                # 如果该平台没有内容，跳过
                if not contents:
                    continue

                # 查询这些内容的所有评论
                comments = []
                content_ids = [
                    c.get(content_id_field) for c in contents if c.get(content_id_field)
                ]

                if content_ids:
                    # 构建 IN 查询
                    placeholders = ",".join(["%s"] * len(content_ids))
                    comment_sql = f"""
                        SELECT * FROM {comment_table}
                        WHERE {content_id_field} IN ({placeholders})
                        ORDER BY add_ts DESC
                    """
                    await cursor.execute(comment_sql, content_ids)
                    comments = await cursor.fetchall()

                # 统计
                platform_contents_count = len(contents)
                platform_comments_count = len(comments)
                total_contents_count += platform_contents_count
                total_comments_count += platform_comments_count

                # 添加到结果
                platforms_data.append(
                    PlatformContents(
                        platform=platform,
                        contents=contents,
                        comments=comments,
                        total_contents=platform_contents_count,
                        total_comments=platform_comments_count,
                    )
                )

        return GetHotspotContentsResponse(
            success=True,
            hotspot_id=hotspot_id,
            hotspot_keyword=keyword,
            platforms=platforms_data,
            total_contents=total_contents_count,
            total_comments=total_comments_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"获取热点内容时发生错误 - hotspot_id: {hotspot_id}, "
            f"error: {str(e)}, traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=str(e))
