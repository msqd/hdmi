"""Tests for hdmi.utils.typing module."""

from typing import Optional, Union


from hdmi.utils.typing import extract_type_from_optional


class DummyClass:
    """A dummy class for testing."""

    pass


class AnotherClass:
    """Another dummy class for testing."""

    pass


def test_extract_type_from_optional_with_union_none():
    """Extract type from Union[Type, None] (modern Optional syntax)."""
    result = extract_type_from_optional(str | None)
    assert result is str


def test_extract_type_from_optional_with_optional():
    """Extract type from Optional[Type] (old syntax)."""
    result = extract_type_from_optional(Optional[int])
    assert result is int


def test_extract_type_from_optional_with_plain_type():
    """Plain type without Optional returns the type itself."""
    result = extract_type_from_optional(str)
    assert result is str


def test_extract_type_from_optional_with_class():
    """Extract type from Optional with custom class."""
    result = extract_type_from_optional(DummyClass | None)
    assert result is DummyClass


def test_extract_type_from_optional_with_multiple_non_none_types():
    """Union with multiple non-None types returns None."""
    result = extract_type_from_optional(str | int)
    assert result is None


def test_extract_type_from_optional_with_three_way_union():
    """Union with three types (two non-None) returns None."""
    result = extract_type_from_optional(Union[str, int, None])
    assert result is None


def test_extract_type_from_optional_with_only_none():
    """Union with only None returns None."""
    result = extract_type_from_optional(type(None))
    assert result is type(None)
