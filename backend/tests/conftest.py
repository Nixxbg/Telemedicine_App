"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import asyncio
from collections.abc import Generator

import pytest

import src.models  # noqa: F401  # Ensure metadata tables are registered
from src.core.database import create_tables, drop_tables


@pytest.fixture(autouse=True, scope="function")
def reset_database() -> Generator[None, None, None]:
    """Reset the database before each test function.

    The contract tests rely on a pristine database so that the first request in a
    test can create records and later assertions can observe persisted state
    without interference from previous tests. We synchronously run the async table
    drop/create helpers to guarantee isolation for every test case.
    """

    asyncio.run(drop_tables())
    asyncio.run(create_tables())
    yield
