# hdmi

**A lightweight dependency injection framework for Python 3.13+ with type-driven discovery and scope validation.**

[![PyPI version](https://img.shields.io/pypi/v/hdmi.svg)](https://pypi.org/project/hdmi/)
[![CI](https://github.com/msqd/hdmi/actions/workflows/cicd.yml/badge.svg)](https://github.com/msqd/hdmi/actions/workflows/cicd.yml)
[![Documentation](https://readthedocs.org/projects/python-hdmi/badge/?version=latest)](https://python-hdmi.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Warning: Pre-Alpha Software**
>
> hdmi is experimental software in active development. Breaking changes may occur until version 1.0.

**Documentation:** [Full Docs](https://python-hdmi.readthedocs.io/) | [Getting Started](https://python-hdmi.readthedocs.io/en/latest/tutorials/) | [API Reference](https://python-hdmi.readthedocs.io/en/latest/reference/)

## Features

- **Type-driven dependency discovery** — Uses Python's standard type annotations, no decorators needed
- **Scope-aware validation** — Prevents lifetime bugs at container build time
- **Lazy instantiation** — Services created just-in-time when first resolved
- **Two-phase architecture** — Configuration separated from runtime for immutable, validated graphs

## Quick Start

```bash
pip install hdmi
```

```python
import asyncio
from hdmi import ContainerBuilder

class DatabaseConnection:
    def __init__(self):
        self.connected = True

class UserRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

async def main():
    builder = ContainerBuilder()
    builder.register(DatabaseConnection)
    builder.register(UserRepository)
    builder.register(UserService)

    container = builder.build()  # Validates the dependency graph
    user_service = await container.get(UserService)  # Auto-wired!

asyncio.run(main())
```

For scoped services (per-request lifecycles), transient services, and scope validation rules, see the [documentation](https://python-hdmi.readthedocs.io/).

## Development

This project follows strict TDD methodology. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
make test    # Run all tests
make docs    # Build documentation
make help    # Show all available commands
```

## License

MIT License — see [LICENSE](LICENSE) for details.
