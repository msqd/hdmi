Architecture deep dive
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

Core components
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

The two phases
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

   # Register services using boolean flags for scope configuration
   builder.register(DatabaseConnection)  # singleton (default: scoped=False, transient=False)
   builder.register(UserRepository, scoped=True)  # scoped service
   builder.register(UserService, transient=True)  # transient service

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

Service resolution flow
-----------------------

.. mermaid::

   sequenceDiagram
       participant User
       participant Builder as ContainerBuilder
       participant Container
       participant ServiceA
       participant ServiceB

       User->>Builder: register(ServiceA)  # singleton (default)
       User->>Builder: register(ServiceB, scoped=True)  # scoped
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

Scope hierarchy and validation
-------------------------------

One of **hdmi**'s key features is **scope-aware dependency validation**. Services have
lifecycles (scopes) that determine when they are created and how long they live.

The four service types
~~~~~~~~~~~~~~~~~~~~~~

Services are configured using two boolean flags that combine to create four distinct types:

.. mermaid::

   graph TD
       Singleton[Singleton<br/>scoped=False, transient=False<br/>Cached in Container]
       Scoped[Scoped<br/>scoped=True, transient=False<br/>Cached in ScopedContainer]
       Transient[Transient<br/>scoped=False, transient=True<br/>Not cached, no scope required]
       ScopedTransient[Scoped Transient<br/>scoped=True, transient=True<br/>Not cached, requires scope]

       style Singleton fill:#e1ffe1
       style Scoped fill:#fff4e1
       style Transient fill:#ffe1e1
       style ScopedTransient fill:#f0e1ff

**Singleton** (scoped=False, transient=False - default)
   - Created once per container
   - Lives for the entire container lifetime
   - Ideal for: configurations, database connections, caches

**Scoped** (scoped=True, transient=False)
   - Created once per scope (e.g., per web request, per operation)
   - Lives for the duration of the scope
   - Ideal for: request-specific services, unit of work patterns

**Transient** (scoped=False, transient=True)
   - Created every time it's requested
   - No reuse across calls
   - Ideal for: stateful operations, disposable services

**Scoped Transient** (scoped=True, transient=True)
   - Created every time it's requested within a scope
   - Requires scope context but not cached
   - Ideal for: per-request commands, non-reusable scope-aware operations

Scope safety rules
~~~~~~~~~~~~~~~~~~

**Critical principle**: Non-scoped services cannot depend on scoped services.

The validation rules have been simplified: the only invalid dependency pattern is when
a non-scoped service (singleton or transient) attempts to depend on a scoped service,
because scoped services only exist within a scope context.

.. code-block:: python

   # ✅ VALID: Any service can depend on Singleton
   class Config:  # singleton (default)
       pass

   class Database:  # singleton
       def __init__(self, config: Config):
           self.config = config

   # ✅ VALID: Scoped depends on Singleton
   class RequestHandler:  # scoped
       def __init__(self, db: Database):  # Database is singleton
           self.db = db

   # ✅ VALID: Singleton can now depend on Transient
   class SingletonService:  # singleton
       def __init__(self, loader: ConfigLoader):  # ConfigLoader is transient
           # The transient is created once during singleton construction
           # and lives for the singleton's lifetime
           self.loader = loader

   # ✅ VALID: Scoped can depend on Transient
   class ScopedService:  # scoped
       def __init__(self, cmd: CommandProcessor):  # CommandProcessor is transient
           # The transient is created once per scoped instance
           self.cmd = cmd

   # ❌ INVALID: Singleton depends on Scoped
   class SingletonService:  # singleton
       def __init__(self, handler: RequestHandler):  # RequestHandler is scoped!
           # ERROR: Singleton cannot access scoped services
           # which only exist within a scope context
           self.handler = handler

   # ❌ INVALID: Transient depends on Scoped (when resolved from Container)
   class TransientService:  # transient (scoped=False)
       def __init__(self, handler: RequestHandler):  # RequestHandler is scoped!
           # ERROR: Non-scoped transient cannot depend on scoped services
           self.handler = handler

Validation matrix
~~~~~~~~~~~~~~~~~

This table shows which dependencies are allowed:

