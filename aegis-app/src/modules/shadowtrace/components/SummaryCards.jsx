export function SummaryCards({ summary }) {
  const cards = [
    {
      label: "Graph nodes",
      value: summary?.total_nodes ?? "—",
      hint: "IPs + services",
    },
    {
      label: "Flagged sources",
      value: summary?.suspicious_count ?? "—",
      hint: "Anomaly threshold",
    },
    {
      label: "Top suspect",
      value: summary?.top_suspect ?? "—",
      hint: "Highest fusion score",
    },
    {
      label: "Confidence",
      value: summary?.top_confidence != null ? `${summary.top_confidence}%` : "—",
      hint: "0–100 scale",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="glass-panel relative overflow-hidden p-5 transition hover:shadow-glow"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent pointer-events-none" />
          <p className="text-xs uppercase tracking-widest text-cyber-muted">{c.label}</p>
          <p className="mt-2 font-display text-2xl text-cyber-accent drop-shadow-[0_0_12px_rgba(0,240,255,0.25)]">
            {c.value}
          </p>
          <p className="mt-1 text-xs text-slate-500">{c.hint}</p>
        </div>
      ))}
    </div>
  );
}
