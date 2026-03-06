.PHONY: help dev lint lint-fix migrate setup

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial project setup (install deps, copy env, migrate, create superuser, load fixtures)
	uv sync
	@test -f .env || cp .env.example .env && echo "Created .env from .env.example"
	uv run ./manage.py makemigrations
	uv run ./manage.py migrate
	uv run ./manage.py createcachetable
	DJANGO_SUPERUSER_USERNAME=admin \
	DJANGO_SUPERUSER_EMAIL=admin@example.com \
	DJANGO_SUPERUSER_PASSWORD=admin \
	uv run ./manage.py createsuperuser --noinput
	uv run python portal/fixtures/generate.py > portal/fixtures/data.json
	uv run ./manage.py loaddata portal/fixtures/data.json
	@echo "Setup complete! Run 'make dev' to start the development server."

dev: ## Start the development server
	uv run ./manage.py runserver

lint: ## Run linter checks
	uv run ruff check .
	uv run ruff format --check .

lint-fix: ## Auto-fix lint issues
	uv run ruff check --fix .
	uv run ruff format .

migrate: ## Create and run migrations
	uv run ./manage.py makemigrations
	uv run ./manage.py migrate

