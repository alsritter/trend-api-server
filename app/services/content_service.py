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

    def __init__(self):
        """初始化内容服务"""
        pass

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """
        解析日期时间字段

        Args:
            value: 可能是 datetime、字符串、整数时间戳或 None

        Returns:
            datetime 对象或 None
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                # 假设是秒级时间戳
                return datetime.fromtimestamp(value)
            except Exception:
                return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return None
        return None

    # ========== 小红书映射 ==========
    def _map_xhs_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射小红书内容"""
        return StructuredContent(
            platform="xhs",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("desc"),  # 小红书的文本内容在 desc 字段
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("liked_count"),
            collected_count=raw.get("collected_count"),
            comment_count=raw.get("comment_count"),
            share_count=raw.get("share_count"),
            view_count=None,
            time=str(raw.get("time", "")) if raw.get("time") else None,
            create_time=self._parse_datetime(raw.get("time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "type": raw.get("type"),
                "video_url": raw.get("video_url"),
                "last_update_time": raw.get("last_update_time"),
                "image_list": raw.get("image_list"),
                "tag_list": raw.get("tag_list"),
                "note_url": raw.get("note_url"),
                "source_keyword": raw.get("source_keyword"),
            },
            comments=raw.get("comments", []),
        )

    def _map_xhs_comment(self, raw: dict) -> StructuredComment:
        """映射小红书评论"""
        return StructuredComment(
            platform="xhs",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "pictures": raw.get("pictures"),
                "parent_comment_id": raw.get("parent_comment_id"),
                "note_url": raw.get("note_url"),
                "target_comment_id": raw.get("target_comment_id"),
            },
        )

    # ========== 抖音映射 ==========
    def _map_douyin_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射抖音内容"""
        return StructuredContent(
            platform="dy",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("desc"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("liked_count"),
            collected_count=raw.get("collected_count"),
            comment_count=raw.get("comment_count"),
            share_count=raw.get("share_count"),
            view_count=None,
            time=str(raw.get("create_time", "")) if raw.get("create_time") else None,
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "aweme_id": raw.get("aweme_id"),
                "aweme_type": raw.get("aweme_type"),
                "sec_uid": raw.get("sec_uid"),
                "short_user_id": raw.get("short_user_id"),
                "user_unique_id": raw.get("user_unique_id"),
                "user_signature": raw.get("user_signature"),
                "aweme_url": raw.get("aweme_url"),
                "cover_url": raw.get("cover_url"),
                "video_download_url": raw.get("video_download_url"),
                "source_keyword": raw.get("source_keyword"),
                "is_ai_generated": raw.get("is_ai_generated"),
            },
            comments=raw.get("comments", []),
        )

    def _map_douyin_comment(self, raw: dict) -> StructuredComment:
        """映射抖音评论"""
        return StructuredComment(
            platform="dy",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "aweme_id": raw.get("aweme_id"),
                "sec_uid": raw.get("sec_uid"),
                "short_user_id": raw.get("short_user_id"),
                "user_unique_id": raw.get("user_unique_id"),
                "user_signature": raw.get("user_signature"),
                "parent_comment_id": raw.get("parent_comment_id"),
                "pictures": raw.get("pictures"),
                "reply_to_reply_id": raw.get("reply_to_reply_id"),
            },
        )

    # ========== B站映射 ==========
    def _map_bilibili_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射B站内容"""
        return StructuredContent(
            platform="bili",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("desc"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=None,
            liked_count=raw.get("liked_count"),
            collected_count=None,
            comment_count=raw.get("video_comment"),
            share_count=None,
            view_count=raw.get("video_play_count"),
            time=str(raw.get("create_time", "")) if raw.get("create_time") else None,
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "video_id": raw.get("video_id"),
                "bvid": raw.get("bvid"),
                "video_type": raw.get("video_type"),
                "video_danmaku": raw.get("video_danmaku"),
                "video_url": raw.get("video_url"),
                "video_cover_url": raw.get("video_cover_url"),
                "source_keyword": raw.get("source_keyword"),
                "duration": raw.get("duration"),
            },
            comments=raw.get("comments", []),
        )

    def _map_bilibili_comment(self, raw: dict) -> StructuredComment:
        """映射B站评论"""
        return StructuredComment(
            platform="bili",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=None,
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "video_id": raw.get("video_id"),
                "parent_comment_id": raw.get("parent_comment_id"),
            },
        )

    # ========== 快手映射 ==========
    def _map_kuaishou_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射快手内容"""
        return StructuredContent(
            platform="ks",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("desc"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=None,
            liked_count=raw.get("liked_count"),
            collected_count=None,
            comment_count=None,
            share_count=None,
            view_count=raw.get("viewd_count"),
            time=str(raw.get("create_time", "")) if raw.get("create_time") else None,
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "video_id": raw.get("video_id"),
                "video_type": raw.get("video_type"),
                "video_url": raw.get("video_url"),
                "video_cover_url": raw.get("video_cover_url"),
                "video_play_url": raw.get("video_play_url"),
                "source_keyword": raw.get("source_keyword"),
            },
            comments=raw.get("comments", []),
        )

    def _map_kuaishou_comment(self, raw: dict) -> StructuredComment:
        """映射快手评论"""
        return StructuredComment(
            platform="ks",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=None,
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "video_id": raw.get("video_id"),
                "parent_comment_id": raw.get("parent_comment_id"),
            },
        )

    # ========== 微博映射 ==========
    def _map_weibo_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射微博内容"""
        return StructuredContent(
            platform="wb",
            content_id=str(raw.get("id", "")),
            title=None,  # 微博没有标题
            desc=None,
            content_text=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("liked_count"),
            collected_count=None,
            comment_count=raw.get("comments_count"),
            share_count=raw.get("shared_count"),
            view_count=None,
            time=str(raw.get("create_time", "")) if raw.get("create_time") else None,
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "gender": raw.get("gender"),
                "profile_url": raw.get("profile_url"),
                "create_date_time": raw.get("create_date_time"),
                "note_url": raw.get("note_url"),
                "image_list": raw.get("image_list"),
                "video_url": raw.get("video_url"),
                "source_keyword": raw.get("source_keyword"),
            },
            comments=raw.get("comments", []),
        )

    def _map_weibo_comment(self, raw: dict) -> StructuredComment:
        """映射微博评论"""
        return StructuredComment(
            platform="wb",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("nickname"),
            avatar=raw.get("avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=self._parse_datetime(raw.get("create_time")),
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "gender": raw.get("gender"),
                "profile_url": raw.get("profile_url"),
                "create_date_time": raw.get("create_date_time"),
                "parent_comment_id": raw.get("parent_comment_id"),
            },
        )

    # ========== 贴吧映射 ==========
    def _map_tieba_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射贴吧内容"""
        return StructuredContent(
            platform="tieba",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("desc"),
            user_id=None,
            nickname=raw.get("user_nickname"),
            avatar=raw.get("user_avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=None,
            collected_count=None,
            comment_count=raw.get("total_replay_num"),
            share_count=None,
            view_count=None,
            time=raw.get("publish_time"),
            create_time=None,  # 贴吧的 publish_time 是字符串格式
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "note_url": raw.get("note_url"),
                "user_link": raw.get("user_link"),
                "tieba_id": raw.get("tieba_id"),
                "tieba_name": raw.get("tieba_name"),
                "tieba_link": raw.get("tieba_link"),
                "total_replay_page": raw.get("total_replay_page"),
                "source_keyword": raw.get("source_keyword"),
            },
            comments=raw.get("comments", []),
        )

    def _map_tieba_comment(self, raw: dict) -> StructuredComment:
        """映射贴吧评论"""
        return StructuredComment(
            platform="tieba",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=None,
            nickname=raw.get("user_nickname"),
            avatar=raw.get("user_avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=None,
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=None,  # 贴吧的 publish_time 是字符串格式
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "note_id": raw.get("note_id"),
                "note_url": raw.get("note_url"),
                "parent_comment_id": raw.get("parent_comment_id"),
                "user_link": raw.get("user_link"),
                "tieba_id": raw.get("tieba_id"),
                "tieba_name": raw.get("tieba_name"),
                "tieba_link": raw.get("tieba_link"),
                "publish_time": raw.get("publish_time"),
            },
        )

    # ========== 知乎映射 ==========
    def _map_zhihu_content(
        self,
        raw: dict,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """映射知乎内容"""
        return StructuredContent(
            platform="zhihu",
            content_id=str(raw.get("id", "")),
            title=raw.get("title"),
            desc=raw.get("desc"),
            content_text=raw.get("content_text"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("user_nickname"),
            avatar=raw.get("user_avatar"),
            ip_location=None,
            liked_count=raw.get("voteup_count"),
            collected_count=None,
            comment_count=raw.get("comment_count"),
            share_count=None,
            view_count=None,
            time=raw.get("created_time"),
            create_time=None,  # 知乎的时间是字符串格式
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            hotspot_id=hotspot_id or raw.get("hotspot_id"),
            hotspot_keyword=hotspot_keyword or raw.get("hotspot_keyword"),
            platform_specific={
                "content_id": raw.get("content_id"),
                "content_type": raw.get("content_type"),
                "content_url": raw.get("content_url"),
                "question_id": raw.get("question_id"),
                "updated_time": raw.get("updated_time"),
                "source_keyword": raw.get("source_keyword"),
                "user_link": raw.get("user_link"),
                "user_url_token": raw.get("user_url_token"),
            },
            comments=raw.get("comments", []),
        )

    def _map_zhihu_comment(self, raw: dict) -> StructuredComment:
        """映射知乎评论"""
        return StructuredComment(
            platform="zhihu",
            comment_id=str(raw.get("comment_id", "")),
            content=raw.get("content"),
            user_id=str(raw.get("user_id", "")),
            nickname=raw.get("user_nickname"),
            avatar=raw.get("user_avatar"),
            ip_location=raw.get("ip_location"),
            liked_count=raw.get("like_count"),
            sub_comment_count=raw.get("sub_comment_count"),
            create_time=None,  # 知乎的时间是字符串格式
            add_ts=raw.get("add_ts"),
            last_modify_ts=raw.get("last_modify_ts"),
            platform_specific={
                "content_id": raw.get("content_id"),
                "content_type": raw.get("content_type"),
                "parent_comment_id": raw.get("parent_comment_id"),
                "publish_time": raw.get("publish_time"),
                "dislike_count": raw.get("dislike_count"),
                "user_link": raw.get("user_link"),
            },
        )

    # ========== 统一映射入口 ==========
    def _map_raw_to_structured_content(
        self,
        raw_dict: dict,
        platform: str,
        hotspot_id: Optional[int] = None,
        hotspot_keyword: Optional[str] = None,
    ) -> StructuredContent:
        """
        将原始数据库记录转换为结构化内容模型（统一入口）

        Args:
            raw_dict: 原始数据库记录
            platform: 平台代码
            hotspot_id: 热点ID（可选）
            hotspot_keyword: 热点关键词（可选）

        Returns:
            结构化内容对象
        """
        mapper = {
            "xhs": self._map_xhs_content,
            "dy": self._map_douyin_content,
            "bili": self._map_bilibili_content,
            "ks": self._map_kuaishou_content,
            "wb": self._map_weibo_content,
            "tieba": self._map_tieba_content,
            "zhihu": self._map_zhihu_content,
        }.get(platform)

        if not mapper:
            raise ValueError(f"不支持的平台: {platform}")

        # 处理嵌套的评论
        comments_raw = raw_dict.pop("comments", [])
        structured_content = mapper(raw_dict, hotspot_id, hotspot_keyword)

        # 映射评论
        if comments_raw:
            structured_content.comments = [
                self._map_raw_to_structured_comment(c, platform) for c in comments_raw
            ]

        return structured_content

    def _map_raw_to_structured_comment(
        self, raw_dict: dict, platform: str
    ) -> StructuredComment:
        """
        将原始数据库记录转换为结构化评论模型（统一入口）

        Args:
            raw_dict: 原始数据库记录
            platform: 平台代码

        Returns:
            结构化评论对象
        """
        mapper = {
            "xhs": self._map_xhs_comment,
            "dy": self._map_douyin_comment,
            "bili": self._map_bilibili_comment,
            "ks": self._map_kuaishou_comment,
            "wb": self._map_weibo_comment,
            "tieba": self._map_tieba_comment,
            "zhihu": self._map_zhihu_comment,
        }.get(platform)

        if not mapper:
            raise ValueError(f"不支持的平台: {platform}")

        return mapper(raw_dict)

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
