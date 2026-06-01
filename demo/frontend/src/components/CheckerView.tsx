import { useState } from "react";
import { api } from "../api/client";
import type { RedeemResponse, ResolveResult, TrustEntry } from "../types";
import QRScanner from "./QRScanner";
import ThemedCard from "./ThemedCard";

interface Props {
  trust: TrustEntry[];
}

// Gate consumes one use slot per scan. Kept as a constant so the redeem call
// and the "(used/limit)" banner denominator can never drift apart.
const MAX_USES = 1;

/**
 * Gate-checker full-screen mode. A scan is consumed once via POST /api/redeem
 * (max_uses=1) and surfaced as a large entry verdict, alongside the M2.5
 * schema card built from POST /api/resolve. The duplicate signal is the redeem
 * `status` (`already_used`), NOT use_count>1 — with max_uses=1 the store keeps
 * use_count at 1 and returns "already_used" on every subsequent scan.
 */
export default function CheckerView({ trust }: Props) {
  const [verdict, setVerdict] = useState<RedeemResponse | null>(null);
  const [resolved, setResolved] = useState<ResolveResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [scanned, setScanned] = useState<string | null>(null);
  // Bumping this remounts QRScanner so the camera restarts on "다음 스캔".
  const [scanKey, setScanKey] = useState(0);

  async function onResult(payload: string) {
    if (busy) return; // single-flight: ignore a re-fire while a scan is in flight
    setScanned(payload);
    setBusy(true);
    setErr(null);
    // allSettled: an undecodable string makes decode_layers throw 422, which
    // rejects redeem/resolve. Each branch is handled independently so one
    // rejection does not blank the other.
    const [r, rv] = await Promise.allSettled([
      api.redeem(payload, MAX_USES),
      api.resolve(payload, "verified"),
    ]);
    setVerdict(
      r.status === "fulfilled"
        ? r.value
        : { status: "invalid", use_count: 0 },
    );
    setResolved(rv.status === "fulfilled" ? rv.value : null);
    setBusy(false);
  }

  function nextScan() {
    setVerdict(null);
    setResolved(null);
    setScanned(null);
    setErr(null);
    setScanKey((k) => k + 1);
  }

  // Card data derivation mirrors ResolveColumn: an empty Layer B hex ("") is a
  // legal verified-empty outcome (→ empty `{}` card), distinct from absent (null).
  const layerBData =
    resolved && resolved.layer_b != null
      ? (resolved.layer_b_ticket ?? {})
      : null;
  const issuer =
    trust.find((t) => t.issuer_id === resolved?.issuer_id) ?? null;

  const isOk = verdict?.status === "ok";
  const isInvalid = verdict?.status === "invalid";
  const bannerClass = isOk
    ? "bg-emerald-600"
    : verdict
      ? "bg-red-600"
      : "bg-slate-700";

  let bannerText = "🛂 스캔 대기 중";
  if (verdict?.status === "ok") bannerText = "✅ 진본 · 입장";
  else if (verdict?.status === "already_used")
    bannerText = "⛔ 복제 / 재사용 · 차단";
  else if (verdict?.status === "invalid") bannerText = "❌ 위조 / 미등록";

  return (
    <main
      data-testid="checker-scan"
      className="min-h-screen bg-slate-100 px-4 py-5 mx-auto max-w-md space-y-4"
    >
      <div
        data-testid="checker-verdict"
        data-status={verdict?.status ?? "idle"}
        className={`rounded-xl px-5 py-6 text-center text-white shadow-lg ${bannerClass}`}
      >
        <div className="text-2xl sm:text-3xl font-extrabold leading-tight">
          {bannerText}
        </div>
        {verdict?.status === "already_used" && (
          <div
            data-testid="checker-usecount"
            className="mt-2 text-sm font-semibold opacity-90"
          >
            이미 사용됨 ({verdict.use_count}/{MAX_USES})
          </div>
        )}
      </div>

      {err && (
        <div className="rounded bg-red-50 text-red-700 px-3 py-2 text-sm">
          {err}
        </div>
      )}

      {verdict && (
        <div className="space-y-3">
          {isOk &&
            (issuer ? (
              <ThemedCard
                issuer={issuer}
                data={layerBData ?? {}}
                verified={resolved?.verified ?? true}
              />
            ) : null)}

          {verdict.status === "already_used" &&
            (issuer ? (
              <ThemedCard
                issuer={issuer}
                data={layerBData ?? {}}
                verified={resolved?.verified ?? true}
              />
            ) : null)}

          {isInvalid &&
            (issuer ? (
              <ThemedCard
                issuer={issuer}
                data={layerBData ?? {}}
                verified={false}
                locked
              />
            ) : (
              <div className="rounded-lg border-2 border-dashed border-red-300 bg-red-50 px-4 py-6 text-center text-red-700">
                <div className="text-base font-semibold">
                  미등록 발급자 / 위조 페이로드
                </div>
                <div className="text-xs mt-1 opacity-80">
                  신뢰 레지스트리에 없는 발급자이거나 서명이 유효하지 않습니다.
                </div>
              </div>
            ))}

          <button
            data-testid="checker-next"
            onClick={nextScan}
            className="w-full px-4 py-3 rounded-lg bg-slate-900 text-white text-base font-semibold active:bg-slate-700"
          >
            다음 스캔
          </button>
        </div>
      )}

      {!verdict && (
        <div className="space-y-3">
          {busy && (
            <p className="text-sm text-slate-500 text-center animate-pulse">
              판정 중…
            </p>
          )}
          <QRScanner key={scanKey} onResult={onResult} />
          {scanned && busy && (
            <pre className="text-[10px] bg-slate-200 p-2 rounded font-mono whitespace-pre-wrap break-all">
              {scanned}
            </pre>
          )}
        </div>
      )}
    </main>
  );
}
