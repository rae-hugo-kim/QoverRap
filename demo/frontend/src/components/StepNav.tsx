interface Props {
  steps: { id: string; label: string }[];
  activeId: string;
  onSelect: (id: string) => void;
}

export default function StepNav({ steps, activeId, onSelect }: Props) {
  return (
    <nav className="flex flex-wrap gap-2 mb-6">
      {steps.map((s, i) => {
        const active = s.id === activeId;
        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`px-3 py-1.5 rounded-full text-sm border transition ${
              active
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
          >
            <span className="font-mono mr-1.5 opacity-70">{i + 1}</span>
            {s.label}
          </button>
        );
      })}
    </nav>
  );
}
