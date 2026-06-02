import { useEffect, useMemo, useRef, useState } from "react";
import { api, strToHex } from "./api/client";
import type {
  AccessLevel,
  LayerBFormat,
  ResolveResult,
  SchemaInfo,
  TrustEntry,
} from "./types";
import StepNav from "./components/StepNav";
import IssuerPicker from "./components/IssuerPicker";
import MediaPicker from "./components/MediaPicker";
import SchemaForm from "./components/SchemaForm";
import QRPanel from "./components/QRPanel";
import QRScanner from "./components/QRScanner";
import ResolveColumn from "./components/ResolveColumn";
import CollectionPanel from "./components/CollectionPanel";
import CheckerView from "./components/CheckerView";

const STEPS = [
  { id: "issuer", label: "발급자 선택" },
  { id: "compose", label: "레이어 입력" },
  { id: "qr", label: "QR 생성" },
  { id: "scan", label: "스캔" },
  { id: "resolve", label: "접근레벨 비교" },
  { id: "collect", label: "방문 컬렉션" },
];

const LEVELS: AccessLevel[] = ["public", "authenticated", "verified"];

// Layer A labels are keyed by issuer, with an optional per-(issuer:kind)
// refinement so small media read distinctly (e.g. a wristband vs. a pass).
const LAYER_A_PRESETS: Record<string, string> = {
  "tigers-2026": "Tigers 정규시즌 입장권",
  "violet-fandom": "Violet 팬이벤트 패스",
  "comic-con-2026": "Comic Con 2026 출입증",
  "comic-con-2026:wristband": "Comic Con 팔찌",
};

// Structured Layer B field presets, keyed by `${issuer}:${kind}` with a
// `${kind}` fallback. Values are per-field strings (Record<string,string>) so
// they feed SchemaForm directly; field names match the backend schema models
// (layer_b_codec.py) exactly. `kind` is omitted — the schema selection fixes it.
type FieldValues = Record<string, string>;

const LAYER_B_PRESETS: Record<string, FieldValues> = {
  // baseball_ticket — existing Tigers data
  "tigers-2026:baseball_ticket": {
    event_id: "tigers-2026-042",
    serial: "T-000042",
    issued_at: "2026-04-20",
    section: "1루 응원석",
    seat: "12B",
    gate: "Gate 3",
    datetime: "2026-05-10",
    opponent: "Lions",
    holder: "FAN-2456",
  },
  // festival_pass — Violet fan-event pass
  "violet-fandom:festival_pass": {
    festival_id: "violet-fanmeet-2026",
    serial: "VIO-008812",
    issued_at: "2026-05-01",
    day: "Day 1 / Sat",
    zone: "Diamond Floor",
    tier: "Diamond Fan",
    gate: "Members Hall",
    holder: "VIO-008812",
  },
  // festival_pass — Comic Con day pass
  "comic-con-2026:festival_pass": {
    festival_id: "comic-con-2026",
    serial: "CC-VIP-1138",
    issued_at: "2026-03-15",
    day: "Day 1 / Sat",
    zone: "Hall H",
    tier: "VIP",
    gate: "West Entrance",
    holder: "코드네임 인비저블",
  },
  // wristband — Comic Con small-media band
  "comic-con-2026:wristband": {
    band_id: "CC-BAND-7741",
    serial: "WB-7741",
    issued_at: "2026-07-17",
    tier: "Weekend",
    valid_until: "2026-07-20",
    holder: "코드네임 인비저블",
  },
};

// Generic per-kind fallback so any (issuer, kind) without a bespoke preset
// still pre-fills sensible required fields.
const KIND_FALLBACK_PRESETS: Record<string, FieldValues> = {
  baseball_ticket: { event_id: "event-001", serial: "T-0001", issued_at: "2026-01-01" },
  festival_pass: { festival_id: "festival-001", serial: "F-0001", issued_at: "2026-01-01" },
  wristband: { band_id: "BAND-0001", serial: "WB-0001", issued_at: "2026-01-01" },
};

