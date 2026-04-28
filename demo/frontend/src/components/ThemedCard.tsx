import type { TrustEntry } from "../types";

type CardData = Record<string, unknown>;

interface Props {
  issuer: TrustEntry;
  data: CardData;
  verified: boolean;
  locked?: boolean;
}

function safeParse(s: string | null | undefined): CardData {
  if (!s) return {};
  try {
    const v = JSON.parse(s);
    return typeof v === "object" && v !== null ? (v as CardData) : {};
  } catch {
    return { _raw: s };
  }
}

export function parseLayerBJson(s: string | null | undefined): CardData {
  return safeParse(s);
}

function VerifiedStamp({ verified }: { verified: boolean }) {
  return (
    <div
      className={`absolute right-3 top-3 px-2 py-1 rounded-full text-[10px] font-bold tracking-wider border-2 rotate-6 z-10 ${
        verified
          ? "border-emerald-400 text-emerald-200 bg-emerald-950/50"
          : "border-amber-400 text-amber-200 bg-amber-950/50"
      }`}
    >
      {verified ? "✓ ISSUER VERIFIED" : "UNVERIFIED"}
    </div>
  );
}

function LockedCover({ issuer }: { issuer: TrustEntry }) {
  return (
    <div
      className="rounded-lg p-5 text-center relative overflow-hidden"
      style={{ background: issuer.theme_color, color: "#fff" }}
    >
      <div className="text-3xl mb-1">🔒</div>
      <div className="text-xs opacity-80 leading-relaxed">
        {issuer.display_name} 앱으로 스캔하면
        <br />
        잠금이 풀립니다
      </div>
      <div className="text-[10px] opacity-50 mt-2 font-mono">
        Layer B / C 잠금
      </div>
    </div>
  );
}

/* --- Decorative SVGs ----------------------------------------------------- */

function BaseballIcon({ color }: { color: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      stroke={color}
      strokeWidth="2"
      className="w-12 h-12 opacity-30 absolute -bottom-2 -right-2 rotate-12"
      aria-hidden
    >
      <circle cx="24" cy="24" r="18" />
      <path d="M10 14c4 5 4 15 0 20" />
      <path d="M38 14c-4 5-4 15 0 20" />
    </svg>
  );
}

function SparkleIcon({ color }: { color: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill={color}
      className="w-10 h-10 opacity-25 absolute top-3 right-12"
      aria-hidden
    >
      <path d="M24 4l3 12 12 3-12 3-3 12-3-12-12-3 12-3z" />
      <circle cx="40" cy="40" r="2" />
      <circle cx="8" cy="36" r="1.5" />
    </svg>
  );
}

function StarBurstIcon({ color }: { color: string }) {
  return (
    <svg
      viewBox="0 0 60 60"
      fill="none"
      stroke={color}
      strokeWidth="2"
      className="w-14 h-14 opacity-25 absolute -top-2 -right-2"
      aria-hidden
    >
      <path d="M30 4l5 11 12 1-9 8 3 12-11-7-11 7 3-12-9-8 12-1z" />
    </svg>
  );
}

/* --- Per-issuer cards ---------------------------------------------------- */

function TigersTicket({ issuer, data, verified }: Props) {
  return (
    <div
      className="relative rounded-lg overflow-hidden text-white shadow-xl"
      style={{
        background: `linear-gradient(135deg, ${issuer.theme_color} 0%, #2a1a00 100%)`,
      }}
    >
      <BaseballIcon color={issuer.accent_color} />
      <VerifiedStamp verified={verified} />
      <div
        className="px-4 py-3 flex items-center gap-3 border-b-2 border-dashed relative z-[1]"
        style={{ borderColor: issuer.accent_color }}
      >
        <div
          className="w-10 h-10 rounded-full grid place-items-center font-extrabold text-xs ring-2"
          style={{
            background: issuer.accent_color,
            color: issuer.theme_color,
            boxShadow: `0 0 0 4px ${issuer.theme_color}`,
          }}
        >
          {issuer.logo_text}
        </div>
        <div>
          <div
            className="text-[9px] uppercase tracking-[0.25em]"
            style={{ color: issuer.accent_color }}
          >
            BASEBALL TICKET
          </div>
          <div className="text-sm font-semibold">{issuer.display_name}</div>
        </div>
      </div>
      <div className="px-4 py-3 grid grid-cols-2 gap-y-2 gap-x-3 text-sm relative z-[1]">
        <div>
          <div className="text-[9px] uppercase opacity-60">DATE</div>
          <div className="font-semibold">{String(data.date ?? "—")}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">TIME</div>
          <div className="font-semibold">{String(data.time ?? "—")}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">SECTION</div>
          <div className="font-semibold">{String(data.section ?? "—")}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">SEAT</div>
          <div
            className="font-extrabold text-3xl leading-none"
            style={{ color: issuer.accent_color }}
          >
            {String(data.seat ?? "—")}
          </div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">GATE</div>
          <div className="font-semibold">{String(data.gate ?? "—")}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">OPPONENT</div>
          <div className="font-semibold">vs {String(data.opponent ?? "—")}</div>
        </div>
      </div>
      <div
        className="px-4 py-2 text-[10px] opacity-70 font-mono border-t border-dashed flex justify-between relative z-[1]"
        style={{ borderColor: issuer.accent_color }}
      >
        <span>HOLDER · {String(data.holder ?? "—")}</span>
        <span>NON-TRANSFERABLE</span>
      </div>
    </div>
  );
}

