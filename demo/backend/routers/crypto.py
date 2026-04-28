"""Crypto endpoints: keypair generation, signing, verification."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from qoverwrap.crypto import generate_keypair, sign_layers, verify_signature

from ..schemas import (
    GenerateKeyResponse,
    SignRequest,
    SignResponse,
    VerifyRequest,
    VerifyResponse,
)

router = APIRouter(prefix="/api", tags=["crypto"])


def _hex_to_bytes(value: str, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{name} is not valid hex: {exc}") from exc


@router.post("/generate-key", response_model=GenerateKeyResponse)
def generate_key() -> GenerateKeyResponse:
    priv, pub = generate_keypair()
    return GenerateKeyResponse(private_key=priv.hex(), public_key=pub.hex())


@router.post("/sign", response_model=SignResponse)
def sign(req: SignRequest) -> SignResponse:
    priv = _hex_to_bytes(req.private_key, "private_key")
    if len(priv) != 32:
        raise HTTPException(status_code=422, detail="private_key must be 32 bytes (64 hex chars)")
    layer_b = _hex_to_bytes(req.layer_b, "layer_b") if req.layer_b else b""
    sig = sign_layers(priv, req.layer_a, layer_b)
    return SignResponse(signature=sig.hex())


@router.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest) -> VerifyResponse:
    pub = _hex_to_bytes(req.public_key, "public_key")
    if len(pub) != 32:
        raise HTTPException(status_code=422, detail="public_key must be 32 bytes")
    layer_b = _hex_to_bytes(req.layer_b, "layer_b") if req.layer_b else b""
    sig = _hex_to_bytes(req.signature, "signature")
    return VerifyResponse(valid=verify_signature(pub, req.layer_a, layer_b, sig))
