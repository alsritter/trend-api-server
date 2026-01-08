"""
平台相关常量定义
"""

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

# 中文映射成平台
PLATFORM_NAME_MAP = {
    "小红书": "xhs",
    "抖音": "dy",
    "快手": "ks",
    "哔哩哔哩": "bili",
    "微博": "wb",
    "贴吧": "tieba",
    "知乎": "zhihu",
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
