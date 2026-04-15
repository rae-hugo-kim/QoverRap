#!/usr/bin/env python3
"""generate_test_qrs.py — Generate QR test images for physical device testing.

Produces batches of 3-layer overlapping QR images following:
- A-ENV1 lighting conditions (indoor general / low-light)
- MET-1 200-trial scan protocol (95%+ success rate target)

Encoding scheme: Plain-Text-Prefix with Base64 Trailer
    <Layer A UTF-8 text>\\n---QWR---\\n<base64(header + B_payload + C_payload)>

Binary header (inside base64 blob):
    Offset  Size  Field
    0       1     version   (0x01)
    1       2     b_len     (uint16 big-endian)
    3       2     c_len     (uint16 big-endian)
    5       b_len B_payload
    5+b_len c_len C_payload
"""

__version__ = "0.1.0"

import argparse
import base64
import json
import os
import pathlib
import struct
import sys
from datetime import datetime, timezone
from typing import NamedTuple

try:
    import qrcode
    import qrcode.constants as qrc
    from PIL import Image as PILImage
    from PIL import ImageDraw, ImageFont
except ImportError as exc:
    sys.exit(f"Missing dependency: {exc}\nHint: pip install qrcode[pil] Pillow")


# ---------------------------------------------------------------------------
# Encoding helpers (copied from tests/feasibility/test_a_hyp.py)
# ---------------------------------------------------------------------------

DELIMITER = "\n---QWR---\n"

_ECC_MAP = {
    "L": qrc.ERROR_CORRECT_L,
    "M": qrc.ERROR_CORRECT_M,
    "Q": qrc.ERROR_CORRECT_Q,
    "H": qrc.ERROR_CORRECT_H,
}


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


