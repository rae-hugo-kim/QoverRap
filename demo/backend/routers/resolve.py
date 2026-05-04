"""Resolve endpoint: access-level-based layer exposure with trust-registry routing."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from qoverwrap.resolver import resolve as core_resolve

from .. import trust_registry
from ..schemas import ResolveRequest, ResolveResponse

router = APIRouter(prefix="/api", tags=["resolve"])


def _hex_to_bytes(value: str, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{name} is not valid hex: {exc}") from exc


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

    return ResolveResponse(
        layer_a=resolved.layer_a,
        layer_b=resolved.layer_b.hex() if resolved.layer_b else None,
        signature=resolved.signature.hex() if resolved.signature else None,
        verified=resolved.verified,
        issuer_id=issuer_id,
        routed_public_key=routed_pub.hex() if routed_pub else None,
    )
