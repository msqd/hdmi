Architecture Deep Dive
======================

Overview
--------

**hdmi** is built around a simple two-phase architecture:

1. **ContainerBuilder**: Configuration phase - define services and their dependencies
2. **Container**: Runtime phase - lazily instantiate validated services on-demand

The **ContainerBuilder** performs all validation during the ``.build()`` call, producing
an immutable, validated **Container**. This separation ensures that configuration errors
are caught early (during build), while actual instantiation happens lazily (just-in-time)
when services are first accessed.

Core Components
---------------

.. mermaid::

   graph TB
       subgraph Configuration["🔧 Configuration Phase"]
           Builder[ContainerBuilder]
           Builder -->|register| Services[Service Definitions]
       end

       subgraph BuildValidation["✓ Build & Validation"]
           Services -->|.build| Validate{ContainerBuilder<br/>validates}
           Validate -->|checks| Graph[Dependency Graph]
           Validate -->|checks| Cycles[No Cycles]
           Validate -->|checks| Scopes[Scope Safety]
           Validate -->|ensures| Resolvable[All Resolvable]
           Validate -->|produces| Container[Container<br/>Validated & Immutable]
       end

       subgraph Runtime["⚡ Runtime Phase"]
           Container -->|.get| Instance[Service Instance]
           Instance -->|lazy| Dependencies[Dependent Services]
       end

       style Builder fill:#e1f5ff
       style Validate fill:#fff4e1
       style Container fill:#d4edda
       style Instance fill:#e1ffe1

The Two Phases
--------------

Phase 1: Configuration (ContainerBuilder)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **ContainerBuilder** is a mutable builder that accumulates service definitions. It's where you:

- Register service types
- Define dependencies (via type annotations)
- Configure lifecycles (singleton, scoped, transient)
- Set up factories and custom constructors

**Key characteristics:**

- Mutable: you can add/modify service definitions
- No validation yet: misconfiguration won't be detected
- Lightweight: just collecting configuration data

.. code-block:: python

   from hdmi import ContainerBuilder

   builder = ContainerBuilder()

   # Register services using type annotations with scopes
   builder.register(DatabaseConnection, scope="singleton")
   builder.register(UserRepository, scope="scoped")  # depends on DatabaseConnection
   builder.register(UserService, scope="transient")   # depends on UserRepository

Phase 2: Build & Validation (ContainerBuilder → Container)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you call ``builder.build()``, the **ContainerBuilder** performs all validation:

- Constructs the dependency graph
- Detects circular dependencies
- **Validates scope hierarchy** (ensures services only depend on same/higher scopes)
- Validates all dependencies can be resolved
- Checks type compatibility

If all validation passes, the ContainerBuilder produces a **Container** - an immutable,
validated dependency graph ready for runtime use.

**Container characteristics:**

- **Immutable**: the dependency graph cannot be modified after build
- **Pre-validated**: all configuration errors were caught during ``.build()``
- **No instances yet**: services aren't instantiated until ``.get()`` is called
- **Runtime-ready**: Used at runtime to lazily instantiate services on-demand

.. code-block:: python

   # ContainerBuilder validates during .build()
   container = builder.build()
   # ↑ All validation happens HERE, by the ContainerBuilder
   #   - Dependency graph constructed and validated
   #   - Cycles checked
   #   - Scope hierarchy validated
   #   - Type compatibility ensured

   # Container is now immutable and validated
   # At this point:
   # - All dependencies are validated ✓
   # - No cycles exist ✓
   # - Scope hierarchy is correct ✓
   # - No services are instantiated yet

   # Later, at runtime, Container just resolves:
   user_service = container.get(UserService)  # Lazy instantiation

Service Resolution Flow
-----------------------

.. mermaid::

   sequenceDiagram
       participant User
       participant Builder as ContainerBuilder
       participant Container
       participant ServiceA
       participant ServiceB

       User->>Builder: register(ServiceA, scope="singleton")
       User->>Builder: register(ServiceB, scope="scoped")
       Note over Builder: Configuration Phase<br/>No validation yet

       User->>Builder: build()
       Note over Builder: Builder validates:
       Builder->>Builder: construct dependency graph
       Builder->>Builder: check for cycles
       Builder->>Builder: validate scope hierarchy
       Builder->>Builder: ensure all resolvable
       Builder->>Container: create validated Container
       Note over Container: Immutable & Validated<br/>Graph is frozen
       Container-->>User: Container instance

       User->>Container: get(ServiceA)
       Container->>ServiceB: instantiate (dependency)
       ServiceB-->>Container: instance
       Container->>ServiceA: instantiate(ServiceB)
       ServiceA-->>Container: instance
       Container-->>User: ServiceA instance
       Note over User,ServiceA: Resolution Phase<br/>Lazy instantiation

Scope Hierarchy and Validation
-------------------------------

One of **hdmi**'s key features is **scope-aware dependency validation**. Services have
lifecycles (scopes) that determine when they are created and how long they live.

