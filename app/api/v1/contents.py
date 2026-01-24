from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import aiomysql
from app.schemas.content import ContentListResponse, CommentListResponse, StructuredContent, StructuredComment
from app.schemas.common import APIResponse
from app.dependencies import get_db
from app.db.session import get_vector_db
from app.services.content_service import content_service
from app.constants import (
    PLATFORM_CONTENT_TABLES,
    PLATFORM_COMMENT_TABLES,
    PLATFORM_CREATOR_TABLES,
    PLATFORM_NAME_MAP,
    PLATFORM_TIME_FIELDS,
    PLATFORM_CONTENT_ID_FIELDS,
)
import asyncpg

router = APIRouter()


@router.get("/{platform}/notes", response_model=APIResponse[ContentListResponse])
async def list_contents(
    platform: str,
    keyword: Optional[str] = Query(None, description="关键词搜索（标题或内容）"),
    hotspot_id: Optional[int] = Query(None, description="热词ID过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mysql_conn: aiomysql.Connection = Depends(get_db),
    pg_conn: asyncpg.Connection = Depends(get_vector_db),
):
    """
    查询平台内容列表（笔记/视频）- 返回结构化数据

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu
    支持按热词ID过滤，返回该热词关联的所有内容

    返回结构化内容模型，统一不同平台的字段
    """

    if platform not in PLATFORM_CONTENT_TABLES:
        # 有可能是中文平台名，转换成代码
        if platform in PLATFORM_NAME_MAP:
            platform = PLATFORM_NAME_MAP[platform]
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

    try:
        # 如果提供了 hotspot_id，验证热词是否存在并获取关键词
        hotspot_keyword = None
        if hotspot_id:
            hotspot_result = await pg_conn.fetchrow(
                "SELECT id, keyword FROM hotspots WHERE id = $1", hotspot_id
            )
            if not hotspot_result:
                raise HTTPException(status_code=404, detail=f"热词 {hotspot_id} 不存在")
            hotspot_keyword = hotspot_result["keyword"]

        # 使用 ContentService 获取结构化内容
        filters = {
            "hotspot_id": hotspot_id,
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
        }

        structured_contents, total = await content_service.get_contents_by_platform(
            platform, filters, page, page_size, mysql_conn
        )

        # 批量查询热词信息（为没有 hotspot_keyword 的内容补充）
        hotspot_ids = set()
        for content in structured_contents:
            if content.hotspot_id and not content.hotspot_keyword:
                hotspot_ids.add(content.hotspot_id)

        hotspot_map = {}
        if hotspot_ids:
            hotspots = await pg_conn.fetch(
                "SELECT id, keyword FROM hotspots WHERE id = ANY($1::int[])",
                list(hotspot_ids),
            )
            hotspot_map = {h["id"]: h["keyword"] for h in hotspots}

        # 补充 hotspot_keyword
        for content in structured_contents:
            if content.hotspot_id and not content.hotspot_keyword:
                content.hotspot_keyword = hotspot_map.get(content.hotspot_id)

        # 转换为字典以保持兼容性
        items = [content.model_dump() for content in structured_contents]

        return APIResponse(
            code=0,
            message="success",
            data=ContentListResponse(
                total=total, page=page, page_size=page_size, items=items
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to query contents: {str(e)}"
        )


@router.get("/stats/counts", response_model=APIResponse[dict])
async def get_content_counts(
    hotspot_ids: str = Query(..., description="热词ID列表，逗号分隔"),
    platform: str = Query("xhs", description="平台代码"),
    conn: aiomysql.Connection = Depends(get_db),
):
    """
    批量查询热词的内容数量

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu
    返回格式: {hotspot_id: count, ...}
    """
    if platform not in PLATFORM_CONTENT_TABLES:
        # 有可能是中文平台名，转换成代码
        if platform in PLATFORM_NAME_MAP:
            platform = PLATFORM_NAME_MAP[platform]
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

    table_name = PLATFORM_CONTENT_TABLES[platform]

    try:
        # 解析热词ID列表
        ids = [int(id.strip()) for id in hotspot_ids.split(",") if id.strip()]
        if not ids:
            return APIResponse(code=0, message="success", data={})

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 构建批量查询SQL
            placeholders = ",".join(["%s"] * len(ids))
            count_sql = f"""
                SELECT hotspot_id, COUNT(*) as count
                FROM {table_name}
                WHERE hotspot_id IN ({placeholders})
                GROUP BY hotspot_id
            """
            await cursor.execute(count_sql, ids)
            results = await cursor.fetchall()

            # 转换为字典格式
            counts = {str(row["hotspot_id"]): row["count"] for row in results}

            # 补充没有内容的热词（设为0）
            for hotspot_id in ids:
                if str(hotspot_id) not in counts:
                    counts[str(hotspot_id)] = 0

            return APIResponse(code=0, message="success", data=counts)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hotspot_ids format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to query content counts: {str(e)}"
        )


@router.get("/{platform}/comments", response_model=APIResponse[CommentListResponse])
async def list_comments(
    platform: str,
    note_id: str = Query(..., description="笔记/视频/内容 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: aiomysql.Connection = Depends(get_db),
):
    """
    查询评论列表（返回结构化数据）

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu

    注意：不同平台使用不同的关联字段
    - dy(抖音): aweme_id
    - bili(B站): video_id
    - ks(快手): video_id
    - zhihu(知乎): content_id
    - 其他平���: note_id

    返回结构化评论模型，统一不同平台的字段
    """
    if platform not in PLATFORM_COMMENT_TABLES:
        # 有可能是中文平台名，转换成代码
        if platform in PLATFORM_NAME_MAP:
            platform = PLATFORM_NAME_MAP[platform]
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

    try:
        # 使用 ContentService 获取结构化评论
        structured_comments, total = await content_service.get_comments_by_note_id(
            platform, note_id, page, page_size, conn
        )

        # 转换为字典以保持兼容性
        items = [comment.model_dump() for comment in structured_comments]

        return APIResponse(
            code=0,
            message="success",
            data=CommentListResponse(
                total=total, page=page, page_size=page_size, items=items
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to query comments: {str(e)}"
        )


@router.get("/{platform}/creators/{user_id}", response_model=APIResponse[dict])
async def get_creator(
    platform: str, user_id: str, conn: aiomysql.Connection = Depends(get_db)
):
    """
    查询创作者信息

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu
    """
    if platform not in PLATFORM_CREATOR_TABLES:
        # 有可能是中文平台名，转换成代码
        if platform in PLATFORM_NAME_MAP:
            platform = PLATFORM_NAME_MAP[platform]
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

    table_name = PLATFORM_CREATOR_TABLES[platform]

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            sql = f"SELECT * FROM {table_name} WHERE user_id = %s"
            await cursor.execute(sql, (user_id,))
            creator = await cursor.fetchone()

            if not creator:
                raise HTTPException(status_code=404, detail="Creator not found")

            return APIResponse(code=0, message="success", data=creator)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to query creator: {str(e)}"
        )
