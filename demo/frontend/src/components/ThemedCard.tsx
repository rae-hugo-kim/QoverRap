import { useEffect, useState } from "react";
import type { TrustEntry } from "../types";

// Cards read from the backend-decoded Layer B dict, so they are
// format-agnostic (json / cbor / cbor_aggr all decode to this shape) and
// schema-agnostic at the field level. The union of every schema's fields is
// flattened into one optional-string accessor; the active card reads only the
// fields its `kind` defines. `kind` is the discriminator that selects the card.
type CardData = {
  kind?: string;
  // baseball_ticket
  event_id?: string;
  section?: string;
  seat?: string;
  datetime?: string;
  opponent?: string;
  // festival_pass
  festival_id?: string;
  day?: string;
  zone?: string;
  // wristband
  band_id?: string;
  valid_until?: string;
  // shared
  serial?: string;
  issued_at?: string;
  gate?: string;
  tier?: string;
  holder?: string;
};

// ISO timestamps are displayed at a fixed timezone so the same ticket reads
// identically across formats: aggressive-CBOR normalizes to a UTC ISO string
// while json/cbor keep the original offset, but both denote the same instant.
// Pinning to Asia/Seoul makes that instant render the same wall-clock time.
const _SEOUL_DATETIME = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  dateStyle: "medium",
  timeStyle: "short",
});

function fmtDateTime(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : _SEOUL_DATETIME.format(d);
}

