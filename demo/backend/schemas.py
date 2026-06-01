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


class EncodeLayerBRequest(BaseModel):
    """Build a Layer B hex string from structured ticket data via the demo codec.

    The chosen format determines the byte layout (and downstream QR size).
    """

    ticket: dict = Field(
        ..., description="TicketLayerB fields as a JSON object (validated server-side)"
    )
    format: Literal["json", "cbor", "cbor_aggr"] = Field(
        "json", description="Layer B serialization format — see layer_b_codec"
    )


class EncodeLayerBResponse(BaseModel):
    layer_b_hex: str = Field(..., description="Encoded Layer B bytes as hex string")
    byte_size: int = Field(..., description="Encoded Layer B size in bytes")
    format: Literal["json", "cbor", "cbor_aggr"]


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
    layer_b_ticket: Optional[dict] = Field(
        None,
        description="Layer B bytes decoded via the demo codec (TicketLayerB.model_dump()). Present only when Layer B is exposed and decodable; None otherwise.",
    )
    layer_b_format: Optional[Literal["json", "cbor", "cbor_aggr"]] = Field(
        None,
        description="Layer B serialization format derived from the leading tag byte (0x01->json, 0x02->cbor, 0x03->cbor_aggr). None when Layer B is absent/empty/undecodable.",
    )
    signature: Optional[str] = Field(
        None,
        description="Hex-encoded Ed25519 signature when verified=True; diagnostic only, not user data.",
    )
    verified: bool
    issuer_id: Optional[str] = Field(
        None,
        description="Issuer id parsed from Layer A (qwr:<issuer-id>|...), if any.",
    )
    routed_public_key: Optional[str] = Field(
        None,
        description="Hex-encoded public key chosen via trust registry routing. None if not routed.",
    )


# ---- redeem -----------------------------------------------------------------

class RedeemRequest(BaseModel):
    payload: str
    max_uses: int = Field(1, ge=1, description="Maximum number of times this ticket may be redeemed")


class RedeemResponse(BaseModel):
    status: Literal["ok", "already_used", "invalid"]
    use_count: int = Field(..., description="Current use count after this attempt (0 when invalid)")


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


# ---- visit collection (stamp rally) -----------------------------------------

class VisitCollectRequest(BaseModel):
    ticket_payload: str = Field(..., description="The attendee's full ticket QR payload string")
    booth_id: str


class VisitCollectResponse(BaseModel):
    status: Literal["collected", "already_collected", "ticket_invalid", "wrong_issuer"]
    booth_id: str
    booth_name: Optional[str] = None
    visitor_token: Optional[str] = Field(
        None,
        description="sha256(ticket Layer C)[:32] — pseudonymous binding token, carries no PII.",
    )
    visited_at: Optional[str] = None
    collection: Optional[str] = None
    emoji: Optional[str] = None
    marker_payload: Optional[str] = Field(
        None,
        description="Full wire-format marker string for offline re-verification (present only when collected).",
    )


class VisitVerifyRequest(BaseModel):
    marker_payload: str


class VisitVerifyResponse(BaseModel):
    verified: bool
    booth_id: Optional[str] = None
    booth_name: Optional[str] = None
    visitor_token: Optional[str] = None
    visited_at: Optional[str] = None
    collection: Optional[str] = None


class BoothInfo(BaseModel):
    booth_id: str
    issuer_id: str
    booth_name: str
    collection: str
    emoji: str


class BoothListResponse(BaseModel):
    booths: list[BoothInfo]
