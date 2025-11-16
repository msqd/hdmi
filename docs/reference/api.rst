API reference
=============

Complete API documentation for the hdmi dependency injection framework.

Core classes
------------

ContainerBuilder
~~~~~~~~~~~~~~~~

.. autoclass:: hdmi.ContainerBuilder
   :members:
   :undoc-members:
   :show-inheritance:

Container
~~~~~~~~~

.. autoclass:: hdmi.Container
   :members:
   :undoc-members:
   :show-inheritance:

ServiceDefinition
~~~~~~~~~~~~~~~~~

.. autoclass:: hdmi.ServiceDefinition
   :members:
   :undoc-members:
   :show-inheritance:

   The ServiceDefinition class describes everything needed to know about a service:

   - **service_type**: The type/class to be registered (positional only)
   - **scoped**: Boolean flag indicating if the service is scoped (default: False)
   - **transient**: Boolean flag indicating if the service is transient (default: False)
   - **name**: Optional name for named registrations
   - **factory**: Optional factory callable for custom instantiation

   The combination of scoped and transient flags creates four service types:

   - **Singleton** (scoped=False, transient=False): One instance per container
   - **Scoped** (scoped=True, transient=False): One instance per scope
   - **Transient** (scoped=False, transient=True): New instance every time
   - **Scoped Transient** (scoped=True, transient=True): New instance every time, requires scope

   Example usage:

   .. code-block:: python

      from hdmi import ServiceDefinition, ContainerBuilder

      # Basic definition (singleton by default)
      definition = ServiceDefinition(MyService)

      # Scoped service
      scoped_definition = ServiceDefinition(MyService, scoped=True)

      # Transient service
      transient_definition = ServiceDefinition(MyService, transient=True)

      # With custom factory
      def create_service():
          return MyService(custom_param="value")

      definition = ServiceDefinition(
          MyService,
          scoped=True,
          factory=create_service
      )

      # Register with ContainerBuilder
      builder = ContainerBuilder()
      builder.register(definition)  # Note: no boolean flags when using ServiceDefinition

ScopedContainer
~~~~~~~~~~~~~~~

.. autoclass:: hdmi.ScopedContainer
   :members:
   :undoc-members:
   :show-inheritance:

Protocols
---------

IContainer
~~~~~~~~~~

.. autoclass:: hdmi.IContainer
   :members:
   :undoc-members:
   :show-inheritance:

   Protocol defining the interface for dependency injection containers.

Exceptions
----------

HDMIError
~~~~~~~~~

.. autoexception:: hdmi.HDMIError
   :members:
   :show-inheritance:

   Base exception for all hdmi-related errors.

CircularDependencyError
~~~~~~~~~~~~~~~~~~~~~~~

.. autoexception:: hdmi.CircularDependencyError
   :members:
   :show-inheritance:

   Raised when a circular dependency is detected during container build.

ScopeViolationError
~~~~~~~~~~~~~~~~~~~

.. autoexception:: hdmi.ScopeViolationError
   :members:
   :show-inheritance:

   Raised when a service depends on another service with a shorter lifetime.

UnresolvableDependencyError
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoexception:: hdmi.UnresolvableDependencyError
   :members:
   :show-inheritance:

   Raised when a required dependency cannot be resolved.

Type definitions
----------------

Service Types
~~~~~~~~~~~~~

Services are configured using two boolean flags that combine to create four distinct types:

.. code-block:: python

   # Singleton (default): scoped=False, transient=False
   builder.register(MyService)

   # Scoped: scoped=True, transient=False
   builder.register(MyService, scoped=True)

   # Transient: scoped=False, transient=True
   builder.register(MyService, transient=True)

   # Scoped Transient: scoped=True, transient=True
   builder.register(MyService, scoped=True, transient=True)

The four service types:

- **Singleton**: One instance per container (default)
- **Scoped**: One instance per scope
- **Transient**: New instance every time
- **Scoped Transient**: New instance every time, requires scope context

Public API summary
------------------

The main hdmi package exports the following:

.. code-block:: python

   from hdmi import (
       # Core classes
       ContainerBuilder,
       Container,
       ScopedContainer,
       ServiceDefinition,

       # Protocols
       IContainer,

       # Exceptions
       HDMIError,
       CircularDependencyError,
       ScopeViolationError,
       UnresolvableDependencyError,
   )

Usage examples
--------------

Basic registration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hdmi import ContainerBuilder

   builder = ContainerBuilder()
   builder.register(DatabaseService)  # singleton (default)
   builder.register(UserRepository, scoped=True)  # scoped service

   container = builder.build()

   # Singleton services can be accessed directly
   db = container.get(DatabaseService)

   # Scoped services require a scope context
   with container.scope() as scope:
       repo = scope.get(UserRepository)

Using service definition
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hdmi import ContainerBuilder, ServiceDefinition

   # Create definitions with custom configuration
   db_definition = ServiceDefinition(
       DatabaseService,
       name="primary_db"  # singleton by default
   )

   # Register definitions (no boolean flag parameters allowed)
   builder = ContainerBuilder()
   builder.register(db_definition)

   container = builder.build()

See also
--------

- :doc:`/explanation/architecture` for architectural overview
- :doc:`/how-to/index` for practical guides
- :doc:`/tutorials/index` for step-by-step tutorials