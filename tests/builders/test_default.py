"""Tests for ContainerBuilder - Configuration Phase."""

import pytest


class SimpleService:
    """A simple service with no dependencies."""

    pass


class ServiceWithDependency:
    """A service that depends on SimpleService."""

    def __init__(self, simple: SimpleService):
        self.simple = simple


@pytest.mark.anyio
async def test_container_builder_can_register_service():
    """ContainerBuilder can register a service type."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    # Should not raise any exception
    assert True


@pytest.mark.anyio
async def test_container_builder_can_build_container():
    """ContainerBuilder can build a Container."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)

    async with builder.build() as container:
        # Container should exist
        assert container is not None


@pytest.mark.anyio
async def test_container_builder_register_with_scope():
    """ContainerBuilder can register a service with a specific scope."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService)
    builder.register(ServiceWithDependency, transient=True)

    # Should not raise any exception
    assert True


@pytest.mark.anyio
async def test_container_builder_register_with_custom_scope():
    """ContainerBuilder.register() creates ServiceDefinition with custom scope."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, scoped=True)

    # The builder should have stored the definition correctly
    # Access internal state to verify (this is a test, so it's acceptable)
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.service_type is SimpleService
    assert stored_def.scoped is True
    assert stored_def.transient is False


@pytest.mark.anyio
async def test_container_builder_register_with_name():
    """ContainerBuilder.register() supports name parameter."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, name="my_service")

    # Verify the name was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.name == "my_service"


@pytest.mark.anyio
async def test_container_builder_register_with_factory():
    """ContainerBuilder.register() supports factory parameter."""
    from hdmi import ContainerBuilder

    def create_simple_service():
        return SimpleService()

    builder = ContainerBuilder()
    builder.register(SimpleService, transient=True, factory=create_simple_service)

    # Verify the factory was preserved
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.factory is create_simple_service


@pytest.mark.anyio
async def test_container_builder_register_with_autowire_true():
    """ContainerBuilder.register() supports autowire parameter set to True."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, autowire=True)

    # Verify autowire was set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.autowire is True


@pytest.mark.anyio
async def test_container_builder_register_with_autowire_false():
    """ContainerBuilder.register() supports autowire parameter set to False."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(SimpleService, autowire=False)

    # Verify autowire was set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.autowire is False


@pytest.mark.anyio
async def test_container_builder_register_with_all_parameters():
    """ContainerBuilder.register() supports all ServiceDefinition parameters."""
    from hdmi import ContainerBuilder

    def create_simple_service():
        return SimpleService()

    builder = ContainerBuilder()
    builder.register(
        SimpleService,
        scoped=True,
        name="my_service",
        factory=create_simple_service,
        autowire=False,
    )

    # Verify all parameters were set correctly
    assert SimpleService in builder._definitions
    stored_def = builder._definitions[SimpleService]
    assert stored_def.scoped is True
    assert stored_def.transient is False
    assert stored_def.name == "my_service"
    assert stored_def.factory is create_simple_service
    assert stored_def.autowire is False


# Circular Dependency Detection Tests (Issue #1)
# Test fixtures for circular dependency scenarios


class ServiceA:
    """Service A that depends on ServiceB (creates A → B → A cycle)."""

    def __init__(self, b: "ServiceB"):
        self.b = b


class ServiceB:
    """Service B that depends on ServiceA (completes the cycle)."""

    def __init__(self, a: ServiceA):
        self.a = a


class ServiceX:
    """Service X that depends on ServiceY (part of indirect cycle X → Y → Z → X)."""

    def __init__(self, y: "ServiceY"):
        self.y = y


class ServiceY:
    """Service Y that depends on ServiceZ."""

    def __init__(self, z: "ServiceZ"):
        self.z = z


class ServiceZ:
    """Service Z that depends on ServiceX (completes the indirect cycle)."""

    def __init__(self, x: ServiceX):
        self.x = x


class SelfReferential:
    """Service that depends on itself."""

    def __init__(self, self_ref: "SelfReferential"):
        self.self_ref = self_ref


class ValidServiceA:
    """Valid service with no dependencies."""

    pass


class ValidServiceB:
    """Valid service that depends on ValidServiceA."""

    def __init__(self, a: ValidServiceA):
        self.a = a


class ValidServiceC:
    """Valid service that depends on ValidServiceB."""

    def __init__(self, b: ValidServiceB):
        self.b = b


class DiamondTop:
    """Top of diamond pattern."""

    pass


class DiamondLeft:
    """Left path of diamond."""

    def __init__(self, top: DiamondTop):
        self.top = top


class DiamondRight:
    """Right path of diamond."""

    def __init__(self, top: DiamondTop):
        self.top = top


class DiamondBottom:
    """Bottom of diamond (converges left and right paths)."""

    def __init__(self, left: DiamondLeft, right: DiamondRight):
        self.left = left
        self.right = right


@pytest.mark.anyio
async def test_valid_acyclic_dependencies_build_successfully():
    """Valid acyclic dependencies should build successfully."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(ValidServiceA)
    builder.register(ValidServiceB)
    builder.register(ValidServiceC)

    async with builder.build() as container:
        assert container is not None


