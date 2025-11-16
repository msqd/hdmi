from hdmi import ContainerBuilder


class DatabaseService:
    def __init__(self):
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")


class UserRepository:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")


def main():
    print("=== Basic Registration (shorthand syntax) ===")
    builder = ContainerBuilder()

    # Shorthand registration with Type + scope
    builder.register(DatabaseService, scope="singleton")
    builder.register(UserRepository, scope="scoped")
    builder.register(UserService, scope="transient")

    container = builder.build()

    unscoped_database_service = container.get(DatabaseService)
    assert isinstance(unscoped_database_service, DatabaseService)

    with container.scope() as scope:
        user_service = scope.get(UserService)
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.user_repo, UserRepository)
        assert isinstance(user_service.user_repo.db_service, DatabaseService)

        user_service2 = scope.get(UserService)
        assert user_service is not user_service2  # transient - new instance
        assert user_service.user_repo is user_service2.user_repo  # scoped - same
        assert user_service.user_repo.db_service is user_service2.user_repo.db_service  # singleton - same

        assert user_service.user_repo.db_service is unscoped_database_service

    print("\n✅ All examples completed successfully!")


if __name__ == "__main__":
    main()
