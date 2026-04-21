"""B-INT1~5: Integration tests for QoverwRap 3-layer encode/decode/resolve pipeline.

Tests the full module stack end-to-end:
  encoder → decoder → resolver → crypto → QR image generation/scanning

Test IDs
--------
B-INT1  encode → decode 3-layer lossless
B-INT2  encode → resolve(public) → A only
B-INT3  encode → resolve(verified) → A+B+C + C verification
B-INT4  file save/load roundtrip
B-INT5  independent read path compatibility
"""
from __future__ import annotations

import pathlib

import pytest

from qoverwrap.encoder import encode, encode_layers, DELIMITER
from qoverwrap.decoder import decode, decode_layers
from qoverwrap.models import QwrPayload
from qoverwrap.crypto import generate_keypair, sign_layers, verify_signature
from qoverwrap.resolver import resolve

# ---------------------------------------------------------------------------
# Optional dependency imports — skip QR image tests if libs not installed
# ---------------------------------------------------------------------------

try:
    import qrcode
    import qrcode.constants as qrc
    from PIL import Image as PILImage
    _QRCODE_AVAILABLE = True
except ImportError:
    _QRCODE_AVAILABLE = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    _PYZBAR_AVAILABLE = True
except ImportError:
    _PYZBAR_AVAILABLE = False

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

import numpy as np

_QR_STACK_AVAILABLE = _QRCODE_AVAILABLE and _PYZBAR_AVAILABLE and _CV2_AVAILABLE

# ---------------------------------------------------------------------------
# Helpers (mirror of feasibility test_a_asm.py pattern)
# ---------------------------------------------------------------------------

def _sample_a(n: int = 80) -> str:
    base = "https://qoverwrap.example.com/v1/card?id=abc123&seq="
    return (base + "X" * max(0, n - len(base)))[:n]


def _sample_b(n: int = 96) -> bytes:
    stub = b'{"issuer":"QoverwRap","ts":1700000000,"nonce":"'
    pad = b"A" * max(0, n - len(stub) - 2)
    return (stub + pad + b'"}')[:n]


def _sample_c(n: int = 64) -> bytes:
    return bytes([i % 256 for i in range(n)])


