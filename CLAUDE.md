# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hdmi** is a dependency injection framework for Python that manages dynamic dependencies with late (just-in-time)
resolution. The framework provides:

- Dependency injection containers with runtime introspection capabilities
- Late-binding dependency resolution (instantiated only when needed)
- Type-annotation-based configuration using Python's standard typing system
- Scope-aware dependency validation (singleton, scoped, transient)
- Tools for inspecting and debugging the dependency graph at runtime

## Development Setup

This project uses **uv** for dependency management and **pytest** for testing.

### Common Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_filename.py

# Run a specific test
uv run pytest tests/test_filename.py::test_function_name

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=hdmi --cov-report=html

# Using Makefile targets
make test           # Run all tests
make test-verbose   # Run tests with verbose output
make test-cov       # Run tests with coverage
make help           # Show all available targets
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
- Tests live in the `tests/` directory, mirroring the `src/` structure

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

# Build and watch for changes
make docs-watch

# Clean documentation build
make docs-clean
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
- **Introspection First**: Easy to inspect and debug

## Project Status

This project is in the **specification phase**. The focus is currently on:
1. Defining the API and behavior through tests (TDD)
2. Documenting the architecture and design decisions
3. Creating examples demonstrating the type-annotation-based API

Implementation will follow once the specification is solid.
