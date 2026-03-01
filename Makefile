.PHONY: help dev up down build logs migrate seed test lint clean

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ===== Development =====

dev: ## Start all services in development mode
	docker compose up --build

up: ## Start all services (detached)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

build: ## Build all images
	docker compose build

logs: ## Tail logs
	docker compose logs -f

# ===== Database =====

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with initial data
	docker compose exec backend python -m scripts.seed_color_schemes

# ===== Testing =====

test: ## Run tests
	docker compose exec backend pytest -v

test-cov: ## Run tests with coverage
	docker compose exec backend pytest --cov=app --cov-report=html -v

# ===== Code Quality =====

lint: ## Run linter
	docker compose exec backend ruff check app/
	docker compose exec backend ruff format --check app/

format: ## Auto-format code
	docker compose exec backend ruff check --fix app/
	docker compose exec backend ruff format app/

# ===== Production =====

prod-up: ## Start production services
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down: ## Stop production services
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# ===== Utilities =====

shell: ## Open a shell in the backend container
	docker compose exec backend bash

dbshell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U afg_user -d academic_figure_generator

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all --remove-orphans
