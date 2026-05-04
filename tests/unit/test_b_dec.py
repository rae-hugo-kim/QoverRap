"""B-D1~5: Decoder unit tests for QoverwRap 3-layer decoding.

Tests the decode_layers() and decode() functions defined in
qoverwrap.decoder against the Phase A-proven wire format:

  - Layer A only  → plain text, no delimiter
  - Layer A+B/C   → layer_a + DELIMITER + base64(header + layer_b + layer_c)
  - Binary header → [1B version=0x01][2B b_len big-endian][2B c_len big-endian]

Test IDs
--------
B-D1  Layer A decoding
B-D2  Layer A+B decoding
B-D3  Layer A+B+C decoding (full roundtrip)
B-D4  Corrupted input handling
B-D5  Unsupported version/format
"""
from __future__ import annotations

import base64
import struct

import pytest

from qoverwrap.decoder import DELIMITER, HEADER_SIZE, HEADER_VERSION, decode, decode_layers
from qoverwrap.encoder import encode_layers
from qoverwrap.models import QwrPayload

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
# B-D1: Layer A decoding
# ---------------------------------------------------------------------------


class TestBD1LayerADecoding:
    """B-D1: Layer A only — decode_layers returns (layer_a, b'', b'')."""

    def test_a_only_plaintext(self) -> None:
        """B-D1 — decode_layers('hello') returns ('hello', b'', b'')."""
        a, b, c = decode_layers("hello")
        assert a == "hello", f"[B-D1] layer_a mismatch: expected 'hello', got {a!r}"
        assert b == b"", f"[B-D1] layer_b should be b'', got {b!r}"
        assert c == b"", f"[B-D1] layer_c should be b'', got {c!r}"
        print("[B-D1] test_a_only_plaintext — PASS")

    def test_a_only_url(self) -> None:
        """B-D1 — URL string roundtrips through decode_layers unchanged."""
        url = "https://example.com/qr?layer=A&seq=1&token=abc123"
        a, b, c = decode_layers(url)
        assert a == url, f"[B-D1] URL layer_a mismatch: expected {url!r}, got {a!r}"
        assert b == b"", f"[B-D1] layer_b should be b'', got {b!r}"
        assert c == b"", f"[B-D1] layer_c should be b'', got {c!r}"
        print("[B-D1] test_a_only_url — PASS")

    def test_a_only_unicode(self) -> None:
        """B-D1 — Korean/emoji text roundtrips through decode_layers unchanged."""
        text = "안녕하세요 QoverwRap 🎉"
        a, b, c = decode_layers(text)
        assert a == text, f"[B-D1] Unicode layer_a mismatch: expected {text!r}, got {a!r}"
        assert b == b"", f"[B-D1] layer_b should be b'', got {b!r}"
        assert c == b"", f"[B-D1] layer_c should be b'', got {c!r}"
        print("[B-D1] test_a_only_unicode — PASS")

    def test_a_only_empty_string(self) -> None:
        """B-D1 — decode_layers('') returns ('', b'', b'')."""
        a, b, c = decode_layers("")
        assert a == "", f"[B-D1] Empty string: expected a='', got {a!r}"
        assert b == b"", f"[B-D1] layer_b should be b'', got {b!r}"
        assert c == b"", f"[B-D1] layer_c should be b'', got {c!r}"
        print("[B-D1] test_a_only_empty_string — PASS")


# ---------------------------------------------------------------------------
# B-D2: Layer B decoding
# ---------------------------------------------------------------------------


class TestBD2LayerBDecoding:
    """B-D2: Layer A+B — decode recovers layer_b and leaves layer_c empty."""

    def test_ab_recovers_layer_b(self) -> None:
        """B-D2 — encode A+B then decode; layer_b matches original."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        encoded = encode_layers(layer_a, layer_b)
        _a, b, _c = decode_layers(encoded)
        assert b == layer_b, (
            f"[B-D2] layer_b mismatch after encode+decode.\n"
            f"  Expected: {layer_b!r}\n  Got:      {b!r}"
        )
        print(f"[B-D2] test_ab_recovers_layer_b — PASS ({len(layer_b)} bytes)")

    def test_ab_layer_a_preserved(self) -> None:
        """B-D2 — After encode+decode of A+B, layer_a is unchanged."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        encoded = encode_layers(layer_a, layer_b)
        a, _b, _c = decode_layers(encoded)
        assert a == layer_a, (
            f"[B-D2] layer_a mismatch after encode+decode.\n"
            f"  Expected: {layer_a!r}\n  Got:      {a!r}"
        )
        print("[B-D2] test_ab_layer_a_preserved — PASS")

    def test_ab_layer_c_is_empty(self) -> None:
        """B-D2 — Decode of A+B encoded payload returns empty layer_c."""
        encoded = encode_layers(_sample_layer_a(), _sample_layer_b())
        _a, _b, c = decode_layers(encoded)
        assert c == b"", f"[B-D2] layer_c should be b'' for A+B payload, got {c!r}"
        print("[B-D2] test_ab_layer_c_is_empty — PASS")


