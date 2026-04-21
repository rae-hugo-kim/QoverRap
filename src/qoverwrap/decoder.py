"""Decoder for QoverwRap 3-layer QR overlapping payloads."""
from __future__ import annotations

import base64
import struct

from .models import QwrPayload

DELIMITER = "\n---QWR---\n"
HEADER_VERSION = 0x01
HEADER_SIZE = 5  # 1B version + 2B b_len + 2B c_len


def decode_layers(payload: str) -> tuple[str, bytes, bytes]:
    """Decode a QR payload string back into (layer_a, layer_b, layer_c)."""
    if not isinstance(payload, str):
        raise TypeError(f"payload must be str, got {type(payload).__name__}")

    if DELIMITER not in payload:
        return (payload, b"", b"")

    layer_a, trailer = payload.split(DELIMITER, maxsplit=1)

    try:
        frame = base64.b64decode(trailer)
    except Exception as exc:
        raise ValueError(f"Invalid base64 trailer: {exc}") from exc

    if len(frame) < HEADER_SIZE:
        raise ValueError(
            f"Frame too short: expected >= {HEADER_SIZE} bytes, got {len(frame)}"
        )

    version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])

    if version != HEADER_VERSION:
        raise ValueError(
            f"Unsupported version: 0x{version:02X} (expected 0x{HEADER_VERSION:02X})"
        )

    if HEADER_SIZE + b_len + c_len > len(frame):
        raise ValueError(
            f"Frame too short for declared lengths: "
            f"need {HEADER_SIZE + b_len + c_len}, have {len(frame)}"
        )

    layer_b = frame[HEADER_SIZE : HEADER_SIZE + b_len]
    layer_c = frame[HEADER_SIZE + b_len : HEADER_SIZE + b_len + c_len]

    return (layer_a, layer_b, layer_c)


def decode(payload: str) -> QwrPayload:
    """Decode a QR payload string into a QwrPayload."""
    a, b, c = decode_layers(payload)
    return QwrPayload(a, b, c)
