#!/usr/bin/env python3
"""generate_density_qrs.py — Generate QR codes at forced specific versions (v5–v40).

Tests the density/resolution limits of real phone cameras by generating the same
3-layer payload structure at escalating QR versions, not just payloads that happen
to land on those versions.

Encoding scheme: Plain-Text-Prefix with Base64 Trailer
    <Layer A UTF-8 text>\\n---QWR---\\n<base64(header + B_payload + C_payload)>

Binary header (inside base64 blob):
    Offset  Size  Field
    0       1     version   (0x01)
    1       2     b_len     (uint16 big-endian)
    3       2     c_len     (uint16 big-endian)
    5       b_len B_payload
    5+b_len c_len C_payload

Test matrix: 8 versions × 3 display sizes × 2 ECC levels = 48 images.
"""

__version__ = "0.1.0"

import argparse
import base64
import json
import pathlib
import random
import struct
import sys
from datetime import datetime, timezone
from typing import NamedTuple

try:
    import qrcode
    import qrcode.constants as qrc
    import qrcode.exceptions
    from PIL import Image as PILImage
except ImportError as exc:
    sys.exit(f"Missing dependency: {exc}\nHint: pip install qrcode[pil] Pillow")


# ---------------------------------------------------------------------------
# Encoding helpers — same scheme as generate_test_qrs.py
# ---------------------------------------------------------------------------

DELIMITER = "\n---QWR---\n"

_ECC_MAP = {
    "L": qrc.ERROR_CORRECT_L,
    "M": qrc.ERROR_CORRECT_M,
    "Q": qrc.ERROR_CORRECT_Q,
    "H": qrc.ERROR_CORRECT_H,
}

# QR version byte-mode capacities per ECC level (data codewords * 1 for byte mode).
# Source: ISO/IEC 18004 Table 9.  These are the *total byte capacity* of the
# data region; the qrcode library enforces these limits internally.
#
# Keyed as (version, ecc_char) -> bytes.  Only the versions we care about:
_VERSION_CAPACITY: dict[tuple[int, str], int] = {
    (5,  "L"): 108, (5,  "M"): 86,  (5,  "Q"): 62,  (5,  "H"): 48,
    (10, "L"): 321, (10, "M"): 251, (10, "Q"): 177, (10, "H"): 139,
    (15, "L"): 614, (15, "M"): 480, (15, "Q"): 346, (15, "H"): 272,
    (20, "L"): 1013,(20, "M"): 787, (20, "Q"): 573, (20, "H"): 445,
    (25, "L"): 1489,(25, "M"): 1171,(25, "Q"): 857, (25, "H"): 669,
    (30, "L"): 1994,(30, "M"): 1591,(30, "Q"): 1171,(30, "H"): 911,
    (35, "L"): 2566,(35, "M"): 2055,(35, "Q"): 1511,(35, "H"): 1171,
    (40, "L"): 2956,(40, "M"): 2331,(40, "Q"): 1725,(40, "H"): 1367,
}

_FILL_RATIO = 0.95  # fill to 95 % of capacity so we land solidly in the target version


def encode_layers(layer_a: str, layer_b: bytes = b"", layer_c: bytes = b"") -> str:
    """Encode A/B/C into a single QR payload string."""
    if DELIMITER.strip() in layer_a:
        raise ValueError("Layer A must not contain the delimiter")
    if not layer_b and not layer_c:
        return layer_a
    header = struct.pack(">BHH", 0x01, len(layer_b), len(layer_c))
    frame = header + layer_b + layer_c
    trailer = base64.b64encode(frame).decode("ascii")
    return layer_a + DELIMITER + trailer


# ---------------------------------------------------------------------------
# Deterministic fixed B/C layers (constant across all versions)
# ---------------------------------------------------------------------------

_RNG = random.Random(42)

_LAYER_B: bytes = bytes(_RNG.getrandbits(8) for _ in range(32))
_LAYER_C: bytes = bytes(_RNG.getrandbits(8) for _ in range(16))

# Compute the fixed trailer overhead once:
#   header(5) + B(32) + C(16) = 53 bytes → base64 → 72 chars
#   DELIMITER = 12 chars
#   Total overhead in the payload string: 12 + 72 = 84 chars (= 84 bytes, ASCII only)
_TRAILER_OVERHEAD: int = len(encode_layers("", _LAYER_B, _LAYER_C).lstrip())


