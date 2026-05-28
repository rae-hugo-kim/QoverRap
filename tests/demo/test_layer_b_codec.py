"""Tests for demo Layer B codec — schema + JSON/CBOR/CBOR-aggressive + size budget."""
from __future__ import annotations

import cbor2
import pytest

from demo.backend.layer_b_codec import (
    LAYER_B_TAG_CBOR,
    LAYER_B_TAG_CBOR_AGGR,
    LAYER_B_TAG_JSON,
    TicketLayerB,
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


def test_kind_default_is_ticket() -> None:
    """Schema fixes kind="ticket" — future polymorphism keys off this field."""
    t = _sample_ticket()
    assert t.kind == "ticket"
    raw = encode_json(t)
    assert b'"kind":"ticket"' in raw


def test_aggressive_omits_kind_from_body() -> None:
    """kind is implicit in tag 0x03 — no need to spend bytes on it."""
    t = _sample_ticket()
    raw = encode_cbor_aggressive(t)
    body = cbor2.loads(raw[1:])
    assert isinstance(body, dict)
    # No string key "kind", no int key reserved for it either
    assert "kind" not in body
    # All keys are ints
    assert all(isinstance(k, int) for k in body.keys())


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
    raw = encode_json(_sample_ticket())
    assert len(raw) <= 250, f"JSON layer_b is {len(raw)}B, expected ≤250B (target QR v10)"


def test_size_budget_cbor() -> None:
    raw = encode_cbor(_sample_ticket())
    assert len(raw) <= 215, f"CBOR layer_b is {len(raw)}B, expected ≤215B (target QR v9)"


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
