import { useEffect, useMemo, useRef, useState } from "react";
import { api, strToHex } from "./api/client";
import type { AccessLevel, ResolveResult, TrustEntry } from "./types";
import StepNav from "./components/StepNav";
import IssuerPicker from "./components/IssuerPicker";
import QRPanel from "./components/QRPanel";
import QRScanner from "./components/QRScanner";
import ResolveColumn from "./components/ResolveColumn";

const STEPS = [
  { id: "issuer", label: "발급자 선택" },
  { id: "compose", label: "레이어 입력" },
  { id: "qr", label: "QR 생성" },
  { id: "scan", label: "스캔" },
  { id: "resolve", label: "접근레벨 비교" },
];

const LEVELS: AccessLevel[] = ["public", "authenticated", "verified"];

const LAYER_A_PRESETS: Record<string, string> = {
  "tigers-2026": "Tigers 정규시즌 입장권",
  "violet-fandom": "VF Diamond Pass",
  "comic-con-2026": "Comic Con 2026 출입증",
};

const LAYER_B_PRESETS: Record<string, object> = {
  "tigers-2026": {
    section: "1루 응원석",
    seat: "12B",
    gate: "Gate 3",
    date: "2026-05-10",
    time: "18:30",
    opponent: "Lions",
    holder: "FAN-2456",
  },
  "violet-fandom": {
    tier: "Diamond Fan",
    member_id: "VIO-008812",
    since: "2024-09",
    exclusive: "Behind The Scenes #07",
  },
  "comic-con-2026": {
    badge: "VIP Pass",
    name: "코드네임 인비저블",
    track: "Hall H",
    panel: "Marvel Studios Reveal",
    day: "Day 1 / Sat",
  },
};

const TAMPER_PRESETS: Record<string, object> = {
  "tigers-2026": {
    section: "VVIP 스카이박스",
    seat: "FORGED",
    gate: "Gate 1",
    date: "2026-05-10",
    time: "18:30",
    opponent: "Lions",
    holder: "STOLEN-0001",
  },
  "violet-fandom": {
    tier: "★★★ Platinum ★★★",
    member_id: "VIO-FORGED",
    since: "2020-01",
    exclusive: "ALL CONTENT",
  },
  "comic-con-2026": {
    badge: "STAFF ALL-ACCESS",
    name: "FORGED ATTENDEE",
    track: "Hall H",
    panel: "Marvel Studios Reveal",
    day: "All Days",
  },
};

const presetLayerB = (id: string | null) =>
  id ? JSON.stringify(LAYER_B_PRESETS[id] ?? {}, null, 2) : "{}";
const presetLayerA = (id: string | null) =>
  id ? LAYER_A_PRESETS[id] ?? "" : "";
const presetTamper = (id: string | null) =>
  id ? JSON.stringify(TAMPER_PRESETS[id] ?? {}, null, 2) : "{}";

