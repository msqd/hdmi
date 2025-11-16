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

   .. automethod:: __init__
   .. automethod:: register
   .. automethod:: build

Container
~~~~~~~~~

.. autoclass:: hdmi.Container
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: get
   .. automethod:: scope

ServiceDefinition
~~~~~~~~~~~~~~~~~

.. autoclass:: hdmi.ServiceDefinition
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: __init__

   The ServiceDefinition class describes everything needed to know about a service:

   - **service_type**: The type/class to be registered (positional only)
   - **scope**: The lifecycle scope ("singleton", "scoped", or "transient")
   - **name**: Optional name for named registrations
   - **factory**: Optional factory callable for custom instantiation

   Example usage:

   .. code-block:: python

      from hdmi import ServiceDefinition, ContainerBuilder

      # Basic definition
      definition = ServiceDefinition(MyService, scope="singleton")

      # With custom factory
      def create_service():
          return MyService(custom_param="value")

      definition = ServiceDefinition(
          MyService,
          scope="scoped",
          factory=create_service
      )

      # Register with ContainerBuilder
      builder = ContainerBuilder()
      builder.register(definition)  # Note: no scope parameter when using ServiceDefinition

ScopedContainer
~~~~~~~~~~~~~~~

.. autoclass:: hdmi.ScopedContainer
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: get
   .. automethod:: __enter__
   .. automethod:: __exit__

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

Scope
~~~~~

.. code-block:: python

   from typing import Literal

   Scope = Literal["singleton", "scoped", "transient"]

Defines the three available service lifecycles:

- **singleton**: One instance per container
- **scoped**: One instance per scope
- **transient**: New instance every time

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
   builder.register(DatabaseService, scope="singleton")
   builder.register(UserRepository, scope="scoped")

   container = builder.build()

   # Singleton services can be accessed directly
   db = container.get(DatabaseService)

   # Scoped services require a scope context
   with container.scope() as scope:
       repo = scope.get(UserRepository)

Using service definition
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from hdmi import ContainerBuilder, ServiceDefinition

   # Create definitions with custom configuration
   db_definition = ServiceDefinition(
       DatabaseService,
       scope="singleton",
       name="primary_db"
   )

   # Register definitions (no scope parameter allowed)
   builder = ContainerBuilder()
   builder.register(db_definition)

   container = builder.build()

See also
--------

- :doc:`/explanation/architecture` for architectural overview
- :doc:`/how-to/index` for practical guides
- :doc:`/tutorials/index` for step-by-step tutorials