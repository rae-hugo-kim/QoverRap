"""TDD tests for visit-collection (stamp rally) — POST /api/visit/* (M2).

Boundary/limit-focused per project guidance: probe the edges of the core crypto
guarantees (forged-ticket refusal, tamper detection, deterministic binding token,
PII-absence) and the badge invariant — not the obvious happy path.

Each test uses an isolated in-memory SQLite store via the `visit_client` fixture,
mirroring test_redeem.py. The session-autouse fixture in conftest.py enables demo
signing. Helpers are defined locally (matching test_resolve_layer_b.py's style).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from demo.backend import trust_registry
from qoverwrap.decoder import decode_layers
from qoverwrap.encoder import encode_layers

SEOUL = "tigers-seoul-gate1"
BUSAN = "tigers-busan-gate1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sign_ticket(client: TestClient, issuer_id: str, message: str, layer_b: str = "") -> str:
    """Build a fully-signed, encoded ticket payload (the attendee's QR)."""
    layer_a = trust_registry.format_layer_a(issuer_id, message)
    sig = client.post(
        f"/api/trust/{issuer_id}/sign", json={"layer_a": layer_a, "layer_b": layer_b}
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b, "layer_c": sig["signature"]},
    ).json()
    return enc["encoded"]


def _forged_ticket(client: TestClient, issuer_id: str, message: str) -> str:
    """Ticket whose layer_b was changed after signing → signature is invalid."""
    layer_a = trust_registry.format_layer_a(issuer_id, message)
    sig = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": b"original".hex()},
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": b"tampered!".hex(), "layer_c": sig["signature"]},
    ).json()
    return enc["encoded"]


def _collect(client: TestClient, ticket: str, booth_id: str) -> dict:
    return client.post(
        "/api/visit/collect", json={"ticket_payload": ticket, "booth_id": booth_id}
    ).json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def visit_client() -> TestClient:
    """TestClient with a fresh in-memory SQLite store per test (shares redeem.get_store)."""
    import sqlite3

    from demo.backend.main import app
    from demo.backend.redemption_store import RedemptionStore
    from demo.backend.routers.redeem import get_store

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    store = RedemptionStore(conn=conn)

    app.dependency_overrides[get_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_store, None)


# ---------------------------------------------------------------------------
# Tests — trust model B: real member, really there
# ---------------------------------------------------------------------------

def test_forged_ticket_is_refused_and_store_untouched(visit_client: TestClient) -> None:
    """A ticket with an invalid signature cannot earn a badge, and the refusal must
    not touch the counter — a subsequent valid collect at the same booth still works."""
    forged = _forged_ticket(visit_client, "tigers-2026", "seat-A1")
    bad = _collect(visit_client, forged, SEOUL)
    assert bad["status"] == "ticket_invalid"
    assert bad["marker_payload"] is None

    valid = _sign_ticket(visit_client, "tigers-2026", "seat-A1")
    good = _collect(visit_client, valid, SEOUL)
    assert good["status"] == "collected"  # store was never poisoned by the forged attempt


def test_same_booth_revisit_is_already_collected(visit_client: TestClient) -> None:
    """One badge per (ticket × booth): the second collect of the same booth is blocked."""
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-B2")
    first = _collect(visit_client, ticket, SEOUL)
    second = _collect(visit_client, ticket, SEOUL)
    assert first["status"] == "collected"
    assert second["status"] == "already_collected"
    assert second["marker_payload"] is None


def test_different_booth_is_a_separate_badge(visit_client: TestClient) -> None:
    """booth_id differs → automatically a different badge (Seoul ≠ Busan), even for the
    same ticket. Only re-visiting the *same* booth is blocked."""
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-C3")
    assert _collect(visit_client, ticket, SEOUL)["status"] == "collected"
    assert _collect(visit_client, ticket, BUSAN)["status"] == "collected"
    assert _collect(visit_client, ticket, SEOUL)["status"] == "already_collected"


def test_marker_reverifies_offline(visit_client: TestClient) -> None:
    """The issued marker is a standalone wire-format payload — re-verifiable offline."""
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-D4")
    col = _collect(visit_client, ticket, SEOUL)
    res = visit_client.post(
        "/api/visit/verify", json={"marker_payload": col["marker_payload"]}
    ).json()
    assert res["verified"] is True
    assert res["booth_id"] == SEOUL
    assert res["visitor_token"] == col["visitor_token"]
    assert res["collection"] == "tigers-2026-stamprally"


