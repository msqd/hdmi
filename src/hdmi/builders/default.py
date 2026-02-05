"""ContainerBuilder - Configuration phase for dependency injection.

The ContainerBuilder accumulates service registrations and produces
a validated, immutable Container when build() is called.
"""

import inspect
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Type, get_type_hints

from hdmi.utils.typing import extract_type_from_optional
from hdmi.types.definitions import ServiceDefinition
from hdmi.exceptions import ScopeViolationError, CircularDependencyError

if TYPE_CHECKING:
    from hdmi.containers import Container


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

        # Check for circular dependencies
        self._check_circular_dependencies()

        # Validate scope hierarchy for all registrations
        self._validate_scopes()

        # Create and return the validated Container
        return Container(self._definitions)

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies in the dependency graph.

        Uses depth-first search to detect cycles. Fails fast on the first cycle found.

        Raises:
            CircularDependencyError: If a circular dependency is detected
        """
        visited = set()
        path = []

        def visit(service_type: Type) -> None:
            if service_type in path:
                # Found a cycle - build the cycle path
                cycle_start = path.index(service_type)
                cycle_path = path[cycle_start:] + [service_type]
                path_str = " → ".join(cls.__name__ for cls in cycle_path)
                raise CircularDependencyError(f"Circular dependency detected: {path_str}")

            if service_type in visited:
                return

            path.append(service_type)

            # Get dependencies that will be injected
            dependencies = self._get_dependencies(service_type)

            for dep_type in dependencies.values():
                if dep_type in self._definitions:
                    visit(dep_type)

            path.pop()
            visited.add(service_type)

        # Visit all registered services
        for service_type in self._definitions:
            visit(service_type)

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
            dependencies = self._get_dependencies(service_type)

            for dependency_name, dependency_type in dependencies.items():
                if dependency_type not in self._definitions:
                    # Will be caught later by unresolvable dependency check
                    continue

                self._validate_scope_compatibility(
                    service_type, definition, dependency_type, self._definitions[dependency_type]
                )

    def _validate_scope_compatibility(
        self,
        service_type: Type,
        service_definition: ServiceDefinition,
        dependency_type: Type,
        dependency_definition: ServiceDefinition,
    ) -> None:
        """Validate that a service's scope is compatible with its dependency's scope.

        Args:
            service_type: The type of the service being validated
            service_definition: The definition of the service
            dependency_type: The type of the dependency
            dependency_definition: The definition of the dependency

        Raises:
            ScopeViolationError: If a non-scoped service depends on a scoped service
        """
        # Non-scoped services cannot depend on scoped services
        if not service_definition.scoped and dependency_definition.scoped:
            service_description = self._format_service_description(service_type, service_definition)
            dependency_description = self._format_service_description(dependency_type, dependency_definition)

            raise ScopeViolationError(
                f"{service_description} cannot depend on {dependency_description}. "
                f"Non-scoped services cannot depend on scoped services because "
                f"scoped services only exist within a scope context."
            )

    def _format_service_description(self, service_type: Type, definition: ServiceDefinition) -> str:
        """Format a service type and definition for error messages.

        Args:
            service_type: The service type
            definition: The service definition

        Returns:
            A formatted string describing the service and its scope
        """
        return f"{service_type.__name__} (scoped={definition.scoped}, transient={definition.transient})"

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

            dependency_type = self._extract_dependency_type(hints[param_name])
            if dependency_type is None:
                continue

            if self._should_inject_dependency(dependency_type, param.default is not inspect.Parameter.empty):
                dependencies[param_name] = dependency_type

        return dependencies

    def _extract_dependency_type(self, type_hint: Type) -> Type | None:
        """Extract the concrete type from a type hint.

        Handles Optional types by extracting the non-None type.
        Returns None if no single concrete type can be determined.

        Args:
            type_hint: The type annotation to process

        Returns:
            The extracted concrete type, or None if not determinable
        """
        return extract_type_from_optional(type_hint)

    def _should_inject_dependency(self, dependency_type: Type, is_optional: bool) -> bool:
        """Determine if a dependency should be injected.

        Args:
            dependency_type: The type of the dependency
            is_optional: Whether the parameter has a default value

        Returns:
            True if the dependency should be injected, False otherwise
        """
        if not is_optional:
            # Required dependencies are always injected
            return True

        # Optional dependencies need to be registered AND have autowire=True
        if dependency_type not in self._definitions:
            return False

        definition = self._definitions[dependency_type]
        return definition.autowire
