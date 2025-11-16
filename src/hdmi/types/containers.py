"""Container protocols - Interface definitions for dependency injection containers."""

from typing import TypeVar, Protocol, Type

T = TypeVar("T")


class IContainer(Protocol):
    """Protocol defining the interface for dependency injection containers.

    This protocol is implemented by both Container (root container) and
    ScopedContainer (scoped container), ensuring they provide a consistent
    interface for resolving service instances.
    """

    def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance.

        Args:
            service_type: The service type to resolve

        Returns:
            An instance of the service type

        Raises:
            KeyError: If the service type is not registered
            ScopeViolationError: If trying to resolve a scoped service
                outside a scope (for root container only)
        """
        ...
