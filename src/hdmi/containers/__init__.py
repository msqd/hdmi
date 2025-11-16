"""hdmi.containers - Dependency injection container implementations.

This package provides the runtime containers for dependency injection:
- Container: Root container for singleton and transient services
- ScopedContainer: Scoped container for scoped service resolution
"""

from hdmi.containers.default import Container
from hdmi.containers.scoped import ScopedContainer

__all__ = [
    "Container",
    "ScopedContainer",
]
