"""B-R1~5: Resolver unit tests for QoverwRap access-level policy gate.

Tests the resolve() function defined in qoverwrap.resolver against the
Phase B access level policy:

  - "public"        → Layer A only
  - "authenticated" → Layer A + B (parsed metadata; not cryptographically authenticated)
  - "verified"      → Layer A + B + signature bytes when Ed25519 verifies
  - unknown level   → safe default (same as "public")

Test IDs
--------
B-R1  public → A only
B-R2  authenticated → A+B
B-R3  verified → A+B+signature (diagnostic)
B-R4  unknown → safe default
B-R5  forgery/partial/expired → B/C hidden
"""
from __future__ import annotations

import pytest

from qoverwrap.encoder import encode_layers
from qoverwrap.crypto import generate_keypair, sign_layers
from qoverwrap.resolver import resolve, ResolvedPayload


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


def _sample_layer_c(n: int = 64) -> bytes:
    return bytes([i % 256 for i in range(n)])


# ---------------------------------------------------------------------------
# B-R1: public → A only
# ---------------------------------------------------------------------------

class TestBR1Public:
    """B-R1: resolve(..., "public") returns Layer A only."""

    def test_public_returns_layer_a(self) -> None:
        """B-R1 — resolve public: layer_a matches, layer_b is None, signature is None."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = _sample_layer_c()
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "public")

        assert resolved.layer_a == layer_a, (
            f"[B-R1] layer_a mismatch: expected {layer_a!r}, got {resolved.layer_a!r}"
        )
        assert resolved.layer_b is None, (
            f"[B-R1] layer_b should be None for public access, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, (
            f"[B-R1] signature should be None for public access, got {resolved.signature!r}"
        )
        print("[B-R1] test_public_returns_layer_a — PASS")

    def test_public_verified_false(self) -> None:
        """B-R1 — resolve public: verified is False."""
        encoded = encode_layers(_sample_layer_a(), _sample_layer_b())

        resolved = resolve(encoded, "public")

        assert resolved.verified is False, (
            f"[B-R1] verified should be False for public access, got {resolved.verified!r}"
        )
        print("[B-R1] test_public_verified_false — PASS")

    def test_public_a_only_payload(self) -> None:
        """B-R1 — Layer-A-only encoded payload resolves fine under public."""
        layer_a = _sample_layer_a()
        encoded = encode_layers(layer_a)  # no B or C

        resolved = resolve(encoded, "public")

        assert resolved.layer_a == layer_a, (
            f"[B-R1] layer_a mismatch for A-only payload: {resolved.layer_a!r}"
        )
        assert resolved.layer_b is None, "[B-R1] layer_b should be None"
        assert resolved.signature is None, "[B-R1] signature should be None"
        assert resolved.verified is False, "[B-R1] verified should be False"
        print("[B-R1] test_public_a_only_payload — PASS")


# ---------------------------------------------------------------------------
# B-R2: authenticated → A+B
# ---------------------------------------------------------------------------

class TestBR2Authenticated:
    """B-R2: resolve(..., "authenticated") returns Layer A + B."""

    def test_authenticated_returns_a_and_b(self) -> None:
        """B-R2 — layer_a matches, layer_b matches original, signature is None."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = _sample_layer_c()
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "authenticated")

        assert resolved.layer_a == layer_a, (
            f"[B-R2] layer_a mismatch: {resolved.layer_a!r}"
        )
        assert resolved.layer_b == layer_b, (
            f"[B-R2] layer_b mismatch: expected {layer_b!r}, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, (
            f"[B-R2] signature should be None for authenticated access, got {resolved.signature!r}"
        )
        print("[B-R2] test_authenticated_returns_a_and_b — PASS")

    def test_authenticated_verified_false(self) -> None:
        """B-R2 — verified is False for authenticated access (no sig check)."""
        encoded = encode_layers(_sample_layer_a(), _sample_layer_b())

        resolved = resolve(encoded, "authenticated")

        assert resolved.verified is False, (
            f"[B-R2] verified should be False for authenticated access, got {resolved.verified!r}"
        )
        print("[B-R2] test_authenticated_verified_false — PASS")

    def test_authenticated_a_only_payload(self) -> None:
        """B-R2 — Layer-A-only payload → layer_b is None (nothing to decode)."""
        layer_a = _sample_layer_a()
        encoded = encode_layers(layer_a)  # no B or C

        resolved = resolve(encoded, "authenticated")

        assert resolved.layer_a == layer_a, (
            f"[B-R2] layer_a mismatch for A-only payload: {resolved.layer_a!r}"
        )
        assert resolved.layer_b is None, (
            f"[B-R2] layer_b should be None when payload has no B layer, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, "[B-R2] signature should be None"
        print("[B-R2] test_authenticated_a_only_payload — PASS")


# ---------------------------------------------------------------------------
# B-R3: verified → A+B+C
# ---------------------------------------------------------------------------

class TestBR3Verified:
    """B-R3: resolve(..., "verified") returns A+B+signature when signature is valid."""

    def test_verified_valid_signature(self) -> None:
        """B-R3 — encode with signed Layer C, resolve "verified" with correct public_key → verified=True."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        private_key, public_key = generate_keypair()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "verified", public_key=public_key)

        assert resolved.verified is True, (
            f"[B-R3] verified should be True for valid signature, got {resolved.verified!r}"
        )
        print("[B-R3] test_verified_valid_signature — PASS")

    def test_verified_returns_all_layers(self) -> None:
        """B-R3 — layer_a, layer_b, signature bytes match originals."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        private_key, public_key = generate_keypair()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "verified", public_key=public_key)

        assert resolved.layer_a == layer_a, (
            f"[B-R3] layer_a mismatch: {resolved.layer_a!r}"
        )
        assert resolved.layer_b == layer_b, (
            f"[B-R3] layer_b mismatch: expected {layer_b!r}, got {resolved.layer_b!r}"
        )
        assert resolved.signature == layer_c, (
            f"[B-R3] signature mismatch: expected {layer_c!r}, got {resolved.signature!r}"
        )
        print("[B-R3] test_verified_returns_all_layers — PASS")

    def test_verified_without_public_key(self) -> None:
        """B-R3 — resolve "verified" with public_key=None → falls back to public (safe default)."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        private_key, _public_key = generate_keypair()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "verified", public_key=None)

        assert resolved.layer_b is None, (
            f"[B-R3] layer_b should be None when no public_key given, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, (
            f"[B-R3] signature should be None when no public_key given, got {resolved.signature!r}"
        )
        assert resolved.verified is False, (
            f"[B-R3] verified should be False when no public_key given, got {resolved.verified!r}"
        )
        print("[B-R3] test_verified_without_public_key — PASS")


# ---------------------------------------------------------------------------
# B-R4: unknown → safe default
# ---------------------------------------------------------------------------

class TestBR4UnknownAccessLevel:
    """B-R4: resolve(..., unknown_level) treats as "public" (safe default)."""

    def test_unknown_level_returns_public(self) -> None:
        """B-R4 — resolve(encoded, "admin") → same as "public" (layer_a only)."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        encoded = encode_layers(layer_a, layer_b)

        resolved = resolve(encoded, "admin")

        assert resolved.layer_a == layer_a, (
            f"[B-R4] layer_a mismatch: {resolved.layer_a!r}"
        )
        assert resolved.layer_b is None, (
            f"[B-R4] layer_b should be None for unknown access level, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, "[B-R4] signature should be None"
        assert resolved.verified is False, "[B-R4] verified should be False"
        print("[B-R4] test_unknown_level_returns_public — PASS")

    def test_empty_string_level(self) -> None:
        """B-R4 — resolve(encoded, "") → same as "public"."""
        layer_a = _sample_layer_a()
        encoded = encode_layers(layer_a, _sample_layer_b())

        resolved = resolve(encoded, "")

        assert resolved.layer_b is None, (
            f"[B-R4] layer_b should be None for empty string access level, got {resolved.layer_b!r}"
        )
        assert resolved.verified is False, "[B-R4] verified should be False"
        print("[B-R4] test_empty_string_level — PASS")

    def test_none_level(self) -> None:
        """B-R4 — resolve(encoded, None) → same as "public" (handle gracefully, don't crash)."""
        layer_a = _sample_layer_a()
        encoded = encode_layers(layer_a, _sample_layer_b())

        resolved = resolve(encoded, None)  # type: ignore[arg-type]

        assert resolved.layer_b is None, (
            f"[B-R4] layer_b should be None for None access level, got {resolved.layer_b!r}"
        )
        assert resolved.verified is False, "[B-R4] verified should be False"
        print("[B-R4] test_none_level — PASS")


# ---------------------------------------------------------------------------
# B-R5: forgery/partial/expired → B/C hidden
# ---------------------------------------------------------------------------

class TestBR5ForgeryProtection:
    """B-R5: Invalid/tampered signatures fall back to public access (B/C hidden)."""

    def test_wrong_key_falls_back_to_public(self) -> None:
        """B-R5 — sign with key1, resolve "verified" with key2's public → verified=False, b=None, c=None."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()

        private_key1, _pub1 = generate_keypair()
        _priv2, public_key2 = generate_keypair()

        layer_c = sign_layers(private_key1, layer_a, layer_b)
        encoded = encode_layers(layer_a, layer_b, layer_c)

        resolved = resolve(encoded, "verified", public_key=public_key2)

        assert resolved.verified is False, (
            f"[B-R5] verified should be False for wrong key, got {resolved.verified!r}"
        )
        assert resolved.layer_b is None, (
            f"[B-R5] layer_b should be None on signature failure, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, (
            f"[B-R5] signature should be None on signature failure, got {resolved.signature!r}"
        )
        print("[B-R5] test_wrong_key_falls_back_to_public — PASS")

    def test_tampered_payload_falls_back(self) -> None:
        """B-R5 — sign, tamper layer_a in encoded string, resolve "verified" → falls back to public."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        private_key, public_key = generate_keypair()
        layer_c = sign_layers(private_key, layer_a, layer_b)
        encoded = encode_layers(layer_a, layer_b, layer_c)

        # Tamper: replace first char of layer_a in encoded string
        tampered = "Z" + encoded[1:]

        resolved = resolve(tampered, "verified", public_key=public_key)

        assert resolved.verified is False, (
            f"[B-R5] verified should be False for tampered payload, got {resolved.verified!r}"
        )
        assert resolved.layer_b is None, (
            f"[B-R5] layer_b should be None on tamper detection, got {resolved.layer_b!r}"
        )
        assert resolved.signature is None, (
            f"[B-R5] signature should be None on tamper detection, got {resolved.signature!r}"
        )
        print("[B-R5] test_tampered_payload_falls_back — PASS")

    def test_corrupted_trailer_returns_error_or_public(self) -> None:
        """B-R5 — garbage base64 after delimiter → resolve returns public-like or raises ValueError (no crash)."""
        from qoverwrap.encoder import DELIMITER

        layer_a = _sample_layer_a()
        corrupted = layer_a + DELIMITER + "!!!NOT_VALID_BASE64!!!"

        try:
            resolved = resolve(corrupted, "verified", public_key=b"\x00" * 32)
            # If it returns, must be a safe public-like result
            assert resolved.layer_b is None, (
                f"[B-R5] layer_b should be None for corrupted trailer, got {resolved.layer_b!r}"
            )
            assert resolved.signature is None, (
                f"[B-R5] signature should be None for corrupted trailer, got {resolved.signature!r}"
            )
            assert resolved.verified is False, (
                f"[B-R5] verified should be False for corrupted trailer, got {resolved.verified!r}"
            )
        except ValueError:
            pass  # Raising ValueError is also acceptable
        print("[B-R5] test_corrupted_trailer_returns_error_or_public — PASS")


class TestBR6SimpleModeVerified:
    """B-R6: delimiter-free (simple mode) payload under verified access."""

    def test_verified_simple_mode_falls_back_without_signature(self) -> None:
        """B-R6 — A-only wire payload: verified cannot succeed; behave like public for B/signature."""
        layer_a = _sample_layer_a()
        _priv, pub = generate_keypair()
        encoded = encode_layers(layer_a)

        resolved = resolve(encoded, "verified", public_key=pub)

        assert resolved.layer_a == layer_a
        assert resolved.layer_b is None
        assert resolved.signature is None
        assert resolved.verified is False
        print("[B-R6] test_verified_simple_mode_falls_back_without_signature — PASS")
