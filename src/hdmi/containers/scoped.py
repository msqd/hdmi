"""ScopedContainer - Scoped container for dependency injection.

ScopedContainer follows the decorator pattern, extending Container to provide
scoped service resolution within a specific scope context.
"""

from typing import TYPE_CHECKING, Type, TypeVar

from hdmi.containers.default import Container

if TYPE_CHECKING:
    pass

T = TypeVar("T")


class ScopedContainer(Container):
    """Scoped container for resolving scoped services within a scope context.

    ScopedContainer extends Container, following the decorator pattern to delegate
    to its parent Container for non-scoped services while maintaining its own
    cache for scoped instances.

    Implements IContainer protocol to provide a consistent interface with Container.
    """

    def __init__(self, parent: Container):
        """Initialize ScopedContainer with a parent Container.

        Args:
            parent: The parent Container to delegate to
        """
        # Don't call super().__init__ - we use parent's definitions
        self._parent = parent
        self._definitions = parent._definitions
        self._scoped_instances: dict[Type, object] = {}
        # Note: we don't initialize _singletons as we delegate to parent

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
            UnresolvableDependencyError: If the service type is not registered
        """
        from hdmi.exceptions import UnresolvableDependencyError

        try:
            definition = self._definitions[service_type]
        except KeyError:
            raise UnresolvableDependencyError(
                f"{service_type.__name__} is not registered in the container. "
                f"Use ContainerBuilder.register({service_type.__name__}) to register it."
            ) from None

        # If scoped, create and cache in this container
        if definition.scope == "scoped":
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = self._create_instance(service_type)
            return self._scoped_instances[service_type]  # type: ignore

        # For singleton, delegate to parent (singletons cached there)
        if definition.scope == "singleton":
            return self._parent.get(service_type)  # type: ignore

        # For transient, create locally (dependencies resolved through this scope)
        return self._create_instance(service_type)  # type: ignore
