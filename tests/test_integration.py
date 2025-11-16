"""Integration tests - end-to-end scenarios.

These tests verify that the complete system works together correctly.
"""

import pytest


def test_complete_dependency_chain():
    """Test a complete dependency chain with multiple levels."""
    from hdmi import ContainerBuilder

    class Config:
        def __init__(self):
            self.setting = "production"

    class Database:
        def __init__(self, config: Config):
            self.config = config
            self.connected = True

    class Repository:
        def __init__(self, db: Database):
            self.db = db

    class Service:
        def __init__(self, repo: Repository):
            self.repo = repo

    # Build the container
    builder = ContainerBuilder()
    builder.register(Config, scope="singleton")
    builder.register(Database, scope="singleton")
    builder.register(Repository, scope="scoped")
    builder.register(Service, scope="transient")

    container = builder.build()

    # Service depends on scoped Repository, so must be resolved through a scope
    with container.scope() as scoped:
        service = scoped.get(Service)

        # Verify the entire chain is resolved
        assert isinstance(service, Service)
        assert isinstance(service.repo, Repository)
        assert isinstance(service.repo.db, Database)
        assert isinstance(service.repo.db.config, Config)
        assert service.repo.db.config.setting == "production"
        assert service.repo.db.connected


def test_singleton_sharing_across_transients():
    """Test that singletons are shared across multiple transient instances."""
    from hdmi import ContainerBuilder

    class SingletonCounter:
        instance_count = 0

        def __init__(self):
            SingletonCounter.instance_count += 1
            self.id = SingletonCounter.instance_count

    class TransientService:
        def __init__(self, counter: SingletonCounter):
            self.counter = counter

    # Reset counter
    SingletonCounter.instance_count = 0

    builder = ContainerBuilder()
    builder.register(SingletonCounter, scope="singleton")
    builder.register(TransientService, scope="transient")

    container = builder.build()

    # Create multiple transient instances
    service1 = container.get(TransientService)
    service2 = container.get(TransientService)
    service3 = container.get(TransientService)

    # Transient services are different
    assert service1 is not service2
    assert service2 is not service3

    # But they all share the same singleton
    assert service1.counter is service2.counter
    assert service2.counter is service3.counter
    assert service1.counter.id == 1  # Only one instance created
    assert SingletonCounter.instance_count == 1


def test_readme_example():
    """Test the example from README.md to ensure it actually works."""
    from hdmi import ContainerBuilder

    # Define your services
    class DatabaseConnection:
        def __init__(self):
            self.connected = True

    class UserRepository:
        def __init__(self, db: DatabaseConnection):
            self.db = db

    class UserService:
        def __init__(self, repo: UserRepository):
            self.repo = repo

    # Configure the container
    builder = ContainerBuilder()
    builder.register(DatabaseConnection, scope="singleton")
    builder.register(UserRepository, scope="scoped")
    builder.register(UserService, scope="transient")

    # Build validates the dependency graph
    container = builder.build()

    # UserService depends on scoped UserRepository, so must be resolved through a scope
    with container.scope() as scoped:
        user_service = scoped.get(UserService)

        # Verify it works
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.repo, UserRepository)
        assert isinstance(user_service.repo.db, DatabaseConnection)
        assert user_service.repo.db.connected


def test_scope_violation_example():
    """Test the scope violation example from README.md."""
    from hdmi import ContainerBuilder
    from hdmi.exceptions import ScopeViolationError

    class RequestHandler:
        def __init__(self):
            pass

    class SingletonService:
        def __init__(self, handler: RequestHandler):
            self.handler = handler

    builder = ContainerBuilder()
    builder.register(RequestHandler, scope="scoped")
    builder.register(SingletonService, scope="singleton")

    # Should raise ScopeViolationError
    with pytest.raises(ScopeViolationError) as exc_info:
        builder.build()

    assert "SingletonService" in str(exc_info.value)
    assert "RequestHandler" in str(exc_info.value)
    assert "singleton" in str(exc_info.value).lower()
    assert "scoped" in str(exc_info.value).lower()
