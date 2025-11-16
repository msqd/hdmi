"""hdmi.containers - Dependency injection container implementations.

This package provides the runtime containers for dependency injection:
- IContainer: Protocol defining the container interface
- Container: Root container for singleton and transient services
- ScopedContainer: Scoped container for scoped service resolution
"""

from hdmi.containers.default import Container
from hdmi.containers.protocols import IContainer
from hdmi.containers.scoped import ScopedContainer

__all__ = [
    "IContainer",
    "Container",
    "ScopedContainer",
]
