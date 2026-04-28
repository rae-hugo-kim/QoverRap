import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";

interface Props {
  onResult: (text: string) => void;
}

export default function QRScanner({ onResult }: Props) {
  const elRef = useRef<HTMLDivElement | null>(null);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manual, setManual] = useState("");

  useEffect(() => {
    return () => {
      const s = scannerRef.current;
      if (s && s.isScanning) {
        s.stop().catch(() => {});
      }
    };
  }, []);

  async function start() {
    setError(null);
    if (!elRef.current) return;
    try {
      if (!scannerRef.current) {
        // Prefer browser-native BarcodeDetector when available — much faster
        // and more tolerant on mobile. Falls back to ZXing-wasm otherwise.
        scannerRef.current = new Html5Qrcode(elRef.current.id, {
          verbose: false,
          useBarCodeDetectorIfSupported: true,
          experimentalFeatures: { useBarCodeDetectorIfSupported: true },
        });
      }
      await scannerRef.current.start(
        {
          facingMode: { ideal: "environment" },
        },
        {
          fps: 24,
          // Adaptive scan box: 75% of the smaller viewport dimension.
          qrbox: (vw: number, vh: number) => {
            const min = Math.min(vw, vh);
            const size = Math.max(200, Math.floor(min * 0.75));
            return { width: size, height: size };
          },
          aspectRatio: 1.0,
          // Ask the camera for HD; mobile cameras pick the closest mode.
          videoConstraints: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
        } as never,
        (decoded) => {
          onResult(decoded);
          stop();
        },
        () => {
          /* per-frame scan error: ignore */
        },
      );
      setRunning(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function stop() {
    const s = scannerRef.current;
    if (s && s.isScanning) {
      try {
        await s.stop();
      } catch {
        /* noop */
      }
    }
    setRunning(false);
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2 items-center">
        {!running ? (
          <button
            onClick={start}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
          >
            카메라 시작
          </button>
        ) : (
          <button
            onClick={stop}
            className="px-3 py-1.5 bg-slate-200 rounded text-sm"
          >
            카메라 정지
          </button>
        )}
        {running && (
          <span className="text-xs text-slate-500 animate-pulse">
            QR을 화면 가운데 박스 안에 맞추세요
          </span>
        )}
      </div>
      <div
        id="qr-scanner-region"
        ref={elRef}
        className="w-full max-w-md aspect-square bg-slate-900 rounded overflow-hidden mx-auto"
      />
      {error && (
        <p className="text-xs text-red-600">
          카메라 오류: {error}. HTTPS 환경 또는 권한을 확인하세요.
        </p>
      )}
      <p className="text-[11px] text-slate-500">
        팁: 화면 위 QR을 스캔할 땐 폰을 20–30cm 거리, QR이 박스 안 80%를 차지하도록 맞추세요. 흔들림이 있으면 잠시 멈추고 재시도.
      </p>
      <details className="text-sm">
        <summary className="cursor-pointer text-slate-600">
          카메라 없이 직접 입력
        </summary>
        <div className="mt-2 flex gap-2">
          <input
            value={manual}
            onChange={(e) => setManual(e.target.value)}
            placeholder="QR payload 문자열 붙여넣기"
            className="flex-1 px-2 py-1.5 border border-slate-300 rounded text-sm font-mono"
          />
          <button
            onClick={() => manual && onResult(manual)}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
          >
            적용
          </button>
        </div>
      </details>
    </div>
  );
}
