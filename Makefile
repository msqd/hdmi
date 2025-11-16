.PHONY: test install check docs docs-watch clean help

UV ?= $(shell command -v uv 2>/dev/null || echo "uv")
RUN ?= $(UV) run
TEST_VERBOSE ?=
TEST_COVERAGE ?=

DEV ?= 1

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:
	$(UV) pip install -e $(if $(DEV),.[dev],.)

check: install  ## Check and fix code with ruff (lint + format)
	$(RUN) ruff check --fix .
	$(RUN) ruff format .
	$(RUN) basedpyright

test: install check  ## Run all tests
	$(RUN) pytest $(if $(TEST_VERBOSE),--verbose,) $(if $(TEST_COVERAGE),--cov=hdmi --cov-report=html --cov-report=term,)

docs: install  ## Build documentation with Sphinx
	$(RUN) sphinx-build -b html docs docs/_build/html

docs-watch: install  ## Build documentation and watch for changes
	$(RUN) sphinx-autobuild docs docs/_build/html --watch src

clean:  ## Clean up temporary files
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf docs/_build
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
