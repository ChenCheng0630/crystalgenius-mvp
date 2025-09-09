# CrystalGenius MVP - Development Commands

.PHONY: help build up down logs clean dev-backend dev-frontend test lint check-docker

# Check if Docker Compose is available
DOCKER_COMPOSE_CMD := $(shell command -v docker-compose 2> /dev/null)
ifdef DOCKER_COMPOSE_CMD
    COMPOSE_CMD = docker-compose
else
    COMPOSE_CMD = docker compose
endif

# Default target
help:
	@echo "CrystalGenius MVP Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Docker Commands:"
	@echo "  build         Build all Docker images"
	@echo "  test-build    Test individual builds"
	@echo "  docker-cleanup Clean up Docker cache and unused resources"
	@echo "  up            Start all services"
	@echo "  down          Stop all services"
	@echo "  logs          View service logs"
	@echo "  clean         Clean up containers and images"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev-backend   Start backend in development mode"
	@echo "  dev-frontend  Start frontend in development mode"
	@echo "  dev           Start both backend and frontend in development mode"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test      Run all tests"
	@echo "  lint      Run linting checks"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup     Initial project setup"
	@echo "  env       Create environment files from examples"

# Docker commands
check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Please install Docker first."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "❌ Docker is not running. Please start Docker."; exit 1; }
	@echo "✅ Docker is ready"

build: check-docker
	$(COMPOSE_CMD) build

test-build:
	@chmod +x scripts/test-build.sh
	@./scripts/test-build.sh

docker-cleanup:
	@chmod +x scripts/docker-cleanup.sh
	@./scripts/docker-cleanup.sh

up: check-docker
	$(COMPOSE_CMD) up -d

down: check-docker
	$(COMPOSE_CMD) down

logs: check-docker
	$(COMPOSE_CMD) logs -f

clean: check-docker
	$(COMPOSE_CMD) down -v --rmi all --remove-orphans
	docker system prune -f

# Development commands
dev-backend:
	@echo "Starting backend in development mode..."
	cd backend && python run.py

dev-frontend:
	@echo "Starting frontend in development mode..."
	cd frontend && npm start

dev:
	@echo "Starting both services in development mode..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo ""
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

# Testing and quality
test:
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

lint:
	@echo "Running backend linting..."
	cd backend && black . && isort . && mypy .
	@echo "Running frontend linting..."
	cd frontend && npm run lint

# Setup commands
setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

env:
	@if [ ! -f backend/.env ]; then \
		echo "Creating backend/.env from example..."; \
		cp backend/.env.example backend/.env 2>/dev/null || \
		echo "# OpenAI Configuration\nOPENAI_API_KEY=your_openai_api_key_here\nOPENAI_MODEL=gpt-4o-mini\n\n# Feature Flags\nENABLE_LLM_CHAT=true\nENABLE_LLM_FILTERS=true" > backend/.env; \
	else \
		echo "backend/.env already exists"; \
	fi

# Quick commands
start: up
stop: down
restart: down up
status: check-docker
	$(COMPOSE_CMD) ps

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"
	@curl -f http://localhost:3000/health 2>/dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"