# ---------------------------------------------------------------------------
# Payload calibration
# ---------------------------------------------------------------------------

class LayerSpec(NamedTuple):
    layer_a: str
    payload: str
    payload_bytes: int
    actual_version: int


def _trailer_bytes() -> str:
    """Return only the delimiter+base64 trailer (for overhead accounting)."""
    return DELIMITER + base64.b64encode(
        struct.pack(">BHH", 0x01, len(_LAYER_B), len(_LAYER_C))
        + _LAYER_B + _LAYER_C
    ).decode("ascii")


def _build_layer_a(version: int, a_text_len: int) -> str:
    """Build Layer A with a fixed prefix followed by 'A' padding."""
    prefix = f"QoverwRap/density-test/v{version:02d} #"
    # Reserve 4 chars for a 4-digit serial that makes each image unique
    serial_len = 4
    pad_len = max(0, a_text_len - len(prefix) - serial_len)
    serial = f"{version:04d}"
    return prefix + serial + "A" * pad_len


def calibrate_payload(target_version: int, ecc_char: str) -> LayerSpec:
    """Calibrate a Layer A length so the QR lands on (or as close as possible to) target_version.

    Strategy:
    1. Compute target_bytes = capacity(version, ecc) * FILL_RATIO.
    2. Subtract fixed trailer overhead to get the Layer-A budget.
    3. If trailer alone already exceeds the version capacity, use a minimal
       Layer A (just the identification prefix) and let the QR library
       auto-select the lowest version that fits — the manifest records the
       actual_version so callers can detect the mismatch.
    4. Otherwise build the padded Layer A, verify with fit=False, and fall
       back to fit=True on DataOverflowError (trims 8 bytes at a time).
    """
    ecc_key = (target_version, ecc_char)
    if ecc_key not in _VERSION_CAPACITY:
        raise ValueError(f"No capacity data for version={target_version} ecc={ecc_char}")

    capacity = _VERSION_CAPACITY[ecc_key]
    target_bytes = int(capacity * _FILL_RATIO)

    trailer = _trailer_bytes()
    trailer_len = len(trailer.encode("utf-8"))

    # When trailer alone already exceeds the version capacity we cannot
    # fabricate a payload that genuinely fits in target_version.  Use the
    # minimal Layer A (identification prefix only) and let fit=True choose
    # the actual version.
    if trailer_len >= capacity:
        layer_a = f"QoverwRap/density-test/v{target_version:02d} #min"
        payload = layer_a + trailer
        qr = qrcode.QRCode(
            version=None,
            error_correction=_ECC_MAP[ecc_char],
            box_size=1,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        return LayerSpec(
            layer_a=layer_a,
            payload=payload,
            payload_bytes=len(payload.encode("utf-8")),
            actual_version=qr.version,
        )

    # Happy path: we have room to pad Layer A up to the fill target.
    a_budget = max(1, target_bytes - trailer_len)
    layer_a = _build_layer_a(target_version, a_budget)
    payload = layer_a + trailer

    # Try strict version enforcement first (fit=False).
    try:
        qr = qrcode.QRCode(
            version=target_version,
            error_correction=_ECC_MAP[ecc_char],
            box_size=1,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=False)
        actual_version = qr.version
    except qrcode.exceptions.DataOverflowError:
        # Trim Layer A 8 bytes at a time until it fits, then use fit=True.
        while a_budget > 1:
            a_budget = max(1, a_budget - 8)
            layer_a = _build_layer_a(target_version, a_budget)
            payload = layer_a + trailer
            try:
                qr = qrcode.QRCode(
                    version=target_version,
                    error_correction=_ECC_MAP[ecc_char],
                    box_size=1,
                    border=4,
                )
                qr.add_data(payload)
                qr.make(fit=True)
                break
            except qrcode.exceptions.DataOverflowError:
                continue
        actual_version = qr.version

    return LayerSpec(
        layer_a=layer_a,
        payload=payload,
        payload_bytes=len(payload.encode("utf-8")),
        actual_version=actual_version,
    )


# ---------------------------------------------------------------------------
# QR image rendering
# ---------------------------------------------------------------------------

def _render_qr(
    payload: str,
    target_version: int,
    ecc_char: str,
    display_px: int,
) -> PILImage.Image:
    """Render a QR code at exactly display_px × display_px (NEAREST resize)."""
    ecc_const = _ECC_MAP[ecc_char]
    border = 4
    modules = target_version * 4 + 17  # module count without border
    total_modules = modules + 2 * border  # including quiet zone

    # Choose box_size so the raw image is close to display_px, then resize
    box_size = max(1, display_px // total_modules)

    qr = qrcode.QRCode(
        version=target_version,
        error_correction=ecc_const,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Resize to exact pixel size using NEAREST to preserve sharp module edges
    if img.width != display_px or img.height != display_px:
        img = img.resize((display_px, display_px), PILImage.NEAREST)

    return img


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _module_px(version: int, display_px: int, border: int = 4) -> float:
    """Approximate pixels per module: display_px / total_modules."""
    total_modules = version * 4 + 17 + 2 * border
    return round(display_px / total_modules, 2)


def _build_manifest(entries: list[dict]) -> dict:
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "script_version": __version__,
            "test_type": "density_limit",
            "purpose": "Find max QR version readable by real cameras",
            "total_images": len(entries),
        },
        "test_matrix": entries,
    }


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate(args: argparse.Namespace) -> None:
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    versions = [int(v.strip()) for v in args.versions.split(",")]
    sizes = [int(s.strip()) for s in args.sizes.split(",")]
    ecc_chars = [e.strip().upper() for e in args.ecc.split(",")]

    # Validate
    bad_ecc = [e for e in ecc_chars if e not in _ECC_MAP]
    if bad_ecc:
        sys.exit(f"Unknown ECC level(s): {bad_ecc}. Choose from: L M Q H")
    bad_ver = [v for v in versions if not (1 <= v <= 40)]
    if bad_ver:
        sys.exit(f"QR versions must be 1–40, got: {bad_ver}")

    total = len(versions) * len(sizes) * len(ecc_chars)
    print(
        f"Generating {total} QR image(s) -> {output_dir}  "
        f"[versions={versions}, sizes={sizes}px, ecc={ecc_chars}]"
    )

    manifest_entries: list[dict] = []
    done = 0

    for version in versions:
        for ecc_char in ecc_chars:
            # Calibrate payload once per (version, ecc) — reuse for all sizes
            try:
                spec = calibrate_payload(version, ecc_char)
            except ValueError as exc:
                print(f"  [SKIP] v{version:02d} ecc={ecc_char}: {exc}")
                continue

            for display_px in sizes:
                done += 1
                filename = f"v{version:02d}_{display_px}px_{ecc_char}.png"
                img = _render_qr(spec.payload, version, ecc_char, display_px)
                img_path = output_dir / filename
                img.save(str(img_path))

                mod_px = _module_px(version, display_px)
                entry = {
                    "filename": filename,
                    "qr_version": version,
                    "actual_version": spec.actual_version,
                    "display_px": display_px,
                    "ecc": ecc_char,
                    "modules": version * 4 + 17,
                    "module_px": mod_px,
                    "payload_bytes": spec.payload_bytes,
                    "layer_a": spec.layer_a,
                    "layer_b_hex": _LAYER_B.hex(),
                    "layer_c_hex": _LAYER_C.hex(),
                }
                manifest_entries.append(entry)

                version_mismatch = (
                    f"  [WARN] actual version {spec.actual_version} != target {version}"
                    if spec.actual_version != version
                    else ""
                )
                print(
                    f"  [{done:02d}/{total}] {filename}"
                    f"  ver={spec.actual_version}  payload={spec.payload_bytes}B"
                    f"  module_px={mod_px}"
                    + version_mismatch
                )

    manifest = _build_manifest(manifest_entries)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest -> {manifest_path}")
    print(f"\nDone. {done} QR image(s) written to {output_dir.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate 3-layer QR codes at forced specific versions (v5–v40) "
            "to test the density/resolution limits of real phone cameras."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default="test-qr-density",
        help="Directory to write QR images and manifest.json",
    )
    parser.add_argument(
        "--versions",
        default="5,10,15,20,25,30,35,40",
        help="Comma-separated QR versions to test (1–40)",
    )
    parser.add_argument(
        "--sizes",
        default="200,400,600",
        help="Comma-separated display pixel sizes (image width=height in px)",
    )
    parser.add_argument(
        "--ecc",
        default="M,H",
        help="Comma-separated ECC levels to test (L, M, Q, H)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    generate(args)


if __name__ == "__main__":
    main()