// Tamper presets feed the raw/empty path (strToHex → encode with original
// signature), so they are intentionally NOT codec-tagged: verification fails
// and Layer B collapses to null. Shapes mirror each schema for a coherent
// "forged" display in the bare view. One or two fields are visibly altered.
const TAMPER_PRESETS: Record<string, object> = {
  "tigers-2026:baseball_ticket": {
    event_id: "tigers-2026-042",
    serial: "T-000042",
    issued_at: "2026-04-20T09:00:00+09:00",
    section: "VVIP 스카이박스",
    seat: "FORGED",
    gate: "Gate 1",
    datetime: "2026-05-10T18:30:00+09:00",
    opponent: "Lions",
    holder: "STOLEN-0001",
  },
  "violet-fandom:festival_pass": {
    festival_id: "violet-fanmeet-2026",
    serial: "VIO-FORGED",
    issued_at: "2026-05-01T12:00:00+09:00",
    day: "Day 1 / Sat",
    zone: "Backstage ALL",
    tier: "★★★ Platinum ★★★",
    gate: "Members Hall",
    holder: "VIO-FORGED",
  },
  "comic-con-2026:festival_pass": {
    festival_id: "comic-con-2026",
    serial: "CC-FORGED",
    issued_at: "2026-03-15T10:00:00+09:00",
    day: "All Days",
    zone: "Hall H",
    tier: "STAFF ALL-ACCESS",
    gate: "West Entrance",
    holder: "FORGED ATTENDEE",
  },
  "comic-con-2026:wristband": {
    band_id: "CC-BAND-7741",
    serial: "WB-FORGED",
    issued_at: "2026-07-17T09:00:00+09:00",
    tier: "ALL-ACCESS",
    valid_until: "2026-12-31T23:59:59+09:00",
    holder: "FORGED",
  },
};

const presetKey = (id: string | null, kind: string | null) =>
  id && kind ? `${id}:${kind}` : "";

const presetFields = (id: string | null, kind: string | null): FieldValues =>
  kind
    ? {
        ...(KIND_FALLBACK_PRESETS[kind] ?? {}),
        ...(LAYER_B_PRESETS[presetKey(id, kind)] ?? {}),
      }
    : {};

const presetLayerA = (id: string | null, kind: string | null) => {
  if (!id) return "";
  return LAYER_A_PRESETS[presetKey(id, kind)] ?? LAYER_A_PRESETS[id] ?? "";
};

const presetTamper = (id: string | null, kind: string | null) =>
  JSON.stringify(TAMPER_PRESETS[presetKey(id, kind)] ?? {}, null, 2);

