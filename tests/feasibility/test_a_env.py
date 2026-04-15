"""A-ENV2~4: Environment durability — QR readability under transforms and degradation.

Feasibility spike: verify that QR codes survive real-world image transforms
(rotation, perspective tilt), image degradation (JPEG compression, blur, noise,
occlusion, rescaling), and characterise the payload-size vs success-rate curve.

All transforms are simulated via image processing — no physical devices.

Test IDs
--------
A-ENV2  Rotation and perspective tilt (simulated camera angle)
A-ENV3  Image degradation (JPEG, blur, noise, resize, occlusion)
A-ENV4  Payload size vs scan success / latency curve

Discovery
---------
(to be filled after running tests)
"""
import base64
import io
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
# Encoding helpers — will be extracted to a shared module in Phase B
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
# Shared helpers for image transforms
# ---------------------------------------------------------------------------

def _try_decode(img_array: np.ndarray) -> str | None:
    """Attempt to decode a QR code from a BGR numpy array via pyzbar.

    Returns the decoded UTF-8 string, or None on failure.
    """
    results = pyzbar_decode(img_array)
    if len(results) == 1:
        try:
            return results[0].data.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None


def _make_three_layer_payload() -> tuple[str, str, bytes, bytes]:
    """Generate a standard 3-layer payload. Returns (payload, a_text, b_data, c_data)."""
    a_text = _sample_layer_a(80)
    b_data = _sample_layer_b(96)
    c_data = _sample_layer_c(64)
    payload = encode_layers(a_text, b_data, c_data)
    return payload, a_text, b_data, c_data


