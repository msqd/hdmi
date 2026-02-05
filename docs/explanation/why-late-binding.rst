Why Late Binding?
=================

Late binding (or lazy instantiation) is a core design principle of **hdmi**. This document
explains why we chose this approach and how it benefits your applications.

What is Late Binding?
---------------------

**Late binding** means that services are instantiated only when they're first accessed,
not when the builder is configured or the container is built.

.. mermaid::

   graph LR
       subgraph "Early Binding (Eager)"
           E1[Configure] --> E2[Build]
           E2 --> E3[Instantiate ALL]
           E3 --> E4[Use Services]
       end

       subgraph "Late Binding (Lazy)"
           L1[Configure] --> L2[Build & Validate]
           L2 --> L3[Use Service A]
           L3 --> L4[Instantiate A only]
           L2 --> L5[Use Service B]
           L5 --> L6[Instantiate B only]
       end

       style E3 fill:#ffcccc
       style L4 fill:#ccffcc
       style L6 fill:#ccffcc

With early binding, all services are created upfront. With late binding, they're created on-demand.

Benefits of Late Binding
-------------------------

1. Faster Startup Time
~~~~~~~~~~~~~~~~~~~~~~

Applications start faster because services aren't created until needed:

.. code-block:: python

   import asyncio

   async def main():
       # With early binding: ALL services created here (slow!)
       container = builder.build()

       # With late binding: only validation happens (fast!)
       container = builder.build()

       # Services created only when accessed
       service = await container.get(MyService)  # <- instantiation happens here

   asyncio.run(main())

For applications with many services, this can significantly reduce startup time.

2. Lower Memory Footprint
~~~~~~~~~~~~~~~~~~~~~~~~~~

Services that are never used are never created:

.. code-block:: python

   import asyncio

   async def main():
       # Register many services
       builder.register(ServiceA)
       builder.register(ServiceB)
       builder.register(ServiceC)
       # ... 50 more services ...

       container = builder.build()

       # Only use one service
       service_a = await container.get(ServiceA)

       # ServiceB, ServiceC, and the other 50 services are never instantiated
       # Memory is conserved!

   asyncio.run(main())

This is especially valuable in:

- CLI applications (not all commands use all services)
- Testing (tests often use a subset of services)
- Microservices (different endpoints use different services)

3. Conditional Service Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Services can be created based on runtime conditions:

.. code-block:: python

   import asyncio

   async def main():
       container = builder.build()

       if user_wants_feature_x():
           # Service created only if feature is used
           feature_x = await container.get(FeatureXService)

       if environment == "production":
           # Different service for production
           monitor = await container.get(ProductionMonitor)
       else:
           # Different service for development
           monitor = await container.get(DevMonitor)

   asyncio.run(main())

4. Better Error Isolation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Errors in service constructors don't prevent the application from starting:

.. code-block:: python

   import asyncio

   async def main():
       # Build succeeds even if OptionalService has constructor issues
       container = builder.build()

       try:
           # Error only occurs if we actually try to use this service
           optional = await container.get(OptionalService)
       except Exception:
           # Handle gracefully - other services still work
           logger.warning("Optional feature unavailable")

       # Core services still work fine
       core = await container.get(CoreService)

   asyncio.run(main())

5. Circular Dependency Detection Without Full Instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Late binding allows us to validate the dependency graph without creating instances:

.. code-block:: python

   # These services have a circular dependency
   builder.register(ServiceA)  # depends on ServiceB
   builder.register(ServiceB)  # depends on ServiceA

   # Validation catches the cycle immediately
   container = builder.build()  # Raises CircularDependencyError

   # No services were instantiated!
   # The error is caught at graph-validation time, not instantiation time

Early Validation + Late Instantiation
--------------------------------------

The key insight of **hdmi** is that you can validate the dependency graph without instantiating services:

