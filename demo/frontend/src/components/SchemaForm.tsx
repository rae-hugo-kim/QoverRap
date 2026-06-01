import type { SchemaInfo } from "../types";

interface Props {
  schema: SchemaInfo;
  /** Controlled field values keyed by field name. */
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
}

// Human-friendly labels for the few fields that read awkwardly uppercased.
// Falls back to the raw field name (uppercased) when absent.
const FIELD_LABELS: Record<string, string> = {
  event_id: "EVENT ID",
  festival_id: "FESTIVAL ID",
  band_id: "BAND ID",
  serial: "SERIAL",
  issued_at: "ISSUED AT",
  valid_until: "VALID UNTIL",
  datetime: "DATETIME",
  section: "SECTION",
  seat: "SEAT",
  gate: "GATE",
  opponent: "OPPONENT",
  holder: "HOLDER",
  day: "DAY",
  zone: "ZONE",
  tier: "TIER",
};

/**
 * Generic per-field issue form built from a schema's field descriptors.
 * `is_timestamp` fields render a date input; everything else is text. The
 * `kind` discriminator is never rendered (it's fixed by the schema selection
 * and filled by the backend model default). Empty optionals are sent as-is —
 * the backend treats "" as a valid optional default.
 */
export default function SchemaForm({ schema, value, onChange }: Props) {
  const fields = schema.fields.filter((f) => f.name !== "kind");
  return (
    <div data-testid="schema-form" className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {fields.map((f) => {
        const label = FIELD_LABELS[f.name] ?? f.name.replace(/_/g, " ").toUpperCase();
        return (
          <label key={f.name} className="block text-sm">
            <span className="block text-[11px] uppercase tracking-wide text-slate-500 mb-1">
              {label}
              {f.required && <span className="text-red-500 ml-0.5">*</span>}
            </span>
            <input
              data-testid={`field-${f.name}`}
              type={f.is_timestamp ? "date" : "text"}
              required={f.required}
              value={value[f.name] ?? ""}
              onChange={(e) =>
                onChange({ ...value, [f.name]: e.target.value })
              }
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm"
            />
          </label>
        );
      })}
    </div>
  );
}
