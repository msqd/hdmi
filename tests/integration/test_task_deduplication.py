"""Tests for task deduplication during concurrent dependency resolution."""

import pytest

from hdmi import ContainerBuilder


# Track how many times each service is instantiated
instantiation_counts = {}


class SharedDependency:
    """A service that multiple others depend on."""

    def __init__(self):
        instantiation_counts["SharedDependency"] = instantiation_counts.get("SharedDependency", 0) + 1


class ServiceB:
    """Service that depends on SharedDependency."""

    def __init__(self, shared: SharedDependency):
        self.shared = shared
        instantiation_counts["ServiceB"] = instantiation_counts.get("ServiceB", 0) + 1


class ServiceC:
    """Service that depends on SharedDependency."""

    def __init__(self, shared: SharedDependency):
        self.shared = shared
        instantiation_counts["ServiceC"] = instantiation_counts.get("ServiceC", 0) + 1


class ServiceA:
    """Service with diamond dependency: depends on B and C, which both depend on SharedDependency."""

    def __init__(self, b: ServiceB, c: ServiceC):
        self.b = b
        self.c = c
        instantiation_counts["ServiceA"] = instantiation_counts.get("ServiceA", 0) + 1


@pytest.mark.anyio
async def test_singleton_diamond_dependency_creates_shared_service_once():
    """When resolving diamond dependencies with singletons, shared service created only once.

    Scenario:
    - A depends on B and C
    - Both B and C depend on SharedDependency
    - All are singletons
    - Expected: SharedDependency instantiated exactly once (task reused)
    """
    global instantiation_counts
    instantiation_counts = {}

    builder = ContainerBuilder()
    builder.register(SharedDependency)
    builder.register(ServiceB)
    builder.register(ServiceC)
    builder.register(ServiceA)

    async with builder.build() as container:
        service_a = await container.get(ServiceA)

        # Verify structure is correct
        assert service_a.b.shared is service_a.c.shared  # Same instance

        # SharedDependency should be instantiated exactly once
        assert instantiation_counts["SharedDependency"] == 1
        assert instantiation_counts["ServiceB"] == 1
        assert instantiation_counts["ServiceC"] == 1
        assert instantiation_counts["ServiceA"] == 1


@pytest.mark.anyio
async def test_transient_diamond_dependency_creates_shared_service_multiple_times():
    """When resolving diamond dependencies with transients, each dependent gets its own instance.

    Scenario:
    - A depends on B and C
    - Both B and C depend on SharedDependency
    - All are transients
    - Expected: SharedDependency instantiated twice (separate tasks)
    """
    global instantiation_counts
    instantiation_counts = {}

    builder = ContainerBuilder()
    builder.register(SharedDependency, transient=True)
    builder.register(ServiceB, transient=True)
    builder.register(ServiceC, transient=True)
    builder.register(ServiceA, transient=True)

    async with builder.build() as container:
        service_a = await container.get(ServiceA)

        # Verify structure: different instances for transient
        assert service_a.b.shared is not service_a.c.shared  # Different instances

        # SharedDependency should be instantiated twice (once for B, once for C)
        assert instantiation_counts["SharedDependency"] == 2
        assert instantiation_counts["ServiceB"] == 1
        assert instantiation_counts["ServiceC"] == 1
        assert instantiation_counts["ServiceA"] == 1


@pytest.mark.anyio
async def test_mixed_scopes_singleton_shared_across_transients():
    """Singleton shared dependency should be instantiated once even when dependents are transient.

    Scenario:
    - A (transient) depends on B (transient) and C (transient)
    - Both B and C depend on SharedDependency (singleton)
    - Expected: SharedDependency instantiated once, B and C each instantiated once
    """
    global instantiation_counts
    instantiation_counts = {}

    builder = ContainerBuilder()
    builder.register(SharedDependency)
    builder.register(ServiceB, transient=True)
    builder.register(ServiceC, transient=True)
    builder.register(ServiceA, transient=True)

    async with builder.build() as container:
        service_a = await container.get(ServiceA)

        # Singleton should be same instance
        assert service_a.b.shared is service_a.c.shared

        # SharedDependency (singleton) should be instantiated once
        assert instantiation_counts["SharedDependency"] == 1
        # B and C (transient) should each be instantiated once
        assert instantiation_counts["ServiceB"] == 1
        assert instantiation_counts["ServiceC"] == 1
        assert instantiation_counts["ServiceA"] == 1
