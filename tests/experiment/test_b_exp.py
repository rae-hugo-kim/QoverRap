"""B-EXP1~5: Phase B acceptance criteria gate tests.

These are the final AC measurement tests for QoverwRap Phase B.
They validate MET-1 through MET-4 metrics protocol requirements.

Test IDs
--------
B-EXP1  MET-1: Scan success rate >= 95% (200 scans)
B-EXP2  MET-2: Decode latency p95 <= 300ms
B-EXP3  MET-3: Layer integrity >= 99% tamper detection (200 tampered + 50 normal)
B-EXP4  MET-4: Context routing accuracy >= 98% (100 cases)
B-EXP5  AC gate summary: all metrics in one test (smaller sample for speed)
"""
from __future__ import annotations

import random
import time

import numpy as np
import pytest

try:
    import qrcode
    from qrcode.constants import (
        ERROR_CORRECT_H,
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
    )
    from PIL import Image
    from pyzbar.pyzbar import decode as pyzbar_decode
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"QR/pyzbar dependency missing: {exc}", allow_module_level=True)

from qoverwrap.crypto import generate_keypair, sign_layers, verify_signature
from qoverwrap.decoder import decode_layers
from qoverwrap.encoder import encode_layers
from qoverwrap.resolver import resolve


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_ECC_LEVELS = [
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
]

_ECC_NAMES = ["L", "M", "Q", "H"]


def _make_qr(data: str, *, ecc=ERROR_CORRECT_M, version=None, box_size: int = 10, border: int = 4) -> Image.Image:
    qr = qrcode.QRCode(version=version, error_correction=ecc, box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=(version is None))
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _pil_to_numpy(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("L"))


def _sample_layer_a(n: int = 60) -> str:
    base = "https://qoverwrap.example.com/v1/card?id=abc123&seq="
    return (base + "X" * max(0, n - len(base)))[:n]


def _sample_layer_b(n: int = 80) -> bytes:
    stub = b'{"issuer":"QoverwRap","ts":1700000000,"nonce":"'
    pad = b"A" * max(0, n - len(stub) - 2)
    return (stub + pad + b'"}')[:n]


def _build_signed_payload(rng: random.Random, b_size: int = 80) -> tuple[str, bytes, bytes, bytes, bytes]:
    """Build a signed 3-layer payload. Returns (payload_str, layer_a, layer_b, layer_c, pub_key)."""
    priv, pub = generate_keypair()
    layer_a = _sample_layer_a(50 + rng.randint(0, 30))
    layer_b = _sample_layer_b(b_size + rng.randint(0, 48))
    layer_c = sign_layers(priv, layer_a, layer_b)
    payload_str = encode_layers(layer_a, layer_b, layer_c)
    return payload_str, layer_a, layer_b, layer_c, pub


# ---------------------------------------------------------------------------
# B-EXP1: MET-1 Scan success rate
# ---------------------------------------------------------------------------

class TestBEXP1ScanSuccessRate:
    """B-EXP1: MET-1 — Software decoder scan success rate >= 95% over 200 scans."""

    def test_scan_success_rate_meets_ac(self) -> None:
        """B-EXP1 — Generate 200 3-layer QR images (4 ECC × 5 size tiers × 10 reps), scan with pyzbar.

        Success = pyzbar reads Layer A correctly from the QR image.
        Target: success_rate >= 0.95
        """
        # 4 ECC levels × 5 payload size tiers × 10 repetitions = 200
        payload_sizes = [50, 80, 120, 160, 200]
        total = 0
        successes = 0
        seed = 0

        for ecc_idx, ecc in enumerate(_ECC_LEVELS):
            for size_tier in payload_sizes:
                for rep in range(10):
                    rng = random.Random(seed)
                    seed += 1

                    priv, pub = generate_keypair()
                    layer_a = _sample_layer_a(size_tier)
                    layer_b = _sample_layer_b(min(size_tier, 128))
                    layer_c = sign_layers(priv, layer_a, layer_b)
                    payload_str = encode_layers(layer_a, layer_b, layer_c)

                    total += 1
                    try:
                        img = _make_qr(payload_str, ecc=ecc)
                        decoded = pyzbar_decode(img)
                        if decoded:
                            scanned_text = decoded[0].data.decode("utf-8", errors="replace")
                            # Success = decoded text starts with layer_a
                            if scanned_text.startswith(layer_a):
                                successes += 1
                    except Exception:
                        pass  # count as failure

        scan_success_rate = successes / total
        print(
            f"\n[B-EXP1] Scan success rate: {successes}/{total} = "
            f"{scan_success_rate:.1%} (target >= 95%)"
        )
        assert scan_success_rate >= 0.95, (
            f"[B-EXP1] MET-1 FAIL: scan success rate {scan_success_rate:.1%} < 95%"
        )
        print("[B-EXP1] test_scan_success_rate_meets_ac — PASS")


