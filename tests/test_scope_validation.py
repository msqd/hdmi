"""Tests for Scope Validation - Build-Time Safety.

Following TDD methodology, tests are written first to define behavior.

Scope hierarchy (highest to lowest):
- Singleton: One instance per container
- Scoped: One instance per scope
- Transient: New instance every time

Validation rules:
- Singleton can only depend on Singleton
- Scoped can depend on Singleton or Scoped
- Transient can depend on any scope
"""

import pytest


class SingletonService:
    """A singleton service."""

    def __init__(self):
        self.value = "singleton"


class ScopedService:
    """A scoped service."""

    def __init__(self):
        self.value = "scoped"


class TransientService:
    """A transient service."""

    def __init__(self):
        self.value = "transient"


class SingletonDependsOnSingleton:
    """Valid: Singleton → Singleton."""

    def __init__(self, dep: SingletonService):
        self.dep = dep


class ScopedDependsOnSingleton:
    """Valid: Scoped → Singleton."""

    def __init__(self, dep: SingletonService):
        self.dep = dep


class ScopedDependsOnScoped:
    """Valid: Scoped → Scoped."""

    def __init__(self, dep: ScopedService):
        self.dep = dep


class TransientDependsOnSingleton:
    """Valid: Transient → Singleton."""

    def __init__(self, dep: SingletonService):
        self.dep = dep


class TransientDependsOnScoped:
    """Valid: Transient → Scoped."""

    def __init__(self, dep: ScopedService):
        self.dep = dep


class TransientDependsOnTransient:
    """Valid: Transient → Transient."""

    def __init__(self, dep: TransientService):
        self.dep = dep


class SingletonDependsOnScoped:
    """Invalid: Singleton → Scoped (lifetime violation)."""

    def __init__(self, dep: ScopedService):
        self.dep = dep


class SingletonDependsOnTransient:
    """Invalid: Singleton → Transient (lifetime violation)."""

    def __init__(self, dep: TransientService):
        self.dep = dep


class ScopedDependsOnTransient:
    """Invalid: Scoped → Transient (lifetime violation)."""

    def __init__(self, dep: TransientService):
        self.dep = dep


# Valid dependency tests


@pytest.mark.anyio
async def test_singleton_can_depend_on_singleton():
    """Test that singleton services can depend on other singletons.

    This is valid because both have the same lifetime.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SingletonService, scope="singleton")
    builder.register(SingletonDependsOnSingleton, scope="singleton")

    # Should not raise ScopeViolationError
    async with builder.build() as container:
        service = await container.get(SingletonDependsOnSingleton)

        assert isinstance(service, SingletonDependsOnSingleton)
        assert isinstance(service.dep, SingletonService)


@pytest.mark.anyio
async def test_scoped_can_depend_on_singleton():
    """Test that scoped services can depend on singletons.

    This is valid because singleton outlives scoped.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SingletonService, scope="singleton")
    builder.register(ScopedDependsOnSingleton, scope="scoped")

    # Should not raise ScopeViolationError during build
    async with builder.build() as container:
        # Scoped services must be resolved through a scope
        async with container.scope() as scoped:
            service = await scoped.get(ScopedDependsOnSingleton)

            assert isinstance(service, ScopedDependsOnSingleton)
            assert isinstance(service.dep, SingletonService)


@pytest.mark.anyio
async def test_scoped_can_depend_on_scoped():
    """Test that scoped services can depend on other scoped services.

    This is valid because both have the same lifetime.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(ScopedService, scope="scoped")
    builder.register(ScopedDependsOnScoped, scope="scoped")

    # Should not raise ScopeViolationError during build
    async with builder.build() as container:
        # Scoped services must be resolved through a scope
        async with container.scope() as scoped:
            service = await scoped.get(ScopedDependsOnScoped)

            assert isinstance(service, ScopedDependsOnScoped)
            assert isinstance(service.dep, ScopedService)


@pytest.mark.anyio
async def test_transient_can_depend_on_any_scope():
    """Test that transient services can depend on any scope.

    This is valid because transient has the shortest lifetime.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SingletonService, scope="singleton")
    builder.register(ScopedService, scope="scoped")
    builder.register(TransientService, scope="transient")
    builder.register(TransientDependsOnSingleton, scope="transient")
    builder.register(TransientDependsOnScoped, scope="transient")
    builder.register(TransientDependsOnTransient, scope="transient")

    # Should not raise ScopeViolationError during build
    async with builder.build() as container:
        # Transient→singleton and transient→transient can be resolved from Container
        service1 = await container.get(TransientDependsOnSingleton)
        assert isinstance(service1, TransientDependsOnSingleton)

        service3 = await container.get(TransientDependsOnTransient)
        assert isinstance(service3, TransientDependsOnTransient)

        # Transient→scoped must be resolved through a scope
        async with container.scope() as scoped:
            service2 = await scoped.get(TransientDependsOnScoped)
            assert isinstance(service2, TransientDependsOnScoped)


