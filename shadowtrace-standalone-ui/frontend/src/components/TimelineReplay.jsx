/**
 * Timeline scrubber: highlights activity bucket for demo "replay" feel.
 * Full packet replay would need per-edge timestamps on the API — this uses minute buckets.
 */
export function TimelineReplay({ timeline, bucketIndex, onBucketChange }) {
  const max = Math.max(0, (timeline?.length || 1) - 1);
  const cur = timeline?.[bucketIndex];

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h4 className="font-display text-sm text-cyber-accent">Attack timeline scrubber</h4>
          <p className="text-xs text-cyber-muted">
            Scrub through aggregated activity to stress-test analyst focus.
          </p>
        </div>
        {cur && (
          <div className="text-right text-xs font-mono text-slate-400">
            <div>
              <span className="text-cyber-muted">bucket </span>
              {new Date(cur.bucket).toLocaleString()}
            </div>
            <div>
              requests <span className="text-cyber-accent">{cur.requests}</span> · sources{" "}
              <span className="text-cyber-warn">{cur.unique_sources}</span>
            </div>
          </div>
        )}
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={Math.min(bucketIndex, max)}
        onChange={(e) => onBucketChange(Number(e.target.value))}
        className="w-full accent-cyan-400 h-2 bg-cyber-border rounded-lg appearance-none cursor-pointer"
      />
      <div className="flex gap-0.5 h-8 rounded overflow-hidden border border-cyber-border/80">
        {(timeline || []).map((t, i) => {
          const h = Math.min(1, (t.requests || 0) / 50);
          const hot = i === bucketIndex;
          return (
            <div
              key={t.bucket}
              title={`${t.requests} req`}
              className="flex-1 min-w-[2px] transition-colors"
              style={{
                background: hot
                  ? "linear-gradient(180deg, #00f0ff, #ff3366)"
                  : `linear-gradient(180deg, rgba(0,240,255,${0.15 + h * 0.5}), #0b1220)`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
