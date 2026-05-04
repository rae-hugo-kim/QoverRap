"""Cryptographic signing and verification for QoverwRap Layer C."""
from __future__ import annotations

import struct

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .encoder import HEADER_VERSION

SIGNING_MAGIC = b"QWR1"
MAX_U16 = 65535


def canonical_signing_message(
    layer_a: str,
    layer_b: bytes,
    *,
    version: int = HEADER_VERSION,
) -> bytes:
    """Build the deterministic Ed25519 signing message (spec §8.1.1).

    Layout: MAGIC || uint8(version) || uint16_be(len(layer_a_utf8))
              || layer_a_utf8 || uint16_be(len(layer_b)) || layer_b
    """
    if not isinstance(layer_a, str):
        raise TypeError("layer_a must be str")
    if not isinstance(layer_b, bytes):
        raise TypeError("layer_b must be bytes")
    if not (0 <= version <= 255):
        raise ValueError("version must fit in uint8")

    layer_a_bytes = layer_a.encode("utf-8")
    la_len = len(layer_a_bytes)
    lb_len = len(layer_b)
    if la_len > MAX_U16:
        raise ValueError(f"layer_a UTF-8 length {la_len} exceeds uint16 max ({MAX_U16})")
    if lb_len > MAX_U16:
        raise ValueError(f"layer_b length {lb_len} exceeds uint16 max ({MAX_U16})")

    # Spec §8.1.1 / claim 12 layout — interleaved length||value, NOT
    # lengths-grouped. External implementers that follow the spec will
    # produce incompatible signatures if this order is changed.
    return (
        SIGNING_MAGIC
        + struct.pack(">B", version)
        + struct.pack(">H", la_len)
        + layer_a_bytes
        + struct.pack(">H", lb_len)
        + layer_b
    )


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate an Ed25519 keypair. Returns (private_key_bytes, public_key_bytes)."""
    private_key = Ed25519PrivateKey.generate()
    seed_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (seed_bytes, public_bytes)


def sign_layers(private_key: bytes, layer_a: str, layer_b: bytes) -> bytes:
    """Sign the canonical message for (layer_a, layer_b); returns Layer C signature bytes."""
    if not isinstance(private_key, bytes):
        raise TypeError("private_key must be bytes")
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    message = canonical_signing_message(layer_a, layer_b)
    return key.sign(message)


def verify_signature(public_key: bytes, layer_a: str, layer_b: bytes, layer_c: bytes) -> bool:
    """Verify that layer_c is a valid Ed25519 signature over the canonical message.

    Returns True if valid, False if invalid or on expected input errors.
    """
    if not isinstance(public_key, bytes):
        raise TypeError("public_key must be bytes")
    try:
        key = Ed25519PublicKey.from_public_bytes(public_key)
        message = canonical_signing_message(layer_a, layer_b)
        key.verify(layer_c, message)
        return True
    except InvalidSignature:
        return False
    except (TypeError, ValueError):
        return False