The Three Scopes
~~~~~~~~~~~~~~~~

.. mermaid::

   graph TD
       Singleton[Singleton<br/>Highest Scope<br/>One instance per container]
       Scoped[Scoped<br/>Middle Scope<br/>One instance per scope]
       Transient[Transient<br/>Lowest Scope<br/>New instance every time]

       Singleton -->|longer lifetime| Scoped
       Scoped -->|longer lifetime| Transient

       style Singleton fill:#e1ffe1
       style Scoped fill:#fff4e1
       style Transient fill:#ffe1e1

**Singleton** (Highest Scope)
   - Created once per container
   - Lives for the entire container lifetime
   - Ideal for: configurations, database connections, caches

**Scoped** (Middle Scope)
   - Created once per scope (e.g., per web request, per operation)
   - Lives for the duration of the scope
   - Ideal for: request-specific services, unit of work patterns

**Transient** (Lowest Scope)
   - Created every time it's requested
   - No reuse across calls
   - Ideal for: stateful operations, disposable services

Scope Safety Rules
~~~~~~~~~~~~~~~~~~

**Critical principle**: A service can only depend on services in the **same or higher scope**.

This prevents lifetime bugs where a long-lived service captures a reference to a
short-lived service.

.. code-block:: python

   # ✅ VALID: Singleton depends on Singleton
   class Config:  # singleton
       pass

   class Database:  # singleton
       def __init__(self, config: Config):  # Config is also singleton
           self.config = config

   # ✅ VALID: Scoped depends on Singleton
   class RequestHandler:  # scoped
       def __init__(self, db: Database):  # Database is singleton
           self.db = db

   # ✅ VALID: Transient depends on Scoped
   class CommandProcessor:  # transient
       def __init__(self, handler: RequestHandler):  # RequestHandler is scoped
           self.handler = handler

   # ❌ INVALID: Singleton depends on Scoped
   class SingletonService:  # singleton
       def __init__(self, handler: RequestHandler):  # RequestHandler is scoped!
           # ERROR: Singleton would capture a scoped instance
           # and hold it beyond the scope's lifetime
           self.handler = handler

   # ❌ INVALID: Scoped depends on Transient
   class ScopedService:  # scoped
       def __init__(self, cmd: CommandProcessor):  # CommandProcessor is transient!
           # ERROR: Scoped service would reuse a transient instance
           # across multiple calls
           self.cmd = cmd

Validation Matrix
~~~~~~~~~~~~~~~~~

This table shows which dependencies are allowed:

======================  ==================  ================  ==================
Service Scope           Can Depend On
======================  ==================  ================  ==================
**Singleton**           ✅ Singleton        ❌ Scoped         ❌ Transient
**Scoped**              ✅ Singleton        ✅ Scoped         ❌ Transient
**Transient**           ✅ Singleton        ✅ Scoped         ✅ Transient
======================  ==================  ================  ==================

**Why these rules?**

- **Longer-lived services cannot capture shorter-lived dependencies** because the
  dependency might be disposed while the service still exists
- **Shorter-lived services CAN depend on longer-lived ones** because the dependency
  will outlive the service

Build-Time Validation
~~~~~~~~~~~~~~~~~~~~~

The **ContainerBuilder** catches scope violations during ``.build()``, not at runtime:

.. code-block:: python

   builder = ContainerBuilder()
   builder.register(SingletonService, scope="singleton")
   builder.register(RequestHandler, scope="scoped")

   # ContainerBuilder validates during .build() and fails immediately:
   container = builder.build()  # Raises ScopeViolationError:
   # "SingletonService (singleton) cannot depend on RequestHandler (scoped)"

This "fail fast" approach ensures that lifetime bugs are caught during development
by the ContainerBuilder, not in production by the Container.

Type Annotations and Dependency Discovery
------------------------------------------

**hdmi** uses Python's standard type annotations to discover dependencies automatically:

.. code-block:: python

   from typing import Protocol

   class IDatabase(Protocol):
       def query(self, sql: str) -> list: ...

   class IRepository(Protocol):
       def find_user(self, id: int) -> User: ...

   # Dependencies are inferred from type annotations
   class UserRepository:
       def __init__(self, db: IDatabase):
           self.db = db

   class UserService:
       def __init__(self, repo: IRepository):
           self.repo = repo

   # Register with scopes
   builder = ContainerBuilder()
   builder.register(DatabaseConnection, implements=IDatabase, scope="singleton")
   builder.register(UserRepository, implements=IRepository, scope="scoped")
   builder.register(UserService, scope="transient")

   container = builder.build()

When you register these services, **hdmi** automatically:

1. Inspects constructor signatures
2. Extracts type annotations
3. Builds the dependency graph
4. Validates scopes and cycles at ``.build()`` time

Lifecycle Management
--------------------

Services behave differently based on their scope:

