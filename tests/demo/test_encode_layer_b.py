"""Tests for POST /api/encode-layer-b — codec-driven Layer B hex builder."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from demo.backend.layer_b_codec import (
    LAYER_B_TAG_CBOR,
    LAYER_B_TAG_CBOR_AGGR,
    LAYER_B_TAG_JSON,
)
from demo.backend.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _ticket_dict() -> dict:
    return {
        "event_id": "tigers-2026-042",
        "serial": "T-2026-000123",
        "issued_at": "2026-05-01T00:00:00+00:00",
        "section": "1루 응원석",
        "seat": "12B",
        "gate": "Gate 3",
        "datetime": "2026-05-10T09:30:00+00:00",
        "opponent": "Lions",
        "holder": "FAN-2456",
    }


def test_default_format_is_json(client: TestClient) -> None:
    r = client.post("/api/encode-layer-b", json={"ticket": _ticket_dict()})
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "json"
    assert data["byte_size"] > 0
    raw = bytes.fromhex(data["layer_b_hex"])
    assert raw[0] == LAYER_B_TAG_JSON
    assert len(raw) == data["byte_size"]


def test_cbor_format(client: TestClient) -> None:
    r = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "cbor"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "cbor"
    raw = bytes.fromhex(data["layer_b_hex"])
    assert raw[0] == LAYER_B_TAG_CBOR


def test_cbor_aggressive_format(client: TestClient) -> None:
    r = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "cbor_aggr"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "cbor_aggr"
    raw = bytes.fromhex(data["layer_b_hex"])
    assert raw[0] == LAYER_B_TAG_CBOR_AGGR


def test_format_size_ordering_via_api(client: TestClient) -> None:
    """JSON > CBOR > CBOR-aggr (matching unit-test gradient, exposed via API)."""
    t = _ticket_dict()
    sizes = {}
    for fmt in ("json", "cbor", "cbor_aggr"):
        r = client.post("/api/encode-layer-b", json={"ticket": t, "format": fmt})
        sizes[fmt] = r.json()["byte_size"]
    assert sizes["json"] > sizes["cbor"] > sizes["cbor_aggr"], sizes


def test_invalid_format_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "msgpack"},
    )
    assert r.status_code == 422  # pydantic Literal validation


def test_missing_required_ticket_field_rejected(client: TestClient) -> None:
    """Pydantic must surface schema validation errors with HTTP 422."""
    t = _ticket_dict()
    del t["event_id"]
    r = client.post("/api/encode-layer-b", json={"ticket": t, "format": "json"})
    assert r.status_code == 422
    body = r.json()
    # FastAPI surfaces pydantic errors under "detail"
    detail = body["detail"]
    if isinstance(detail, list):
        assert any("event_id" in str(item) for item in detail)
    else:
        assert "event_id" in str(detail)


def test_minimal_ticket_with_short_layer_a_fits_wristband(client: TestClient) -> None:
    """Sanity-check the wristband size claim from PRD §7.2 via the live API.

    With required-only fields + aggressive CBOR + short Layer A, the resulting
    payload must fit under ~150B (QR v8, ≈24mm @ 0.5mm/module).
    """
    minimal = {
        "event_id": "t26",
        "serial": "T123",
        "issued_at": "2026-05-01T00:00:00+00:00",
    }
    r = client.post(
        "/api/encode-layer-b",
        json={"ticket": minimal, "format": "cbor_aggr"},
    )
    assert r.status_code == 200
    # Layer B alone budget for wristband case
    assert r.json()["byte_size"] <= 30, r.json()
