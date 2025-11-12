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

Quick Example
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
   service = container.get(UserService)

Quick Links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Project Status
--------------

This project is currently in the **specification phase**. We are focusing on:

1. Defining the API and behavior through tests (TDD methodology)
2. Documenting the architecture and design decisions
3. Creating examples demonstrating the type-annotation-based API

Implementation will follow once the specification is solid.
