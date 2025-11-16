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
    builder = ContainerBuilder()

    builder.register(DatabaseService, scope="singleton")
    builder.register(UserRepository, scope="scoped")
    builder.register(UserService, scope="transient")

    container = builder.build()

    user_service = container.get(UserService)
    assert isinstance(user_service, UserService)
    assert isinstance(user_service.user_repo, UserRepository)
    assert isinstance(user_service.user_repo.db_service, DatabaseService)

    user_service2 = container.get(UserService)
    assert user_service is not user_service2
    assert user_service.user_repo is user_service2.user_repo
    assert user_service.user_repo.db_service is user_service2.user_repo.db_service

if __name__ == "__main__":
    main()

