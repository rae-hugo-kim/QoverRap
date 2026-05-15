#!/usr/bin/env bash
# render_patent_figures.sh - Render KIPO patent figures (Fig. 1-6) from PlantUML sources.
#
# KIPO 도면 작성 기준:
#   - 흑백 (BW) — color disabled via _kipo_style.iuml
#   - 선명한 실선 (300dpi+) — skinparam dpi 300
#   - 참조부호 일관 — sources include numbered labels
#
# Outputs:
#   docs/patent/figures/rendered/<name>.png  — 300dpi raster (KEAPS 첨부용)
#   docs/patent/figures/rendered/<name>.svg  — vector (PDF 변환용)
#
# PlantUML detection priority:
#   1. system `plantuml` (apt install plantuml)
#   2. `plantuml.jar` in project root or PLANTUML_JAR env var
#   3. Docker fallback (plantuml/plantuml-server)
#
# Usage:
#   bash scripts/render_patent_figures.sh           # render all
#   bash scripts/render_patent_figures.sh fig1      # render single

set -euo pipefail

cd "$(dirname "$0")/.."

SRC_DIR="docs/patent/figures/sources"
OUT_DIR="docs/patent/figures/rendered"
mkdir -p "$OUT_DIR"

# Determine renderer
PLANTUML_CMD=""
if command -v plantuml >/dev/null 2>&1; then
  PLANTUML_CMD="plantuml"
elif [[ -n "${PLANTUML_JAR:-}" && -f "$PLANTUML_JAR" ]]; then
  PLANTUML_CMD="java -jar $PLANTUML_JAR"
elif [[ -f "plantuml.jar" ]]; then
  PLANTUML_CMD="java -jar plantuml.jar"
elif command -v docker >/dev/null 2>&1; then
  PLANTUML_CMD="docker run --rm -v $(pwd):/work -w /work plantuml/plantuml"
else
  echo "ERROR: PlantUML not found. Install one of:"
  echo "  - sudo apt install plantuml"
  echo "  - download plantuml.jar to project root: wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"
  echo "  - install docker"
  exit 1
fi

echo "Renderer: $PLANTUML_CMD"
echo "Source:   $SRC_DIR"
echo "Output:   $OUT_DIR"
echo

# Filter (optional)
FILTER="${1:-}"

shopt -s nullglob
for src in "$SRC_DIR"/fig*.puml; do
  base="$(basename "$src" .puml)"
  if [[ -n "$FILTER" ]] && [[ "$base" != "$FILTER"* ]]; then
    continue
  fi
  echo "▶ Rendering $base ..."

  # PNG (raster, KEAPS 첨부용)
  $PLANTUML_CMD -tpng -o "$(realpath "$OUT_DIR")" "$src"

  # SVG (vector, PDF 변환 소스)
  $PLANTUML_CMD -tsvg -o "$(realpath "$OUT_DIR")" "$src"

  echo "  → $OUT_DIR/$base.png  (KEAPS PNG)"
  echo "  → $OUT_DIR/$base.svg  (vector — convert to PDF if needed)"
done

# Optional: SVG → PDF (requires rsvg-convert or cairosvg)
if command -v rsvg-convert >/dev/null 2>&1; then
  echo
  echo "Converting SVG → PDF (via rsvg-convert)..."
  for svg in "$OUT_DIR"/fig*.svg; do
    base="$(basename "$svg" .svg)"
    rsvg-convert -f pdf -o "$OUT_DIR/$base.pdf" "$svg"
    echo "  → $OUT_DIR/$base.pdf"
  done
elif python3 -c "import cairosvg" >/dev/null 2>&1; then
  echo
  echo "Converting SVG → PDF (via cairosvg)..."
  for svg in "$OUT_DIR"/fig*.svg; do
    base="$(basename "$svg" .svg)"
    python3 -c "import cairosvg; cairosvg.svg2pdf(url='$svg', write_to='$OUT_DIR/$base.pdf')"
    echo "  → $OUT_DIR/$base.pdf"
  done
else
  echo
  echo "(SVG→PDF skipped: install rsvg-convert ('sudo apt install librsvg2-bin') or 'pip install cairosvg' to enable)"
fi

echo
echo "Done."