.. mermaid::

   graph LR
       subgraph Singleton["Singleton"]
           S1[Instance] --> S1
           S1 -.shared across all requests.-> S1
       end

       subgraph Scoped["Scoped"]
           SC1[Instance A<br/>Request 1]
           SC2[Instance B<br/>Request 2]
           SC1 -.shared within request 1.-> SC1
           SC2 -.shared within request 2.-> SC2
           SC1 -.different request.-> SC2
       end

       subgraph Transient["Transient"]
           T1[Instance 1]
           T2[Instance 2]
           T3[Instance 3]
           T1 -.new instance each time.-> T2
           T2 -.new instance each time.-> T3
       end

Example with Scopes:

.. code-block:: python

   # Singleton: Created once
   db = container.get(Database)
   db2 = container.get(Database)
   assert db is db2  # Same instance

   # Scoped: Created once per scope
   with container.create_scope() as scope:
       handler1 = scope.get(RequestHandler)
       handler2 = scope.get(RequestHandler)
       assert handler1 is handler2  # Same instance within scope

   with container.create_scope() as scope2:
       handler3 = scope2.get(RequestHandler)
       assert handler1 is not handler3  # Different instance in different scope

   # Transient: New instance every time
   cmd1 = container.get(CommandProcessor)
   cmd2 = container.get(CommandProcessor)
   assert cmd1 is not cmd2  # Always different instances

Design Principles
-----------------

Early Validation, Late Instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ContainerBuilder performs all validation during ``.build()``, producing an immutable
Container for runtime resolution. This separation ensures:

- **ContainerBuilder validates early**: Configuration errors (including scope violations) are
  caught immediately during ``.build()``
- **Container resolves late**: Services are instantiated only when ``.get()`` is called
- Memory is conserved by not creating unused services

Immutability After Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a Container is built, it's immutable. This ensures:

- Thread safety
- Predictable behavior
- No runtime surprises from configuration changes

Type-Driven Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

By using Python's type annotations, we get:

- IDE autocomplete and type checking
- Self-documenting code
- Less boilerplate configuration
- Compile-time safety (with mypy/pyright)

Scope Safety
~~~~~~~~~~~~

Scope validation prevents common lifetime bugs:

- Capturing short-lived services in long-lived ones
- Reusing transient services across operations
- Accessing disposed services

Simplicity Over Features
~~~~~~~~~~~~~~~~~~~~~~~~

Unlike the harp/rodi implementation, **hdmi** focuses on:

- Minimal API surface (ContainerBuilder, Container)
- No YAML configuration (Python-native)
- Standard library patterns
- Clear phase separation (configuration → validation/runtime)

Comparison with harp/rodi Implementation
-----------------------------------------

The harp implementation (based on rodi) has several layers:

.. code-block:: text

   harp/rodi architecture:
   ├── Container (extends rodi.Container)
   ├── ServiceDefinitionCollection (YAML-based)
   ├── ServiceDefinition (Pydantic models)
   ├── ServiceResolver (resolution logic)
   └── ServiceProvider (instance creation)

**hdmi** simplifies this to:

.. code-block:: text

   hdmi architecture:
   ├── ContainerBuilder (configuration)
   └── Container (validation + runtime resolution)

**Key differences:**

========================  ===================================  ============================
Aspect                    harp/rodi                            hdmi
========================  ===================================  ============================
Configuration             YAML + Pydantic models               Python type annotations
Naming                    Container/Provider                   ContainerBuilder/Container
Dependency discovery      Manual + annotations                 Pure type annotations
Validation phase          Implicit during resolution           Explicit at ``.build()``
Scope validation          Runtime checks                       Build-time validation
API complexity            Many classes and concepts            Two core concepts
External dependencies     rodi, pydantic                       Standard library only
========================  ===================================  ============================

Error Handling
--------------

.. mermaid::

   graph TD
       Start[Register Services] --> Build{build}
       Build -->|Success| Container[Container Created]
       Build -->|Cycle Detected| CycleError[CircularDependencyError]
       Build -->|Missing Dependency| MissingError[UnresolvableDependencyError]
       Build -->|Type Mismatch| TypeError[TypeResolutionError]
       Build -->|Scope Violation| ScopeError[ScopeViolationError]

       Container --> Get{get}
       Get -->|Success| Instance[Service Instance]
       Get -->|Instantiation Error| InstError[InstantiationError]

       style CycleError fill:#ffcccc
       style MissingError fill:#ffcccc
       style TypeError fill:#ffcccc
       style ScopeError fill:#ffcccc
       style InstError fill:#ffcccc

All configuration errors are detected at **build time**, not at runtime:

- **CircularDependencyError**: Service A depends on B, which depends on A
- **UnresolvableDependencyError**: Required dependency is not registered
- **TypeResolutionError**: Type annotation cannot be resolved
- **ScopeViolationError**: Service depends on a service with shorter lifetime (e.g., singleton → scoped)

Only instantiation errors occur at resolution time:

- **InstantiationError**: Constructor raised an exception

This ensures "fail fast" behavior - catch issues early during setup, not in production.
