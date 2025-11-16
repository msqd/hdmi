"""Exceptions for hdmi dependency injection framework."""


class HDMIError(Exception):
    """Base exception for all hdmi errors."""

    pass


class ScopeViolationError(HDMIError):
    """Raised when a service depends on a service with incompatible scope.

    The only invalid dependency pattern is when a non-scoped service
    (singleton or transient) attempts to depend on a scoped service.

    Valid patterns:
    - Any service can depend on singleton services
    - Any service can depend on transient services
    - Scoped services can depend on any service type

    Invalid patterns:
    - Singleton (scoped=False) depending on Scoped (scoped=True)
    - Transient (scoped=False) depending on Scoped (scoped=True)

    Note: Transient dependencies are created once during their dependent's
    construction and live for the dependent's lifetime, making them safe
    dependencies for any service type.
    """

    pass


class CircularDependencyError(HDMIError):
    """Raised when circular dependencies are detected."""

    pass


class UnresolvableDependencyError(HDMIError, KeyError):
    """Raised when a required dependency cannot be resolved.

    This exception extends both HDMIError and KeyError for compatibility
    with code that catches KeyError.
    """

    pass
