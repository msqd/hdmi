"""Tests for allowing singleton and scoped services to depend on transient services.

These tests verify that longer-lived services (singleton, scoped) can safely
depend on transient services. The transient dependency is created once during
the dependent's construction and lives for the dependent's lifetime.
"""

import pytest

from hdmi import ContainerBuilder


class TransientDependency:
    """A transient service that others depend on."""

    def __init__(self):
        self.value = "transient"


class SingletonWithTransientDep:
    """Singleton service depending on a transient."""

    def __init__(self, dep: TransientDependency):
        self.dep = dep


class ScopedWithTransientDep:
    """Scoped service depending on a transient."""

    def __init__(self, dep: TransientDependency):
        self.dep = dep


@pytest.mark.anyio
async def test_singleton_can_depend_on_transient():
    """Singleton services should be able to depend on transient services.

    The transient dependency is created once during singleton construction
    and lives for the singleton's lifetime.
    """
    builder = ContainerBuilder()
    builder.register(TransientDependency, scope="transient")
    builder.register(SingletonWithTransientDep, scope="singleton")

    # Should build without validation errors
    async with builder.build() as container:
        singleton1 = await container.get(SingletonWithTransientDep)
        singleton2 = await container.get(SingletonWithTransientDep)

        # Same singleton instance
        assert singleton1 is singleton2

        # The transient dependency lives with the singleton
        assert singleton1.dep is singleton2.dep
        assert singleton1.dep.value == "transient"


@pytest.mark.anyio
async def test_scoped_can_depend_on_transient():
    """Scoped services should be able to depend on transient services.

    The transient dependency is created once per scoped instance and lives
    for that scoped instance's lifetime.
    """
    builder = ContainerBuilder()
    builder.register(TransientDependency, scope="transient")
    builder.register(ScopedWithTransientDep, scope="scoped")

    # Should build without validation errors
    async with builder.build() as container:
        async with container.scope() as scope1:
            scoped1a = await scope1.get(ScopedWithTransientDep)
            scoped1b = await scope1.get(ScopedWithTransientDep)

            # Same scoped instance within scope
            assert scoped1a is scoped1b
            # The transient dependency lives with the scoped instance
            assert scoped1a.dep is scoped1b.dep

        async with container.scope() as scope2:
            scoped2 = await scope2.get(ScopedWithTransientDep)

            # Different scoped instance in different scope
            assert scoped2 is not scoped1a
            # Different transient dependency
            assert scoped2.dep is not scoped1a.dep


@pytest.mark.anyio
async def test_transient_dependency_is_not_shared_across_direct_requests():
    """Transient services requested directly should still create new instances each time.

    This verifies that making transients valid dependencies doesn't break
    their transient behavior when requested directly.
    """
    builder = ContainerBuilder()
    builder.register(TransientDependency, scope="transient")

    async with builder.build() as container:
        # Each direct request creates a new instance
        trans1 = await container.get(TransientDependency)
        trans2 = await container.get(TransientDependency)

        assert trans1 is not trans2


@pytest.mark.anyio
async def test_singleton_still_cannot_depend_on_scoped():
    """Singleton services still cannot depend on scoped services.

    This is unsafe because the scoped service only exists within a scope,
    but the singleton lives for the entire container lifetime.
    """
    from hdmi.exceptions import ScopeViolationError

    class ScopedDependency:
        """A scoped service."""

        pass

    class SingletonWithScopedDep:
        """Singleton trying to depend on scoped."""

        def __init__(self, dep: ScopedDependency):
            self.dep = dep

    builder = ContainerBuilder()
    builder.register(ScopedDependency, scope="scoped")
    builder.register(SingletonWithScopedDep, scope="singleton")

    # Should raise validation error
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "SingletonWithScopedDep (singleton) cannot depend on ScopedDependency (scoped)" in str(exc_info.value)