# ---------------------------------------------------------------------------
# B-EXP2: MET-2 Decode latency
# ---------------------------------------------------------------------------

class TestBEXP2DecodeLatency:
    """B-EXP2: MET-2 — Decode latency p95 <= 300ms."""

    def test_decode_latency_p95_under_300ms(self) -> None:
        """B-EXP2 — 200 decode_layers() + verify_signature() calls, p95 <= 300ms.

        Warmup: 1 run before measurement.
        Timing: time.perf_counter() per call.
        """
        rng = random.Random(42)
        payloads: list[tuple[str, bytes]] = []

        # Pre-generate 200 encoded payloads of varied sizes
        for i in range(200):
            priv, pub = generate_keypair()
            b_size = 40 + (i % 5) * 30  # 40, 70, 100, 130, 160 cycling
            layer_a = _sample_layer_a(50 + rng.randint(0, 30))
            layer_b = _sample_layer_b(b_size)
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)
            payloads.append((payload_str, pub))

        # 1 warmup run
        warmup_payload, warmup_pub = payloads[0]
        a, b, c = decode_layers(warmup_payload)
        verify_signature(warmup_pub, a, b, c)

        # Timed measurement
        latencies_ms: list[float] = []
        for payload_str, pub in payloads:
            t0 = time.perf_counter()
            a, b, c = decode_layers(payload_str)
            verify_signature(pub, a, b, c)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

        latencies_arr = np.array(latencies_ms)
        mean_ms = float(np.mean(latencies_arr))
        p50_ms = float(np.percentile(latencies_arr, 50))
        p95_ms = float(np.percentile(latencies_arr, 95))
        p99_ms = float(np.percentile(latencies_arr, 99))

        print(
            f"\n[B-EXP2] Decode latency over {len(latencies_ms)} calls:\n"
            f"  mean={mean_ms:.2f}ms  p50={p50_ms:.2f}ms  "
            f"p95={p95_ms:.2f}ms  p99={p99_ms:.2f}ms  (target p95 <= 300ms)"
        )
        assert p95_ms <= 300.0, (
            f"[B-EXP2] MET-2 FAIL: p95 latency {p95_ms:.2f}ms exceeds 300ms"
        )
        print("[B-EXP2] test_decode_latency_p95_under_300ms — PASS")


# ---------------------------------------------------------------------------
# B-EXP3: MET-3 Layer integrity
# ---------------------------------------------------------------------------

