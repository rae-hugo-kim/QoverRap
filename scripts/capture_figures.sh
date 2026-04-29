#!/usr/bin/env bash
# Capture patent figures (Fig 5/6/7) from the running demo via agent-browser.
#
# Prereqs:
#   - Backend up:  uvicorn demo.backend.main:app --port 8000
#   - Frontend up: cd demo/frontend && npm run dev   (default :5173)
#   - agent-browser CLI on PATH (npm i -g agent-browser)
#
# Output: docs/patent/figures/*.png

set -euo pipefail

URL="${URL:-http://127.0.0.1:5173/}"
OUT="${OUT:-docs/patent/figures}"
mkdir -p "$OUT"

ab() { agent-browser "$@"; }
# Click via JS to bypass actionability heuristics that occasionally stall on
# elements that just mounted from a parent re-render.
abclick() { agent-browser eval "document.querySelector(${1@Q})?.click()"; }

# 1100x900 = comfortable for the 3-column md:grid-cols-3 layout
ab set viewport 1100 900 || true
ab open "$URL"
ab wait '[data-testid="issuer-tigers-2026"]'
# Wait for Google Fonts (Noto Sans KR) to load before any screenshots,
# otherwise Korean glyphs render as boxes on a CJK-fontless host.
ab eval "document.fonts.ready.then(() => true)"
ab wait 1500

build_and_resolve() {
  local issuer="$1"
  abclick '[data-testid="reset"]' || true
  ab wait 800
  ab wait "[data-testid=\"issuer-$issuer\"]"
  abclick "[data-testid=\"issuer-$issuer\"]"
  ab wait 400
  ab wait '[data-testid="build-qr"]'
  abclick '[data-testid="build-qr"]'
  ab wait 'img[alt="QR"]'
  ab wait 2800  # toast clear
  ab wait '[data-testid="skip-scan"]'
  abclick '[data-testid="skip-scan"]'
  ab wait '[data-testid="resolve-grid"]'
  ab wait 2800
}

screenshot_mode_on()  { abclick '[data-testid="mode-screenshot"]'; ab wait 350; }
screenshot_mode_off() { abclick '[data-testid="mode-screenshot"]'; ab wait 350; }
themed_on()           { abclick '[data-testid="mode-themed"]'; ab wait 350; }
bare_on()             { abclick '[data-testid="mode-bare"]'; ab wait 350; }

# --- Tigers: Fig 5 (Bare) + Fig 6a (Themed) + Fig 7 (tamper pair) ----------
build_and_resolve "tigers-2026"

screenshot_mode_on
bare_on
ab screenshot "$OUT/fig5-bare-3col.png"

themed_on
ab screenshot "$OUT/fig6a-tigers.png"

abclick '[data-testid="tamper"]'
ab wait 2700  # toast + tamper resolve
ab screenshot "$OUT/fig7a-tampered-invalid.png"

abclick '[data-testid="restore"]'
ab wait 2700
ab screenshot "$OUT/fig7b-restored-valid.png"

screenshot_mode_off

# --- Violet: Fig 6b ---------------------------------------------------------
build_and_resolve "violet-fandom"
screenshot_mode_on
themed_on
ab screenshot "$OUT/fig6b-violet.png"
screenshot_mode_off

# --- Comic Con: Fig 6c ------------------------------------------------------
build_and_resolve "comic-con-2026"
screenshot_mode_on
themed_on
ab screenshot "$OUT/fig6c-comiccon.png"
screenshot_mode_off

ab close

echo "---"
ls -la "$OUT"
echo "Done. Captures in $OUT"
