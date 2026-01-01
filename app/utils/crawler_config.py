"""
MediaCrawlerPro-Python 配置转换工具

此模块将 API 服务的配置转换为 MediaCrawlerPro-Python 需要的环境变量格式，
实现配置的统一管理，无需修改 MediaCrawlerPro-Python 项目代码。
"""

from typing import Dict
from app.config import settings


def get_crawler_env_config() -> Dict[str, str]:
    """
    将 API 服务的配置转换为 MediaCrawlerPro-Python 需要的环境变量字典

    MediaCrawlerPro-Python 使用 os.getenv() 读取配置，
    我们通过设置环境变量的方式，让它使用我们 API 服务的配置。

    Returns:
        Dict[str, str]: 环境变量字典
    """
    env_config = {
        # 数据库配置 (db_config.py)
        "RELATION_DB_HOST": str(settings.RELATION_DB_HOST),
        "RELATION_DB_PORT": str(settings.RELATION_DB_PORT),
        "RELATION_DB_USER": str(settings.RELATION_DB_USER),
        "RELATION_DB_PWD": str(settings.RELATION_DB_PWD),
        "RELATION_DB_NAME": str(settings.RELATION_DB_NAME),
        # Redis 配置 (db_config.py)
        "REDIS_DB_HOST": str(settings.REDIS_DB_HOST),
        "REDIS_DB_PORT": str(settings.REDIS_DB_PORT),
        "REDIS_DB_PWD": str(settings.REDIS_DB_PWD),
        "REDIS_DB_NUM": str(settings.REDIS_DB_NUM),
        # 缓存类型配置 (db_config.py)
        "USE_CACHE_TYPE": str(settings.CRAWLER_CACHE_TYPE),
        # 签名服务配置 (sign_srv_config.py)
        "SIGN_SRV_HOST": str(settings.SIGN_SRV_HOST),
        "SIGN_SRV_PORT": str(settings.SIGN_SRV_PORT),
        # IP 代理配置 (proxy_config.py)
        "ENABLE_IP_PROXY": str(settings.ENABLE_IP_PROXY),
        "IP_PROXY_POOL_COUNT": str(settings.IP_PROXY_POOL_COUNT),
        "IP_PROXY_PROVIDER_NAME": str(settings.IP_PROXY_PROVIDER_NAME),
        "KDL_SECERT_ID": str(settings.KDL_SECERT_ID),
        "KDL_SIGNATURE": str(settings.KDL_SIGNATURE),
        "KDL_USER_NAME": str(settings.KDL_USER_NAME),
        "KDL_USER_PWD": str(settings.KDL_USER_PWD),
        # 基础配置 (base_config.py)
        "PLATFORM": str(settings.CRAWLER_PLATFORM),
        "KEYWORDS": str(settings.CRAWLER_KEYWORDS),
        "CRAWLER_TYPE": str(settings.CRAWLER_TYPE),
        "SORT_TYPE": str(settings.CRAWLER_SORT_TYPE),
        "PUBLISH_TIME_TYPE": str(settings.CRAWLER_PUBLISH_TIME_TYPE),
        # 数据保存配置 (base_config.py)
        "SAVE_DATA_OPTION": str(settings.CRAWLER_SAVE_DATA_OPTION),
        "ACCOUNT_POOL_SAVE_TYPE": str(settings.CRAWLER_ACCOUNT_POOL_SAVE_TYPE),
        # 爬取控制配置 (base_config.py)
        "START_PAGE": str(settings.CRAWLER_START_PAGE),
        "CRAWLER_MAX_NOTES_COUNT": str(settings.CRAWLER_MAX_NOTES_COUNT),
        "MAX_CONCURRENCY_NUM": str(settings.CRAWLER_MAX_CONCURRENCY_NUM),
        "CRAWLER_TIME_SLEEP": str(settings.CRAWLER_TIME_SLEEP),
        # 评论爬取配置 (base_config.py)
        "ENABLE_GET_COMMENTS": str(settings.CRAWLER_ENABLE_GET_COMMENTS),
        "ENABLE_GET_SUB_COMMENTS": str(settings.CRAWLER_ENABLE_GET_SUB_COMMENTS),
        "PER_NOTE_MAX_COMMENTS_COUNT": str(
            settings.CRAWLER_PER_NOTE_MAX_COMMENTS_COUNT
        ),
        # 断点续爬配置 (base_config.py)
        "ENABLE_CHECKPOINT": str(settings.CRAWLER_ENABLE_CHECKPOINT),
        "SPECIFIED_CHECKPOINT_ID": str(settings.CRAWLER_SPECIFIED_CHECKPOINT_ID),
        "CHECKPOINT_STORAGE_TYPE": str(settings.CRAWLER_CHECKPOINT_STORAGE_TYPE),
        # 其他配置 (base_config.py)
        "ENABLE_LOG_FILE": str(settings.CRAWLER_ENABLE_LOG_FILE),
        "ENABLE_WEIBO_FULL_TEXT": str(settings.CRAWLER_ENABLE_WEIBO_FULL_TEXT),
    }

    return env_config