class TestBEXP3LayerIntegrity:
    """B-EXP3: MET-3 — Layer integrity >= 99% tamper detection."""

    def test_tamper_detection_rate_meets_ac(self) -> None:
        """B-EXP3 — 200 tampered samples across 6 tamper types, detection_rate >= 0.99.

        Tamper types (evenly distributed ~33 each):
          0: bit-flip in layer_a (modify a character)
          1: bit-flip in layer_b (flip a byte)
          2: bit-flip in layer_c (flip a byte in signature)
          3: wrong-key re-sign (sign with a different private key)
          4: truncated signature (drop last 16 bytes)
          5: zeroed signature (replace with 64 zero bytes)
        """
        rng = random.Random(42)
        n_samples = 200
        detected = 0

        for i in range(n_samples):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(50 + rng.randint(0, 30))
            layer_b = _sample_layer_b(60 + rng.randint(0, 68))
            layer_c = sign_layers(priv, layer_a, layer_b)

            tamper_type = i % 6

            if tamper_type == 0:
                # Bit-flip in layer_a: change one character
                pos = rng.randint(0, len(layer_a) - 1)
                a_list = list(layer_a)
                a_list[pos] = "Z" if a_list[pos] != "Z" else "Y"
                tampered_a = "".join(a_list)
                result = verify_signature(pub, tampered_a, layer_b, layer_c)

            elif tamper_type == 1:
                # Bit-flip in layer_b: flip a byte
                pos = rng.randint(0, len(layer_b) - 1)
                b_list = bytearray(layer_b)
                b_list[pos] ^= 0xFF
                result = verify_signature(pub, layer_a, bytes(b_list), layer_c)

            elif tamper_type == 2:
                # Bit-flip in layer_c: flip a byte in signature
                pos = rng.randint(0, len(layer_c) - 1)
                c_list = bytearray(layer_c)
                c_list[pos] ^= 0xFF
                result = verify_signature(pub, layer_a, layer_b, bytes(c_list))

            elif tamper_type == 3:
                # Wrong-key re-sign
                wrong_priv, _wrong_pub = generate_keypair()
                wrong_layer_c = sign_layers(wrong_priv, layer_a, layer_b)
                result = verify_signature(pub, layer_a, layer_b, wrong_layer_c)

            elif tamper_type == 4:
                # Truncated signature
                truncated_c = layer_c[:-16]
                result = verify_signature(pub, layer_a, layer_b, truncated_c)

            else:  # tamper_type == 5
                # Zeroed signature
                zeroed_c = bytes(64)
                result = verify_signature(pub, layer_a, layer_b, zeroed_c)

            # Tampered must return False — True means a missed detection
            if result is False:
                detected += 1

        detection_rate = detected / n_samples
        print(
            f"\n[B-EXP3] Tamper detection: {detected}/{n_samples} = "
            f"{detection_rate:.1%} (target >= 99%)"
        )
        assert detection_rate >= 0.99, (
            f"[B-EXP3] MET-3 FAIL: tamper detection rate {detection_rate:.1%} < 99%"
        )
        print("[B-EXP3] test_tamper_detection_rate_meets_ac — PASS")

    def test_normal_samples_no_false_positives(self) -> None:
        """B-EXP3 — 50 normal samples, all must verify True (zero false positives)."""
        rng = random.Random(99)
        n_samples = 50
        correct = 0

        for i in range(n_samples):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(50 + rng.randint(0, 30))
            layer_b = _sample_layer_b(60 + rng.randint(0, 68))
            layer_c = sign_layers(priv, layer_a, layer_b)
            if verify_signature(pub, layer_a, layer_b, layer_c):
                correct += 1

        print(
            f"\n[B-EXP3] Normal samples: {correct}/{n_samples} verified correctly "
            f"(target: zero false positives)"
        )
        assert correct == n_samples, (
            f"[B-EXP3] MET-3 FAIL: {n_samples - correct} false positives in "
            f"{n_samples} normal samples"
        )
        print("[B-EXP3] test_normal_samples_no_false_positives — PASS")


# ---------------------------------------------------------------------------
# B-EXP4: MET-4 Context routing accuracy
# ---------------------------------------------------------------------------

class TestBEXP4ContextRouting:
    """B-EXP4: MET-4 — Context routing accuracy >= 98% (100 cases)."""

    def test_routing_accuracy_meets_ac(self) -> None:
        """B-EXP4 — 100 resolve() calls with varied access levels, accuracy >= 98%.

        Grid:
          25 public            -> expect (A, None, None, verified=False)
          25 authenticated     -> expect (A, B,    None, verified=False)
          25 verified-valid    -> expect (A, B,    C,    verified=True)
          25 verified-invalid  -> expect (A, None, None, verified=False)
        """
        rng = random.Random(7)
        total = 100
        correct = 0

        # Pre-generate shared payloads for the 100 cases
        cases: list[tuple[str, str, bytes | None, tuple]] = []

        # 25 public
        for _ in range(25):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(55 + rng.randint(0, 25))
            layer_b = _sample_layer_b(70 + rng.randint(0, 50))
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)
            # expect: layer_a, layer_b=None, layer_c=None, verified=False
            cases.append((payload_str, "public", None, (layer_a, None, None, False)))

        # 25 authenticated
        for _ in range(25):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(55 + rng.randint(0, 25))
            layer_b = _sample_layer_b(70 + rng.randint(0, 50))
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)
            # expect: layer_a, layer_b (non-None), layer_c=None, verified=False
            cases.append((payload_str, "authenticated", None, (layer_a, layer_b, None, False)))

        # 25 verified-valid
        valid_cases = []
        for _ in range(25):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(55 + rng.randint(0, 25))
            layer_b = _sample_layer_b(70 + rng.randint(0, 50))
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)
            # expect: layer_a, layer_b, layer_c, verified=True
            cases.append((payload_str, "verified", pub, (layer_a, layer_b, layer_c, True)))

        # 25 verified-invalid (wrong key)
        for _ in range(25):
            priv, pub = generate_keypair()
            _wrong_priv, wrong_pub = generate_keypair()  # wrong public key
            layer_a = _sample_layer_a(55 + rng.randint(0, 25))
            layer_b = _sample_layer_b(70 + rng.randint(0, 50))
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)
            # verify with wrong key -> fails -> expect public fallback
            cases.append((payload_str, "verified", wrong_pub, (layer_a, None, None, False)))

        # Run all 100 cases
        for payload_str, access_level, pub_key, expected in cases:
            exp_a, exp_b, exp_c, exp_verified = expected
            resolved = resolve(payload_str, access_level, pub_key)

            # Compare fields
            match = (
                resolved.layer_a == exp_a
                and resolved.layer_b == exp_b
                and resolved.layer_c == exp_c
                and resolved.verified == exp_verified
            )
            if match:
                correct += 1

        accuracy = correct / total
        print(
            f"\n[B-EXP4] Routing accuracy: {correct}/{total} = "
            f"{accuracy:.1%} (target >= 98%)"
        )
        assert accuracy >= 0.98, (
            f"[B-EXP4] MET-4 FAIL: routing accuracy {accuracy:.1%} < 98%"
        )
        print("[B-EXP4] test_routing_accuracy_meets_ac — PASS")