export default function App() {
  const [active, setActive] = useState("issuer");
  const [trust, setTrust] = useState<TrustEntry[]>([]);
  const [issuerId, setIssuerId] = useState<string | null>(null);
  const issuer = useMemo(
    () => trust.find((t) => t.issuer_id === issuerId) ?? null,
    [trust, issuerId],
  );

  const [layerAMessage, setLayerAMessage] = useState("");
  const [layerBJson, setLayerBJson] = useState("{}");
  const [tamperedJson, setTamperedJson] = useState("{}");

  const [encoded, setEncoded] = useState<string | null>(null);
  const [pngBase64, setPngBase64] = useState<string | null>(null);
  const [lastSig, setLastSig] = useState<string | null>(null);
  const [lastLayerBHex, setLastLayerBHex] = useState<string | null>(null);
  const [tampered, setTampered] = useState(false);

  const [themed, setThemed] = useState(true);
  const [screenshot, setScreenshot] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [pulse, setPulse] = useState(false);
  const resolveRef = useRef<HTMLElement | null>(null);

  const [scanned, setScanned] = useState<string | null>(null);
  const [resolves, setResolves] = useState<
    Record<AccessLevel, ResolveResult | null>
  >({
    public: null,
    authenticated: null,
    verified: null,
  });

  // bootstrap trust list
  useEffect(() => {
    api
      .trustList()
      .then((r) => {
        setTrust(r.entries);
        if (r.entries.length && !issuerId) {
          const first = r.entries[0].issuer_id;
          setIssuerId(first);
          setLayerAMessage(presetLayerA(first));
          setLayerBJson(presetLayerB(first));
          setTamperedJson(presetTamper(first));
        }
      })
      .catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const layerA = useMemo(
    () => (issuerId ? `qwr:${issuerId}|${layerAMessage}` : layerAMessage),
    [issuerId, layerAMessage],
  );

  function pickIssuer(id: string) {
    setIssuerId(id);
    setLayerAMessage(presetLayerA(id));
    setLayerBJson(presetLayerB(id));
    setTamperedJson(presetTamper(id));
    setActive("compose");
  }

  function reset() {
    setEncoded(null);
    setPngBase64(null);
    setScanned(null);
    setResolves({ public: null, authenticated: null, verified: null });
    setLastSig(null);
    setLastLayerBHex(null);
    setTampered(false);
    setErr(null);
    setActive("issuer");
    if (issuerId) {
      setLayerAMessage(presetLayerA(issuerId));
      setLayerBJson(presetLayerB(issuerId));
      setTamperedJson(presetTamper(issuerId));
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function flashToast(msg: string) {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2400);
  }

  async function buildQR() {
    if (!issuerId) return;
    setBusy(true);
    setErr(null);
    setScanned(null);
    setResolves({ public: null, authenticated: null, verified: null });
    setTampered(false);
    try {
      const layerBHex = strToHex(layerBJson);
      const sig = await api.trustSign(issuerId, layerA, layerBHex);
      const enc = await api.encode(layerA, layerBHex, sig.signature);
      const img = await api.qrImage(enc.encoded, { box_size: 14, border: 4 });
      setLastSig(sig.signature);
      setLastLayerBHex(layerBHex);
      setEncoded(enc.encoded);
      setPngBase64(img.image_png_base64);
      setActive("qr");
      flashToast("✓ QR 생성됨");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function resolveAll(payload: string) {
    setBusy(true);
    setErr(null);
    try {
      const results = await Promise.all(
        LEVELS.map((lvl) => api.resolve(payload, lvl)),
      );
      setResolves({
        public: results[0],
        authenticated: results[1],
        verified: results[2],
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onScanned(text: string) {
    setScanned(text);
    setActive("resolve");
    flashToast("✓ 스캔 완료 — 해석 중");
    setPulse(true);
    window.setTimeout(() => setPulse(false), 900);
    await resolveAll(text);
    requestAnimationFrame(() =>
      resolveRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
    );
  }

  async function attemptTamper() {
    if (!lastSig) return;
    setBusy(true);
    setErr(null);
    try {
      const tHex = strToHex(tamperedJson);
      // Re-encode with tampered layer_b but original signature → Verified must INVALID
      const enc = await api.encode(layerA, tHex, lastSig);
      setScanned(enc.encoded);
      setTampered(true);
      await resolveAll(enc.encoded);
      flashToast("⚠ 변조 시도 — Verified 가 INVALID 로 강등됩니다");
      setPulse(true);
      window.setTimeout(() => setPulse(false), 900);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function restoreOriginal() {
    if (!lastSig || !lastLayerBHex) return;
    setBusy(true);
    setErr(null);
    try {
      const enc = await api.encode(layerA, lastLayerBHex, lastSig);
      setScanned(enc.encoded);
      setTampered(false);
      await resolveAll(enc.encoded);
      flashToast("↺ 원본 복원");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function downloadQR() {
    if (!pngBase64) return;
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${pngBase64}`;
    a.download = `qoverwrap-${issuerId ?? "qr"}.png`;
    a.click();
  }

  return (
    <div className="min-h-full">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <img src="/favicon.svg" alt="" className="w-7 h-7" />
            <div>
              <h1 className="text-base sm:text-xl font-semibold leading-none">
                QoverwRap
              </h1>
              {!screenshot && (
                <p className="text-[11px] text-slate-500 mt-0.5 hidden sm:block">
                  3-layer QR · 내장 서명 · 발급자 라우팅
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="bg-slate-100 rounded p-0.5 flex">
              <button
                data-testid="mode-bare"
                onClick={() => setThemed(false)}
                className={`px-2.5 py-1 rounded text-xs ${
                  !themed
                    ? "bg-white shadow font-semibold"
                    : "text-slate-500"
                }`}
              >
                Bare
              </button>
              <button
                data-testid="mode-themed"
                onClick={() => setThemed(true)}
                className={`px-2.5 py-1 rounded text-xs ${
                  themed
                    ? "bg-white shadow font-semibold"
                    : "text-slate-500"
                }`}
              >
                Themed
              </button>
            </span>
            <button
              data-testid="mode-screenshot"
              onClick={() => setScreenshot((v) => !v)}
              className={`px-2 py-1.5 rounded text-xs border ${
                screenshot
                  ? "bg-amber-100 border-amber-300 text-amber-900"
                  : "bg-white border-slate-300 text-slate-600 hover:border-slate-500"
              }`}
              title="스크린샷 모드: 설명/디버그 UI를 숨겨 카드만 깔끔히 보입니다"
            >
              📸 {screenshot ? "샷 ON" : "샷"}
            </button>
            <button
              data-testid="reset"
              onClick={reset}
              className="px-3 py-1.5 rounded text-xs bg-slate-900 text-white hover:bg-slate-700"
            >
              ↻ 처음부터
            </button>
          </div>
        </div>
      </header>

      {toast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white text-sm px-4 py-2 rounded-full shadow-lg pointer-events-none">
          {toast}
        </div>
      )}

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        {!screenshot && (
          <StepNav steps={STEPS} activeId={active} onSelect={setActive} />
        )}

        {err && (
          <div className="rounded bg-red-50 text-red-700 px-3 py-2 text-sm">
            {err}
          </div>
        )}

        {/* 1. Issuer */}
        <section id="issuer" className="space-y-3">
          {!screenshot && (
            <>
              <h2 className="font-semibold">
                1. 발급자 선택 (시각 = 검증 루트)
              </h2>
              <p className="text-sm text-slate-600">
                테마 색·로고는 응용 레이어이며, 동시에 *어느 공개키로 검증할지*를
                결정합니다.
              </p>
            </>
          )}
          <IssuerPicker
            entries={trust}
            selectedId={issuerId}
            onSelect={pickIssuer}
          />
        </section>

        {/* 2. Compose */}
        {!screenshot && (
          <section id="compose" className="space-y-3">
            <h2 className="font-semibold">2. 레이어 입력</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label className="block text-sm">
                <span className="block text-xs text-slate-500 mb-1">
                  Layer A (공개 텍스트, 표지)
                </span>
                <input
                  value={layerAMessage}
                  onChange={(e) => setLayerAMessage(e.target.value)}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm"
                />
                <span className="block text-[10px] text-slate-400 mt-1 font-mono">
                  실제 Layer A: {layerA}
                </span>
              </label>
              <label className="block text-sm">
                <span className="block text-xs text-slate-500 mb-1">
                  Layer B (앱 전용 콘텐츠 JSON)
                </span>
                <textarea
                  value={layerBJson}
                  onChange={(e) => setLayerBJson(e.target.value)}
                  rows={6}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs font-mono"
                />
              </label>
            </div>
            <details className="text-sm">
              <summary className="cursor-pointer text-slate-600">
                위변조 시 사용할 페이로드 (서명 후 Layer B 교체)
              </summary>
              <textarea
                value={tamperedJson}
                onChange={(e) => setTamperedJson(e.target.value)}
                rows={4}
                className="mt-2 w-full px-2 py-1.5 border border-red-300 rounded text-xs font-mono bg-red-50"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                QR 생성 후 5번 섹션에서 "변조 시도" 버튼을 누르면 이 값으로 교체됩니다.
              </p>
            </details>
            <button
              data-testid="build-qr"
              onClick={buildQR}
              disabled={!issuerId || busy}
              className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
            >
              서명 + 인코딩 + QR 생성
            </button>
          </section>
        )}

        {/* 3. QR */}
        <section id="qr" className="space-y-3">
          {!screenshot && <h2 className="font-semibold">3. QR 코드</h2>}
          <div
            className={`grid gap-4 ${
              screenshot ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2"
            }`}
          >
            <div>
              <QRPanel pngBase64={pngBase64} themed={themed} issuer={issuer} />
              {pngBase64 && !screenshot && (
                <button
                  onClick={downloadQR}
                  className="mt-2 px-3 py-1 bg-slate-200 rounded text-xs"
                >
                  PNG 다운로드
                </button>
              )}
            </div>
            {!screenshot && (
              <div>
                <div className="text-xs text-slate-500 mb-1">
                  인코딩된 페이로드 (Bare/Themed 동일)
                </div>
                <pre className="text-[10px] bg-slate-100 p-2 rounded overflow-auto max-h-56 font-mono whitespace-pre-wrap break-all">
                  {encoded ?? "(QR 미생성)"}
                </pre>
              </div>
            )}
          </div>
        </section>

        {/* 4. Scan */}
        {!screenshot && (
          <section id="scan" className="space-y-3">
            <h2 className="font-semibold">4. 스캔</h2>
            <div className="flex flex-wrap gap-2 mb-2">
              {encoded && (
                <button
                  data-testid="skip-scan"
                  onClick={() => onScanned(encoded)}
                  className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
                >
                  지금 만든 QR 바로 해석 (스캔 건너뛰기)
                </button>
              )}
            </div>
            <QRScanner onResult={onScanned} />
            {scanned && (
              <div>
                <div className="text-xs text-slate-500">스캔된 페이로드:</div>
                <pre className="text-[10px] bg-slate-100 p-2 rounded font-mono whitespace-pre-wrap break-all">
                  {scanned}
                </pre>
              </div>
            )}
          </section>
        )}

        {/* 5. Resolve */}
        <section
          id="resolve"
          ref={resolveRef as React.RefObject<HTMLElement>}
          className={`space-y-3 transition-shadow rounded-lg ${
            pulse ? "ring-4 ring-emerald-300/60 ring-offset-2" : ""
          }`}
        >
          {!screenshot && (
            <>
              <h2 className="font-semibold">5. 접근레벨별 해석</h2>
              <p className="text-sm text-slate-600">
                동일한 QR 페이로드를 3개 레벨로 해석합니다.{" "}
                <em>Public</em>은 일반 QR 리더, <em>Authenticated</em>는 우리
                앱이 Layer B까지, <em>Verified</em>는 발급자 공개키로 Layer C
                서명까지 검증한 모습입니다.
              </p>
            </>
          )}

          {scanned && lastSig && (
            <div className="flex flex-wrap gap-2 items-center">
              {!tampered ? (
                <button
                  data-testid="tamper"
                  onClick={attemptTamper}
                  disabled={busy}
                  className="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
                >
                  🛠 위변조 시도
                </button>
              ) : (
                <button
                  data-testid="restore"
                  onClick={restoreOriginal}
                  disabled={busy}
                  className="px-3 py-1.5 bg-emerald-600 text-white rounded text-sm hover:bg-emerald-700 disabled:opacity-50"
                >
                  ↺ 원본 복원
                </button>
              )}
              <button
                onClick={() => resolveAll(scanned)}
                disabled={busy}
                className="px-3 py-1 bg-slate-200 rounded text-xs"
              >
                다시 해석
              </button>
              {tampered && (
                <span className="text-xs text-red-700 bg-red-50 border border-red-200 px-2 py-1 rounded">
                  ⚠ 현재 표시 중: 변조본 (Layer B 가 서명 후 변경됨)
                </span>
              )}
            </div>
          )}

          {!scanned && !screenshot && (
            <p className="text-xs text-slate-400 italic">
              스캔 또는 "지금 만든 QR 바로 해석" 후 결과가 여기 표시됩니다.
            </p>
          )}
          {scanned && (
            <div data-testid="resolve-grid" className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {LEVELS.map((lvl) => (
                <ResolveColumn
                  key={lvl}
                  level={lvl}
                  result={resolves[lvl]}
                  themed={themed}
                  issuer={issuer}
                  loading={busy && !resolves[lvl]}
                  hideDebug={screenshot}
                />
              ))}
            </div>
          )}
          {resolves.verified && !screenshot && (
            <p className="text-xs text-slate-500">
              Verified 결과:{" "}
              {resolves.verified.verified
                ? "서명 유효 — Layer B/C 노출"
                : "서명 무효 또는 미확인 — public 으로 안전 강등"}{" "}
              (Layer A 평문은{" "}
              <span className="font-mono">{resolves.verified.layer_a}</span>)
            </p>
          )}
        </section>

        {!screenshot && (
          <footer className="text-[11px] text-slate-400 pt-8 border-t border-slate-200">
            <p>
              <strong>특허 청구 대상</strong>: 단일 QR 페이로드 문자열 안의
              delimiter+base64(header+B+C) 3-layer 인코딩 + 내장 Ed25519 서명 +
              역할 기반 Resolver.
            </p>
            <p className="mt-1">
              <strong>응용 예시 (특허 청구 외)</strong>: 발급자 라우팅, 신뢰
              레지스트리, 시각 테마, 앱 카드 렌더링. 데이터는 두 표시 모드에서
              100% 동일.
            </p>
          </footer>
        )}
      </main>
    </div>
  );
}
