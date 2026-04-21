"""B-E1~5: Encoder unit tests for QoverwRap 3-layer encoding.

Tests the encode_layers() and encode() functions defined in
qoverwrap.encoder against the Phase A-proven wire format:

  - Layer A only  → plain text, no delimiter
  - Layer A+B/C   → layer_a + DELIMITER + base64(header + layer_b + layer_c)
  - Binary header → [1B version=0x01][2B b_len big-endian][2B c_len big-endian]

Test IDs
--------
B-E1  Layer A single encoding
B-E2  Layer A+B encoding
B-E3  Layer A+B+C encoding
B-E4  Error handling
B-E5  Serialization determinism
"""
from __future__ import annotations

import base64
import struct

import pytest

from qoverwrap.encoder import DELIMITER, HEADER_SIZE, HEADER_VERSION, encode_layers
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
# B-E1: Layer A single encoding
# ---------------------------------------------------------------------------

class TestBE1LayerASingleEncoding:
    """B-E1: Layer A only — result is the plain text string, no delimiter."""

    def test_a_only_returns_plaintext(self) -> None:
        """B-E1 — encode_layers('hello') returns 'hello' exactly."""
        result = encode_layers("hello")
        assert result == "hello", (
            f"[B-E1] Expected 'hello', got {result!r}"
        )
        print("[B-E1] test_a_only_returns_plaintext — PASS")

    def test_a_only_url_payload(self) -> None:
        """B-E1 — URL-like string roundtrips as-is (no transformation)."""
        url = "https://example.com/qr?layer=A&seq=1&token=abc123"
        result = encode_layers(url)
        assert result == url, (
            f"[B-E1] URL payload mutated: expected {url!r}, got {result!r}"
        )
        print("[B-E1] test_a_only_url_payload — PASS")

    def test_a_only_unicode(self) -> None:
        """B-E1 — Korean/emoji characters in Layer A are returned as-is."""
        text = "안녕하세요 QoverwRap 🎉"
        result = encode_layers(text)
        assert result == text, (
            f"[B-E1] Unicode payload mutated: expected {text!r}, got {result!r}"
        )
        print("[B-E1] test_a_only_unicode — PASS")

    def test_a_only_empty_string(self) -> None:
        """B-E1 — encode_layers('') returns empty string."""
        result = encode_layers("")
        assert result == "", (
            f"[B-E1] Empty string: expected '', got {result!r}"
        )
        print("[B-E1] test_a_only_empty_string — PASS")

    def test_a_only_no_base64_trailer(self) -> None:
        """B-E1 — Result does not contain DELIMITER when only Layer A is given."""
        result = encode_layers(_sample_layer_a())
        assert DELIMITER not in result, (
            f"[B-E1] DELIMITER must not appear in Layer-A-only output; got {result!r}"
        )
        print("[B-E1] test_a_only_no_base64_trailer — PASS")


# ---------------------------------------------------------------------------
# B-E2: Layer A+B encoding
# ---------------------------------------------------------------------------

