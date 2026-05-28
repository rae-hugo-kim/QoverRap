"""Redeem endpoint: one-time-use ticket counter for QoverwRap demo (M1).

Flow:
  1. Decode payload → layer_a / layer_b / layer_c (signature).
  2. Route public key via trust registry (issuer prefix in layer_a).
  3. Verify Ed25519 signature.
  4. On valid signature: consult SQLite counter keyed on layer_c hex.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from qoverwrap.decoder import decode_layers
from qoverwrap.crypto import verify_signature

from .. import trust_registry
from ..redemption_store import RedemptionStore
from ..schemas import RedeemRequest, RedeemResponse

router = APIRouter(prefix="/api", tags=["redeem"])

_store: RedemptionStore | None = None


def get_store() -> RedemptionStore:
    """Lazy-init redemption store. Tests override via `app.dependency_overrides`."""
    global _store
    if _store is None:
        _store = RedemptionStore()
    return _store


@router.post("/redeem", response_model=RedeemResponse)
def redeem(
    req: RedeemRequest,
    store: RedemptionStore = Depends(get_store),
) -> RedeemResponse:
    # 1. Decode
    try:
        layer_a, layer_b_bytes, layer_c_bytes = decode_layers(req.payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # 2. Route public key
    pub_bytes = trust_registry.route_public_key(layer_a)
    if pub_bytes is None:
        # No registered issuer → treat as invalid signature
        return RedeemResponse(status="invalid", use_count=0)

    # 3. Verify signature
    valid = verify_signature(pub_bytes, layer_a, layer_b_bytes, layer_c_bytes)
    if not valid:
        return RedeemResponse(status="invalid", use_count=0)

    # 4. Consult counter
    signature_hex = layer_c_bytes.hex()
    status, use_count = store.redeem(signature_hex, req.max_uses)
    return RedeemResponse(status=status, use_count=use_count)
