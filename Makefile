.PHONY: test install check docs docs-watch clean wheel help

UV ?= $(shell command -v uv 2>/dev/null || echo "uv")
RUN ?= $(UV) run
TEST_VERBOSE ?=
TEST_COVERAGE ?=

DEV ?= 1

help:  ## Show available commands
	@echo "Available commands:"
	@echo
	@echo "\033[1mDevelopment\033[0m"
	@grep -E '^(install):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "\033[1mTesting & Quality\033[0m"
	@grep -E '^(test|check):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "\033[1mDocumentation\033[0m"
	@grep -E '^(docs|docs-watch):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "\033[1mBuild\033[0m"
	@grep -E '^(wheel):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "\033[1mCleanup\033[0m"
	@grep -E '^(clean):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo

install:  ## Install dependencies (use DEV=0 for production only)
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

wheel: test clean  ## Build and check wheel for PyPI distribution
	$(UV) build
	$(RUN) twine check dist/*
	@echo ""
	@echo "Wheel built and validated successfully!"
	@echo "Files ready for upload:"
	@ls -lh dist/
