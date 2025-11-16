"""Container - Root container for dependency injection.

The Container is an immutable, validated dependency graph that resolves
service instances lazily (just-in-time) when requested.
"""

import asyncio
import inspect
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Type, TypeVar, get_type_hints

from anyio import to_thread

from hdmi.utils.typing import extract_type_from_optional

if TYPE_CHECKING:
    from hdmi.types.definitions import ServiceDefinition
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
        self._pending_tasks: dict[Type, asyncio.Task] = {}
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
        if definition.scoped:
            raise ScopeViolationError(
                f"{service_type.__name__} is a scoped service (scoped=True) and cannot be resolved "
                f"directly from Container. Use Container.scope() to create a scoped context."
            )

        # Handle non-scoped services
        if definition.transient:
            # Transient (scoped=False, transient=True): new instance every time, no task sharing
            return await self._create_instance(service_type)  # type: ignore
        else:
            # Singleton (scoped=False, transient=False): cached with task sharing
            # Check if already cached
            if service_type in self._singletons:
                return self._singletons[service_type]  # type: ignore

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
                self._singletons[service_type] = instance
                return instance  # type: ignore
            finally:
                # Remove from pending tasks (cleanup)
                self._pending_tasks.pop(service_type, None)

    async def _create_instance(self, service_type: Type[T]) -> T:
        """Create an instance of a service, resolving dependencies and managing lifecycle.

        Args:
            service_type: The service type to instantiate

        Returns:
            An instance with all dependencies resolved and lifecycle hooks executed
        """
        # Get the __init__ signature
        try:
            sig = inspect.signature(service_type.__init__)
        except ValueError:
            # If we can't get signature, try without parameters
            instance = service_type()  # type: ignore
            await self._manage_lifecycle(service_type, instance)
            return instance

        # Get type hints for the __init__ method
        try:
            hints = get_type_hints(service_type.__init__)
        except Exception:
            hints = {}

        # Collect dependencies to resolve concurrently
        dependency_tasks: dict[str, asyncio.Task] = {}

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
                        # Create task for concurrent resolution
                        dependency_tasks[param_name] = asyncio.create_task(self.get(dependency_type))
                    # else: skip (autowire=False, let class use default)
                # else: skip (not registered, let class use default)
            else:
                # Required dependency - create task for concurrent resolution
                dependency_tasks[param_name] = asyncio.create_task(self.get(dependency_type))

        # Resolve all dependencies concurrently
        if dependency_tasks:
            # Wait for all dependency tasks to complete
            await asyncio.gather(*dependency_tasks.values())

            # Collect results into kwargs
            kwargs = {param_name: task.result() for param_name, task in dependency_tasks.items()}
        else:
            kwargs = {}

        instance = service_type(**kwargs)  # type: ignore

        # Manage lifecycle (initializer, context manager, finalizer)
        await self._manage_lifecycle(service_type, instance)

        return instance

    async def _manage_lifecycle(self, service_type: Type[T], instance: T) -> None:
        """Manage the lifecycle of a service instance.

        This includes:
        - Calling initializer (if provided)
        - Registering finalizer with exit stack (if provided)

        Note: Services that are context managers are NOT automatically entered.
        The user is responsible for managing their context themselves.

        Args:
            service_type: The service type
            instance: The service instance
        """
        definition = self._definitions[service_type]

        # Call initializer if provided
        if definition.initializer is not None:
            if inspect.iscoroutinefunction(definition.initializer):
                await definition.initializer(instance)
            else:
                # Run sync initializer in thread pool
                await to_thread.run_sync(definition.initializer, instance)

        # Register finalizer with exit stack if provided
        if definition.finalizer is not None and self._exit_stack is not None:
            if inspect.iscoroutinefunction(definition.finalizer):
                # Async finalizer
                self._exit_stack.push_async_callback(definition.finalizer, instance)
            else:
                # Sync finalizer - wrap in async callback that runs in thread pool
                finalizer = definition.finalizer  # Capture to satisfy type checker

                async def _run_sync_finalizer():
                    await to_thread.run_sync(finalizer, instance)

                self._exit_stack.push_async_callback(_run_sync_finalizer)
