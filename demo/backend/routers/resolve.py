"""Resolve endpoint: access-level-based layer exposure with trust-registry routing."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException

from qoverwrap.resolver import resolve as core_resolve

from .. import trust_registry
from .. import layer_b_codec
from ..schemas import ResolveRequest, ResolveResponse

router = APIRouter(prefix="/api", tags=["resolve"])

LayerBFormat = Literal["json", "cbor", "cbor_aggr"]

_LAYER_B_TAG_TO_FORMAT: dict[int, LayerBFormat] = {
    layer_b_codec.LAYER_B_TAG_JSON: "json",
    layer_b_codec.LAYER_B_TAG_CBOR: "cbor",
    layer_b_codec.LAYER_B_TAG_CBOR_AGGR: "cbor_aggr",
}


def _hex_to_bytes(value: str, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{name} is not valid hex: {exc}") from exc


def _decode_layer_b(raw: bytes | None) -> tuple[dict | None, LayerBFormat | None]:
    """Best-effort decode of Layer B via the demo codec.

    Returns (ticket_dict, format_tag). Either may be None. Empty/absent bytes
    and any decode failure (unknown tag, corrupt body, tampered content) yield
    (None, None) without raising — preserving claim 7(iii) and the resolver's
    safe-fallback contract. The raw hex is still surfaced by the caller.
    """
    if not raw:  # None or b"" (verified-empty, claim 7(iii))
        return None, None
    try:
        ticket = layer_b_codec.decode(raw)
    except Exception:
        return None, None
    # decode() only returns for the three known tags, so raw[0] is guaranteed
    # to be a mapped key here — index directly (preserves the Literal type).
    return ticket.model_dump(), _LAYER_B_TAG_TO_FORMAT[raw[0]]


@router.post("/resolve", response_model=ResolveResponse)
def resolve(req: ResolveRequest) -> ResolveResponse:
    issuer_id = None
    routed_pub: bytes | None = None

    # Try to extract layer_a from payload to read issuer prefix (without trusting decoded
    # bytes yet — we only need the plaintext head)
    layer_a_head = req.payload.split("\n---QWR---\n", maxsplit=1)[0]
    issuer_id = trust_registry.parse_issuer(layer_a_head)
    if issuer_id is not None:
        entry = trust_registry.get_entry(issuer_id)
        routed_pub = entry.public_key if entry else None

    # Choose effective public key: explicit override beats registry routing
    pub_bytes: bytes | None = None
    if req.public_key:
        pub_bytes = _hex_to_bytes(req.public_key, "public_key")
    elif routed_pub is not None:
        pub_bytes = routed_pub

    resolved = core_resolve(req.payload, req.access_level, pub_bytes)

    # Decode Layer B only from the bytes the resolver chose to expose. This
    # inherits the level/safe-fallback semantics for free: public hides Layer B
    # (None -> no decode), verified-empty keeps b"" (claim 7(iii) -> no decode),
    # and a tampered/failed verification collapses Layer B to None (no decode).
    layer_b_ticket, layer_b_format = _decode_layer_b(resolved.layer_b)
    # Every catalog model carries `kind`; derive the schema name from the
    # decoded dict so _decode_layer_b's signature stays unchanged.
    layer_b_schema = layer_b_ticket["kind"] if layer_b_ticket else None

    # Use `is not None` (not truthiness): an empty bytes Layer B with verified=True
    # is a legal outcome and must be distinguishable from "Layer B absent". See
    # claim 7(iii) and resolver.py — verified path preserves b"" instead of
    # collapsing to None.
    return ResolveResponse(
        layer_a=resolved.layer_a,
        layer_b=resolved.layer_b.hex() if resolved.layer_b is not None else None,
        layer_b_ticket=layer_b_ticket,
        layer_b_format=layer_b_format,
        layer_b_schema=layer_b_schema,
        signature=resolved.signature.hex() if resolved.signature is not None else None,
        verified=resolved.verified,
        issuer_id=issuer_id,
        routed_public_key=routed_pub.hex() if routed_pub is not None else None,
    )
