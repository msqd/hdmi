# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hdmi** is a dependency injection framework for Python that manages dynamic dependencies with late (just-in-time)
resolution. The framework provides:

- Late-binding dependency resolution (instantiated only when needed)
- Type-annotation-based configuration using Python's standard typing system
- Scope-aware dependency validation (singleton, scoped, transient)
- Early error detection at build time (before runtime)

## Development Setup

This project uses **uv** for dependency management and **pytest** for testing.

### Common Commands

**Quick Testing (pytest only):**
```bash
# Run only pytest tests (no linting or type checking)
uv run pytest

# Run a single test file
uv run pytest tests/test_filename.py

# Run a specific test
uv run pytest tests/test_filename.py::test_function_name

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=hdmi --cov-report=html
```

**Full Quality Checks (recommended for commits):**
```bash
# Run all checks: linting, formatting, type checking, and tests
make test

# Run with verbose test output
make test TEST_VERBOSE=1

# Run with coverage report
make test TEST_COVERAGE=1

# Show all available make targets
make help
```

## Development Methodology

**This project strictly follows Test-Driven Development (TDD).**

All code must be developed using the Red-Green-Refactor cycle:

1. **Red**: Write a failing test that describes the desired behavior
2. **Green**: Write the minimum code necessary to make the test pass
3. **Refactor**: Improve the code structure while keeping tests green

**Key TDD Principles:**
- Never write production code without a failing test first
- Write only enough code to make the current test pass
- Tests define the specification and behavior of the system
- Each commit should include both tests and implementation

**Testing Guidelines:**
- Tests should be behavioral and describe what the code does, not how it does it
- Use descriptive test names that explain the expected behavior
- Keep tests focused on a single behavior
- **Tests directory structure MUST mirror the Python package structure**:
  - For `src/hdmi/module.py`, tests go in `tests/test_module.py`
  - For `src/hdmi/subpackage/module.py`, tests go in `tests/subpackage/test_module.py`
  - Maintain the same package hierarchy in tests as in src
  - This ensures tests are organized, discoverable, and maintainable

### Commit Guidelines

**ALWAYS run `make test` before committing** to ensure all quality checks pass (linting, type checking, and tests).

**Commit Message Best Practices:**
- Focus on **what changed and why** for the user, not implementation details
- Use conventional commits format: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- **NEVER mention tests passing or coverage** in commit messages
  - Tests passing is a prerequisite for all commits (enforced by `make test`)
  - This information adds no value to the commit history
- Keep messages concise and user-focused
- Example: `feat: add scope validation for dependency graph` (good)
- Example: `feat: add scope validation with tests passing at 95% coverage` (bad - unnecessary noise)

## Documentation

All features and architecture must be documented in the `docs/` directory using **Sphinx** and organized according to the **Diátaxis framework**.

### Diátaxis Framework

Documentation is organized into four categories:

1. **Tutorials** (`docs/tutorials/`): Learning-oriented guides that help newcomers learn by doing
   - Step-by-step instructions
   - Complete working examples
   - Assumes little prior knowledge

2. **How-To Guides** (`docs/how-to/`): Goal-oriented guides for solving specific problems
   - Focused on accomplishing specific tasks
   - Assumes basic knowledge
   - Practical and actionable

3. **Reference** (`docs/reference/`): Information-oriented technical descriptions
   - API documentation
   - Complete and accurate technical details
   - Generated from docstrings where appropriate

4. **Explanation** (`docs/explanation/`): Understanding-oriented discussions
   - Architecture and design decisions
   - Conceptual background
   - Why things are the way they are

### Documentation Commands

```bash
# Build documentation
make docs

# Build and watch for changes (auto-rebuild on file changes)
make docs-watch

# Clean all build artifacts (including docs)
make clean
```

## Architecture

**hdmi** follows a two-phase architecture: **ContainerBuilder → Container**

### Two-Phase Flow

1. **ContainerBuilder** (Configuration Phase)
   - Register service types and their dependencies
   - Define lifecycles (singleton, scoped, transient)
   - Configure using Python type annotations
   - Mutable: can add/modify service definitions

2. **Container** (Validation & Runtime Phase)
   - Built from ContainerBuilder via `.build()`
   - Validates the dependency graph (no cycles, all resolvable, scope-safe)
   - Checks type compatibility and scope hierarchies
   - Immutable: dependency graph is frozen
   - Used at runtime to resolve service instances via `.get(ServiceType)`
   - Services created lazily (just-in-time) when first requested

### Example Flow

```python
# Phase 1: Configuration
builder = ContainerBuilder()
builder.register(DatabaseConnection, scope="singleton")
builder.register(UserRepository, scope="scoped")     # can depend on singleton
builder.register(UserService, scope="transient")      # can depend on any scope

# Phase 2: Build & Runtime
container = builder.build()  # validates graph, no instantiation yet

# Service resolution (lazy instantiation)
user_service = container.get(UserService)  # creates all dependencies on-demand
```

### Core Concepts

1. **Type-Driven Dependencies**: Python type annotations define the dependency graph automatically

2. **Scope Hierarchy & Validation**: Services can only depend on services in the same or higher scope
   - **Singleton** (highest): One instance per container, lives for container lifetime
   - **Scoped** (middle): One instance per scope (e.g., per web request)
   - **Transient** (lowest): New instance every time it's requested

   Validation rules:
   - Singleton services can only depend on other singleton services
   - Scoped services can depend on singleton or scoped services
   - Transient services can depend on any scope

3. **Late Resolution**: Services instantiated just-in-time, not eagerly (see `docs/explanation/why-late-binding.rst`)

4. **Early Validation**: Configuration errors (cycles, missing deps, scope violations) caught at `.build()` time

5. **Immutable Containers**: Once built, the dependency graph cannot be modified

### Design Principles

- **Fail Fast, Run Lazy**: Validate early (scope violations, cycles), instantiate late
- **Type Annotations as Truth**: No separate configuration required
- **Scope Safety**: Compile-time prevention of scope-related lifetime bugs
- **Simplicity by Design**: Two core concepts (ContainerBuilder, Container), one clear workflow
- **No External DSL**: Pure Python, no YAML/XML required (unlike harp/rodi)
- **Minimal Overhead**: Lightweight and fast