def test_tampered_marker_fails_verification(visit_client: TestClient) -> None:
    """Flip one Layer B byte but keep the original signature → verification fails.
    Probes the core Ed25519 tamper-detection boundary for the marker itself."""
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-E5")
    col = _collect(visit_client, ticket, SEOUL)

    layer_a, layer_b, layer_c = decode_layers(col["marker_payload"])
    tampered_b = bytearray(layer_b)
    tampered_b[0] ^= 0x01
    tampered_marker = encode_layers(layer_a, bytes(tampered_b), layer_c)

    res = visit_client.post(
        "/api/visit/verify", json={"marker_payload": tampered_marker}
    ).json()
    assert res["verified"] is False


def test_visitor_token_is_deterministic_for_same_ticket(visit_client: TestClient) -> None:
    """Same ticket across different booths → identical visitor_token (binds the
    collection to one pseudonymous holder)."""
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-F6")
    a = _collect(visit_client, ticket, SEOUL)
    b = _collect(visit_client, ticket, BUSAN)
    assert a["visitor_token"] == b["visitor_token"]


def test_visitor_token_differs_across_tickets(visit_client: TestClient) -> None:
    """Different tickets (different layer_b → different signatures) → different tokens."""
    t1 = _sign_ticket(visit_client, "tigers-2026", "seat-G7", layer_b=b"seat:G7".hex())
    t2 = _sign_ticket(visit_client, "tigers-2026", "seat-G8", layer_b=b"seat:G8".hex())
    a = _collect(visit_client, t1, SEOUL)
    b = _collect(visit_client, t2, SEOUL)
    assert a["visitor_token"] != b["visitor_token"]


def test_marker_carries_no_pii(visit_client: TestClient) -> None:
    """Identity-blind: the marker echoes none of the ticket's PII — only the blind
    fields. Regression guard for '양자적 감정' (name/seat hidden, visit proven)."""
    ticket = _sign_ticket(
        visit_client,
        "tigers-2026",
        "VIP",
        layer_b=b'{"seat":"1A","holder":"Hong Gildong","serial":"T-42"}'.hex(),
    )
    col = _collect(visit_client, ticket, SEOUL)
    _, marker_b, _ = decode_layers(col["marker_payload"])
    data = json.loads(marker_b)

    assert set(data.keys()) == {
        "kind", "booth_id", "booth_name", "visitor_token", "visited_at", "collection",
    }
    blob = json.dumps(data, ensure_ascii=False)
    for leaked in ("Hong Gildong", "1A", "T-42", "holder", "serial"):
        assert leaked not in blob


def test_unknown_booth_returns_404(visit_client: TestClient) -> None:
    ticket = _sign_ticket(visit_client, "tigers-2026", "seat-H9")
    r = visit_client.post(
        "/api/visit/collect", json={"ticket_payload": ticket, "booth_id": "no-such-booth"}
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "unknown_booth"


def test_cross_event_ticket_is_rejected(visit_client: TestClient) -> None:
    """Issuer binding is fixed: a genuine Violet(IU-like) ticket cannot collect a
    Tigers booth — it's a real ticket, but for a different event → wrong_issuer.
    Distinct from ticket_invalid (which is for forged/unregistered tickets)."""
    violet_ticket = _sign_ticket(visit_client, "violet-fandom", "diamond-pass")
    res = _collect(visit_client, violet_ticket, SEOUL)  # SEOUL is a tigers-2026 booth
    assert res["status"] == "wrong_issuer"
    assert res["marker_payload"] is None


def test_holder_collects_the_booth_of_an_event_they_actually_hold(visit_client: TestClient) -> None:
    """No limit on events you actually bought a ticket for: a Violet ticket collects
    the Violet booth (its own event). One person can amass several event collections,
    each via that event's own ticket."""
    violet_ticket = _sign_ticket(visit_client, "violet-fandom", "diamond-pass")
    res = _collect(visit_client, violet_ticket, "violet-popup")  # violet-fandom booth
    assert res["status"] == "collected"
    assert res["collection"] == "violet-2026"
