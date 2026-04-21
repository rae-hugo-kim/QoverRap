"""Shared fixtures for integration tests."""
from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def tmp_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Provide a temporary directory isolated per test."""
    return tmp_path
