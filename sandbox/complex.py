import asyncio

from hdmi import ContainerBuilder


class Config:
    def __init__(self):
        print(f"{type(self).__name__} < {id(self)} > :: __init__()")
        self.settings = {"app_name": "MyApp", "version": "1.0.0"}


class Context:
    def __init__(self, *, config: Config | None = None):
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


async def main():
    builder = ContainerBuilder()

    builder.register(Config)  # autowire=True by default
    builder.register(Context)
    builder.register(Something)

    async with builder.build() as container:
        something = await container.get(Something)
        print(something, something.context)
        print(f"Context's config: {something.context.config}")
        container_config = await container.get(Config)
        print(f"Container's config: {container_config}")
        print(f"Are they the same? {something.context.config is container_config}")


if __name__ == "__main__":
    asyncio.run(main())
