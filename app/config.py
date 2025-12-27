import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置（复用 MediaCrawlerPro-Python 的配置）"""

    # API 服务配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # 数据库配置（复用 MediaCrawlerPro-Python 的配置）
    RELATION_DB_HOST: str = "localhost"
    RELATION_DB_PORT: int = 3307
    RELATION_DB_USER: str = "root"
    RELATION_DB_PWD: str = "123456"
    RELATION_DB_NAME: str = "media_crawler_pro"

    # Redis 配置
    REDIS_DB_HOST: str = "localhost"
    REDIS_DB_PORT: int = 6378
    REDIS_DB_PWD: str = "123456"
    REDIS_DB_NUM: int = 0

    # Celery 配置
    @property
    def CELERY_BROKER_URL(self) -> str:
        if self.REDIS_DB_PWD:
            return f"redis://:{self.REDIS_DB_PWD}@{self.REDIS_DB_HOST}:{self.REDIS_DB_PORT}/1"
        return f"redis://{self.REDIS_DB_HOST}:{self.REDIS_DB_PORT}/1"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        if self.REDIS_DB_PWD:
            return f"redis://:{self.REDIS_DB_PWD}@{self.REDIS_DB_HOST}:{self.REDIS_DB_PORT}/2"
        return f"redis://{self.REDIS_DB_HOST}:{self.REDIS_DB_PORT}/2"

    # MediaCrawlerPro-Python 路径配置
    CRAWLER_BASE_PATH: str = os.getenv(
        "CRAWLER_BASE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "MediaCrawlerPro-Python")
    )

    @property
    def CRAWLER_MAIN_PATH(self) -> str:
        return os.path.join(self.CRAWLER_BASE_PATH, "main.py")

    CRAWLER_PYTHON_PATH: str = "python"

    # 签名服务配置
    SIGN_SRV_HOST: str = "localhost"
    SIGN_SRV_PORT: int = 8989

    # IP 代理配置
    ENABLE_IP_PROXY: bool = False
    IP_PROXY_POOL_COUNT: int = 2
    IP_PROXY_PROVIDER_NAME: str = "kuaidaili"
    KDL_SECERT_ID: str = ""
    KDL_SIGNATURE: str = ""
    KDL_USER_NAME: str = ""
    KDL_USER_PWD: str = ""

    # MediaCrawlerPro-Python 爬虫配置
    # 基础配置
    CRAWLER_PLATFORM: str = "xhs"  # xhs, weibo, douyin, kuaishou, bilibili, tieba, zhihu
    CRAWLER_KEYWORDS: str = "deepseek,chatgpt"  # 搜索关键词，逗号分隔
    CRAWLER_TYPE: str = "search"  # search, detail, creator, homefeed
    CRAWLER_SORT_TYPE: str = "popularity_descending"  # 排序类型（小红书）
    CRAWLER_PUBLISH_TIME_TYPE: int = 0  # 发布时间类型（抖音）

    # 数据保存配置
    CRAWLER_SAVE_DATA_OPTION: str = "db"  # csv, db, json
    CRAWLER_ACCOUNT_POOL_SAVE_TYPE: str = "mysql"  # xlsx, mysql

    # 爬取控制配置
    CRAWLER_START_PAGE: int = 1  # 开始页数
    CRAWLER_MAX_NOTES_COUNT: int = 40  # 最大爬取数量
    CRAWLER_MAX_CONCURRENCY_NUM: int = 1  # 并发数量（建议设为1）
    CRAWLER_TIME_SLEEP: int = 5  # 请求间隔（秒）

    # 评论爬取配置
    CRAWLER_ENABLE_GET_COMMENTS: bool = True  # 是否爬取评论
    CRAWLER_ENABLE_GET_SUB_COMMENTS: bool = False  # 是否爬取二级评论
    CRAWLER_PER_NOTE_MAX_COMMENTS_COUNT: int = 0  # 单帖最大评论数（0表示不限制）

    # 断点续爬配置
    CRAWLER_ENABLE_CHECKPOINT: bool = True  # 是否启用断点续爬
    CRAWLER_SPECIFIED_CHECKPOINT_ID: str = ""  # 指定检查点ID
    CRAWLER_CHECKPOINT_STORAGE_TYPE: str = "file"  # file, redis

    # 其他配置
    CRAWLER_ENABLE_LOG_FILE: bool = True  # 是否输出日志到文件
    CRAWLER_ENABLE_WEIBO_FULL_TEXT: bool = False  # 微博是否爬取全文

    # 缓存配置
    CRAWLER_CACHE_TYPE: str = "redis"  # redis, memory

    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/trend-api-server/app.log"

    @property
    def database_url(self) -> str:
        """MySQL 连接 URL（用于 SQLAlchemy）"""
        return f"mysql+aiomysql://{self.RELATION_DB_USER}:{self.RELATION_DB_PWD}@{self.RELATION_DB_HOST}:{self.RELATION_DB_PORT}/{self.RELATION_DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
