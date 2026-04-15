#!/usr/bin/env python3
"""qr-display-server.py — QR 이미지 디스플레이 서버 (물리 기기 테스트용)
QR image display server for physical device testing.

기기가 스캔할 QR 이미지를 화면에 하나씩 자동으로 표시합니다.
Displays QR images one at a time for a physical device to scan.

사용법 (Usage):
    python scripts/qr-display-server.py [--image-dir DIR] [--port PORT] [--interval SECS]

예시 (Example):
    python scripts/qr-display-server.py --image-dir test-qr-images/ --port 8080 --interval 8

키보드 컨트롤 (Keyboard controls — browser page):
    Space      — 일시정지/재개 (Pause/Resume auto-advance)
    ArrowRight — 다음 QR (Next QR)
    ArrowLeft  — 이전 QR (Previous QR)

의존성: Python 표준 라이브러리만 사용 (stdlib only — no external deps)
"""

__version__ = "0.1.0"

import argparse
import base64
import json
import os
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


# ---------------------------------------------------------------------------
# Image discovery
# ---------------------------------------------------------------------------

def _find_qr_images(image_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return sorted list of PNG images in image_dir (excludes grid files)."""
    if not image_dir.exists():
        return []
    images = sorted(
        p for p in image_dir.glob("qr_*.png")
        if "grid" not in p.name
    )
    return images


# ---------------------------------------------------------------------------
# HTML page (inline — no external deps)
# ---------------------------------------------------------------------------

def _build_html(images_json: str, interval_ms: int) -> str:
    """Build the fullscreen QR display HTML page."""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QoverwRap QR Display</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: #000;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: 'Courier New', monospace;
      color: #fff;
      overflow: hidden;
      user-select: none;
    }}

    #qr-container {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }}

    #qr-img {{
      width: 80vh;
      height: 80vh;
      object-fit: contain;
      image-rendering: pixelated;  /* QR 코드 선명도 유지 / Keep QR crisp */
      background: #fff;
      padding: 8px;
      border-radius: 4px;
    }}

    /* 진행 상황 오버레이 (좌상단) / Progress overlay (top-left) */
    #progress {{
      position: fixed;
      top: 12px;
      left: 16px;
      font-size: 14px;
      color: rgba(255,255,255,0.7);
      background: rgba(0,0,0,0.5);
      padding: 4px 10px;
      border-radius: 4px;
      line-height: 1.6;
    }}

    /* 카운트다운 타이머 (우상단) / Countdown timer (top-right) */
    #timer {{
      position: fixed;
      top: 12px;
      right: 16px;
      font-size: 22px;
      font-weight: bold;
      color: rgba(255,255,255,0.85);
      background: rgba(0,0,0,0.5);
      padding: 4px 12px;
      border-radius: 4px;
      min-width: 48px;
      text-align: center;
    }}

    #timer.paused {{
      color: #f0a500;
    }}

    /* 파일명 (하단 중앙) / Filename (bottom-center) */
    #filename {{
      position: fixed;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 13px;
      color: rgba(255,255,255,0.5);
      background: rgba(0,0,0,0.4);
      padding: 3px 10px;
      border-radius: 4px;
      white-space: nowrap;
    }}

    /* 조작 힌트 (하단 우측) / Controls hint (bottom-right) */
    #controls-hint {{
      position: fixed;
      bottom: 16px;
      right: 16px;
      font-size: 11px;
      color: rgba(255,255,255,0.35);
      text-align: right;
      line-height: 1.8;
    }}

    /* 일시정지 오버레이 / Pause overlay */
    #pause-banner {{
      display: none;
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 32px;
      font-weight: bold;
      color: #f0a500;
      background: rgba(0,0,0,0.7);
      padding: 16px 32px;
      border-radius: 8px;
      pointer-events: none;
    }}
    #pause-banner.visible {{ display: block; }}
  </style>
</head>
<body>

  <div id="qr-container">
    <img id="qr-img" src="" alt="QR Code">
  </div>

  <div id="progress">
    <span id="idx-display">1</span> / <span id="total-display">?</span>
  </div>

  <div id="timer">8</div>

  <div id="filename">loading...</div>

  <div id="controls-hint">
    Space: 일시정지/재개<br>
    ← → : 이전/다음
  </div>

  <div id="pause-banner">⏸ PAUSED</div>

  <script>
    // -------------------------------------------------------------------------
    // Data from server
    // -------------------------------------------------------------------------
    const IMAGES = {images_json};
    const INTERVAL_MS = {interval_ms};

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------
    let currentIndex = 0;
    let paused = false;
    let remainingMs = INTERVAL_MS;
    let lastTick = null;
    let rafId = null;

    const imgEl       = document.getElementById('qr-img');
    const idxEl       = document.getElementById('idx-display');
    const totalEl     = document.getElementById('total-display');
    const timerEl     = document.getElementById('timer');
    const filenameEl  = document.getElementById('filename');
    const pauseBanner = document.getElementById('pause-banner');

    totalEl.textContent = IMAGES.length;

    // -------------------------------------------------------------------------
    // Display a specific QR image
    // -------------------------------------------------------------------------
    function showImage(index) {{
      if (IMAGES.length === 0) {{
        imgEl.src = '';
        idxEl.textContent = '0';
        filenameEl.textContent = 'No QR images found in directory';
        return;
      }}
      currentIndex = ((index % IMAGES.length) + IMAGES.length) % IMAGES.length;
      const entry = IMAGES[currentIndex];

      // Fetch image as data URL via API endpoint to avoid CORS / file serving issues
      fetch('/api/image?index=' + currentIndex)
        .then(r => r.json())
        .then(data => {{
          imgEl.src = 'data:image/png;base64,' + data.b64;
        }})
        .catch(() => {{
          imgEl.src = '';
        }});

      idxEl.textContent  = currentIndex + 1;
      filenameEl.textContent = entry.filename;
      remainingMs = INTERVAL_MS;
    }}

    // -------------------------------------------------------------------------
    // Animation-frame countdown loop
    // -------------------------------------------------------------------------
    function tick(timestamp) {{
      if (!paused) {{
        if (lastTick !== null) {{
          remainingMs -= (timestamp - lastTick);
        }}
        lastTick = timestamp;

        const secs = Math.max(0, Math.ceil(remainingMs / 1000));
        timerEl.textContent = INTERVAL_MS > 0 ? secs : '→';

        if (INTERVAL_MS > 0 && remainingMs <= 0) {{
          lastTick = null;
          showImage(currentIndex + 1);
        }}
      }} else {{
        lastTick = null;
        timerEl.textContent = '⏸';
      }}
      rafId = requestAnimationFrame(tick);
    }}

    // -------------------------------------------------------------------------
    // Keyboard controls
    // -------------------------------------------------------------------------
    document.addEventListener('keydown', (e) => {{
      if (e.code === 'Space') {{
        e.preventDefault();
        paused = !paused;
        timerEl.classList.toggle('paused', paused);
        pauseBanner.classList.toggle('visible', paused);
        if (!paused) remainingMs = INTERVAL_MS;  // 재개 시 타이머 리셋 / reset timer on resume
      }} else if (e.code === 'ArrowRight') {{
        e.preventDefault();
        showImage(currentIndex + 1);
      }} else if (e.code === 'ArrowLeft') {{
        e.preventDefault();
        showImage(currentIndex - 1);
      }}
    }});

    // -------------------------------------------------------------------------
    // Init
    // -------------------------------------------------------------------------
    if (IMAGES.length === 0) {{
      document.body.innerHTML = '<div style="color:#f55;font-size:24px;padding:40px;">' +
        'QR 이미지를 찾을 수 없습니다.<br>' +
        'Run: python scripts/generate_test_qrs.py<br><br>' +
        'No QR images found.<br>Run: python scripts/generate_test_qrs.py' +
        '</div>';
    }} else {{
      showImage(0);
      rafId = requestAnimationFrame(tick);
    }}
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

class QRDisplayHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # 간결한 로그 / Compact logging
        sys.stdout.write(f"[{self.address_string()}] {fmt % args}\n")
        sys.stdout.flush()

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            images = self.server.qr_images
            image_list = [{"filename": p.name} for p in images]
            html = _build_html(
                images_json=json.dumps(image_list),
                interval_ms=self.server.interval_ms,
            )
            self._send_html(html)

        elif path == "/api/image":
            images = self.server.qr_images
            params = parse_qs(parsed.query)
            try:
                idx = int(params.get("index", ["0"])[0])
                idx = max(0, min(idx, len(images) - 1))
            except (ValueError, IndexError):
                self._send_json({"error": "invalid index"}, 400)
                return
            if not images:
                self._send_json({"error": "no images"}, 404)
                return
            img_path = images[idx]
            b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
            self._send_json({"b64": b64, "filename": img_path.name, "index": idx})

        elif path == "/api/list":
            images = self.server.qr_images
            self._send_json({
                "count": len(images),
                "images": [p.name for p in images],
                "interval_ms": self.server.interval_ms,
            })

        elif path == "/health":
            self._send_json({"status": "ok", "version": __version__})

        elif path == "/api/current":
            self._send_json({
                "current_index": getattr(self.server, "_remote_index", 0),
            })

        else:
            self._send_html("<h1>404 Not Found</h1>", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        images = self.server.qr_images

        if path == "/api/next":
            cur = getattr(self.server, "_remote_index", 0)
            nxt = min(cur + 1, len(images) - 1)
            self.server._remote_index = nxt
            self._send_json({"index": nxt, "total": len(images)})

        elif path == "/api/prev":
            cur = getattr(self.server, "_remote_index", 0)
            prv = max(cur - 1, 0)
            self.server._remote_index = prv
            self._send_json({"index": prv, "total": len(images)})

        elif path == "/api/set":
            params = parse_qs(parsed.query)
            try:
                idx = int(params.get("index", ["0"])[0])
                idx = max(0, min(idx, len(images) - 1))
            except (ValueError, IndexError):
                self._send_json({"error": "invalid index"}, 400)
                return
            self.server._remote_index = idx
            self._send_json({"index": idx, "total": len(images)})

        else:
            self._send_json({"error": "not found"}, 404)


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------

def _make_server(
    image_dir: pathlib.Path,
    port: int,
    interval: int,
) -> HTTPServer:
    images = _find_qr_images(image_dir)
    server = HTTPServer(("0.0.0.0", port), QRDisplayHandler)
    server.qr_images = images          # type: ignore[attr-defined]
    server.interval_ms = interval * 1000  # type: ignore[attr-defined]
    return server


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "QR 이미지 디스플레이 서버 — 물리 기기 스캔 테스트용\n"
            "QR image display server for physical device scan testing.\n\n"
            "브라우저에서 http://localhost:PORT 를 열어 QR을 표시하고,\n"
            "기기를 화면 앞에 위치시켜 스캔합니다.\n"
            "Open http://localhost:PORT in a browser, position device in front to scan."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--image-dir",
        default="test-qr-images/",
        metavar="DIR",
        help="QR PNG 이미지가 있는 디렉터리 (default: test-qr-images/)\n"
             "Directory containing QR PNG images (default: test-qr-images/)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        metavar="PORT",
        help="HTTP 서버 포트 (default: 8080) / HTTP server port (default: 8080)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=8,
        metavar="SECS",
        help="QR 자동 전환 간격(초) (default: 8)\n"
             "Seconds between automatic QR advances (default: 8)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    image_dir = pathlib.Path(args.image_dir)

    images = _find_qr_images(image_dir)
    print(f"QoverwRap QR Display Server v{__version__}")
    print(f"  이미지 디렉터리 / Image dir : {image_dir.resolve()}")
    print(f"  발견된 QR 이미지 수 / Found : {len(images)} image(s)")
    print(f"  자동 전환 간격 / Interval   : {args.interval}s")
    print(f"  포트 / Port                 : {args.port}")
    print()

    if not images:
        print(
            "경고: QR 이미지가 없습니다. 먼저 생성하세요:\n"
            "Warning: No QR images found. Generate them first:\n"
            "  python scripts/generate_test_qrs.py\n"
        )

    server = _make_server(image_dir, args.port, args.interval)
    print(f"서버 시작 / Server started: http://0.0.0.0:{args.port}")
    print("브라우저에서 위 URL을 열고 기기를 화면 앞에 위치시키세요.")
    print("Open the URL in a browser and position your device in front of the screen.")
    print("종료: Ctrl+C / Stop: Ctrl+C")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료 / Server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
