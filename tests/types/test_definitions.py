"""Tests for ServiceDefinition."""

import pytest

from hdmi.types.definitions import ServiceDefinition


class SimpleService:
    """A simple service for testing."""

    pass


def test_service_definition_basic_creation():
    """ServiceDefinition can be created with service_type and default flags."""
    definition = ServiceDefinition(SimpleService)

    assert definition.service_type is SimpleService
    assert definition.scoped is False  # singleton (default)
    assert definition.transient is False  # singleton (default)


def test_service_type_must_be_positional():
    """service_type parameter must be passed positionally, not as keyword."""
    with pytest.raises(TypeError, match="positional"):
        ServiceDefinition(service_type=SimpleService)  # type: ignore


def test_scoped_can_be_passed_as_keyword():
    """scoped parameter can be passed as a keyword argument."""
    definition = ServiceDefinition(SimpleService, scoped=True)

    assert definition.scoped is True
    assert definition.transient is False  # default


def test_transient_can_be_passed_as_keyword():
    """transient parameter can be passed as a keyword argument."""
    definition = ServiceDefinition(SimpleService, transient=True)

    assert definition.scoped is False  # default
    assert definition.transient is True


def test_both_flags_can_be_set():
    """Both scoped and transient flags can be set (scoped transient)."""
    definition = ServiceDefinition(SimpleService, scoped=True, transient=True)

    assert definition.scoped is True
    assert definition.transient is True


def test_name_defaults_to_none():
    """name parameter defaults to None when not provided."""
    definition = ServiceDefinition(SimpleService)

    assert definition.name is None


def test_name_can_be_provided():
    """name parameter can be provided as a keyword argument."""
    definition = ServiceDefinition(SimpleService, name="my_service")

    assert definition.name == "my_service"


def test_name_must_be_keyword():
    """name parameter must be passed as keyword, not positional."""
    with pytest.raises(TypeError):
        ServiceDefinition(SimpleService, False, False, "my_service")  # type: ignore


def test_factory_defaults_to_none():
    """factory parameter defaults to None when not provided."""
    definition = ServiceDefinition(SimpleService)

    assert definition.factory is None


def test_factory_can_be_provided():
    """factory parameter can be provided as a callable."""

    def create_service():
        return SimpleService()

    definition = ServiceDefinition(SimpleService, factory=create_service)

    assert definition.factory is create_service


def test_factory_must_be_keyword():
    """factory parameter must be passed as keyword, not positional."""

    def create_service():
        return SimpleService()

    with pytest.raises(TypeError):
        ServiceDefinition(SimpleService, False, False, None, create_service)  # type: ignore


def test_factory_must_be_callable():
    """factory parameter must be callable when provided."""
    with pytest.raises(ValueError, match="factory must be callable"):
        ServiceDefinition(SimpleService, factory="not_callable")  # type: ignore


def test_autowire_defaults_to_true():
    """autowire parameter defaults to True when not provided."""
    definition = ServiceDefinition(SimpleService)

    assert definition.autowire is True


def test_autowire_can_be_provided():
    """autowire parameter can be provided as a boolean."""
    definition = ServiceDefinition(SimpleService, autowire=False)

    assert definition.autowire is False


def test_autowire_must_be_keyword():
    """autowire parameter must be passed as keyword, not positional."""
    with pytest.raises(TypeError):
        ServiceDefinition(SimpleService, False, False, None, None, True)  # type: ignore


def test_async_factory_can_be_provided():
    """factory parameter can be an async callable."""

    async def create_service_async():
        return SimpleService()

    definition = ServiceDefinition(SimpleService, factory=create_service_async)

    assert definition.factory is create_service_async


def test_initializer_defaults_to_none():
    """initializer parameter defaults to None when not provided."""
    definition = ServiceDefinition(SimpleService)

    assert definition.initializer is None


def test_sync_initializer_can_be_provided():
    """initializer parameter can be a sync callable."""

    def init_service(service):
        service.initialized = True

    definition = ServiceDefinition(SimpleService, initializer=init_service)

    assert definition.initializer is init_service


def test_async_initializer_can_be_provided():
    """initializer parameter can be an async callable."""

    async def init_service_async(service):
        service.initialized = True

    definition = ServiceDefinition(SimpleService, initializer=init_service_async)

    assert definition.initializer is init_service_async


def test_finalizer_defaults_to_none():
    """finalizer parameter defaults to None when not provided."""
    definition = ServiceDefinition(SimpleService)

    assert definition.finalizer is None


def test_sync_finalizer_can_be_provided():
    """finalizer parameter can be a sync callable."""

    def cleanup_service(service):
        service.cleaned = True

    definition = ServiceDefinition(SimpleService, finalizer=cleanup_service)

    assert definition.finalizer is cleanup_service


def test_async_finalizer_can_be_provided():
    """finalizer parameter can be an async callable."""

    async def cleanup_service_async(service):
        service.cleaned = True

    definition = ServiceDefinition(SimpleService, finalizer=cleanup_service_async)

    assert definition.finalizer is cleanup_service_async
