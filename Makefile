.PHONY: install dev test lint format clean run-server run-web docker-build docker-up

# 安装依赖
install:
	pip install -r requirements.txt
	cd web && npm install

# 开发模式运行
dev:
	make -j 2 run-server run-web

# 运行服务端
run-server:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行Web端
run-web:
	cd web && npm run dev

# 运行测试
test:
	pytest tests/ -v

# 代码检查
lint:
	flake8 app/ --max-line-length=100
	black --check app/
	mypy app/

# 代码格式化
format:
	black app/
	cd web && npm run lint

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info

# 初始化数据目录
init-data:
	mkdir -p data/chroma

# Docker构建
docker-build:
	docker-compose build

# Docker启动
docker-up:
	docker-compose up -d

# Docker停止
docker-down:
	docker-compose down

# 帮助
help:
	@echo "GustoBot - 开发命令"
	@echo ""
	@echo "make install       - 安装所有依赖"
	@echo "make dev           - 开发模式（同时运行服务端和Web端）"
	@echo "make run-server    - 运行服务端"
	@echo "make run-web       - 运行Web端"
	@echo "make test          - 运行测试"
	@echo "make lint          - 代码检查"
	@echo "make format        - 代码格式化"
	@echo "make clean         - 清理临时文件"
	@echo "make docker-build  - Docker构建"
	@echo "make docker-up     - Docker启动"
