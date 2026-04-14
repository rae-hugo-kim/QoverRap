"""A-HYP1~4: Overlapping hypothesis — multi-layer QR encoding feasibility.

Feasibility spike Cycle 2: verify that three logical layers (A, B, C) can be
packed into a single QR symbol using a plain-text prefix + base64 binary
trailer, and that the result is scannable, performant, and visually standard.

Encoding scheme: Plain-Text-Prefix with Base64 Trailer
    <Layer A UTF-8 text>\\n---QWR---\\n<base64(header + B_payload + C_payload)>

Binary header (inside base64 blob):
    Offset  Size  Field
    0       1     version   (0x01)
    1       2     b_len     (uint16 big-endian)
    3       2     c_len     (uint16 big-endian)
    5       b_len B_payload
    5+b_len c_len C_payload

Test IDs
--------
A-HYP1  Layer separation — A/B/C encode and decode distinguishably
A-HYP2  Normal vs extended read path — normal scanners see only Layer A
A-HYP3  Performance baseline — overlapping QR acceptable vs single-layer
A-HYP4  Visual identity — output is a single standard QR symbol

Discovery
---------
(to be filled after running tests)
"""
import base64
import pathlib
import struct
import time

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Library imports — any ImportError surfaces immediately as a collection error
# so the CI clearly shows "missing dependency" rather than a vague failure.
# ---------------------------------------------------------------------------
try:
    import qrcode
    import qrcode.constants as qrc
    from PIL import Image as PILImage
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"qrcode/Pillow not installed: {exc}", allow_module_level=True)

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"pyzbar not installed (hint: apt-get install libzbar0): {exc}", allow_module_level=True)

try:
    import cv2
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"opencv-python-headless not installed: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Encoding helpers — will be extracted to a module in Phase B
# ---------------------------------------------------------------------------

DELIMITER = "\n---QWR---\n"


def encode_layers(layer_a: str, layer_b: bytes = b"", layer_c: bytes = b"") -> str:
    """Encode A/B/C into a single QR payload string."""
    if DELIMITER.strip() in layer_a:
        raise ValueError("Layer A must not contain the delimiter")
    if not layer_b and not layer_c:
        return layer_a  # A-only, no trailer
    header = struct.pack('>BHH', 0x01, len(layer_b), len(layer_c))
    frame = header + layer_b + layer_c
    trailer = base64.b64encode(frame).decode('ascii')
    return layer_a + DELIMITER + trailer


def decode_layers(payload: str) -> tuple[str, bytes, bytes]:
    """Decode a QR payload into (layer_a, layer_b, layer_c)."""
    if DELIMITER not in payload:
        return (payload, b"", b"")
    layer_a, b64_trailer = payload.split(DELIMITER, maxsplit=1)
    frame = base64.b64decode(b64_trailer)
    version, b_len, c_len = struct.unpack('>BHH', frame[:5])
    if version != 0x01:
        raise ValueError(f"Unsupported version: {version}")
    layer_b = frame[5 : 5 + b_len]
    layer_c = frame[5 + b_len : 5 + b_len + c_len]
    return (layer_a, layer_b, layer_c)


# ---------------------------------------------------------------------------
# QR helpers (copied from test_a_asm.py for spike isolation)
# ---------------------------------------------------------------------------