# Invalid dependency tests


@pytest.mark.anyio
async def test_singleton_cannot_depend_on_scoped():
    """Test that singleton services cannot depend on scoped services.

    RED: This test will fail because scope validation isn't implemented yet.
    This is invalid because singleton would capture a scoped instance.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(ScopedService, scope="scoped")
    builder.register(SingletonDependsOnScoped, scope="singleton")

    # Should raise ScopeViolationError during build()
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "singleton" in str(exc_info.value).lower()
    assert "scoped" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_singleton_cannot_depend_on_transient():
    """Test that singleton services cannot depend on transient services.

    RED: This test will fail because scope validation isn't implemented yet.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(TransientService, scope="transient")
    builder.register(SingletonDependsOnTransient, scope="singleton")

    # Should raise ScopeViolationError during build()
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "singleton" in str(exc_info.value).lower()
    assert "transient" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_scoped_cannot_depend_on_transient():
    """Test that scoped services cannot depend on transient services.

    RED: This test will fail because scope validation isn't implemented yet.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(TransientService, scope="transient")
    builder.register(ScopedDependsOnTransient, scope="scoped")

    # Should raise ScopeViolationError during build()
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "scoped" in str(exc_info.value).lower()
    assert "transient" in str(exc_info.value).lower()


# Optional dependency scope validation tests


class SingletonWithOptionalTransient:
    """Singleton with optional transient dependency."""

    def __init__(self, *, dep: TransientService | None = None):
        self.dep = dep


@pytest.mark.anyio
async def test_singleton_with_unregistered_optional_transient_is_valid():
    """Singleton with optional transient dependency is valid when transient is NOT registered.

    Since the transient dependency is not registered, it won't be injected,
    so no scope violation should occur.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    # Note: TransientService is NOT registered
    builder.register(SingletonWithOptionalTransient, scope="singleton")

    # Should not raise ScopeViolationError
    async with builder.build() as container:
        service = await container.get(SingletonWithOptionalTransient)

        assert isinstance(service, SingletonWithOptionalTransient)
        assert service.dep is None  # Should use the default


@pytest.mark.anyio
async def test_singleton_with_optional_transient_autowire_false_is_valid():
    """Singleton with optional transient dependency is valid when autowire=False.

    Since autowire=False, the transient dependency won't be injected into the
    optional parameter, so no scope violation should occur.
    """
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(TransientService, scope="transient", autowire=False)
    builder.register(SingletonWithOptionalTransient, scope="singleton")

    # Should not raise ScopeViolationError
    async with builder.build() as container:
        service = await container.get(SingletonWithOptionalTransient)

        assert isinstance(service, SingletonWithOptionalTransient)
        assert service.dep is None  # Should use the default (not injected)


@pytest.mark.anyio
async def test_singleton_with_optional_transient_autowire_true_is_invalid():
    """Singleton with optional transient dependency is INVALID when autowire=True.

    Since autowire=True and the dependency is registered, it WILL be injected,
    so the scope violation should be caught.
    """
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    builder = ContainerBuilder()
    builder.register(TransientService, scope="transient", autowire=True)
    builder.register(SingletonWithOptionalTransient, scope="singleton")

    # Should raise ScopeViolationError during build()
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "singleton" in str(exc_info.value).lower()
    assert "transient" in str(exc_info.value).lower()
