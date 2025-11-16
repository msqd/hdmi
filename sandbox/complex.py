from hdmi import ContainerBuilder


class Config:
    def __init__(self):
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")
        self.settings = {"app_name": "MyApp", "version": "1.0.0"}


class Context:
    def __init__(self, *, config: Config = None):
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")
        self.data = {}
        self.config = config if config is not None else Config()

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)


class Something:
    def __init__(self, context: Context):
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")
        self.context = context


def main():
    builder = ContainerBuilder()

    # builder.register(Config)
    builder.register(Context)
    builder.register(Something)

    container = builder.build()

    something = container.get(Something)
    print(something, something.context)


if __name__ == "__main__":
    main()
