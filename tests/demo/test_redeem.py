"""TDD tests for POST /api/redeem — one-time-use ticket counter (M1).

Each test uses an isolated in-memory SQLite DB via the `redeem_client` fixture.
The trust registry keys are generated fresh per process (see trust_registry.py),
so we sign payloads through /api/trust/{id}/sign, then redeem them.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from demo.backend import trust_registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signed_payload(client: TestClient, issuer_id: str, message: str, layer_b: str = "") -> str:
    """Build a fully-signed, encoded QR payload for the given issuer."""
    layer_a = trust_registry.format_layer_a(issuer_id, message)
    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": layer_b},
    ).json()
    layer_c_hex = sig_resp["signature"]
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b, "layer_c": layer_c_hex},
    ).json()
    return enc["encoded"]


def _make_tampered_payload(client: TestClient, issuer_id: str, message: str) -> str:
    """Build a payload where the signature is wrong (layer_b changed after signing)."""
    layer_a = trust_registry.format_layer_a(issuer_id, message)
    layer_b_original = b"original".hex()
    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": layer_b_original},
    ).json()
    layer_c_hex = sig_resp["signature"]
    # Tamper: different layer_b but keep original signature → invalid
    tampered_b = b"tampered!".hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": tampered_b, "layer_c": layer_c_hex},
    ).json()
    return enc["encoded"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def redeem_client(tmp_path) -> TestClient:
    """TestClient with a fresh in-memory SQLite redemption store per test."""
    import sqlite3
    from demo.backend.redemption_store import RedemptionStore
    from demo.backend.main import app
    from demo.backend.routers import redeem as redeem_router

    db_path = ":memory:"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    store = RedemptionStore(conn=conn)

    # Override the store on the router so tests use isolated DB
    redeem_router._store = store  # noqa: SLF001

    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_first_redeem_is_ok(redeem_client: TestClient) -> None:
    """First use of a valid signed payload returns ok with use_count=1."""
    payload = _make_signed_payload(redeem_client, "tigers-2026", "seat-A1")
    r = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["use_count"] == 1


def test_second_redeem_with_max_uses_1_is_already_used(redeem_client: TestClient) -> None:
    """max_uses=1: second redeem of identical payload → already_used, counter not incremented."""
    payload = _make_signed_payload(redeem_client, "tigers-2026", "seat-B2")
    redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 1})
    r = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "already_used"
    assert data["use_count"] == 1  # did not increment


def test_max_uses_2_allows_two_redeems(redeem_client: TestClient) -> None:
    """max_uses=2: first two redeems ok, third → already_used."""
    payload = _make_signed_payload(redeem_client, "violet-fandom", "vip-pass")
    r1 = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 2})
    assert r1.json()["status"] == "ok"
    assert r1.json()["use_count"] == 1

    r2 = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 2})
    assert r2.json()["status"] == "ok"
    assert r2.json()["use_count"] == 2

    r3 = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 2})
    assert r3.json()["status"] == "already_used"
    assert r3.json()["use_count"] == 2  # did not increment


def test_tampered_signature_returns_invalid(redeem_client: TestClient) -> None:
    """Payload with invalid signature → invalid; counter is not touched."""
    payload = _make_tampered_payload(redeem_client, "tigers-2026", "seat-C3")
    r = redeem_client.post("/api/redeem", json={"payload": payload, "max_uses": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "invalid"
    assert data["use_count"] == 0


def test_tampered_does_not_increment_counter(redeem_client: TestClient) -> None:
    """A tampered redeem attempt leaves a later valid redeem unaffected."""
    # First, a tampered attempt
    tampered = _make_tampered_payload(redeem_client, "tigers-2026", "seat-D4")
    redeem_client.post("/api/redeem", json={"payload": tampered, "max_uses": 1})

    # A valid payload for the same issuer (different signature → different counter key)
    valid = _make_signed_payload(redeem_client, "tigers-2026", "seat-D4-valid")
    r = redeem_client.post("/api/redeem", json={"payload": valid, "max_uses": 1})
    assert r.json()["status"] == "ok"
    assert r.json()["use_count"] == 1


def test_different_seat_different_counter(redeem_client: TestClient) -> None:
    """Two distinct payloads (different layer_b → different signatures) have independent counters."""
    # seat E5 and E6 — different layer_b content so different Ed25519 signatures
    payload_e5 = _make_signed_payload(
        redeem_client, "tigers-2026", "seat-E5", layer_b=b"seat:E5".hex()
    )
    payload_e6 = _make_signed_payload(
        redeem_client, "tigers-2026", "seat-E6", layer_b=b"seat:E6".hex()
    )

    r_e5 = redeem_client.post("/api/redeem", json={"payload": payload_e5, "max_uses": 1})
    assert r_e5.json()["status"] == "ok"
    assert r_e5.json()["use_count"] == 1

    # E6 has its own fresh counter
    r_e6 = redeem_client.post("/api/redeem", json={"payload": payload_e6, "max_uses": 1})
    assert r_e6.json()["status"] == "ok"
    assert r_e6.json()["use_count"] == 1

    # Second attempt on E5 → already used
    r_e5_dup = redeem_client.post("/api/redeem", json={"payload": payload_e5, "max_uses": 1})
    assert r_e5_dup.json()["status"] == "already_used"


def test_concurrent_redeem_only_one_succeeds() -> None:
    """Hammer the store directly from N threads — exactly one ok, rest already_used.

    We exercise RedemptionStore.redeem directly (not via TestClient) because
    TestClient is not guaranteed thread-safe. The race lives in the store,
    which is what we need to verify is atomic.
    """
    import sqlite3
    import threading

    from demo.backend.redemption_store import RedemptionStore

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    store = RedemptionStore(conn=conn)

    sig = "deadbeef" * 16  # fake 64-byte signature (hex)
    n_threads = 16
    results: list[tuple[str, int]] = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(n_threads)

    def hammer() -> None:
        barrier.wait()
        status, count = store.redeem(sig, max_uses=1)
        with results_lock:
            results.append((status, count))

    threads = [threading.Thread(target=hammer) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok_count = sum(1 for s, _ in results if s == "ok")
    already = sum(1 for s, _ in results if s == "already_used")
    assert ok_count == 1, f"expected exactly 1 ok, got {ok_count}: {results}"
    assert already == n_threads - 1, f"expected {n_threads - 1} already_used: {results}"
    # No thread should observe use_count > 1 — that would mean overshoot.
    assert all(c == 1 for _, c in results), results
