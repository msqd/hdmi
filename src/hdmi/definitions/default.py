"""Default service definition implementation."""

from typing import Any, Callable, Literal, Type

Scope = Literal["singleton", "scoped", "transient"]


class ServiceDefinition:
    """Describes everything to know about a service."""

    def __init__(
        self,
        service_type: Type,
        /,
        *,
        scope: Scope = "singleton",
        name: str | None = None,
        factory: Callable[..., Any] | None = None,
    ):
        if factory is not None and not callable(factory):
            raise ValueError("factory must be callable")

        self.service_type = service_type
        self.scope = scope
        self.name = name
        self.factory = factory
