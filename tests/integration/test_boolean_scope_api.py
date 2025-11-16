"""Tests for boolean-based scope API (scoped and transient flags).

This replaces the string-based scope parameter with two boolean flags:
- scoped: False (default) = available from Container, True = requires ScopedContainer
- transient: False (default) = cached, True = new instance per request

Four service types:
1. Singleton (scoped=False, transient=False): cached in Container
2. Scoped (scoped=True, transient=False): cached in ScopedContainer
3. Transient (scoped=False, transient=True): not cached, no scope required
4. Scoped Transient (scoped=True, transient=True): not cached, requires scope
"""

import pytest

from hdmi import ContainerBuilder


class SharedDependency:
    """A dependency used by multiple services."""

    def __init__(self):
        self.value = "shared"


class SingletonService:
    """Singleton service (scoped=False, transient=False)."""

    def __init__(self, dep: SharedDependency):
        self.dep = dep


class ScopedService:
    """Scoped service (scoped=True, transient=False)."""

    def __init__(self, dep: SharedDependency):
        self.dep = dep


class TransientService:
    """Transient service (scoped=False, transient=True)."""

    def __init__(self, dep: SharedDependency):
        self.dep = dep


class ScopedTransientService:
    """Scoped transient service (scoped=True, transient=True)."""

    def __init__(self, dep: SharedDependency):
        self.dep = dep


@pytest.mark.anyio
async def test_singleton_service_with_boolean_flags():
    """Test singleton service (scoped=False, transient=False) - the default."""
    builder = ContainerBuilder()
    builder.register(SharedDependency)  # defaults: scoped=False, transient=False
    builder.register(SingletonService)

    async with builder.build() as container:
        instance1 = await container.get(SingletonService)
        instance2 = await container.get(SingletonService)

        # Same instance (cached)
        assert instance1 is instance2
        # Dependency also singleton
        assert instance1.dep is instance2.dep


@pytest.mark.anyio
async def test_scoped_service_with_boolean_flags():
    """Test scoped service (scoped=True, transient=False)."""
    builder = ContainerBuilder()
    builder.register(SharedDependency)  # singleton
    builder.register(ScopedService, scoped=True)

    async with builder.build() as container:
        async with container.scope() as scope1:
            instance1a = await scope1.get(ScopedService)
            instance1b = await scope1.get(ScopedService)

            # Same instance within scope (cached)
            assert instance1a is instance1b
            assert instance1a.dep is instance1b.dep

        async with container.scope() as scope2:
            instance2 = await scope2.get(ScopedService)

            # Different instance in different scope
            assert instance2 is not instance1a
            # But shared singleton dependency
            assert instance2.dep is instance1a.dep


@pytest.mark.anyio
async def test_transient_service_with_boolean_flags():
    """Test transient service (scoped=False, transient=True)."""
    builder = ContainerBuilder()
    builder.register(SharedDependency)  # singleton
    builder.register(TransientService, transient=True)

    async with builder.build() as container:
        instance1 = await container.get(TransientService)
        instance2 = await container.get(TransientService)

        # Different instances (not cached)
        assert instance1 is not instance2
        # But shared singleton dependency
        assert instance1.dep is instance2.dep


@pytest.mark.anyio
async def test_scoped_transient_service_with_boolean_flags():
    """Test scoped transient service (scoped=True, transient=True)."""
    builder = ContainerBuilder()
    builder.register(SharedDependency)  # singleton
    builder.register(ScopedTransientService, scoped=True, transient=True)

    async with builder.build() as container:
        async with container.scope() as scope:
            instance1 = await scope.get(ScopedTransientService)
            instance2 = await scope.get(ScopedTransientService)

            # Different instances (not cached)
            assert instance1 is not instance2
            # But shared singleton dependency
            assert instance1.dep is instance2.dep


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


@pytest.mark.anyio
async def test_diamond_dependency_with_mixed_scopes():
    """Test diamond dependency pattern with mixed scope types.

    Pattern from diamond.py:
    - A: singleton (scoped=False, transient=False)
    - B, C: singleton (depend on A)
    - D: transient (scoped=False, transient=True, depends on B and C)
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
    builder.register(A)  # singleton (default)
    builder.register(B)  # singleton (default)
    builder.register(C)  # singleton (default)
    builder.register(D, transient=True)  # transient

    async with builder.build() as container:
        # Request D multiple times
        d1 = await container.get(D)
        d2 = await container.get(D)

        # D is transient - different instances
        assert d1 is not d2

        # But both share the same B and C singletons
        assert d1.b is d2.b
        assert d1.c is d2.c

        # And B and C share the same A singleton
        assert d1.b.a is d1.c.a
        assert d2.b.a is d2.c.a
