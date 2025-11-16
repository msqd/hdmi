#!/usr/bin/env python3
"""Demo script showing hdmi in action."""

from hdmi import ContainerBuilder, ScopeViolationError


# Define some example services
class Config:
    """Application configuration (singleton)."""

    def __init__(self):
        self.database_url = "postgresql://localhost/myapp"
        self.debug = True
        print(f"✓ Config created: debug={self.debug}")


class Database:
    """Database connection (singleton)."""

    def __init__(self, config: Config):
        self.config = config
        self.connected = True
        print(f"✓ Database connected to: {config.database_url}")


class UserRepository:
    """User data access (scoped - per request)."""

    def __init__(self, db: Database):
        self.db = db
        print("✓ UserRepository created with database")


class UserService:
    """User business logic (transient - new per use)."""

    def __init__(self, repo: UserRepository):
        self.repo = repo
        print("✓ UserService created with repository")

    def get_user(self, user_id: int):
        return f"User {user_id} from {self.repo.db.config.database_url}"


def demo_basic_usage():
    """Demonstrate basic dependency injection."""
    print("\n=== Demo 1: Basic Dependency Injection ===\n")

    # Configure the container
    builder = ContainerBuilder()
    builder.register(Config, scope="singleton")
    builder.register(Database, scope="singleton")
    builder.register(UserRepository, scope="scoped")
    builder.register(UserService, scope="transient")

    print("Building container (validates dependency graph)...")
    container = builder.build()
    print("✓ Container built successfully!\n")

    print("Getting UserService (triggers lazy instantiation)...")
    service1 = container.get(UserService)
    print(f"✓ Got service: {service1}\n")

    print("Getting another UserService (transient - new instance)...")
    service2 = container.get(UserService)
    print(f"✓ Got service: {service2}")

    print(f"\nTransient services are different: {service1 is not service2}")
    print(f"But they share the same singleton database: {service1.repo.db is service2.repo.db}")


def demo_scope_validation():
    """Demonstrate scope validation catching errors at build time."""
    print("\n\n=== Demo 2: Scope Validation (Build-Time Safety) ===\n")

    class RequestHandler:
        """Scoped service."""

        pass

    class CacheService:
        """Singleton trying to depend on scoped service (INVALID!)."""

        def __init__(self, handler: RequestHandler):
            self.handler = handler

    builder = ContainerBuilder()
    builder.register(RequestHandler, scope="scoped")
    builder.register(CacheService, scope="singleton")

    print("Trying to build container with invalid scope dependency...")
    print("(Singleton → Scoped is not allowed)\n")

    try:
        container = builder.build()
        print("❌ Should have raised ScopeViolationError!")
    except ScopeViolationError as e:
        print("✓ Caught error at BUILD time (not runtime):")
        print(f"  {e}\n")
        print("This prevents lifetime bugs from reaching production!")


def demo_lazy_instantiation():
    """Demonstrate that services are created lazily."""
    print("\n\n=== Demo 3: Lazy Instantiation ===\n")

    class ServiceA:
        def __init__(self):
            print("  → ServiceA instantiated")

    class ServiceB:
        def __init__(self):
            print("  → ServiceB instantiated")

    builder = ContainerBuilder()
    builder.register(ServiceA, scope="singleton")
    builder.register(ServiceB, scope="singleton")

    print("Building container...")
    container = builder.build()
    print("✓ Container built (no services instantiated yet)\n")

    print("Requesting ServiceA...")
    service_a = container.get(ServiceA)
    print("✓ Got ServiceA\n")

    print("ServiceB was NOT instantiated (it wasn't requested)")
    print("This saves memory and startup time!")


if __name__ == "__main__":
    demo_basic_usage()
    demo_scope_validation()
    demo_lazy_instantiation()

    print("\n\n=== All Demos Completed Successfully! ===\n")
