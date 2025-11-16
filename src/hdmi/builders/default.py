"""ContainerBuilder - Configuration phase for dependency injection.

The ContainerBuilder accumulates service registrations and produces
a validated, immutable Container when build() is called.
"""

import inspect
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Type, get_type_hints

from hdmi.utils.typing import extract_type_from_optional
from hdmi.types.definitions import ServiceDefinition
from hdmi.exceptions import ScopeViolationError

if TYPE_CHECKING:
    from hdmi.containers import Container

# Removed - no longer using scope hierarchy with boolean flags


class ContainerBuilder:
    """Mutable builder for configuring dependency injection services.

    The ContainerBuilder is responsible for:
    - Accumulating service registrations
    - Validating the dependency graph when build() is called
    - Producing an immutable, validated Container
    """

    def __init__(self):
        self._definitions: dict[Type, ServiceDefinition] = {}

    def register(
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
    ) -> None:
        """Register a service type with the container.

        Args:
            service_type: The class to register as a service
            scoped: False (default) = available from Container, True = requires ScopedContainer
            transient: False (default) = cached, True = new instance per request
            name: Optional name for the service
            factory: Optional factory function to create the service (sync or async)
            autowire: Whether to auto-inject this service into optional dependencies (defaults to True)
            initializer: Optional initialization function called after service creation (sync or async)
            finalizer: Optional cleanup function called when service is disposed (sync or async)
        """
        definition = ServiceDefinition(
            service_type,
            scoped=scoped,
            transient=transient,
            name=name,
            factory=factory,
            autowire=autowire,
            initializer=initializer,
            finalizer=finalizer,
        )
        self._definitions[service_type] = definition

    def build(self) -> "Container":
        """Build and validate the Container.

        This method:
        1. Validates the dependency graph
        2. Checks for circular dependencies
        3. Validates scope hierarchy
        4. Produces an immutable Container

        Returns:
            An immutable, validated Container ready for runtime use

        Raises:
            CircularDependencyError: If circular dependencies are detected
            UnresolvableDependencyError: If a dependency cannot be resolved
            ScopeViolationError: If scope hierarchy is violated
        """
        from hdmi.containers import Container

        # Validate scope hierarchy for all registrations
        self._validate_scopes()

        # Create and return the validated Container
        return Container(self._definitions)

    def _validate_scopes(self) -> None:
        """Validate that scope rules are respected.

        Validation rule:
        - Non-scoped services (scoped=False) cannot depend on scoped services (scoped=True)

        This is because non-scoped services are available from Container, but scoped
        services only exist within a ScopedContainer context.

        Raises:
            ScopeViolationError: If a non-scoped service depends on a scoped service
        """
        for service_type, definition in self._definitions.items():
            # Get dependencies from type annotations
            dependencies = self._get_dependencies(service_type)

            # Check each dependency's scope
            for dep_name, dep_type in dependencies.items():
                if dep_type not in self._definitions:
                    # Will be caught later by unresolvable dependency check
                    continue

                dep_definition = self._definitions[dep_type]

                # Validate scope compatibility
                # The only unsafe dependency is: non-scoped -> scoped
                # (non-scoped service needs a scoped instance that only exists within a scope)
                if not definition.scoped and dep_definition.scoped:
                    service_type_str = (
                        f"{service_type.__name__} (scoped={definition.scoped}, transient={definition.transient})"
                    )
                    dep_type_str = (
                        f"{dep_type.__name__} (scoped={dep_definition.scoped}, transient={dep_definition.transient})"
                    )
                    raise ScopeViolationError(
                        f"{service_type_str} cannot depend on {dep_type_str}. "
                        f"Non-scoped services cannot depend on scoped services because "
                        f"scoped services only exist within a scope context."
                    )

    def _get_dependencies(self, service_type: Type) -> dict[str, Type]:
        """Get dependencies that will actually be injected.

        Only returns dependencies that will be injected at runtime, respecting:
        - Optional dependencies not registered are skipped
        - Optional dependencies with autowire=False are skipped
        - Required dependencies are always included

        Args:
            service_type: The service type to analyze

        Returns:
            Dictionary mapping parameter name to dependency type (only dependencies that will be injected)
        """
        try:
            sig = inspect.signature(service_type.__init__)
            hints = get_type_hints(service_type.__init__)
        except Exception:
            return {}

        dependencies = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

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
                # Optional dependency - only include if registered AND autowire=True
                if is_registered:
                    dep_definition = self._definitions[dependency_type]
                    if dep_definition.autowire:
                        # Will be injected - include in dependencies
                        dependencies[param_name] = dependency_type
                    # else: skip (autowire=False, won't be injected)
                # else: skip (not registered, won't be injected)
            else:
                # Required dependency - always include (will always be injected)
                dependencies[param_name] = dependency_type

        return dependencies
