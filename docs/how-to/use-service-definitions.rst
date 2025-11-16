How to use service definition
==============================

This guide shows how to use the ``ServiceDefinition`` class for advanced service configuration.

When to use service definition
-------------------------------

Use ``ServiceDefinition`` when you need:

- Custom factory functions for service creation
- Named service registrations (for future multi-registration support)
- Pre-configured service definitions to share across modules
- More explicit control over service configuration

Basic usage
-----------

Creating a service definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hdmi import ServiceDefinition

   # Basic definition with scope
   definition = ServiceDefinition(MyService, scope="singleton")

   # Note: service_type must be positional, scope must be keyword
   # This will fail:
   # definition = ServiceDefinition(service_type=MyService)  # TypeError
   # definition = ServiceDefinition(MyService, "singleton")  # TypeError

Registering with container builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hdmi import ContainerBuilder, ServiceDefinition

   builder = ContainerBuilder()

   # Register a ServiceDefinition
   definition = ServiceDefinition(DatabaseService, scope="singleton")
   builder.register(definition)

   # IMPORTANT: Cannot specify scope when registering ServiceDefinition
   # This will raise ValueError:
   # builder.register(definition, scope="scoped")  # ValueError!

   # For simple registrations, use the shorthand:
   builder.register(UserService, scope="scoped")

Using custom factories
----------------------

ServiceDefinition allows you to provide a custom factory function:

.. code-block:: python

   from hdmi import ContainerBuilder, ServiceDefinition

   def create_database_connection():
       """Custom factory that configures the database."""
       return DatabaseConnection(
           host="localhost",
           port=5432,
           database="myapp"
       )

   # Create definition with factory
   db_definition = ServiceDefinition(
       DatabaseConnection,
       scope="singleton",
       factory=create_database_connection
   )

   builder = ContainerBuilder()
   builder.register(db_definition)

   container = builder.build()
   db = container.get(DatabaseConnection)  # Uses the factory

Factory requirements
~~~~~~~~~~~~~~~~~~~~

- Must be callable (function, method, or callable object)
- Must be passed as keyword argument
- Will be validated when ServiceDefinition is created

.. code-block:: python

   # Valid factories
   def factory_function():
       return MyService()

   definition = ServiceDefinition(MyService, factory=factory_function)

   # Invalid - not callable
   definition = ServiceDefinition(MyService, factory="not_callable")
   # Raises: ValueError: factory must be callable

Named services
--------------

ServiceDefinition supports named registrations for future multi-registration scenarios:

.. code-block:: python

   primary_db = ServiceDefinition(
       DatabaseConnection,
       scope="singleton",
       name="primary"
   )

   readonly_db = ServiceDefinition(
       DatabaseConnection,
       scope="singleton",
       name="readonly",
       factory=create_readonly_connection
   )

   builder = ContainerBuilder()
   builder.register(primary_db)
   builder.register(readonly_db)

.. note::
   Named service resolution is planned for future releases.
   Currently, names are stored but not used for resolution.

Exporting and importing definitions
------------------------------------

ServiceDefinition is now exported from the main hdmi package:

.. code-block:: python

   # Direct import from hdmi
   from hdmi import ServiceDefinition, ContainerBuilder

   # Create reusable definitions
   STANDARD_SERVICES = [
       ServiceDefinition(LoggingService, scope="singleton"),
       ServiceDefinition(ConfigService, scope="singleton"),
       ServiceDefinition(CacheService, scope="singleton"),
   ]

   # Use in multiple places
   def configure_container():
       builder = ContainerBuilder()
       for definition in STANDARD_SERVICES:
           builder.register(definition)
       return builder

Common patterns
---------------

Module-level definitions
~~~~~~~~~~~~~~~~~~~~~~~~

Define services at module level for reuse:

.. code-block:: python

   # services.py
   from hdmi import ServiceDefinition
   from myapp.database import DatabaseConnection
   from myapp.cache import RedisCache

   # Export pre-configured definitions
   database_definition = ServiceDefinition(
       DatabaseConnection,
       scope="singleton",
       factory=lambda: DatabaseConnection.from_env()
   )

   cache_definition = ServiceDefinition(
       RedisCache,
       scope="singleton",
       name="main_cache"
   )

   # main.py
   from hdmi import ContainerBuilder
   from services import database_definition, cache_definition

   builder = ContainerBuilder()
   builder.register(database_definition)
   builder.register(cache_definition)

Testing with ServiceDefinition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ServiceDefinition to override services in tests:

.. code-block:: python

   # test_services.py
   from hdmi import ContainerBuilder, ServiceDefinition

   def test_with_mock_database():
       # Create mock with custom factory
       mock_db_definition = ServiceDefinition(
           DatabaseConnection,
           scope="singleton",
           factory=lambda: MockDatabase()
       )

       builder = ContainerBuilder()
       builder.register(mock_db_definition)
       builder.register(UserService, scope="scoped")

       container = builder.build()
       # UserService will use the mock database

Best practices
--------------

1. **Use shorthand for simple registrations**: If you only need type and scope,
   use ``builder.register(Type, scope="...")`` directly.

2. **Use ServiceDefinition for complex scenarios**: When you need factories,
   names, or want to pre-configure definitions.

3. **Don't mix approaches**: When registering a ServiceDefinition, never
   provide a scope parameter to register().

4. **Validate early**: ServiceDefinition validates the factory parameter
   immediately, catching errors early.

5. **Group related definitions**: Create collections of related ServiceDefinitions
   that can be registered together.

See also
--------

- :doc:`/reference/api` for complete ServiceDefinition API
- :doc:`/explanation/architecture` for understanding service lifecycles
- :doc:`/tutorials/index` for step-by-step examples