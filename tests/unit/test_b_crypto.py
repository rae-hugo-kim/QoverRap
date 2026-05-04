"""B-C1~5: Crypto unit tests for QoverwRap Layer C signing and verification.

Tests the generate_keypair(), sign_layers(), and verify_signature() functions
defined in qoverwrap.crypto using Ed25519 digital signatures over Layer A + Layer B.

Test IDs
--------
B-C1  Layer C signature generation
B-C2  Correct key verification
B-C3  Wrong key verification
B-C4  Tampered payload verification
B-C5  Edge cases and defense
"""
from __future__ import annotations

import os

import pytest

from qoverwrap.crypto import (
    canonical_signing_message,
    generate_keypair,
    sign_layers,
    verify_signature,
)

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _sample_layer_a(n: int = 80) -> str:
    base = "https://qoverwrap.example.com/v1/card?id=abc123&seq="
    return (base + "X" * max(0, n - len(base)))[:n]


def _sample_layer_b(n: int = 96) -> bytes:
    stub = b'{"issuer":"QoverwRap","ts":1700000000,"nonce":"'
    pad = b"A" * max(0, n - len(stub) - 2)
    return (stub + pad + b'"}')[:n]


# ---------------------------------------------------------------------------
# B-C1: Layer C signature generation
# ---------------------------------------------------------------------------


class TestBC1SignatureGeneration:
    """B-C1: generate_keypair() and sign_layers() basic contract."""

    def test_generate_keypair_returns_two_bytes(self) -> None:
        """B-C1 — generate_keypair() returns a tuple of (bytes, bytes)."""
        result = generate_keypair()
        assert isinstance(result, tuple), (
            f"[B-C1] Expected tuple, got {type(result).__name__}"
        )
        assert len(result) == 2, (
            f"[B-C1] Expected tuple of length 2, got length {len(result)}"
        )
        private_key, public_key = result
        assert isinstance(private_key, bytes), (
            f"[B-C1] private_key must be bytes, got {type(private_key).__name__}"
        )
        assert isinstance(public_key, bytes), (
            f"[B-C1] public_key must be bytes, got {type(public_key).__name__}"
        )
        print("[B-C1] test_generate_keypair_returns_two_bytes — PASS")

    def test_generate_keypair_private_key_length(self) -> None:
        """B-C1 — private key is 32 bytes (Ed25519 seed size)."""
        private_key, _public_key = generate_keypair()
        assert len(private_key) == 32, (
            f"[B-C1] private_key length: expected 32, got {len(private_key)}"
        )
        print("[B-C1] test_generate_keypair_private_key_length — PASS")

    def test_generate_keypair_unique(self) -> None:
        """B-C1 — two calls produce different keys."""
        private_key_1, public_key_1 = generate_keypair()
        private_key_2, public_key_2 = generate_keypair()
        assert private_key_1 != private_key_2, (
            "[B-C1] Two generate_keypair() calls returned identical private keys"
        )
        assert public_key_1 != public_key_2, (
            "[B-C1] Two generate_keypair() calls returned identical public keys"
        )
        print("[B-C1] test_generate_keypair_unique — PASS")

    def test_sign_returns_bytes(self) -> None:
        """B-C1 — sign_layers() returns bytes."""
        private_key, _public_key = generate_keypair()
        sig = sign_layers(private_key, _sample_layer_a(), _sample_layer_b())
        assert isinstance(sig, bytes), (
            f"[B-C1] sign_layers() must return bytes, got {type(sig).__name__}"
        )
        print("[B-C1] test_sign_returns_bytes — PASS")

    def test_sign_returns_64_bytes(self) -> None:
        """B-C1 — Ed25519 signature is always 64 bytes."""
        private_key, _public_key = generate_keypair()
        sig = sign_layers(private_key, _sample_layer_a(), _sample_layer_b())
        assert len(sig) == 64, (
            f"[B-C1] Ed25519 signature must be 64 bytes, got {len(sig)}"
        )
        print("[B-C1] test_sign_returns_64_bytes — PASS")


# ---------------------------------------------------------------------------
# B-C2: Correct key verification
# ---------------------------------------------------------------------------


