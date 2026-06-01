"""Tests for Layer B decode in the resolve endpoint.

The resolve endpoint exposes the raw Layer B hex; on top of that it decodes the
demo codec (JSON / CBOR / aggressive-CBOR) into a structured ticket dict plus a
format tag, but only at access levels where Layer B is already exposed and only
when the bytes are decodable. Empty / absent / tampered Layer B must NOT crash
and must NOT produce a ticket — preserving claim 7(iii) (verified-empty) and the
claim 8 safe-fallback semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from demo.backend.layer_b_codec import TicketLayerB, _iso_to_epoch
from demo.backend.main import app
from demo.backend import trust_registry


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _ticket_dict() -> dict:
    # Timestamps are already UTC so the aggressive-CBOR epoch roundtrip
    # (_epoch_to_iso emits UTC) reproduces them exactly.
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


def _offset_ticket_dict() -> dict:
    # Same fields as _ticket_dict but timestamps carry a +09:00 offset, so the
    # wall-clock string differs from its UTC-normalized form (the aggressive
    # path) while denoting the same instant.
    d = _ticket_dict()
    d["issued_at"] = "2026-05-01T09:00:00+09:00"
    d["datetime"] = "2026-05-10T18:30:00+09:00"
    return d


def _verified_resolve_for_format(
    client: TestClient, fmt: str, ticket: dict | None = None
) -> dict:
    """encode-layer-b → sign as issuer → encode → resolve(verified)."""
    issuer_id = "tigers-2026"
    layer_a = trust_registry.format_layer_a(issuer_id, "VIP seat A1")

    enc_b = client.post(
        "/api/encode-layer-b",
        json={"ticket": ticket if ticket is not None else _ticket_dict(), "format": fmt},
    ).json()
    layer_b_hex = enc_b["layer_b_hex"]

    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": layer_b_hex},
    ).json()
    layer_c_hex = sig_resp["signature"]

    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": layer_b_hex, "layer_c": layer_c_hex},
    ).json()

    return client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()


@pytest.mark.parametrize("fmt", ["json", "cbor", "cbor_aggr"])
def test_verified_decodes_layer_b_ticket(client: TestClient, fmt: str) -> None:
    r = _verified_resolve_for_format(client, fmt)
    assert r["verified"] is True
    assert r["layer_b_format"] == fmt
    assert r["layer_b_schema"] == "baseball_ticket"

    # model_dump of the original ticket is the canonical comparison target:
    # aggressive CBOR drops empty optionals and roundtrips UTC timestamps, but
    # the validated model normalizes both back to the original here.
    expected = TicketLayerB.model_validate(_ticket_dict()).model_dump()
    assert r["layer_b_ticket"] == expected


@pytest.mark.parametrize("fmt", ["json", "cbor", "cbor_aggr"])
def test_offset_timestamps_preserve_instant_across_formats(
    client: TestClient, fmt: str
) -> None:
    """A ticket with +09:00 timestamps decodes to the SAME instant in every
    format. json/cbor keep the original offset (string equality holds); cbor_aggr
    normalizes to an equivalent UTC ISO string (a different wall-clock string but
    the same instant). The assertion is on the instant, not the literal string —
    this pins the M2 trade-off so the formats never silently diverge in meaning.
    """
    ticket = _offset_ticket_dict()
    r = _verified_resolve_for_format(client, fmt, ticket)
    assert r["verified"] is True
    assert r["layer_b_format"] == fmt

    decoded = r["layer_b_ticket"]
    for field in ("issued_at", "datetime"):
        want = datetime.fromisoformat(ticket[field])
        got = datetime.fromisoformat(decoded[field])
        # instant equivalence (aware datetimes compare by absolute time), not
        # wall-clock string equivalence
        assert got == want, f"{fmt}:{field} drifted instant"
        if fmt == "cbor_aggr":
            # aggressive path is normalized to UTC
            assert got.utcoffset() == timezone.utc.utcoffset(None)
        else:
            # lossless paths preserve the original offset string verbatim
            assert decoded[field] == ticket[field]


def test_verified_empty_layer_b_has_no_ticket(client: TestClient) -> None:
    """claim 7(iii): verified with empty Layer B keeps layer_b == "" (distinct
    from absent) and yields no decoded ticket / format."""
    issuer_id = "tigers-2026"
    layer_a = trust_registry.format_layer_a(issuer_id, "no metadata")

    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": ""},
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": "", "layer_c": sig_resp["signature"]},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    ).json()
    assert r["verified"] is True
    assert r["layer_b"] == ""  # empty hex preserved, NOT None (claim 7(iii))
    assert r["layer_b_ticket"] is None
    assert r["layer_b_format"] is None
    assert r["layer_b_schema"] is None


def test_tampered_layer_b_falls_back_no_crash(client: TestClient) -> None:
    """Replacing signed Layer B with other bytes fails verification → public
    fallback. layer_b is hidden (None) and no ticket is decoded; no crash."""
    issuer_id = "violet-fandom"
    layer_a = trust_registry.format_layer_a(issuer_id, "exclusive content")

    enc_b = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "json"},
    ).json()
    sig_resp = client.post(
        f"/api/trust/{issuer_id}/sign",
        json={"layer_a": layer_a, "layer_b": enc_b["layer_b_hex"]},
    ).json()

    tampered_b = b"forged!!".hex()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": tampered_b, "layer_c": sig_resp["signature"]},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "verified"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is False
    assert body["layer_b"] is None  # safe-fallback hides Layer B
    assert body["layer_b_ticket"] is None
    assert body["layer_b_format"] is None
    assert body["layer_b_schema"] is None


def test_authenticated_undecodable_layer_b_no_crash(client: TestClient) -> None:
    """At authenticated level Layer B is exposed without verification. If the
    bytes are not valid codec output (unknown tag / garbage), the raw hex is
    still returned but no ticket is decoded — no crash."""
    layer_a = "qwr:demo|x"
    garbage_b = bytes([0xFF, 0xDE, 0xAD, 0xBE, 0xEF]).hex()  # unknown tag 0xFF
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": garbage_b, "layer_c": ""},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "authenticated"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["layer_b"] == garbage_b  # raw hex preserved
    assert body["layer_b_ticket"] is None
    assert body["layer_b_format"] is None
    assert body["layer_b_schema"] is None


def test_authenticated_decodes_layer_b_ticket(client: TestClient) -> None:
    """Layer B decode is available wherever Layer B is exposed, not only at
    verified level (authenticated exposes Layer B without signature check)."""
    layer_a = "qwr:demo|x"
    enc_b = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "cbor"},
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": enc_b["layer_b_hex"], "layer_c": ""},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "authenticated"},
    ).json()
    assert r["verified"] is False
    assert r["layer_b_format"] == "cbor"
    assert r["layer_b_schema"] == "baseball_ticket"
    assert r["layer_b_ticket"] == TicketLayerB.model_validate(_ticket_dict()).model_dump()


def test_public_level_no_layer_b_fields(client: TestClient) -> None:
    """Public level hides Layer B entirely; the decode fields stay None too."""
    layer_a = "qwr:demo|x"
    enc_b = client.post(
        "/api/encode-layer-b",
        json={"ticket": _ticket_dict(), "format": "json"},
    ).json()
    enc = client.post(
        "/api/encode",
        json={"layer_a": layer_a, "layer_b": enc_b["layer_b_hex"], "layer_c": ""},
    ).json()

    r = client.post(
        "/api/resolve",
        json={"payload": enc["encoded"], "access_level": "public"},
    ).json()
    assert r["layer_b"] is None
    assert r["layer_b_ticket"] is None
    assert r["layer_b_format"] is None
    assert r["layer_b_schema"] is None


def test_iso_to_epoch_naive_is_utc_not_host_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Naive (offset-less) ISO must be interpreted as UTC, so the aggressive-CBOR
    epoch is identical regardless of the host's local timezone. Without the UTC
    pin this value would shift with TZ, making issued tokens non-deterministic.
    """
    naive = "2026-05-10T09:30:00"
    expected = int(datetime(2026, 5, 10, 9, 30, tzinfo=timezone.utc).timestamp())

    for tz in ("UTC", "Asia/Seoul", "America/Los_Angeles"):
        monkeypatch.setenv("TZ", tz)
        import time

        time.tzset()
        assert _iso_to_epoch(naive) == expected

    # an offset-carrying input is unaffected by this normalization
    assert _iso_to_epoch("2026-05-10T09:30:00+00:00") == expected
    assert _iso_to_epoch("") == 0
