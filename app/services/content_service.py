"""
内容服务 - 提供统一的内容和评论查询接口
"""

from typing import List, Dict, Optional, Any
import aiomysql
from app.schemas.content import StructuredContent, StructuredComment
from app.constants import (
    PLATFORM_CONTENT_TABLES,
    PLATFORM_COMMENT_TABLES,
    PLATFORM_CONTENT_ID_FIELDS,
)
from datetime import datetime


class ContentService:
    """内容服务类 - 提供跨平台的内容和评论查询功能"""

    # 字段映射：标准字段名 -> 可能的平台字段名列表
    FIELD_MAPPINGS = {
        # 内容字段
        "title": ["title"],
        "desc": ["desc", "description"],
        "content_text": ["content", "note_card_content", "content_text"],
        "user_id": ["user_id"],
        "nickname": ["nickname", "author_name"],
        "avatar": ["avatar", "user_avatar"],
        "ip_location": ["ip_location"],
        "liked_count": ["liked_count", "like_count", "digg_count"],
        "collected_count": ["collected_count", "collect_count", "favorite_count"],
        "comment_count": ["comment_count", "comments_count"],
        "share_count": ["share_count"],
        "view_count": ["view_count", "play_count"],
        "time": ["time"],
        "create_time": ["create_time", "created_time"],
        "add_ts": ["add_ts"],
        "last_modify_ts": ["last_modify_ts"],
        # 评论字段
        "comment_content": ["content", "comment_content"],
        "sub_comment_count": ["sub_comment_count"],
    }

    def __init__(self):
        """初始化内容服务"""
        pass

    def _get_field_value(self, raw_dict: dict, field_name: str) -> Any:
        """
        从原始数据中获取字段值（处理不同平台的字段名差异）

        Args:
            raw_dict: 原始数据库记录
            field_name: 标准字段名

        Returns:
            字段值，如果不存在则返回 None
        """
        possible_names = self.FIELD_MAPPINGS.get(field_name, [field_name])
        for name in possible_names:
            if name in raw_dict and raw_dict[name] is not None:
                return raw_dict[name]
        return None

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """
        解析日期时间字段

        Args:
            value: 可能是 datetime、字符串或 None

        Returns:
            datetime 对象或 None
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return None
        return None

    def _map_raw_to_structured_content(
        self,
        raw_dict: dict,
        platform: str,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """
        将原始数据库记录转换为结构化内容模型

        Args:
            raw_dict: 原始数据库记录
            platform: 平台代码
            hotspot_id: 热点ID（可选）
            hotspot_keyword: 热点关键词（可选）

        Returns:
            结构化内容对象
        """
        # content_id 使用数据库主键 id，而不是平台特定的字段
        content_id = raw_dict.get("id", "")

        # 提取公共字段
        time_value = self._get_field_value(raw_dict, "time")
        # 将时间戳转换为字符串（如果是整数）
        if isinstance(time_value, int):
            time_value = str(time_value)
        
        common_fields = {
            "platform": platform,
            "content_id": str(content_id),
            "title": self._get_field_value(raw_dict, "title"),
            "desc": self._get_field_value(raw_dict, "desc"),
            "content_text": self._get_field_value(raw_dict, "content_text"),
            "user_id": str(self._get_field_value(raw_dict, "user_id") or ""),
            "nickname": self._get_field_value(raw_dict, "nickname"),
            "avatar": self._get_field_value(raw_dict, "avatar"),
            "ip_location": self._get_field_value(raw_dict, "ip_location"),
            "liked_count": self._get_field_value(raw_dict, "liked_count"),
            "collected_count": self._get_field_value(raw_dict, "collected_count"),
            "comment_count": self._get_field_value(raw_dict, "comment_count"),
            "share_count": self._get_field_value(raw_dict, "share_count"),
            "view_count": self._get_field_value(raw_dict, "view_count"),
            "time": time_value,
            "create_time": self._parse_datetime(
                self._get_field_value(raw_dict, "create_time")
            ),
            "add_ts": self._get_field_value(raw_dict, "add_ts"),
            "last_modify_ts": self._get_field_value(raw_dict, "last_modify_ts"),
            "hotspot_id": hotspot_id or raw_dict.get("hotspot_id"),
            "hotspot_keyword": hotspot_keyword or raw_dict.get("hotspot_keyword"),
        }

        # 标准字段列表
        standard_fields = {
            "id",  # 数据库主键
            # 平台特定的内容ID字段
            "note_id",
            "aweme_id",
            "video_id",
            "content_id",
            # 其他标准字段
            "title",
            "desc",
            "content",
            "note_card_content",
            "content_text",
            "user_id",
            "nickname",
            "author_name",
            "avatar",
            "user_avatar",
            "ip_location",
            "liked_count",
            "like_count",
            "digg_count",
            "collected_count",
            "collect_count",
            "favorite_count",
            "comment_count",
            "comments_count",
            "share_count",
            "view_count",
            "play_count",
            "time",
            "create_time",
            "created_time",
            "add_ts",
            "last_modify_ts",
            "hotspot_id",
            "hotspot_keyword",
            "comments",  # 不放入 platform_specific
        }

        # 提取平台特有字段
        platform_specific = {}
        for key, value in raw_dict.items():
            if key not in standard_fields:
                # 转换 datetime 为字符串
                if isinstance(value, datetime):
                    platform_specific[key] = value.isoformat()
                else:
                    platform_specific[key] = value

        common_fields["platform_specific"] = platform_specific

        # 处理嵌套的评论
        comments = []
        if "comments" in raw_dict and isinstance(raw_dict["comments"], list):
            for comment_raw in raw_dict["comments"]:
                comments.append(
                    self._map_raw_to_structured_comment(comment_raw, platform)
                )
        common_fields["comments"] = comments

        return StructuredContent(**common_fields)

    def _map_raw_to_structured_comment(
        self, raw_dict: dict, platform: str
    ) -> StructuredComment:
        """
        将原始数据库记录转换为结构化评论模型

        Args:
            raw_dict: 原始数据库记录
            platform: 平台代码

        Returns:
            结构化评论对象
        """
        # 评论ID字段可能是 comment_id 或 id
        comment_id = raw_dict.get("comment_id") or raw_dict.get("id") or ""

        # 提取公共字段
        common_fields = {
            "platform": platform,
            "comment_id": str(comment_id),
            "content": self._get_field_value(raw_dict, "comment_content"),
            "user_id": str(self._get_field_value(raw_dict, "user_id") or ""),
            "nickname": self._get_field_value(raw_dict, "nickname"),
            "avatar": self._get_field_value(raw_dict, "avatar"),
            "ip_location": self._get_field_value(raw_dict, "ip_location"),
            "liked_count": self._get_field_value(raw_dict, "liked_count"),
            "sub_comment_count": self._get_field_value(raw_dict, "sub_comment_count"),
            "create_time": self._parse_datetime(
                self._get_field_value(raw_dict, "create_time")
            ),
            "add_ts": self._get_field_value(raw_dict, "add_ts"),
            "last_modify_ts": self._get_field_value(raw_dict, "last_modify_ts"),
        }

        # 标准字段列表
        standard_fields = {
            "comment_id",
            "id",
            "content",
            "comment_content",
            "user_id",
            "nickname",
            "author_name",
            "avatar",
            "user_avatar",
            "ip_location",
            "liked_count",
            "like_count",
            "sub_comment_count",
            "create_time",
            "created_time",
            "add_ts",
            "last_modify_ts",
        }

        # 提取平台特有字段
        platform_specific = {}
        for key, value in raw_dict.items():
            if key not in standard_fields:
                # 转换 datetime 为字符串
                if isinstance(value, datetime):
                    platform_specific[key] = value.isoformat()
                else:
                    platform_specific[key] = value

        common_fields["platform_specific"] = platform_specific

        return StructuredComment(**common_fields)

    async def get_contents_by_hotspot_id(
        self, hotspot_id: int, hotspot_keyword: str, conn: aiomysql.Connection
    ) -> Dict[str, List[StructuredContent]]:
        """
        根据热点ID获取所有平台的内容和评论

        Args:
            hotspot_id: 热点ID
            hotspot_keyword: 热点关键词
            conn: MySQL数据库连接

        Returns:
            字典，key为平台代码，value为该平台的结构化内容列表
        """
        results = {}

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            for platform, content_table in PLATFORM_CONTENT_TABLES.items():
                comment_table = PLATFORM_COMMENT_TABLES[platform]
                content_id_field = PLATFORM_CONTENT_ID_FIELDS.get(platform, "note_id")

                # 查询该平台下 hotspot_id 匹配的所有内容
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
                content_ids = [
                    c.get(content_id_field) for c in contents if c.get(content_id_field)
                ]

                comments_by_content = {}
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

                    # 将评论按 content_id 分组
                    for comment in comments:
                        cid = comment.get(content_id_field)
                        if cid:
                            if cid not in comments_by_content:
                                comments_by_content[cid] = []
                            comments_by_content[cid].append(comment)

                # 转换为结构化内容
                structured_contents = []
                for content in contents:
                    cid = content.get(content_id_field)
                    # 将评论嵌入到内容中
                    content["comments"] = comments_by_content.get(cid, [])
                    structured_content = self._map_raw_to_structured_content(
                        content, platform, hotspot_id, hotspot_keyword
                    )
                    structured_contents.append(structured_content)

                results[platform] = structured_contents

        return results

    async def get_contents_by_platform(
        self,
        platform: str,
        filters: Dict[str, Any],
        page: int,
        page_size: int,
        conn: aiomysql.Connection,
    ) -> tuple[List[StructuredContent], int]:
        """
        根据平台和过滤条件获取内容列表

        Args:
            platform: 平台代码
            filters: 过滤条件（hotspot_id, keyword, start_date, end_date）
            page: 页码
            page_size: 每页大小
            conn: MySQL数据库连接

        Returns:
            (结构化内容列表, 总数)
        """
        from app.constants import PLATFORM_TIME_FIELDS

        table_name = PLATFORM_CONTENT_TABLES[platform]
        time_field = PLATFORM_TIME_FIELDS[platform]

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 构建查询条件
            where_clauses = []
            params = []

            # 热词ID过滤
            if "hotspot_id" in filters and filters["hotspot_id"]:
                where_clauses.append("hotspot_id = %s")
                params.append(filters["hotspot_id"])

            # 关键词搜索
            if "keyword" in filters and filters["keyword"]:
                where_clauses.append(
                    "(title LIKE %s OR `desc` LIKE %s OR content LIKE %s)"
                )
                keyword_pattern = f"%{filters['keyword']}%"
                params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

            # 时间范围过滤
            if "start_date" in filters and filters["start_date"]:
                where_clauses.append(f"{time_field} >= %s")
                params.append(f"{filters['start_date']} 00:00:00")

            if "end_date" in filters and filters["end_date"]:
                where_clauses.append(f"{time_field} <= %s")
                params.append(f"{filters['end_date']} 23:59:59")

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

            # 转换为结构化内容
            structured_contents = []
            for item in items:
                structured_content = self._map_raw_to_structured_content(item, platform)
                structured_contents.append(structured_content)

            return structured_contents, total

    async def get_comments_by_note_id(
        self,
        platform: str,
        note_id: str,
        page: int,
        page_size: int,
        conn: aiomysql.Connection,
    ) -> tuple[List[StructuredComment], int]:
        """
        根据内容ID获取评论列表

        Args:
            platform: 平台代码
            note_id: 内容ID
            page: 页码
            page_size: 每页大小
            conn: MySQL数据库连接

        Returns:
            (结构化评论列表, 总数)
        """
        table_name = PLATFORM_COMMENT_TABLES[platform]
        content_id_field = PLATFORM_CONTENT_ID_FIELDS.get(platform, "note_id")

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

            # 转换为结构化评论
            structured_comments = []
            for item in items:
                structured_comment = self._map_raw_to_structured_comment(item, platform)
                structured_comments.append(structured_comment)

            return structured_comments, total


# 全局实例
content_service = ContentService()
