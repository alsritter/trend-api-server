# Project Context

## Purpose
Trend API Server is an HTTP API service that wraps MediaCrawlerPro-Python crawler, providing asynchronous task scheduling, account management, content query, and hotspot detection for multi-platform social media data collection. The system supports crawling from major Chinese social media platforms (Xiaohongshu, Douyin, Kuaishou, Bilibili, Weibo, Baidu Tieba, Zhihu).

## Tech Stack

### Backend
- **Web Framework**: FastAPI 0.109.0
- **Async Task Queue**: Celery 5.3.4 + Redis 4.6.0
- **Database**: MySQL 8.0 (shared with MediaCrawlerPro-Python)
- **ORM**: aiomysql 0.2.0, pymysql 1.1.0
- **Process Management**: Supervisor
- **Containerization**: Docker + Docker Compose
- **Python Version**: >=3.11
- **Dependency Manager**: uv (Astral)

### Frontend
- **Framework**: React 18 + TypeScript
- **UI Library**: Ant Design 5.x
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query) + Zustand
- **HTTP Client**: Axios
- **Charts**: ECharts
- **Build Tool**: Vite

### External Dependencies
- **MediaCrawlerPro-Python** (git submodule) - Core crawler logic
- **MediaCrawlerPro-SignSrv** (git submodule) - Signature service for API requests

## Project Conventions

### Code Style
- **Python**: Follow PEP 8 conventions
  - Use kebab-case for module/package names (e.g., `celery_app`, `crawler_tasks`)
  - Use PascalCase for class names (e.g., `TaskCreate`, `HotspotService`)
  - Use snake_case for functions/variables (e.g., `create_task`, `max_notes_count`)
  - Type hints required for function signatures
- **TypeScript/React**: Follow React best practices
  - Use PascalCase for components (e.g., `Dashboard`, `AccountManagement`)
  - Use camelCase for functions/variables
  - Prefer functional components with hooks
- **API Naming**: RESTful conventions
  - Use plural nouns for collections (e.g., `/api/v1/tasks`, `/api/v1/accounts`)
  - Use kebab-case for multi-word endpoints

### Architecture Patterns
- **API Layer**: FastAPI router-based modular design under `app/api/v1/`
- **Task Queue**: Celery workers for long-running crawler tasks, separate queues for crawler_queue and control_queue
- **Database Access**: Direct SQL queries using aiomysql, no ORM abstraction
- **Configuration**: Environment variables via python-dotenv, centralized in `app/config.py`
- **Frontend**: Component-based architecture with page/component separation
- **Static Files**: Frontend build artifacts served from `static/web/` directory
- **Submodules**: Core crawler logic isolated in MediaCrawlerPro-Python submodule

### Testing Strategy
- Manual testing via Web UI and Swagger/ReDoc documentation
- No automated test suite currently implemented

### Git Workflow
- **Main Branch**: `main` (default branch)
- **Commit Style**: Descriptive imperative mood (e.g., "feat: Add proxy agent support", "fix: Update hotspot filtering logic")
- **Submodules**: Use `git submodule update --remote --merge` to update dependencies

## Domain Context

### Social Media Platforms
The system supports crawling from 7 major Chinese platforms:
- **xhs** (小红书/Xiaohongshu): Notes, comments, creators
- **dy** (抖音/Douyin): Videos, comments, creators
- **ks** (快手/Kuaishou): Videos, comments, creators
- **bili** (哔哩哔哩/Bilibili): Videos, comments, creators
- **wb** (微博/Weibo): Posts, comments, creators
- **tieba** (百度贴吧/Baidu Tieba): Posts, comments
- **zhihu** (知乎/Zhihu): Articles, answers, comments

### Crawler Types
- **search**: Keyword-based content search
- **detail**: Single content detail fetch
- **creator**: Creator profile and content fetch
- **homefeed**: Platform homepage/feed crawl

### Task Management
- Tasks are created via API, executed asynchronously via Celery workers
- Each task has a unique `task_id` (UUID format)
- Task states: PENDING, STARTED, SUCCESS, FAILURE, REVOKED
- Tasks can be stopped mid-execution via control queue

### Hotspot Detection
- **Hotspots**: Clusters of similar content identified by keyword similarity
- **Hotspot Service**: Analyzes crawled content to identify trending topics
- **Clustering**: Groups content by keywords, calculates hotspot scores
- **Word Cover**: Tracks keyword coverage within clusters

## Important Constraints
- **Shared Database**: Must maintain compatibility with MediaCrawlerPro-Python schema
- **Crawler Execution**: All crawler logic runs in submodule, API server only orchestrates
- **Account Cookies**: Platform authentication requires valid cookies stored per account
- **Rate Limiting**: Each platform has different rate limits and anti-bot measures
- **Signature Service**: Some platforms require signature generation via SignSrv
- **Python Version**: Requires Python 3.11+ for optimal performance
- **Redis**: Required for Celery task queue and result backend

## External Dependencies
- **MySQL 8.0**: Shared database on port 3307
- **Redis**: Task queue backend on port 6378
- **MediaCrawlerPro-SignSrv**: Signature service on port 8989
- **MediaCrawlerPro-Python**: Core crawler submodule in `/MediaCrawlerPro-Python`
