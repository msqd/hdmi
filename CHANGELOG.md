# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial implementation of dependency injection framework with type-driven configuration
- `ContainerBuilder` for service registration with lifecycle scopes
- `Container` for lazy service resolution at runtime
- Automatic dependency discovery from Python type annotations
- Comprehensive Sphinx documentation organized using Diátaxis framework
- Support for multi-level dependency chains with recursive resolution
- `IContainer` protocol for consistent container interface
- Static type checking with basedpyright
- `ServiceDefinition` class for declarative service configuration with optional factory and name support
- Support for custom factory functions to control service instantiation
- Named service registration for future multi-registration support
- **Scoped Transient services** - new service type requiring scope context but creating fresh instances per request
- Async container support with concurrent dependency resolution
- Service lifecycle hooks (initializers and finalizers)
- Task deduplication for diamond dependency patterns
- Boolean-based scope API with `scoped` and `transient` flags
- Circular dependency detection at build time with descriptive error messages showing the cycle path

### Changed

- Reorganized container implementation into `hdmi.containers` package for better modularity
- `ServiceDefinition` is now exported from main `hdmi` package for direct usage
- `ContainerBuilder.register()` now raises `ValueError` when both `ServiceDefinition` and `scope` parameter are provided
- `UnresolvableDependencyError` now extends `KeyError` for backward compatibility while providing clearer error messages
- Container resolution failures now raise `UnresolvableDependencyError` instead of raw `KeyError` with helpful guidance on how to fix the issue
- **BREAKING**: Replaced string-based `scope` parameter with boolean flags `scoped` and `transient` in `ContainerBuilder.register()`
  - Before: `builder.register(Service, scope="singleton|scoped|transient")`
  - After: `builder.register(Service, scoped=True/False, transient=True/False)`
- **BREAKING**: Relaxed scope validation - singleton and scoped services can now depend on transient services
  - Transient dependencies are instantiated once during dependent's construction
  - Only restriction: non-scoped services cannot depend on scoped services
- Reorganized package structure: `ServiceDefinition` moved to `hdmi.types.definitions`, type utilities to `hdmi.utils.typing`
