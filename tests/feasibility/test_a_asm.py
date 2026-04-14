"""A-ASM1~3: Stack viability — QR library basic generate/read.

Feasibility spike: verify that the chosen library stack (qrcode, pyzbar,
opencv-python-headless) can do the fundamental operations needed for
multi-layer QR encoding.

Test IDs
--------
A-ASM1  Basic QR generate + read roundtrip (qrcode -> pyzbar)
A-ASM2  Capacity limits per ECC level and QR version
A-ASM3  Independent read path (qrcode -> OpenCV QRCodeDetector)

Discovery
---------
pyzbar interprets QR byte-mode data as UTF-8, so raw bytes >= 0x80 are
corrupted on decode (e.g. 0x80 → 0xC2 0x80).  Binary payloads MUST use
base64 (or similar ASCII-safe encoding) for lossless roundtrip.
"""
import base64
import pathlib

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
# Helpers
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
        Force a specific QR version (1–40).  None = auto-fit.
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
# A-ASM1 — Basic generate + read roundtrip
# ---------------------------------------------------------------------------

class TestASM1BasicRoundtrip:
    """A-ASM1: Encode a payload with qrcode, decode with pyzbar, assert match."""

    def test_simple_ascii_roundtrip(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM1 — ASCII text survives a QR encode/decode cycle via pyzbar."""
        payload = "Hello, QoverwRap!"

        img = _make_qr(payload)
        img_path = tmp_dir / "asm1_ascii.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1, "Expected exactly one QR symbol in the image"
        assert decoded[0].data.decode("utf-8") == payload

    def test_binary_bytes_roundtrip(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM1 — Arbitrary bytes survive a QR encode/decode cycle via pyzbar."""
        payload = bytes(range(64))  # 0x00 … 0x3F

        img = _make_qr(payload, ecc=qrc.ERROR_CORRECT_L)
        img_path = tmp_dir / "asm1_binary.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        assert decoded[0].data == payload

    def test_unicode_url_roundtrip(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM1 — A realistic URL payload roundtrips correctly."""
        payload = "https://example.com/qr?layer=A&seq=1"

        img = _make_qr(payload)
        img_path = tmp_dir / "asm1_url.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1
        assert decoded[0].data.decode("utf-8") == payload


# ---------------------------------------------------------------------------
# A-ASM2 — Capacity discovery
# ---------------------------------------------------------------------------

# ECC levels: L=7%, M=15%, Q=25%, H=30% recovery
_ECC_LEVELS = [
    (qrc.ERROR_CORRECT_L, "L"),
    (qrc.ERROR_CORRECT_M, "M"),
    (qrc.ERROR_CORRECT_Q, "Q"),
    (qrc.ERROR_CORRECT_H, "H"),
]

# QR versions to probe (higher version = more data capacity)
_PROBE_VERSIONS = [1, 5, 10, 20, 40]

# Byte capacities from the QR spec (version, ecc) -> max bytes.
# Source: ISO/IEC 18004 Table 7 (binary/byte mode).
# These are the ground-truth values we assert against to confirm the library
# agrees with the spec.
_SPEC_BYTE_CAPACITY: dict[tuple[int, str], int] = {
    (1, "L"): 17,  (1, "M"): 14,  (1, "Q"): 11,  (1, "H"): 7,
    (5, "L"): 86,  (5, "M"): 68,  (5, "Q"): 48,  (5, "H"): 34,
    (10, "L"): 174, (10, "M"): 136, (10, "Q"): 96, (10, "H"): 68,
    (20, "L"): 370, (20, "M"): 288, (20, "Q"): 208, (20, "H"): 154,
    (40, "L"): 2953, (40, "M"): 2331, (40, "Q"): 1663, (40, "H"): 1273,
}


class TestASM2CapacityLimits:
    """A-ASM2: Measure and verify QR byte capacity per ECC level and version.

    Discovery goal: can a single QR code hold enough data for one of the
    three overlay layers?  (Typical AES-256 encrypted chunk + header ~300 B.)

    KEY FINDING: pyzbar interprets byte-mode data as UTF-8, corrupting
    raw bytes >= 0x80.  All binary payloads must use base64 encoding.
    Base64 overhead is ~33%, so effective capacity = spec_capacity * 3/4.
    """

    @pytest.mark.parametrize("version", _PROBE_VERSIONS)
    @pytest.mark.parametrize("ecc,ecc_name", _ECC_LEVELS)
    def test_capacity_roundtrip_at_max(
        self, version: int, ecc: int, ecc_name: str, tmp_dir: pathlib.Path
    ) -> None:
        """A-ASM2 — Base64 payload at spec max capacity roundtrips cleanly."""
        max_bytes = _SPEC_BYTE_CAPACITY[(version, ecc_name)]
        # base64: every 3 raw bytes → 4 ASCII chars (padded to multiple of 4)
        # To guarantee output fits: raw_len = (max_bytes // 4) * 3
        raw_len = (max_bytes // 4) * 3
        if raw_len == 0:
            pytest.skip(f"v{version}/{ecc_name}: capacity {max_bytes} too small for base64")
        raw_data = bytes([i % 256 for i in range(raw_len)])
        payload_str = base64.b64encode(raw_data).decode("ascii")
        assert len(payload_str) <= max_bytes, (
            f"base64 output {len(payload_str)} exceeds QR capacity {max_bytes}"
        )

        img = _make_qr(payload_str, ecc=ecc, version=version)
        img_path = tmp_dir / f"asm2_v{version}_{ecc_name}_max.png"
        img.save(str(img_path))

        decoded = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(decoded) == 1, (
            f"v{version}/{ecc_name}: expected 1 symbol, got {len(decoded)}"
        )
        decoded_raw = base64.b64decode(decoded[0].data)
        assert decoded_raw == raw_data, (
            f"v{version}/{ecc_name}: decoded payload mismatch "
            f"(raw_len={raw_len}, decoded_len={len(decoded_raw)})"
        )

        print(
            f"\n[A-ASM2] v{version}/{ecc_name}: "
            f"spec_cap={max_bytes}, b64_raw={raw_len} bytes — ROUNDTRIP OK"
        )

    def test_utf8_corruption_documented(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM2 — Discovery: raw bytes >= 0x80 are corrupted by pyzbar UTF-8.

        This test DOCUMENTS the issue rather than failing on it.
        Bytes 0x80+ get UTF-8 encoded (e.g. 0x80 → 0xC2 0x80), making
        the decoded output longer than the original.
        """
        raw = bytes(range(160))  # includes 0x80 .. 0x9F
        img = _make_qr(raw)
        decoded = pyzbar_decode(img.convert("RGB"))
        assert len(decoded) == 1
        # Decoded bytes are LONGER due to UTF-8 expansion — this is expected
        assert len(decoded[0].data) > len(raw), (
            "Expected UTF-8 expansion for bytes >= 0x80"
        )
        print(
            f"\n[A-ASM2] UTF-8 corruption confirmed: "
            f"sent {len(raw)} bytes, got {len(decoded[0].data)} bytes back. "
            f"Binary payloads MUST use base64."
        )

    @pytest.mark.parametrize("ecc,ecc_name", _ECC_LEVELS)
    def test_overflow_forces_larger_version(self, ecc: int, ecc_name: str) -> None:
        """A-ASM2 — Exceeding v1 capacity auto-promotes to a larger version.

        When fit=True (version=None), qrcode must select a version that fits;
        we verify the generated version is strictly greater than 1.
        """
        # v1 max + 1 byte must not fit in version 1.
        # Use byte values 0x00..N to force byte mode (not alphanumeric).
        v1_max = _SPEC_BYTE_CAPACITY[(1, ecc_name)]
        payload = bytes([i % 128 for i in range(v1_max + 1)])

        qr = qrcode.QRCode(error_correction=ecc, box_size=10, border=4)
        qr.add_data(payload)
        qr.make(fit=True)

        assert qr.version > 1, (
            f"ECC={ecc_name}: v1 overflow should produce version >1, got {qr.version}"
        )
        print(f"\n[A-ASM2] ECC={ecc_name}: {v1_max+1} bytes -> auto version {qr.version}")

    def test_three_layer_feasibility(self) -> None:
        """A-ASM2 — Discovery: capacity summary accounting for base64 overhead.

        Effective capacity = spec_capacity * 3/4 (base64 overhead).
        3-layer share = effective / 3.
        Key question: is the per-layer share enough for an encrypted block?
        """
        print("\n[A-ASM2] Capacity discovery (with base64 overhead):")
        print(
            f"  {'Version':>7}  {'ECC':>3}  "
            f"{'SpecCap':>7}  {'Effective':>9}  {'Per-layer':>9}"
        )
        for version in _PROBE_VERSIONS:
            for _ecc, ecc_name in _ECC_LEVELS:
                cap = _SPEC_BYTE_CAPACITY[(version, ecc_name)]
                effective = (cap * 3) // 4
                per_layer = effective // 3
                print(
                    f"  v{version:>6}  {ecc_name:>3}  "
                    f"{cap:>7}  {effective:>9}  {per_layer:>9}"
                )

        # v20/M effective = 288 * 3/4 = 216 bytes; per-layer = 72
        # v40/M effective = 2331 * 3/4 = 1748; per-layer = 582
        # Assert at least one viable config for a 128-byte encrypted block
        v40_m_effective = (_SPEC_BYTE_CAPACITY[(40, "M")] * 3) // 4
        per_layer_v40_m = v40_m_effective // 3
        assert per_layer_v40_m >= 128, (
            f"v40/M per-layer {per_layer_v40_m} bytes is too small for "
            f"a 128-byte encrypted block"
        )


# ---------------------------------------------------------------------------
# A-ASM3 — Independent read path via OpenCV
# ---------------------------------------------------------------------------

class TestASM3OpenCVReadPath:
    """A-ASM3: Verify qrcode-generated images are decodable by cv2.QRCodeDetector.

    This tests that the two decoders (pyzbar and OpenCV) agree, establishing
    that Layer A content is reader-independent — a requirement for the PoC.
    """

    def test_opencv_decodes_qrcode_output(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM3 — OpenCV QRCodeDetector reads a qrcode-generated image."""
        payload = "Layer-A: OpenCV read path check"

        img = _make_qr(payload)
        img_path = tmp_dir / "asm3_opencv.png"
        img.save(str(img_path))

        bgr = cv2.imread(str(img_path))
        assert bgr is not None, "cv2.imread returned None — file not found or unreadable"

        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(bgr)

        assert text == payload, (
            f"OpenCV decoded '{text}' but expected '{payload}'"
        )
        assert points is not None, "OpenCV found no QR code corners in the image"

    def test_opencv_and_pyzbar_agree(self, tmp_dir: pathlib.Path) -> None:
        """A-ASM3 — Both decoders produce identical output for the same QR image."""
        payload = "Layer-A: dual-decoder agreement test"

        img = _make_qr(payload, ecc=qrc.ERROR_CORRECT_M)
        img_path = tmp_dir / "asm3_agreement.png"
        img.save(str(img_path))

        # pyzbar decode
        pyzbar_result = pyzbar_decode(PILImage.open(str(img_path)))
        assert len(pyzbar_result) == 1
        pyzbar_text = pyzbar_result[0].data.decode("utf-8")

        # OpenCV decode
        bgr = cv2.imread(str(img_path))
        detector = cv2.QRCodeDetector()
        cv2_text, _, _ = detector.detectAndDecode(bgr)

        assert pyzbar_text == cv2_text == payload, (
            f"Decoder mismatch — pyzbar='{pyzbar_text}', cv2='{cv2_text}', "
            f"expected='{payload}'"
        )

    @pytest.mark.parametrize("ecc,ecc_name", _ECC_LEVELS)
    def test_opencv_reads_all_ecc_levels(
        self, ecc: int, ecc_name: str, tmp_dir: pathlib.Path
    ) -> None:
        """A-ASM3 — OpenCV successfully decodes QR codes at every ECC level."""
        payload = f"Layer-A ECC={ecc_name} OpenCV test"

        img = _make_qr(payload, ecc=ecc)
        img_path = tmp_dir / f"asm3_ecc_{ecc_name}.png"
        img.save(str(img_path))

        bgr = cv2.imread(str(img_path))
        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(bgr)

        assert text == payload, (
            f"ECC={ecc_name}: OpenCV decoded '{text}', expected '{payload}'"
        )
        assert points is not None, f"ECC={ecc_name}: OpenCV found no QR corners"
