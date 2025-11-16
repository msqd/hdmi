"""Tests for ContainerBuilder - Configuration Phase.

Following TDD methodology, tests are written first to define behavior.
"""


class SimpleService:
    """A simple service with no dependencies."""

    pass


class ServiceWithDependency:
    """A service that depends on SimpleService."""

    def __init__(self, simple: SimpleService):
        self.simple = simple


def test_container_builder_can_register_service():
    """Test that ContainerBuilder can register a service type.

    RED: This test will fail because ContainerBuilder doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    # Should not raise any exception
    assert True


def test_container_builder_can_build_container():
    """Test that ContainerBuilder can build a Container.

    RED: This test will fail because build() method doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    container = builder.build()

    # Container should exist
    assert container is not None


def test_container_builder_register_with_scope():
    """Test that ContainerBuilder can register a service with a specific scope.

    RED: This test will fail because scope parameter doesn't exist yet.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    builder.register(ServiceWithDependency, scope="transient")

    # Should not raise any exception
    assert True


def test_container_builder_can_register_service_definition():
    """ContainerBuilder can register using a ServiceDefinition directly."""
    from hdmi import ContainerBuilder
    from hdmi.definitions import ServiceDefinition

    builder = ContainerBuilder()
    definition = ServiceDefinition(SimpleService, scope="scoped")
    builder.register(definition)

    # The builder should have stored the definition correctly
    # Access internal state to verify (this is a test, so it's acceptable)
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.service_type is SimpleService
    assert stored_def.scope == "scoped"


def test_container_builder_register_definition_with_name():
    """ContainerBuilder can register a ServiceDefinition with a name."""
    from hdmi import ContainerBuilder
    from hdmi.definitions import ServiceDefinition

    builder = ContainerBuilder()
    definition = ServiceDefinition(SimpleService, scope="singleton", name="my_service")
    builder.register(definition)

    # Verify the name was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.name == "my_service"


def test_container_builder_register_definition_with_factory():
    """ContainerBuilder can register a ServiceDefinition with a factory."""
    from hdmi import ContainerBuilder
    from hdmi.definitions import ServiceDefinition

    def create_simple_service():
        return SimpleService()

    builder = ContainerBuilder()
    definition = ServiceDefinition(SimpleService, scope="transient", factory=create_simple_service)
    builder.register(definition)

    # Verify the factory was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.factory is create_simple_service
