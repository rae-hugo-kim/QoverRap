"""Data models for QoverwRap QR overlapping layers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QwrPayload:
    """Immutable container for a 3-layer QR overlapping payload.

    Attributes:
        layer_a: Public text layer (UTF-8, readable by standard QR scanners).
        layer_b: Context metadata layer (binary).
        layer_c: Verification/signature layer (binary).
    """
    layer_a: str
    layer_b: bytes = b""
    layer_c: bytes = b""