# ---------------------------------------------------------------------------
# B-D3: Layer C decoding (full roundtrip)
# ---------------------------------------------------------------------------


class TestBD3LayerCDecoding:
    """B-D3: Layer A+B+C — full 3-layer roundtrip via encode then decode."""

    def test_abc_full_roundtrip(self) -> None:
        """B-D3 — encode(a,b,c) then decode; all three layers match originals."""
        layer_a = _sample_layer_a(80)
        layer_b = _sample_layer_b(96)
        layer_c = _sample_layer_c(64)

        encoded = encode_layers(layer_a, layer_b, layer_c)
        a, b, c = decode_layers(encoded)

        assert a == layer_a, (
            f"[B-D3] layer_a mismatch.\n  Expected: {layer_a!r}\n  Got: {a!r}"
        )
        assert b == layer_b, (
            f"[B-D3] layer_b mismatch.\n  Expected: {layer_b!r}\n  Got: {b!r}"
        )
        assert c == layer_c, (
            f"[B-D3] layer_c mismatch.\n  Expected: {layer_c!r}\n  Got: {c!r}"
        )
        print(f"[B-D3] test_abc_full_roundtrip — PASS (b={len(layer_b)}B, c={len(layer_c)}B)")

    def test_abc_binary_full_byte_range(self) -> None:
        """B-D3 — 256-byte B + 256-byte C (all byte values) roundtrip losslessly."""
        layer_a = _sample_layer_a()
        layer_b = bytes(range(256))
        layer_c = bytes(range(255, -1, -1))

        encoded = encode_layers(layer_a, layer_b, layer_c)
        a, b, c = decode_layers(encoded)

        assert b == layer_b, (
            f"[B-D3] Full-range Layer B not recovered. First diff at byte "
            f"{next(i for i, (x, y) in enumerate(zip(b, layer_b)) if x != y)}"
        )
        assert c == layer_c, (
            f"[B-D3] Full-range Layer C not recovered. First diff at byte "
            f"{next(i for i, (x, y) in enumerate(zip(c, layer_c)) if x != y)}"
        )
        print("[B-D3] test_abc_binary_full_byte_range — PASS (256-byte full range)")

    def test_abc_empty_b_with_c(self) -> None:
        """B-D3 — encode(a, b'', c) → decode → b_len=0, c recovered correctly."""
        layer_a = _sample_layer_a()
        layer_c = _sample_layer_c(64)

        encoded = encode_layers(layer_a, b"", layer_c)
        a, b, c = decode_layers(encoded)

        assert b == b"", f"[B-D3] layer_b should be b'' when encoded with empty b, got {b!r}"
        assert c == layer_c, (
            f"[B-D3] layer_c mismatch when layer_b is empty.\n"
            f"  Expected: {layer_c!r}\n  Got: {c!r}"
        )
        print(f"[B-D3] test_abc_empty_b_with_c — PASS (b_len=0, c_len={len(layer_c)})")

    def test_abc_empty_c_with_b(self) -> None:
        """B-D3 — encode(a, b, b'') → decode → c_len=0, b recovered correctly."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b(96)

        encoded = encode_layers(layer_a, layer_b, b"")
        a, b, c = decode_layers(encoded)

        assert b == layer_b, (
            f"[B-D3] layer_b mismatch when layer_c is empty.\n"
            f"  Expected: {layer_b!r}\n  Got: {b!r}"
        )
        assert c == b"", f"[B-D3] layer_c should be b'' when encoded with empty c, got {c!r}"
        print(f"[B-D3] test_abc_empty_c_with_b — PASS (b_len={len(layer_b)}, c_len=0)")

    def test_abc_decode_returns_qwr_payload(self) -> None:
        """B-D3 — decode() returns a QwrPayload with correct field values."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = _sample_layer_c()

        encoded = encode_layers(layer_a, layer_b, layer_c)
        result = decode(encoded)

        assert isinstance(result, QwrPayload), (
            f"[B-D3] decode() should return QwrPayload, got {type(result).__name__}"
        )
        assert result.layer_a == layer_a, (
            f"[B-D3] QwrPayload.layer_a mismatch: {result.layer_a!r}"
        )
        assert result.layer_b == layer_b, (
            f"[B-D3] QwrPayload.layer_b mismatch"
        )
        assert result.layer_c == layer_c, (
            f"[B-D3] QwrPayload.layer_c mismatch"
        )
        print("[B-D3] test_abc_decode_returns_qwr_payload — PASS")


# ---------------------------------------------------------------------------
# B-D4: Corrupted input handling
# ---------------------------------------------------------------------------


