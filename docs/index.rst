hdmi - Lightweight DI for Python 3.13+
======================================

.. warning::

   **Pre-Alpha Software**

   hdmi is experimental software in active development. Breaking changes may occur
   until version 1.0. Use with care in production environments.

**hdmi** is a lightweight dependency injection framework with type-driven discovery and scope validation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorials/index
   how-to/index
   explanation/index
   reference/index

Features
--------

- **Type-Driven Dependencies**: Dependencies discovered automatically from Python type annotations
- **Two-Phase Architecture**: ContainerBuilder (configuration) → Container (validation & runtime)
- **Scope Safety**: Build-time validation prevents lifetime bugs (singleton → scoped, etc.)
- **Late Binding**: Services instantiated lazily (just-in-time) when first accessed
- **Early Validation**: Configuration errors caught at build time, not runtime
- **Async-First Design**: All service resolution is async for modern Python applications

Quick example
-------------

.. code-block:: python

   import asyncio
   from hdmi import ContainerBuilder

   async def main():
       # Phase 1: Configure services using boolean flags
       builder = ContainerBuilder()
       builder.register(DatabaseConnection)  # singleton (default)
       builder.register(UserRepository, scoped=True)  # scoped service
       builder.register(UserService, transient=True)  # transient service

       # Phase 2: Build & validate
       async with builder.build() as container:  # Validates scopes, cycles, dependencies

           # Phase 3: Resolve services (lazy instantiation)
           db = await container.get(DatabaseConnection)  # Singleton - accessible directly

           # Scoped services require a scope context
           async with container.scope() as scoped:
               repo = await scoped.get(UserRepository)

   asyncio.run(main())

Quick links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Current features
----------------

The framework currently supports:

- Service registration with four lifecycle types (singleton, scoped, transient, scoped transient)
- Automatic dependency resolution from type annotations
- Build-time scope validation to prevent lifetime bugs
- ServiceDefinition for advanced configuration (factories, named services)
- ScopedContainer for managing scoped service lifecycles
- Comprehensive error handling with descriptive messages

Development follows Test-Driven Development (TDD) methodology, ensuring robust
and well-tested implementation.
