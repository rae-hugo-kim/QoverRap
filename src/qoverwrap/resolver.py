"""Resolver for QoverwRap — access-level-based layer exposure."""
from __future__ import annotations

from dataclasses import dataclass

from .decoder import decode_layers, DELIMITER
from .crypto import verify_signature


@dataclass(frozen=True)
class ResolvedPayload:
    """Result of resolving a QwrPayload at a given access level."""
    layer_a: str
    layer_b: bytes | None  # None if not authorized
    layer_c: bytes | None  # None if not authorized
    verified: bool  # True only if signature was checked and valid


_VALID_LEVELS = {"public", "authenticated", "verified"}


def resolve(payload_str: str, access_level: str, public_key: bytes | None = None) -> ResolvedPayload:
    """Resolve a QR payload string according to access level policy.

    - "public": returns layer_a only (b=None, c=None, verified=False)
    - "authenticated": returns layer_a + layer_b (c=None, verified=False)
    - "verified": returns layer_a + layer_b + layer_c, verified=True only if signature valid
      If signature invalid, falls back to public (b=None, c=None, verified=False)
    - unknown access_level: treated as "public" (safe default)
    """
    # Normalize access_level
    if access_level not in _VALID_LEVELS:
        access_level = "public"

    # Decode the payload
    try:
        layer_a, layer_b, layer_c = decode_layers(payload_str)
    except ValueError:
        # Corrupted trailer — extract layer_a before delimiter if present
        if DELIMITER in payload_str:
            layer_a = payload_str.split(DELIMITER, maxsplit=1)[0]
        else:
            layer_a = payload_str
        return ResolvedPayload(layer_a, None, None, False)

    # Convert empty bytes to None for unauthorized/absent layers
    def _or_none(b: bytes) -> bytes | None:
        return b if b else None

    if access_level == "public":
        return ResolvedPayload(layer_a, None, None, False)

    if access_level == "authenticated":
        return ResolvedPayload(layer_a, _or_none(layer_b), None, False)

    # access_level == "verified"
    if public_key is None:
        return ResolvedPayload(layer_a, None, None, False)

    if verify_signature(public_key, layer_a, layer_b, layer_c):
        return ResolvedPayload(layer_a, _or_none(layer_b), _or_none(layer_c), True)
    else:
        return ResolvedPayload(layer_a, None, None, False)