class TestBD4CorruptedInputHandling:
    """B-D4: decode_layers() raises appropriate errors on malformed payloads."""

    def _make_trailer(self, frame: bytes) -> str:
        """Helper: build a valid-looking encoded payload with a custom frame."""
        return _sample_layer_a() + DELIMITER + base64.b64encode(frame).decode("ascii")

    def test_invalid_base64_trailer(self) -> None:
        """B-D4 — Payload with DELIMITER but garbage after it raises ValueError."""
        bad_payload = _sample_layer_a() + DELIMITER + "!!!not_valid_base64!!!"
        with pytest.raises(ValueError):
            decode_layers(bad_payload)
        print("[B-D4] test_invalid_base64_trailer — PASS")

    def test_truncated_header(self) -> None:
        """B-D4 — Frame that base64-decodes to < 5 bytes raises ValueError."""
        short_frame = b"\x01\x00"  # Only 2 bytes, less than HEADER_SIZE=5
        bad_payload = self._make_trailer(short_frame)
        with pytest.raises(ValueError):
            decode_layers(bad_payload)
        print("[B-D4] test_truncated_header — PASS")

    def test_b_len_exceeds_frame(self) -> None:
        """B-D4 — Header says b_len=9999 but frame is too short raises ValueError."""
        # Header: version=0x01, b_len=9999, c_len=0, then only a few bytes of data
        header = struct.pack(">BHH", HEADER_VERSION, 9999, 0)
        frame = header + b"short"
        bad_payload = self._make_trailer(frame)
        with pytest.raises(ValueError):
            decode_layers(bad_payload)
        print("[B-D4] test_b_len_exceeds_frame — PASS")

    def test_c_len_exceeds_frame(self) -> None:
        """B-D4 — Header says c_len=9999 but frame is too short raises ValueError."""
        # Header: version=0x01, b_len=0, c_len=9999, then only a few bytes of data
        header = struct.pack(">BHH", HEADER_VERSION, 0, 9999)
        frame = header + b"short"
        bad_payload = self._make_trailer(frame)
        with pytest.raises(ValueError):
            decode_layers(bad_payload)
        print("[B-D4] test_c_len_exceeds_frame — PASS")

    def test_non_string_input(self) -> None:
        """B-D4 — Passing non-str to decode_layers raises TypeError."""
        with pytest.raises(TypeError):
            decode_layers(b"not a string")  # type: ignore[arg-type]
        print("[B-D4] test_non_string_input — PASS")


# ---------------------------------------------------------------------------
# B-D5: Unsupported version/format
# ---------------------------------------------------------------------------


class TestBD5UnsupportedVersionFormat:
    """B-D5: decode_layers() rejects unknown version bytes and handles extra bytes."""

    def _make_trailer(self, frame: bytes) -> str:
        """Helper: build a valid-looking encoded payload with a custom frame."""
        return _sample_layer_a() + DELIMITER + base64.b64encode(frame).decode("ascii")

    def test_unsupported_version_byte(self) -> None:
        """B-D5 — Version byte 0x99 raises ValueError mentioning 'version'."""
        header = struct.pack(">BHH", 0x99, 10, 10)
        frame = header + b"A" * 20
        bad_payload = self._make_trailer(frame)
        with pytest.raises(ValueError, match="version"):
            decode_layers(bad_payload)
        print("[B-D5] test_unsupported_version_byte — PASS")

    def test_extra_bytes_after_bc_rejected_for_v1(self) -> None:
        """B-D5 — v1 frame must be exactly header+b+c; trailing bytes are rejected."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b(32)
        layer_c = _sample_layer_c(16)

        header = struct.pack(">BHH", HEADER_VERSION, len(layer_b), len(layer_c))
        frame = header + layer_b + layer_c + b"\xff\xfe\xfd"
        payload = layer_a + DELIMITER + base64.b64encode(frame).decode("ascii")

        with pytest.raises(ValueError, match="Frame length mismatch"):
            decode_layers(payload)
        print("[B-D5] test_extra_bytes_after_bc_rejected_for_v1 — PASS")

    def test_invalid_base64_strict_decode(self) -> None:
        """B-D5 — Non-base64 alphabet in trailer fails strict decode."""
        bad = _sample_layer_a() + DELIMITER + "!!!not_valid_base64!!!"
        with pytest.raises(ValueError, match="Invalid base64"):
            decode_layers(bad)
        print("[B-D5] test_invalid_base64_strict_decode — PASS")

    def test_base64_with_whitespace_rejected(self) -> None:
        """B-D5 — validate=True rejects whitespace-padded base64."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b(8)
        header = struct.pack(">BHH", HEADER_VERSION, len(layer_b), 0)
        frame = header + layer_b
        trailer = base64.b64encode(frame).decode("ascii")
        payload = layer_a + DELIMITER + " " + trailer + " "
        with pytest.raises(ValueError):
            decode_layers(payload)
        print("[B-D5] test_base64_with_whitespace_rejected — PASS")