def merge_task_config(task_params: Dict) -> Dict[str, str]:
    """
    合并任务参数到环境变量配置中

    允许每个任务使用不同的配置参数，覆盖默认配置

    Args:
        task_params: 任务参数字典，例如:
            {
                "platform": "xhs",
                "keywords": "AI,机器学习",
                "max_notes": 100,
                "enable_comments": True,
                "specified_id_list": ["id1", "id2"]
            }

    Returns:
        Dict[str, str]: 合并后的环境变量字典
    """
    # 先获取默认配置
    env_config = get_crawler_env_config()

    # 参数映射表：任务参数名 -> 环境变量名
    param_mapping = {
        "platform": "PLATFORM",
        "keywords": "KEYWORDS",
        "crawler_type": "CRAWLER_TYPE",
        "sort_type": "SORT_TYPE",
        "publish_time_type": "PUBLISH_TIME_TYPE",
        "save_data_option": "SAVE_DATA_OPTION",
        "start_page": "START_PAGE",
        "max_notes": "CRAWLER_MAX_NOTES_COUNT",
        "max_concurrency": "MAX_CONCURRENCY_NUM",
        "time_sleep": "CRAWLER_TIME_SLEEP",
        "enable_comments": "ENABLE_GET_COMMENTS",
        "enable_sub_comments": "ENABLE_GET_SUB_COMMENTS",
        "max_comments_per_note": "PER_NOTE_MAX_COMMENTS_COUNT",
        "enable_checkpoint": "ENABLE_CHECKPOINT",
        "checkpoint_id": "SPECIFIED_CHECKPOINT_ID",
        "hotspot_id": "HOTSPOT_ID",  # 热点ID参数映射
    }

    # 将任务参数映射到环境变量
    for task_key, env_key in param_mapping.items():
        if task_key in task_params:
            env_config[env_key] = str(task_params[task_key])

    # 小红书笔记URL列表
    if "xhs_note_url_list" in task_params and task_params["xhs_note_url_list"]:
        env_config["XHS_SPECIFIED_NOTE_URL_LIST"] = "||".join(
            task_params["xhs_note_url_list"]
        )

    # 小红书创作者URL列表
    if "xhs_creator_url_list" in task_params and task_params["xhs_creator_url_list"]:
        env_config["XHS_CREATOR_URL_LIST"] = "||".join(
            task_params["xhs_creator_url_list"]
        )

    # 微博指定ID列表
    if (
        "weibo_specified_id_list" in task_params
        and task_params["weibo_specified_id_list"]
    ):
        env_config["WEIBO_SPECIFIED_ID_LIST"] = ",".join(
            task_params["weibo_specified_id_list"]
        )

    # 微博创作者ID列表
    if "weibo_creator_id_list" in task_params and task_params["weibo_creator_id_list"]:
        env_config["WEIBO_CREATOR_ID_LIST"] = ",".join(
            task_params["weibo_creator_id_list"]
        )

    # 贴吧指定ID列表
    if (
        "tieba_specified_id_list" in task_params
        and task_params["tieba_specified_id_list"]
    ):
        env_config["TIEBA_SPECIFIED_ID_LIST"] = ",".join(
            task_params["tieba_specified_id_list"]
        )

    # 贴吧名称列表
    if "tieba_name_list" in task_params and task_params["tieba_name_list"]:
        env_config["TIEBA_NAME_LIST"] = ",".join(task_params["tieba_name_list"])

    # 贴吧创作者URL列表
    if (
        "tieba_creator_url_list" in task_params
        and task_params["tieba_creator_url_list"]
    ):
        env_config["TIEBA_CREATOR_URL_LIST"] = "||".join(
            task_params["tieba_creator_url_list"]
        )

    # B站创作者ID列表
    if "bili_creator_id_list" in task_params and task_params["bili_creator_id_list"]:
        env_config["BILI_CREATOR_ID_LIST"] = ",".join(
            task_params["bili_creator_id_list"]
        )

    # B站视频ID列表
    if (
        "bili_specified_id_list" in task_params
        and task_params["bili_specified_id_list"]
    ):
        env_config["BILI_SPECIFIED_ID_LIST"] = ",".join(
            task_params["bili_specified_id_list"]
        )

    # 抖音指定ID列表
    if "dy_specified_id_list" in task_params and task_params["dy_specified_id_list"]:
        env_config["DY_SPECIFIED_ID_LIST"] = ",".join(
            task_params["dy_specified_id_list"]
        )

    # 抖音创作者ID列表
    if "dy_creator_id_list" in task_params and task_params["dy_creator_id_list"]:
        env_config["DY_CREATOR_ID_LIST"] = ",".join(task_params["dy_creator_id_list"])

    # 快手指定ID列表
    if "ks_specified_id_list" in task_params and task_params["ks_specified_id_list"]:
        env_config["KS_SPECIFIED_ID_LIST"] = ",".join(
            task_params["ks_specified_id_list"]
        )

    # 快手创作者ID列表
    if "ks_creator_id_list" in task_params and task_params["ks_creator_id_list"]:
        env_config["KS_CREATOR_ID_LIST"] = ",".join(task_params["ks_creator_id_list"])

    # 知乎创作者URL列表
    if (
        "zhihu_creator_url_list" in task_params
        and task_params["zhihu_creator_url_list"]
    ):
        env_config["ZHIHU_CREATOR_URL_LIST"] = "||".join(
            task_params["zhihu_creator_url_list"]
        )

    # 知乎指定ID列表
    if (
        "zhihu_specified_id_list" in task_params
        and task_params["zhihu_specified_id_list"]
    ):
        env_config["ZHIHU_SPECIFIED_ID_LIST"] = "||".join(
            task_params["zhihu_specified_id_list"]
        )

    return env_config
