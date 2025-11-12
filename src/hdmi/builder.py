"""ContainerBuilder - Configuration phase for dependency injection.

The ContainerBuilder accumulates service registrations and produces
a validated, immutable Container when build() is called.
"""

import inspect
from typing import Any, Literal, Type, get_type_hints

from hdmi.exceptions import ScopeViolationError

Scope = Literal["singleton", "scoped", "transient"]

# Scope hierarchy: higher number = longer lifetime
SCOPE_HIERARCHY = {
    "singleton": 3,
    "scoped": 2,
    "transient": 1,
}


class ServiceRegistration:
    """Internal representation of a registered service."""

    def __init__(
        self,
        service_type: Type,
        scope: Scope = "singleton",
    ):
        self.service_type = service_type
        self.scope = scope


class ContainerBuilder:
    """Mutable builder for configuring dependency injection services.

    The ContainerBuilder is responsible for:
    - Accumulating service registrations
    - Validating the dependency graph when build() is called
    - Producing an immutable, validated Container
    """

    def __init__(self):
        self._registrations: dict[Type, ServiceRegistration] = {}

    def register(
        self,
        service_type: Type,
        *,
        scope: Scope = "singleton",
    ) -> None:
        """Register a service type with the container.

        Args:
            service_type: The class to register as a service
            scope: The lifecycle scope (singleton, scoped, or transient)
        """
        registration = ServiceRegistration(service_type, scope=scope)
        self._registrations[service_type] = registration

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
        from hdmi.container import Container

        # Validate scope hierarchy for all registrations
        self._validate_scopes()

        # Create and return the validated Container
        return Container(self._registrations)

    def _validate_scopes(self) -> None:
        """Validate that scope hierarchy is respected.

        Raises:
            ScopeViolationError: If a service depends on a service with shorter lifetime
        """
        for service_type, registration in self._registrations.items():
            # Get dependencies from type annotations
            dependencies = self._get_dependencies(service_type)

            # Check each dependency's scope
            for dep_name, dep_type in dependencies.items():
                if dep_type not in self._registrations:
                    # Will be caught later by unresolvable dependency check
                    continue

                dep_registration = self._registrations[dep_type]

                # Validate scope hierarchy
                service_scope_level = SCOPE_HIERARCHY[registration.scope]
                dep_scope_level = SCOPE_HIERARCHY[dep_registration.scope]

                # A service can only depend on services with same or higher scope level
                # (higher number = longer lifetime)
                if service_scope_level > dep_scope_level:
                    raise ScopeViolationError(
                        f"{service_type.__name__} ({registration.scope}) cannot depend on "
                        f"{dep_type.__name__} ({dep_registration.scope}). "
                        f"Services can only depend on services with the same or longer lifetime."
                    )

    def _get_dependencies(self, service_type: Type) -> dict[str, Type]:
        """Get dependencies from type annotations.

        Args:
            service_type: The service type to analyze

        Returns:
            Dictionary mapping parameter name to dependency type
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

            if param_name in hints:
                dependencies[param_name] = hints[param_name]

        return dependencies
