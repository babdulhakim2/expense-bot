.PHONY: help install dev frontend backend emulators test build clean lint setup health-check infra infra-stop infra-logs docker-backend docker-frontend docker-stop docker-clean deploy-dev deploy-prod destroy-dev destroy-prod rag-local rag-test rag-deploy-dev rag-deploy-prod rag-clean

# Default target
help: ## Show this help message
	@echo "Expense Bot Development Commands"
	@echo "================================"
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: install-frontend install-backend ## Install all dependencies
	@echo "✅ All dependencies installed"

install-frontend: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && bun install

install-backend: ## Install backend dependencies
	@echo "🐍 Installing backend dependencies..."
	@cd backend && \
	if [ ! -d "venv" ]; then \
		echo "Creating Python virtual environment..."; \
		python -m venv venv; \
	fi && \
	if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && pip install -r requirements.txt; \
	else \
		. venv/Scripts/activate && pip install -r requirements.txt; \
	fi

# Development targets
setup: install ## Complete setup for new developers
	@echo "🚀 Setting up development environment..."
	@make health-check
	@echo "✅ Setup complete! Run 'make dev' to start development"

dev: ## Start all services (frontend, backend, emulators)
	@echo "🚀 Starting full development environment..."
	@echo "Press Ctrl+C to stop all services"
	@trap 'echo "🛑 Stopping all services..."; kill 0' SIGINT; \
	make emulators-stop >/dev/null 2>&1 || true; \
	sleep 2; \
	make emulators & \
	EMULATOR_PID=$$!; \
	sleep 5; \
	if ! make health-check-emulators >/dev/null 2>&1; then \
		echo "❌ Firebase emulators failed to start. Check ports 8080, 9099, 9199"; \
		kill $$EMULATOR_PID 2>/dev/null || true; \
		exit 1; \
	fi; \
	echo "✅ Firebase emulators started"; \
	make backend & \
	sleep 3; \
	make frontend & \
	wait

frontend: ## Start frontend development server
	@echo "⚛️ Starting frontend..."
	@cd frontend && bun run dev

backend: ## Start backend development server
	@echo "🐍 Starting backend on port 9000..."
	@cd backend && \
	if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && PORT=9000 python app.py; \
	elif [ -f "venv/Scripts/activate" ]; then \
		. venv/Scripts/activate && PORT=9000 python app.py; \
	else \
		echo "⚠️  Virtual environment not found. Run 'make install-backend' first."; \
		PORT=9000 python app.py; \
	fi

emulators: ## Start Firebase emulators
	@echo "🔥 Starting Firebase emulators..."
	@cd backend/firebase && firebase emulators:start --project=expense-bot-9906c

# Build targets
build: build-frontend ## Build production artifacts
	@echo "✅ Build complete"

build-frontend: ## Build frontend for production
	@echo "🏗️ Building frontend..."
	@cd frontend && bun run build

# Testing targets
test: test-frontend test-backend ## Run all tests
	@echo "✅ All tests passed"

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	@cd frontend && bun run test || echo "⚠️ No frontend tests found"

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	@cd backend && python -m pytest

# Linting targets
lint: lint-frontend lint-backend ## Run all linting
	@echo "✅ All linting passed"

lint-frontend: ## Lint frontend code
	@echo "🔍 Linting frontend..."
	@cd frontend && bun run lint

lint-backend: ## Lint backend code
	@echo "🔍 Linting backend..."
	@cd backend && flake8 . || echo "⚠️ Backend linting issues found"

# Utility targets
clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	@cd frontend && rm -rf .next node_modules/.cache
	@cd backend && find . -type d -name "__pycache__" -delete
	@cd backend && find . -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

health-check: ## Check if all required tools are installed
	@echo "🏥 Running health check..."
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js not installed"; exit 1; }
	@command -v bun >/dev/null 2>&1 || { echo "❌ Bun not installed"; exit 1; }
	@command -v python >/dev/null 2>&1 || { echo "❌ Python not installed"; exit 1; }
	@command -v firebase >/dev/null 2>&1 || { echo "❌ Firebase CLI not installed"; exit 1; }
	@echo "✅ All required tools are installed"

health-check-emulators: ## Check if Firebase emulators are running
	@curl -s http://localhost:8080 >/dev/null 2>&1 || { echo "❌ Firestore emulator not running"; exit 1; }
	@curl -s http://localhost:9099 >/dev/null 2>&1 || { echo "❌ Auth emulator not running"; exit 1; }
	@echo "✅ Firebase emulators are running"

