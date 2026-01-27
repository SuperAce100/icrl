"""Pytest configuration for ACME API tests.

This file configures pytest-asyncio and provides common fixtures.
"""

import pytest


# Configure pytest-asyncio to use auto mode
pytest_plugins = ["pytest_asyncio"]
