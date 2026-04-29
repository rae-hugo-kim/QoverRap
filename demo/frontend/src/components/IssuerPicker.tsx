import type { TrustEntry } from "../types";

interface Props {
  entries: TrustEntry[];
  selectedId: string | null;
  onSelect: (issuer_id: string) => void;
}

export default function IssuerPicker({ entries, selectedId, onSelect }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {entries.map((e) => {
        const active = e.issuer_id === selectedId;
        return (
          <button
            key={e.issuer_id}
            data-testid={`issuer-${e.issuer_id}`}
            onClick={() => onSelect(e.issuer_id)}
            className={`text-left rounded-lg p-4 border-2 transition ${
              active ? "border-slate-900" : "border-transparent hover:border-slate-300"
            }`}
            style={{
              background: e.theme_color,
              color: "#fff",
            }}
          >
            <div
              className="inline-flex items-center justify-center rounded-full w-10 h-10 font-bold text-xs mb-2"
              style={{ background: e.accent_color, color: e.theme_color }}
            >
              {e.logo_text}
            </div>
            <div className="font-semibold text-sm">{e.display_name}</div>
            <div className="text-xs opacity-80 font-mono mt-1">{e.issuer_id}</div>
          </button>
        );
      })}
    </div>
  );
}
