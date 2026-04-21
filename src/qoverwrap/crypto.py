"""Cryptographic signing and verification for QoverwRap Layer C."""
from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


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
    """Sign layer_a + layer_b content, returning the signature bytes for Layer C."""
    if not isinstance(private_key, bytes):
        raise TypeError("private_key must be bytes")
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    message = layer_a.encode("utf-8") + layer_b
    return key.sign(message)


def verify_signature(public_key: bytes, layer_a: str, layer_b: bytes, layer_c: bytes) -> bool:
    """Verify that layer_c is a valid signature over layer_a + layer_b.

    Returns True if valid, False if invalid.
    """
    if not isinstance(public_key, bytes):
        raise TypeError("public_key must be bytes")
    try:
        key = Ed25519PublicKey.from_public_bytes(public_key)
        message = layer_a.encode("utf-8") + layer_b
        key.verify(layer_c, message)
        return True
    except (InvalidSignature, Exception):
        return False
