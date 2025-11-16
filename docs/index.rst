hdmi - Dynamic Dependency Injection for Python
==============================================

**hdmi** is a dependency injection framework for Python that manages dynamic dependencies with late (just-in-time) resolution.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorials/index
   how-to/index
   reference/index
   explanation/index

Features
--------

- **Type-Driven Dependencies**: Dependencies discovered automatically from Python type annotations
- **Two-Phase Architecture**: ContainerBuilder (configuration) → Container (validation & runtime)
- **Scope Safety**: Build-time validation prevents lifetime bugs (singleton → scoped, etc.)
- **Late Binding**: Services instantiated lazily (just-in-time) when first accessed
- **Early Validation**: Configuration errors caught at build time, not runtime
- **Introspection Tools**: Inspect dependency graphs and resolution order at runtime

Quick example
-------------

.. code-block:: python

   from hdmi import ContainerBuilder

   # Phase 1: Configure services
   builder = ContainerBuilder()
   builder.register(DatabaseConnection, scope="singleton")
   builder.register(UserRepository, scope="scoped")
   builder.register(UserService, scope="transient")

   # Phase 2: Build & validate
   container = builder.build()  # Validates scopes, cycles, dependencies

   # Phase 3: Resolve services (lazy instantiation)
   db = container.get(DatabaseConnection)  # Singleton - accessible directly

   # Scoped services require a scope context
   with container.scope() as scope:
       service = scope.get(UserService)

Quick links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Current features
----------------

The framework currently supports:

- Service registration with lifecycle scopes (singleton, scoped, transient)
- Automatic dependency resolution from type annotations
- Build-time scope validation to prevent lifetime bugs
- ServiceDefinition for advanced configuration (factories, named services)
- ScopedContainer for managing scoped service lifecycles
- Comprehensive error handling with descriptive messages

Development follows Test-Driven Development (TDD) methodology, ensuring robust
and well-tested implementation.
