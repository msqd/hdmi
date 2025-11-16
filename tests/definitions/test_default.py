"""Tests for ServiceDefinition."""

import pytest

from hdmi.definitions import ServiceDefinition


class SimpleService:
    """A simple service for testing."""

    pass


def test_service_definition_basic_creation():
    """ServiceDefinition can be created with service_type and default scope."""
    definition = ServiceDefinition(SimpleService)

    assert definition.service_type is SimpleService
    assert definition.scope == "singleton"


def test_service_type_must_be_positional():
    """service_type parameter must be passed positionally, not as keyword."""
    with pytest.raises(TypeError, match="positional"):
        ServiceDefinition(service_type=SimpleService)  # type: ignore


def test_scope_can_be_passed_as_keyword():
    """scope parameter can be passed as a keyword argument."""
    definition = ServiceDefinition(SimpleService, scope="scoped")

    assert definition.scope == "scoped"


def test_scope_cannot_be_positional():
    """scope parameter cannot be passed as positional argument."""
    with pytest.raises(TypeError):
        ServiceDefinition(SimpleService, "scoped")  # type: ignore


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
        ServiceDefinition(SimpleService, "singleton", "my_service")  # type: ignore


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
        ServiceDefinition(SimpleService, "singleton", None, create_service)  # type: ignore


def test_factory_must_be_callable():
    """factory parameter must be callable when provided."""
    with pytest.raises(ValueError, match="factory must be callable"):
        ServiceDefinition(SimpleService, factory="not_callable")  # type: ignore
