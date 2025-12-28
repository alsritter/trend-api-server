from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import aiomysql
from app.schemas.content import ContentListResponse, CommentListResponse
from app.schemas.common import APIResponse
from app.dependencies import get_db

router = APIRouter()

# 平台内容表映射
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

# 平台创作者表映射
PLATFORM_CREATOR_TABLES = {
    "xhs": "xhs_creator",
    "dy": "dy_creator",
    "ks": "kuaishou_creator",
    "bili": "bilibili_up_info",
    "wb": "weibo_creator",
    "tieba": "tieba_creator",
    "zhihu": "zhihu_creator",
}

# 平台时间字段映射
PLATFORM_TIME_FIELDS = {
    "xhs": "time",
    "dy": "create_time",
    "ks": "create_time",
    "bili": "create_time",
    "wb": "create_time",
    "tieba": "publish_time",
    "zhihu": "created_time",
}


@router.get("/{platform}/notes", response_model=APIResponse[ContentListResponse])
async def list_contents(
    platform: str,
    keyword: Optional[str] = Query(None, description="关键词搜索（标题或内容）"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn: aiomysql.Connection = Depends(get_db),
):
    """
    查询平台内容列表（笔记/视频）

    支持的平台: xhs, dy, ks, bili, wb, tieba, zhihu
    """
    if platform not in PLATFORM_CONTENT_TABLES:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    table_name = PLATFORM_CONTENT_TABLES[platform]
    time_field = PLATFORM_TIME_FIELDS[platform]

    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 构建查询条件
            where_clauses = []
            params = []

            if keyword:
                # 不同平台的字段名可能不同，这里使用通用的方式
                where_clauses.append(
                    "(title LIKE %s OR `desc` LIKE %s OR content LIKE %s)"
                )
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

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

            return APIResponse(
                code=0,
                message="success",
                data=ContentListResponse(
                    total=total, page=page, page_size=page_size, items=items
                ),
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to query contents: {str(e)}"
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
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    table_name = PLATFORM_COMMENT_TABLES[platform]

    # 根据平台确定关联字段名
    PLATFORM_CONTENT_ID_FIELDS = {
        "dy": "aweme_id",  # 抖音
        "bili": "video_id",  # B站
        "ks": "video_id",  # 快手
        "zhihu": "content_id",  # 知乎
        "xhs": "note_id",  # 小红书
        "wb": "note_id",  # 微博
        "tieba": "note_id",  # 贴吧
    }

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
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

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
