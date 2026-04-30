#!/usr/bin/env bash
# cleanup_demo_figures.sh - Convert demo screenshots (Fig. 5-7) to KIPO BW format.
#
# Input:  docs/patent/figures/fig{5,6a,6b,6c,7a,7b}-*.png  (1100x900 RGB demo captures)
# Output: docs/patent/figures/rendered/fig{5,6a,6b,6c,7a,7b}_clean.png
#
# Operations applied:
#   1. Crop top 60px (remove app header + toggle buttons)
#   2. Convert to grayscale (-colorspace gray)
#   3. Bump contrast for KIPO scanner readability (-level 10%,90%)
#   4. Strip EXIF/metadata
#   5. Re-density to 300 DPI (KIPO 권장)
#
# KIPO 도면 작성 기준 자동 충족: BW + 300dpi.
# 추가 수동 작업이 필요한 항목 (스크립트 범위 외):
#   - 참조부호 부착 (Layer A→11, Layer B→15, Layer C→16, 출력 수준 표시)
#   - QR 코드 영역만 별도 crop
#   - 데모 앱 UI 라벨 ("샷 ON", "위변조 시도" 등) 영역 제거 (PNG 위에 white box 덮기)
#
# 권장: 본 스크립트로 1차 정리한 뒤, 출원 직전에 GIMP/Inkscape 로
# 참조부호와 화살표를 수동 추가하거나, 데모 앱을 patent-mode 로 다시 캡처.
#
# Usage:
#   bash scripts/cleanup_demo_figures.sh
#   bash scripts/cleanup_demo_figures.sh fig5    # 단일 처리

set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v convert >/dev/null 2>&1; then
  echo "ERROR: ImageMagick 'convert' not found."
  echo "Install: sudo apt install imagemagick"
  exit 1
fi

SRC_DIR="docs/patent/figures"
OUT_DIR="docs/patent/figures/rendered"
mkdir -p "$OUT_DIR"

FILTER="${1:-}"

shopt -s nullglob
processed=0
for src in "$SRC_DIR"/fig5-*.png "$SRC_DIR"/fig6*-*.png "$SRC_DIR"/fig7*-*.png; do
  base="$(basename "$src" .png)"
  # base example: "fig5-bare-3col" → key "fig5"
  key="${base%%-*}"

  if [[ -n "$FILTER" ]] && [[ "$key" != "$FILTER"* ]]; then
    continue
  fi

  out="$OUT_DIR/${key}_clean.png"
  echo "▶ $src → $out"

  convert "$src" \
    -crop "1100x840+0+60" +repage \
    -colorspace gray \
    -level "10%,90%" \
    -strip \
    -density 300 -units PixelsPerInch \
    "$out"

  processed=$((processed + 1))
done

echo
echo "Processed: $processed file(s)"
echo
echo "Manual touchups still required for KEAPS submission:"
echo "  - 참조부호 부착 (Layer A→11, B→15, C→16)"
echo "  - 데모 앱 UI 텍스트/버튼 영역 제거 또는 마스킹"
echo "  - 출력 수준 라벨 (제1/제2/제3) 추가"
echo "  - 또는 demo/ 앱을 'patent capture mode' 로 재캡처"
