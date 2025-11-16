"""hdmi - Dynamic Dependency Injection for Python.

A lightweight dependency injection framework with:
- Type-driven dependency discovery
- Scope-aware validation
- Lazy instantiation
- Early error detection
"""

from hdmi.builder import ContainerBuilder
from hdmi.containers import Container, IContainer, ScopedContainer
from hdmi.exceptions import (
    CircularDependencyError,
    HDMIError,
    ScopeViolationError,
    UnresolvableDependencyError,
)

__all__ = [
    "ContainerBuilder",
    "Container",
    "IContainer",
    "ScopedContainer",
    "HDMIError",
    "ScopeViolationError",
    "CircularDependencyError",
    "UnresolvableDependencyError",
]