class TestBC2CorrectKeyVerification:
    """B-C2: verify_signature() returns True for valid sign/verify pairs."""

    def test_verify_valid_signature(self) -> None:
        """B-C2 — sign with private, verify with matching public → True."""
        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        result = verify_signature(public_key, layer_a, layer_b, layer_c)
        assert result is True, (
            f"[B-C2] verify_signature() returned {result!r}, expected True"
        )
        print("[B-C2] test_verify_valid_signature — PASS")

    def test_verify_with_sample_payload(self) -> None:
        """B-C2 — sign/verify with realistic layer_a URL + layer_b JSON."""
        private_key, public_key = generate_keypair()
        layer_a = "https://qoverwrap.example.com/v1/card?id=test42&seq=1"
        layer_b = b'{"issuer":"QoverwRap","ts":1700000001,"nonce":"abc123XYZ"}'
        layer_c = sign_layers(private_key, layer_a, layer_b)
        result = verify_signature(public_key, layer_a, layer_b, layer_c)
        assert result is True, (
            f"[B-C2] verify_signature() with sample payload returned {result!r}, expected True"
        )
        print("[B-C2] test_verify_with_sample_payload — PASS")

    def test_verify_different_payloads_different_signatures(self) -> None:
        """B-C2 — two different (a,b) inputs produce different signatures."""
        private_key, _public_key = generate_keypair()
        layer_a_1 = "https://qoverwrap.example.com/v1/card?id=1"
        layer_b_1 = b'{"nonce":"aaa"}'
        layer_a_2 = "https://qoverwrap.example.com/v1/card?id=2"
        layer_b_2 = b'{"nonce":"bbb"}'
        sig_1 = sign_layers(private_key, layer_a_1, layer_b_1)
        sig_2 = sign_layers(private_key, layer_a_2, layer_b_2)
        assert sig_1 != sig_2, (
            "[B-C2] Different (layer_a, layer_b) inputs produced identical signatures"
        )
        print("[B-C2] test_verify_different_payloads_different_signatures — PASS")


# ---------------------------------------------------------------------------
# B-C3: Wrong key verification
# ---------------------------------------------------------------------------


class TestBC3WrongKeyVerification:
    """B-C3: verify_signature() returns False when the public key does not match."""

    def test_verify_wrong_public_key(self) -> None:
        """B-C3 — sign with key1, verify with key2's public → False."""
        private_key_1, _public_key_1 = generate_keypair()
        _private_key_2, public_key_2 = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = sign_layers(private_key_1, layer_a, layer_b)
        result = verify_signature(public_key_2, layer_a, layer_b, layer_c)
        assert result is False, (
            f"[B-C3] verify_signature() with wrong public key returned {result!r}, expected False"
        )
        print("[B-C3] test_verify_wrong_public_key — PASS")

    def test_verify_with_random_bytes_as_signature(self) -> None:
        """B-C3 — random 64 bytes as layer_c → False."""
        _private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        random_sig = os.urandom(64)
        result = verify_signature(public_key, layer_a, layer_b, random_sig)
        assert result is False, (
            f"[B-C3] verify_signature() with random bytes returned {result!r}, expected False"
        )
        print("[B-C3] test_verify_with_random_bytes_as_signature — PASS")


# ---------------------------------------------------------------------------
# B-C4: Tampered payload verification
# ---------------------------------------------------------------------------


class TestBC4TamperedPayloadVerification:
    """B-C4: verify_signature() returns False when content is tampered."""

    def test_tampered_layer_a(self) -> None:
        """B-C4 — sign, modify layer_a, verify → False."""
        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        tampered_a = layer_a + "_tampered"
        result = verify_signature(public_key, tampered_a, layer_b, layer_c)
        assert result is False, (
            f"[B-C4] verify_signature() with tampered layer_a returned {result!r}, expected False"
        )
        print("[B-C4] test_tampered_layer_a — PASS")

    def test_tampered_layer_b(self) -> None:
        """B-C4 — sign, modify layer_b, verify → False."""
        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        tampered_b = layer_b[:-1] + bytes([layer_b[-1] ^ 0xFF])
        result = verify_signature(public_key, layer_a, tampered_b, layer_c)
        assert result is False, (
            f"[B-C4] verify_signature() with tampered layer_b returned {result!r}, expected False"
        )
        print("[B-C4] test_tampered_layer_b — PASS")

    def test_tampered_layer_c_single_bit(self) -> None:
        """B-C4 — flip one bit in signature → False."""
        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        # Flip the first bit of the signature
        tampered_c = bytes([layer_c[0] ^ 0x01]) + layer_c[1:]
        result = verify_signature(public_key, layer_a, layer_b, tampered_c)
        assert result is False, (
            f"[B-C4] verify_signature() with single-bit-flipped signature returned {result!r}, expected False"
        )
        print("[B-C4] test_tampered_layer_c_single_bit — PASS")

    def test_empty_signature(self) -> None:
        """B-C4 — layer_c=b'' → False."""
        _private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        result = verify_signature(public_key, layer_a, layer_b, b"")
        assert result is False, (
            f"[B-C4] verify_signature() with empty signature returned {result!r}, expected False"
        )
        print("[B-C4] test_empty_signature — PASS")


