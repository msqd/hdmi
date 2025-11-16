"""Pytest configuration for hdmi tests."""

import pytest


@pytest.fixture
def anyio_backend():
    """Configure anyio to use only asyncio backend."""
    return "asyncio"
