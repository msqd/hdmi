"""Exceptions for hdmi dependency injection framework."""


class HDMIError(Exception):
    """Base exception for all hdmi errors."""

    pass


class ScopeViolationError(HDMIError):
    """Raised when a service depends on a service with incompatible scope.

    Examples:
    - Singleton depending on Scoped
    - Singleton depending on Transient
    - Scoped depending on Transient
    """

    pass


class CircularDependencyError(HDMIError):
    """Raised when circular dependencies are detected."""

    pass


class UnresolvableDependencyError(HDMIError):
    """Raised when a required dependency cannot be resolved."""

    pass
