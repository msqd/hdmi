"""Tests for ContainerBuilder - Configuration Phase.

Following TDD methodology, tests are written first to define behavior.
"""

import pytest


class SimpleService:
    """A simple service with no dependencies."""

    pass


class ServiceWithDependency:
    """A service that depends on SimpleService."""

    def __init__(self, simple: SimpleService):
        self.simple = simple


@pytest.mark.anyio
async def test_container_builder_can_register_service():
    """Test that ContainerBuilder can register a service type.

    RED: This test will fail because ContainerBuilder doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    # Should not raise any exception
    assert True


@pytest.mark.anyio
async def test_container_builder_can_build_container():
    """Test that ContainerBuilder can build a Container.

    RED: This test will fail because build() method doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    async with builder.build() as container:
        # Container should exist
        assert container is not None


@pytest.mark.anyio
async def test_container_builder_register_with_scope():
    """Test that ContainerBuilder can register a service with a specific scope.

    RED: This test will fail because scope parameter doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    builder.register(ServiceWithDependency, scope="transient")

    # Should not raise any exception
    assert True


@pytest.mark.anyio
async def test_container_builder_register_with_custom_scope():
    """ContainerBuilder.register() creates ServiceDefinition with custom scope."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")

    # The builder should have stored the definition correctly
    # Access internal state to verify (this is a test, so it's acceptable)
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.service_type is SimpleService
    assert stored_def.scope == "scoped"


@pytest.mark.anyio
async def test_container_builder_register_with_name():
    """ContainerBuilder.register() supports name parameter."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton", name="my_service")

    # Verify the name was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.name == "my_service"


@pytest.mark.anyio
async def test_container_builder_register_with_factory():
    """ContainerBuilder.register() supports factory parameter."""
    from hdmi import ContainerBuilder

    def create_simple_service():
        return SimpleService()

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="transient", factory=create_simple_service)

    # Verify the factory was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.factory is create_simple_service


@pytest.mark.anyio
async def test_container_builder_register_with_autowire_true():
    """ContainerBuilder.register() supports autowire parameter set to True."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, autowire=True)

    # Verify autowire was set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.autowire is True


@pytest.mark.anyio
async def test_container_builder_register_with_autowire_false():
    """ContainerBuilder.register() supports autowire parameter set to False."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, autowire=False)

    # Verify autowire was set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.autowire is False


@pytest.mark.anyio
async def test_container_builder_register_with_all_parameters():
    """ContainerBuilder.register() supports all ServiceDefinition parameters."""
    from hdmi import ContainerBuilder

    def create_simple_service():
        return SimpleService()

    builder = ContainerBuilder()
    builder.register(
        SimpleService,
        scope="scoped",
        name="my_service",
        factory=create_simple_service,
        autowire=False,
    )

    # Verify all parameters were set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.scope == "scoped"
    assert stored_def.name == "my_service"
    assert stored_def.factory is create_simple_service
    assert stored_def.autowire is False
