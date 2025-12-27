# MediaCrawlerPro-Python 配置集成指南

## 概述

本项目通过**环境变量**的方式，将 API 服务的配置传递给 MediaCrawlerPro-Python，实现了配置的统一管理，**无需修改 MediaCrawlerPro-Python 项目本身的任何代码**。

## 核心原理

MediaCrawlerPro-Python 的配置文件都使用 `os.getenv()` 读取环境变量，例如：

```python
# MediaCrawlerPro-Python/config/db_config.py
RELATION_DB_HOST = os.getenv("RELATION_DB_HOST", "localhost")
RELATION_DB_PWD = os.getenv("RELATION_DB_PWD", "123456")

# MediaCrawlerPro-Python/config/proxy_config.py
ENABLE_IP_PROXY = os.getenv("ENABLE_IP_PROXY", False)
```

我们利用这个特性，在 Celery 任务执行时设置环境变量，让 MediaCrawlerPro-Python 使用 API 服务的配置。

## 实现方案

### 1. 配置文件扩展

在 [app/config.py](app/config.py) 中添加了所有 MediaCrawlerPro-Python 需要的配置项：

```python
class Settings(BaseSettings):
    # 数据库配置
    RELATION_DB_HOST: str = "localhost"
    RELATION_DB_PORT: int = 3307

    # 爬虫配置
    CRAWLER_PLATFORM: str = "xhs"
    CRAWLER_KEYWORDS: str = "deepseek,chatgpt"
    CRAWLER_MAX_NOTES_COUNT: int = 40
    # ... 更多配置
```

### 2. 配置转换工具

创建了 [app/utils/crawler_config.py](app/utils/crawler_config.py) 配置转换工具：

- `get_crawler_env_config()`: 将 API 配置转换为环境变量字典
- `merge_task_config()`: 合并任务参数，支持每个任务使用不同配置

### 3. Celery 任务集成

在 [app/celery_app/tasks/crawler_tasks.py](app/celery_app/tasks/crawler_tasks.py) 中：

```python
from app.utils.crawler_config import merge_task_config

def run_crawler(self, platform, keywords, ...):
    # 构建任务参数
    task_params = {
        "platform": platform,
        "keywords": keywords,
        "max_notes": max_notes_count,
        # ...
    }

    # 获取环境变量配置
    env_config = merge_task_config(task_params)

    # 设置环境变量
    env = os.environ.copy()
    env.update(env_config)

    # 执行爬虫（会使用我们设置的环境变量）
    subprocess.Popen(cmd, env=env, ...)
```

### 4. 数据库初始化

在 [app/db/session.py](app/db/session.py) 中添加了表结构初始化逻辑：

- 自动读取 `MediaCrawlerPro-Python/schema/tables.sql`
- 在首次启动时自动创建所有表结构
- 如果表已存在则跳过初始化

## 配置说明

### 环境变量配置

所有配置都可以通过 `.env` 文件设置，参考 [.env.example](.env.example)：

```bash
# 数据库配置
RELATION_DB_HOST=localhost
RELATION_DB_PORT=3307
RELATION_DB_NAME=media_crawler_pro

# 爬虫配置
CRAWLER_PLATFORM=xhs
CRAWLER_KEYWORDS=deepseek,chatgpt
CRAWLER_MAX_NOTES_COUNT=40
CRAWLER_ENABLE_GET_COMMENTS=True
# ... 更多配置
```

### API 调用时动态配置

调用 API 接口时，可以动态覆盖默认配置：

```bash
POST /api/v1/tasks/create
{
  "platform": "xhs",
  "keywords": "AI,机器学习",  # 覆盖默认关键词
  "max_notes": 100,           # 覆盖默认数量
  "enable_comments": true
}
```

## 配置映射表

| API 配置项 | 环境变量名 | MediaCrawlerPro-Python 配置文件 |
|-----------|-----------|--------------------------------|
| `RELATION_DB_HOST` | `RELATION_DB_HOST` | `config/db_config.py` |
| `SIGN_SRV_HOST` | `SIGN_SRV_HOST` | `config/sign_srv_config.py` |
| `ENABLE_IP_PROXY` | `ENABLE_IP_PROXY` | `config/proxy_config.py` |
| `CRAWLER_PLATFORM` | `PLATFORM` | `config/base_config.py` |
| `CRAWLER_KEYWORDS` | `KEYWORDS` | `config/base_config.py` |
| `CRAWLER_MAX_NOTES_COUNT` | `CRAWLER_MAX_NOTES_COUNT` | `config/base_config.py` |
| ... | ... | ... |

完整映射关系请查看 [app/utils/crawler_config.py](app/utils/crawler_config.py)

## 优势

1. **无需修改 MediaCrawlerPro-Python 代码**: 完全通过环境变量控制
2. **统一配置管理**: 所有配置在 API 服务中集中管理
3. **灵活的配置覆盖**: 支持全局配置 + 任务级别配置
4. **自动数据库初始化**: 首次启动自动创建表结构
5. **配置隔离**: 不同任务可以使用不同配置

## 使用示例

### 1. 修改全局配置

编辑 `.env` 文件：

```bash
# 修改默认平台为微博
CRAWLER_PLATFORM=weibo

# 修改默认关键词
CRAWLER_KEYWORDS=热搜,新闻

# 修改爬取数量
CRAWLER_MAX_NOTES_COUNT=100
```

### 2. 创建任务时覆盖配置

```python
# 使用默认配置
POST /api/v1/tasks/create
{
  "platform": "xhs",
  "keywords": "AI"
}

# 覆盖部分配置
POST /api/v1/tasks/create
{
  "platform": "weibo",
  "keywords": "科技新闻",
  "max_notes": 200,           # 覆盖默认的 40
  "enable_comments": false,   # 覆盖默认的 true
  "time_sleep": 2            # 增加请求间隔
}
```

## 注意事项

1. 修改 `.env` 文件后需要重启 API 服务才能生效
2. MediaCrawlerPro-Python 必须在 `CRAWLER_BASE_PATH` 指定的路径下
3. 数据库和 Redis 必须正确配置并可访问
4. 首次启动会自动创建数据库表，确保数据库已创建

## 目录结构

```
trend-api-server/
├── app/
│   ├── config.py                          # 统一配置文件（包含爬虫配置）
│   ├── utils/
│   │   └── crawler_config.py             # 配置转换工具
│   ├── db/
│   │   └── session.py                    # 数据库初始化（含表结构）
│   └── celery_app/
│       └── tasks/
│           └── crawler_tasks.py          # Celery 任务（使用环境变量）
├── MediaCrawlerPro-Python/               # 不需要修改
│   ├── config/
│   │   ├── base_config.py               # 从环境变量读取
│   │   ├── db_config.py                 # 从环境变量读取
│   │   ├── proxy_config.py              # 从环境变量读取
│   │   └── sign_srv_config.py           # 从环境变量读取
│   └── schema/
│       └── tables.sql                    # 表结构（API 启动时自动执行）
├── .env                                   # 实际配置（不提交到 git）
├── .env.example                           # 配置模板
└── CRAWLER_CONFIG_GUIDE.md               # 本文档
```

## 总结

通过这个方案，我们实现了：

- ✅ **不修改 MediaCrawlerPro-Python 代码**
- ✅ **统一配置管理**
- ✅ **自动数据库初始化**
- ✅ **灵活的配置覆盖**
- ✅ **方便的外部接口调用**

所有配置都通过 API 服务的 `.env` 文件或 API 接口参数控制，实现了配置的集中管理和动态调整。
