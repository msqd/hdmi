"""Tests for ScopedContainer - Scoped Service Resolution.

Following TDD methodology, tests are written first to define behavior.
"""

import pytest


class SimpleService:
    """A simple service with no dependencies."""

    def __init__(self):
        self.value = "simple"


@pytest.mark.anyio
async def test_scoped_container_is_context_manager():
    """Test that ScopedContainer can be used as a context manager.

    RED: ScopedContainer should implement __enter__ and __exit__.
    """
    from hdmi import ContainerBuilder, ScopedContainer

    builder = ContainerBuilder()
    async with builder.build() as container:
        # Should work as context manager
        async with container.scope() as scoped:
            # scoped should be the ScopedContainer instance
            assert isinstance(scoped, ScopedContainer)


@pytest.mark.anyio
async def test_scoped_container_resolves_and_caches_scoped_services():
    """Test that ScopedContainer can resolve scoped services and caches them.

    RED: ScopedContainer.get() should resolve scoped services once per scope.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")
    async with builder.build() as container:
        async with container.scope() as scoped:
            service1 = await scoped.get(SimpleService)
            service2 = await scoped.get(SimpleService)

            # Should be the same instance (cached)
            assert service1 is service2
            assert isinstance(service1, SimpleService)


@pytest.mark.anyio
async def test_scoped_container_delegates_singleton_to_parent():
    """Test that ScopedContainer delegates singleton services to parent Container.

    RED: Singleton services should be shared across all scopes.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    async with builder.build() as container:
        # Get from parent container first
        singleton = await container.get(SimpleService)

        # Get from scoped container - should be same instance
        async with container.scope() as scoped:
            scoped_singleton = await scoped.get(SimpleService)
            assert scoped_singleton is singleton


@pytest.mark.anyio
async def test_scoped_container_delegates_transient_to_parent():
    """Test that ScopedContainer delegates transient services to parent Container.

    RED: Transient services should create new instances each time.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="transient")
    async with builder.build() as container:
        async with container.scope() as scoped:
            transient1 = await scoped.get(SimpleService)
            transient2 = await scoped.get(SimpleService)

            # Should be different instances (transient behavior)
            assert transient1 is not transient2
            assert isinstance(transient1, SimpleService)
            assert isinstance(transient2, SimpleService)


@pytest.mark.anyio
async def test_scoped_dependencies_share_same_cache():
    """Test that scoped services can depend on other scoped services.

    RED: Scoped→scoped dependencies should all be resolved from the same cache.
    """
    from hdmi import ContainerBuilder

    class ScopedA:
        def __init__(self):
            self.value = "scoped_a"

    class ScopedB:
        def __init__(self, a: ScopedA):
            self.a = a

    builder = ContainerBuilder()
    builder.register(ScopedA, scope="scoped")
    builder.register(ScopedB, scope="scoped")
    async with builder.build() as container:
        async with container.scope() as scoped:
            # Get ScopedA directly
            a1 = await scoped.get(ScopedA)

            # Get ScopedB which depends on ScopedA
            b = await scoped.get(ScopedB)

            # ScopedB should have the same instance of ScopedA
            assert b.a is a1


@pytest.mark.anyio
async def test_new_scope_creates_new_instances():
    """Test that each new scope creates fresh instances of scoped services.

    RED: Different scopes should have different instances.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")
    async with builder.build() as container:
        # First scope
        async with container.scope() as scope1:
            service1 = await scope1.get(SimpleService)

        # Second scope - should create a new instance
        async with container.scope() as scope2:
            service2 = await scope2.get(SimpleService)

        # Different scopes should have different instances
        assert service1 is not service2
        assert isinstance(service1, SimpleService)
        assert isinstance(service2, SimpleService)


@pytest.mark.anyio
async def test_scoped_container_raises_error_for_unregistered_service():
    """Test that ScopedContainer raises error when requesting unregistered service.

    RED: This test will verify error handling in scoped context.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import UnresolvableDependencyError

    builder = ContainerBuilder()
    async with builder.build() as container:
        async with container.scope() as scoped:
            with pytest.raises(UnresolvableDependencyError) as exc_info:
                await scoped.get(SimpleService)

            # Verify the error message is helpful
            assert "SimpleService" in str(exc_info.value)
            assert "not registered" in str(exc_info.value).lower()