# ---------------------------------------------------------------------------
# B-EXP5: AC gate summary
# ---------------------------------------------------------------------------

class TestBEXP5ACGate:
    """B-EXP5: AC gate summary — all 4 metrics in one test (smaller samples for speed)."""

    def test_all_metrics_pass(self) -> None:
        """B-EXP5 — Run all 4 metrics, collect results, assert all pass.

        Sample sizes reduced for speed:
          MET-1: 50 QR scans (1 ECC × 5 sizes × 10 reps)
          MET-2: 50 decode calls
          MET-3: 50 tampered + 25 normal
          MET-4: 25 routes (varied access levels)
        """
        results: dict[str, tuple[float, float, bool]] = {}

        # --- MET-1: Scan success rate ---
        rng1 = random.Random(11)
        payload_sizes = [50, 80, 120, 160, 200]
        met1_total = 0
        met1_ok = 0

        for size_tier in payload_sizes:
            for rep in range(10):
                priv, pub = generate_keypair()
                layer_a = _sample_layer_a(size_tier)
                layer_b = _sample_layer_b(min(size_tier, 128))
                layer_c = sign_layers(priv, layer_a, layer_b)
                payload_str = encode_layers(layer_a, layer_b, layer_c)
                met1_total += 1
                try:
                    img = _make_qr(payload_str, ecc=ERROR_CORRECT_M)
                    decoded = pyzbar_decode(img)
                    if decoded and decoded[0].data.decode("utf-8", errors="replace").startswith(layer_a):
                        met1_ok += 1
                except Exception:
                    pass

        met1_rate = met1_ok / met1_total
        met1_pass = met1_rate >= 0.95
        results["MET-1 Scan>=95%"] = (met1_rate, 0.95, met1_pass)

        # --- MET-2: Decode latency ---
        rng2 = random.Random(22)
        met2_payloads: list[tuple[str, bytes]] = []
        for i in range(50):
            priv, pub = generate_keypair()
            b_size = 40 + (i % 5) * 30
            layer_a = _sample_layer_a(50 + rng2.randint(0, 30))
            layer_b = _sample_layer_b(b_size)
            layer_c = sign_layers(priv, layer_a, layer_b)
            met2_payloads.append((encode_layers(layer_a, layer_b, layer_c), pub))

        # warmup
        a, b, c = decode_layers(met2_payloads[0][0])
        verify_signature(met2_payloads[0][1], a, b, c)

        met2_latencies: list[float] = []
        for ps, pk in met2_payloads:
            t0 = time.perf_counter()
            a, b, c = decode_layers(ps)
            verify_signature(pk, a, b, c)
            t1 = time.perf_counter()
            met2_latencies.append((t1 - t0) * 1000.0)

        met2_p95 = float(np.percentile(met2_latencies, 95))
        met2_pass = met2_p95 <= 300.0
        results["MET-2 p95<=300ms"] = (met2_p95, 300.0, met2_pass)

        # --- MET-3: Tamper detection ---
        rng3 = random.Random(33)
        met3_n = 50
        met3_detected = 0

        for i in range(met3_n):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(50 + rng3.randint(0, 30))
            layer_b = _sample_layer_b(60 + rng3.randint(0, 68))
            layer_c = sign_layers(priv, layer_a, layer_b)
            tamper_type = i % 6

            if tamper_type == 0:
                pos = rng3.randint(0, len(layer_a) - 1)
                a_list = list(layer_a)
                a_list[pos] = "Z" if a_list[pos] != "Z" else "Y"
                result = verify_signature(pub, "".join(a_list), layer_b, layer_c)
            elif tamper_type == 1:
                pos = rng3.randint(0, len(layer_b) - 1)
                b_arr = bytearray(layer_b)
                b_arr[pos] ^= 0xFF
                result = verify_signature(pub, layer_a, bytes(b_arr), layer_c)
            elif tamper_type == 2:
                pos = rng3.randint(0, len(layer_c) - 1)
                c_arr = bytearray(layer_c)
                c_arr[pos] ^= 0xFF
                result = verify_signature(pub, layer_a, layer_b, bytes(c_arr))
            elif tamper_type == 3:
                wp, _ = generate_keypair()
                wc = sign_layers(wp, layer_a, layer_b)
                result = verify_signature(pub, layer_a, layer_b, wc)
            elif tamper_type == 4:
                result = verify_signature(pub, layer_a, layer_b, layer_c[:-16])
            else:
                result = verify_signature(pub, layer_a, layer_b, bytes(64))

            if result is False:
                met3_detected += 1

        met3_rate = met3_detected / met3_n
        met3_pass = met3_rate >= 0.99
        results["MET-3 Tamper>=99%"] = (met3_rate, 0.99, met3_pass)

        # --- MET-4: Routing accuracy ---
        rng4 = random.Random(44)
        met4_total = 25
        met4_correct = 0

        access_levels = ["public", "authenticated", "verified-valid", "verified-invalid"]
        for i in range(met4_total):
            priv, pub = generate_keypair()
            layer_a = _sample_layer_a(55 + rng4.randint(0, 25))
            layer_b = _sample_layer_b(70 + rng4.randint(0, 30))
            layer_c = sign_layers(priv, layer_a, layer_b)
            payload_str = encode_layers(layer_a, layer_b, layer_c)

            tier = i % 4

            if tier == 0:
                resolved = resolve(payload_str, "public", None)
                ok = (resolved.layer_a == layer_a and resolved.layer_b is None
                      and resolved.layer_c is None and not resolved.verified)
            elif tier == 1:
                resolved = resolve(payload_str, "authenticated", None)
                ok = (resolved.layer_a == layer_a and resolved.layer_b == layer_b
                      and resolved.layer_c is None and not resolved.verified)
            elif tier == 2:
                resolved = resolve(payload_str, "verified", pub)
                ok = (resolved.layer_a == layer_a and resolved.layer_b == layer_b
                      and resolved.layer_c == layer_c and resolved.verified)
            else:  # verified with wrong key
                _, wrong_pub = generate_keypair()
                resolved = resolve(payload_str, "verified", wrong_pub)
                ok = (resolved.layer_a == layer_a and resolved.layer_b is None
                      and resolved.layer_c is None and not resolved.verified)

            if ok:
                met4_correct += 1

        met4_acc = met4_correct / met4_total
        met4_pass = met4_acc >= 0.98
        results["MET-4 Route>=98%"] = (met4_acc, 0.98, met4_pass)

        # --- Summary table ---
        print("\n[B-EXP5] AC Gate Summary")
        print(f"  {'Metric':<20}  {'Target':>8}  {'Actual':>8}  {'Result':>6}")
        print(f"  {'-'*20}  {'-'*8}  {'-'*8}  {'-'*6}")
        all_pass = True
        for metric, (actual, target, passed) in results.items():
            label = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            if "ms" in metric:
                print(f"  {metric:<20}  {target:>7.0f}ms  {actual:>7.2f}ms  {label:>6}")
            else:
                print(f"  {metric:<20}  {target:>7.0%}  {actual:>7.1%}  {label:>6}")

        failed = [m for m, (_, _, p) in results.items() if not p]
        assert all_pass, (
            f"[B-EXP5] AC Gate FAIL — metrics not meeting targets: {failed}"
        )
        print("\n[B-EXP5] test_all_metrics_pass — ALL METRICS PASS")
