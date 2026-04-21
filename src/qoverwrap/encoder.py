"""Encoder for QoverwRap 3-layer QR overlapping payloads."""
from __future__ import annotations

import base64
import struct

from .models import QwrPayload

DELIMITER = "\n---QWR---\n"
HEADER_VERSION = 0x01
HEADER_SIZE = 5  # 1B version + 2B b_len + 2B c_len


def encode_layers(layer_a: str, layer_b: bytes = b"", layer_c: bytes = b"") -> str:
    """Encode A/B/C layers into a single QR payload string.

    Layer A only (B and C both empty): return layer_a as-is, no delimiter.
    Layer A + B/C (at least one non-empty): return layer_a + DELIMITER + base64(header + layer_b + layer_c).
    """
    if not isinstance(layer_a, str):
        raise TypeError(f"layer_a must be str, got {type(layer_a).__name__}")
    if not isinstance(layer_b, bytes):
        raise TypeError(f"layer_b must be bytes, got {type(layer_b).__name__}")
    if not isinstance(layer_c, bytes):
        raise TypeError(f"layer_c must be bytes, got {type(layer_c).__name__}")
    if DELIMITER in layer_a:
        raise ValueError("layer_a must not contain the QWR delimiter string")
    if len(layer_b) > 65535:
        raise ValueError(f"layer_b length {len(layer_b)} exceeds uint16 max (65535)")
    if len(layer_c) > 65535:
        raise ValueError(f"layer_c length {len(layer_c)} exceeds uint16 max (65535)")

    if not layer_b and not layer_c:
        return layer_a

    header = struct.pack(">BHH", HEADER_VERSION, len(layer_b), len(layer_c))
    frame = header + layer_b + layer_c
    trailer = base64.b64encode(frame).decode("ascii")
    return layer_a + DELIMITER + trailer


def encode(payload: QwrPayload) -> str:
    """Encode a QwrPayload into a single QR payload string."""
    return encode_layers(payload.layer_a, payload.layer_b, payload.layer_c)
