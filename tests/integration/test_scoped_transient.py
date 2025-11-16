"""Tests for scoped transient services (scoped=True, transient=True).

Scoped transient services:
- Require a scope context (cannot be resolved from Container)
- Create a new instance on each get() call (not cached)
- Can depend on scoped or non-scoped services
"""

import asyncio

import pytest

from hdmi import ContainerBuilder


class SingletonDep:
    """A singleton dependency."""

    def __init__(self):
        self.value = "singleton"


class ScopedDep:
    """A scoped dependency."""

    def __init__(self):
        self.value = "scoped"


class ScopedTransientService:
    """A scoped transient service."""

    def __init__(self, singleton: SingletonDep, scoped: ScopedDep):
        self.singleton = singleton
        self.scoped = scoped
        self.value = "scoped-transient"


@pytest.mark.anyio
async def test_scoped_transient_creates_new_instance_each_request():
    """Scoped transient services create a new instance on each get() call."""
    builder = ContainerBuilder()
    builder.register(SingletonDep)
    builder.register(ScopedDep, scoped=True)
    builder.register(ScopedTransientService, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope:
            instance1 = await scope.get(ScopedTransientService)
            instance2 = await scope.get(ScopedTransientService)

            # Different instances (not cached)
            assert instance1 is not instance2

            # But they share the same scoped dependency
            assert instance1.scoped is instance2.scoped

            # And they share the same singleton dependency
            assert instance1.singleton is instance2.singleton


@pytest.mark.anyio
async def test_scoped_transient_different_across_scopes():
    """Scoped transient services in different scopes are independent."""
    builder = ContainerBuilder()
    builder.register(SingletonDep)
    builder.register(ScopedDep, scoped=True)
    builder.register(ScopedTransientService, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope1:
            instance1 = await scope1.get(ScopedTransientService)

        async with container.scope() as scope2:
            instance2 = await scope2.get(ScopedTransientService)

        # Different instances
        assert instance1 is not instance2

        # Different scoped dependencies (from different scopes)
        assert instance1.scoped is not instance2.scoped

        # Same singleton dependency
        assert instance1.singleton is instance2.singleton


@pytest.mark.anyio
async def test_scoped_transient_concurrent_requests_create_multiple_instances():
    """Concurrent requests for scoped transient services create multiple instances.

    Unlike scoped services (which use task sharing), scoped transient services
    do not share tasks - each request creates a new instance.
    """
    instantiation_count = 0

    class CountedScopedTransient:
        """Service that counts instantiations."""

        def __init__(self):
            nonlocal instantiation_count
            instantiation_count += 1

    builder = ContainerBuilder()
    builder.register(CountedScopedTransient, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope:
            # Make 5 concurrent requests
            tasks = [scope.get(CountedScopedTransient) for _ in range(5)]
            instances = await asyncio.gather(*tasks)

            # Should have created 5 instances (no task sharing for transients)
            assert instantiation_count == 5

            # All instances are different
            for i in range(len(instances)):
                for j in range(i + 1, len(instances)):
                    assert instances[i] is not instances[j]


@pytest.mark.anyio
async def test_diamond_dependency_with_scoped_transient():
    """Test diamond dependency pattern with scoped transient services.

    Pattern similar to diamond.py:
    - A: singleton (shared)
    - B, C: singleton (share A)
    - D: scoped transient (gets new instance each time, depends on B and C)
    """

    class A:
        pass

    class B:
        def __init__(self, a: A):
            self.a = a

    class C:
        def __init__(self, a: A):
            self.a = a

    class D:
        def __init__(self, b: B, c: C):
            self.b = b
            self.c = c

    builder = ContainerBuilder()
    builder.register(A)
    builder.register(B)
    builder.register(C)
    builder.register(D, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope:
            # Request D multiple times
            d1 = await scope.get(D)
            d2 = await scope.get(D)

            # D is scoped transient - different instances
            assert d1 is not d2

            # But both share the same B and C singletons
            assert d1.b is d2.b
            assert d1.c is d2.c

            # And B and C share the same A singleton
            assert d1.b.a is d1.c.a
            assert d2.b.a is d2.c.a


@pytest.mark.anyio
async def test_scoped_transient_with_scoped_dependencies():
    """Test scoped transient depending on scoped service.

    The scoped transient gets a new instance each time, but always gets
    the same scoped dependency instance within the scope.
    """

    class ScopedService:
        def __init__(self):
            self.value = "scoped"

    class ScopedTransient:
        def __init__(self, scoped: ScopedService):
            self.scoped = scoped

    builder = ContainerBuilder()
    builder.register(ScopedService, scoped=True)
    builder.register(ScopedTransient, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope:
            st1 = await scope.get(ScopedTransient)
            st2 = await scope.get(ScopedTransient)
            st3 = await scope.get(ScopedTransient)

            # All different instances
            assert st1 is not st2
            assert st2 is not st3

            # All share the same scoped dependency
            assert st1.scoped is st2.scoped
            assert st2.scoped is st3.scoped


@pytest.mark.anyio
async def test_scoped_transient_cannot_be_resolved_from_container():
    """Scoped transient services require a scope context."""
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(ScopedTransientService, scoped=True, transient=True)

    async with builder.build() as container:
        # Should raise ScopeViolationError when trying to resolve from Container
        with pytest.raises(ScopeViolationError) as exc_info:
            await container.get(ScopedTransientService)

        assert "scoped" in str(exc_info.value).lower()