class TestBE2LayerABEncoding:
    """B-E2: Layer A+B — result is layer_a + DELIMITER + base64(header+b)."""

    def test_ab_has_delimiter(self) -> None:
        """B-E2 — Result contains DELIMITER when Layer B is non-empty."""
        result = encode_layers(_sample_layer_a(), _sample_layer_b())
        assert DELIMITER in result, (
            f"[B-E2] DELIMITER missing from A+B result: {result!r}"
        )
        print("[B-E2] test_ab_has_delimiter — PASS")

    def test_ab_starts_with_layer_a(self) -> None:
        """B-E2 — Result starts with the Layer A text verbatim."""
        layer_a = _sample_layer_a()
        result = encode_layers(layer_a, _sample_layer_b())
        assert result.startswith(layer_a), (
            f"[B-E2] Result does not start with Layer A.\n"
            f"  Expected prefix: {layer_a!r}\n"
            f"  Got: {result[:len(layer_a)+10]!r}"
        )
        print("[B-E2] test_ab_starts_with_layer_a — PASS")

    def test_ab_trailer_is_valid_base64(self) -> None:
        """B-E2 — The trailer after DELIMITER is valid base64."""
        result = encode_layers(_sample_layer_a(), _sample_layer_b())
        parts = result.split(DELIMITER, maxsplit=1)
        assert len(parts) == 2, "[B-E2] Expected exactly one DELIMITER split"
        trailer = parts[1]
        try:
            decoded = base64.b64decode(trailer)
        except Exception as exc:
            pytest.fail(f"[B-E2] Trailer is not valid base64: {exc}\nTrailer: {trailer!r}")
        assert len(decoded) >= HEADER_SIZE, (
            f"[B-E2] Decoded frame shorter than HEADER_SIZE={HEADER_SIZE}: {len(decoded)}"
        )
        print(f"[B-E2] test_ab_trailer_is_valid_base64 — PASS (frame={len(decoded)} bytes)")

    def test_ab_header_version_correct(self) -> None:
        """B-E2 — Decoded frame starts with version byte 0x01."""
        result = encode_layers(_sample_layer_a(), _sample_layer_b())
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        version = frame[0]
        assert version == HEADER_VERSION, (
            f"[B-E2] Header version byte: expected 0x{HEADER_VERSION:02x}, got 0x{version:02x}"
        )
        print(f"[B-E2] test_ab_header_version_correct — PASS (version=0x{version:02x})")

    def test_ab_header_lengths_correct(self) -> None:
        """B-E2 — b_len matches actual Layer B length; c_len == 0."""
        layer_b = _sample_layer_b(96)
        result = encode_layers(_sample_layer_a(), layer_b)
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])
        assert b_len == len(layer_b), (
            f"[B-E2] b_len mismatch: header says {b_len}, actual Layer B is {len(layer_b)}"
        )
        assert c_len == 0, (
            f"[B-E2] c_len should be 0 when no Layer C is given, got {c_len}"
        )
        print(f"[B-E2] test_ab_header_lengths_correct — PASS (b_len={b_len}, c_len={c_len})")

    def test_ab_layer_b_recoverable(self) -> None:
        """B-E2 — Layer B bytes can be extracted verbatim from the frame."""
        layer_b = _sample_layer_b(96)
        result = encode_layers(_sample_layer_a(), layer_b)
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])
        recovered_b = frame[HEADER_SIZE:HEADER_SIZE + b_len]
        assert recovered_b == layer_b, (
            f"[B-E2] Layer B not recovered correctly.\n"
            f"  Expected: {layer_b!r}\n"
            f"  Got:      {recovered_b!r}"
        )
        print(f"[B-E2] test_ab_layer_b_recoverable — PASS ({b_len} bytes recovered)")


# ---------------------------------------------------------------------------
# B-E3: Layer A+B+C encoding
# ---------------------------------------------------------------------------

