"""Service definition types for dependency injection."""

from typing import Any, Awaitable, Callable, Literal, Type, TypeVar

T = TypeVar("T")

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
        factory: Callable[..., Any] | Callable[..., Awaitable[Any]] | None = None,
        autowire: bool = True,
        initializer: Callable[[Any], None] | Callable[[Any], Awaitable[None]] | None = None,
        finalizer: Callable[[Any], None] | Callable[[Any], Awaitable[None]] | None = None,
    ):
        if factory is not None and not callable(factory):
            raise ValueError("factory must be callable")
        if initializer is not None and not callable(initializer):
            raise ValueError("initializer must be callable")
        if finalizer is not None and not callable(finalizer):
            raise ValueError("finalizer must be callable")

        self.service_type = service_type
        self.scope = scope
        self.name = name
        self.factory = factory
        self.autowire = autowire
        self.initializer = initializer
        self.finalizer = finalizer
