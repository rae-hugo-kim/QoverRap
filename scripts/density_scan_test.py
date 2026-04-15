#!/usr/bin/env python3
"""density_scan_test.py — Manual QR density limit test recorder.

User displays QR images on a monitor (via qr-display-server.py) and scans each
with a real phone/tablet camera, recording pass/fail results. The script then
calculates the maximum readable QR version for each (ECC, display_px) pair.

Question answered: "QR 버전이 올라갈 때 실제 카메라에서 몇 버전까지 읽히는가?"
(At which QR version does real camera recognition break down?)

사용법 (Usage):
    # Terminal 1: display server (interval=0 = manual advance via → key)
    python scripts/qr-display-server.py --image-dir test-qr-density --interval 0

    # Terminal 2: this script
    python scripts/density_scan_test.py --device "Galaxy Tab S9 Ultra"

의존성: Python 표준 라이브러리만 사용 (stdlib only — no external deps)
"""

__version__ = "0.1.0"

import argparse
import json
import pathlib
import signal
import sys
import urllib.request
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# QR geometry helper
# ---------------------------------------------------------------------------

def _module_px(qr_version: int, display_px: int) -> float:
    """Return pixels-per-module for the given version and display size.

    QR matrix size = version * 4 + 17 modules (the spec 'modules' field).
    The quiet-zone border is part of the image padding, not the matrix count
    used for per-module pixel density, so it is not included here.
    """
    modules = qr_version * 4 + 17
    return round(display_px / modules, 2)


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

def _load_manifest(path: pathlib.Path) -> list[dict[str, Any]]:
    """Load and return the images list from manifest.json.

    Expected entry fields (from generate_density_qrs.py):
        filename, qr_version, display_px, ecc, modules (optional)
    """
    with open(path, encoding="utf-8") as f:
        manifest = json.load(f)

    images: list[dict[str, Any]] = manifest.get("test_matrix", manifest.get("images", []))
    if not images:
        sys.exit(f"No images found in manifest: {path}")
    return images


# ---------------------------------------------------------------------------
# Sort key: ECC (M before H) → version → display_px
# ---------------------------------------------------------------------------

_ECC_ORDER = {"M": 0, "L": 1, "Q": 2, "H": 3}


def _sort_key(entry: dict[str, Any]) -> tuple[int, int, int]:
    ecc = entry.get("ecc", "M").upper()
    return (
        _ECC_ORDER.get(ecc, 99),
        entry.get("qr_version", 0),
        entry.get("display_px", 0),
    )


# ---------------------------------------------------------------------------
# Resume: load previous results from output file
# ---------------------------------------------------------------------------

def _load_previous_results(output_path: pathlib.Path) -> dict[str, str]:
    """Return {filename: result} for already-tested entries."""
    if not output_path.exists():
        return {}
    try:
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        return {r["filename"]: r["result"] for r in data.get("results", [])}
    except (json.JSONDecodeError, KeyError):
        return {}


# ---------------------------------------------------------------------------
# Boundary analysis
# ---------------------------------------------------------------------------

