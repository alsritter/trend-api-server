.PHONY: help init build build-signsrv up down restart logs clean shell db-init test install

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
DOCKER_COMPOSE = docker-compose
DOCKER = docker
PYTHON = python3
UV = uv

# 项目名称和镜像名称
PROJECT_NAME = trend-api-server
SIGNSRV_IMAGE = mediacrawler_signsrv:latest
API_IMAGE = trend-api-server:latest

# 颜色输出
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

##@ 帮助

help: ## 显示帮助信息
	@echo ''
	@echo '使用方式:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2 } /^##@/ { printf "\n${WHITE}%s${RESET}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 环境初始化

init: ## 快速初始化项目环境（Git 子模块 + 配置文件 + Python 依赖）
	@echo "${GREEN}开始初始化项目环境...${RESET}"
	@echo "${YELLOW}1. 初始化 Git 子模块...${RESET}"
	git submodule update --init --recursive
	@echo "${YELLOW}2. 复制环境配置文件...${RESET}"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${GREEN}已创建 .env 文件，请根据需要修改配置${RESET}"; \
	else \
		echo "${YELLOW}.env 文件已存在，跳过${RESET}"; \
	fi
	@echo "${YELLOW}3. 创建必要的目录...${RESET}"
	mkdir -p logs
	@echo "${GREEN}环境初始化完成！${RESET}"
	@echo "${YELLOW}提示: 请检查 .env 文件中的配置是否正确${RESET}"

install: ## 安装本地开发 Python 依赖（包含主项目和所有子项目）
	@echo "${GREEN}安装 Python 依赖（主项目 + 子项目）...${RESET}"
	@echo "${YELLOW}1. 同步主项目依赖...${RESET}"
	$(UV) sync
	@echo "${GREEN}✓ 主项目依赖安装完成${RESET}"
	@echo "${YELLOW}2. 将 MediaCrawlerPro-Python 依赖安装到主虚拟环境...${RESET}"
	@if [ -d "MediaCrawlerPro-Python" ] && [ -f "MediaCrawlerPro-Python/pyproject.toml" ]; then \
		cd MediaCrawlerPro-Python && \
		$(UV) export --no-hashes | tail -n +2 > /tmp/mcp_reqs.txt && \
		cd .. && \
		$(UV) pip install -r /tmp/mcp_reqs.txt && \
		rm /tmp/mcp_reqs.txt && \
		echo "${GREEN}✓ MediaCrawlerPro-Python 依赖已安装${RESET}"; \
	else \
		echo "${YELLOW}! MediaCrawlerPro-Python 目录不存在，跳过${RESET}"; \
	fi
	@echo "${YELLOW}3. 将 MediaCrawlerPro-SignSrv 依赖安装到主虚拟环境...${RESET}"
	@if [ -d "MediaCrawlerPro-SignSrv" ] && [ -f "MediaCrawlerPro-SignSrv/pyproject.toml" ]; then \
		cd MediaCrawlerPro-SignSrv && \
		$(UV) export --no-hashes | tail -n +2 > /tmp/signsrv_reqs.txt && \
		cd .. && \
		$(UV) pip install -r /tmp/signsrv_reqs.txt && \
		rm /tmp/signsrv_reqs.txt && \
		echo "${GREEN}✓ MediaCrawlerPro-SignSrv 依赖已安装${RESET}"; \
	else \
		echo "${YELLOW}! MediaCrawlerPro-SignSrv 目录不存在，跳过${RESET}"; \
	fi
	@echo "${GREEN}所有依赖安装完成！${RESET}"
	@echo "${YELLOW}提示: uv 已创建虚拟环境，使用 'source .venv/bin/activate' 激活${RESET}"


add: ## 添加新依赖包 (使用方法: make add PACKAGE=package_name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "${YELLOW}使用方法: make add PACKAGE=package_name${RESET}"; \
		exit 1; \
	fi
	@echo "${GREEN}添加依赖: $(PACKAGE)${RESET}"
	$(UV) add $(PACKAGE)

run: ## 在虚拟环境中运行 Python 命令 (使用方法: make run CMD="python script.py")
	@if [ -z "$(CMD)" ]; then \
		echo "${YELLOW}使用方法: make run CMD=\"your command\"${RESET}"; \
		exit 1; \
	fi
	$(UV) run $(CMD)

shell-venv: ## 激活虚拟环境的提示
	@echo "${YELLOW}激活虚拟环境:${RESET}"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "${YELLOW}或使用 uv run 直接运行命令:${RESET}"
	@echo "  uv run python your_script.py"

##@ Docker 镜像管理

