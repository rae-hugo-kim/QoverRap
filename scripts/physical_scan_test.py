#!/usr/bin/env python3
"""Physical device QR scan test — semi-automated via adb clipboard.

Workflow:
  1. QR display server shows images on a monitor (→ key to advance)
  2. Device camera recognizes QR, user taps "복사" (copy)
  3. User presses Enter in this script
  4. Script reads clipboard via adb (paste into a text field)
  5. Compares with manifest.json to verify correctness

Usage:
  # Terminal 1: display server (interval=0 = manual advance)
  .venv/bin/python scripts/qr-display-server.py --image-dir test-qr-images --interval 0

  # Terminal 2: this script
  .venv/bin/python scripts/physical_scan_test.py --device 10.39.160.124:35723

Prerequisites:
  - adb connected device
  - Camera app open, pointing at monitor showing QR
  - QR images generated via generate_test_qrs.py
"""
import argparse
import base64
import json
import pathlib
import struct
import subprocess
import sys
import time

DELIMITER = "\n---QWR---\n"


def decode_layers(payload: str) -> tuple[str, bytes, bytes]:
    """Decode a QR payload into (layer_a, layer_b, layer_c)."""
    if DELIMITER not in payload:
        return (payload, b"", b"")
    layer_a, b64_trailer = payload.split(DELIMITER, maxsplit=1)
    frame = base64.b64decode(b64_trailer)
    version, b_len, c_len = struct.unpack('>BHH', frame[:5])
    if version != 0x01:
        raise ValueError(f"Unsupported version: {version}")
    layer_b = frame[5: 5 + b_len]
    layer_c = frame[5 + b_len: 5 + b_len + c_len]
    return (layer_a, layer_b, layer_c)


def adb_read_clipboard(device: str) -> str:
    """Read clipboard text from Android device via adb.

    Strategy: open a settings search field, paste, read via uiautomator,
    then clean up. Works on Android 10+ without root.
    """
    adb = ["adb", "-s", device]

    # 1. Open browser with a data URI that has an input field
    #    This is the most universal approach - works on any Android device
    html = "data:text/html,<input id=p autofocus style='width:100%;font-size:30px'>"
    subprocess.run(
        adb + ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", html],
        capture_output=True, timeout=5,
    )
    time.sleep(1.5)

    # 2. Tap the input field area (top center of screen) and paste
    #    First get screen size
    result = subprocess.run(
        adb + ["shell", "wm", "size"],
        capture_output=True, text=True, timeout=5,
    )
    # Parse "Physical size: 1600x2560"
    size_str = result.stdout.strip().split(":")[-1].strip()
    w, h = size_str.split("x")
    tap_x, tap_y = int(w) // 2, int(h) // 6  # top area

    subprocess.run(adb + ["shell", "input", "tap", str(tap_x), str(tap_y)],
                   capture_output=True, timeout=5)
    time.sleep(0.5)

    # 3. Long press to get paste option, or use keyevent PASTE
    subprocess.run(adb + ["shell", "input", "keyevent", "279"],  # KEYCODE_PASTE
                   capture_output=True, timeout=5)
    time.sleep(0.5)

    # 4. Select all + copy to ensure we get full text
    subprocess.run(adb + ["shell", "input", "keyevent", "256"],  # KEYCODE_CTRL_LEFT (modifier)
                   capture_output=True, timeout=5)

    # 5. Read the text via uiautomator dump
    subprocess.run(
        adb + ["shell", "uiautomator", "dump", "/sdcard/_clip.xml"],
        capture_output=True, timeout=10,
    )
    result = subprocess.run(
        adb + ["shell", "cat", "/sdcard/_clip.xml"],
        capture_output=True, text=True, timeout=5,
    )

    # 6. Parse the input field text
    import re
    texts = re.findall(r'text="([^"]*)"', result.stdout)
    clipboard_text = ""
    for t in texts:
        if "QoverwRap" in t or "---QWR---" in t or len(t) > 50:
            clipboard_text = t
            break

    # 7. Clean up - go back to camera
    subprocess.run(adb + ["shell", "input", "keyevent", "4"],  # BACK
                   capture_output=True, timeout=5)
    subprocess.run(adb + ["shell", "input", "keyevent", "4"],  # BACK again
                   capture_output=True, timeout=5)
    subprocess.run(adb + ["shell", "rm", "/sdcard/_clip.xml"],
                   capture_output=True, timeout=5)

    return clipboard_text


