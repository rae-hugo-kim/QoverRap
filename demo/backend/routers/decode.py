"""Decode endpoint: split a QR payload string into 3 layers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from qoverwrap.decoder import decode_layers

from ..schemas import DecodeRequest, DecodeResponse

router = APIRouter(prefix="/api", tags=["decode"])


@router.post("/decode", response_model=DecodeResponse)
def decode(req: DecodeRequest) -> DecodeResponse:
    try:
        a, b, c = decode_layers(req.payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DecodeResponse(layer_a=a, layer_b=b.hex(), layer_c=c.hex())
