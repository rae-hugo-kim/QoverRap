"""Pydantic schemas for the QoverwRap demo API.

All binary fields are serialized as hex strings (e.g. private/public keys, signature,
layer_b raw bytes). Layer A is plain UTF-8 text.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---- crypto -----------------------------------------------------------------

class GenerateKeyResponse(BaseModel):
    private_key: str = Field(..., description="Ed25519 seed, 64 hex chars (32 bytes)")
    public_key: str = Field(..., description="Ed25519 public key, 64 hex chars (32 bytes)")


class SignRequest(BaseModel):
    private_key: str
    layer_a: str
    layer_b: str = Field("", description="hex-encoded bytes (may be empty)")


class SignResponse(BaseModel):
    signature: str = Field(..., description="Ed25519 signature, 128 hex chars (64 bytes)")


class VerifyRequest(BaseModel):
    public_key: str
    layer_a: str
    layer_b: str = ""
    signature: str


class VerifyResponse(BaseModel):
    valid: bool


# ---- encode / decode --------------------------------------------------------

class EncodeRequest(BaseModel):
    layer_a: str
    layer_b: str = Field("", description="hex-encoded bytes (may be empty)")
    layer_c: str = Field("", description="hex-encoded signature bytes (may be empty)")


class EncodeResponse(BaseModel):
    encoded: str = Field(..., description="Full QR payload string")


class QrImageRequest(BaseModel):
    encoded: str
    box_size: int = Field(10, ge=2, le=40)
    border: int = Field(4, ge=0, le=16)
    error_correction: Literal["L", "M", "Q", "H"] = "H"


class QrImageResponse(BaseModel):
    image_png_base64: str = Field(..., description="base64-encoded PNG (no data URI prefix)")


class DecodeRequest(BaseModel):
    payload: str


class DecodeResponse(BaseModel):
    layer_a: str
    layer_b: str = Field("", description="hex-encoded bytes")
    layer_c: str = Field("", description="hex-encoded signature bytes")


# ---- resolve ----------------------------------------------------------------

AccessLevel = Literal["public", "authenticated", "verified"]


class ResolveRequest(BaseModel):
    payload: str
    access_level: AccessLevel
    public_key: Optional[str] = Field(
        None,
        description="Hex-encoded public key. If omitted, the trust registry will be consulted using the issuer prefix in Layer A.",
    )


class ResolveResponse(BaseModel):
    layer_a: str
    layer_b: Optional[str] = None
    layer_c: Optional[str] = None
    verified: bool
    issuer_id: Optional[str] = Field(
        None,
        description="Issuer id parsed from Layer A (qwr:<issuer-id>|...), if any.",
    )
    routed_public_key: Optional[str] = Field(
        None,
        description="Hex-encoded public key chosen via trust registry routing. None if not routed.",
    )


# ---- trust registry ---------------------------------------------------------

class TrustEntry(BaseModel):
    issuer_id: str
    display_name: str
    theme_color: str = Field(..., description="CSS color (hex or name) for UI theming")
    accent_color: str = Field(..., description="Secondary CSS color")
    logo_text: str = Field(..., description="Short label rendered as logo placeholder")
    public_key: str = Field(..., description="Hex-encoded Ed25519 public key")


class TrustListResponse(BaseModel):
    entries: list[TrustEntry]