class TestBE3LayerABCEncoding:
    """B-E3: Layer A+B+C — full 3-layer frame structure and content."""

    def test_abc_full_roundtrip_structure(self) -> None:
        """B-E3 — Encode 3 layers; verify delimiter, header, and all layer bytes."""
        layer_a = _sample_layer_a(80)
        layer_b = _sample_layer_b(96)
        layer_c = _sample_layer_c(64)

        result = encode_layers(layer_a, layer_b, layer_c)

        assert DELIMITER in result, "[B-E3] DELIMITER missing from A+B+C result"
        assert result.startswith(layer_a), "[B-E3] Result does not start with Layer A"

        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)

        version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])
        assert version == HEADER_VERSION, (
            f"[B-E3] Header version: expected 0x{HEADER_VERSION:02x}, got 0x{version:02x}"
        )

        recovered_b = frame[HEADER_SIZE:HEADER_SIZE + b_len]
        recovered_c = frame[HEADER_SIZE + b_len:HEADER_SIZE + b_len + c_len]

        assert recovered_b == layer_b, (
            f"[B-E3] Layer B mismatch after roundtrip.\n"
            f"  Expected: {layer_b!r}\n  Got: {recovered_b!r}"
        )
        assert recovered_c == layer_c, (
            f"[B-E3] Layer C mismatch after roundtrip.\n"
            f"  Expected: {layer_c!r}\n  Got: {recovered_c!r}"
        )
        print(
            f"[B-E3] test_abc_full_roundtrip_structure — PASS "
            f"(b={b_len}B, c={c_len}B)"
        )

    def test_abc_header_lengths_match(self) -> None:
        """B-E3 — b_len and c_len in header exactly match actual layer sizes."""
        layer_b = _sample_layer_b(120)
        layer_c = _sample_layer_c(48)

        result = encode_layers(_sample_layer_a(), layer_b, layer_c)
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])

        assert b_len == len(layer_b), (
            f"[B-E3] b_len mismatch: header={b_len}, actual={len(layer_b)}"
        )
        assert c_len == len(layer_c), (
            f"[B-E3] c_len mismatch: header={c_len}, actual={len(layer_c)}"
        )
        print(f"[B-E3] test_abc_header_lengths_match — PASS (b_len={b_len}, c_len={c_len})")

    def test_abc_binary_full_byte_range(self) -> None:
        """B-E3 — All 256 byte values in B and C are stored and recovered losslessly."""
        layer_b = bytes(range(256))
        layer_c = bytes(range(255, -1, -1))

        result = encode_layers(_sample_layer_a(), layer_b, layer_c)
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])

        recovered_b = frame[HEADER_SIZE:HEADER_SIZE + b_len]
        recovered_c = frame[HEADER_SIZE + b_len:HEADER_SIZE + b_len + c_len]

        assert recovered_b == layer_b, (
            f"[B-E3] Full-range Layer B not recovered. First diff at byte "
            f"{next(i for i,(a,b) in enumerate(zip(recovered_b,layer_b)) if a!=b)}"
        )
        assert recovered_c == layer_c, (
            f"[B-E3] Full-range Layer C not recovered. First diff at byte "
            f"{next(i for i,(a,b) in enumerate(zip(recovered_c,layer_c)) if a!=b)}"
        )
        print("[B-E3] test_abc_binary_full_byte_range — PASS (256-byte full range)")

    def test_abc_empty_b_with_c(self) -> None:
        """B-E3 — layer_b=b'', layer_c=64 bytes: b_len=0, c_len=64 correct."""
        layer_c = _sample_layer_c(64)

        result = encode_layers(_sample_layer_a(), b"", layer_c)
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])

        assert b_len == 0, f"[B-E3] b_len should be 0, got {b_len}"
        assert c_len == len(layer_c), (
            f"[B-E3] c_len mismatch: header={c_len}, actual={len(layer_c)}"
        )

        recovered_c = frame[HEADER_SIZE + b_len:HEADER_SIZE + b_len + c_len]
        assert recovered_c == layer_c, (
            f"[B-E3] Layer C not recovered when Layer B is empty.\n"
            f"  Expected: {layer_c!r}\n  Got: {recovered_c!r}"
        )
        print(f"[B-E3] test_abc_empty_b_with_c — PASS (b_len=0, c_len={c_len})")

    def test_abc_empty_c_with_b(self) -> None:
        """B-E3 — layer_b=96 bytes, layer_c=b'': b_len=96, c_len=0 correct."""
        layer_b = _sample_layer_b(96)

        result = encode_layers(_sample_layer_a(), layer_b, b"")
        trailer = result.split(DELIMITER, maxsplit=1)[1]
        frame = base64.b64decode(trailer)
        _version, b_len, c_len = struct.unpack(">BHH", frame[:HEADER_SIZE])

        assert b_len == len(layer_b), (
            f"[B-E3] b_len mismatch: header={b_len}, actual={len(layer_b)}"
        )
        assert c_len == 0, f"[B-E3] c_len should be 0, got {c_len}"

        recovered_b = frame[HEADER_SIZE:HEADER_SIZE + b_len]
        assert recovered_b == layer_b, (
            f"[B-E3] Layer B not recovered when Layer C is empty.\n"
            f"  Expected: {layer_b!r}\n  Got: {recovered_b!r}"
        )
        print(f"[B-E3] test_abc_empty_c_with_b — PASS (b_len={b_len}, c_len=0)")


# ---------------------------------------------------------------------------
# B-E4: Error handling
# ---------------------------------------------------------------------------