========================  ==================  ================  ==================  ====================
Service Type              Can Depend On
========================  ==================  ================  ==================  ====================
**Singleton**             ✅ Singleton        ❌ Scoped         ✅ Transient       ❌ Scoped Transient
**Scoped**                ✅ Singleton        ✅ Scoped         ✅ Transient       ✅ Scoped Transient
**Transient**             ✅ Singleton        ❌ Scoped         ✅ Transient       ❌ Scoped Transient
**Scoped Transient**      ✅ Singleton        ✅ Scoped         ✅ Transient       ✅ Scoped Transient
========================  ==================  ================  ==================  ====================

**Important note about transient dependencies:**

When a transient service is injected as a dependency, it's created **once** during the
dependent's construction and lives for the dependent's lifetime. This means:

- A singleton with a transient dependency gets one transient instance for its entire lifetime
- A scoped service with a transient dependency gets one transient instance per scope
- Direct requests for transient services still create new instances each time
  will outlive the service

Build-time validation
~~~~~~~~~~~~~~~~~~~~~

The **ContainerBuilder** catches scope violations during ``.build()``, not at runtime:

.. code-block:: python

   builder = ContainerBuilder()
   builder.register(SingletonService)  # singleton (default)
   builder.register(RequestHandler, scoped=True)  # scoped

   # ContainerBuilder validates during .build() and fails immediately:
   container = builder.build()  # Raises ScopeViolationError:
   # "SingletonService (singleton) cannot depend on RequestHandler (scoped)"

This "fail fast" approach ensures that lifetime bugs are caught during development
by the ContainerBuilder, not in production by the Container.

Type annotations and dependency discovery
------------------------------------------

**hdmi** uses Python's standard type annotations to discover dependencies automatically:

.. code-block:: python

   # Dependencies are inferred from type annotations
   class DatabaseConnection:
       def __init__(self):
           self.connected = True

   class UserRepository:
       def __init__(self, db: DatabaseConnection):
           self.db = db

   class UserService:
       def __init__(self, repo: UserRepository):
           self.repo = repo

   # Register with scopes using boolean flags
   builder = ContainerBuilder()
   builder.register(DatabaseConnection)  # singleton (default)
   builder.register(UserRepository, scoped=True)  # scoped service
   builder.register(UserService, transient=True)  # transient service

   container = builder.build()

When you register these services, **hdmi** automatically:

1. Inspects constructor signatures
2. Extracts type annotations
3. Builds the dependency graph
4. Validates scopes and cycles at ``.build()`` time

Lifecycle management
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

Design principles
-----------------

Early validation, late instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ContainerBuilder performs all validation during ``.build()``, producing an immutable
Container for runtime resolution. This separation ensures:

- **ContainerBuilder validates early**: Configuration errors (including scope violations) are
  caught immediately during ``.build()``
- **Container resolves late**: Services are instantiated only when ``.get()`` is called
- Memory is conserved by not creating unused services

Immutability after validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a Container is built, it's immutable. This ensures:

- Thread safety
- Predictable behavior
- No runtime surprises from configuration changes

Type-driven configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

By using Python's type annotations, we get:

- IDE autocomplete and type checking
- Self-documenting code
- Less boilerplate configuration
- Compile-time safety (with mypy/pyright)

Scope safety
~~~~~~~~~~~~

Scope validation prevents common lifetime bugs:

- Capturing short-lived services in long-lived ones
- Reusing transient services across operations
- Accessing disposed services

Simplicity over features
~~~~~~~~~~~~~~~~~~~~~~~~

Unlike the harp/rodi implementation, **hdmi** focuses on:

- Minimal API surface (ContainerBuilder, Container)
- No YAML configuration (Python-native)
- Standard library patterns
- Clear phase separation (configuration → validation/runtime)

Design philosophy
-----------------

**hdmi** follows a minimalist approach with just two core concepts:

.. code-block:: text

   hdmi architecture:
   ├── ContainerBuilder (configuration)
   ├── Container (validation + runtime resolution)
   └── ServiceDefinition (optional advanced configuration)

**Key design choices:**

- **Python-native configuration**: Use type annotations, no external DSLs
- **Two-phase architecture**: Clear separation between configuration and runtime
- **Build-time validation**: Catch all configuration errors before runtime
- **Minimal dependencies**: Standard library only, no external packages
- **Type-driven**: Leverage Python's typing system for safety and IDE support
- **Explicit over implicit**: Clear phase transitions and error messages

Error handling
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
