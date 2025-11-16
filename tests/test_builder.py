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
