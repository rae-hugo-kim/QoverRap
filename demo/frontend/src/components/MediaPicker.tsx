import type { SchemaInfo } from "../types";

interface Props {
  /** Full schema catalog from GET /api/schemas. */
  schemas: SchemaInfo[];
  /** Schema kinds the selected issuer may emit (TrustEntry.allowed_schemas). */
  allowed: string[];
  selected: string | null;
  onSelect: (kind: string) => void;
}

// Korean media labels keyed by schema kind. Falls back to the raw kind.
const MEDIA_LABELS: Record<string, string> = {
  baseball_ticket: "야구 입장권",
  festival_pass: "페스티벌 패스",
  wristband: "팔찌 (소형 매체)",
};

const MEDIA_EMOJI: Record<string, string> = {
  baseball_ticket: "⚾",
  festival_pass: "🎫",
  wristband: "🪢",
};

/**
 * Media (schema) picker. Chips are limited to the issuer's allowed schemas.
 * The compose section only mounts this when allowed.length > 1, but the
 * single-chip rendering is kept here too so the component stays self-contained.
 */
export default function MediaPicker({ schemas, allowed, selected, onSelect }: Props) {
  // Preserve the catalog order, filtered to what this issuer may emit.
  const options = schemas.filter((s) => allowed.includes(s.kind));
  if (options.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-slate-500 mr-1">발급 매체:</span>
      {options.map((s) => {
        const active = s.kind === selected;
        const label = MEDIA_LABELS[s.kind] ?? s.kind;
        const emoji = MEDIA_EMOJI[s.kind] ?? "🎟";
        return (
          <button
            key={s.kind}
            data-testid={`media-${s.kind}`}
            onClick={() => onSelect(s.kind)}
            className={`px-3 py-1.5 rounded-full text-xs border transition ${
              active
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
            }`}
          >
            {emoji} {label}
          </button>
        );
      })}
    </div>
  );
}
