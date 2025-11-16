"""Tests for concurrent dependency resolution."""

import asyncio

import pytest

from hdmi import ContainerBuilder


class SlowServiceA:
    """Service that takes time to initialize."""

    def __init__(self):
        self.created_at: float | None = None


class SlowServiceB:
    """Another slow service."""

    def __init__(self):
        self.created_at: float | None = None


class ServiceWithTwoDependencies:
    """Service that depends on two independent services."""

    def __init__(self, dep_a: SlowServiceA, dep_b: SlowServiceB):
        self.dep_a = dep_a
        self.dep_b = dep_b


@pytest.mark.anyio
async def test_independent_dependencies_resolved_concurrently():
    """Independent dependencies are resolved concurrently for better performance."""
    builder = ContainerBuilder()

    # Track when each service is created
    creation_times = {}

    async def slow_init_a(service: SlowServiceA):
        await asyncio.sleep(0.1)  # Simulate slow initialization
        creation_times["A"] = asyncio.get_event_loop().time()
        service.created_at = creation_times["A"]

    async def slow_init_b(service: SlowServiceB):
        await asyncio.sleep(0.1)  # Simulate slow initialization
        creation_times["B"] = asyncio.get_event_loop().time()
        service.created_at = creation_times["B"]

    builder.register(SlowServiceA, initializer=slow_init_a)
    builder.register(SlowServiceB, initializer=slow_init_b)
    builder.register(ServiceWithTwoDependencies)

    async with builder.build() as container:
        start = asyncio.get_event_loop().time()
        service = await container.get(ServiceWithTwoDependencies)
        elapsed = asyncio.get_event_loop().time() - start

        # Both dependencies should have been created
        assert service.dep_a.created_at is not None
        assert service.dep_b.created_at is not None

        # If resolved sequentially: ~0.2s (0.1 + 0.1)
        # If resolved concurrently: ~0.1s (max(0.1, 0.1))
        # Allow some margin for overhead
        assert elapsed < 0.15, f"Expected concurrent resolution (<0.15s), but took {elapsed:.3f}s"

        # Verify both were created at approximately the same time
        time_diff = abs(creation_times["A"] - creation_times["B"])
        assert time_diff < 0.05, f"Dependencies should be created concurrently, but time diff was {time_diff:.3f}s"


@pytest.mark.anyio
async def test_dependent_services_resolved_in_order():
    """Dependent services are resolved in correct order (not concurrently)."""

    class ServiceA:
        def __init__(self):
            self.created_at: float | None = None

    class ServiceB:
        def __init__(self, dep_a: ServiceA):
            self.dep_a = dep_a
            self.created_at: float | None = None

    builder = ContainerBuilder()
    creation_times = {}

    async def init_a(service: ServiceA):
        await asyncio.sleep(0.05)
        creation_times["A"] = asyncio.get_event_loop().time()
        service.created_at = creation_times["A"]

    async def init_b(service: ServiceB):
        await asyncio.sleep(0.05)
        creation_times["B"] = asyncio.get_event_loop().time()
        service.created_at = creation_times["B"]

    builder.register(ServiceA, initializer=init_a)
    builder.register(ServiceB, initializer=init_b)

    async with builder.build() as container:
        _service = await container.get(ServiceB)

        # B should be created AFTER A (since B depends on A)
        assert creation_times["A"] < creation_times["B"]
        time_diff = creation_times["B"] - creation_times["A"]
        # Should take at least 0.05s between them (sequential)
        assert time_diff >= 0.04, f"B should be created after A completes, time diff: {time_diff:.3f}s"