@pytest.mark.anyio
async def test_diamond_pattern_is_valid():
    """Diamond pattern (shared dependencies) is valid and should build."""
    from hdmi import ContainerBuilder

    builder = ContainerBuilder()
    builder.register(DiamondTop)
    builder.register(DiamondLeft)
    builder.register(DiamondRight)
    builder.register(DiamondBottom)

    async with builder.build() as container:
        assert container is not None


@pytest.mark.anyio
async def test_direct_cycle_detected():
    """Direct cycle A → B → A raises CircularDependencyError."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    builder.register(ServiceA)
    builder.register(ServiceB)

    with pytest.raises(CircularDependencyError) as exc_info:
        builder.build()

    # Verify error message contains service names and indicates circular dependency
    error_msg = str(exc_info.value).lower()
    assert "servicea" in error_msg
    assert "serviceb" in error_msg
    assert "circular" in error_msg


@pytest.mark.anyio
async def test_indirect_cycle_detected_with_full_path():
    """Indirect cycle X → Y → Z → X raises CircularDependencyError with full path."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    builder.register(ServiceX)
    builder.register(ServiceY)
    builder.register(ServiceZ)

    with pytest.raises(CircularDependencyError) as exc_info:
        builder.build()

    # Verify error message shows the cycle
    error_msg = str(exc_info.value).lower()
    assert "servicex" in error_msg
    assert "circular" in error_msg


@pytest.mark.anyio
async def test_self_dependency_detected_immediately():
    """Self-dependency A → A raises CircularDependencyError."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    builder.register(SelfReferential)

    with pytest.raises(CircularDependencyError) as exc_info:
        builder.build()

    # Verify error message contains service name
    error_msg = str(exc_info.value).lower()
    assert "selfreferential" in error_msg
    assert "circular" in error_msg


@pytest.mark.anyio
async def test_cycle_with_singleton_scope():
    """Cycles are detected regardless of singleton scope."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    # Default registration is singleton (scoped=False, transient=False)
    builder.register(ServiceA)
    builder.register(ServiceB)

    with pytest.raises(CircularDependencyError):
        builder.build()


@pytest.mark.anyio
async def test_cycle_with_scoped_scope():
    """Cycles are detected regardless of scoped scope."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    builder.register(ServiceA, scoped=True)
    builder.register(ServiceB, scoped=True)

    with pytest.raises(CircularDependencyError):
        builder.build()


@pytest.mark.anyio
async def test_cycle_with_transient_scope():
    """Cycles are detected regardless of transient scope."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import CircularDependencyError

    builder = ContainerBuilder()
    builder.register(ServiceA, transient=True)
    builder.register(ServiceB, transient=True)

    with pytest.raises(CircularDependencyError):
        builder.build()
