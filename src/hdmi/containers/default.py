"""Container - Root container for dependency injection.

The Container is an immutable, validated dependency graph that resolves
service instances lazily (just-in-time) when requested.
"""

import inspect
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Type, TypeVar, get_type_hints

from hdmi._type_utils import extract_type_from_optional

if TYPE_CHECKING:
    from hdmi.builders.types import ServiceDefinition
    from hdmi.containers.scoped import ScopedContainer

T = TypeVar("T")


class Container:
    """Immutable root container for resolving service instances at runtime.

    The Container is produced by ContainerBuilder.build() and is:
    - Immutable: cannot be modified after creation
    - Pre-validated: all configuration errors caught during build
    - Lazy: services instantiated only when first requested via get()
    - Async: all resolution and lifecycle management is async

    Implements IContainer protocol to provide a consistent interface with
    ScopedContainer.
    """

    def __init__(self, definitions: dict[Type, "ServiceDefinition"]):
        """Initialize Container with validated service definitions.

        This should only be called by ContainerBuilder.build().

        Args:
            definitions: Validated service definitions from builder
        """
        self._definitions = definitions
        self._singletons: dict[Type, object] = {}
        self._exit_stack: AsyncExitStack | None = None

    async def __aenter__(self) -> "Container":
        """Enter the async context manager.

        Returns:
            Self to enable 'async with builder.build() as container:' syntax
        """
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager and cleanup all managed services.

        This triggers all registered finalizers and closes all async context managers.
        """
        if self._exit_stack is not None:
            await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
            self._exit_stack = None

    def scope(self) -> "ScopedContainer":
        """Create a new scoped container for resolving scoped services.

        Returns:
            A new ScopedContainer instance
        """
        from hdmi.containers.scoped import ScopedContainer

        return ScopedContainer(self)

    async def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance (lazy instantiation).

        Args:
            service_type: The service type to resolve

        Returns:
            An instance of the service type

        Raises:
            UnresolvableDependencyError: If the service type is not registered
            ScopeViolationError: If trying to resolve a scoped service outside a scope
        """
        from hdmi.exceptions import ScopeViolationError, UnresolvableDependencyError

        try:
            definition = self._definitions[service_type]
        except KeyError:
            raise UnresolvableDependencyError(
                f"{service_type.__name__} is not registered in the container. "
                f"Use ContainerBuilder.register({service_type.__name__}) to register it."
            ) from None

        # Scoped services cannot be resolved directly from Container
        if definition.scope == "scoped":
            raise ScopeViolationError(
                f"{service_type.__name__} is a scoped service and cannot be resolved "
                f"directly from Container. Use Container.scope() to create a scoped context."
            )

        # Handle singleton scope
        if definition.scope == "singleton":
            if service_type not in self._singletons:
                self._singletons[service_type] = await self._create_instance(service_type)
            return self._singletons[service_type]  # type: ignore

        # Handle transient scope (new instance every time)
        return await self._create_instance(service_type)  # type: ignore

    async def _create_instance(self, service_type: Type[T]) -> T:
        """Create an instance of a service, resolving dependencies.

        Args:
            service_type: The service type to instantiate

        Returns:
            An instance with all dependencies resolved
        """
        # Get the __init__ signature
        try:
            sig = inspect.signature(service_type.__init__)
        except ValueError:
            # If we can't get signature, try without parameters
            return service_type()  # type: ignore

        # Get type hints for the __init__ method
        try:
            hints = get_type_hints(service_type.__init__)
        except Exception:
            hints = {}

        # Resolve dependencies from type annotations
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Get the type annotation for this parameter
            if param_name not in hints:
                continue

            type_hint = hints[param_name]
            has_default = param.default is not inspect.Parameter.empty

            # Extract actual type from Optional/Union types (e.g., Config | None -> Config)
            dependency_type = extract_type_from_optional(type_hint)
            if dependency_type is None:
                # Can't determine single type (e.g., Union[A, B] or just None)
                continue

            # Check if dependency is registered
            is_registered = dependency_type in self._definitions

            if has_default:
                # Optional dependency - only inject if registered AND autowire=True
                if is_registered:
                    dep_definition = self._definitions[dependency_type]
                    if dep_definition.autowire:
                        # Inject the dependency
                        kwargs[param_name] = await self.get(dependency_type)
                    # else: skip (autowire=False, let class use default)
                # else: skip (not registered, let class use default)
            else:
                # Required dependency - always inject (even if autowire=False)
                kwargs[param_name] = await self.get(dependency_type)

        return service_type(**kwargs)  # type: ignore
