"""hdmi - Dynamic Dependency Injection for Python.

A lightweight dependency injection framework with:
- Type-driven dependency discovery
- Scope-aware validation
- Lazy instantiation
- Early error detection
"""

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
    "CircularDependencyError",
    "Container",
    "ContainerBuilder",
    "HDMIError",
    "IContainer",
    "IContainer",
    "ScopeViolationError",
    "ScopedContainer",
    "ServiceDefinition",
    "UnresolvableDependencyError",
]
