"""hdmi - Dynamic Dependency Injection for Python.

A lightweight dependency injection framework with:
- Type-driven dependency discovery
- Scope-aware validation
- Lazy instantiation
- Early error detection
"""

__version__ = "0.2.2"

from hdmi.builders import ContainerBuilder
from hdmi.containers import Container, ScopedContainer
from hdmi.types import IContainer, ServiceDefinition
from hdmi.exceptions import (
    CircularDependencyError,
    HDMIError,
    ScopeViolationError,
    UnresolvableDependencyError,
)

__all__ = [
    "__version__",
    "CircularDependencyError",
    "Container",
    "ContainerBuilder",
    "HDMIError",
    "IContainer",
    "ScopeViolationError",
    "ScopedContainer",
    "ServiceDefinition",
    "UnresolvableDependencyError",
]
