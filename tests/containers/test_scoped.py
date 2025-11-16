"""Tests for ScopedContainer - Scoped Service Resolution.

Following TDD methodology, tests are written first to define behavior.
"""


class SimpleService:
    """A simple service with no dependencies."""

    def __init__(self):
        self.value = "simple"


def test_scoped_container_is_context_manager():
    """Test that ScopedContainer can be used as a context manager.

    RED: ScopedContainer should implement __enter__ and __exit__.
    """
    from hdmi import ContainerBuilder, ScopedContainer

    builder = ContainerBuilder()
    container = builder.build()

    # Should work as context manager
    with container.scope() as scoped:
        # scoped should be the ScopedContainer instance
        assert isinstance(scoped, ScopedContainer)


def test_scoped_container_resolves_and_caches_scoped_services():
    """Test that ScopedContainer can resolve scoped services and caches them.

    RED: ScopedContainer.get() should resolve scoped services once per scope.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")
    container = builder.build()

    with container.scope() as scoped:
        service1 = scoped.get(SimpleService)
        service2 = scoped.get(SimpleService)

        # Should be the same instance (cached)
        assert service1 is service2
        assert isinstance(service1, SimpleService)


def test_scoped_container_delegates_singleton_to_parent():
    """Test that ScopedContainer delegates singleton services to parent Container.

    RED: Singleton services should be shared across all scopes.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="singleton")
    container = builder.build()

    # Get from parent container first
    singleton = container.get(SimpleService)

    # Get from scoped container - should be same instance
    with container.scope() as scoped:
        scoped_singleton = scoped.get(SimpleService)
        assert scoped_singleton is singleton


def test_scoped_container_delegates_transient_to_parent():
    """Test that ScopedContainer delegates transient services to parent Container.

    RED: Transient services should create new instances each time.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="transient")
    container = builder.build()

    with container.scope() as scoped:
        transient1 = scoped.get(SimpleService)
        transient2 = scoped.get(SimpleService)

        # Should be different instances (transient behavior)
        assert transient1 is not transient2
        assert isinstance(transient1, SimpleService)
        assert isinstance(transient2, SimpleService)


def test_scoped_dependencies_share_same_cache():
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
    container = builder.build()

    with container.scope() as scoped:
        # Get ScopedA directly
        a1 = scoped.get(ScopedA)

        # Get ScopedB which depends on ScopedA
        b = scoped.get(ScopedB)

        # ScopedB should have the same instance of ScopedA
        assert b.a is a1


def test_new_scope_creates_new_instances():
    """Test that each new scope creates fresh instances of scoped services.

    RED: Different scopes should have different instances.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scope="scoped")
    container = builder.build()

    # First scope
    with container.scope() as scope1:
        service1 = scope1.get(SimpleService)

    # Second scope - should create a new instance
    with container.scope() as scope2:
        service2 = scope2.get(SimpleService)

    # Different scopes should have different instances
    assert service1 is not service2
    assert isinstance(service1, SimpleService)
    assert isinstance(service2, SimpleService)
