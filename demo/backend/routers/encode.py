"""Encode endpoints: build payload string and render QR PNG."""
from __future__ import annotations

import base64
import io

import qrcode
from fastapi import APIRouter, HTTPException
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

from qoverwrap.encoder import encode_layers

from ..schemas import EncodeRequest, EncodeResponse, QrImageRequest, QrImageResponse

router = APIRouter(prefix="/api", tags=["encode"])

_ECC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def _hex_to_bytes(value: str, name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{name} is not valid hex: {exc}") from exc


@router.post("/encode", response_model=EncodeResponse)
def encode(req: EncodeRequest) -> EncodeResponse:
    layer_b = _hex_to_bytes(req.layer_b, "layer_b") if req.layer_b else b""
    layer_c = _hex_to_bytes(req.layer_c, "layer_c") if req.layer_c else b""
    try:
        encoded = encode_layers(req.layer_a, layer_b, layer_c)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EncodeResponse(encoded=encoded)


@router.post("/qr-image", response_model=QrImageResponse)
def qr_image(req: QrImageRequest) -> QrImageResponse:
    qr = qrcode.QRCode(
        error_correction=_ECC_MAP[req.error_correction],
        box_size=req.box_size,
        border=req.border,
    )
    qr.add_data(req.encoded)
    try:
        qr.make(fit=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"QR generation failed: {exc}") from exc
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return QrImageResponse(image_png_base64=base64.b64encode(buf.getvalue()).decode("ascii"))
