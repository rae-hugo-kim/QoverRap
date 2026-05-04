"""Trust-registry endpoints: list registered issuers (theme metadata + public key).

Demo-only convenience: also exposes a sign-as-issuer endpoint so the frontend can
produce themed QR codes without managing private keys client-side. Real deployments
would have private keys held only by the issuing service.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from qoverwrap.crypto import sign_layers

from .. import trust_registry
from ..schemas import TrustEntry, TrustListResponse

router = APIRouter(prefix="/api", tags=["trust"])


@router.get("/trust", response_model=TrustListResponse)
def list_trust() -> TrustListResponse:
    entries = [
        TrustEntry(
            issuer_id=e.issuer_id,
            display_name=e.display_name,
            theme_color=e.theme_color,
            accent_color=e.accent_color,
            logo_text=e.logo_text,
            public_key=e.public_key.hex(),
        )
        for e in trust_registry.list_entries()
    ]
    return TrustListResponse(entries=entries)


@router.post("/trust/{issuer_id}/sign", response_model=dict)
def sign_as_issuer(issuer_id: str, body: dict) -> dict:
    """Demo-only: sign (layer_a, layer_b) using the issuer's bundled private key.

    Body: {"layer_a": str, "layer_b": str (hex)}

    Disabled unless ``QWR_ENABLE_DEMO_SIGNING=1`` is set (prevents accidental
    exposure in production-like deployments).
    """
    if os.environ.get("QWR_ENABLE_DEMO_SIGNING", "").strip() != "1":
        raise HTTPException(
            status_code=403,
            detail="Demo issuer signing is disabled. Set QWR_ENABLE_DEMO_SIGNING=1 to enable.",
        )

    entry = trust_registry.get_entry(issuer_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown issuer: {issuer_id}")

    layer_a = body.get("layer_a")
    if not isinstance(layer_a, str):
        raise HTTPException(status_code=422, detail="layer_a must be a string")

    layer_b_hex = body.get("layer_b", "") or ""
    try:
        layer_b = bytes.fromhex(layer_b_hex) if layer_b_hex else b""
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"layer_b not valid hex: {exc}") from exc

    sig = sign_layers(entry.private_key, layer_a, layer_b)
    return {
        "issuer_id": issuer_id,
        "signature": sig.hex(),
        "public_key": entry.public_key.hex(),
    }