def adb_read_clipboard_simple(device: str) -> str:
    """Simpler clipboard read: broadcast to get clipboard via logcat.

    Fallback: just use the broadcast receiver approach.
    """
    adb = ["adb", "-s", device]

    # Use am broadcast with a clipboard reader intent
    # Actually, simplest: open a shell and use service call
    result = subprocess.run(
        adb + ["shell", "service", "call", "clipboard", "2", "s16", "com.android.shell"],
        capture_output=True, text=True, timeout=5,
    )

    # Parse the Parcel output - it's in 32-bit words, UTF-16LE with swapped pairs
    import re
    lines = result.stdout.strip().split('\n')
    hex_words = []
    for line in lines:
        parts = re.findall(r'[0-9a-fA-F]{8}', line)
        if len(parts) > 1:
            hex_words.extend(parts[1:])  # skip offset

    if not hex_words:
        return ""

    # Build raw bytes - each 32-bit word needs byte swapping for UTF-16
    raw = b""
    for w in hex_words:
        b = bytes.fromhex(w)
        # Swap each pair of UTF-16 code units: ABCD -> CDAB
        raw += b[2:4] + b[0:2]

    # Skip header (first word is status, second is string length)
    # Find the actual string start after the length prefix
    try:
        text = raw[4:].decode("utf-16-le", errors="ignore").rstrip("\x00").strip()
        # Clean up any non-printable characters
        text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
        return text
    except Exception:
        return ""


def run_test(device: str, manifest_path: pathlib.Path, output_path: pathlib.Path) -> dict:
    """Run semi-automated physical scan test."""

    with open(manifest_path) as f:
        manifest = json.load(f)

    images = manifest["images"]
    total = len(images)
    results = []

    print(f"\n{'='*60}")
    print(f" Physical QR Scan Test (반자동 / Semi-automated)")
    print(f" Device: {device}")
    print(f" QR count: {total}")
    print(f"{'='*60}")
    print()
    print(" 절차 / Procedure:")
    print("   1. 패드 카메라로 모니터 QR을 스캔")
    print("   2. 인식되면 '복사' 버튼 탭")
    print("   3. 이 터미널에서 Enter")
    print("   4. 브라우저에서 → 키로 다음 QR")
    print("   5. 반복")
    print()

    for i, entry in enumerate(images):
        qr_id = entry["filename"]
        expected_a = entry["layer_a"]
        expected_b_hex = entry.get("layer_b_hex", "")
        expected_c_hex = entry.get("layer_c_hex", "")
        expected_b = bytes.fromhex(expected_b_hex) if expected_b_hex else b""
        expected_c = bytes.fromhex(expected_c_hex) if expected_c_hex else b""

        print(f"[{i+1}/{total}] {qr_id}")
        print(f"  Expected A: {expected_a[:70]}...")

        input(f"  >>> 패드에서 '복사' 누른 후 Enter: ")

        # Read clipboard
        print(f"  클립보드 읽는 중...")
        clipboard = adb_read_clipboard_simple(device)

        if not clipboard:
            print(f"  Result: FAIL (클립보드 비어있음)")
            results.append({
                "qr_id": qr_id, "success": False, "reason": "empty_clipboard",
                "layer_a_match": False, "layer_b_match": False, "layer_c_match": False,
            })
        else:
            try:
                got_a, got_b, got_c = decode_layers(clipboard)
                a_match = got_a.strip() == expected_a.strip()
                b_match = got_b == expected_b
                c_match = got_c == expected_c
                success = a_match and b_match and c_match

                status = "PASS ✓" if success else "FAIL ✗"
                print(f"  Got A: {got_a[:70]}...")
                print(f"  A={a_match} B={b_match} C={c_match}")
                print(f"  Result: {status}")

                results.append({
                    "qr_id": qr_id, "success": success,
                    "reason": "ok" if success else "mismatch",
                    "layer_a_match": a_match, "layer_b_match": b_match,
                    "layer_c_match": c_match,
                    "recognized_a": got_a[:100],
                })
            except Exception as e:
                print(f"  Result: FAIL (디코딩 오류: {e})")
                results.append({
                    "qr_id": qr_id, "success": False,
                    "reason": f"decode_error: {e}",
                    "layer_a_match": False, "layer_b_match": False,
                    "layer_c_match": False,
                })

        if i < total - 1:
            print(f"  → 브라우저에서 → 키로 다음 QR 넘기세요")
        print()

    # Summary
    passed = sum(1 for r in results if r["success"])
    rate = passed / total if total > 0 else 0
    met1_pass = rate >= 0.95

    print(f"{'='*60}")
    print(f" SUMMARY")
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success Rate: {rate:.1%}")
    print(f"  MET-1 (>= 95%): {'PASS' if met1_pass else 'FAIL'}")
    print(f"{'='*60}")

    report = {
        "device": device,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "success_rate": rate,
        "met1_pass": met1_pass,
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: {output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Physical QR scan test (semi-automated)")
    parser.add_argument("--device", required=True, help="ADB device ID")
    parser.add_argument("--manifest", default="test-qr-images/manifest.json")
    parser.add_argument("--output", default="test-results/physical-scan-results.json")
    args = parser.parse_args()

    run_test(
        device=args.device,
        manifest_path=pathlib.Path(args.manifest),
        output_path=pathlib.Path(args.output),
    )


if __name__ == "__main__":
    main()