def _rotate_image_cv2(bgr: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate a BGR image by an arbitrary angle with white background fill."""
    h, w = bgr.shape[:2]
    center = (w / 2.0, h / 2.0)
    mat = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    # Compute new bounding box size so nothing is clipped
    cos_a = abs(mat[0, 0])
    sin_a = abs(mat[0, 1])
    new_w = int(h * sin_a + w * cos_a)
    new_h = int(h * cos_a + w * sin_a)

    # Adjust translation
    mat[0, 2] += (new_w - w) / 2.0
    mat[1, 2] += (new_h - h) / 2.0

    return cv2.warpAffine(
        bgr, mat, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _perspective_tilt(bgr: np.ndarray, pct: float) -> np.ndarray:
    """Apply a perspective tilt simulating a camera viewing angle.

    Parameters
    ----------
    pct:
        Corner displacement as a fraction of image dimension (0.05 = 5%).
        Top-left and top-right corners are inset, simulating top-down tilt.
    """
    h, w = bgr.shape[:2]
    dx = int(w * pct)
    dy = int(h * pct)

    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    # Inset top corners to simulate viewing from above
    dst = np.float32([
        [dx, dy],
        [w - dx, dy],
        [w, h],
        [0, h],
    ])
    mat = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        bgr, mat, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


# ---------------------------------------------------------------------------
# A-ENV2 — Rotation and perspective tilt
# ---------------------------------------------------------------------------

class TestENV2RotationAndTilt:
    """A-ENV2: QR readability under rotation and perspective transforms (simulated)."""

    @pytest.mark.parametrize("angle", [0, 90, 180, 270])
    def test_rotation_0_90_180_270(self, angle: int) -> None:
        """A-ENV2 — QR is rotation-invariant at cardinal angles."""
        payload = "ENV2-rotation-cardinal-test"
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)
        rotated = _rotate_image_cv2(bgr, angle)

        decoded = _try_decode(rotated)
        assert decoded == payload, (
            f"Rotation {angle}deg: expected {payload!r}, got {decoded!r}"
        )
        print(f"\n[A-ENV2] Rotation {angle}deg — OK")

    @pytest.mark.parametrize("angle", [15, 30, 45, 60, 135])
    def test_rotation_arbitrary_angles(self, angle: int) -> None:
        """A-ENV2 — Arbitrary rotation: record pass/fail per angle.

        QR codes are rotation-invariant in principle, but interpolation
        artifacts from warpAffine may degrade readability at some angles.
        """
        payload = "ENV2-rotation-arbitrary"
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)
        rotated = _rotate_image_cv2(bgr, angle)

        decoded = _try_decode(rotated)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV2] Rotation {angle}deg — {status}")
        assert passed, (
            f"Rotation {angle}deg failed to decode (got {decoded!r})"
        )

    @pytest.mark.parametrize(
        "pct,label",
        [(0.05, "mild-5%"), (0.15, "moderate-15%"), (0.25, "severe-25%")],
    )
    def test_perspective_tilt(self, pct: float, label: str) -> None:
        """A-ENV2 — Perspective tilt at various severity levels.

        Uses a larger QR (box_size=10 default) to give the decoder more
        pixels to work with.  Records pass/fail for each tilt level.
        """
        payload = "ENV2-perspective-tilt-test"
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)
        tilted = _perspective_tilt(bgr, pct)

        decoded = _try_decode(tilted)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV2] Perspective tilt {label} — {status}")
        # Mild and moderate should pass; severe is informational
        if pct <= 0.15:
            assert passed, (
                f"Perspective tilt {label} failed (got {decoded!r})"
            )

    def test_three_layer_survives_rotation(self) -> None:
        """A-ENV2 — 3-layer overlapping QR rotated 45deg, full decode_layers roundtrip."""
        payload, a_text, b_data, c_data = _make_three_layer_payload()
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)
        rotated = _rotate_image_cv2(bgr, 45)

        decoded_raw = _try_decode(rotated)
        assert decoded_raw is not None, "3-layer QR at 45deg failed to decode"

        got_a, got_b, got_c = decode_layers(decoded_raw)
        assert got_a == a_text
        assert got_b == b_data
        assert got_c == c_data
        print(
            f"\n[A-ENV2] 3-layer 45deg rotation roundtrip OK — "
            f"A={len(a_text)}B, B={len(b_data)}B, C={len(c_data)}B"
        )


# ---------------------------------------------------------------------------
# A-ENV3 — Image degradation
# ---------------------------------------------------------------------------

class TestENV3ImageDegradation:
    """A-ENV3: QR readability under various image degradations."""

    @pytest.mark.parametrize("quality", [95, 80, 60, 40, 20, 10])
    def test_jpeg_compression_quality(self, quality: int) -> None:
        """A-ENV3 — JPEG compression at various quality levels."""
        payload = "ENV3-jpeg-compression-test"
        img = _make_qr(payload)

        # Save to JPEG in memory, reload
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        reloaded = PILImage.open(buf).convert("RGB")
        bgr = _pil_to_numpy(reloaded)

        decoded = _try_decode(bgr)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV3] JPEG q={quality} — {status}")
        # Quality >= 20 should be fine for QR at this size
        if quality >= 20:
            assert passed, f"JPEG q={quality} failed (got {decoded!r})"

    @pytest.mark.parametrize("scale", [1.0, 0.75, 0.5, 0.35, 0.25])
    def test_resize_downscale(self, scale: float) -> None:
        """A-ENV3 — Downscaling: smaller images are harder to read."""
        payload = "ENV3-downscale-test"
        img = _make_qr(payload)
        w, h = img.size
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = img.resize((new_w, new_h), PILImage.LANCZOS)
        bgr = _pil_to_numpy(resized)

        decoded = _try_decode(bgr)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV3] Downscale {scale}x ({new_w}x{new_h}) — {status}")
        # Scales >= 0.35 should be readable
        if scale >= 0.35:
            assert passed, f"Downscale {scale}x failed (got {decoded!r})"

    @pytest.mark.parametrize("scale", [1.5, 2.0, 3.0])
    def test_resize_upscale(self, scale: float) -> None:
        """A-ENV3 — Upscaling: more pixels should always pass.

        Uses NEAREST resampling to preserve sharp QR module edges.
        LANCZOS blurs module boundaries on upscale, causing decode failure.
        """
        payload = "ENV3-upscale-test"
        img = _make_qr(payload)
        w, h = img.size
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = img.resize((new_w, new_h), PILImage.NEAREST)
        bgr = _pil_to_numpy(resized)

        decoded = _try_decode(bgr)
        assert decoded == payload, (
            f"Upscale {scale}x ({new_w}x{new_h}) failed (got {decoded!r})"
        )
        print(f"\n[A-ENV3] Upscale {scale}x ({new_w}x{new_h}) — PASS")

    def test_partial_occlusion(self) -> None:
        """A-ENV3 — Partial occlusion sweep with gray patches in the data region.

        ECC_M recovers ~15% codeword damage, ECC_H recovers ~30%.
        Damage is restricted to the interior data region (avoiding the ~9-module
        border where finder patterns, timing, and format info live) and uses
        gray (128,128,128) patches rather than black/white to avoid creating
        phantom QR modules.

        Discovery findings:
        - Pixel-area occlusion does not map 1:1 to codeword damage rate.
        - Finder patterns, timing patterns, and format info are structurally
          critical and not protected by data-level ECC.  Any damage to these
          regions causes total decode failure regardless of ECC level.
        - With damage confined to the data region, effective recovery is lower
          than theoretical ECC capacity because gray patches straddle module
          boundaries and create ambiguous thresholding for the decoder.
        - ECC_H reliably recovers from ~10% data-region damage; ECC_M from ~5%.
        """
        np.random.seed(42)
        configs = [
            (5, qrc.ERROR_CORRECT_M, "M"),
            (10, qrc.ERROR_CORRECT_M, "M"),
            (15, qrc.ERROR_CORRECT_M, "M"),
            (5, qrc.ERROR_CORRECT_H, "H"),
            (10, qrc.ERROR_CORRECT_H, "H"),
            (15, qrc.ERROR_CORRECT_H, "H"),
            (20, qrc.ERROR_CORRECT_H, "H"),
            (25, qrc.ERROR_CORRECT_H, "H"),
            (30, qrc.ERROR_CORRECT_H, "H"),
        ]
        results: list[tuple[int, str, bool]] = []

        for occlusion_pct, ecc, ecc_name in configs:
            payload = f"ENV3-occlusion-{occlusion_pct}pct"
            img = _make_qr(payload, ecc=ecc)
            bgr = _pil_to_numpy(img)
            h, w = bgr.shape[:2]

            # Avoid the ~9-module border (finder + timing + format info).
            # With box_size=10: 9 modules * 10 px = 90 px from each edge.
            border_px = 90
            safe_y0 = border_px
            safe_y1 = h - border_px
            safe_x0 = border_px
            safe_x1 = w - border_px

            if safe_y1 <= safe_y0 or safe_x1 <= safe_x0:
                # QR too small to have a meaningful data-only region
                results.append((occlusion_pct, ecc_name, False))
                continue

            safe_area = (safe_y1 - safe_y0) * (safe_x1 - safe_x0)
            target_pixels = int(safe_area * occlusion_pct / 100.0)
            patch_size = 5
            pixels_covered = 0
            while pixels_covered < target_pixels:
                py = np.random.randint(safe_y0, safe_y1 - patch_size)
                px = np.random.randint(safe_x0, safe_x1 - patch_size)
                bgr[py:py + patch_size, px:px + patch_size] = (128, 128, 128)
                pixels_covered += patch_size * patch_size

            decoded = _try_decode(bgr)
            passed = decoded == payload
            results.append((occlusion_pct, ecc_name, passed))

        # Print summary table
        print("\n[A-ENV3] Occlusion sweep results (data-region only, gray patches):")
        print(f"  {'Pct':>4}  {'ECC':>3}  {'Result':>6}")
        for pct, ecc_name, passed in results:
            print(f"  {pct:>3}%  {ecc_name:>3}  {'PASS' if passed else 'FAIL':>6}")

        # Assert: ECC_H should recover at least 5% data-region damage
        h_results = [(p, ok) for p, e, ok in results if e == "H"]
        h_low_pct_pass = any(ok for p, ok in h_results if p <= 10)
        assert h_low_pct_pass, (
            "ECC_H failed to recover even 5-10% data-region occlusion — "
            "unexpected for 30% theoretical capacity"
        )

    @pytest.mark.parametrize("ksize", [3, 5, 7, 11, 15])
    def test_gaussian_blur(self, ksize: int) -> None:
        """A-ENV3 — Gaussian blur with increasing kernel size."""
        payload = "ENV3-gaussian-blur-test"
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)
        blurred = cv2.GaussianBlur(bgr, (ksize, ksize), 0)

        decoded = _try_decode(blurred)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV3] Gaussian blur ksize={ksize} — {status}")
        # Small kernels should always be readable
        if ksize <= 7:
            assert passed, f"Blur ksize={ksize} failed (got {decoded!r})"

    @pytest.mark.parametrize("sigma", [5, 10, 20, 30, 50])
    def test_noise_addition(self, sigma: int) -> None:
        """A-ENV3 — Additive Gaussian noise with increasing sigma."""
        np.random.seed(42)
        payload = "ENV3-noise-test"
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)

        noise = np.random.normal(0, sigma, bgr.shape).astype(np.float64)
        noisy = np.clip(bgr.astype(np.float64) + noise, 0, 255).astype(np.uint8)

        decoded = _try_decode(noisy)
        passed = decoded == payload
        status = "PASS" if passed else "FAIL"
        print(f"\n[A-ENV3] Noise sigma={sigma} — {status}")
        # Low noise should be readable
        if sigma <= 20:
            assert passed, f"Noise sigma={sigma} failed (got {decoded!r})"

    def test_three_layer_survives_jpeg60(self) -> None:
        """A-ENV3 — 3-layer QR saved as JPEG q=60, full decode_layers roundtrip."""
        payload, a_text, b_data, c_data = _make_three_layer_payload()
        img = _make_qr(payload)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        buf.seek(0)
        reloaded = PILImage.open(buf).convert("RGB")
        bgr = _pil_to_numpy(reloaded)

        decoded_raw = _try_decode(bgr)
        assert decoded_raw is not None, "3-layer JPEG q=60 failed to decode"

        got_a, got_b, got_c = decode_layers(decoded_raw)
        assert got_a == a_text
        assert got_b == b_data
        assert got_c == c_data
        print(
            f"\n[A-ENV3] 3-layer JPEG q=60 roundtrip OK — "
            f"A={len(a_text)}B, B={len(b_data)}B, C={len(c_data)}B"
        )


# ---------------------------------------------------------------------------
# A-ENV4 — Payload size vs scan success / latency curve
# ---------------------------------------------------------------------------

class TestENV4PayloadSizeCurve:
    """A-ENV4: Payload size effects on scan success and decode speed."""

    def _make_payload_of_size(self, total_bytes: int) -> tuple[str, str, bytes, bytes]:
        """Generate a 3-layer payload targeting a specific total byte count.

        Distributes bytes roughly: A=20%, B=40%, C=40%.
        """
        a_len = max(20, total_bytes // 5)
        remaining = total_bytes - a_len
        b_len = remaining // 2
        c_len = remaining - b_len
        a_text = _sample_layer_a(a_len)
        b_data = _sample_layer_b(b_len)
        c_data = _sample_layer_c(c_len)
        payload = encode_layers(a_text, b_data, c_data)
        return payload, a_text, b_data, c_data

    @pytest.mark.parametrize(
        "target_bytes",
        [100, 200, 400, 600, 800, 1000, 1500, 2000],
    )
    def test_success_rate_vs_payload_size(self, target_bytes: int) -> None:
        """A-ENV4 — Measure scan success rate for 3-layer QRs of increasing size.

        Generates 10 QRs per size with slight payload variation and measures
        the fraction that round-trip correctly.
        """
        n_trials = 10
        successes = 0

        for i in range(n_trials):
            # Vary payload slightly per trial
            a_len = max(20, target_bytes // 5) + (i % 5)
            remaining = target_bytes - a_len
            b_len = remaining // 2 + (i % 3)
            c_len = max(1, remaining - b_len)
            a_text = _sample_layer_a(a_len)
            b_data = _sample_layer_b(b_len)
            c_data = _sample_layer_c(c_len)

            try:
                payload = encode_layers(a_text, b_data, c_data)
                img = _make_qr(payload)
                bgr = _pil_to_numpy(img)
                decoded_raw = _try_decode(bgr)
                if decoded_raw is not None:
                    got_a, got_b, got_c = decode_layers(decoded_raw)
                    if got_a == a_text and got_b == b_data and got_c == c_data:
                        successes += 1
            except Exception:
                pass

        rate = successes / n_trials
        status = "PASS" if rate >= 0.9 else "FAIL"
        print(f"\n[A-ENV4] Size {target_bytes:>5}B: success {rate:.0%} ({successes}/{n_trials}) — {status}")

        if target_bytes <= 1000:
            assert rate >= 0.9, (
                f"Payload {target_bytes}B: success rate {rate:.0%} < 90% "
                f"({successes}/{n_trials})"
            )

    @pytest.mark.parametrize(
        "target_bytes",
        [100, 500, 1000, 1500, 2000],
    )
    def test_decode_latency_vs_payload_size(self, target_bytes: int) -> None:
        """A-ENV4 — Measure p50 and p95 decode latency per payload size.

        Runs 20 samples per size after a 3-sample warmup.
        """
        payload, _, _, _ = self._make_payload_of_size(target_bytes)
        img = _make_qr(payload)
        bgr = _pil_to_numpy(img)

        # Warmup
        for _ in range(3):
            _try_decode(bgr)

        n_samples = 20
        times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            _try_decode(bgr)
            times.append(time.perf_counter() - t0)

        times.sort()
        p50 = times[n_samples // 2]
        p95 = times[int(n_samples * 0.95) - 1]

        print(
            f"\n[A-ENV4] Size {target_bytes:>5}B: "
            f"p50={p50*1000:.2f}ms, p95={p95*1000:.2f}ms"
        )
        # Observed: larger QR versions (1000B+) take 60-130ms p95.
        # Threshold set at 200ms to allow headroom on slower CI runners.
        assert p95 <= 0.200, (
            f"Payload {target_bytes}B: p95 decode {p95*1000:.2f}ms > 200ms"
        )

    @pytest.mark.parametrize(
        "target_bytes",
        [100, 200, 400, 600, 800, 1000, 1500, 2000],
    )
    def test_qr_version_vs_payload_size(self, target_bytes: int) -> None:
        """A-ENV4 — Record auto-selected QR version per payload size (informational)."""
        payload, _, _, _ = self._make_payload_of_size(target_bytes)

        qr = qrcode.QRCode(
            error_correction=qrc.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        print(
            f"\n[A-ENV4] Size {target_bytes:>5}B -> "
            f"QR version {qr.version} ({qr.modules_count}x{qr.modules_count} modules), "
            f"payload_len={len(payload)}B"
        )
        # Informational — no hard assertion, just record the curve
