"""hdmi - Lightweight dependency injection for Python 3.13+."""

__version__ = "0.2.3"

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