# ---------------------------------------------------------------------------
# B-C5: Edge cases and defense
# ---------------------------------------------------------------------------


class TestBC5EdgeCases:
    """B-C5: Edge cases and defensive behavior for crypto functions."""

    def test_sign_empty_layers(self) -> None:
        """B-C5 — sign_layers with layer_a='' and layer_b=b'' works (no crash)."""
        private_key, public_key = generate_keypair()
        sig = sign_layers(private_key, "", b"")
        assert isinstance(sig, bytes), (
            f"[B-C5] sign_layers() with empty inputs must return bytes, got {type(sig).__name__}"
        )
        assert len(sig) == 64, (
            f"[B-C5] Ed25519 signature must be 64 bytes, got {len(sig)}"
        )
        result = verify_signature(public_key, "", b"", sig)
        assert result is True, (
            f"[B-C5] verify_signature() with empty layers returned {result!r}, expected True"
        )
        print("[B-C5] test_sign_empty_layers — PASS")

    def test_sign_unicode_layer_a(self) -> None:
        """B-C5 — Korean/emoji in layer_a signs and verifies correctly."""
        private_key, public_key = generate_keypair()
        layer_a = "안녕하세요 QoverwRap 🎉 테스트"
        layer_b = _sample_layer_b()
        sig = sign_layers(private_key, layer_a, layer_b)
        result = verify_signature(public_key, layer_a, layer_b, sig)
        assert result is True, (
            f"[B-C5] verify_signature() with unicode layer_a returned {result!r}, expected True"
        )
        print("[B-C5] test_sign_unicode_layer_a — PASS")

    def test_sign_large_payload(self) -> None:
        """B-C5 — 10KB layer_b signs and verifies."""
        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = bytes([i % 256 for i in range(10 * 1024)])
        sig = sign_layers(private_key, layer_a, layer_b)
        assert len(sig) == 64, (
            f"[B-C5] Ed25519 signature must be 64 bytes even for large payloads, got {len(sig)}"
        )
        result = verify_signature(public_key, layer_a, layer_b, sig)
        assert result is True, (
            f"[B-C5] verify_signature() with 10KB layer_b returned {result!r}, expected True"
        )
        print("[B-C5] test_sign_large_payload — PASS")

    def test_invalid_private_key_type(self) -> None:
        """B-C5 — passing non-bytes private_key raises TypeError."""
        with pytest.raises(TypeError):
            sign_layers("not bytes", _sample_layer_a(), _sample_layer_b())  # type: ignore[arg-type]
        print("[B-C5] test_invalid_private_key_type — PASS")

    def test_invalid_public_key_type(self) -> None:
        """B-C5 — passing non-bytes public_key raises TypeError."""
        with pytest.raises(TypeError):
            verify_signature("not bytes", _sample_layer_a(), _sample_layer_b(), b"\x00" * 64)  # type: ignore[arg-type]
        print("[B-C5] test_invalid_public_key_type — PASS")


class TestBC6CanonicalBoundaries:
    """B-C6: canonical signing message disambiguates A/B boundaries and binds version."""

    def test_signature_is_boundary_aware(self) -> None:
        """B-C6 — sign('ab', b'c') must not verify as ('a', b'bc')."""
        private_key, public_key = generate_keypair()
        sig = sign_layers(private_key, "ab", b"c")
        assert verify_signature(public_key, "ab", b"c", sig) is True
        assert verify_signature(public_key, "a", b"bc", sig) is False
        print("[B-C6] test_signature_is_boundary_aware — PASS")

    def test_canonical_messages_differ_by_signing_version(self) -> None:
        """B-C6 — canonical bytes differ when version byte in signing message differs."""
        a, b = "x", b"y"
        m1 = canonical_signing_message(a, b, version=0x01)
        m2 = canonical_signing_message(a, b, version=0x02)
        assert m1 != m2
        print("[B-C6] test_canonical_messages_differ_by_signing_version — PASS")

    def test_wrong_version_signature_does_not_verify(self) -> None:
        """B-C6 — signature over version=0x02 canonical must not verify under default v1 verify."""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        private_key, public_key = generate_keypair()
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        key = Ed25519PrivateKey.from_private_bytes(private_key)
        alt_msg = canonical_signing_message(layer_a, layer_b, version=0x02)
        sig_alt = key.sign(alt_msg)
        assert verify_signature(public_key, layer_a, layer_b, sig_alt) is False
        print("[B-C6] test_wrong_version_signature_does_not_verify — PASS")