export default function App() {
  const [appMode, setAppMode] = useState<"builder" | "checker">("builder");
  const [active, setActive] = useState("issuer");
  const [trust, setTrust] = useState<TrustEntry[]>([]);
  const [schemas, setSchemas] = useState<SchemaInfo[]>([]);
  const [issuerId, setIssuerId] = useState<string | null>(null);
  const issuer = useMemo(
    () => trust.find((t) => t.issuer_id === issuerId) ?? null,
    [trust, issuerId],
  );
  // The schema kind (media) currently being issued. Defaults to the issuer's
  // first allowed schema; Comic Con (2 schemas) can switch via MediaPicker.
  const [schemaKind, setSchemaKind] = useState<string | null>(null);
  const schemaInfo = useMemo(
    () => schemas.find((s) => s.kind === schemaKind) ?? null,
    [schemas, schemaKind],
  );

  const [layerAMessage, setLayerAMessage] = useState("");
  // Structured issue input as per-field values, rendered by SchemaForm.
  const [layerBFields, setLayerBFields] = useState<Record<string, string>>({});
  // Raw JSON textarea — used ONLY in rawMode (verified-empty + tamper demos).
  const [layerBJson, setLayerBJson] = useState("{}");
  const [tamperedJson, setTamperedJson] = useState("{}");

  const [layerBFormat, setLayerBFormat] = useState<LayerBFormat>("json");
  // raw/empty mode preserves the strToHex path used for verified-empty, tamper,
  // and arbitrary-Layer-B demos. When on, the format selector is ignored.
  const [rawMode, setRawMode] = useState(false);

  const [encoded, setEncoded] = useState<string | null>(null);
  const [pngBase64, setPngBase64] = useState<string | null>(null);
  const [lastSig, setLastSig] = useState<string | null>(null);
  const [lastLayerBHex, setLastLayerBHex] = useState<string | null>(null);
  const [layerBBytes, setLayerBBytes] = useState<number | null>(null);
  const [payloadBytes, setPayloadBytes] = useState<number | null>(null);
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

  // bootstrap trust list + schema catalog
  useEffect(() => {
    Promise.all([api.trustList(), api.schemas()])
      .then(([t, s]) => {
        setTrust(t.entries);
        setSchemas(s.schemas);
        if (t.entries.length && !issuerId) {
          const first = t.entries[0];
          const kind = first.allowed_schemas[0] ?? null;
          setIssuerId(first.issuer_id);
          setSchemaKind(kind);
          setLayerAMessage(presetLayerA(first.issuer_id, kind));
          setLayerBFields(presetFields(first.issuer_id, kind));
          setTamperedJson(presetTamper(first.issuer_id, kind));
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
    const entry = trust.find((t) => t.issuer_id === id);
    const kind = entry?.allowed_schemas[0] ?? null;
    setIssuerId(id);
    setSchemaKind(kind);
    setLayerAMessage(presetLayerA(id, kind));
    setLayerBFields(presetFields(id, kind));
    setTamperedJson(presetTamper(id, kind));
    setActive("compose");
  }

  // Switch media (schema) for the current issuer — reset the form to that
  // schema's preset so fields match the new kind.
  function pickMedia(kind: string) {
    setSchemaKind(kind);
    setLayerAMessage(presetLayerA(issuerId, kind));
    setLayerBFields(presetFields(issuerId, kind));
    setTamperedJson(presetTamper(issuerId, kind));
  }

  function reset() {
    setEncoded(null);
    setPngBase64(null);
    setScanned(null);
    setResolves({ public: null, authenticated: null, verified: null });
    setLastSig(null);
    setLastLayerBHex(null);
    setLayerBBytes(null);
    setPayloadBytes(null);
    setTampered(false);
    setErr(null);
    setActive("issuer");
    if (issuerId) {
      setLayerAMessage(presetLayerA(issuerId, schemaKind));
      setLayerBFields(presetFields(issuerId, schemaKind));
      setTamperedJson(presetTamper(issuerId, schemaKind));
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function flashToast(msg: string) {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2400);
  }

  // StepNav click: mark active AND scroll the section into view. The nav lives
  // in a long single-page layout, so without this the tab highlights but the
  // viewport never moves. scroll-margin-top (index.css) clears the sticky header.
  function goToStep(id: string) {
    setActive(id);
    requestAnimationFrame(() =>
      document
        .getElementById(id)
        ?.scrollIntoView({ behavior: "smooth", block: "start" }),
    );
  }

  async function buildQR() {
    if (!issuerId) return;
    setBusy(true);
    setErr(null);
    setScanned(null);
    setResolves({ public: null, authenticated: null, verified: null });
    setTampered(false);
    try {
      let layerBHex: string;
      let layerBByteCount: number;
      if (rawMode) {
        // raw/empty path: preserves verified-empty (empty Layer B) and
        // arbitrary-Layer-B demos. Format selector is ignored here.
        layerBHex = strToHex(layerBJson);
        layerBByteCount = layerBHex.length / 2;
      } else {
        // structured path: build the ticket object from the per-field form
        // values + the selected schema kind, then encode via the codec in the
        // selected format. byte_size is the demo's headline metric.
        if (!schemaKind) {
          setErr("매체(스키마)를 먼저 선택하세요.");
          return;
        }
        const ticketObj = { kind: schemaKind, ...layerBFields };
        const lb = await api.encodeLayerB(ticketObj, layerBFormat, schemaKind);
        layerBHex = lb.layer_b_hex;
        layerBByteCount = lb.byte_size;
      }
      const sig = await api.trustSign(issuerId, layerA, layerBHex);
      const enc = await api.encode(layerA, layerBHex, sig.signature);
      const img = await api.qrImage(enc.encoded, { box_size: 14, border: 4 });
      setLastSig(sig.signature);
      setLastLayerBHex(layerBHex);
      setLayerBBytes(layerBByteCount);
      setPayloadBytes(new TextEncoder().encode(enc.encoded).length);
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
        <div className="max-w-5xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
          <div className="flex items-center gap-2 shrink-0">
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
            {appMode === "checker" ? (
              <button
                data-testid="mode-builder"
                onClick={() => setAppMode("builder")}
                className="px-3 py-1.5 rounded text-xs bg-slate-900 text-white hover:bg-slate-700"
              >
                ← 발급자 데모
              </button>
            ) : (
              <>
                <button
                  data-testid="mode-checker"
                  onClick={() => setAppMode("checker")}
                  className="px-2.5 py-1.5 rounded text-xs border border-emerald-300 bg-emerald-50 text-emerald-800 hover:border-emerald-500"
                >
                  🛂 검표원 모드
                </button>
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
              </>
            )}
          </div>
        </div>
      </header>

      {appMode === "checker" ? (
        <CheckerView trust={trust} />
      ) : (
        <>
      {toast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white text-sm px-4 py-2 rounded-full shadow-lg pointer-events-none">
          {toast}
        </div>
      )}

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        {!screenshot && (
          <StepNav steps={STEPS} activeId={active} onSelect={goToStep} />
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
            {/* Media (schema) picker — shown only when the issuer may emit
                more than one schema (e.g. Comic Con: festival_pass + wristband).
                Single-schema issuers auto-select and skip the picker. */}
            {issuer && issuer.allowed_schemas.length > 1 && (
              <MediaPicker
                schemas={schemas}
                allowed={issuer.allowed_schemas}
                selected={schemaKind}
                onSelect={pickMedia}
              />
            )}
            <div className="block text-sm">
              <span className="block text-xs text-slate-500 mb-1">
                Layer B (
                {rawMode
                  ? "임의 바이트 (raw)"
                  : `${schemaKind ?? "schema"} 필드`}
                )
              </span>
              {rawMode ? (
                <textarea
                  data-testid="layer-b-raw"
                  value={layerBJson}
                  onChange={(e) => setLayerBJson(e.target.value)}
                  rows={6}
                  className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs font-mono"
                />
              ) : schemaInfo ? (
                <SchemaForm
                  schema={schemaInfo}
                  value={layerBFields}
                  onChange={setLayerBFields}
                />
              ) : (
                <p className="text-xs text-slate-400 italic">스키마 로딩 중…</p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-1.5 text-xs text-slate-600">
                <input
                  data-testid="raw-mode-toggle"
                  type="checkbox"
                  checked={rawMode}
                  onChange={(e) => setRawMode(e.target.checked)}
                  className="rounded border-slate-300"
                />
                raw / empty Layer B 모드 (verified-empty · 변조 데모용)
              </label>
              <div
                className={`flex items-center gap-1 ${
                  rawMode ? "opacity-40 pointer-events-none" : ""
                }`}
              >
                <span className="text-xs text-slate-500 mr-1">Layer B 포맷:</span>
                {(
                  [
                    ["json", "JSON"],
                    ["cbor", "CBOR"],
                    ["cbor_aggr", "CBOR aggr."],
                  ] as [LayerBFormat, string][]
                ).map(([fmt, label]) => (
                  <label
                    key={fmt}
                    className={`px-2 py-1 rounded text-xs border cursor-pointer ${
                      layerBFormat === fmt
                        ? "bg-slate-900 text-white border-slate-900"
                        : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
                    }`}
                  >
                    <input
                      data-testid={`format-${fmt}`}
                      type="radio"
                      name="layer-b-format"
                      value={fmt}
                      checked={layerBFormat === fmt}
                      onChange={() => setLayerBFormat(fmt)}
                      className="sr-only"
                    />
                    {label}
                  </label>
                ))}
              </div>
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
              {pngBase64 && layerBBytes != null && (
                <div
                  data-testid="byte-size"
                  className="mt-2 inline-flex items-center gap-2 rounded-lg bg-slate-900 text-white px-3 py-1.5 text-xs"
                >
                  <span className="font-semibold">
                    Layer B {layerBBytes} B
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="uppercase tracking-wide text-emerald-300 font-mono">
                    {rawMode ? "raw" : layerBFormat}
                  </span>
                  {payloadBytes != null && (
                    <>
                      <span className="text-slate-400">·</span>
                      <span className="text-slate-300">
                        전체 페이로드 {payloadBytes} B
                      </span>
                    </>
                  )}
                </div>
              )}
              {pngBase64 && !screenshot && (
                <button
                  onClick={downloadQR}
                  className="mt-2 px-3 py-1 bg-slate-200 rounded text-xs block"
                >
                  PNG 다운로드
                </button>
              )}
              {pngBase64 && !screenshot && !rawMode && (
                <p className="mt-1 text-[10px] text-slate-400">
                  포맷을 바꿔 다시 생성하면 Layer B 바이트 수가 달라집니다 (JSON →
                  CBOR → CBOR aggr.).
                </p>
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

        {/* 6. Collection */}
        <section id="collect" className="space-y-3">
          {!screenshot && (
            <>
              <h2 className="font-semibold">6. 방문 성취 컬렉션 (스탬프러시)</h2>
              <p className="text-sm text-slate-600">
                현장 부스에서 <em>내 티켓을 제시</em>하면 — 진짜 회원이 진짜
                거기 갔을 때만 — 부스가 방문 마커를 서명 발급합니다. 뱃지는 신원
                노출 없이 내 것으로 누적되고, 같은 컨텐츠라도 부스(서울/부산
                등)가 다르면 별도 뱃지입니다.
              </p>
            </>
          )}
          <CollectionPanel
            ticketPayload={encoded}
            trust={trust}
            screenshot={screenshot}
          />
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
        </>
      )}
    </div>
  );
}
