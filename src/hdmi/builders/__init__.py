"""hdmi.builders - Container builder implementations.

This package provides builder classes for configuring dependency injection:
- ContainerBuilder: Builder for creating and validating containers
"""

from hdmi.builders.default import ContainerBuilder

__all__ = [
    "ContainerBuilder",
]
