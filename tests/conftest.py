"""Pytest configuration for QoverwRap tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _enable_demo_trust_signing() -> None:
    """Allow ``/api/trust/{id}/sign`` in demo tests (guarded in production)."""
    os.environ["QWR_ENABLE_DEMO_SIGNING"] = "1"
    yield
