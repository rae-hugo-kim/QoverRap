#!/usr/bin/env python3
"""collect-results.py — Maestro 결과 파싱 및 요약 리포트 생성
Parse Maestro test output and generate summary report.

physical-device-checklist.md 보고 템플릿 형식으로 출력합니다.
Outputs in physical-device-checklist.md reporting template format.

사용법 (Usage):
    python scripts/collect-results.py [--results-dir DIR] [--manifest PATH] [--output PATH]

예시 (Example):
    python scripts/collect-results.py --results-dir test-results/samsung
    python scripts/collect-results.py --results-dir test-results/generic --output test-results/report.md
"""

__version__ = "0.1.0"

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 데이터 구조 (Data structures)
# ---------------------------------------------------------------------------

class ScanResult(NamedTuple):
    index: int            # 스캔 번호 (1-based) / Scan number
    screenshot_path: str  # 스크린샷 파일 경로 / Screenshot file path
    status: str           # "pass" | "fail" | "timeout" | "unknown"
    qr_filename: str      # 대응하는 QR 파일명 / Corresponding QR filename
    notes: str            # 추가 메모 / Additional notes


# ---------------------------------------------------------------------------
# Screenshot 파싱 (Parse screenshots)
# ---------------------------------------------------------------------------

def _parse_screenshots(results_dir: pathlib.Path) -> list[pathlib.Path]:
    """결과 디렉터리에서 스캔 스크린샷을 정렬하여 반환합니다.
    Return sorted scan screenshots from results directory."""
    screenshots = sorted(results_dir.glob("scan_*.png"))
    return screenshots


def _extract_index_from_screenshot(path: pathlib.Path) -> int:
    """scan_001.png → 1 형태로 인덱스 추출 / Extract index from filename."""
    match = re.search(r"scan_(\d+)", path.name)
    if match:
        return int(match.group(1))
    return 0


# ---------------------------------------------------------------------------
# Maestro 로그 파싱 (Parse Maestro log)
# ---------------------------------------------------------------------------

def _parse_maestro_log(log_path: pathlib.Path) -> dict[int, str]:
    """Maestro 로그에서 스캔 인덱스별 상태를 추출합니다.
    Extract per-scan status from Maestro log.

    Returns: dict mapping scan_index → "pass" | "fail" | "timeout"
    """
    if not log_path.exists():
        return {}

    statuses: dict[int, str] = {}
    content = log_path.read_text(encoding="utf-8", errors="replace")

    # Maestro 출력 패턴 분석 / Analyze Maestro output patterns
    # 성공: "Flow Completed" 또는 반복 내 오류 없음
    # 실패: "Flow Failed", "Error", "Timeout"
    lines = content.splitlines()
    current_iteration = 0

    for line in lines:
        # 반복 시작 감지 / Detect iteration start
        iter_match = re.search(r"iteration[:\s]+(\d+)", line, re.IGNORECASE)
        if iter_match:
            current_iteration = int(iter_match.group(1))

        # 오류/타임아웃 감지 / Detect error/timeout
        if re.search(r"(timeout|timed out)", line, re.IGNORECASE):
            if current_iteration > 0:
                statuses[current_iteration] = "timeout"
        elif re.search(r"(error|failed|exception)", line, re.IGNORECASE):
            if current_iteration > 0 and current_iteration not in statuses:
                statuses[current_iteration] = "fail"

    return statuses


# ---------------------------------------------------------------------------
# 매니페스트 참조 (Cross-reference with manifest)
# ---------------------------------------------------------------------------

def _load_manifest(manifest_path: pathlib.Path) -> dict:
    """manifest.json을 로드합니다 / Load manifest.json."""
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _match_qr_to_scan(
    scan_index: int,
    manifest: dict,
) -> str:
    """스캔 인덱스에 대응하는 QR 파일명을 반환합니다.
    Return QR filename corresponding to scan index."""
    images = manifest.get("images", [])
    if not images:
        return f"qr_{scan_index:03d}_unknown.png"
    # 인덱스 기반 순환 매칭 / Cycle through images by index
    idx = (scan_index - 1) % len(images)
    return images[idx].get("filename", f"qr_{scan_index:03d}.png")


# ---------------------------------------------------------------------------
# 결과 집계 (Aggregate results)
# ---------------------------------------------------------------------------