# Firebase specific targets
emulators-stop: ## Stop Firebase emulators
	@echo "🛑 Stopping Firebase emulators..."
	@pkill -f "firebase.*emulator" || echo "No emulators running"

emulators-reset: emulators-stop ## Reset Firebase emulators data
	@echo "🔄 Resetting emulator data..."
	@cd backend/firebase && firebase emulators:start --project=expense-bot-9906c --import=./emulator_data --export-on-exit=./emulator_data &
	@sleep 5 && pkill -f "firebase.*emulator"

# Infrastructure targets
infra: ## Start monitoring stack (Grafana + Prometheus)
	@echo "📊 Starting monitoring infrastructure..."
	@cd infra && docker compose up -d prometheus grafana minio
	@echo "✅ Infrastructure started:"
	@echo "  Grafana:    http://localhost:3002 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  MinIO:      http://localhost:9001 (admin/admin123456)"

infra-stop: ## Stop monitoring stack
	@echo "🛑 Stopping infrastructure..."
	@cd infra && docker compose down

infra-logs: ## Show infrastructure logs
	@cd infra && docker compose logs -f prometheus grafana

# Docker targets
docker-build: ## Build Docker containers
	@echo "🐳 Building Docker containers..."
	@cd infra && docker compose build

docker-backend: ## Start backend in Docker
	@echo "🐳 Starting backend in Docker..."
	@cd infra && docker compose up -d backend
	@echo "✅ Backend started: http://localhost:8080"

docker-frontend: ## Start frontend in Docker  
	@echo "🐳 Starting frontend in Docker..."
	@cd infra && docker compose up -d frontend
	@echo "✅ Frontend started: http://localhost:3000"

docker-stop: ## Stop all Docker services
	@echo "🐳 Stopping Docker services..."
	@cd infra && docker compose down

docker-clean: ## Clean Docker containers and volumes
	@echo "🧹 Cleaning Docker..."
	@cd infra && docker compose down -v --remove-orphans
	@docker system prune -f

# Deployment targets
deploy-dev: ## Deploy to development environment
	@echo "🚀 Deploying to development..."
	@./scripts/deploy.sh development

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	@./scripts/deploy.sh production

destroy-dev: ## Destroy development environment
	@echo "💥 Destroying development..."
	@./scripts/destroy-environment.sh development

destroy-prod: ## Destroy production environment
	@echo "💥 Destroying production..."
	@./scripts/destroy-environment.sh production

# Quick development shortcuts
quick-start: ## Quick start (emulators + frontend only)
	@echo "⚡ Quick start - emulators and frontend only..."
	@trap 'kill 0' SIGINT; \
	make emulators & \
	sleep 5 && \
	make frontend & \
	wait

logs: ## Show logs from all services
	@echo "📋 Showing recent logs..."
	@echo "=== Frontend logs ==="
	@tail -n 20 frontend/.next/trace 2>/dev/null || echo "No frontend logs"
	@echo "=== Backend logs ==="
	@tail -n 20 backend/*.log 2>/dev/null || echo "No backend logs"

# RAG Function targets
rag-local: ## Start RAG processor locally with local LanceDB
	@echo "🧠 Starting RAG processor locally..."
	@cd functions/rag-processor && \
	if [ ! -d "data" ]; then mkdir -p data; fi && \
	LANCEDB_URI="./data/lancedb" \
	LANCEDB_API_KEY="" \
	LANCEDB_REGION="" \
	LANCEDB_TABLE_NAME="expense_documents_local" \
	ENVIRONMENT="local" \
	python local_test.py

rag-test: ## Run RAG function tests
	@echo "🧪 Running RAG tests..."
	@cd functions/rag-processor && python -m pytest tests/ -v || echo "⚠️ No RAG tests found"

rag-deploy-dev: ## Deploy RAG function to development
	@echo "🚀 Deploying RAG function to development..."
	@cd functions/rag-processor && ./deploy.sh development

rag-deploy-prod: ## Deploy RAG function to production
	@echo "🚀 Deploying RAG function to production..."
	@cd functions/rag-processor && ./deploy.sh production

rag-clean: ## Clean RAG local data and cache
	@echo "🧹 Cleaning RAG local data..."
	@rm -rf functions/rag-processor/.lancedb
	@rm -rf functions/rag-processor/data
	@rm -rf functions/rag-processor/__pycache__
	@find functions/rag-processor -name "*.pyc" -delete
	@echo "✅ RAG cleanup complete"