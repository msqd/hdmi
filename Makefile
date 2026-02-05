.PHONY: test install install-dev check docs docs-watch clean wheel help

UV ?= $(shell command -v uv 2>/dev/null || echo "uv")
RUN ?= $(UV) run
TEST_VERBOSE ?=
TEST_COVERAGE ?=

# helpers
define execute
@echo "⚙️ \033[36m$@\033[0m: \033[2m$(1)\033[0m"
@$(1)
endef

help:  ## Show available commands
	@echo "Available commands:"
	@echo
	@echo "\033[1mDevelopment\033[0m"
	@grep -E '^(install|install-dev):.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "    make \033[36m%-20s\033[0m %s\n", $$1, $$2}'
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

install:  ## Install dependencies (without dev tools)
	$(call execute,$(UV) sync)

install-dev:  ## Install dependencies with dev tools
	$(call execute,$(UV) sync --extra dev)

check: install-dev  ## Check and fix code with ruff (lint + format)
	$(call execute,$(RUN) ruff check --fix .)
	$(call execute,$(RUN) ruff format .)
	$(call execute,$(RUN) basedpyright)

test: install-dev check  ## Run all tests
	$(call execute,$(RUN) pytest $(if $(TEST_VERBOSE),--verbose,) $(if $(TEST_COVERAGE),--cov=hdmi --cov-report=html --cov-report=term,))

docs: install-dev  ## Build documentation with Sphinx
	$(call execute,$(RUN) sphinx-build -b html docs docs/_build/html)

docs-watch: install-dev  ## Build documentation and watch for changes
	$(call execute,$(RUN) sphinx-autobuild docs docs/_build/html --watch src)

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
	$(call execute,$(UV) build)
	$(call execute,$(RUN) twine check dist/*)
	@echo ""
	@echo "Wheel built and validated successfully!"
	@echo "Files ready for upload:"
	@ls -lh dist/