def _aggregate_results(
    screenshots: list[pathlib.Path],
    log_statuses: dict[int, str],
    manifest: dict,
) -> list[ScanResult]:
    """스크린샷 + 로그 + 매니페스트를 통합하여 스캔 결과 목록을 생성합니다.
    Combine screenshots + log + manifest into scan result list."""
    results: list[ScanResult] = []

    for screenshot in screenshots:
        idx = _extract_index_from_screenshot(screenshot)
        # 스크린샷이 존재하면 기본적으로 pass (카메라 앱이 열리고 스캔까지 도달)
        # Screenshot exists → at least reached scan step (default pass)
        base_status = "pass"
        if idx in log_statuses:
            base_status = log_statuses[idx]

        qr_filename = _match_qr_to_scan(idx, manifest)

        results.append(ScanResult(
            index=idx,
            screenshot_path=str(screenshot.name),
            status=base_status,
            qr_filename=qr_filename,
            notes="",
        ))

    # 스크린샷이 없는 스캔 항목 추가 (로그에서 실패로 기록된 경우)
    # Add entries for scans without screenshots (logged as fail)
    screenshotted_indices = {r.index for r in results}
    for idx, status in log_statuses.items():
        if idx not in screenshotted_indices:
            results.append(ScanResult(
                index=idx,
                screenshot_path="(없음 / none)",
                status=status,
                qr_filename=_match_qr_to_scan(idx, manifest),
                notes="스크린샷 없음 / No screenshot captured",
            ))

    return sorted(results, key=lambda r: r.index)


# ---------------------------------------------------------------------------
# 리포트 생성 (Generate report)
# ---------------------------------------------------------------------------

