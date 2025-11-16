"""ScopedContainer - Scoped container for dependency injection.

ScopedContainer follows the decorator pattern, extending Container to provide
scoped service resolution within a specific scope context.
"""

import asyncio
from contextlib import AsyncExitStack
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
        self._pending_tasks: dict[Type, asyncio.Task] = {}  # For scoped services only
        self._exit_stack: AsyncExitStack | None = None
        # Note: we don't initialize _singletons as we delegate to parent

    async def __aenter__(self) -> "ScopedContainer":
        """Enter the async scope context.

        Returns:
            Self to enable 'async with container.scope() as scoped:' syntax
        """
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async scope context and cleanup all scoped services.

        This triggers finalizers and closes async context managers for scoped services.
        """
        if self._exit_stack is not None:
            await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
            self._exit_stack = None
        self._scoped_instances.clear()

    async def get(self, service_type: Type[T]) -> T:
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

        # Handle based on scope flags
        if not definition.scoped:
            # Non-scoped services (singleton or transient) - delegate to parent
            return await self._parent.get(service_type)  # type: ignore

        # Scoped services (scoped=True)
        if definition.transient:
            # Scoped Transient (scoped=True, transient=True): new instance every time, no task sharing
            return await self._create_instance(service_type)  # type: ignore
        else:
            # Scoped (scoped=True, transient=False): cached with task sharing
            # Check if already cached
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]  # type: ignore

            # Check if task is already pending (task sharing)
            if service_type in self._pending_tasks:
                # Reuse existing task
                return await self._pending_tasks[service_type]  # type: ignore

            # Create new task and store it
            task = asyncio.create_task(self._create_instance(service_type))
            self._pending_tasks[service_type] = task

            try:
                # Await the task
                instance = await task
                # Cache the result
                self._scoped_instances[service_type] = instance
                return instance  # type: ignore
            finally:
                # Remove from pending tasks (cleanup)
                self._pending_tasks.pop(service_type, None)