build: ## 构建 Docker 镜像（包含 API Server + Celery Worker + SignSrv）
	@echo "${GREEN}构建 Docker 镜像（包含 API Server + Celery Worker + SignSrv）...${RESET}"
	$(DOCKER) build -t $(API_IMAGE) .
	@echo "${GREEN}镜像构建完成: $(API_IMAGE)${RESET}"

##@ 本地开发和测试

up: ## 启动所有服务（后台运行）
	@echo "${GREEN}启动所有服务...${RESET}"
	$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}服务已启动！${RESET}"
	@echo "${YELLOW}API Server: http://localhost:8000${RESET}"
	@echo "${YELLOW}API Docs: http://localhost:8000/docs${RESET}"
	@echo "${YELLOW}SignSrv: http://localhost:8989${RESET}"

up-build: ## 重新构建并启动所有服务
	@echo "${GREEN}重新构建并启动所有服务...${RESET}"
	$(DOCKER_COMPOSE) up -d --build
	@echo "${GREEN}服务已启动！${RESET}"

down: ## 停止所有服务
	@echo "${YELLOW}停止所有服务...${RESET}"
	$(DOCKER_COMPOSE) down
	@echo "${GREEN}服务已停止${RESET}"

restart: down up ## 重启所有服务

##@ 日志和监控

logs: ## 查看所有服务日志
	$(DOCKER_COMPOSE) logs -f

logs-api: ## 查看 API Server 日志
	$(DOCKER_COMPOSE) logs -f trend-api-server

logs-db: ## 查看 MySQL 日志
	$(DOCKER_COMPOSE) logs -f db

logs-redis: ## 查看 Redis 日志
	$(DOCKER_COMPOSE) logs -f redis

ps: ## 查看服务状态
	$(DOCKER_COMPOSE) ps

##@ 数据库管理

db-init: ## 初始化数据库（仅在首次运行时需要）
	@echo "${GREEN}等待数据库启动...${RESET}"
	@sleep 5
	@echo "${GREEN}数据库已就绪${RESET}"

db-shell: ## 进入 MySQL 数据库 Shell
	$(DOCKER_COMPOSE) exec db mysql -uroot -p123456 media_crawler_pro

##@ 容器操作

shell: ## 进入 API Server 容器 Shell
	$(DOCKER_COMPOSE) exec trend-api-server /bin/bash

shell-db: ## 进入 MySQL 容器 Shell
	$(DOCKER_COMPOSE) exec db /bin/bash

shell-redis: ## 进入 Redis 容器 Shell
	$(DOCKER_COMPOSE) exec redis /bin/sh

##@ 清理

clean: ## 清理临时文件和缓存
	@echo "${YELLOW}清理临时文件...${RESET}"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "${GREEN}清理完成${RESET}"

clean-all: down ## 停止服务并清理所有 Docker 资源（容器、镜像、数据卷）
	@echo "${YELLOW}警告: 这将删除所有数据卷中的数据！${RESET}"
	@read -p "确定要继续吗? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "${YELLOW}清理 Docker 资源...${RESET}"; \
		$(DOCKER_COMPOSE) down -v --remove-orphans; \
		$(DOCKER) rmi $(API_IMAGE) 2>/dev/null || true; \
		echo "${GREEN}清理完成${RESET}"; \
	else \
		echo "${GREEN}已取消${RESET}"; \
	fi

##@ 开发测试

dev: ## 本地开发模式启动（不使用 Docker）
	@echo "${GREEN}启动本地开发服务器...${RESET}"
	@echo "${YELLOW}注意: 请确保 MySQL、Redis 和 SignSrv 服务已启动${RESET}"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## 运行测试
	@echo "${GREEN}运行测试...${RESET}"
	$(PYTHON) -m pytest tests/ -v

##@ 快速启动

quick-start: init up-build db-init ## 一键快速启动（初始化 + 构建 + 启动）
	@echo "${GREEN}========================================${RESET}"
	@echo "${GREEN}🎉 项目启动完成！${RESET}"
	@echo "${GREEN}========================================${RESET}"
	@echo "${YELLOW}API Server: http://localhost:8000${RESET}"
	@echo "${YELLOW}API Docs: http://localhost:8000/docs${RESET}"
	@echo "${YELLOW}SignSrv: http://localhost:8989${RESET}"
	@echo ""
	@echo "${YELLOW}常用命令:${RESET}"
	@echo "  make logs      - 查看日志"
	@echo "  make ps        - 查看服务状态"
	@echo "  make shell     - 进入容器"
	@echo "  make down      - 停止服务"
	@echo "  make help      - 查看所有命令"
