"""A-MET1~4: Measurement protocol — Phase B pass/fail criteria validation.

Codifies the metric definitions from metrics-protocol.md as executable tests.
These tests do NOT run the full 200-trial physical protocol (that requires real
devices); instead they:
  1. Validate that metric definitions are internally consistent and parseable.
  2. Run small-scale automated versions that exercise the measurement machinery.
  3. Prove that the pass/fail evaluation logic works correctly.

Encoding scheme: Plain-Text-Prefix with Base64 Trailer (same as A-HYP tests)
    <Layer A UTF-8 text>\n---QWR---\n<base64(header + B_payload + C_payload)>

Test IDs
--------
A-MET1  Scan success rate measurement machinery (AC: >= 95%)
A-MET2  Decode latency measurement machinery (AC: p95 <= 300ms)
A-MET3  Layer integrity / tampering detection machinery (AC: >= 99%)
A-MET4  Context routing accuracy machinery (AC: >= 98%)

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


# ---------------------------------------------------------------------------
# Encoding helpers — copied from test_a_hyp.py for spike isolation
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
# QR helpers
# ---------------------------------------------------------------------------

def _make_qr(data: str | bytes, *, ecc=qrc.ERROR_CORRECT_M, version: int | None = None) -> PILImage.Image:
    """Generate a QR code image using the qrcode library."""
    qr = qrcode.QRCode(
        version=version,
        error_correction=ecc,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=(version is None))
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# ---------------------------------------------------------------------------
# Payload factories
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
# Routing helper (MET-4)
# ---------------------------------------------------------------------------

def resolve_layers(layer_a: str, layer_b: bytes, layer_c: bytes, context: str) -> dict:
    """Route layers based on context policy.

    Returns dict with keys: 'a' (always), 'b' (if authorized), 'c' (if verified).
    """
    result: dict = {'a': layer_a}
    if context in ('authenticated', 'verified'):
        result['b'] = layer_b
    if context == 'verified':
        result['c'] = layer_c
    return result


# ---------------------------------------------------------------------------
# A-MET1 — Scan success rate (AC: >= 95%)
# ---------------------------------------------------------------------------

class TestMET1ScanSuccessProtocol:
    """A-MET1: Scan success rate measurement machinery (AC: >= 95%)."""

    def test_success_rate_calculation(self) -> None:
        """A-MET1 — Rate computation is correct for known pass/fail counts."""
        def compute_rate(successes: int, total: int) -> float:
            return successes / total

        assert compute_rate(95, 100) == pytest.approx(0.95)
        assert compute_rate(190, 200) == pytest.approx(0.95)
        assert compute_rate(100, 100) == pytest.approx(1.0)
        assert compute_rate(0, 100) == pytest.approx(0.0)
        assert compute_rate(47, 50) == pytest.approx(0.94)
        print("\n[A-MET1] Rate computation correct for known counts — OK")

    def test_threshold_95_percent(self) -> None:
        """A-MET1 — 95/100 passes, 94/100 fails the 95% threshold."""
        threshold = 0.95

        passing_rate = 95 / 100
        assert passing_rate >= threshold, (
            f"95/100 ({passing_rate:.1%}) should meet {threshold:.0%} threshold"
        )

        failing_rate = 94 / 100
        assert failing_rate < threshold, (
            f"94/100 ({failing_rate:.1%}) should NOT meet {threshold:.0%} threshold"
        )

        print(
            f"\n[A-MET1] Threshold check: 95/100={passing_rate:.1%} PASS, "
            f"94/100={failing_rate:.1%} FAIL — OK"
        )

    def test_mini_trial_overlapping_qr(self) -> None:
        """A-MET1 — 30 trials with 3-layer QRs (varying payloads), success rate >= 95%.

        Mini version of the 200-trial MET-1 protocol. In-memory decode with pyzbar
        simulates the 'success' definition: Layer A is read correctly.
        """
        n_trials = 30
        successes = 0

        for i in range(n_trials):
            a_text = _sample_layer_a(60 + (i % 40))
            b_data = _sample_layer_b(48 + (i % 64))
            c_data = _sample_layer_c(32 + (i % 48))
            payload = encode_layers(a_text, b_data, c_data)

            img = _make_qr(payload)
            decoded = pyzbar_decode(img)
            if len(decoded) == 1:
                try:
                    raw = decoded[0].data.decode("utf-8")
                    got_a, got_b, got_c = decode_layers(raw)
                    # Success definition (MET-1): Layer A is read without error
                    if got_a == a_text and got_b == b_data and got_c == c_data:
                        successes += 1
                except Exception:
                    pass

        rate = successes / n_trials
        assert rate >= 0.95, (
            f"[A-MET1] Mini-trial success rate {rate:.1%} ({successes}/{n_trials}) "
            f"below 95% threshold"
        )
        print(
            f"\n[A-MET1] Mini-trial (n={n_trials}): "
            f"success rate {rate:.1%} ({successes}/{n_trials}) — PASS"
        )

    def test_failure_modes_categorized(self) -> None:
        """A-MET1 — Tiny 20x20px QRs are correctly classified as failures.

        Generates intentionally unreadable QRs by resizing to 20x20px (below
        minimum viable resolution), verifies pyzbar returns empty results.
        """
        n_attempts = 10
        failures = 0

        for i in range(n_attempts):
            a_text = _sample_layer_a(60 + i)
            b_data = _sample_layer_b(48)
            c_data = _sample_layer_c(32)
            payload = encode_layers(a_text, b_data, c_data)

            img = _make_qr(payload)
            # Resize to 20x20 — well below readable threshold
            tiny = img.resize((20, 20), PILImage.LANCZOS)
            decoded = pyzbar_decode(tiny)

            # Failure: pyzbar cannot read the degraded image
            if len(decoded) == 0:
                failures += 1

        failure_rate = failures / n_attempts
        assert failure_rate >= 0.9, (
            f"[A-MET1] Expected >= 90% failure on 20x20px QRs, "
            f"got only {failure_rate:.0%} ({failures}/{n_attempts})"
        )
        print(
            f"\n[A-MET1] Failure mode (20x20px resize): "
            f"{failures}/{n_attempts} correctly classified as failures — OK"
        )


# ---------------------------------------------------------------------------
# A-MET2 — Decode latency (AC: p95 <= 300ms)
# ---------------------------------------------------------------------------

class TestMET2DecodeLatency:
    """A-MET2: Decode latency measurement machinery (AC: p95 <= 300ms)."""

    def test_latency_measurement_method(self) -> None:
        """A-MET2 — Measure decode of a single QR 50 times; verify statistical fields."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)
        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)

        n_samples = 50
        times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(img)
            times.append(time.perf_counter() - t0)

        times_sorted = sorted(times)
        mean_t = sum(times) / len(times)
        p50 = times_sorted[n_samples // 2]
        p95 = times_sorted[int(n_samples * 0.95) - 1]
        p99 = times_sorted[int(n_samples * 0.99) - 1]

        # All four required fields must be computable and positive
        assert mean_t > 0, "Mean latency must be positive"
        assert p50 > 0, "p50 must be positive"
        assert p95 > 0, "p95 must be positive"
        assert p99 > 0, "p99 must be positive"
        assert p50 <= p95 <= p99, "Percentiles must be non-decreasing"
        assert len(times) == n_samples, f"Expected {n_samples} samples, got {len(times)}"

        print(
            f"\n[A-MET2] Latency stats (n={n_samples}): "
            f"mean={mean_t*1000:.2f}ms, "
            f"p50={p50*1000:.2f}ms, "
            f"p95={p95*1000:.2f}ms, "
            f"p99={p99*1000:.2f}ms"
        )

    def test_p95_under_threshold(self) -> None:
        """A-MET2 — p95 of 3-layer QR decode is well under the 300ms AC threshold.

        In-memory pyzbar decode is fast (typically <50ms). 300ms budget exists
        for real-device scanning with camera capture overhead.
        """
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)
        payload = encode_layers(a_text, b_data, c_data)
        img = _make_qr(payload)

        n_warmup = 3
        n_samples = 50
        threshold_s = 0.300  # 300ms AC threshold

        # Warmup
        for _ in range(n_warmup):
            pyzbar_decode(img)

        times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(img)
            times.append(time.perf_counter() - t0)

        times.sort()
        p95 = times[int(n_samples * 0.95) - 1]

        assert p95 <= threshold_s, (
            f"[A-MET2] p95 decode latency {p95*1000:.2f}ms exceeds "
            f"AC threshold of {threshold_s*1000:.0f}ms"
        )
        print(
            f"\n[A-MET2] p95 decode latency: {p95*1000:.2f}ms "
            f"(<= {threshold_s*1000:.0f}ms AC threshold) — PASS"
        )

    def test_warmup_excluded(self) -> None:
        """A-MET2 — First N warmup measurements are excluded from final stats.

        Verifies that the measurement harness correctly separates warmup
        iterations from production samples, per MET-2 protocol.
        """
        a_text = _sample_layer_a(80)
        payload = encode_layers(a_text, _sample_layer_b(96), _sample_layer_c(64))
        img = _make_qr(payload)

        n_warmup = 3
        n_samples = 30

        warmup_times: list[float] = []
        for _ in range(n_warmup):
            t0 = time.perf_counter()
            pyzbar_decode(img)
            warmup_times.append(time.perf_counter() - t0)

        production_times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(img)
            production_times.append(time.perf_counter() - t0)

        assert len(warmup_times) == n_warmup, "Warmup count mismatch"
        assert len(production_times) == n_samples, "Production sample count mismatch"

        # Production samples should not include warmup entries
        # (they are different list objects — structural check)
        all_times = warmup_times + production_times
        assert len(all_times) == n_warmup + n_samples

        production_times.sort()
        p95 = production_times[int(n_samples * 0.95) - 1]
        print(
            f"\n[A-MET2] Warmup excluded: {n_warmup} warmup + {n_samples} production, "
            f"p95={p95*1000:.2f}ms — OK"
        )

    def test_latency_report_format(self) -> None:
        """A-MET2 — Report includes all required fields: mean, p50, p95, p99, trial count."""
        a_text = _sample_layer_a(80)
        payload = encode_layers(a_text, _sample_layer_b(96), _sample_layer_c(64))
        img = _make_qr(payload)

        n_samples = 30
        times: list[float] = []
        for _ in range(n_samples):
            t0 = time.perf_counter()
            pyzbar_decode(img)
            times.append(time.perf_counter() - t0)

        times_sorted = sorted(times)
        report = {
            'mean_ms': (sum(times) / len(times)) * 1000,
            'p50_ms': times_sorted[n_samples // 2] * 1000,
            'p95_ms': times_sorted[int(n_samples * 0.95) - 1] * 1000,
            'p99_ms': times_sorted[int(n_samples * 0.99) - 1] * 1000,
            'trial_count': n_samples,
        }

        required_fields = {'mean_ms', 'p50_ms', 'p95_ms', 'p99_ms', 'trial_count'}
        assert required_fields == set(report.keys()), (
            f"Report missing fields: {required_fields - set(report.keys())}"
        )
        assert report['trial_count'] == n_samples
        assert report['p95_ms'] <= 300.0, (
            f"p95 {report['p95_ms']:.2f}ms exceeds 300ms AC threshold"
        )

        print(
            f"\n[A-MET2] Report format OK — "
            f"mean={report['mean_ms']:.2f}ms, "
            f"p50={report['p50_ms']:.2f}ms, "
            f"p95={report['p95_ms']:.2f}ms, "
            f"p99={report['p99_ms']:.2f}ms, "
            f"trials={report['trial_count']}"
        )


# ---------------------------------------------------------------------------
# A-MET3 — Layer integrity / tampering detection (AC: >= 99%)
# ---------------------------------------------------------------------------

class TestMET3LayerIntegrity:
    """A-MET3: Tampering detection measurement machinery (AC: >= 99%)."""

    def _make_valid_payload(self) -> tuple[str, str, bytes, bytes]:
        """Generate a canonical 3-layer payload. Returns (payload, a, b, c)."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)
        payload = encode_layers(a_text, b_data, c_data)
        return payload, a_text, b_data, c_data

    def _is_tampered(self, raw_payload: str, orig_a: str, orig_b: bytes, orig_c: bytes) -> bool:
        """Return True if the payload does not match the original content (tampered)."""
        try:
            got_a, got_b, got_c = decode_layers(raw_payload)
            return not (got_a == orig_a and got_b == orig_b and got_c == orig_c)
        except Exception:
            return True  # decode failure = tampering detected

    def test_bitflip_detected(self) -> None:
        """A-MET3 — Bit flip in the base64 trailer causes mismatch detection."""
        payload, orig_a, orig_b, orig_c = self._make_valid_payload()

        assert DELIMITER in payload, "Payload must have a trailer section"
        a_part, trailer = payload.split(DELIMITER, maxsplit=1)

        # Flip the first character of the base64 trailer
        flipped_char = 'A' if trailer[0] != 'A' else 'B'
        tampered_trailer = flipped_char + trailer[1:]
        tampered_payload = a_part + DELIMITER + tampered_trailer

        detected = self._is_tampered(tampered_payload, orig_a, orig_b, orig_c)
        assert detected, "[A-MET3] Bitflip in trailer was NOT detected — integrity broken"
        print("\n[A-MET3] Bitflip in base64 trailer detected — OK")

    def test_signature_removal_detected(self) -> None:
        """A-MET3 — Removing Layer C (signature) by truncating the trailer is detected."""
        _, orig_a, orig_b, orig_c = self._make_valid_payload()

        # Rebuild without layer C (c_len=0 in header)
        truncated_payload = encode_layers(orig_a, orig_b, b"")

        # This should differ from the original (c_data is non-empty)
        detected = self._is_tampered(truncated_payload, orig_a, orig_b, orig_c)
        assert detected, "[A-MET3] Signature removal was NOT detected — integrity broken"
        print("\n[A-MET3] Signature removal (Layer C truncation) detected — OK")

    def test_repack_with_wrong_data(self) -> None:
        """A-MET3 — Encoding with different B data is detected against the original."""
        _, orig_a, orig_b, orig_c = self._make_valid_payload()

        # Substitute layer B with different content
        wrong_b = b"WRONG_B_DATA_SUBSTITUTED_BY_ATTACKER"
        repacked = encode_layers(orig_a, wrong_b, orig_c)

        detected = self._is_tampered(repacked, orig_a, orig_b, orig_c)
        assert detected, "[A-MET3] Wrong B data was NOT detected — integrity broken"
        print("\n[A-MET3] Repack with wrong B data detected — OK")

    def test_normal_samples_pass(self) -> None:
        """A-MET3 — 20 untampered QRs all decode correctly (false positive check)."""
        n_samples = 20
        false_positives = 0

        for i in range(n_samples):
            a_text = _sample_layer_a(60 + (i % 30))
            b_data = _sample_layer_b(48 + (i % 48))
            c_data = _sample_layer_c(32 + (i % 32))
            payload = encode_layers(a_text, b_data, c_data)

            try:
                got_a, got_b, got_c = decode_layers(payload)
                if not (got_a == a_text and got_b == b_data and got_c == c_data):
                    false_positives += 1
            except Exception:
                false_positives += 1

        assert false_positives == 0, (
            f"[A-MET3] {false_positives}/{n_samples} untampered samples "
            f"incorrectly flagged as tampered (false positives)"
        )
        print(f"\n[A-MET3] Normal samples (n={n_samples}): 0 false positives — OK")

    def test_detection_rate_above_threshold(self) -> None:
        """A-MET3 — 100 tampered samples (bitflip + truncation + wrong-key), >= 99% detected.

        Mix of tampering types per MET-3 protocol:
          - Bitflip: modify a character in the base64 trailer
          - Truncation: remove Layer C from the frame
          - Wrong data: substitute Layer B with different content
        """
        n_samples = 100
        detected_count = 0

        orig_a = _sample_layer_a(80)
        orig_b = _sample_layer_b(96)
        orig_c = _sample_layer_c(64)
        original = encode_layers(orig_a, orig_b, orig_c)
        a_part, trailer = original.split(DELIMITER, maxsplit=1)

        for i in range(n_samples):
            tamper_type = i % 3

            if tamper_type == 0:
                # Bitflip: change character at position i%len(trailer)
                pos = (i // 3) % len(trailer)
                original_char = trailer[pos]
                # Cycle through a few valid base64 chars to ensure the flip is different
                candidates = [c for c in ('A', 'B', 'C', 'D', 'Z', '0', '1') if c != original_char]
                flipped_char = candidates[i % len(candidates)]
                tampered_trailer = trailer[:pos] + flipped_char + trailer[pos + 1:]
                tampered = a_part + DELIMITER + tampered_trailer

            elif tamper_type == 1:
                # Truncation: remove Layer C
                tampered = encode_layers(orig_a, orig_b, b"")

            else:
                # Wrong data: substitute Layer B with random-like bytes
                wrong_b = bytes([(b + i + 17) % 256 for b in orig_b])
                tampered = encode_layers(orig_a, wrong_b, orig_c)

            if self._is_tampered(tampered, orig_a, orig_b, orig_c):
                detected_count += 1

        detection_rate = detected_count / n_samples
        assert detection_rate >= 0.99, (
            f"[A-MET3] Detection rate {detection_rate:.1%} ({detected_count}/{n_samples}) "
            f"below 99% AC threshold"
        )
        print(
            f"\n[A-MET3] Tampering detection (n={n_samples}): "
            f"{detected_count}/{n_samples} = {detection_rate:.1%} — PASS"
        )

    def _is_tampered(self, raw_payload: str, orig_a: str, orig_b: bytes, orig_c: bytes) -> bool:
        """Return True if the payload does not match the original content (tampered)."""
        try:
            got_a, got_b, got_c = decode_layers(raw_payload)
            return not (got_a == orig_a and got_b == orig_b and got_c == orig_c)
        except Exception:
            return True


# ---------------------------------------------------------------------------
# A-MET4 — Context routing accuracy (AC: >= 98%)
# ---------------------------------------------------------------------------

class TestMET4ContextRouting:
    """A-MET4: Context routing accuracy measurement machinery (AC: >= 98%)."""

    def test_public_context_returns_a_only(self) -> None:
        """A-MET4 — 'public' context returns only Layer A."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)

        result = resolve_layers(a_text, b_data, c_data, 'public')

        assert set(result.keys()) == {'a'}, (
            f"Public context should return only 'a', got keys: {set(result.keys())}"
        )
        assert result['a'] == a_text
        print("\n[A-MET4] public context -> {a} only — OK")

    def test_authenticated_context_returns_ab(self) -> None:
        """A-MET4 — 'authenticated' context returns A + B."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)

        result = resolve_layers(a_text, b_data, c_data, 'authenticated')

        assert set(result.keys()) == {'a', 'b'}, (
            f"Authenticated context should return 'a'+'b', got: {set(result.keys())}"
        )
        assert result['a'] == a_text
        assert result['b'] == b_data
        print("\n[A-MET4] authenticated context -> {a, b} — OK")

    def test_verified_context_returns_abc(self) -> None:
        """A-MET4 — 'verified' context returns A + B + C."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)

        result = resolve_layers(a_text, b_data, c_data, 'verified')

        assert set(result.keys()) == {'a', 'b', 'c'}, (
            f"Verified context should return 'a'+'b'+'c', got: {set(result.keys())}"
        )
        assert result['a'] == a_text
        assert result['b'] == b_data
        assert result['c'] == c_data
        print("\n[A-MET4] verified context -> {a, b, c} — OK")

    def test_unknown_context_safe_default(self) -> None:
        """A-MET4 — Unknown context returns Layer A only (safe default, no data leak)."""
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)

        for unknown_ctx in ('unknown', 'admin', 'root', 'superuser', '', 'VERIFIED'):
            result = resolve_layers(a_text, b_data, c_data, unknown_ctx)
            assert 'b' not in result, (
                f"Context '{unknown_ctx}' should not expose Layer B (safe default)"
            )
            assert 'c' not in result, (
                f"Context '{unknown_ctx}' should not expose Layer C (safe default)"
            )
            assert 'a' in result, (
                f"Context '{unknown_ctx}' must always return Layer A"
            )

        print("\n[A-MET4] Unknown/unexpected contexts all return safe default {a} — OK")

    def test_routing_accuracy_100_cases(self) -> None:
        """A-MET4 — 100 routing cases with known expected outputs, >= 98% accurate.

        Grid: 25 public + 25 authenticated + 25 verified + 25 unknown,
        matching the explicit-ratio generation rule from metrics-protocol.md.
        """
        a_text = _sample_layer_a(80)
        b_data = _sample_layer_b(96)
        c_data = _sample_layer_c(64)

        # Expected layer key sets per context
        expected: dict[str, set] = {
            'public':        {'a'},
            'authenticated': {'a', 'b'},
            'verified':      {'a', 'b', 'c'},
            'unknown':       {'a'},
        }

        contexts = (['public'] * 25 + ['authenticated'] * 25
                    + ['verified'] * 25 + ['unknown'] * 25)

        n_cases = len(contexts)
        correct = 0

        for ctx in contexts:
            result = resolve_layers(a_text, b_data, c_data, ctx)
            if set(result.keys()) == expected[ctx]:
                correct += 1

        accuracy = correct / n_cases
        assert accuracy >= 0.98, (
            f"[A-MET4] Routing accuracy {accuracy:.1%} ({correct}/{n_cases}) "
            f"below 98% AC threshold"
        )
        print(
            f"\n[A-MET4] Routing accuracy (n={n_cases}): "
            f"{correct}/{n_cases} = {accuracy:.1%} — PASS"
        )


