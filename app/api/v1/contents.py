from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import aiomysql
from app.schemas.content import ContentListResponse, CommentListResponse
from app.schemas.common import APIResponse
from app.dependencies import get_db
from app.db.vector_session import get_vector_db
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
    查询平台内容列表（笔记/视频）

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu
    支持按热词ID过滤，返回该热词关联的所有内容
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
    time_field = PLATFORM_TIME_FIELDS[platform]

    try:
        # 如果提供了 hotspot_id，验证热词是否存在
        if hotspot_id:
            hotspot_result = await pg_conn.fetchrow(
                "SELECT id, keyword FROM hotspots WHERE id = $1", hotspot_id
            )
            if not hotspot_result:
                raise HTTPException(status_code=404, detail=f"热词 {hotspot_id} 不存在")

        # 从 MySQL 查询内容数据
        async with mysql_conn.cursor(aiomysql.DictCursor) as cursor:
            # 构建查询条件
            where_clauses = []
            params = []

            # 热词ID过滤 - 直接使用 hotspot_id 字段
            if hotspot_id:
                where_clauses.append("hotspot_id = %s")
                params.append(hotspot_id)

            # 关键词搜索
            if keyword:
                where_clauses.append(
                    "(title LIKE %s OR `desc` LIKE %s OR content LIKE %s)"
                )
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

            # 时间范围过滤
            if start_date:
                where_clauses.append(f"{time_field} >= %s")
                params.append(f"{start_date} 00:00:00")

            if end_date:
                where_clauses.append(f"{time_field} <= %s")
                params.append(f"{end_date} 23:59:59")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {where_sql}"
            await cursor.execute(count_sql, params)
            total_result = await cursor.fetchone()
            total = total_result["total"]

            # 查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {table_name}
                WHERE {where_sql}
                ORDER BY {time_field} DESC
                LIMIT %s OFFSET %s
            """
            await cursor.execute(data_sql, params + [page_size, offset])
            items = await cursor.fetchall()

            # 如果结果中有 hotspot_id，从 PostgreSQL 获取对应的关键词信息
            hotspot_ids = set()
            for item in items:
                hid = item.get("hotspot_id")
                if hid is not None and hid != "":
                    # 确保转换为整数类型
                    hotspot_ids.add(int(hid) if isinstance(hid, str) else hid)

            # 批量查询热词信息
            hotspot_map = {}
            if hotspot_ids:
                hotspots = await pg_conn.fetch(
                    "SELECT id, keyword FROM hotspots WHERE id = ANY($1::int[])",
                    list(hotspot_ids),
                )
                hotspot_map = {h["id"]: h["keyword"] for h in hotspots}

            # 为每个 item 添加 hotspot_keyword
            for item in items:
                hid = item.get("hotspot_id")
                item["hotspot_keyword"] = (
                    hotspot_map.get(int(hid)) if hid and hid != "" else None
                )

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
    查询评论列表

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu

    注意：不同平台使用不同的关联字段
    - dy(抖音): aweme_id
    - bili(B站): video_id
    - ks(快手): video_id
    - zhihu(知乎): content_id
    - 其他平台: note_id
    """
    if platform not in PLATFORM_COMMENT_TABLES:
        # 有可能是中文平台名，转换成代码
        if platform in PLATFORM_NAME_MAP:
            platform = PLATFORM_NAME_MAP[platform]
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported platform: {platform}"
            )

    table_name = PLATFORM_COMMENT_TABLES[platform]

    # 根据平台确定关联字段名
    content_id_field = PLATFORM_CONTENT_ID_FIELDS.get(platform, "note_id")

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {content_id_field} = %s"
            await cursor.execute(count_sql, (note_id,))
            total_result = await cursor.fetchone()
            total = total_result["total"]

            # 查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {table_name}
                WHERE {content_id_field} = %s
                ORDER BY add_ts DESC
                LIMIT %s OFFSET %s
            """
            await cursor.execute(data_sql, (note_id, page_size, offset))
            items = await cursor.fetchall()

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