def _compute_stats(results: list[ScanResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    timeouts = sum(1 for r in results if r.status == "timeout")
    unknown = sum(1 for r in results if r.status == "unknown")
    success_rate = (passed / total * 100) if total > 0 else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "timeouts": timeouts,
        "unknown": unknown,
        "success_rate": success_rate,
    }


def _format_report(
    results: list[ScanResult],
    stats: dict,
    results_dir: pathlib.Path,
    device_label: str,
) -> str:
    """physical-device-checklist.md 보고 양식에 맞는 마크다운 리포트를 생성합니다.
    Generate markdown report matching physical-device-checklist.md format."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status_emoji = {
        "pass": "PASS",
        "fail": "FAIL",
        "timeout": "TIMEOUT",
        "unknown": "?",
    }

    lines = [
        "# QoverwRap 물리 기기 스캔 테스트 결과 / Physical Device Scan Test Results",
        "",
        f"**생성 시각 / Generated**: {now}",
        f"**기기 / Device**: {device_label}",
        f"**결과 디렉터리 / Results dir**: `{results_dir.resolve()}`",
        f"**스크립트 버전 / Script version**: {__version__}",
        "",
        "---",
        "",
        "## 요약 / Summary",
        "",
        f"| 항목 / Metric             | 값 / Value                     |",
        f"|---------------------------|--------------------------------|",
        f"| 총 스캔 수 / Total scans  | {stats['total']}               |",
        f"| 성공 / Passed             | {stats['passed']}              |",
        f"| 실패 / Failed             | {stats['failed']}              |",
        f"| 타임아웃 / Timeouts       | {stats['timeouts']}            |",
        f"| 불명 / Unknown            | {stats['unknown']}             |",
        f"| **성공률 / Success rate** | **{stats['success_rate']:.1f}%** |",
        "",
        "### MET-1 프로토콜 판정 (95%+ 기준) / MET-1 Protocol Verdict (95%+ threshold)",
        "",
    ]

    if stats["success_rate"] >= 95.0:
        lines += [
            f"> **PASS** — 성공률 {stats['success_rate']:.1f}% >= 95% 기준 충족",
            f"> **PASS** — Success rate {stats['success_rate']:.1f}% meets 95% threshold",
        ]
    else:
        lines += [
            f"> **FAIL** — 성공률 {stats['success_rate']:.1f}% < 95% 기준 미달",
            f"> **FAIL** — Success rate {stats['success_rate']:.1f}% below 95% threshold",
        ]

    lines += [
        "",
        "---",
        "",
        "## 스캔별 결과 / Per-Scan Results",
        "",
        "| # | 상태 | QR 파일 | 스크린샷 | 메모 |",
        "|---|------|---------|---------|------|",
    ]

    for r in results:
        emoji = status_emoji.get(r.status, "?")
        lines.append(
            f"| {r.index} | {emoji} | `{r.qr_filename}` | `{r.screenshot_path}` | {r.notes} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 다음 단계 / Next Steps",
        "",
        "- [ ] 실패/타임아웃 케이스 원인 분석 / Analyze failed/timeout cases",
        "- [ ] 필요 시 조명 조건 개선 후 재테스트 / Retest with improved lighting if needed",
        "- [ ] physical-device-checklist.md에 결과 기록 / Record results in physical-device-checklist.md",
        "- [ ] 스크린샷 팀 리뷰 / Team review of screenshots",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Maestro 물리 기기 테스트 결과를 파싱하고 요약 리포트를 생성합니다.\n"
            "Parse Maestro physical device test results and generate summary report."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--results-dir",
        default="test-results/samsung",
        metavar="DIR",
        help="Maestro 스크린샷과 로그가 있는 디렉터리 / Directory with screenshots and log",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        metavar="PATH",
        help=(
            "manifest.json 경로 (기본: --image-dir/manifest.json)\n"
            "Path to manifest.json (default: image-dir/manifest.json)"
        ),
    )
    parser.add_argument(
        "--image-dir",
        default="test-qr-images/",
        metavar="DIR",
        help="QR 이미지 디렉터리 (manifest.json 위치 특정용) / QR image dir (for locating manifest.json)",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="리포트 저장 경로 (기본: stdout) / Output file path (default: stdout)",
    )
    parser.add_argument(
        "--device-label",
        default=None,
        metavar="LABEL",
        help="기기 레이블 (기본: results-dir 마지막 경로 요소) / Device label (default: last results-dir component)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    results_dir = pathlib.Path(args.results_dir)
    if not results_dir.exists():
        sys.exit(
            f"결과 디렉터리가 없습니다: {results_dir}\n"
            f"Results directory not found: {results_dir}"
        )

    # 매니페스트 로드 / Load manifest
    manifest_path = (
        pathlib.Path(args.manifest)
        if args.manifest
        else pathlib.Path(args.image_dir) / "manifest.json"
    )
    manifest = _load_manifest(manifest_path)
    if manifest:
        print(f"매니페스트 로드됨 / Manifest loaded: {manifest_path}", file=sys.stderr)
        print(f"  QR 이미지 수 / Images: {len(manifest.get('images', []))}", file=sys.stderr)
    else:
        print(f"경고: 매니페스트 없음 / Warning: No manifest found at {manifest_path}", file=sys.stderr)

    # 스크린샷 파싱 / Parse screenshots
    screenshots = _parse_screenshots(results_dir)
    print(f"스크린샷 발견 / Screenshots found: {len(screenshots)}", file=sys.stderr)

    # Maestro 로그 파싱 / Parse Maestro log
    log_path = results_dir / "maestro-output.log"
    log_statuses = _parse_maestro_log(log_path)
    if log_statuses:
        print(f"로그 파싱됨 / Log parsed: {len(log_statuses)} status entries", file=sys.stderr)

    # 결과 집계 / Aggregate results
    results = _aggregate_results(screenshots, log_statuses, manifest)

    if not results:
        print("결과 없음. 스크린샷이나 로그 항목을 찾을 수 없습니다.", file=sys.stderr)
        print("No results found. No screenshots or log entries.", file=sys.stderr)
        sys.exit(1)

    # 통계 계산 / Compute stats
    stats = _compute_stats(results)

    # 기기 레이블 / Device label
    device_label = args.device_label or results_dir.name

    # 리포트 생성 / Generate report
    report = _format_report(results, stats, results_dir, device_label)

    # 출력 / Output
    if args.output:
        output_path = pathlib.Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"리포트 저장됨 / Report saved: {output_path}", file=sys.stderr)
    else:
        print(report)

    # 콘솔 요약 / Console summary
    print("", file=sys.stderr)
    print("=== 요약 / Summary ===", file=sys.stderr)
    print(f"  총 / Total   : {stats['total']}", file=sys.stderr)
    print(f"  성공 / Pass  : {stats['passed']}", file=sys.stderr)
    print(f"  실패 / Fail  : {stats['failed']}", file=sys.stderr)
    print(f"  성공률 / Rate: {stats['success_rate']:.1f}%", file=sys.stderr)
    verdict = "PASS" if stats["success_rate"] >= 95.0 else "FAIL"
    print(f"  MET-1 판정 / Verdict: {verdict}", file=sys.stderr)


if __name__ == "__main__":
    main()
