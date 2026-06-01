"""Tests for demo Layer B codec — catalog + JSON/CBOR/CBOR-aggressive + size budget."""
from __future__ import annotations

import cbor2
import pytest
from pydantic import ValidationError

from demo.backend.layer_b_codec import (
    LAYER_B_TAG_CBOR,
    LAYER_B_TAG_CBOR_AGGR,
    LAYER_B_TAG_JSON,
    FestivalPass,
    TicketLayerB,
    Wristband,
    decode,
    encode_cbor,
    encode_cbor_aggressive,
    encode_json,
)


def _sample_ticket() -> TicketLayerB:
    """Fixture using UTC ISO timestamps so the aggressive-CBOR roundtrip
    (which normalizes to UTC) preserves field-equality across formats."""
    return TicketLayerB(
        event_id="tigers-2026-042",
        serial="T-2026-000123",
        issued_at="2026-05-01T00:00:00+00:00",
        section="1루 응원석",
        seat="12B",
        gate="Gate 3",
        datetime="2026-05-10T09:30:00+00:00",
        opponent="Lions",
        holder="FAN-2456",
    )


def _sample_festival() -> FestivalPass:
    return FestivalPass(
        festival_id="comic-con-2026",
        serial="F-2026-000777",
        issued_at="2026-07-01T00:00:00+00:00",
        day="Day 1 / Sat",
        zone="Hall A",
        tier="VIP",
        gate="Gate 7",
        holder="FAN-9981",
    )


def _sample_wristband() -> Wristband:
    return Wristband(
        band_id="comic-con-2026-band",
        serial="W-2026-000333",
        issued_at="2026-07-01T00:00:00+00:00",
        tier="3-day",
        valid_until="2026-07-03T23:59:59+00:00",
        holder="FAN-9981",
    )


# ---------------------------------------------------------------------------
# Roundtrip — all three formats
# ---------------------------------------------------------------------------

def test_json_roundtrip() -> None:
    t = _sample_ticket()
    raw = encode_json(t)
    assert raw[0] == LAYER_B_TAG_JSON
    assert decode(raw) == t


def test_cbor_roundtrip() -> None:
    t = _sample_ticket()
    raw = encode_cbor(t)
    assert raw[0] == LAYER_B_TAG_CBOR
    assert decode(raw) == t


def test_cbor_aggressive_roundtrip() -> None:
    t = _sample_ticket()
    raw = encode_cbor_aggressive(t)
    assert raw[0] == LAYER_B_TAG_CBOR_AGGR
    assert decode(raw) == t


def test_kind_default_is_baseball_ticket() -> None:
    """Schema fixes kind="baseball_ticket" — JSON/CBOR routing keys off this field."""
    t = _sample_ticket()
    assert t.kind == "baseball_ticket"
    raw = encode_json(t)
    assert b'"kind":"baseball_ticket"' in raw


def test_aggressive_encodes_schema_id_not_kind_string() -> None:
    """kind never spends string bytes in 0x03 — the schema_id rides in int key 0."""
    t = _sample_ticket()
    raw = encode_cbor_aggressive(t)
    body = cbor2.loads(raw[1:])
    assert isinstance(body, dict)
    # No string key "kind"; all keys are ints
    assert "kind" not in body
    assert all(isinstance(k, int) for k in body.keys())
    # Int key 0 carries the schema_id discriminator (baseball_ticket == 1)
    assert body[0] == 1


# ---------------------------------------------------------------------------
# Format dispatch
# ---------------------------------------------------------------------------

def test_unknown_tag_rejected() -> None:
    with pytest.raises(ValueError, match="unknown layer_b tag"):
        decode(b"\xff" + b"garbage")


def test_empty_raw_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        decode(b"")


