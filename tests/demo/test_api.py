"""Integration tests for the QoverwRap demo backend.

Covers each endpoint with a roundtrip flow plus the trust-registry routing path.
"""
from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from demo.backend.main import app
from demo.backend import trust_registry


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_key_shape(client: TestClient) -> None:
    r = client.post("/api/generate-key")
    assert r.status_code == 200
    data = r.json()
    # Ed25519: 32B private seed, 32B public key
    assert len(data["private_key"]) == 64
    assert len(data["public_key"]) == 64
    bytes.fromhex(data["private_key"])
    bytes.fromhex(data["public_key"])


def test_sign_verify_roundtrip(client: TestClient) -> None:
    keys = client.post("/api/generate-key").json()
    layer_a = "qwr:demo|hello"
    layer_b_hex = b"context-bytes".hex()

    sig_resp = client.post(
        "/api/sign",
        json={"private_key": keys["private_key"], "layer_a": layer_a, "layer_b": layer_b_hex},
    ).json()
    assert len(sig_resp["signature"]) == 128  # 64 bytes hex

    verify = client.post(
        "/api/verify",
        json={
            "public_key": keys["public_key"],
            "layer_a": layer_a,
            "layer_b": layer_b_hex,
            "signature": sig_resp["signature"],
        },
    ).json()
    assert verify["valid"] is True

    # Tamper layer_a -> invalid
    bad = client.post(
        "/api/verify",
        json={
            "public_key": keys["public_key"],
            "layer_a": layer_a + "X",
            "layer_b": layer_b_hex,
            "signature": sig_resp["signature"],
        },
    ).json()
    assert bad["valid"] is False


def test_encode_decode_roundtrip(client: TestClient) -> None:
    layer_a = "qwr:tigers-2026|seat 12B"
    layer_b_hex = b'{"section":"A","row":12}'.hex()
    layer_c_hex = (b"\x00" * 64).hex()

    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": layer_c_hex},
    ).json()
    assert layer_a in enc["encoded"]
    assert "---QWR---" in enc["encoded"]

    dec = client.post("/api/decode", json={"payload": enc["encoded"]}).json()
    assert dec["layer_a"] == layer_a
    assert dec["layer_b"] == layer_b_hex
    assert dec["layer_c"] == layer_c_hex


def test_qr_image_returns_png(client: TestClient) -> None:
    enc = client.post(
        "/api/encode",
        json={"layer_a": "qwr:demo|hi", "layer_b": "", "layer_c": ""},
    ).json()
    img = client.post(
        "/api/qr-image",
        json={"encoded": enc["encoded"], "box_size": 6, "border": 4, "error_correction": "H"},
    ).json()
    raw = base64.b64decode(img["image_png_base64"])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"


def test_resolve_public_only_hides_layers(client: TestClient) -> None:
    layer_a = "qwr:tigers-2026|seat 12B"
    layer_b_hex = b"context".hex()
    layer_c_hex = (b"\x42" * 64).hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": layer_c_hex},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "public"},
    ).json()
    assert r["layer_a"] == layer_a
    assert r["layer_b"] is None
    assert r["signature"] is None
    assert r["verified"] is False
    assert r["issuer_id"] == "tigers-2026"
    assert r["routed_public_key"] is not None  # routed via trust registry


def test_resolve_authenticated_exposes_b_only(client: TestClient) -> None:
    layer_a = "qwr:demo|x"
    layer_b_hex = b"meta".hex()
    layer_c_hex = (b"\x01" * 64).hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": layer_c_hex},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "authenticated"},
    ).json()
    assert r["layer_b"] == layer_b_hex
    assert r["signature"] is None
    assert r["verified"] is False


def test_resolve_verified_with_routing(client: TestClient) -> None:
    """End-to-end: sign as registered issuer, resolve with verified level, no
    explicit public_key — routing must pick the right key from the registry.
    """
    issuer_id = "tigers-2026"
    layer_a = trust_registry.format_layer_a(issuer_id, "VIP seat A1")
    layer_b_hex = b'{"vip":true}'.hex()

    # Use the trust endpoint to sign as the issuer (demo-only convenience)
    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": layer_b_hex},
    ).json()
    layer_c_hex = sig_resp["signature"]

    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": layer_c_hex},
    ).json()

    # verified, no explicit public_key -> routing kicks in
    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()
    assert r["verified"] is True
    assert r["layer_b"] == layer_b_hex
    assert r["signature"] == layer_c_hex
    assert r["issuer_id"] == issuer_id
    assert r["routed_public_key"] == sig_resp["public_key"]


def test_resolve_verified_tampered_falls_back_to_public(client: TestClient) -> None:
    issuer_id = "violet-fandom"
    layer_a = trust_registry.format_layer_a(issuer_id, "exclusive content")
    layer_b_hex = b"original".hex()

    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": layer_b_hex},
    ).json()
    layer_c_hex = sig_resp["signature"]

    # Tamper layer_b after signing
    tampered_b = b"forged!!".hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": tampered_b, "layer_c": layer_c_hex},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()
    assert r["verified"] is False
    assert r["layer_b"] is None
    assert r["signature"] is None
    assert r["layer_a"] == layer_a  # public still visible


def test_trust_list_returns_seeded_issuers(client: TestClient) -> None:
    r = client.get("/api/trust").json()
    ids = {e["issuer_id"] for e in r["entries"]}
    assert {"tigers-2026", "violet-fandom", "comic-con-2026"} <= ids
    for e in r["entries"]:
        assert len(e["public_key"]) == 64
        assert e["theme_color"].startswith("#")


def test_unknown_issuer_no_routing(client: TestClient) -> None:
    layer_a = "qwr:never-registered|x"
    layer_b_hex = b"x".hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": ""},
    ).json()
    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()
    assert r["issuer_id"] == "never-registered"
    assert r["routed_public_key"] is None
    assert r["verified"] is False


def test_invalid_hex_returns_422(client: TestClient) -> None:
    r = client.post(
        "/api/sign",
        json={"private_key": "ZZ" * 32, "layer_a": "x", "layer_b": ""},
    )
    assert r.status_code == 422


def test_trust_sign_disabled_without_env(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("QWR_ENABLE_DEMO_SIGNING", "")
    r = client.post(
        "/api/trust/tigers-2026/sign",
        json={"layer_a": "qwr:tigers-2026|x", "layer_b": ""},
    )
    assert r.status_code == 403