def _compute_boundary(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """For each (ecc, display_px) pair, find the highest passing version.

    Returns a dict keyed by "{ECC}_{display_px}px" with:
        max_version, min_module_px, ecc, display_px
    """
    # Group by (ecc, display_px)
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for r in results:
        key = (r["ecc"].upper(), r["display_px"])
        groups.setdefault(key, []).append(r)

    boundary: dict[str, dict[str, Any]] = {}
    for (ecc, dpx), entries in sorted(groups.items()):
        passed = [e for e in entries if e["result"] == "pass"]
        if passed:
            best = max(passed, key=lambda e: e["qr_version"])
            max_ver = best["qr_version"]
            min_mpx = best["module_px"]
        else:
            max_ver = 0
            min_mpx = 0.0

        key_str = f"{ecc}_{dpx}px"
        boundary[key_str] = {
            "ecc": ecc,
            "display_px": dpx,
            "max_version": max_ver,
            "min_module_px": min_mpx,
        }
    return boundary


def _critical_metric(boundary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Find the minimum module_px across all passing boundaries."""
    passing = [v for v in boundary.values() if v["max_version"] > 0]
    if not passing:
        return {
            "min_module_px_for_reliable_scan": None,
            "note": "No passing results recorded",
        }
    min_mpx = min(v["min_module_px"] for v in passing)
    return {
        "min_module_px_for_reliable_scan": min_mpx,
        "note": "Below this px/module ratio, camera scan becomes unreliable",
    }


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------

def _print_report(
    results: list[dict[str, Any]],
    boundary: dict[str, dict[str, Any]],
    critical: dict[str, Any],
    device: str,
    timestamp: str,
) -> None:
    sep = "=" * 60

    print(f"\n{sep}")
    print(" DENSITY LIMIT TEST RESULTS")
    print(f" Device: {device}")
    print(f" Date:   {timestamp}")
    print(sep)

    # Collect distinct ECC levels and sizes, sorted
    eccs = sorted({v["ecc"] for v in boundary.values()})
    sizes_by_ecc: dict[str, list[int]] = {}
    for v in boundary.values():
        sizes_by_ecc.setdefault(v["ecc"], []).append(v["display_px"])
    for ecc in eccs:
        sizes_by_ecc[ecc] = sorted(set(sizes_by_ecc[ecc]))

    # All distinct versions, sorted
    all_versions = sorted({r["qr_version"] for r in results})
    # All sizes across all eccs
    all_sizes = sorted({r["display_px"] for r in results})

    # Build lookup: (ecc, version, display_px) -> result
    lookup: dict[tuple[str, int, int], str] = {}
    for r in results:
        lookup[(r["ecc"].upper(), r["qr_version"], r["display_px"])] = r["result"]

    # Module px lookup per (version, display_px)
    mpx_lookup: dict[tuple[int, int], float] = {}
    for r in results:
        mpx_lookup[(r["qr_version"], r["display_px"])] = r["module_px"]

    for ecc in eccs:
        sizes = sizes_by_ecc[ecc]
        print(f"\n ECC-{ecc} Results:")

        # Header row
        size_headers = "  ".join(f"{s:>6}px" for s in sizes)
        mpx_header = "  ".join(f"{'px/mod':>6}" for _ in sizes)
        print(f" {'Version':>8} | {size_headers} | {mpx_header}")
        print(f" {'-'*8}-+-{'-' * (9 * len(sizes))}-+-{'-' * (8 * len(sizes))}")

        for ver in all_versions:
            # Check if this version has any results for this ECC
            has_results = any(
                (ecc, ver, s) in lookup for s in sizes
            )
            if not has_results:
                continue

            result_cells = []
            mpx_cells = []
            for s in sizes:
                res = lookup.get((ecc, ver, s))
                if res is None:
                    result_cells.append(f"{'---':>6}  ")
                    mpx_cells.append(f"{'---':>6}  ")
                elif res == "pass":
                    result_cells.append(f"{'PASS':>6}  ")
                    mpx_cells.append(f"{mpx_lookup.get((ver, s), 0.0):>6.1f}  ")
                elif res == "fail":
                    result_cells.append(f"{'FAIL':>6}  ")
                    mpx_cells.append(f"{mpx_lookup.get((ver, s), 0.0):>6.1f}  ")
                else:
                    result_cells.append(f"{'SKIP':>6}  ")
                    mpx_cells.append(f"{'---':>6}  ")

            print(f" v{ver:>6}  | {'  '.join(c.strip() for c in result_cells)} | {'  '.join(m.strip() for m in mpx_cells)}")

    print(f"\n BOUNDARY ANALYSIS:")
    for key_str in sorted(boundary.keys()):
        b = boundary[key_str]
        if b["max_version"] > 0:
            print(
                f"  ECC-{b['ecc']} @ {b['display_px']:>4}px: "
                f"max readable version = v{b['max_version']} "
                f"({b['min_module_px']:.1f} px/module)"
            )
        else:
            print(
                f"  ECC-{b['ecc']} @ {b['display_px']:>4}px: "
                f"no passing results"
            )

    mpx_val = critical["min_module_px_for_reliable_scan"]
    if mpx_val is not None:
        print(f"\n CRITICAL METRIC: Minimum px/module for reliable scan = ~{mpx_val:.1f}px")

    print(sep)


# ---------------------------------------------------------------------------
# Interactive test loop
# ---------------------------------------------------------------------------

def run_test(
    device: str,
    manifest_path: pathlib.Path,
    output_path: pathlib.Path,
    server: str | None = "http://localhost:8765",
) -> None:
    images = _load_manifest(manifest_path)

    # Sort: ECC (M first) → version → display_px
    images = sorted(images, key=_sort_key)

    # Enrich entries with module_px if not already present from manifest
    for entry in images:
        if "module_px" not in entry:
            ver = entry.get("qr_version", 0)
            dpx = entry.get("display_px", 0)
            entry["module_px"] = _module_px(ver, dpx)

    total = len(images)

    # Resume: skip already-tested entries
    previous = _load_previous_results(output_path)
    results: list[dict[str, Any]] = []

    # Pre-populate results with previous entries in their original order
    for entry in images:
        fname = entry["filename"]
        if fname in previous:
            results.append(_make_result(entry, previous[fname]))

    print(f"\n{'='*60}")
    print(f" QR Density Limit Test (수동 / Manual)")
    print(f" Device: {device}")
    print(f" Total QR codes: {total}")
    if previous:
        print(f" Resuming: {len(previous)} already recorded, {total - len(previous)} remaining")
    print(f"{'='*60}")
    print()
    print(" 절차 / Procedure:")
    print("   1. 디스플레이 서버의 QR을 카메라로 스캔")
    print("   2. 인식되면 y, 실패하면 n, 건너뛰기 s")
    print("   3. 다음 QR은 자동 전환 (서버 연결 시) / → 키로 수동 전환")
    print()

    # Register Ctrl+C handler for graceful save
    def _handle_sigint(sig: int, frame: Any) -> None:
        print("\n\n 인터럽트 감지 / Interrupt detected — 결과 저장 중...")
        _save_and_report(results, device, output_path)
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)

    # Build display-server filename→index mapping for auto-sync
    server_url = server
    server_index_map: dict[str, int] = {}
    if server_url:
        try:
            resp = urllib.request.urlopen(f"{server_url}/api/list", timeout=2)
            data = json.loads(resp.read())
            for i, name in enumerate(data.get("images", [])):
                server_index_map[name] = i
            print(f" Display server 연결됨 / Connected: {server_url} ({len(server_index_map)} images)")
        except Exception:
            print(f" Display server 미연결 / Not connected: {server_url} (수동으로 → 키 사용)")
            server_url = None
    print()

    # Main loop
    pending = [e for e in images if e["filename"] not in previous]
    tested_count = len(previous)

    for entry in pending:
        tested_count += 1
        fname = entry["filename"]
        ver = entry.get("qr_version", 0)
        dpx = entry.get("display_px", 0)
        ecc = entry.get("ecc", "?").upper()
        modules = entry.get("modules", ver * 4 + 17)
        mpx = entry["module_px"]

        # Auto-sync display server to show the current image
        if server_url and fname in server_index_map:
            try:
                idx = server_index_map[fname]
                req = urllib.request.Request(
                    f"{server_url}/api/set?index={idx}", method="POST",
                )
                urllib.request.urlopen(req, timeout=2)
            except Exception:
                pass  # non-critical — user can still navigate manually

        print(
            f"[{tested_count}/{total}] v{ver:02d} | {dpx}px | ECC-{ecc} | "
            f"modules={modules} | ~{mpx}px/module"
        )

        result_str = ""
        while result_str not in ("y", "n", "s"):
            try:
                raw = input("  스캔 결과 [y/n/s]: ").strip().lower()
            except EOFError:
                # stdin closed — save and exit
                print("\n stdin closed — 결과 저장 중...")
                _save_and_report(results, device, output_path)
                sys.exit(0)

            if raw in ("y", "n", "s"):
                result_str = raw
            elif raw == "":
                pass  # repeat prompt
            else:
                print("  y (pass) / n (fail) / s (skip) 중 하나를 입력하세요.")

        result_word = {"y": "pass", "n": "fail", "s": "skip"}[result_str]
        results.append(_make_result(entry, result_word))

        if result_word == "pass":
            print("  PASS")
        elif result_word == "fail":
            print("  FAIL")
        else:
            print("  SKIP")

        # Running stats
        done = len(results)
        passed = sum(1 for r in results if r["result"] == "pass")
        failed = sum(1 for r in results if r["result"] == "fail")
        skipped = sum(1 for r in results if r["result"] == "skip")
        print(f"  진행 / Progress: {done}/{total}  PASS={passed} FAIL={failed} SKIP={skipped}")

        if tested_count < total:
            print("  → 브라우저에서 → 키로 다음 QR 넘기세요")
        print()

    # Final save + report
    _save_and_report(results, device, output_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(entry: dict[str, Any], result: str) -> dict[str, Any]:
    """Build a result dict from an entry and a result string."""
    ver = entry.get("qr_version", 0)
    dpx = entry.get("display_px", 0)
    ecc = entry.get("ecc", "?").upper()
    modules = entry.get("modules", ver * 4 + 17)
    mpx = entry.get("module_px", _module_px(ver, dpx))
    return {
        "filename": entry["filename"],
        "qr_version": ver,
        "display_px": dpx,
        "ecc": ecc,
        "modules": modules,
        "module_px": mpx,
        "result": result,
    }


def _save_and_report(
    results: list[dict[str, Any]],
    device: str,
    output_path: pathlib.Path,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    boundary = _compute_boundary(results)
    critical = _critical_metric(boundary)

    _print_report(results, boundary, critical, device, timestamp)

    output: dict[str, Any] = {
        "device": device,
        "timestamp": timestamp,
        "results": results,
        "boundary": boundary,
        "critical_metric": critical,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장 / Saved: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Manual QR density limit test recorder. "
            "User scans QR codes displayed on a monitor and records pass/fail. "
            "Calculates the maximum readable QR version per (ECC, size) pair."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--device",
        required=True,
        help="Device name/label (e.g. 'Galaxy Tab S9 Ultra')",
    )
    parser.add_argument(
        "--manifest",
        default="test-qr-density/manifest.json",
        help="Path to manifest.json produced by generate_density_qrs.py",
    )
    parser.add_argument(
        "--output",
        default="test-results/density-scan-results.json",
        help="Path for the JSON results file (created/overwritten on completion)",
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8765",
        help="Display server URL for auto-sync (set empty to disable)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    run_test(
        device=args.device,
        manifest_path=pathlib.Path(args.manifest),
        output_path=pathlib.Path(args.output),
        server=args.server or None,
    )


if __name__ == "__main__":
    main()
