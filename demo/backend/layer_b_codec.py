"""Layer B codec for QoverwRap demo — self-describing schema catalog + triple format.

Layer B is the application-defined metadata layer inside the QoverwRap wire
format. The patent leaves its internal structure free (≤65535 bytes of
arbitrary binary), so the demo defines a small schema catalog (baseball
tickets, festival passes, wristbands) and three serialization formats here.

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

Self-describing schema catalog
------------------------------
The framing `[tag:1B][body]` is UNCHANGED. The schema discriminator lives
*inside* the body, not in a separate byte:

  - JSON (0x01) / CBOR string-keyed (0x02): the body already carries a `kind`
    string field. decode() reads it and routes via `SCHEMA_BY_KIND`.
  - CBOR-aggressive (0x03): integer key `0` is reserved, across ALL schemas,
    as the `schema_id` discriminator. encode writes `{0: schema_id, 1: …}`;
    decode reads key 0 to select the schema. If key 0 is ABSENT, decode falls
    back to schema_id=1 (baseball_ticket) so pre-catalog ticket bytes (which
    never wrote key 0) still decode.

CBOR-aggressive (0x03) — stability contract
-------------------------------------------
Each schema owns an independent short-key map (e.g. `_TICKET_AGGRESSIVE_V1`).
The maps are a stable v1 contract. Once a wristband / printed token is issued
under a schema's map, it must remain decodable forever under that map. Rules:

  - Integer key `0` is RESERVED globally as the schema_id discriminator and is
    never used as a field key in any schema's map (maps start at 1).
  - NEVER renumber an existing field within a schema's map.
  - Adding fields: assign the next unused integer within that schema's map.
  - Removing fields: leave the integer slot retired; do not reuse.
  - Per-schema maps are namespaced — int key 1 means different fields in
    different schemas; the schema is resolved first (key 0), then the map.
  - Breaking changes go to a NEW tag (0x04 = CBOR-aggressive v2) so old
    tokens still decode via 0x03.

Timestamps in aggressive form are unix epoch seconds (CBOR int) rather than
ISO strings, saving ~20B per timestamp. The codec converts ISO ↔ epoch
transparently so the Pydantic model stays type-stable across formats.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime as dt_module, timezone as tz_module
from typing import Literal

import cbor2
from pydantic import BaseModel, Field

LAYER_B_TAG_JSON = 0x01
LAYER_B_TAG_CBOR = 0x02
LAYER_B_TAG_CBOR_AGGR = 0x03

# Integer key 0 is reserved, across every schema, as the aggressive-CBOR
# schema_id discriminator. Schema field maps therefore start at 1.
_AGGRESSIVE_SCHEMA_ID_KEY = 0

# Fallback when an aggressive body omits key 0 — pre-catalog ticket bytes were
# issued before key 0 existed, so they decode as baseball_ticket (schema_id=1).
_AGGRESSIVE_FALLBACK_SCHEMA_ID = 1


def _iso_to_epoch(iso: str) -> int:
    """Parse ISO 8601 to unix epoch seconds. Empty string → 0.

    Naive (offset-less) inputs are interpreted as UTC rather than the server's
    local timezone, so the aggressive-CBOR epoch is deterministic regardless of
    where encoding runs. Inputs that carry an offset are unchanged.
    """
    if not iso:
        return 0
    d = dt_module.fromisoformat(iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=tz_module.utc)
    return int(d.timestamp())


def _epoch_to_iso(epoch: int) -> str:
    """Unix epoch seconds → UTC ISO 8601 string. 0 → empty string.

    Always emits UTC so the aggressive-CBOR roundtrip is deterministic
    regardless of the decoder's local timezone. Callers that need the
    original timezone display should not use aggressive CBOR.
    """
    if epoch == 0:
        return ""
    return dt_module.fromtimestamp(epoch, tz=tz_module.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema models — every model carries a `kind` discriminator
# ---------------------------------------------------------------------------


class LayerBModel(BaseModel):
    """Base for all Layer B schemas. `kind` is the JSON/CBOR discriminator."""

    kind: str


class TicketLayerB(LayerBModel):
    """Concert / event ticket metadata (schema_id 1)."""

    kind: Literal["baseball_ticket"] = "baseball_ticket"
    event_id: str = Field(..., description="Stable event identifier, e.g. 'tigers-2026-042'")
    serial: str = Field(..., description="Per-event ticket serial; component of uniqueness")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    section: str = ""
    seat: str = ""
    gate: str = ""
    datetime: str = ""
    opponent: str = ""
    holder: str = Field("", description="Tokenized holder identifier (no PII)")


class FestivalPass(LayerBModel):
    """Multi-day festival pass metadata (schema_id 2)."""

    kind: Literal["festival_pass"] = "festival_pass"
    festival_id: str = Field(..., description="Stable festival identifier")
    serial: str = Field(..., description="Per-festival pass serial; component of uniqueness")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    day: str = Field("", description="Day label, e.g. 'Day 1 / Sat' (string, not a timestamp)")
    zone: str = ""
    tier: str = ""
    gate: str = ""
    holder: str = Field("", description="Tokenized holder identifier (no PII)")


class Wristband(LayerBModel):
    """Small-media wristband metadata (schema_id 3)."""

    kind: Literal["wristband"] = "wristband"
    band_id: str = Field(..., description="Stable wristband identifier")
    serial: str = Field(..., description="Per-band serial; component of uniqueness")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    tier: str = ""
    valid_until: str = Field("", description="ISO 8601 expiry (epoch in aggressive form)")
    holder: str = Field("", description="Tokenized holder identifier (no PII)")


# Per-schema aggressive maps. Int key 0 is reserved globally (schema_id), so
# every field map starts at 1. Never renumber; retire-don't-reuse.
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
    # 10-19 reserved for future ticket-specific additions
}
_TICKET_AGGRESSIVE_TS_FIELDS = {"issued_at", "datetime"}

_FESTIVAL_AGGRESSIVE_V1: dict[str, int] = {
    "festival_id": 1,
    "serial":      2,
    "issued_at":   3,  # encoded as unix int
    "day":         4,  # string label, NOT a timestamp
    "zone":        5,
    "tier":        6,
    "gate":        7,
    "holder":      8,
}
_FESTIVAL_AGGRESSIVE_TS_FIELDS = {"issued_at"}

_WRISTBAND_AGGRESSIVE_V1: dict[str, int] = {
    "band_id":     1,
    "serial":      2,
    "issued_at":   3,  # encoded as unix int
    "tier":        4,
    "valid_until": 5,  # encoded as unix int
    "holder":      6,
}
_WRISTBAND_AGGRESSIVE_TS_FIELDS = {"issued_at", "valid_until"}


@dataclass(frozen=True)
class LayerBSchema:
    """Descriptor binding a schema_id/kind to its model and aggressive map."""

    schema_id: int
    kind: str
    model: type[LayerBModel]
    aggressive_map: dict[str, int]  # field → int key, 1..N (0 reserved for schema_id)
    ts_fields: frozenset[str]
    rev_map: dict[int, str] = field(init=False)  # int key → field, built once

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "rev_map", {v: k for k, v in self.aggressive_map.items()}
        )


SCHEMA_CATALOG: dict[int, LayerBSchema] = {
    1: LayerBSchema(
        schema_id=1,
        kind="baseball_ticket",
        model=TicketLayerB,
        aggressive_map=_TICKET_AGGRESSIVE_V1,
        ts_fields=frozenset(_TICKET_AGGRESSIVE_TS_FIELDS),
    ),
    2: LayerBSchema(
        schema_id=2,
        kind="festival_pass",
        model=FestivalPass,
        aggressive_map=_FESTIVAL_AGGRESSIVE_V1,
        ts_fields=frozenset(_FESTIVAL_AGGRESSIVE_TS_FIELDS),
    ),
    3: LayerBSchema(
        schema_id=3,
        kind="wristband",
        model=Wristband,
        aggressive_map=_WRISTBAND_AGGRESSIVE_V1,
        ts_fields=frozenset(_WRISTBAND_AGGRESSIVE_TS_FIELDS),
    ),
}
SCHEMA_BY_KIND: dict[str, LayerBSchema] = {s.kind: s for s in SCHEMA_CATALOG.values()}


def _schema_for_kind(kind: str) -> LayerBSchema:
    schema = SCHEMA_BY_KIND.get(kind)
    if schema is None:
        raise ValueError(f"unknown layer_b kind: {kind!r}")
    return schema


def encode_json(model: LayerBModel) -> bytes:
    """Tag 0x01 + canonical JSON (no whitespace). `kind` rides in the body."""
    body = model.model_dump_json(by_alias=False).encode("utf-8")
    return bytes([LAYER_B_TAG_JSON]) + body


def encode_cbor(model: LayerBModel) -> bytes:
    """Tag 0x02 + CBOR-encoded dict (full string keys). `kind` rides in body."""
    body = cbor2.dumps(model.model_dump(), canonical=True)
    return bytes([LAYER_B_TAG_CBOR]) + body


def encode_cbor_aggressive(model: LayerBModel) -> bytes:
    """Tag 0x03 + CBOR with short int keys + epoch timestamps.

    Int key 0 carries the schema_id (the discriminator); only fields present in
    the model's aggressive map are emitted. Empty optional fields are omitted to
    save further bytes.
    """
    schema = _schema_for_kind(model.kind)
    raw_dict = model.model_dump()
    packed: dict[int, int | str] = {_AGGRESSIVE_SCHEMA_ID_KEY: schema.schema_id}
    for field, int_key in schema.aggressive_map.items():
        value = raw_dict.get(field, "")
        if value == "":
            continue  # skip empty optionals
        if field in schema.ts_fields:
            packed[int_key] = _iso_to_epoch(value)
        else:
            packed[int_key] = value
    body = cbor2.dumps(packed, canonical=True)
    return bytes([LAYER_B_TAG_CBOR_AGGR]) + body


def decode(raw: bytes) -> LayerBModel:
    """Dispatch on first byte, route by schema discriminator, validate.

    JSON/CBOR route on the body's `kind` field; aggressive routes on int key 0
    (absent → baseball_ticket). Unknown kind/schema_id raises ValueError; a
    body whose contents don't match the resolved schema raises pydantic
    ValidationError. Both propagate to the caller's safe-fallback.
    """
    if not raw:
        raise ValueError("layer_b is empty")
    tag, body = raw[0], raw[1:]
    if tag == LAYER_B_TAG_JSON:
        import json

        obj = json.loads(body)
        if not isinstance(obj, dict):
            raise ValueError("JSON layer_b body must be an object")
        schema = _schema_for_kind(obj.get("kind", "baseball_ticket"))
        return schema.model.model_validate(obj)
    if tag == LAYER_B_TAG_CBOR:
        obj = cbor2.loads(body)
        if not isinstance(obj, dict):
            raise ValueError("CBOR layer_b body must be a map")
        schema = _schema_for_kind(obj.get("kind", "baseball_ticket"))
        return schema.model.model_validate(obj)
    if tag == LAYER_B_TAG_CBOR_AGGR:
        packed = cbor2.loads(body)
        if not isinstance(packed, dict):
            raise ValueError("aggressive CBOR body must be a map")
        schema_id = packed.get(_AGGRESSIVE_SCHEMA_ID_KEY, _AGGRESSIVE_FALLBACK_SCHEMA_ID)
        schema = SCHEMA_CATALOG.get(schema_id)
        if schema is None:
            raise ValueError(f"unknown schema_id in aggressive layer_b: {schema_id!r}")
        unpacked: dict[str, object] = {"kind": schema.kind}
        for int_key, value in packed.items():
            if int_key == _AGGRESSIVE_SCHEMA_ID_KEY:
                continue  # discriminator, not a field
            field_name = schema.rev_map.get(int_key)
            if field_name is None:
                # Forward-compat: ignore unknown int keys rather than fail,
                # so an old decoder can still read newer tokens.
                continue
            if field_name in schema.ts_fields:
                unpacked[field_name] = _epoch_to_iso(int(value))
            else:
                unpacked[field_name] = value
        return schema.model.model_validate(unpacked)
    raise ValueError(f"unknown layer_b tag: 0x{tag:02x}")
