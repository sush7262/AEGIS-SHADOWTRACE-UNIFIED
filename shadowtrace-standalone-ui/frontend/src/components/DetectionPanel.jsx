export function DetectionPanel({ ranked, selectedNode, graphNodes }) {
  const top = ranked?.[0];
  const selectedIp =
    selectedNode?.type === "source"
      ? selectedNode.label
      : selectedNode?.label || null;

  const detail =
    ranked?.find((r) => r.source_ip === selectedIp) ||
    top ||
    null;

  const graphMeta = graphNodes?.find(
    (n) => n.type === "source" && n.label === detail?.source_ip
  );

  return (
    <div className="glass-panel p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg tracking-wide text-cyber-accent">Command node attribution</h3>
          <p className="text-sm text-cyber-muted mt-1">
            Fusion of graph influence, behavioral fingerprints, and isolation-forest anomaly scoring.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-cyber-muted">Primary suspect</p>
          <p className="font-mono text-cyber-warn text-lg">{detail?.source_ip ?? "—"}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ["Confidence", detail?.confidence != null ? `${detail.confidence}%` : "—"],
          ["Graph", detail?.graph_score?.toFixed?.(3) ?? "—"],
          ["Behavior", detail?.behavior_score?.toFixed?.(3) ?? "—"],
          ["Anomaly", detail?.anomaly_score?.toFixed?.(3) ?? "—"],
        ].map(([k, v]) => (
          <div key={k} className="rounded-lg border border-cyber-border bg-cyber-bg/60 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wider text-cyber-muted">{k}</p>
            <p className="font-mono text-sm text-slate-100">{v}</p>
          </div>
        ))}
      </div>

      <div>
        <p className="text-xs uppercase text-cyber-muted mb-2">Fingerprint ID</p>
        <code className="block rounded-md bg-black/40 border border-cyber-border px-3 py-2 text-cyber-accent text-sm">
          {graphMeta?.fingerprint_id || detail?.fingerprint_id || "—"}
        </code>
      </div>

      <div>
        <p className="text-xs uppercase text-cyber-muted mb-2">Explanation</p>
        <p className="text-sm leading-relaxed text-slate-300 border-l-2 border-cyber-danger pl-3">
          {detail?.explanation || "Run analysis to generate an analyst-grade narrative."}
        </p>
      </div>

      {detail?.evidence && (
        <div>
          <p className="text-xs uppercase text-cyber-muted mb-2">Supporting features</p>
          <ul className="grid sm:grid-cols-2 gap-2 text-xs font-mono text-slate-400">
            {Object.entries(detail.evidence).map(([k, v]) => (
              <li key={k} className="flex justify-between gap-2 border border-cyber-border/60 rounded px-2 py-1">
                <span className="text-cyber-muted">{k}</span>
                <span className="text-slate-200">{typeof v === "number" ? v.toFixed(3) : String(v)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {ranked?.length > 1 && (
        <div>
          <p className="text-xs uppercase text-cyber-muted mb-2">Ranked watchlist</p>
          <div className="max-h-40 overflow-auto space-y-1 pr-1">
            {ranked.slice(0, 8).map((r, i) => (
              <div
                key={r.source_ip}
                className="flex justify-between text-xs font-mono border border-cyber-border/40 rounded px-2 py-1 bg-black/20"
              >
                <span className="text-cyber-muted w-6">{i + 1}</span>
                <span className="text-slate-200 flex-1">{r.source_ip}</span>
                <span className="text-cyber-warn">{r.final_score?.toFixed?.(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