function VioletMembership({ issuer, data, verified }: Props) {
  return (
    <div
      className="relative rounded-2xl overflow-hidden text-white p-4 shadow-xl"
      style={{
        background: `radial-gradient(circle at 80% 0%, ${issuer.accent_color}30, transparent 60%), linear-gradient(135deg, ${issuer.theme_color} 0%, #1f0033 100%)`,
      }}
    >
      <SparkleIcon color={issuer.accent_color} />
      <VerifiedStamp verified={verified} />
      <div className="flex items-center gap-3 mb-3 relative z-[1]">
        <div
          className="w-12 h-12 rounded-full grid place-items-center font-extrabold text-lg ring-2 ring-white/40"
          style={{ background: issuer.accent_color, color: issuer.theme_color }}
        >
          {issuer.logo_text}
        </div>
        <div>
          <div
            className="text-[9px] uppercase tracking-[0.25em]"
            style={{ color: issuer.accent_color }}
          >
            FAN MEMBERSHIP
          </div>
          <div className="text-base font-semibold">{issuer.display_name}</div>
        </div>
      </div>
      <div className="space-y-2 text-sm relative z-[1]">
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] uppercase opacity-60">TIER</span>
          <span
            className="text-lg font-extrabold tracking-wide"
            style={{ color: issuer.accent_color }}
          >
            ✦ {String(data.tier ?? "—")} ✦
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] uppercase opacity-60">MEMBER ID</span>
          <span className="font-mono text-xs">
            {String(data.member_id ?? "—")}
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] uppercase opacity-60">SINCE</span>
          <span className="text-xs">{String(data.since ?? "—")}</span>
        </div>
      </div>
      <div className="mt-3 rounded-lg bg-white/10 backdrop-blur p-2.5 text-xs relative z-[1]">
        <div className="text-[10px] uppercase opacity-60 mb-0.5">
          🎬 EXCLUSIVE NOW
        </div>
        <div className="font-medium">{String(data.exclusive ?? "—")}</div>
      </div>
    </div>
  );
}

function ComicConBadge({ issuer, data, verified }: Props) {
  // Halftone dots via radial gradient pattern
  const halftone = `radial-gradient(${issuer.accent_color}40 1px, transparent 1.5px)`;
  return (
    <div
      className="relative rounded-xl overflow-hidden p-4 shadow-xl"
      style={{
        background: `${halftone}, linear-gradient(160deg, ${issuer.theme_color} 0%, #001a33 100%)`,
        backgroundSize: "8px 8px, 100% 100%",
        color: "#fff",
      }}
    >
      <StarBurstIcon color={issuer.accent_color} />
      <VerifiedStamp verified={verified} />
      <div
        className="rounded-md px-2 py-0.5 inline-block text-[10px] font-extrabold tracking-widest mb-3 relative z-[1]"
        style={{ background: issuer.accent_color, color: issuer.theme_color }}
      >
        ★ {String(data.badge ?? "ATTENDEE").toUpperCase()} ★
      </div>
      <div className="text-2xl font-extrabold leading-tight mb-0.5 relative z-[1]">
        {String(data.name ?? "ATTENDEE")}
      </div>
      <div className="text-xs opacity-70 mb-3 relative z-[1]">
        {issuer.display_name}
      </div>
      <div className="space-y-1 text-sm relative z-[1]">
        <div className="flex justify-between">
          <span className="text-[10px] uppercase opacity-60">DAY</span>
          <span className="font-semibold">{String(data.day ?? "—")}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[10px] uppercase opacity-60">TRACK</span>
          <span
            className="font-bold"
            style={{ color: issuer.accent_color }}
          >
            {String(data.track ?? "—")}
          </span>
        </div>
        <div className="rounded-md bg-white/10 backdrop-blur px-2 py-1 mt-2">
          <div className="text-[10px] uppercase opacity-60 mb-0.5">PANEL</div>
          <div className="text-xs font-medium">
            {String(data.panel ?? "—")}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ThemedCard(props: Props) {
  if (props.locked) return <LockedCover issuer={props.issuer} />;
  switch (props.issuer.issuer_id) {
    case "tigers-2026":
      return <TigersTicket {...props} />;
    case "violet-fandom":
      return <VioletMembership {...props} />;
    case "comic-con-2026":
      return <ComicConBadge {...props} />;
    default:
      return (
        <div
          className="rounded p-3 text-xs text-white"
          style={{ background: props.issuer.theme_color }}
        >
          {JSON.stringify(props.data)}
        </div>
      );
  }
}
