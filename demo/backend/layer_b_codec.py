"""Layer B codec for QoverwRap demo — schema + triple format (JSON/CBOR/CBOR-aggressive).

Layer B is the application-defined metadata layer inside the QoverwRap wire
format. The patent leaves its internal structure free (≤65535 bytes of
arbitrary binary), so the demo defines a canonical ticket schema and three
serialization formats here.

Wire layout (inside Layer B bytes):

    [tag:1B] + [body]
       │         │
       │         └─ JSON UTF-8 / CBOR with string keys / CBOR with int keys
       └─ format tag, parsed first by decode()

Format catalog (measured against a realistic ticket payload with 9 fields,
Korean text, and two ISO 8601 timestamps):

  - 0x01 JSON: human-readable, ~245B. QR ≈ v10. Use for concert tickets,
    transit, anywhere field debugging matters more than QR size.
  - 0x02 CBOR (string keys): ~208B. QR ≈ v9. Slight save over JSON; mostly
    a stepping stone — same field-name overhead in bytes as JSON.
  - 0x03 CBOR-aggressive: ~80-100B. QR ≈ v5. Use for wristbands, small
    media, anywhere physical size dominates. Trades debuggability for size.

CBOR-aggressive (0x03) — stability contract
-------------------------------------------
The short-key map below (`_TICKET_AGGRESSIVE_V1`) is a stable v1 contract.
Once a wristband / printed token is issued under this map, it must remain
decodable forever under the same map. Rules:

  - NEVER renumber an existing field.
  - Adding fields: assign the next unused integer (reserve 10-19 for ticket
    extensions, 20+ for future polymorphic kinds).
  - Removing fields: leave the integer slot retired; do not reuse.
  - Breaking changes go to a NEW tag (0x04 = CBOR-aggressive v2) so old
    tokens still decode via 0x03.
  - For per-issuer schema variation (e.g. Tigers vs festival having
    different fields), the production path is to store the short-key map
    in the trust registry per-issuer (planned for M2.5+). The demo uses
    the single global v1 map below.

Timestamps in aggressive form are unix epoch seconds (CBOR int) rather than
ISO strings, saving ~20B per timestamp. The codec converts ISO ↔ epoch
transparently so the Pydantic model stays type-stable across formats.
"""
from __future__ import annotations

from datetime import datetime as dt_module, timezone as tz_module
from typing import Literal

import cbor2
from pydantic import BaseModel, Field

LAYER_B_TAG_JSON = 0x01
LAYER_B_TAG_CBOR = 0x02
LAYER_B_TAG_CBOR_AGGR = 0x03

_TICKET_AGGRESSIVE_V1: dict[str, int] = {
    "event_id":  1,
    "serial":    2,
    "issued_at": 3,  # encoded as unix int
    "section":   4,
    "seat":      5,
    "gate":      6,
    "datetime":  7,  # encoded as unix int
    "opponent":  8,
    "holder":    9,
    # kind is implicit — tag 0x03 means "ticket-v1"
    # 10-19 reserved for future ticket-specific additions
    # 20+ reserved for future polymorphic kinds (visit, badge, ...)
}
_TICKET_AGGRESSIVE_V1_REV: dict[int, str] = {v: k for k, v in _TICKET_AGGRESSIVE_V1.items()}
_TICKET_AGGRESSIVE_TS_FIELDS = {"issued_at", "datetime"}


def _iso_to_epoch(iso: str) -> int:
    """Parse ISO 8601 to unix epoch seconds. Empty string → 0."""
    if not iso:
        return 0
    return int(dt_module.fromisoformat(iso).timestamp())


def _epoch_to_iso(epoch: int) -> str:
    """Unix epoch seconds → UTC ISO 8601 string. 0 → empty string.

    Always emits UTC so the aggressive-CBOR roundtrip is deterministic
    regardless of the decoder's local timezone. Callers that need the
    original timezone display should not use aggressive CBOR.
    """
    if epoch == 0:
        return ""
    return dt_module.fromtimestamp(epoch, tz=tz_module.utc).isoformat()


class TicketLayerB(BaseModel):
    """Concert / event ticket metadata."""

    kind: Literal["ticket"] = "ticket"
    event_id: str = Field(..., description="Stable event identifier, e.g. 'tigers-2026-042'")
    serial: str = Field(..., description="Per-event ticket serial; component of uniqueness")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    section: str = ""
    seat: str = ""
    gate: str = ""
    datetime: str = ""
    opponent: str = ""
    holder: str = Field("", description="Tokenized holder identifier (no PII)")


def encode_json(model: TicketLayerB) -> bytes:
    """Tag 0x01 + canonical JSON (no whitespace, sorted keys)."""
    body = model.model_dump_json(by_alias=False).encode("utf-8")
    return bytes([LAYER_B_TAG_JSON]) + body


def encode_cbor(model: TicketLayerB) -> bytes:
    """Tag 0x02 + CBOR-encoded dict (full string keys)."""
    body = cbor2.dumps(model.model_dump(), canonical=True)
    return bytes([LAYER_B_TAG_CBOR]) + body


def encode_cbor_aggressive(model: TicketLayerB) -> bytes:
    """Tag 0x03 + CBOR with short int keys + epoch timestamps.

    Only fields present in `_TICKET_AGGRESSIVE_V1` are emitted. `kind` is
    implicit (tag 0x03 ⇒ ticket-v1). Empty optional fields are omitted to
    save further bytes.
    """
    raw_dict = model.model_dump()
    packed: dict[int, int | str] = {}
    for field, int_key in _TICKET_AGGRESSIVE_V1.items():
        value = raw_dict.get(field, "")
        if value == "":
            continue  # skip empty optionals
        if field in _TICKET_AGGRESSIVE_TS_FIELDS:
            packed[int_key] = _iso_to_epoch(value)
        else:
            packed[int_key] = value
    body = cbor2.dumps(packed, canonical=True)
    return bytes([LAYER_B_TAG_CBOR_AGGR]) + body


def decode(raw: bytes) -> TicketLayerB:
    """Dispatch on first byte, deserialize body, validate against schema."""
    if not raw:
        raise ValueError("layer_b is empty")
    tag, body = raw[0], raw[1:]
    if tag == LAYER_B_TAG_JSON:
        return TicketLayerB.model_validate_json(body)
    if tag == LAYER_B_TAG_CBOR:
        return TicketLayerB.model_validate(cbor2.loads(body))
    if tag == LAYER_B_TAG_CBOR_AGGR:
        packed = cbor2.loads(body)
        if not isinstance(packed, dict):
            raise ValueError("aggressive CBOR body must be a map")
        unpacked: dict[str, object] = {"kind": "ticket"}
        for int_key, value in packed.items():
            field = _TICKET_AGGRESSIVE_V1_REV.get(int_key)
            if field is None:
                # Forward-compat: ignore unknown int keys rather than fail,
                # so an old decoder can still read newer wristbands.
                continue
            if field in _TICKET_AGGRESSIVE_TS_FIELDS:
                unpacked[field] = _epoch_to_iso(int(value))
            else:
                unpacked[field] = value
        return TicketLayerB.model_validate(unpacked)
    raise ValueError(f"unknown layer_b tag: 0x{tag:02x}")
