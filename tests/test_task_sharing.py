"""Tests for async task sharing during concurrent dependency resolution."""

import asyncio

import pytest

from hdmi import ContainerBuilder


# Track task creation
task_ids = {}


class SharedService:
    """A service that multiple others depend on."""

    def __init__(self):
        # Track which task created this instance
        current_task = asyncio.current_task()
        if current_task:
            task_ids["SharedService"] = task_ids.get("SharedService", [])
            task_ids["SharedService"].append(id(current_task))


class DependentA:
    """First service depending on SharedService."""

    def __init__(self, shared: SharedService):
        self.shared = shared


class DependentB:
    """Second service depending on SharedService."""

    def __init__(self, shared: SharedService):
        self.shared = shared


class Root:
    """Root service with diamond dependency."""

    def __init__(self, a: DependentA, b: DependentB):
        self.a = a
        self.b = b


@pytest.mark.anyio
async def test_singleton_shared_dependency_uses_same_task():
    """Singleton shared dependency should be resolved by a single task, not multiple tasks.

    This test verifies that when multiple services depend on the same singleton,
    only ONE async task is created to resolve it, even during concurrent resolution.

    Without task sharing:
    - DependentA resolution creates Task1 for SharedService
    - DependentB resolution creates Task2 for SharedService
    - Both tasks run concurrently, wasting resources

    With task sharing:
    - First request creates Task1 for SharedService
    - Second request reuses Task1
    - Only one task runs
    """
    global task_ids
    task_ids = {}

    builder = ContainerBuilder()

    # Add async initializer to make task tracking more reliable
    async def track_init(service: SharedService):
        await asyncio.sleep(0.01)  # Small delay to ensure task is trackable

    builder.register(SharedService, scope="singleton", initializer=track_init)
    builder.register(DependentA, scope="singleton")
    builder.register(DependentB, scope="singleton")
    builder.register(Root, scope="singleton")

    async with builder.build() as container:
        root = await container.get(Root)

        # Verify same instance
        assert root.a.shared is root.b.shared

        # The key test: SharedService should have been created by only ONE task
        # (currently fails - multiple tasks created)
        assert len(task_ids.get("SharedService", [])) == 1, (
            f"Expected 1 task for SharedService, but got {len(task_ids.get('SharedService', []))} tasks"
        )
