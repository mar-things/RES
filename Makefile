SHELL := /bin/bash

.DEFAULT_GOAL := help

run: ## xvfb-run -a uv run python main.py
	uv run python main.py
	

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

setup: ## Install deps (uv)
	uv sync --dev

lint: ## Lint (ruff)
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-format
	uv run ruff format .

typecheck: ## Typecheck (mypy)
	uv run mypy .

test: ## Tests
	uv run pytest

test-ui: ## Headless UI tests
	xvfb-run -a uv run pytest

package: ## Build app (PyInstaller)
	uv run pyinstaller --noconfirm --clean scripts/pyinstaller.spec || true