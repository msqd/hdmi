# hdmi - Dependency Management Interface

A lightweight dependency injection framework for Python 3.13+ with:

- **Type-driven dependency discovery** - Uses Python's standard type annotations
- **Scope-aware validation** - Prevents lifetime bugs at build time
- **Lazy instantiation** - Services created just-in-time
- **Early error detection** - Configuration errors caught at build time

## Quick Example

```python
from hdmi import ContainerBuilder

# Define your services
class DatabaseConnection:
    def __init__(self):
        self.connected = True

class UserRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# Configure the container
builder = ContainerBuilder()
builder.register(DatabaseConnection, scope="singleton")
builder.register(UserRepository, scope="scoped")
builder.register(UserService, scope="transient")

# Build validates the dependency graph
container = builder.build()

# Resolve services lazily
user_service = container.get(UserService)
```

## Key Features

### Two-Phase Architecture

1. **ContainerBuilder** (Configuration): Register services and define scopes
2. **Container** (Runtime): Validated, immutable graph for lazy resolution

### Scope Safety

Services have lifecycles that are validated at build time:

- **Singleton**: One instance per container (longest lifetime)
- **Scoped**: One instance per scope (e.g., per request)
- **Transient**: New instance every time (shortest lifetime)

**Validation Rules:**
- Singleton can only depend on Singleton
- Scoped can depend on Singleton or Scoped
- Transient can depend on any scope

```python
#  Valid: Scoped � Singleton
builder.register(DatabaseConnection, scope="singleton")
builder.register(UserRepository, scope="scoped")

# L Invalid: Singleton � Scoped (raises ScopeViolationError)
builder.register(RequestHandler, scope="scoped")
builder.register(SingletonService, scope="singleton")  # depends on RequestHandler
container = builder.build()  # ScopeViolationError!
```

### Type-Driven Dependencies

Dependencies are automatically discovered from type annotations:

```python
class ServiceA:
    def __init__(self, dep: DependencyType):
        self.dep = dep
```

No decorators or manual wiring required!

## Installation

```bash
pip install hdmi  # Coming soon
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and follows strict TDD methodology.

```bash
# Install dependencies
uv sync --all-extras

# Run tests
make test

# Run tests with coverage
make test-cov

# Build documentation
make docs
```

## Project Status

Currently in **specification phase**, actively implementing core features following TDD.

## License

MIT License - see LICENSE file for details.