interface Props {
  issuer: TrustEntry;
  data: CardData;
  verified: boolean;
  locked?: boolean;
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

/**
 * Liveness strip — a per-second clock plus a flowing shimmer band. Its only
 * job is to make a still screenshot visibly stale on the spot: the printed
 * timestamp freezes while a live screen keeps ticking (PRD §7.5). Rendered in
 * every mode (including screenshot mode) so the captured frame carries a clock.
 */
function LivenessStrip({ accent }: { accent: string }) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  const hhmmss = now.toLocaleTimeString("ko-KR", { hour12: false });
  return (
    <div className="relative z-[1] overflow-hidden border-t border-white/15 px-4 py-1.5 flex items-center justify-between text-[10px]">
      <span
        className="absolute inset-0 opacity-30 animate-card-shimmer"
        style={{
          background: `linear-gradient(110deg, transparent 35%, ${accent}, transparent 65%)`,
          backgroundSize: "200% 100%",
        }}
        aria-hidden
      />
      <span className="relative font-mono tracking-wider opacity-80">
        LIVE · 실시간 검증 화면
      </span>
      <span
        data-testid="liveness-clock"
        className="relative font-mono font-bold tabular-nums"
        style={{ color: accent }}
      >
        {hhmmss}
      </span>
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

/* --- Per-issuer cards ----------------------------------------------------- */

function BaseballTicketCard({ issuer, data, verified }: Props) {
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
        <div className="col-span-2">
          <div className="text-[9px] uppercase opacity-60">DATETIME</div>
          <div className="font-semibold">{fmtDateTime(data.datetime)}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">SECTION</div>
          <div className="font-semibold">{data.section || "—"}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">SEAT</div>
          <div
            className="font-extrabold text-3xl leading-none"
            style={{ color: issuer.accent_color }}
          >
            {data.seat || "—"}
          </div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">GATE</div>
          <div className="font-semibold">{data.gate || "—"}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase opacity-60">OPPONENT</div>
          <div className="font-semibold">vs {data.opponent || "—"}</div>
        </div>
      </div>
      <div
        className="px-4 py-2 text-[10px] opacity-70 font-mono border-t border-dashed flex justify-between relative z-[1]"
        style={{ borderColor: issuer.accent_color }}
      >
        <span>HOLDER · {data.holder || "—"}</span>
        <span>{data.serial || "NON-TRANSFERABLE"}</span>
      </div>
      <LivenessStrip accent={issuer.accent_color} />
    </div>
  );
}

function FestivalPassCard({ issuer, data, verified }: Props) {
  // Halftone dots via radial gradient pattern (ported from the Comic Con badge
  // visual). Shared by every festival_pass issuer (Violet, Comic Con); the
  // issuer theme color + logo carries the brand. Reads the real FestivalPass
  // fields: day / zone / tier / gate / holder.
  const halftone = `radial-gradient(${issuer.accent_color}40 1px, transparent 1.5px)`;
  return (
    <div
      className="relative rounded-xl overflow-hidden shadow-xl"
      style={{
        background: `${halftone}, linear-gradient(160deg, ${issuer.theme_color} 0%, #001a33 100%)`,
        backgroundSize: "8px 8px, 100% 100%",
        color: "#fff",
      }}
    >
      <div className="p-4 relative">
        <StarBurstIcon color={issuer.accent_color} />
        <VerifiedStamp verified={verified} />
        <div
          className="rounded-md px-2 py-0.5 inline-flex items-center gap-1.5 text-[10px] font-extrabold tracking-widest mb-3 relative z-[1]"
          style={{ background: issuer.accent_color, color: issuer.theme_color }}
        >
          <span
            className="grid place-items-center w-4 h-4 rounded-full text-[8px]"
            style={{ background: issuer.theme_color, color: issuer.accent_color }}
          >
            {issuer.logo_text.slice(0, 2)}
          </span>
          ★ FESTIVAL PASS ★
        </div>
        <div className="text-2xl font-extrabold leading-tight mb-0.5 relative z-[1]">
          {data.holder || "ATTENDEE"}
        </div>
        <div className="text-xs opacity-70 mb-3 relative z-[1]">
          {issuer.display_name}
        </div>
        <div className="space-y-1 text-sm relative z-[1]">
          <div className="flex justify-between">
            <span className="text-[10px] uppercase opacity-60">DAY</span>
            <span className="font-semibold">{data.day || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[10px] uppercase opacity-60">ZONE</span>
            <span className="font-bold" style={{ color: issuer.accent_color }}>
              {data.zone || "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[10px] uppercase opacity-60">TIER</span>
            <span className="font-semibold">{data.tier || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[10px] uppercase opacity-60">GATE</span>
            <span className="font-semibold">{data.gate || "—"}</span>
          </div>
        </div>
      </div>
      <LivenessStrip accent={issuer.accent_color} />
    </div>
  );
}

function WristbandCard({ issuer, data, verified }: Props) {
  // Small-media wristband: minimal, compact, sized like a printed band.
  // Reads the real Wristband fields: band_id / tier / valid_until / holder.
  return (
    <div
      className="relative rounded-full overflow-hidden text-white shadow-xl"
      style={{
        background: `linear-gradient(90deg, ${issuer.theme_color} 0%, ${issuer.accent_color}55 50%, ${issuer.theme_color} 100%)`,
      }}
    >
      <SparkleIcon color={issuer.accent_color} />
      <VerifiedStamp verified={verified} />
      <div className="px-5 py-3 relative z-[1]">
        <div className="flex items-center gap-2 mb-1.5">
          <div
            className="w-7 h-7 rounded-full grid place-items-center font-extrabold text-[9px] ring-2 ring-white/40"
            style={{ background: issuer.accent_color, color: issuer.theme_color }}
          >
            {issuer.logo_text}
          </div>
          <div
            className="text-[9px] uppercase tracking-[0.3em]"
            style={{ color: issuer.accent_color }}
          >
            WRISTBAND
          </div>
        </div>
        <div className="flex items-center justify-between gap-3 text-sm">
          <div>
            <div className="text-[9px] uppercase opacity-60">BAND</div>
            <div className="font-mono font-bold">{data.band_id || "—"}</div>
          </div>
          <div className="text-right">
            <div className="text-[9px] uppercase opacity-60">TIER</div>
            <div
              className="font-extrabold tracking-wide"
              style={{ color: issuer.accent_color }}
            >
              {data.tier || "—"}
            </div>
          </div>
        </div>
        <div className="mt-1.5 flex items-center justify-between gap-3 text-[10px] opacity-80 font-mono border-t border-white/15 pt-1.5">
          <span>VALID UNTIL · {fmtDateTime(data.valid_until)}</span>
          <span>{data.holder || "—"}</span>
        </div>
      </div>
      <LivenessStrip accent={issuer.accent_color} />
    </div>
  );
}

function EmptyPayloadCard({ issuer, verified }: Props) {
  // No structured Layer B (verified-empty / raw / undecodable). Preserves the
  // claim 7(iii) verified-empty path: render a calm themed card stating the
  // payload carries no structured fields rather than crashing or blanking.
  return (
    <div
      className="relative rounded-lg overflow-hidden text-white shadow-xl"
      style={{
        background: `linear-gradient(135deg, ${issuer.theme_color} 0%, #0f172a 100%)`,
      }}
    >
      <VerifiedStamp verified={verified} />
      <div className="px-4 py-5 relative z-[1] flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-full grid place-items-center font-extrabold text-xs ring-2 ring-white/30"
          style={{ background: issuer.accent_color, color: issuer.theme_color }}
        >
          {issuer.logo_text}
        </div>
        <div>
          <div className="text-sm font-semibold">{issuer.display_name}</div>
          <div className="text-[11px] opacity-70 mt-0.5">구조화 페이로드 없음</div>
          <div className="text-[10px] opacity-50 mt-1 leading-relaxed">
            Layer B에 스키마 필드가 없습니다 (verified-empty · raw 바이트).
          </div>
        </div>
      </div>
      <LivenessStrip accent={issuer.accent_color} />
    </div>
  );
}

export default function ThemedCard(props: Props) {
  if (props.locked) return <LockedCover issuer={props.issuer} />;
  // Switch on the decoded Layer B `kind` (the schema discriminator), NOT the
  // issuer — one issuer (Comic Con) may emit multiple media, and each renders
  // its own card. Issuer theme color/logo still skins every card.
  switch (props.data.kind) {
    case "baseball_ticket":
      return <BaseballTicketCard {...props} />;
    case "festival_pass":
      return <FestivalPassCard {...props} />;
    case "wristband":
      return <WristbandCard {...props} />;
    default:
      // No structured Layer B (verified-empty / raw / undecodable).
      return <EmptyPayloadCard {...props} />;
  }
}
