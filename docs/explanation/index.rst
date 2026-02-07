Explanation
===========

Understanding-oriented discussions about architecture and design decisions.

.. toctree::
   :maxdepth: 2

   architecture
   why-late-binding

What is hdmi?
-------------

**hdmi** is a lightweight dependency injection framework for Python 3.13+. It separates
configuration from validation/runtime, giving you:

- **Early error detection**: Configuration issues (cycles, scopes, missing deps) caught at build time
- **Lazy instantiation**: Services are created only when needed
- **Type-driven**: Uses Python's standard type annotations
- **Scope safety**: Prevents lifetime bugs at build time
- **Minimal boilerplate**: No decorators, no YAML, no complex configuration

Core Philosophy
---------------

**Fail Fast, Run Lazy**

Configuration errors (including scope violations) should be detected immediately when you
build the container. Service instantiation should happen as late as possible, only when
actually needed.

**Type Annotations as Truth**

The dependency graph is derived from Python's type annotations. If your type checker
is happy, hdmi will be happy. No separate configuration required.

**Scope Safety First**

Services can only depend on services with the same or longer lifetime. This prevents
common bugs like singletons capturing scoped instances.

**Simplicity by Design**

Two core concepts (ContainerBuilder, Container), one clear workflow (configure → build/validate → resolve).
No magic, no surprises, just straightforward dependency injection.

Design Principles
-----------------

1. **Late Resolution**: Services instantiated just-in-time, not eagerly
2. **Immutable Providers**: Once validated, the dependency graph is frozen
3. **Type-Driven**: Python type annotations define dependencies
4. **No External DSL**: Pure Python, no YAML/XML configuration required
5. **Minimal Overhead**: Lightweight and fast
6. **Async-First**: All service resolution is async for modern Python applications
