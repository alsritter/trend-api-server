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
    MYSQL_HOST: str = os.getenv("RELATION_DB_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("RELATION_DB_PORT", "3307"))
    MYSQL_USER: str = os.getenv("RELATION_DB_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("RELATION_DB_PWD", "123456")
    MYSQL_DATABASE: str = os.getenv("RELATION_DB_NAME", "media_crawler_pro")

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_DB_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_DB_PORT", "6378"))
    REDIS_PASSWORD: str = os.getenv("REDIS_DB_PWD", "123456")
    REDIS_DB: int = int(os.getenv("REDIS_DB_NUM", "0"))

    # Celery 配置
    @property
    def CELERY_BROKER_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/1"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/2"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    # MediaCrawlerPro-Python 路径配置
    CRAWLER_BASE_PATH: str = os.getenv(
        "CRAWLER_BASE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "MediaCrawlerPro-Python")
    )

    @property
    def CRAWLER_MAIN_PATH(self) -> str:
        return os.path.join(self.CRAWLER_BASE_PATH, "main.py")

    CRAWLER_PYTHON_PATH: str = os.getenv("CRAWLER_PYTHON_PATH", "python")

    # 签名服务配置
    SIGN_SRV_HOST: str = os.getenv("SIGN_SRV_HOST", "localhost")
    SIGN_SRV_PORT: int = int(os.getenv("SIGN_SRV_PORT", "8989"))

    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/trend-api-server/app.log"

    @property
    def database_url(self) -> str:
        """MySQL 连接 URL（用于 SQLAlchemy）"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
