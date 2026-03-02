
SHELL := /bin/bash

PY := python
VENV := .venv

# If your project uses Poetry, set USE_POETRY=1
USE_POETRY ?= 0

# If your project uses uv + pyproject, set USE_UV=1 (default)
USE_UV ?= 1

.DEFAULT_GOAL := help

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv + install deps
	@if [ ! -d "$(VENV)" ]; then $(PY) -m venv $(VENV); fi
	@source $(VENV)/bin/activate; \
		pip install -U pip; \
		if [ "$(USE_POETRY)" = "1" ] && [ -f pyproject.toml ]; then \
			pip install -U poetry; poetry install; \
		elif [ "$(USE_UV)" = "1" ] && [ -f pyproject.toml ]; then \
			uv pip install -e ".[dev]" || uv pip install -e .; \
		elif [ -f requirements.txt ]; then \
			pip install -r requirements.txt; \
			[ -f requirements-dev.txt ] && pip install -r requirements-dev.txt || true; \
		else \
			echo "No pyproject.toml or requirements.txt found. Add one, then rerun make setup."; \
		fi

lint: ## Run ruff
	@source $(VENV)/bin/activate; ruff check . && ruff format --check .

format: ## Auto-format with ruff
	@source $(VENV)/bin/activate; ruff format .

typecheck: ## Run mypy (best-effort)
	@source $(VENV)/bin/activate; mypy . || true

test: ## Run tests
	@source $(VENV)/bin/activate; pytest -q

test-ui: ## Run UI tests with xvfb (headless)
	@source $(VENV)/bin/activate; xvfb-run -a pytest -q

package: ## Build distributable (PyInstaller) - adjust entrypoint if needed
	@source $(VENV)/bin/activate; \
		if command -v pyinstaller >/dev/null 2>&1; then \
			pyinstaller --noconfirm --clean scripts/pyinstaller.spec || true; \
		else \
			echo "PyInstaller not installed. Add it to your dev deps, then rerun."; \
		fi
