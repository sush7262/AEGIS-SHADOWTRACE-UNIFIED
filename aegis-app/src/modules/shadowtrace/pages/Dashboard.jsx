import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DetectionPanel } from "../components/DetectionPanel.jsx";
import { GraphView } from "../components/GraphView.jsx";
import { IngestPanel } from "../components/IngestPanel.jsx";
import { MetadataVisualizer } from "../components/MetadataVisualizer.jsx";
import { SummaryCards } from "../components/SummaryCards.jsx";
import { TimelineReplay } from "../components/TimelineReplay.jsx";
import {
  analyzeLogs,
  apiUrl,
  fetchFullSnapshot,
  fetchHealth,
  fetchIngestStatus,
  generateData,
} from "../services/api.js";

/** Unique seed each click — avoids Python RNG seeing the same seed too often. */
function nextRunSeed() {
  const t = Date.now();
  const perf = typeof performance !== "undefined" ? performance.now() : 0;
  const rnd = Math.floor(Math.random() * 0x7fffffff);
  return (t ^ Math.floor(perf * 1e6) ^ rnd) >>> 0;
}

export function Dashboard() {
  const [backendOk, setBackendOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [logs, setLogs] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [bucketIndex, setBucketIndex] = useState(0);
  /** Bumps after every successful analyze so charts/graph remount with fresh data. */
  const [analysisRunId, setAnalysisRunId] = useState(0);
  const [lastRunInfo, setLastRunInfo] = useState(null);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [livePoll, setLivePoll] = useState(false);
  const revisionRef = useRef(0);

  const hydrateFromAnalysis = useCallback((res, meta) => {
    if (!res?.graph) return;
    setAnalysis(res);
    setLogs([]);
    setBucketIndex(0);
    setAnalysisRunId((i) => i + 1);
    setLastRunInfo(meta);
    const topIp = res?.summary?.top_suspect;
    if (topIp) {
      const match = res?.graph?.nodes?.find((n) => n.type === "source" && n.label === topIp);
      setSelectedId(match?.id || null);
    } else {
      setSelectedId(null);
    }
  }, []);

  const refreshIngestStatus = useCallback(async () => {
    try {
      const s = await fetchIngestStatus();
      setIngestStatus(s);
      return s;
    } catch {
      return null;
    }
  }, []);

  const ping = useCallback(async () => {
    try {
      await fetchHealth();
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    }
  }, []);

  useEffect(() => {
    ping();
    const id = setInterval(ping, 15000);
    return () => clearInterval(id);
  }, [ping]);

  useEffect(() => {
    (async () => {
      const s = await refreshIngestStatus();
      if (s?.analysis_revision != null) revisionRef.current = s.analysis_revision;
    })();
  }, [refreshIngestStatus]);

  useEffect(() => {
    if (!livePoll) return;
    const id = setInterval(async () => {
      const s = await refreshIngestStatus();
      if (!s) return;
      const rev = s.analysis_revision ?? 0;
      if (rev > revisionRef.current) {
        revisionRef.current = rev;
        try {
          const snap = await fetchFullSnapshot();
          hydrateFromAnalysis(snap, {
            kind: "live",
            at: Date.now(),
            logCount: snap.summary?.total_requests,
            source: s.last_ingest_source,
          });
        } catch {
          /* no snapshot yet */
        }
      }
    }, 2000);
    return () => clearInterval(id);
  }, [livePoll, refreshIngestStatus, hydrateFromAnalysis]);

  const runAnalyze = async (logPayload, meta = null) => {
    setBusy(true);
    setError(null);
    try {
      const res = await analyzeLogs(logPayload);
      setAnalysis(res);
      setLogs(logPayload);
      setBucketIndex(0);
      setAnalysisRunId((id) => id + 1);
      setLastRunInfo(
        meta || {
          kind: "analyze",
          at: Date.now(),
          logCount: logPayload.length,
        }
      );
      const topIp = res?.summary?.top_suspect;
      if (topIp) {
        const match = res?.graph?.nodes?.find((n) => n.type === "source" && n.label === topIp);
        setSelectedId(match?.id || null);
      } else {
        setSelectedId(null);
      }
      const st = await refreshIngestStatus();
      if (st) revisionRef.current = st.analysis_revision ?? revisionRef.current;
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const onGenerate = async () => {
    setBusy(true);
    setError(null);
    try {
      const seed = nextRunSeed();
      const numLogs = 1050 + Math.floor(Math.random() * 700);
      const gen = await generateData({ num_logs: numLogs, seed });
      await runAnalyze(gen.logs, {
        kind: "generate",
        at: Date.now(),
        seed,
        numLogs: gen.count ?? gen.logs?.length,
        logCount: gen.logs?.length,
      });
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const onDemoSample = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("/sample_logs.json");
      const data = await r.json();
      if (!Array.isArray(data) || data.length < 3) {
        await onGenerate();
        return;
      }
      await runAnalyze(data, { kind: "demo", at: Date.now(), logCount: data.length });
    } catch {
      await onGenerate();
    } finally {
      setBusy(false);
    }
  };

  const exportJson = () => {
    if (!analysis?.export) return;
    const blob = new Blob([JSON.stringify(analysis.export, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "shadowtrace-export.json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const graph = analysis?.graph;
  const summary = analysis?.summary;
  const ranked = summary?.ranked_suspicious;

  const timeline = analysis?.timeline || [];
  useEffect(() => {
    if (bucketIndex >= timeline.length) setBucketIndex(0);
  }, [timeline, bucketIndex]);

  const heroStats = useMemo(
    () => ({
      requests: summary?.total_requests ?? logs.length ?? 0,
      edges: summary?.total_edges ?? graph?.edges?.length ?? 0,
    }),
    [summary, logs, graph]
  );

  const handleSelectNode = useCallback((n) => {
    setSelectedId(n?.id ?? null);
  }, []);

  return (
    <div className="h-full bg-cyber-bg bg-grid bg-[length:48px_48px]">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(0,240,255,0.08),transparent_55%)]" />

      <header className="relative border-b border-cyber-border/80 bg-cyber-panel/40 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyber-muted">ShadowTrace AI</p>
              <h1 className="mt-2 font-display text-4xl sm:text-5xl text-white tracking-tight">
                Find the attacker hiding in plain sight
              </h1>
              <p className="mt-4 max-w-2xl text-slate-400 text-sm leading-relaxed">
                Ingest noisy API and network logs, reconstruct entity interactions, fingerprint metadata patterns,
                and surface the most probable hidden command node with explainable fusion scoring.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono ${
                  backendOk ? "border-emerald-500/40 text-emerald-300" : "border-amber-500/40 text-amber-200"
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${backendOk ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`} />
                {backendOk ? "API online" : "API offline"}
              </span>
              <code className="hidden sm:block text-[10px] text-cyber-muted max-w-xs truncate">{apiUrl("/health")}</code>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={busy}
              title={!backendOk ? "Backend not detected on last ping — click anyway to try, or start uvicorn." : ""}
              onClick={onGenerate}
              className="rounded-lg bg-cyber-accent/90 px-5 py-2.5 text-sm font-semibold text-black shadow-glow transition hover:bg-cyber-accent disabled:opacity-40"
            >
              {busy ? "Working…" : "Generate + analyze"}
            </button>
            <button
              type="button"
              disabled={busy || logs.length === 0}
              onClick={() => runAnalyze(logs)}
              className="rounded-lg border border-cyber-border bg-black/30 px-5 py-2.5 text-sm text-slate-200 transition hover:border-cyber-accent/50 disabled:opacity-40"
            >
              Re-run analysis
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={onDemoSample}
              className="rounded-lg border border-cyber-border/60 px-5 py-2.5 text-sm text-cyber-muted hover:text-white transition disabled:opacity-40"
            >
              Demo mode
            </button>
            <button
              type="button"
              disabled={!analysis?.export}
              onClick={exportJson}
              className="rounded-lg border border-cyber-danger/40 px-5 py-2.5 text-sm text-cyber-danger hover:bg-cyber-danger/10 transition disabled:opacity-30"
            >
              Export JSON
            </button>
          </div>
          {error && (
            <p className="mt-4 text-sm text-red-400 border border-red-500/30 rounded-lg px-3 py-2 bg-red-950/30">
              {error}
            </p>
          )}
          {!backendOk && (
            <p className="mt-4 text-xs text-amber-200/90 border border-amber-500/30 rounded-lg px-3 py-2 bg-amber-950/20">
              Backend ping failed. Start API from <code className="text-slate-300">backend</code> folder, e.g.{" "}
              <code className="text-slate-300">uvicorn app.main:app --reload --port 8080</code>. Dev UI proxies{" "}
              <code className="text-slate-300">/api</code> → <code className="text-slate-300">127.0.0.1:8080</code> (change{" "}
              <code className="text-slate-300">VITE_PROXY_TARGET</code> if you use another port).
            </p>
          )}
          <p className="mt-4 text-xs text-cyber-muted">
            Use <span className="text-slate-400">npm run dev</span> (not opening <span className="text-slate-400">index.html</span> directly) so{" "}
            <span className="text-slate-400">/api</span> reaches FastAPI.
          </p>
        </div>
      </header>

      <main className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-10">
        <section>
          <IngestPanel
            busy={busy}
            ingestStatus={ingestStatus}
            onRefreshStatus={refreshIngestStatus}
            livePoll={livePoll}
            onLivePollChange={setLivePoll}
            onIngestSuccess={(res) => {
              hydrateFromAnalysis(res.analysis, {
                kind: "ingest",
                at: Date.now(),
                logCount: res.accepted_rows,
                source: res.mode,
              });
              if (typeof res.revision === "number") revisionRef.current = res.revision;
              refreshIngestStatus();
            }}
          />
        </section>

        <section className="space-y-4">
          <div className="flex items-baseline justify-between gap-4 flex-wrap">
            <h2 className="font-display text-xl text-white">Mission overview</h2>
            <p className="text-xs font-mono text-cyber-muted text-right">
              <span className="block sm:inline">
                {heroStats.requests} events · {heroStats.edges} edges
              </span>
              {lastRunInfo && (
                <span className="block sm:inline sm:ml-2 text-cyber-accent/90">
                  · Run #{analysisRunId}{" "}
                  {new Date(lastRunInfo.at).toLocaleTimeString()}
                  {lastRunInfo.kind === "generate" && lastRunInfo.seed != null && (
                    <span className="text-cyber-muted"> · seed {lastRunInfo.seed}</span>
                  )}
                </span>
              )}
            </p>
          </div>
          <SummaryCards key={`cards-${analysisRunId}`} summary={summary} />
        </section>

        <section className="grid gap-8 xl:grid-cols-5">
          <div className="xl:col-span-3 space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h2 className="font-display text-xl text-white">Interaction graph</h2>
              <p className="text-xs text-cyber-muted">Drag nodes · scroll to zoom · click for intel</p>
            </div>
            <GraphView
              key={`graph-${analysisRunId}`}
              graph={graph}
              selectedId={selectedId}
              onSelectNode={handleSelectNode}
            />
          </div>
          <div className="xl:col-span-2">
            <DetectionPanel
              key={`panel-${analysisRunId}`}
              ranked={ranked}
              selectedNode={graph?.nodes?.find((n) => n.id === selectedId)}
              graphNodes={graph?.nodes}
            />
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="font-display text-xl text-white">Metadata pattern analysis</h2>
          <TimelineReplay
            key={`replay-${analysisRunId}`}
            timeline={timeline}
            bucketIndex={bucketIndex}
            onBucketChange={setBucketIndex}
          />
          <MetadataVisualizer
            key={`viz-${analysisRunId}`}
            charts={analysis?.charts}
            timeline={timeline}
            benignVs={analysis?.benign_vs_suspicious}
            highlightBucket={bucketIndex}
          />
        </section>
      </main>

      <footer className="relative border-t border-cyber-border/60 py-8 text-center text-xs text-cyber-muted">
        ShadowTrace AI · local-first attribution prototype · no paid external services required
      </footer>
    </div>
  );
}
