"""Container - Runtime phase for dependency injection.

The Container is an immutable, validated dependency graph that resolves
service instances lazily (just-in-time) when requested.
"""

import inspect
from typing import TYPE_CHECKING, Type, TypeVar, get_type_hints

if TYPE_CHECKING:
    from hdmi.builder import ServiceRegistration

T = TypeVar("T")


class ScopedContainer:
    """Scoped container for resolving scoped services within a scope context.

    ScopedContainer follows the decorator pattern, delegating to its parent
    Container for non-scoped services while maintaining its own cache for
    scoped instances.
    """

    def __init__(self, parent: "Container", registrations: dict[Type, "ServiceRegistration"]):
        """Initialize ScopedContainer with a parent Container.

        Args:
            parent: The parent Container to delegate to
            registrations: Service registrations (shared with parent)
        """
        self._parent = parent
        self._registrations = registrations
        self._scoped_instances: dict[Type, object] = {}

    def __enter__(self) -> "ScopedContainer":
        """Enter the scope context.

        Returns:
            Self to enable 'with container.scope() as scoped:' syntax
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the scope context and clear scoped instances.

        This allows scoped instances to be garbage collected.
        """
        self._scoped_instances.clear()

    def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance within the scope.

        Args:
            service_type: The service type to resolve

        Returns:
            An instance of the service type

        Raises:
            KeyError: If the service type is not registered
        """
        registration = self._registrations[service_type]

        # If scoped, create and cache in this container
        if registration.scope == "scoped":
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = self._create_instance(service_type)
            return self._scoped_instances[service_type]  # type: ignore

        # For singleton, delegate to parent (singletons cached there)
        if registration.scope == "singleton":
            return self._parent.get(service_type)  # type: ignore

        # For transient, create locally (dependencies resolved through this scope)
        return self._create_instance(service_type)  # type: ignore

    def _create_instance(self, service_type: Type[T]) -> T:
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
            if param_name in hints:
                dependency_type = hints[param_name]
                # Recursively resolve the dependency through self (ScopedContainer)
                kwargs[param_name] = self.get(dependency_type)

        return service_type(**kwargs)  # type: ignore


class Container:
    """Immutable container for resolving service instances at runtime.

    The Container is produced by ContainerBuilder.build() and is:
    - Immutable: cannot be modified after creation
    - Pre-validated: all configuration errors caught during build
    - Lazy: services instantiated only when first requested via get()
    """

    def __init__(self, registrations: dict[Type, "ServiceRegistration"]):
        """Initialize Container with validated registrations.

        This should only be called by ContainerBuilder.build().

        Args:
            registrations: Validated service registrations from builder
        """
        self._registrations = registrations
        self._singletons: dict[Type, object] = {}

    def scope(self) -> ScopedContainer:
        """Create a new scoped container for resolving scoped services.

        Returns:
            A new ScopedContainer instance
        """
        return ScopedContainer(self, self._registrations)

    def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance (lazy instantiation).

        Args:
            service_type: The service type to resolve

        Returns:
            An instance of the service type

        Raises:
            KeyError: If the service type is not registered
            ScopeViolationError: If trying to resolve a scoped service outside a scope
        """
        from hdmi.exceptions import ScopeViolationError

        registration = self._registrations[service_type]

        # Scoped services cannot be resolved directly from Container
        if registration.scope == "scoped":
            raise ScopeViolationError(
                f"{service_type.__name__} is a scoped service and cannot be resolved "
                f"directly from Container. Use Container.scope() to create a scoped context."
            )

        # Handle singleton scope
        if registration.scope == "singleton":
            if service_type not in self._singletons:
                self._singletons[service_type] = self._create_instance(service_type)
            return self._singletons[service_type]  # type: ignore

        # Handle transient scope (new instance every time)
        return self._create_instance(service_type)  # type: ignore

    def _create_instance(self, service_type: Type[T]) -> T:
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
            if param_name in hints:
                dependency_type = hints[param_name]
                # Recursively resolve the dependency
                kwargs[param_name] = self.get(dependency_type)

        return service_type(**kwargs)  # type: ignore
