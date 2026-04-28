import type { TrustEntry } from "../types";

interface Props {
  pngBase64: string | null;
  themed: boolean;
  issuer: TrustEntry | null;
}

/**
 * QR display panel. The Themed mode wraps the *same* PNG in a fandom-colored
 * card; the underlying QR data is identical between the two modes — this is
 * decoration only, not a different encoding.
 */
export default function QRPanel({ pngBase64, themed, issuer }: Props) {
  if (!pngBase64) {
    return (
      <div className="aspect-square w-full max-w-sm bg-slate-100 rounded grid place-items-center text-slate-400 text-sm">
        QR 미생성
      </div>
    );
  }
  const src = `data:image/png;base64,${pngBase64}`;

  if (!themed || !issuer) {
    return (
      <div className="bg-white p-3 rounded border border-slate-200 inline-block">
        <img
          src={src}
          alt="QR"
          className="block w-full max-w-sm"
          style={{ imageRendering: "pixelated" }}
        />
      </div>
    );
  }

  return (
    <div
      className="rounded-2xl p-5 inline-block shadow-lg"
      style={{ background: issuer.theme_color }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div
          className="inline-flex items-center justify-center rounded-full w-8 h-8 font-bold text-xs"
          style={{ background: issuer.accent_color, color: issuer.theme_color }}
        >
          {issuer.logo_text}
        </div>
        <div className="text-white text-sm font-semibold">
          {issuer.display_name}
        </div>
      </div>
      <div className="bg-white p-3 rounded-lg">
        <img
          src={src}
          alt="QR"
          className="block w-full max-w-sm"
          style={{ imageRendering: "pixelated" }}
        />
      </div>
      <div className="text-white/70 text-[10px] mt-2 font-mono">
        장식은 응용 레이어. QR 데이터는 Bare 모드와 100% 동일.
      </div>
    </div>
  );
}