.. mermaid::

   graph TD
       Builder[ContainerBuilder<br/>Configuration] --> Build{.build}
       Build -->|Validation| CheckCycles[Check for cycles]
       CheckCycles --> CheckTypes[Check types]
       CheckTypes --> CheckResolvable[Check all resolvable]
       CheckResolvable --> Container[Container<br/>Validated Graph]

       Container -->|Later| Get{.get}
       Get --> Instantiate[Instantiate Service]

       style Build fill:#fff4e1
       style Instantiate fill:#e1ffe1

This gives you:

- **Safety**: All configuration errors detected at build time
- **Performance**: Services created only when needed
- **Flexibility**: Runtime decisions about which services to use

When Late Binding Isn't Appropriate
------------------------------------

Late binding isn't always the right choice. Consider early binding when:

1. **Fail-Fast is Critical**
   If you need to know immediately that all services can be instantiated successfully:

   .. code-block:: python

      import asyncio

      async def main():
          # With late binding, this succeeds even if services can't be created
          container = builder.build()

          # You might want to eagerly instantiate critical services
          await container.get(DatabaseConnection)  # Fail immediately if DB is down
          await container.get(ConfigService)       # Fail immediately if config is invalid

      asyncio.run(main())

2. **Warm-Up is Beneficial**
   For some services, instantiation is expensive and you want to do it upfront:

   .. code-block:: python

      import asyncio

      async def main():
          # Warm up expensive services during startup
          ml_model = await container.get(MachineLearningModel)  # Takes 30 seconds
          cache = await container.get(CacheService)             # Needs initialization

          # Now the services are ready for fast access

      asyncio.run(main())

3. **Deterministic Resource Allocation**
   When you need to know upfront what resources will be allocated:

   .. code-block:: python

      # Late binding makes it hard to predict memory usage
      # Early binding (or explicit instantiation) gives predictability

Comparison with Other Approaches
---------------------------------

======================  ====================  ====================  =====================
Approach                Startup Speed         Memory Usage          Error Detection
======================  ====================  ====================  =====================
Early Binding           Slow (all services)   High (all services)   All errors upfront
Late Binding (hdmi)     Fast (validation)     Low (on-demand)       Config errors early,
                                                                    instance errors late
Factory Pattern         Fast                  Low                   Deferred
Service Locator         Fast                  Low                   Runtime only
======================  ====================  ====================  =====================

**hdmi's approach** gives you the best of both worlds:

- Configuration errors are caught early (like early binding)
- Instantiation is deferred (like factory pattern)
- Services are typed and validated (unlike service locator)

Real-World Example
------------------

Consider a web application with these services:

.. code-block:: python

   from hdmi import ContainerBuilder

   # Configure all services
   builder = ContainerBuilder()
   builder.register(DatabaseConnection)
   builder.register(CacheService)
   builder.register(EmailService)
   builder.register(PaymentService)
   builder.register(AnalyticsService)
   builder.register(LoggingService)
   builder.register(MonitoringService)

   # Build container (validates, but doesn't instantiate)
   container = builder.build()  # < 1ms, all dependencies validated

   # Handle a simple GET request
   @app.get("/health")
   async def health():
       # Only LoggingService is instantiated
       logger = await container.get(LoggingService)
       logger.info("Health check")
       return {"status": "ok"}

   # Handle a payment request
   @app.post("/payment")
   async def payment():
       # Now PaymentService, DatabaseConnection are instantiated
       payment_service = await container.get(PaymentService)
       return payment_service.process()

Benefits in this scenario:

- Health check endpoint is very fast (doesn't initialize payment services)
- Each endpoint only pays for the services it uses
- All endpoints benefit from early validation of the dependency graph

Conclusion
----------

Late binding provides:

✅ Faster startup
✅ Lower memory usage
✅ Better error isolation
✅ More flexibility
✅ Still catches configuration errors early

The only tradeoff is that instantiation errors happen at first access, not at startup.
For most applications, this is an excellent tradeoff.