def test_truncated_json_body_rejected() -> None:
    raw = encode_json(_sample_ticket())
    truncated = raw[: len(raw) // 2]
    with pytest.raises(Exception):
        decode(truncated)


def test_truncated_cbor_body_rejected() -> None:
    raw = encode_cbor(_sample_ticket())
    truncated = raw[: len(raw) // 2]
    with pytest.raises(Exception):
        decode(truncated)


def test_aggressive_forward_compat_ignores_unknown_int_keys() -> None:
    """Old decoder must skip int keys it doesn't recognize — newer wristbands
    encoded with v1.1 fields stay decodable on a v1 reader (with degraded data)."""
    t = _sample_ticket()
    raw = encode_cbor_aggressive(t)
    # Inject a fictional int key 99 into the CBOR body
    body = cbor2.loads(raw[1:])
    body[99] = "future-field-value"
    forged = bytes([LAYER_B_TAG_CBOR_AGGR]) + cbor2.dumps(body, canonical=True)
    decoded = decode(forged)
    assert decoded == t  # unknown key dropped, rest preserved


def test_aggressive_rejects_non_dict_body() -> None:
    forged = bytes([LAYER_B_TAG_CBOR_AGGR]) + cbor2.dumps([1, 2, 3])
    with pytest.raises(ValueError, match="must be a map"):
        decode(forged)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_missing_required_field_rejected() -> None:
    """event_id, serial, issued_at are required by schema."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TicketLayerB(serial="X", issued_at="2026-05-01T00:00:00Z")


def test_optional_fields_default_to_empty_string() -> None:
    """section/seat/gate/datetime/opponent/holder are optional → default ''."""
    minimal = TicketLayerB(
        event_id="e1",
        serial="s1",
        issued_at="2026-05-01T00:00:00+00:00",
    )
    assert minimal.section == ""
    assert minimal.holder == ""
    assert decode(encode_json(minimal)) == minimal
    assert decode(encode_cbor(minimal)) == minimal
    assert decode(encode_cbor_aggressive(minimal)) == minimal


# ---------------------------------------------------------------------------
# Size budget — sanity-check QR version math
# ---------------------------------------------------------------------------
#
# Measured values on the realistic sample (9 fields, Korean text, two ISO
# timestamps). QR version mapping per RFC standards at ECC M:
#   QR v5  (37 modules)  : up to 106 bytes (byte mode)
#   QR v9  (53 modules)  : up to 230 bytes
#   QR v10 (57 modules)  : up to 271 bytes
#
# Layer B is one component of the overall payload (Layer A ~30B + delimiter
# + base64-encoded trailer with 64B signature). Budget here is for Layer B
# alone — final QR version depends on the combined payload size.

def test_size_budget_json() -> None:
    # Budget bumped +10B over the pre-catalog 250B: the kind discriminator grew
    # from "ticket" (6) to "baseball_ticket" (15) for self-describing routing.
    raw = encode_json(_sample_ticket())
    assert len(raw) <= 260, f"JSON layer_b is {len(raw)}B, expected ≤260B (target QR v10)"


def test_size_budget_cbor() -> None:
    # Budget bumped +10B over the pre-catalog 215B (longer kind string, see above).
    raw = encode_cbor(_sample_ticket())
    assert len(raw) <= 225, f"CBOR layer_b is {len(raw)}B, expected ≤225B (target QR v9)"


def test_size_budget_cbor_aggressive() -> None:
    raw = encode_cbor_aggressive(_sample_ticket())
    assert len(raw) <= 110, (
        f"CBOR-aggressive layer_b is {len(raw)}B, expected ≤110B (target QR v5 / wristband)"
    )


def test_aggressive_is_meaningfully_smaller_than_json() -> None:
    """Aggressive must deliver the wristband promise — at least 50% savings vs JSON."""
    t = _sample_ticket()
    json_len = len(encode_json(t))
    aggr_len = len(encode_cbor_aggressive(t))
    assert aggr_len < json_len * 0.5, (
        f"CBOR-aggressive={aggr_len}B is only "
        f"{100 * (1 - aggr_len/json_len):.0f}% smaller than JSON={json_len}B; "
        f"expected ≥50% savings"
    )


def test_format_ordering_by_size() -> None:
    """JSON > CBOR (string keys) > CBOR-aggressive — assert the gradient holds."""
    t = _sample_ticket()
    sizes = {
        "json": len(encode_json(t)),
        "cbor": len(encode_cbor(t)),
        "aggr": len(encode_cbor_aggressive(t)),
    }
    assert sizes["json"] > sizes["cbor"] > sizes["aggr"], sizes


# ---------------------------------------------------------------------------
# Self-describing catalog — multi-schema roundtrips
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "factory,kind",
    [
        (_sample_festival, "festival_pass"),
        (_sample_wristband, "wristband"),
    ],
)
def test_non_baseball_schema_roundtrips_all_formats(factory, kind: str) -> None:
    """festival_pass / wristband must roundtrip through every format and decode
    back into their own model (not baseball)."""
    m = factory()
    assert m.kind == kind
    for enc in (encode_json, encode_cbor, encode_cbor_aggressive):
        decoded = decode(enc(m))
        assert decoded.kind == kind
        assert decoded == m


def test_aggressive_festival_carries_its_schema_id() -> None:
    """Int key 0 in a festival aggressive body is schema_id 2 (not baseball's 1)."""
    body = cbor2.loads(encode_cbor_aggressive(_sample_festival())[1:])
    assert body[0] == 2


def test_aggressive_wristband_carries_its_schema_id() -> None:
    body = cbor2.loads(encode_cbor_aggressive(_sample_wristband())[1:])
    assert body[0] == 3


# ---------------------------------------------------------------------------
# Cross-schema decode SAFETY — the core authenticity boundary
# ---------------------------------------------------------------------------

def test_festival_aggressive_bytes_do_not_decode_as_baseball() -> None:
    """A festival_pass aggressive token must decode as festival_pass, never as
    a baseball ticket whose field 1 happens to be the festival_id. The schema_id
    in key 0 is the only thing the decoder trusts."""
    raw = encode_cbor_aggressive(_sample_festival())
    decoded = decode(raw)
    assert decoded.kind == "festival_pass"
    assert not isinstance(decoded, TicketLayerB)


def test_festival_json_bytes_do_not_decode_as_baseball() -> None:
    """JSON/CBOR route on the `kind` string — a festival body must not silently
    validate against TicketLayerB."""
    raw = encode_json(_sample_festival())
    assert decode(raw).kind == "festival_pass"


def test_kind_field_mismatch_is_rejected() -> None:
    """A body claiming kind="baseball_ticket" but carrying festival-only fields
    (no required event_id) must fail schema validation, not coerce."""
    forged = bytes([LAYER_B_TAG_JSON]) + (
        b'{"kind":"baseball_ticket","festival_id":"x","serial":"s",'
        b'"issued_at":"2026-07-01T00:00:00+00:00"}'
    )
    with pytest.raises((ValueError, ValidationError)):
        decode(forged)


def test_unknown_kind_string_rejected() -> None:
    forged = bytes([LAYER_B_TAG_JSON]) + b'{"kind":"spaceship","serial":"s"}'
    with pytest.raises(ValueError, match="unknown layer_b kind"):
        decode(forged)


# ---------------------------------------------------------------------------
# Aggressive schema_id discriminator — boundary cases
# ---------------------------------------------------------------------------

def test_aggressive_unknown_schema_id_rejected() -> None:
    """An aggressive body whose key 0 names an unregistered schema_id must
    raise (no silent fallback to baseball)."""
    forged = bytes([LAYER_B_TAG_CBOR_AGGR]) + cbor2.dumps({0: 99, 2: "s"})
    with pytest.raises(ValueError, match="unknown schema_id"):
        decode(forged)


def test_aggressive_key0_absent_falls_back_to_baseball() -> None:
    """Pre-catalog ticket bytes never wrote key 0. A key-0-absent aggressive
    body must still decode as baseball_ticket so old tokens stay readable."""
    # Hand-build a baseball aggressive body WITHOUT key 0 (legacy shape).
    legacy = cbor2.dumps({1: "tigers-2026-042", 2: "T-1", 3: 1777_000_000})
    forged = bytes([LAYER_B_TAG_CBOR_AGGR]) + legacy
    decoded = decode(forged)
    assert decoded.kind == "baseball_ticket"
    assert isinstance(decoded, TicketLayerB)
    assert decoded.event_id == "tigers-2026-042"


# ---------------------------------------------------------------------------
# Timestamp epoch roundtrip — per-schema ts fields
# ---------------------------------------------------------------------------

def test_festival_issued_at_epoch_roundtrip() -> None:
    """festival_pass ts_fields = {issued_at}; `day` is a STRING, not epoch."""
    f = _sample_festival()
    raw = encode_cbor_aggressive(f)
    body = cbor2.loads(raw[1:])
    # issued_at (int key 3) is an int epoch; day (int key 4) stays a string
    assert isinstance(body[3], int)
    assert isinstance(body[4], str)
    assert decode(raw).issued_at == f.issued_at


def test_wristband_valid_until_epoch_roundtrip() -> None:
    """wristband ts_fields = {issued_at, valid_until} — both epoch-encoded."""
    w = _sample_wristband()
    raw = encode_cbor_aggressive(w)
    body = cbor2.loads(raw[1:])
    assert isinstance(body[3], int)  # issued_at
    assert isinstance(body[5], int)  # valid_until
    decoded = decode(raw)
    assert decoded.issued_at == w.issued_at
    assert decoded.valid_until == w.valid_until