def _make_qr(data: str | bytes, *, ecc=qrc.ERROR_CORRECT_M, version: int | None = None) -> PILImage.Image:
    """Generate a QR code image using the qrcode library.

    Parameters
    ----------
    data:
        Payload to encode.
    ecc:
        Error-correction level constant from qrcode.constants.
    version:
        Force a specific QR version (1-40).  None = auto-fit.
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=ecc,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=(version is None))
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _pil_to_numpy(img: PILImage.Image) -> np.ndarray:
    """Convert a PIL image to a NumPy array suitable for OpenCV (BGR)."""
    rgb = np.array(img)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# Realistic payload factories
# ---------------------------------------------------------------------------

def _sample_layer_a(n: int = 80) -> str:
    """Return a realistic Layer A text payload (URL-like, n chars)."""
    base = "https://qoverwrap.example.com/v1/card?id=abc123&seq="
    return (base + "X" * max(0, n - len(base)))[:n]


def _sample_layer_b(n: int = 96) -> bytes:
    """Return realistic Layer B data (JSON-like context)."""
    stub = b'{"issuer":"QoverwRap","ts":1700000000,"nonce":"'
    pad = b"A" * max(0, n - len(stub) - 2)
    return (stub + pad + b'"}')[:n]


def _sample_layer_c(n: int = 64) -> bytes:
    """Return a mock 64-byte signature for Layer C."""
    return bytes([i % 256 for i in range(n)])


# ---------------------------------------------------------------------------
# Spec byte capacities (from test_a_asm.py / ISO 18004 Table 7)
# ---------------------------------------------------------------------------

_SPEC_BYTE_CAPACITY: dict[tuple[int, str], int] = {
    (1, "M"): 14,
    (5, "M"): 68,
    (10, "M"): 136,
    (20, "M"): 288,
    (40, "M"): 2331,
}


# ---------------------------------------------------------------------------
# A-HYP1 — Layer separation
# ---------------------------------------------------------------------------

class TestHYP1LayerSeparation:
    """A-HYP1: A/B/C can be encoded distinguishably in a single QR symbol."""

    def test_three_layer_roundtrip(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP1 — Encode A+B+C, generate QR, scan, decode_layers, assert match."""
        a_text = _sample_layer_a()
        b_data = _sample_layer_b()
        c_data = _sample_layer_c()

        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)
        img_path = tmp_dir / "hyp1_roundtrip.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1, f"Expected 1 QR symbol, got {len(decoded)}"

        raw = decoded[0].data.decode("utf-8")
        got_a, got_b, got_c = decode_layers(raw)

        assert got_a == a_text
        assert got_b == b_data
        assert got_c == c_data
        print(f"\n[A-HYP1] 3-layer roundtrip OK — A={len(a_text)}B, B={len(b_data)}B, C={len(c_data)}B")

    def test_a_only_no_trailer(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP1 — Encode A only (no B/C), verify no delimiter, roundtrip works."""
        a_text = "Layer-A standalone payload"

        payload = encode_layers(a_text)
        assert DELIMITER.strip() not in payload, "Delimiter should not appear in A-only payload"

        img = _make_qr(payload)
        img_path = tmp_dir / "hyp1_a_only.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")
        got_a, got_b, got_c = decode_layers(raw)

        assert got_a == a_text
        assert got_b == b""
        assert got_c == b""
        print(f"\n[A-HYP1] A-only roundtrip OK — no trailer, payload={len(payload)}B")

    def test_empty_b_with_c(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP1 — B is empty bytes, C has data, roundtrip works."""
        a_text = _sample_layer_a(60)
        c_data = _sample_layer_c()

        payload = encode_layers(a_text, b"", c_data)
        img = _make_qr(payload)
        img_path = tmp_dir / "hyp1_empty_b.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")
        got_a, got_b, got_c = decode_layers(raw)

        assert got_a == a_text
        assert got_b == b""
        assert got_c == c_data
        print(f"\n[A-HYP1] Empty-B roundtrip OK — C={len(c_data)}B")

    def test_empty_c_with_b(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP1 — B has data, C is empty, roundtrip works."""
        a_text = _sample_layer_a(60)
        b_data = _sample_layer_b()

        payload = encode_layers(a_text, b_data, b"")
        img = _make_qr(payload)
        img_path = tmp_dir / "hyp1_empty_c.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")
        got_a, got_b, got_c = decode_layers(raw)

        assert got_a == a_text
        assert got_b == b_data
        assert got_c == b""
        print(f"\n[A-HYP1] Empty-C roundtrip OK — B={len(b_data)}B")

    def test_delimiter_in_layer_a_rejected(self) -> None:
        """A-HYP1 — Layer A containing the delimiter raises ValueError."""
        bad_a = "Some text ---QWR--- more text"
        with pytest.raises(ValueError, match="delimiter"):
            encode_layers(bad_a, b"B", b"C")
        print("\n[A-HYP1] Delimiter-in-A rejection OK")

    def test_binary_b_c_with_base64(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP1 — B and C contain bytes 0x00-0xFF, roundtrip succeeds.

        Proves that base64 encoding solves the pyzbar UTF-8 corruption issue
        for arbitrary binary content in layers B and C.
        """
        a_text = _sample_layer_a(50)
        b_data = bytes(range(256))
        c_data = bytes(range(255, -1, -1))

        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)
        img_path = tmp_dir / "hyp1_full_byte_range.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")
        got_a, got_b, got_c = decode_layers(raw)

        assert got_a == a_text
        assert got_b == b_data, "Layer B 0x00-0xFF mismatch after roundtrip"
        assert got_c == c_data, "Layer C 0xFF-0x00 mismatch after roundtrip"
        print(
            f"\n[A-HYP1] Full byte-range roundtrip OK — "
            f"B=256B (0x00-0xFF), C=256B (0xFF-0x00)"
        )


