"""Tests for service lifecycle management (initializers, finalizers, context managers)."""

import pytest

from hdmi import ContainerBuilder


class ServiceWithInitializer:
    """Service with an initializer callback."""

    def __init__(self):
        self.initialized = False

    def initialize(self):
        """Sync initializer."""
        self.initialized = True


class ServiceWithAsyncInitializer:
    """Service with an async initializer callback."""

    def __init__(self):
        self.initialized = False

    async def initialize_async(self):
        """Async initializer."""
        self.initialized = True


class ServiceWithFinalizer:
    """Service with a finalizer callback."""

    def __init__(self):
        self.finalized = False

    def cleanup(self):
        """Sync finalizer."""
        self.finalized = True


class ServiceWithAsyncFinalizer:
    """Service with an async finalizer callback."""

    def __init__(self):
        self.finalized = False

    async def cleanup_async(self):
        """Async finalizer."""
        self.finalized = True


class ServiceAsAsyncContextManager:
    """Service that is an async context manager."""

    def __init__(self):
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True


@pytest.mark.anyio
async def test_sync_initializer_is_called():
    """Sync initializer is called after service instantiation."""
    builder = ContainerBuilder()

    def init_service(service: ServiceWithInitializer):
        service.initialize()

    builder.register(ServiceWithInitializer, initializer=init_service)

    async with builder.build() as container:
        service = await container.get(ServiceWithInitializer)
        assert service.initialized is True


@pytest.mark.anyio
async def test_async_initializer_is_called():
    """Async initializer is called after service instantiation."""
    builder = ContainerBuilder()

    async def init_service_async(service: ServiceWithAsyncInitializer):
        await service.initialize_async()

    builder.register(ServiceWithAsyncInitializer, initializer=init_service_async)

    async with builder.build() as container:
        service = await container.get(ServiceWithAsyncInitializer)
        assert service.initialized is True


@pytest.mark.anyio
async def test_sync_finalizer_is_called_on_exit():
    """Sync finalizer is called when container exits."""
    builder = ContainerBuilder()
    service_instance = None

    def cleanup_service(service: ServiceWithFinalizer):
        service.cleanup()

    builder.register(ServiceWithFinalizer, finalizer=cleanup_service)

    async with builder.build() as container:
        service_instance = await container.get(ServiceWithFinalizer)
        assert service_instance.finalized is False

    # After exiting context, finalizer should have been called
    assert service_instance.finalized is True


@pytest.mark.anyio
async def test_async_finalizer_is_called_on_exit():
    """Async finalizer is called when container exits."""
    builder = ContainerBuilder()
    service_instance = None

    async def cleanup_service_async(service: ServiceWithAsyncFinalizer):
        await service.cleanup_async()

    builder.register(ServiceWithAsyncFinalizer, finalizer=cleanup_service_async)

    async with builder.build() as container:
        service_instance = await container.get(ServiceWithAsyncFinalizer)
        assert service_instance.finalized is False

    # After exiting context, finalizer should have been called
    assert service_instance.finalized is True


@pytest.mark.anyio
async def test_async_context_manager_service_not_auto_entered():
    """Service implementing async context manager is NOT automatically entered.

    The user is responsible for managing their service's context.
    """
    builder = ContainerBuilder()
    service_instance = None

    builder.register(ServiceAsAsyncContextManager)

    async with builder.build() as container:
        service_instance = await container.get(ServiceAsAsyncContextManager)
        # Service should NOT be automatically entered
        assert service_instance.entered is False
        assert service_instance.exited is False

    # After exiting container, service should still not be entered/exited
    # because the container doesn't manage user service contexts
    assert service_instance.entered is False
    assert service_instance.exited is False


@pytest.mark.anyio
async def test_initializer_and_finalizer_together():
    """Service can have both initializer and finalizer."""

    class ServiceWithBoth:
        def __init__(self):
            self.initialized = False
            self.finalized = False

    builder = ContainerBuilder()
    service_instance = None

    builder.register(
        ServiceWithBoth,
        initializer=lambda s: setattr(s, "initialized", True),
        finalizer=lambda s: setattr(s, "finalized", True),
    )

    async with builder.build() as container:
        service_instance = await container.get(ServiceWithBoth)
        assert service_instance.initialized is True
        assert service_instance.finalized is False

    assert service_instance.finalized is True
