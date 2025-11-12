.PHONY: test test-verbose test-cov docs docs-watch docs-clean clean help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

test:  ## Run all tests
	uv run pytest

test-verbose:  ## Run tests with verbose output
	uv run pytest -v

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=hdmi --cov-report=html --cov-report=term

docs:  ## Build documentation with Sphinx
	uv run sphinx-build -b html docs docs/_build/html

docs-watch:  ## Build documentation and watch for changes
	uv run sphinx-autobuild docs docs/_build/html --watch src

docs-clean:  ## Clean documentation build
	rm -rf docs/_build

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