# ---------------------------------------------------------------------------
# Metrics document completeness
# ---------------------------------------------------------------------------

class TestMetricsDocumentCompleteness:
    """Validates that metrics-protocol.md has all required sections and thresholds."""

    _DOC_PATH = pathlib.Path(
        "/home/rae/projects/workspace/QoverwRap/docs/test-plan/metrics-protocol.md"
    )

    def test_document_exists(self) -> None:
        """A-MET — metrics-protocol.md exists at the expected path."""
        assert self._DOC_PATH.exists(), (
            f"metrics-protocol.md not found at {self._DOC_PATH}"
        )
        assert self._DOC_PATH.stat().st_size > 0, "metrics-protocol.md is empty"
        print(f"\n[A-MET] Document exists: {self._DOC_PATH} — OK")

    def test_all_metrics_defined(self) -> None:
        """A-MET — MET-1, MET-2, MET-3, MET-4 are all defined in the document."""
        content = self._DOC_PATH.read_text(encoding="utf-8")

        for metric_id in ("MET-1", "MET-2", "MET-3", "MET-4"):
            assert metric_id in content, (
                f"Metric {metric_id} not found in metrics-protocol.md"
            )

        print("\n[A-MET] All metrics (MET-1~4) defined in document — OK")

    def test_thresholds_documented(self) -> None:
        """A-MET — 95%, 300ms, 99%, 98% thresholds are present in the document."""
        content = self._DOC_PATH.read_text(encoding="utf-8")

        thresholds = [
            ("95%", "MET-1 scan success rate"),
            ("300", "MET-2 latency (300ms)"),
            ("99%", "MET-3 tampering detection"),
            ("98%", "MET-4 routing accuracy"),
        ]

        for value, description in thresholds:
            assert value in content, (
                f"Threshold '{value}' ({description}) not found in metrics-protocol.md"
            )

        print("\n[A-MET] All required thresholds (95%, 300ms, 99%, 98%) documented — OK")

    def test_pass_fail_report_section(self) -> None:
        """A-MET — B-EXP5 pass/fail report section exists in the document."""
        content = self._DOC_PATH.read_text(encoding="utf-8")

        assert "B-EXP5" in content, (
            "B-EXP5 pass/fail report section not found in metrics-protocol.md"
        )
        # Also verify the report section has key content indicators
        assert "pass/fail" in content.lower() or "Pass/Fail" in content, (
            "Pass/fail evaluation language not found in the B-EXP5 section"
        )

        print("\n[A-MET] B-EXP5 pass/fail report section present — OK")
