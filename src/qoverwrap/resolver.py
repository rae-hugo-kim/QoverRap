"""Resolver for QoverwRap — access-level-based layer exposure."""
from __future__ import annotations

from dataclasses import dataclass

from .crypto import verify_signature
from .decoder import decode_layers, DELIMITER


@dataclass(frozen=True)
class ResolvedPayload:
    """Result of resolving a QwrPayload at a given access level.

    ``signature`` is the raw Ed25519 bytes from the wire (Layer C) and is only
    populated when ``verified`` is True, for diagnostics or optional display.
    It is not treated as application user data (see claims: verified returns
    validated A/B plus verification outcome).
    """

    layer_a: str
    layer_b: bytes | None
    signature: bytes | None
    verified: bool


_VALID_LEVELS = {"public", "authenticated", "verified"}


def resolve(payload_str: str, access_level: str, public_key: bytes | None = None) -> ResolvedPayload:
    """Resolve a QR payload string according to access level policy.

    - "public": returns layer_a only (b=None, signature=None, verified=False)
    - "authenticated": returns layer_a + layer_b (signature=None, verified=False).
      This is an application output level for parsed metadata, not cryptographic
      authentication of Layer B.
    - "verified": returns layer_a + layer_b + signature (diagnostic) when the
      Ed25519 signature over the canonical message is valid; otherwise falls
      back to public-like output (b=None, signature=None, verified=False).
    - unknown access_level: treated as "public" (safe default)

    Per spec §8.3 [안전 기본값] / claim 8: any exception path (parsing, header,
    trailer, public-key absence, signature verification, or any unforeseen
    runtime exception) downgrades the result to public-level (Layer A only,
    or empty Layer A if the input itself is unusable).
    """
    if access_level not in _VALID_LEVELS:
        access_level = "public"

    try:
        layer_a, layer_b, layer_c = decode_layers(payload_str)
    except (ValueError, TypeError):
        if isinstance(payload_str, str) and DELIMITER in payload_str:
            layer_a = payload_str.split(DELIMITER, maxsplit=1)[0]
        elif isinstance(payload_str, str):
            layer_a = payload_str
        else:
            layer_a = ""
        return ResolvedPayload(layer_a, None, None, False)
    except Exception:
        # Defensive: catch unforeseen exceptions to honor the safe-fallback
        # promise of spec §8.3 / claim 8 ("any failure path → Layer A only").
        return ResolvedPayload("", None, None, False)

    def _or_none(b: bytes) -> bytes | None:
        return b if b else None

    if access_level == "public":
        return ResolvedPayload(layer_a, None, None, False)

    if access_level == "authenticated":
        return ResolvedPayload(layer_a, _or_none(layer_b), None, False)

    if public_key is None:
        return ResolvedPayload(layer_a, None, None, False)

    try:
        verified = verify_signature(public_key, layer_a, layer_b, layer_c)
    except (ValueError, TypeError, Exception):
        # safe-fallback (claim 8): any signature-verification exception → public.
        return ResolvedPayload(layer_a, None, None, False)

    if verified:
        # When verified, return Layer B as bytes (preserving b"" if present)
        # rather than collapsing to None — claim 7(iii) requires Layer B as
        # verified data, distinct from "absent Layer B" semantics.
        return ResolvedPayload(layer_a, layer_b, layer_c if layer_c else None, True)
    return ResolvedPayload(layer_a, None, None, False)
