from typing import Type, Callable, Any, Awaitable


class ServiceDefinition:
    """Describes everything to know about a service.

    Service lifetime is defined by two boolean flags:
    - scoped: False (default) = available from Container, True = requires ScopedContainer
    - transient: False (default) = cached, True = new instance per request

    Four service types:
    1. Singleton (scoped=False, transient=False): cached in Container
    2. Scoped (scoped=True, transient=False): cached in ScopedContainer
    3. Transient (scoped=False, transient=True): not cached, no scope required
    4. Scoped Transient (scoped=True, transient=True): not cached, requires scope
    """

    def __init__(
        self,
        service_type: Type,
        /,
        *,
        scoped: bool = False,
        transient: bool = False,
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
        self.scoped = scoped
        self.transient = transient
        self.name = name
        self.factory = factory
        self.autowire = autowire
        self.initializer = initializer
        self.finalizer = finalizer