def _make_qr(data: str) -> "PILImage.Image":
    """Generate a QR code PIL image from a string payload."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrc.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _pil_to_numpy(img: "PILImage.Image") -> "np.ndarray":
    """Convert PIL image to OpenCV BGR numpy array."""
    rgb = np.array(img)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ===========================================================================
# B-INT1: encode → decode 3-layer lossless
# ===========================================================================

class TestBINT1EncodeDecode:
    """B-INT1: Full encode→decode roundtrip is lossless for all layer combinations."""

    def test_abc_full_roundtrip(self) -> None:
        """B-INT1 — encode_layers(a,b,c) → decode_layers → all three layers match."""
        a = _sample_a()
        b = _sample_b()
        c = _sample_c()

        encoded = encode_layers(a, b, c)
        got_a, got_b, got_c = decode_layers(encoded)

        assert got_a == a, f"[B-INT1] layer_a mismatch: {got_a!r} != {a!r}"
        assert got_b == b, f"[B-INT1] layer_b mismatch"
        assert got_c == c, f"[B-INT1] layer_c mismatch"
        print("[B-INT1] test_abc_full_roundtrip — PASS")

    def test_abc_via_model(self) -> None:
        """B-INT1 — encode(QwrPayload(a,b,c)) → decode() → QwrPayload matches."""
        a = _sample_a()
        b = _sample_b()
        c = _sample_c()

        payload = QwrPayload(a, b, c)
        encoded = encode(payload)
        recovered = decode(encoded)

        assert recovered.layer_a == a, f"[B-INT1] layer_a mismatch"
        assert recovered.layer_b == b, f"[B-INT1] layer_b mismatch"
        assert recovered.layer_c == c, f"[B-INT1] layer_c mismatch"
        print("[B-INT1] test_abc_via_model — PASS")

    def test_a_only_roundtrip(self) -> None:
        """B-INT1 — encode_layers(a) → decode_layers → (a, b'', b'')."""
        a = _sample_a()

        encoded = encode_layers(a)
        got_a, got_b, got_c = decode_layers(encoded)

        assert got_a == a, f"[B-INT1] layer_a mismatch"
        assert got_b == b"", f"[B-INT1] layer_b should be empty, got {got_b!r}"
        assert got_c == b"", f"[B-INT1] layer_c should be empty, got {got_c!r}"
        print("[B-INT1] test_a_only_roundtrip — PASS")

    @pytest.mark.parametrize("b_size,c_size", [
        (0, 0),
        (16, 8),
        (256, 64),
        (1024, 512),
    ])
    def test_various_payload_sizes(self, b_size: int, c_size: int) -> None:
        """B-INT1 — Roundtrip holds across (b_size, c_size) combinations."""
        a = _sample_a()
        b = bytes([i % 256 for i in range(b_size)])
        c = bytes([(i * 3) % 256 for i in range(c_size)])

        encoded = encode_layers(a, b, c)
        got_a, got_b, got_c = decode_layers(encoded)

        assert got_a == a
        assert got_b == b, f"[B-INT1] layer_b mismatch at b_size={b_size}"
        assert got_c == c, f"[B-INT1] layer_c mismatch at c_size={c_size}"
        print(f"[B-INT1] test_various_payload_sizes(b={b_size}, c={c_size}) — PASS")


# ===========================================================================
# B-INT2: encode → resolve(public) → A only
# ===========================================================================

class TestBINT2ResolvePublic:
    """B-INT2: resolve('public') exposes only layer_a; B and C are hidden."""

    def _make_signed_payload(self) -> str:
        priv, pub = generate_keypair()
        a = _sample_a()
        b = _sample_b()
        layer_c = sign_layers(priv, a, b)
        return encode_layers(a, b, layer_c), a

    def test_public_hides_bc(self) -> None:
        """B-INT2 — resolve('public') returns layer_b=None, layer_c=None."""
        payload_str, _ = self._make_signed_payload()

        result = resolve(payload_str, "public")

        assert result.layer_b is None, (
            f"[B-INT2] layer_b should be None for public, got {result.layer_b!r}"
        )
        assert result.layer_c is None, (
            f"[B-INT2] layer_c should be None for public, got {result.layer_c!r}"
        )
        assert result.verified is False
        print("[B-INT2] test_public_hides_bc — PASS")

    def test_public_preserves_layer_a(self) -> None:
        """B-INT2 — resolve('public') returns layer_a text exactly."""
        a = _sample_a()
        b = _sample_b()
        priv, _ = generate_keypair()
        layer_c = sign_layers(priv, a, b)
        payload_str = encode_layers(a, b, layer_c)

        result = resolve(payload_str, "public")

        assert result.layer_a == a, (
            f"[B-INT2] layer_a mismatch: {result.layer_a!r} != {a!r}"
        )
        print("[B-INT2] test_public_preserves_layer_a — PASS")


# ===========================================================================
# B-INT3: encode → resolve(verified) → A+B+C + C verification
# ===========================================================================

class TestBINT3ResolveVerified:
    """B-INT3: resolve('verified', pub) validates signature and exposes all layers."""

    def test_verified_end_to_end(self) -> None:
        """B-INT3 — generate_keypair, sign, encode, resolve('verified') → verified=True, all layers match."""
        priv, pub = generate_keypair()
        a = _sample_a()
        b = _sample_b()
        layer_c = sign_layers(priv, a, b)
        payload_str = encode_layers(a, b, layer_c)

        result = resolve(payload_str, "verified", public_key=pub)

        assert result.verified is True, "[B-INT3] verified should be True"
        assert result.layer_a == a, "[B-INT3] layer_a mismatch"
        assert result.layer_b == b, "[B-INT3] layer_b mismatch"
        assert result.layer_c == layer_c, "[B-INT3] layer_c mismatch"
        print("[B-INT3] test_verified_end_to_end — PASS")

    def test_verified_wrong_key_fallback(self) -> None:
        """B-INT3 — sign with key1, resolve with key2 → verified=False, b/c=None."""
        priv1, _pub1 = generate_keypair()
        _priv2, pub2 = generate_keypair()

        a = _sample_a()
        b = _sample_b()
        layer_c = sign_layers(priv1, a, b)
        payload_str = encode_layers(a, b, layer_c)

        result = resolve(payload_str, "verified", public_key=pub2)

        assert result.verified is False, "[B-INT3] verified should be False with wrong key"
        assert result.layer_b is None, "[B-INT3] layer_b should be None on failed verification"
        assert result.layer_c is None, "[B-INT3] layer_c should be None on failed verification"
        print("[B-INT3] test_verified_wrong_key_fallback — PASS")

    def test_verified_roundtrip_preserves_signature(self) -> None:
        """B-INT3 — sign → encode → decode → verify_signature manually → True."""
        priv, pub = generate_keypair()
        a = _sample_a()
        b = _sample_b()
        layer_c = sign_layers(priv, a, b)
        payload_str = encode_layers(a, b, layer_c)

        # Decode manually and verify signature directly
        got_a, got_b, got_c = decode_layers(payload_str)
        is_valid = verify_signature(pub, got_a, got_b, got_c)

        assert is_valid is True, (
            "[B-INT3] manual verify_signature after encode→decode should be True"
        )
        print("[B-INT3] test_verified_roundtrip_preserves_signature — PASS")


# ===========================================================================
# B-INT4: file save/load roundtrip
# ===========================================================================

class TestBINT4FileRoundtrip:
    """B-INT4: Payload survives write-to-file / read-from-file cycle."""

    def test_write_and_read_qr_payload(self, tmp_path: pathlib.Path) -> None:
        """B-INT4 — encode → write to file → read from file → decode → matches."""
        a = _sample_a()
        b = _sample_b()
        c = _sample_c()
        payload_str = encode_layers(a, b, c)

        file = tmp_path / "payload.qwr"
        file.write_text(payload_str, encoding="utf-8")

        loaded = file.read_text(encoding="utf-8")
        got_a, got_b, got_c = decode_layers(loaded)

        assert got_a == a
        assert got_b == b
        assert got_c == c
        print("[B-INT4] test_write_and_read_qr_payload — PASS")

    def test_binary_payload_survives_file_io(self, tmp_path: pathlib.Path) -> None:
        """B-INT4 — full byte-range B+C survives file write/read/decode."""
        a = _sample_a()
        b = bytes(range(256))
        c = bytes(range(255, -1, -1))
        payload_str = encode_layers(a, b, c)

        file = tmp_path / "binary_payload.qwr"
        file.write_text(payload_str, encoding="utf-8")

        loaded = file.read_text(encoding="utf-8")
        got_a, got_b, got_c = decode_layers(loaded)

        assert got_a == a
        assert got_b == b, "[B-INT4] binary layer_b mismatch after file I/O"
        assert got_c == c, "[B-INT4] binary layer_c mismatch after file I/O"
        print("[B-INT4] test_binary_payload_survives_file_io — PASS")

    @pytest.mark.skipif(not _QR_STACK_AVAILABLE, reason="qrcode/pyzbar/cv2 not installed")
    def test_qr_image_roundtrip(self, tmp_path: pathlib.Path) -> None:
        """B-INT4 — encode → QR image → pyzbar decode → decode_layers → matches."""
        a = _sample_a(60)  # keep short enough to fit in a QR code
        b = _sample_b(64)
        c = _sample_c(32)
        payload_str = encode_layers(a, b, c)

        img = _make_qr(payload_str)
        img_path = tmp_path / "roundtrip.png"
        img.save(str(img_path))

        decoded_syms = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded_syms) == 1, (
            f"[B-INT4] expected 1 QR symbol, got {len(decoded_syms)}"
        )
        scanned_str = decoded_syms[0].data.decode("utf-8")

        got_a, got_b, got_c = decode_layers(scanned_str)
        assert got_a == a, f"[B-INT4] QR roundtrip layer_a mismatch"
        assert got_b == b, f"[B-INT4] QR roundtrip layer_b mismatch"
        assert got_c == c, f"[B-INT4] QR roundtrip layer_c mismatch"
        print("[B-INT4] test_qr_image_roundtrip — PASS")


# ===========================================================================
# B-INT5: independent read path compatibility
# ===========================================================================

class TestBINT5IndependentReadPath:
    """B-INT5: Standard QR scanners see layer_a as the human-readable prefix."""

    @pytest.mark.skipif(not _QR_STACK_AVAILABLE, reason="qrcode/pyzbar/cv2 not installed")
    def test_standard_scanner_sees_layer_a(self, tmp_path: pathlib.Path) -> None:
        """B-INT5 — encode A+B+C → QR → pyzbar → result starts with layer_a text."""
        a = _sample_a(60)
        b = _sample_b(64)
        c = _sample_c(32)
        payload_str = encode_layers(a, b, c)

        img = _make_qr(payload_str)
        img_path = tmp_path / "int5_standard.png"
        img.save(str(img_path))

        decoded_syms = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded_syms) == 1
        scanned = decoded_syms[0].data.decode("utf-8")

        assert scanned.startswith(a), (
            f"[B-INT5] pyzbar result does not start with layer_a.\n"
            f"  Expected prefix: {a!r}\n"
            f"  Got: {scanned[:len(a)+20]!r}"
        )
        print("[B-INT5] test_standard_scanner_sees_layer_a — PASS")

    @pytest.mark.skipif(not _QR_STACK_AVAILABLE, reason="qrcode/pyzbar/cv2 not installed")
    def test_opencv_detector_reads_qr(self, tmp_path: pathlib.Path) -> None:
        """B-INT5 — encode A+B+C → QR → OpenCV QRCodeDetector → result starts with layer_a."""
        a = _sample_a(60)
        b = _sample_b(64)
        c = _sample_c(32)
        payload_str = encode_layers(a, b, c)

        img = _make_qr(payload_str)
        img_path = tmp_path / "int5_opencv.png"
        img.save(str(img_path))

        bgr = cv2.imread(str(img_path))
        assert bgr is not None, "[B-INT5] cv2.imread returned None"
        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(bgr)

        assert points is not None, "[B-INT5] OpenCV found no QR corners"
        assert text.startswith(a), (
            f"[B-INT5] OpenCV result does not start with layer_a.\n"
            f"  Expected prefix: {a!r}\n"
            f"  Got: {text[:len(a)+20]!r}"
        )
        print("[B-INT5] test_opencv_detector_reads_qr — PASS")

    def test_layer_a_before_delimiter(self) -> None:
        """B-INT5 — for any payload with B/C, layer_a is the prefix before the delimiter."""
        a = _sample_a()
        b = _sample_b()
        c = _sample_c()
        encoded = encode_layers(a, b, c)

        assert DELIMITER in encoded, "[B-INT5] DELIMITER not found in A+B+C encoded payload"
        prefix = encoded.split(DELIMITER, maxsplit=1)[0]
        assert prefix == a, (
            f"[B-INT5] prefix before delimiter != layer_a.\n"
            f"  Expected: {a!r}\n"
            f"  Got:      {prefix!r}"
        )
        print("[B-INT5] test_layer_a_before_delimiter — PASS")