# ---------------------------------------------------------------------------
# A-HYP2 — Normal vs extended read path
# ---------------------------------------------------------------------------

class TestHYP2NormalVsExtendedPath:
    """A-HYP2: Normal scanners see only Layer A; extended decoders get B/C."""

    def _make_overlapping_qr(self, tmp_dir: pathlib.Path, name: str) -> tuple[str, str, bytes, bytes, pathlib.Path]:
        """Generate a 3-layer QR and return (payload, a_text, b_data, c_data, img_path)."""
        a_text = "QoverwRap/v1 — public layer visible to all scanners"
        b_data = _sample_layer_b()
        c_data = _sample_layer_c()
        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)
        img_path = tmp_dir / f"hyp2_{name}.png"
        img.save(str(img_path))
        return payload, a_text, b_data, c_data, img_path

    def test_normal_scanner_sees_layer_a_first(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP2 — pyzbar raw output starts with Layer A text (before delimiter)."""
        payload, a_text, _, _, img_path = self._make_overlapping_qr(tmp_dir, "a_first")

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")

        assert raw.startswith(a_text), (
            f"Raw payload does not start with Layer A text.\n"
            f"  Expected prefix: {a_text!r}\n"
            f"  Got: {raw[:len(a_text)+20]!r}"
        )
        print(f"\n[A-HYP2] Normal scanner sees Layer A first — OK")

    def test_normal_scanner_b_c_opaque(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP2 — The base64 trailer does NOT accidentally expose B/C plaintext."""
        _, _, b_data, c_data, img_path = self._make_overlapping_qr(tmp_dir, "opaque")

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")

        # The trailer portion (after delimiter) is base64 — it should not
        # contain the raw B or C bytes as readable text.
        _, trailer = raw.split(DELIMITER, maxsplit=1)
        # B is JSON-like bytes; its string form should not appear in the trailer
        b_as_text = b_data.decode("utf-8", errors="replace")
        assert b_as_text not in trailer, "Layer B plaintext leaked into base64 trailer"
        print(f"\n[A-HYP2] B/C opaque in raw scan output — OK")

    def test_extended_decoder_recovers_all_layers(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP2 — Full decode_layers returns correct A, B, C."""
        payload, a_text, b_data, c_data, img_path = self._make_overlapping_qr(tmp_dir, "extended")

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        raw = decoded[0].data.decode("utf-8")

        got_a, got_b, got_c = decode_layers(raw)
        assert got_a == a_text
        assert got_b == b_data
        assert got_c == c_data
        print(f"\n[A-HYP2] Extended decoder recovers all 3 layers — OK")

    def test_opencv_reads_layer_a(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP2 — OpenCV QRCodeDetector output starts with Layer A text."""
        _, a_text, _, _, img_path = self._make_overlapping_qr(tmp_dir, "opencv_a")

        bgr = cv2.imread(str(img_path))
        assert bgr is not None, "cv2.imread returned None"
        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(bgr)

        assert text.startswith(a_text), (
            f"OpenCV output does not start with Layer A.\n"
            f"  Expected prefix: {a_text!r}\n"
            f"  Got: {text[:len(a_text)+20]!r}"
        )
        print(f"\n[A-HYP2] OpenCV reads Layer A — OK")

    def test_two_decoders_agree_on_raw(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP2 — pyzbar and OpenCV produce identical raw payload string."""
        _, _, _, _, img_path = self._make_overlapping_qr(tmp_dir, "agree")

        # pyzbar
        pyzbar_result = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(pyzbar_result) == 1
        pyzbar_text = pyzbar_result[0].data.decode("utf-8")

        # OpenCV
        bgr = cv2.imread(str(img_path))
        detector = cv2.QRCodeDetector()
        cv2_text, _, _ = detector.detectAndDecode(bgr)

        assert pyzbar_text == cv2_text, (
            f"Decoder mismatch —\n"
            f"  pyzbar ({len(pyzbar_text)} chars): {pyzbar_text[:80]!r}...\n"
            f"  cv2    ({len(cv2_text)} chars): {cv2_text[:80]!r}..."
        )
        print(f"\n[A-HYP2] pyzbar and OpenCV agree on raw payload — OK")


# ---------------------------------------------------------------------------
# A-HYP3 — Performance baseline
# ---------------------------------------------------------------------------

class TestHYP3PerformanceBaseline:
    """A-HYP3: Overlapping QR performance is acceptable vs single-layer baseline."""

    def test_scan_success_rate(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP3 — 50 overlapping QRs with varying payloads, success rate >= 95%."""
        n_trials = 50
        successes = 0

        for i in range(n_trials):
            a_text = _sample_layer_a(60 + (i % 40))
            b_data = _sample_layer_b(48 + (i % 64))
            c_data = _sample_layer_c(32 + (i % 48))
            payload = encode_layers(a_text, b_data, c_data)

            img = _make_qr(payload)
            decoded = pyzbar_decode(img)
            if len(decoded) == 1:
                raw = decoded[0].data.decode("utf-8")
                try:
                    got_a, got_b, got_c = decode_layers(raw)
                    if got_a == a_text and got_b == b_data and got_c == c_data:
                        successes += 1
                except Exception:
                    pass

        rate = successes / n_trials
        assert rate >= 0.95, (
            f"Scan success rate {rate:.1%} ({successes}/{n_trials}) below 95% threshold"
        )
        print(f"\n[A-HYP3] Scan success rate: {rate:.1%} ({successes}/{n_trials})")

    def test_decode_latency_vs_baseline(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP3 — Overlapping QR p95 decode latency <= 5x single-layer p95.

        The overlapping QR encodes more data, producing a higher-version
        (larger) symbol.  More modules = more scan work, so a moderate
        slowdown is expected.  Threshold is 5x to account for the image
        size difference while still catching catastrophic regressions.
        """
        n_samples = 50
        n_warmup = 5

        # Baseline: single-layer (A-only) QR
        a_text = _sample_layer_a(80)
        baseline_img = _make_qr(a_text)
        # Warm up to stabilise caches / JIT
        for _ in range(n_warmup):
            pyzbar_decode(baseline_img)
        baseline_times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(baseline_img)
            baseline_times.append(time.perf_counter() - t0)

        # Overlapping: 3-layer QR
        b_data = _sample_layer_b()
        c_data = _sample_layer_c()
        overlapping_payload = encode_layers(a_text, b_data, c_data)
        overlapping_img = _make_qr(overlapping_payload)
        for _ in range(n_warmup):
            pyzbar_decode(overlapping_img)
        overlapping_times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(overlapping_img)
            overlapping_times.append(time.perf_counter() - t0)

        baseline_times.sort()
        overlapping_times.sort()
        p95_idx = int(n_samples * 0.95) - 1

        baseline_p95 = baseline_times[p95_idx]
        overlapping_p95 = overlapping_times[p95_idx]

        ratio = overlapping_p95 / baseline_p95 if baseline_p95 > 0 else float("inf")
        assert ratio <= 5.0, (
            f"Overlapping p95 ({overlapping_p95*1000:.2f}ms) > 5x baseline p95 "
            f"({baseline_p95*1000:.2f}ms), ratio={ratio:.2f}"
        )
        print(
            f"\n[A-HYP3] Decode latency — baseline p95={baseline_p95*1000:.2f}ms, "
            f"overlapping p95={overlapping_p95*1000:.2f}ms, ratio={ratio:.2f}x"
        )

    @pytest.mark.parametrize(
        "version,ecc_name,min_per_layer",
        [
            (20, "M", 50),   # v20/M has 288B total — tight, but usable for compact payloads
            (40, "M", 100),  # v40/M has 2331B — ample room for full-size layers
        ],
    )
    def test_capacity_overhead_acceptable(
        self, version: int, ecc_name: str, min_per_layer: int,
    ) -> None:
        """A-HYP3 — 3-layer encoding leaves usable bytes per B and C layer.

        Accounting for: Layer A (~100 chars) + delimiter (12 bytes) +
        base64 overhead (~33%) + binary header (5 bytes).

        v20/M is capacity-constrained (63B per layer), so the threshold is
        lower (50B) — enough for compact payloads but not full-size blocks.
        v40/M must clear 100B per layer.
        """
        spec_cap = _SPEC_BYTE_CAPACITY[(version, ecc_name)]

        # Budget: total QR capacity in bytes (text mode)
        a_len = 100  # typical Layer A
        delimiter_len = len(DELIMITER)
        header_raw = 5  # version(1) + b_len(2) + c_len(2)

        # Available raw bytes for B+C before base64 expansion:
        # base64 output len = ceil(raw/3)*4
        # trailer_text_len = ceil((header_raw + b_raw + c_raw) / 3) * 4
        # total = a_len + delimiter_len + trailer_text_len <= spec_cap
        trailer_budget = spec_cap - a_len - delimiter_len
        # Invert base64: raw_bytes = trailer_budget * 3 / 4
        raw_budget = (trailer_budget * 3) // 4
        bc_budget = raw_budget - header_raw  # bytes available for B+C combined
        per_layer = bc_budget // 2

        assert per_layer >= min_per_layer, (
            f"v{version}/{ecc_name}: per-layer budget {per_layer}B < {min_per_layer}B minimum "
            f"(spec_cap={spec_cap}, trailer_budget={trailer_budget}, "
            f"raw_budget={raw_budget}, bc_budget={bc_budget})"
        )
        print(
            f"\n[A-HYP3] v{version}/{ecc_name}: spec_cap={spec_cap}, "
            f"per-layer B/C budget={per_layer}B — OK (>= {min_per_layer}B)"
        )


# ---------------------------------------------------------------------------
# A-HYP4 — Visual identity
# ---------------------------------------------------------------------------

class TestHYP4VisualIdentity:
    """A-HYP4: The output is a single standard QR symbol."""

    def _make_three_layer_img(self, tmp_dir: pathlib.Path, name: str) -> pathlib.Path:
        """Generate a typical 3-layer QR image and save it."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b()
        c_data = _sample_layer_c()
        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)
        img_path = tmp_dir / f"hyp4_{name}.png"
        img.save(str(img_path))
        return img_path

    def test_single_symbol_detected(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP4 — pyzbar finds exactly 1 QR symbol in the image."""
        img_path = self._make_three_layer_img(tmp_dir, "single_pyzbar")

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1, (
            f"Expected exactly 1 QR symbol, pyzbar found {len(decoded)}"
        )
        print(f"\n[A-HYP4] pyzbar: exactly 1 symbol detected — OK")

    def test_opencv_single_detection(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP4 — OpenCV finds exactly 1 QR code."""
        img_path = self._make_three_layer_img(tmp_dir, "single_opencv")

        bgr = cv2.imread(str(img_path))
        assert bgr is not None, "cv2.imread returned None"
        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(bgr)

        assert text, "OpenCV decoded empty string — no QR found"
        assert points is not None, "OpenCV found no QR code corners"
        # points shape: (1, 4, 2) for a single QR code
        assert points.shape[0] == 1, (
            f"Expected 1 QR detection, OpenCV found {points.shape[0]}"
        )
        print(f"\n[A-HYP4] OpenCV: exactly 1 QR detection — OK")

    def test_qr_is_standard_compliant(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP4 — The QR can be read by both pyzbar and OpenCV (cross-reader compliance)."""
        img_path = self._make_three_layer_img(tmp_dir, "compliance")

        # pyzbar
        pyzbar_result = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(pyzbar_result) == 1, "pyzbar failed to decode"
        pyzbar_text = pyzbar_result[0].data.decode("utf-8")

        # OpenCV
        bgr = cv2.imread(str(img_path))
        detector = cv2.QRCodeDetector()
        cv2_text, points, _ = detector.detectAndDecode(bgr)

        assert cv2_text, "OpenCV failed to decode"
        assert points is not None, "OpenCV found no corners"
        assert pyzbar_text == cv2_text, (
            f"Cross-reader mismatch — QR may not be standard compliant"
        )
        print(f"\n[A-HYP4] Cross-reader standard compliance — OK")

    def test_version_not_excessive(self, tmp_dir: pathlib.Path) -> None:
        """A-HYP4 — For a typical ~300B 3-layer payload, QR version <= 20."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)
        payload = encode_layers(a_text, b_data, c_data)

        qr = qrcode.QRCode(
            error_correction=qrc.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        assert qr.version <= 20, (
            f"QR version {qr.version} exceeds v20 for a {len(payload)}-byte "
            f"3-layer payload — physical size may be excessive"
        )
        print(
            f"\n[A-HYP4] Payload={len(payload)}B -> QR version {qr.version} "
            f"(<= 20) — OK"
        )
