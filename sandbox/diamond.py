import asyncio

from hdmi import ContainerBuilder

start_time = asyncio.get_event_loop().time()


def elapsed():
    return int(asyncio.get_event_loop().time() - start_time)


class A:
    def __init__(self):
        print(f"[{elapsed()}] {type(self).__name__} < {id(self)} > :: __init__()")


class B:
    def __init__(self, a: A):
        self.a = a
        print(f"[{elapsed()}] {type(self).__name__} < {id(self)} > :: __init__()")


class C:
    def __init__(self, a: A):
        self.a = a
        print(f"[{elapsed()}] {type(self).__name__} < {id(self)} > :: __init__()")


class D:
    def __init__(self, b: B, c: C):
        self.b = b
        self.c = c
        print(f"[{elapsed()}] {type(self).__name__} < {id(self)} > :: __init__()")


class E:
    def __init__(self, d: D):
        self.d = d
        print(f"[{elapsed()}] {type(self).__name__} < {id(self)} > :: __init__()")


async def slow(x):
    await asyncio.sleep(1)
    return x


async def bye(x):
    print(f"[{elapsed()}] {type(x).__name__} < {id(x)} > :: bye()")


async def main():
    builder = ContainerBuilder()
    builder.register(A, initializer=slow, finalizer=bye)
    builder.register(B, initializer=slow, finalizer=bye)
    builder.register(C, initializer=slow, finalizer=bye)
    builder.register(D, initializer=slow, finalizer=bye, scope="transient")
    builder.register(E, initializer=slow, finalizer=bye, scope="scoped")

    print("=== Resolving D multiple times from Container ===")
    async with builder.build() as container:
        tasks = [container.get(D) for _ in range(5)]
        instances = await asyncio.gather(*tasks)
        print(instances)

    print()
    print("=== Resolving D multiple times from ScopedContainer ===")
    async with builder.build() as container:
        async with container.scope() as scope:
            tasks = [scope.get(D) for _ in range(5)]
            instances = await asyncio.gather(*tasks)
            print(instances)

    print()
    print("=== Resolving E multiple times from ScopedContainer ===")
    async with builder.build() as container:
        async with container.scope() as scope:
            tasks = [scope.get(E) for _ in range(5)]
            instances = await asyncio.gather(*tasks)
            print(instances)


if __name__ == "__main__":
    asyncio.run(main())
