import { useCallback, useState } from "react";
import { clearIngestBuffer, uploadIngestFile } from "../services/api.js";

export function IngestPanel({ busy, onIngestSuccess, ingestStatus, onRefreshStatus, livePoll, onLivePollChange }) {
  const [mode, setMode] = useState("replace");
  const [localBusy, setLocalBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const [msg, setMsg] = useState(null);

  const disabled = busy || localBusy;

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      setLocalBusy(true);
      setMsg(null);
      try {
        const res = await uploadIngestFile(file, mode);
        setMsg(
          `Accepted ${res.accepted_rows}/${res.parsed_rows} rows · buffer ${res.buffer_rows}` +
            (res.skipped_rows ? ` · skipped ${res.skipped_rows}` : "")
        );
        onIngestSuccess?.(res);
        onRefreshStatus?.();
      } catch (e) {
        setMsg(String(e.message || e));
      } finally {
        setLocalBusy(false);
      }
    },
    [mode, onIngestSuccess, onRefreshStatus]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) handleFile(f);
  };

  const onClearBuffer = async () => {
    setLocalBusy(true);
    setMsg(null);
    try {
      await clearIngestBuffer();
      setMsg("Buffer cleared.");
      onRefreshStatus?.();
    } catch (e) {
      setMsg(String(e.message || e));
    } finally {
      setLocalBusy(false);
    }
  };

  return (
    <div className="glass-panel p-6 space-y-4 border-cyber-accent/20">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h3 className="font-display text-lg text-cyber-accent">Real-time ingest</h3>
          <p className="text-sm text-cyber-muted mt-1 max-w-xl">
            Drop API/network logs as <strong className="text-slate-400">JSON array</strong>,{" "}
            <strong className="text-slate-400">{"{ \"logs\": [...] }"}</strong>, or{" "}
            <strong className="text-slate-400">NDJSON</strong>. Same schema as <code className="text-xs">/analyze</code>.
            Append mode keeps a rolling window (server-side buffer, max 100k rows by default).
          </p>
        </div>
        <div className="text-xs font-mono text-slate-500 space-y-1 shrink-0">
          <div>
            buffer: <span className="text-cyber-accent">{ingestStatus?.buffer_rows ?? "—"}</span> rows
          </div>
          <div>
            rev: <span className="text-slate-300">{ingestStatus?.analysis_revision ?? 0}</span>
          </div>
          {ingestStatus?.watch_active ? (
            <div className="text-emerald-400">watch: {ingestStatus.watch_dir}</div>
          ) : (
            <div className="text-cyber-muted">folder watch: off</div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs text-cyber-muted flex items-center gap-2">
          Mode
          <select
            value={mode}
            disabled={disabled}
            onChange={(e) => setMode(e.target.value)}
            className="bg-cyber-bg border border-cyber-border rounded px-2 py-1 text-slate-200 text-sm"
          >
            <option value="replace">Replace buffer</option>
            <option value="append">Append (rolling)</option>
          </select>
        </label>
        <label className="rounded-lg border border-cyber-border px-3 py-2 text-sm text-slate-200 cursor-pointer hover:border-cyber-accent/50 disabled:opacity-40">
          <input
            type="file"
            accept=".json,.jsonl,.ndjson,application/json,text/plain"
            disabled={disabled}
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          Choose file
        </label>
        <button
          type="button"
          disabled={disabled}
          onClick={onClearBuffer}
          className="rounded-lg border border-cyber-border/60 px-3 py-2 text-xs text-cyber-muted hover:text-white"
        >
          Clear buffer
        </button>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={`rounded-xl border-2 border-dashed min-h-[120px] flex items-center justify-center text-sm transition ${
          drag ? "border-cyber-accent bg-cyan-500/5 text-cyber-accent" : "border-cyber-border text-cyber-muted"
        }`}
      >
        {localBusy ? "Uploading & analyzing…" : "Drop .json / .jsonl here"}
      </div>

      {msg && <p className="text-xs text-slate-400 font-mono break-words">{msg}</p>}

      <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={!!livePoll}
          onChange={(e) => onLivePollChange?.(e.target.checked)}
          className="accent-cyan-400"
        />
        Live sync (poll server every 2s — picks up folder-watch / other ingest)
      </label>

      <p className="text-[11px] text-cyber-muted leading-relaxed">
        <strong className="text-slate-500">Folder watch:</strong> set env{" "}
        <code className="text-slate-400">SHADOWTRACE_WATCH_DIR</code> (e.g. <code className="text-slate-400">../ingest_drop</code>
        ) and restart API — new files trigger re-analysis. Optional{" "}
        <code className="text-slate-400">SHADOWTRACE_WATCH_MODE=append|replace</code>,{" "}
        <code className="text-slate-400">SHADOWTRACE_BUFFER_MAX</code>.
      </p>
    </div>
  );
}
