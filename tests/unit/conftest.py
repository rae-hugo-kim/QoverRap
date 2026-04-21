"""Shared fixtures for Phase B unit tests."""
import pathlib

import pytest


@pytest.fixture
def tmp_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Isolated temporary directory per test."""
    return tmp_path
