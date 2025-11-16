"""Tests for Container (default) - Runtime Resolution Phase.

Following TDD methodology, tests are written first to define behavior.
"""

import pytest


class SimpleService:
    """A simple service with no dependencies."""

    def __init__(self):
        self.value = "simple"


class AnotherService:
    """Another simple service."""

    def __init__(self):
        self.value = "another"


class ServiceWithDependency:
    """A service that depends on SimpleService."""

    def __init__(self, simple: SimpleService):
        self.simple = simple


def test_container_can_resolve_simple_service():
    """Test that Container can resolve a simple service with no dependencies.

    RED: This test will define the basic get() behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)
    container = builder.build()

    service = container.get(SimpleService)

    assert isinstance(service, SimpleService)
    assert service.value == "simple"


def test_container_singleton_returns_same_instance():
    """Test that singleton scope returns the same instance.

    RED: This test will verify singleton behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    container = builder.build()

    service1 = container.get(SimpleService)
    service2 = container.get(SimpleService)

    assert service1 is service2


def test_container_transient_returns_different_instances():
    """Test that transient scope returns different instances.

    RED: This test will verify transient behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="transient")
    container = builder.build()

    service1 = container.get(SimpleService)
    service2 = container.get(SimpleService)

    assert service1 is not service2
    assert isinstance(service1, SimpleService)
    assert isinstance(service2, SimpleService)


def test_container_resolves_dependencies_from_type_annotations():
    """Test that Container automatically resolves dependencies from type annotations.

    RED: This test will fail because dependency resolution isn't implemented yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    builder.register(ServiceWithDependency, scope="singleton")
    container = builder.build()

    service = container.get(ServiceWithDependency)

    assert isinstance(service, ServiceWithDependency)
    assert isinstance(service.simple, SimpleService)


def test_container_raises_error_for_unregistered_service():
    """Test that Container raises an error when requesting unregistered service.

    RED: This test will verify error handling.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    container = builder.build()

    with pytest.raises(KeyError):
        container.get(SimpleService)


def test_container_raises_error_for_scoped_service():
    """Test that Container.get() raises exception when accessing scoped service.

    RED: Scoped services require a scope context and cannot be resolved
    directly from Container. User must use Container.scope() instead.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")
    container = builder.build()

    with pytest.raises(ScopeViolationError) as exc_info:
        container.get(SimpleService)

    assert "scoped" in str(exc_info.value).lower()
    assert "scope()" in str(exc_info.value)


def test_container_scope_returns_scoped_container():
    """Test that Container.scope() returns a ScopedContainer instance.

    RED: ScopedContainer is needed to resolve scoped services.
    """
    from hdmi import ContainerBuilder, ScopedContainer

    builder = ContainerBuilder()
    container = builder.build()

    scoped = container.scope()

    assert isinstance(scoped, ScopedContainer)