class TestBE4ErrorHandling:
    """B-E4: encode_layers() raises appropriate errors on bad inputs."""

    def test_delimiter_in_layer_a_raises(self) -> None:
        """B-E4 — layer_a containing '---QWR---' raises ValueError."""
        bad_a = "prefix" + DELIMITER + "suffix"
        with pytest.raises(ValueError, match="QWR"):
            encode_layers(bad_a, _sample_layer_b())
        print("[B-E4] test_delimiter_in_layer_a_raises — PASS")

    def test_layer_a_type_error(self) -> None:
        """B-E4 — Passing non-str for layer_a raises TypeError."""
        with pytest.raises(TypeError):
            encode_layers(b"not a string")  # type: ignore[arg-type]
        print("[B-E4] test_layer_a_type_error — PASS")

    def test_layer_b_type_error(self) -> None:
        """B-E4 — Passing non-bytes for layer_b raises TypeError."""
        with pytest.raises(TypeError):
            encode_layers("valid_a", "not bytes")  # type: ignore[arg-type]
        print("[B-E4] test_layer_b_type_error — PASS")

    def test_layer_c_type_error(self) -> None:
        """B-E4 — Passing non-bytes for layer_c raises TypeError."""
        with pytest.raises(TypeError):
            encode_layers("valid_a", b"valid_b", "not bytes")  # type: ignore[arg-type]
        print("[B-E4] test_layer_c_type_error — PASS")

    def test_layer_b_exceeds_uint16(self) -> None:
        """B-E4 — layer_b of 65536 bytes raises ValueError (overflows 2-byte uint16)."""
        oversized_b = bytes(65536)
        with pytest.raises(ValueError):
            encode_layers(_sample_layer_a(), oversized_b)
        print("[B-E4] test_layer_b_exceeds_uint16 — PASS")

    def test_layer_c_exceeds_uint16(self) -> None:
        """B-E4 — layer_c of 65536 bytes raises ValueError (overflows 2-byte uint16)."""
        oversized_c = bytes(65536)
        with pytest.raises(ValueError):
            encode_layers(_sample_layer_a(), b"", oversized_c)
        print("[B-E4] test_layer_c_exceeds_uint16 — PASS")


# ---------------------------------------------------------------------------
# B-E5: Serialization determinism
# ---------------------------------------------------------------------------

class TestBE5SerializationDeterminism:
    """B-E5: encode_layers() is deterministic — same inputs always produce same output."""

    def test_same_input_same_output(self) -> None:
        """B-E5 — 100 calls with identical args produce identical strings."""
        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = _sample_layer_c()

        results = [encode_layers(layer_a, layer_b, layer_c) for _ in range(100)]
        unique = set(results)
        assert len(unique) == 1, (
            f"[B-E5] encode_layers is non-deterministic: {len(unique)} distinct outputs "
            f"across 100 calls"
        )
        print("[B-E5] test_same_input_same_output — PASS (100/100 identical)")

    @pytest.mark.parametrize("b_size,c_size", [
        (32, 16),
        (256, 128),
        (1024, 512),
    ])
    def test_deterministic_across_payload_sizes(self, b_size: int, c_size: int) -> None:
        """B-E5 — Determinism holds across different payload sizes."""
        layer_a = _sample_layer_a()
        layer_b = bytes([i % 256 for i in range(b_size)])
        layer_c = bytes([(i * 3) % 256 for i in range(c_size)])

        first = encode_layers(layer_a, layer_b, layer_c)
        second = encode_layers(layer_a, layer_b, layer_c)
        assert first == second, (
            f"[B-E5] Non-deterministic output for b_size={b_size}, c_size={c_size}"
        )
        print(
            f"[B-E5] test_deterministic_across_payload_sizes "
            f"(b={b_size}, c={c_size}) — PASS"
        )

    def test_qwr_payload_model_encodes_same(self) -> None:
        """B-E5 — encode(QwrPayload(a, b, c)) == encode_layers(a, b, c)."""
        from qoverwrap.encoder import encode

        layer_a = _sample_layer_a()
        layer_b = _sample_layer_b()
        layer_c = _sample_layer_c()

        via_layers = encode_layers(layer_a, layer_b, layer_c)
        via_model = encode(QwrPayload(layer_a, layer_b, layer_c))

        assert via_layers == via_model, (
            f"[B-E5] encode() and encode_layers() produced different results.\n"
            f"  encode_layers: {via_layers!r}\n"
            f"  encode:        {via_model!r}"
        )
        print("[B-E5] test_qwr_payload_model_encodes_same — PASS")
