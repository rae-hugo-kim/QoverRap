"""Shared fixtures for feasibility spike tests."""
import tempfile
import pathlib
import pytest


@pytest.fixture
def tmp_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Provide a temporary directory that is cleaned up after each test.

    Uses pytest's built-in tmp_path fixture so each test gets an isolated
    directory under the system temp area.
    """
    return tmp_path
