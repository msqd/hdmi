"""Tests for async Container functionality."""

import pytest

from hdmi import ContainerBuilder


class SimpleService:
    """A simple service for testing."""

    pass


@pytest.mark.anyio
async def test_container_supports_async_context_manager():
    """Container can be used as an async context manager."""
    builder = ContainerBuilder()
    builder.register(SimpleService)

    async with builder.build() as container:
        assert container is not None


@pytest.mark.anyio
async def test_container_get_is_async():
    """Container.get() is an async method."""
    builder = ContainerBuilder()
    builder.register(SimpleService)

    async with builder.build() as container:
        service = await container.get(SimpleService)
        assert isinstance(service, SimpleService)


@pytest.mark.anyio
async def test_singleton_created_once_across_multiple_gets():
    """Singleton services are created once and cached."""

    class Counter:
        instances = 0

        def __init__(self):
            Counter.instances += 1

    builder = ContainerBuilder()
    builder.register(Counter, scope="singleton")

    async with builder.build() as container:
        service1 = await container.get(Counter)
        service2 = await container.get(Counter)

        assert service1 is service2
        assert Counter.instances == 1


@pytest.mark.anyio
async def test_transient_created_each_time():
    """Transient services are created fresh each time."""

    class Counter:
        instances = 0

        def __init__(self):
            Counter.instances += 1
            self.id = Counter.instances

    builder = ContainerBuilder()
    builder.register(Counter, scope="transient")

    async with builder.build() as container:
        service1 = await container.get(Counter)
        service2 = await container.get(Counter)

        assert service1 is not service2
        assert service1.id == 1
        assert service2.id == 2
