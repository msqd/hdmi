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


@pytest.mark.anyio
async def test_container_can_resolve_simple_service():
    """Test that Container can resolve a simple service with no dependencies.

    RED: This test will define the basic get() behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)
    async with builder.build() as container:
        service = await container.get(SimpleService)

        assert isinstance(service, SimpleService)
        assert service.value == "simple"


@pytest.mark.anyio
async def test_container_singleton_returns_same_instance():
    """Test that singleton scope returns the same instance.

    RED: This test will verify singleton behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)
    async with builder.build() as container:
        service1 = await container.get(SimpleService)
        service2 = await container.get(SimpleService)

        assert service1 is service2


@pytest.mark.anyio
async def test_container_transient_returns_different_instances():
    """Test that transient scope returns different instances.

    RED: This test will verify transient behavior.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, transient=True)
    async with builder.build() as container:
        service1 = await container.get(SimpleService)
        service2 = await container.get(SimpleService)

        assert service1 is not service2
        assert isinstance(service1, SimpleService)
        assert isinstance(service2, SimpleService)


@pytest.mark.anyio
async def test_container_resolves_dependencies_from_type_annotations():
    """Test that Container automatically resolves dependencies from type annotations.

    RED: This test will fail because dependency resolution isn't implemented yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)
    builder.register(ServiceWithDependency)
    async with builder.build() as container:
        service = await container.get(ServiceWithDependency)

        assert isinstance(service, ServiceWithDependency)
        assert isinstance(service.simple, SimpleService)


@pytest.mark.anyio
async def test_container_raises_error_for_unregistered_service():
    """Test that Container raises an error when requesting unregistered service.

    RED: This test will verify error handling.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import UnresolvableDependencyError

    builder = ContainerBuilder()
    async with builder.build() as container:
        with pytest.raises(UnresolvableDependencyError) as exc_info:
            await container.get(SimpleService)

        # Verify the error message is helpful
        assert "SimpleService" in str(exc_info.value)
        assert "not registered" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_unresolvable_dependency_error_extends_keyerror():
    """Test that UnresolvableDependencyError extends KeyError for compatibility.

    This ensures code catching KeyError will still work.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    async with builder.build() as container:
        # Should be catchable as KeyError for backward compatibility
        with pytest.raises(KeyError):
            await container.get(SimpleService)


@pytest.mark.anyio
async def test_container_raises_error_for_scoped_service():
    """Test that Container.get() raises exception when accessing scoped service.

    RED: Scoped services require a scope context and cannot be resolved
    directly from Container. User must use Container.scope() instead.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(SimpleService, scoped=True)
    async with builder.build() as container:
        with pytest.raises(ScopeViolationError) as exc_info:
            await container.get(SimpleService)

        assert "scoped" in str(exc_info.value).lower()
        assert "scope()" in str(exc_info.value)


@pytest.mark.anyio
async def test_container_scope_returns_scoped_container():
    """Test that Container.scope() returns a ScopedContainer instance.

    RED: ScopedContainer is needed to resolve scoped services.
    """
    from hdmi import ContainerBuilder, ScopedContainer

    builder = ContainerBuilder()
    async with builder.build() as container:
        scoped = container.scope()

        assert isinstance(scoped, ScopedContainer)


class Config:
    """A configuration service."""

    def __init__(self):
        self.value = "default_config"


class ServiceWithOptionalDependency:
    """A service with an optional dependency."""

    def __init__(self, *, config: Config | None = None):
        self.config = config if config is not None else Config()


@pytest.mark.anyio
async def test_container_skips_unregistered_optional_dependency():
    """Container does not inject optional dependencies that are not registered.

    When a parameter has a default value and its type is not registered in the
    container, the container should skip injection and let the class use its default.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    # Note: Config is NOT registered
    builder.register(ServiceWithOptionalDependency)
    async with builder.build() as container:
        service = await container.get(ServiceWithOptionalDependency)

        # Service should be created successfully
        assert isinstance(service, ServiceWithOptionalDependency)
        # Config should use the default (created inside __init__)
        assert isinstance(service.config, Config)
        assert service.config.value == "default_config"


@pytest.mark.anyio
async def test_container_injects_registered_optional_dependency_with_autowire_true():
    """Container injects optional dependencies that are registered with autowire=True.

    When a parameter has a default value but its type is registered with autowire=True,
    the container should inject it.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(Config, autowire=True)  # Explicitly autowire=True
    builder.register(ServiceWithOptionalDependency)
    async with builder.build() as container:
        service = await container.get(ServiceWithOptionalDependency)
        injected_config = await container.get(Config)

        # Config should be injected from the container
        assert isinstance(service, ServiceWithOptionalDependency)
        assert service.config is injected_config


@pytest.mark.anyio
async def test_container_skips_registered_optional_dependency_with_autowire_false():
    """Container does not inject optional dependencies when autowire=False.

    When a parameter has a default value and its type is registered with autowire=False,
    the container should NOT inject it into optional dependencies.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(Config, autowire=False)  # Disable autowiring
    builder.register(ServiceWithOptionalDependency)
    async with builder.build() as container:
        service = await container.get(ServiceWithOptionalDependency)

        # Config should use the default (not injected)
        assert isinstance(service, ServiceWithOptionalDependency)
        assert isinstance(service.config, Config)
        # Should be a different instance (not the singleton from container)
        container_config = await container.get(Config)
        assert service.config is not container_config


class ServiceWithRequiredDependency:
    """A service with a required dependency (no default)."""

    def __init__(self, config: Config):
        self.config = config


@pytest.mark.anyio
async def test_container_always_injects_required_dependency():
    """Container always injects required dependencies regardless of autowire setting.

    When a parameter has no default value, it's a required dependency and should
    always be injected, even if autowire=False.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(Config, autowire=False)  # autowire disabled
    builder.register(ServiceWithRequiredDependency)
    async with builder.build() as container:
        service = await container.get(ServiceWithRequiredDependency)

        # Config should still be injected (required dependency)
        assert isinstance(service, ServiceWithRequiredDependency)
        container_config = await container.get(Config)
        assert service.config is container_config  # Same instance
