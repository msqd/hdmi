# hdmi - Dependency Management Interface

A lightweight dependency injection framework for Python 3.13+ with:

- **Type-driven dependency discovery** - Uses Python's standard type annotations
- **Scope-aware validation** - Prevents lifetime bugs at build time
- **Lazy instantiation** - Services created just-in-time
- **Early error detection** - Configuration errors caught at build time

## Quick Example

### Simple Example (Singleton Services)

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

# Configure the container (all singletons by default)
builder = ContainerBuilder()
builder.register(DatabaseConnection)
builder.register(UserRepository)
builder.register(UserService)

# Build validates the dependency graph
container = builder.build()

# Resolve services lazily - dependencies are auto-wired!
user_service = container.get(UserService)
```

### Using Scoped Services

```python
# For request-scoped services (e.g., web requests)
builder = ContainerBuilder()
builder.register(DatabaseConnection)  # singleton (default)
builder.register(UserRepository, scoped=True)  # One per request
builder.register(UserService, transient=True)   # New each time

container = builder.build()

# Scoped services must be resolved within a scope context
with container.scope() as scoped:
    user_service = scoped.get(UserService)
    # All scoped dependencies share the same instance within this scope
```

## Key Features

### Two-Phase Architecture

1. **ContainerBuilder** (Configuration): Register services and define scopes
2. **Container** (Runtime): Validated, immutable graph for lazy resolution

### Scope Safety

Services have four lifecycles that are validated at build time:

- **Singleton** (default): One instance per container
- **Scoped**: One instance per scope (e.g., per request)
- **Transient**: New instance every time
- **Scoped Transient**: New instance every time, requires scope

**Validation Rules (Simplified):**
The only invalid dependency is when a non-scoped service (singleton or transient) depends on a scoped service.

```python
#  Valid: Scoped � Singleton
builder = ContainerBuilder()
builder.register(DatabaseConnection)  # singleton (default)
builder.register(UserRepository, scoped=True)

# L Invalid: Singleton � Scoped (raises ScopeViolationError)
builder = ContainerBuilder()
builder.register(RequestHandler, scoped=True)
builder.register(SingletonService)  # singleton depends on scoped!
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
# Run all checks (linting, type checking, tests)
make test

# Build documentation
make docs

# See all available commands
make help
```

## License

MIT License - see LICENSE file for details.
