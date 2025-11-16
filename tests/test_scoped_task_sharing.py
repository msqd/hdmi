"""Tests for task sharing in scoped containers."""

import asyncio

import pytest

from hdmi import ContainerBuilder


task_ids = {}


class ScopedSharedService:
    """A scoped service that multiple others depend on."""

    def __init__(self):
        current_task = asyncio.current_task()
        if current_task:
            task_ids["ScopedSharedService"] = task_ids.get("ScopedSharedService", [])
            task_ids["ScopedSharedService"].append(id(current_task))


class SingletonSharedService:
    """A singleton service that multiple scoped services depend on."""

    def __init__(self):
        current_task = asyncio.current_task()
        if current_task:
            task_ids["SingletonSharedService"] = task_ids.get("SingletonSharedService", [])
            task_ids["SingletonSharedService"].append(id(current_task))


class ScopedDependentA:
    """First scoped service depending on ScopedSharedService."""

    def __init__(self, shared: ScopedSharedService):
        self.shared = shared


class ScopedDependentB:
    """Second scoped service depending on ScopedSharedService."""

    def __init__(self, shared: ScopedSharedService):
        self.shared = shared


class ScopedDependentC:
    """Scoped service depending on SingletonSharedService."""

    def __init__(self, shared: SingletonSharedService):
        self.shared = shared


class ScopedDependentD:
    """Scoped service depending on SingletonSharedService."""

    def __init__(self, shared: SingletonSharedService):
        self.shared = shared


class ScopedRoot:
    """Root scoped service."""

    def __init__(self, a: ScopedDependentA, b: ScopedDependentB):
        self.a = a
        self.b = b


class ScopedRootWithSingleton:
    """Root scoped service depending on services that share a singleton."""

    def __init__(self, c: ScopedDependentC, d: ScopedDependentD):
        self.c = c
        self.d = d


@pytest.mark.anyio
async def test_scoped_shared_dependency_uses_same_task():
    """Scoped shared dependency should be resolved by a single task within a scope.

    This verifies that scoped services use their own _pending_tasks for scoped dependencies.
    """
    global task_ids
    task_ids = {}

    builder = ContainerBuilder()

    async def track_scoped_init(service: ScopedSharedService):
        await asyncio.sleep(0.01)

    builder.register(ScopedSharedService, scope="scoped", initializer=track_scoped_init)
    builder.register(ScopedDependentA, scope="scoped")
    builder.register(ScopedDependentB, scope="scoped")
    builder.register(ScopedRoot, scope="scoped")

    async with builder.build() as container:
        async with container.scope() as scoped:
            root = await scoped.get(ScopedRoot)

            # Verify same instance within scope
            assert root.a.shared is root.b.shared

            # Should use only one task
            assert len(task_ids.get("ScopedSharedService", [])) == 1, (
                f"Expected 1 task for ScopedSharedService, got {len(task_ids.get('ScopedSharedService', []))}"
            )


@pytest.mark.anyio
async def test_scoped_services_delegate_singleton_task_to_root():
    """Scoped services depending on singleton should use root container's task.

    This verifies that:
    - Singleton resolution is delegated to root container
    - Root container's _pending_tasks is used for singletons
    - Only one task created for singleton even when requested by multiple scoped services
    """
    global task_ids
    task_ids = {}

    builder = ContainerBuilder()

    async def track_singleton_init(service: SingletonSharedService):
        await asyncio.sleep(0.01)

    builder.register(SingletonSharedService, scope="singleton", initializer=track_singleton_init)
    builder.register(ScopedDependentC, scope="scoped")
    builder.register(ScopedDependentD, scope="scoped")
    builder.register(ScopedRootWithSingleton, scope="scoped")

    async with builder.build() as container:
        async with container.scope() as scoped:
            root = await scoped.get(ScopedRootWithSingleton)

            # Verify same singleton instance
            assert root.c.shared is root.d.shared

            # Should use only one task (from root container)
            assert len(task_ids.get("SingletonSharedService", [])) == 1, (
                f"Expected 1 task for SingletonSharedService, got {len(task_ids.get('SingletonSharedService', []))}"
            )


@pytest.mark.anyio
async def test_different_scopes_create_different_scoped_instances():
    """Different scopes should create different instances of scoped services."""
    global task_ids
    task_ids = {}

    builder = ContainerBuilder()
    builder.register(ScopedSharedService, scope="scoped")
    builder.register(ScopedDependentA, scope="scoped")

    async with builder.build() as container:
        async with container.scope() as scope1:
            service1 = await scope1.get(ScopedDependentA)

        # Clear task tracking for second scope
        task_ids.clear()

        async with container.scope() as scope2:
            service2 = await scope2.get(ScopedDependentA)

        # Different scopes should have different instances
        assert service1.shared is not service2.shared
