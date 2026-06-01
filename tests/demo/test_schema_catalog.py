"""Integration tests for the self-describing Layer B schema catalog (M2.5).

These pin the two demo claims that motivate the catalog design:

  1. Multi-media: ONE issuer key (comic-con-2026) signs and verifies BOTH a
     festival_pass and a wristband — different schemas, one operator.
  2. Shared schema: the SAME schema (festival_pass) is issued by TWO different
     operators (violet-fandom AND comic-con-2026) — one schema, many issuers.

Plus allowed_schemas data integrity across the registry and the catalog API.
"""
from __future__ import annotations

import cbor2
import pytest
from fastapi.testclient import TestClient

from demo.backend.main import app
from demo.backend import layer_b_codec as codec
from demo.backend import trust_registry


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _festival_dict() -> dict:
    return {
        "festival_id": "comic-con-2026",
        "serial": "F-2026-000777",
        "issued_at": "2026-07-01T00:00:00+00:00",
        "day": "Day 1 / Sat",
        "zone": "Hall A",
        "tier": "VIP",
        "gate": "Gate 7",
        "holder": "FAN-9981",
    }


def _wristband_dict() -> dict:
    return {
        "band_id": "comic-con-2026-band",
        "serial": "W-2026-000333",
        "issued_at": "2026-07-01T00:00:00+00:00",
        "tier": "3-day",
        "valid_until": "2026-07-03T23:59:59+00:00",
        "holder": "FAN-9981",
    }


def _issue_and_resolve(
    client: TestClient, issuer_id: str, schema: str, fmt: str, ticket: dict
) -> dict:
    """encode-layer-b(schema) → sign as issuer → encode → resolve(verified)."""
    layer_a = trust_registry.format_layer_a(issuer_id, f"{schema} entry")

    enc_b = client.post(
        "/api/encode-layer-b",
        json={"ticket": ticket, "format": fmt, "schema": schema},
    ).json()
    assert enc_b["schema"] == schema

    sig = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": enc_b["layer_b_hex"]},
    ).json()

    enc = client.post(
        "/api/encode",
        json={
            "layer_a": layer_a,
            "layer_b": enc_b["layer_b_hex"],
            "layer_c": sig["signature"],
        },
    ).json()

    return client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()


# ---------------------------------------------------------------------------
# Claim 1 — multi-media: one operator key, two schemas
# ---------------------------------------------------------------------------

def test_comic_con_signs_and_verifies_festival_pass(client: TestClient) -> None:
    r = _issue_and_resolve(
        client, "comic-con-2026", "festival_pass", "json", _festival_dict()
    )
    assert r["verified"] is True
    assert r["layer_b_schema"] == "festival_pass"
    assert r["layer_b_ticket"]["festival_id"] == "comic-con-2026"
    assert r["issuer_id"] == "comic-con-2026"


def test_comic_con_signs_and_verifies_wristband_aggressive(client: TestClient) -> None:
    """Same Comic Con key, different medium (wristband) in the byte-minimal
    aggressive format — multi-media under one operator."""
    r = _issue_and_resolve(
        client, "comic-con-2026", "wristband", "cbor_aggr", _wristband_dict()
    )
    assert r["verified"] is True
    assert r["layer_b_schema"] == "wristband"
    assert r["layer_b_ticket"]["valid_until"] == "2026-07-03T23:59:59+00:00"
    assert r["layer_b_format"] == "cbor_aggr"


def test_comic_con_two_schemas_decode_to_distinct_kinds(client: TestClient) -> None:
    """The same issuer's two media must NOT cross-decode — each token reports
    its own schema even though they share one signing key."""
    fest = _issue_and_resolve(
        client, "comic-con-2026", "festival_pass", "cbor_aggr", _festival_dict()
    )
    band = _issue_and_resolve(
        client, "comic-con-2026", "wristband", "cbor_aggr", _wristband_dict()
    )
    assert fest["layer_b_schema"] == "festival_pass"
    assert band["layer_b_schema"] == "wristband"
    assert "valid_until" not in fest["layer_b_ticket"]
    assert "festival_id" not in band["layer_b_ticket"]


# ---------------------------------------------------------------------------
# Claim 2 — shared schema: one schema, two operators
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("issuer_id", ["violet-fandom", "comic-con-2026"])
def test_festival_pass_shared_across_issuers(client: TestClient, issuer_id: str) -> None:
    """festival_pass is issued by both Violet and Comic Con — one schema, many
    operators, each verifying under its own key."""
    r = _issue_and_resolve(client, issuer_id, "festival_pass", "cbor", _festival_dict())
    assert r["verified"] is True
    assert r["layer_b_schema"] == "festival_pass"
    assert r["issuer_id"] == issuer_id


# ---------------------------------------------------------------------------
# Forgery resistance — a signed token relabeled to another schema must fail
# ---------------------------------------------------------------------------

def test_signed_token_relabeled_to_another_schema_fails_verification(
    client: TestClient,
) -> None:
    """End-to-end forgery invariant: take a validly signed festival_pass
    (aggressive) and flip its embedded schema_id 2→1 (baseball_ticket). The
    relabeled bytes would decode as baseball on their own, but the signature
    covers the whole Layer B byte string, so at `verified` level the mutation
    breaks the signature and Layer B collapses to None — no wrong-but-valid
    ticket survives."""
    issuer_id = "comic-con-2026"
    layer_a = trust_registry.format_layer_a(issuer_id, "festival_pass entry")

    # Authentic festival_pass Layer B (aggressive: body = {0: 2, ...}).
    raw = codec.encode_cbor_aggressive(codec.FestivalPass(**_festival_dict()))
    tag, body = raw[0], raw[1:]
    packed = cbor2.loads(body)
    assert packed[0] == 2  # festival_pass schema_id, as signed
    packed[0] = 1  # relabel → baseball_ticket
    tampered = bytes([tag]) + cbor2.dumps(packed, canonical=True)
    assert tampered != raw

    # Issuer signs the AUTHENTIC bytes; attacker swaps in the relabeled bytes.
    sig = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": raw.hex()},
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": tampered.hex(), "layer_c": sig["signature"]},
    ).json()
    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()

    assert r["verified"] is False
    assert r["layer_b_schema"] is None
    assert r["layer_b_ticket"] is None


# ---------------------------------------------------------------------------
# allowed_schemas data integrity
# ---------------------------------------------------------------------------

def test_allowed_schemas_registry_integrity() -> None:
    entries = {e.issuer_id: e for e in trust_registry.list_entries()}
    assert entries["tigers-2026"].allowed_schemas == ("baseball_ticket",)
    assert entries["violet-fandom"].allowed_schemas == ("festival_pass",)
    assert entries["comic-con-2026"].allowed_schemas == ("festival_pass", "wristband")


def test_allowed_schemas_reference_real_catalog_kinds(client: TestClient) -> None:
    """Every kind named in any issuer's allowed_schemas must exist in the
    catalog — guards against typos drifting the two sources apart."""
    catalog_kinds = {s["kind"] for s in client.get("/api/schemas").json()["schemas"]}
    for entry in trust_registry.list_entries():
        for kind in entry.allowed_schemas:
            assert kind in catalog_kinds, f"{entry.issuer_id} -> unknown {kind!r}"
