import type { ResolveResult, TrustEntry, AccessLevel } from "../types";
import { hexToStr } from "../api/client";
import ThemedCard, { parseLayerBJson } from "./ThemedCard";

interface Props {
  level: AccessLevel;
  result: ResolveResult | null;
  themed: boolean;
  issuer: TrustEntry | null;
  loading?: boolean;
  error?: string | null;
  hideDebug?: boolean;
}

const LEVEL_LABEL: Record<AccessLevel, string> = {
  public: "Public · 일반 QR 리더",
  authenticated: "Authenticated · 파싱된 메타데이터 (미검증)",
  verified: "Verified · 서명까지 확인",
};

const LEVEL_DESC: Record<AccessLevel, string> = {
  public: "표준 QR 리더가 보는 Layer A 평문",
  authenticated:
    "앱 출력 수준: Layer B를 파싱해 표시 (암호학적 인증 아님, verified=False)",
  verified: "+ 발급자 공개키로 Ed25519 서명 검증 (검증 재료는 선택 표시)",
};

function maskedRow(label: string, color: string) {
  return (
    <div className="rounded border border-dashed p-2 text-xs flex items-center gap-2 opacity-60">
      <span className="text-base">🔒</span>
      <span className="font-mono uppercase tracking-wide" style={{ color }}>
        {label}
      </span>
    </div>
  );
}

function PublicGenericReader({ layerA }: { layerA: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-slate-100 px-3 py-1.5 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>📷 Generic QR Reader</span>
        <span>—</span>
      </div>
      <div className="px-3 py-3 text-xs">
        <div className="text-[10px] text-slate-400 mb-1">Detected text:</div>
        <div className="font-mono break-all bg-slate-50 p-2 rounded border border-slate-200">
          {layerA}
        </div>
        <div className="text-[10px] text-slate-400 mt-2 italic">
          (이 리더는 Layer B/C의 존재를 모릅니다)
        </div>
      </div>
    </div>
  );
}

export default function ResolveColumn({
  level,
  result,
  themed,
  issuer,
  loading,
  error,
  hideDebug,
}: Props) {
  const themeBg = themed && issuer ? issuer.theme_color : "#0f172a";
  const themeAccent = themed && issuer ? issuer.accent_color : "#64748b";
  // Use `!= null` (not truthiness): an empty Layer B hex (`""`) is a legal
  // "verified-but-empty" outcome and must be distinguishable from "Layer B
  // absent" (null) per claim 7(iii). Truthy check would collapse both.
  const layerBData =
    result && result.layer_b != null
      ? parseLayerBJson(hexToStr(result.layer_b))
      : null;

  // Themed mode — render each level as an in-app screen
  if (themed && issuer && result) {
    return (
      <div className="rounded-lg overflow-hidden border border-slate-200 bg-white flex flex-col">
        <div
          className="px-3 py-2 text-white text-xs font-semibold flex items-center justify-between"
          style={{ background: themeBg }}
        >
          <span>{LEVEL_LABEL[level]}</span>
          {level === "verified" && (
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                result.verified
                  ? "bg-emerald-300 text-emerald-950"
                  : "bg-red-300 text-red-950"
              }`}
            >
              {result.verified ? "✓ VALID" : "✗ INVALID"}
            </span>
          )}
        </div>
        <div className="p-3 space-y-2 flex-1 bg-slate-50">
          <p className="text-[11px] text-slate-500">{LEVEL_DESC[level]}</p>
          {loading && <p className="text-xs text-slate-400">…해석 중</p>}
          {error && <p className="text-xs text-red-600">{error}</p>}

          {level === "public" && (
            <PublicGenericReader layerA={result.layer_a} />
          )}
          {level === "authenticated" &&
            (layerBData ? (
              <ThemedCard
                issuer={issuer}
                data={layerBData}
                verified={false}
              />
            ) : (
              <ThemedCard
                issuer={issuer}
                data={{}}
                verified={false}
                locked
              />
            ))}
          {level === "verified" &&
            (layerBData && result.verified ? (
              <ThemedCard
                issuer={issuer}
                data={layerBData}
                verified={true}
              />
            ) : (
              <ThemedCard
                issuer={issuer}
                data={layerBData ?? {}}
                verified={false}
                locked
              />
            ))}

          {level !== "public" && !hideDebug && (
            <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-100">
              issuer: <span className="font-mono">{result.issuer_id ?? "—"}</span>
              {result.routed_public_key && (
                <>
                  <br />
                  routed key:{" "}
                  <span className="font-mono">
                    {result.routed_public_key.slice(0, 16)}…
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Bare mode — raw text/hex (patent-eyeballs view)
  return (
    <div className="rounded-lg overflow-hidden border border-slate-200 bg-white flex flex-col">
      <div
        className="px-3 py-2 text-white text-xs font-semibold flex items-center justify-between"
        style={{ background: themeBg }}
      >
        <span>{LEVEL_LABEL[level]}</span>
        {result && level === "verified" && (
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              result.verified
                ? "bg-green-400 text-green-950"
                : "bg-red-400 text-red-950"
            }`}
          >
            {result.verified ? "✓ VALID" : "✗ INVALID"}
          </span>
        )}
      </div>
      <div className="p-3 space-y-2 text-sm flex-1">
        <p className="text-[11px] text-slate-500">{LEVEL_DESC[level]}</p>
        {loading && <p className="text-xs text-slate-400">…해석 중</p>}
        {error && <p className="text-xs text-red-600">{error}</p>}
        {result && (
          <>
            <div>
              <div className="text-[10px] uppercase text-slate-500 mb-0.5">
                Layer A
              </div>
              <div
                className="rounded p-2 text-xs break-all"
                style={{ background: `${themeAccent}22`, color: themeBg }}
              >
                {result.layer_a || <em className="opacity-60">empty</em>}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500 mb-0.5">
                Layer B
              </div>
              {result.layer_b != null ? (
                <div className="rounded p-2 text-xs break-all bg-orange-50 text-orange-900 border border-orange-200">
                  {result.layer_b === "" ? (
                    <em className="opacity-60">(empty — verified)</em>
                  ) : (
                    hexToStr(result.layer_b)
                  )}
                </div>
              ) : (
                maskedRow("hidden", "#ea580c")
              )}
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500 mb-0.5">
                Signature (diagnostic)
              </div>
              {result.signature != null ? (
                <div className="rounded p-2 text-[10px] break-all bg-green-50 text-green-900 font-mono border border-green-200">
                  {result.signature.slice(0, 32)}…
                </div>
              ) : (
                maskedRow("hidden", "#16a34a")
              )}
            </div>
            {level !== "public" && !hideDebug && (
              <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-100">
                issuer:{" "}
                <span className="font-mono">{result.issuer_id ?? "—"}</span>
                <br />
                routed key:{" "}
                <span className="font-mono">
                  {result.routed_public_key
                    ? result.routed_public_key.slice(0, 16) + "…"
                    : "—"}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
