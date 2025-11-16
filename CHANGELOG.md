# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial implementation of dependency injection framework with type-driven configuration
- `ContainerBuilder` for service registration with lifecycle scopes (singleton, scoped, transient)
- `Container` for lazy service resolution at runtime
- Build-time scope validation preventing lifetime bugs (singleton cannot depend on scoped/transient)
- Automatic dependency discovery from Python type annotations
- Comprehensive Sphinx documentation organized using Diátaxis framework
- Support for multi-level dependency chains with recursive resolution
- `IContainer` protocol for consistent container interface
- Static type checking with basedpyright
- `ServiceDefinition` class for declarative service configuration with optional factory and name support
- Support for custom factory functions to control service instantiation
- Named service registration for future multi-registration support

### Changed

- Reorganized container implementation into `hdmi.containers` package for better modularity
- `ServiceDefinition` is now exported from main `hdmi` package for direct usage
- `ContainerBuilder.register()` now raises `ValueError` when both `ServiceDefinition` and `scope` parameter are provided