def _make_qr(
    data: str,
    *,
    ecc=qrc.ERROR_CORRECT_M,
    box_size: int = 10,
) -> PILImage.Image:
    """Generate a QR code image. Returns a PIL RGB image."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ecc,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _qr_version(data: str, ecc=qrc.ERROR_CORRECT_M) -> int:
    """Return the auto-selected QR version for the given payload."""
    qr = qrcode.QRCode(version=None, error_correction=ecc, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.version


# ---------------------------------------------------------------------------
# Payload size presets
# ---------------------------------------------------------------------------

class SizePreset(NamedTuple):
    name: str
    a_len: int   # Layer A text bytes
    b_len: int   # Layer B binary bytes
    c_len: int   # Layer C binary bytes


PRESETS: dict[str, SizePreset] = {
    "small":  SizePreset("small",  a_len=50,  b_len=32,  c_len=32),
    "medium": SizePreset("medium", a_len=80,  b_len=96,  c_len=64),
    "large":  SizePreset("large",  a_len=100, b_len=256, c_len=128),
}


def _build_layer_a(seq_id: int, a_len: int) -> str:
    """Build a unique Layer A text with incrementing ID."""
    id_str = f"{seq_id:03d}"
    prefix = f"QoverwRap/test/{id_str} — https://example.com/v1?id={id_str}"
    if len(prefix) >= a_len:
        return prefix[:a_len]
    # Pad to exact length with spaces
    return prefix + " " * (a_len - len(prefix))


def _build_layer_b(seq_id: int, b_len: int) -> bytes:
    """Build Layer B binary payload (JSON-like context, truncated/padded)."""
    stub = f'{{"issuer":"QoverwRap","id":{seq_id},"nonce":"'.encode()
    pad = b"B" * max(0, b_len - len(stub) - 2)
    raw = (stub + pad + b'"}')[:b_len]
    # Pad with null bytes if stub alone is shorter than b_len
    if len(raw) < b_len:
        raw = raw + b"\x00" * (b_len - len(raw))
    return raw


def _build_layer_c(seq_id: int, c_len: int) -> bytes:
    """Build Layer C binary payload (mock signature, deterministic)."""
    return bytes([(seq_id + i) % 256 for i in range(c_len)])


# ---------------------------------------------------------------------------
# Image sizing
# ---------------------------------------------------------------------------

def _box_size_for_target(payload: str, ecc, target_px: int) -> int:
    """Compute box_size so the QR image is approximately target_px wide."""
    qr = qrcode.QRCode(version=None, error_correction=ecc, box_size=1, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    # modules = (version * 4 + 17), plus 2*border modules
    modules = (qr.version * 4 + 17) + 2 * qr.border
    box_size = max(1, target_px // modules)
    return box_size


# ---------------------------------------------------------------------------
# Grid / PDF output
# ---------------------------------------------------------------------------

def _compose_grid(
    images: list[tuple[PILImage.Image, str]],
    cols: int = 4,
    padding: int = 20,
    label_height: int = 30,
) -> PILImage.Image:
    """Compose a grid of (image, label) pairs into a single PIL image."""
    if not images:
        raise ValueError("No images to compose")

    cell_w = max(img.width for img, _ in images) + padding
    cell_h = max(img.height for img, _ in images) + label_height + padding

    rows = (len(images) + cols - 1) // cols
    grid_w = cols * cell_w
    grid_h = rows * cell_h

    grid = PILImage.new("RGB", (grid_w, grid_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(grid)

    # Use default font — avoids font-file dependency
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (IOError, OSError):
        font = ImageFont.load_default()

    for idx, (img, label) in enumerate(images):
        row = idx // cols
        col = idx % cols
        x = col * cell_w + padding // 2
        y = row * cell_h + padding // 2
        grid.paste(img, (x, y))
        draw.text((x, y + img.height + 4), label, fill=(0, 0, 0), font=font)

    return grid


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def _build_manifest(entries: list[dict], total: int) -> dict:
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "script_version": __version__,
            "total_count": total,
        },
        "images": entries,
    }


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate(args: argparse.Namespace) -> None:
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ecc_const = _ECC_MAP[args.ecc.upper()]
    size_names = [s.strip() for s in args.sizes.split(",")]

    # Validate preset names
    unknown = [s for s in size_names if s not in PRESETS]
    if unknown:
        sys.exit(f"Unknown size preset(s): {unknown}. Choose from: {list(PRESETS)}")

    count = args.count
    target_px = args.print_size
    fmt = args.format.lower()
    if fmt not in ("png", "pdf"):
        sys.exit("--format must be 'png' or 'pdf'")

    print(f"Generating {count} QR image(s) -> {output_dir}  [ecc={args.ecc}, sizes={size_names}]")

    manifest_entries: list[dict] = []
    grid_images: list[tuple[PILImage.Image, str]] = []  # for pdf/grid mode

    for i in range(count):
        seq_id = i + 1
        preset_name = size_names[i % len(size_names)]
        preset = PRESETS[preset_name]

        layer_a = _build_layer_a(seq_id, preset.a_len)
        layer_b = _build_layer_b(seq_id, preset.b_len)
        layer_c = _build_layer_c(seq_id, preset.c_len)

        payload = encode_layers(layer_a, layer_b, layer_c)
        payload_bytes = len(payload.encode("utf-8"))

        # Compute box size to approximate print_size
        box_size = _box_size_for_target(payload, ecc_const, target_px)
        img = _make_qr(payload, ecc=ecc_const, box_size=box_size)

        # Resize to exact target_px if needed (nearest-neighbor to keep crisp)
        if img.width != target_px:
            img = img.resize((target_px, target_px), PILImage.NEAREST)

        version = _qr_version(payload, ecc_const)
        filename = f"qr_{seq_id:03d}_{preset_name}.png"
        img_path = output_dir / filename
        img.save(str(img_path))

        label = f"#{seq_id:03d} {preset_name}"
        grid_images.append((img, label))

        entry = {
            "filename": filename,
            "layer_a": layer_a,
            "layer_b_hex": layer_b.hex(),
            "layer_c_hex": layer_c.hex(),
            "ecc": args.ecc.upper(),
            "qr_version": version,
            "payload_size_bytes": payload_bytes,
            "size_preset": preset_name,
        }
        manifest_entries.append(entry)
        print(f"  [{seq_id:03d}/{count}] {filename}  version={version}  payload={payload_bytes}B")

    # Write manifest
    manifest = _build_manifest(manifest_entries, count)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest -> {manifest_path}")

    # PDF / grid output
    if fmt == "pdf":
        grid = _compose_grid(grid_images, cols=4, padding=20, label_height=30)
        # Pillow can save single-page PDF directly
        grid_path = output_dir / "qr_grid.pdf"
        try:
            grid.save(str(grid_path), "PDF", resolution=150)
            print(f"PDF grid -> {grid_path}")
        except Exception as exc:
            # Fallback: save as PNG grid
            grid_path = output_dir / "qr_grid.png"
            grid.save(str(grid_path))
            print(f"PDF save failed ({exc}); saved PNG grid -> {grid_path}")
    else:
        # Always produce a PNG grid for reference
        if len(grid_images) > 1:
            grid = _compose_grid(grid_images, cols=4, padding=20, label_height=30)
            grid_path = output_dir / "qr_grid.png"
            grid.save(str(grid_path))
            print(f"PNG grid -> {grid_path}")

    print(f"\nDone. {count} QR image(s) written to {output_dir.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate 3-layer overlapping QR test images for physical device testing "
            "(A-ENV1 lighting conditions, MET-1 200-trial scan protocol)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default="test-qr-images/",
        help="Directory to write QR images and manifest.json",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of QR images to generate",
    )
    parser.add_argument(
        "--ecc",
        default="M",
        choices=["L", "M", "Q", "H"],
        help="QR error-correction level",
    )
    parser.add_argument(
        "--sizes",
        default="small,medium,large",
        help=(
            "Comma-separated payload size presets to cycle through. "
            "Choices: small (A=50B B=32B C=32B), "
            "medium (A=80B B=96B C=64B), "
            "large (A=100B B=256B C=128B)"
        ),
    )
    parser.add_argument(
        "--print-size",
        type=int,
        default=300,
        help="Target QR image pixel size (width=height) for printing",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "pdf"],
        help="Output format: 'png' saves individual PNGs + grid; 'pdf' saves a grid PDF",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    generate(args)


if __name__ == "__main__":
    main()
