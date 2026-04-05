"""Single entry for full analysis — used by /analyze, /ingest, and folder watcher."""

from __future__ import annotations

from typing import Any

from modules.shadowtrace.models.schemas import AnalyzeResponse, LogEntry, SummaryResponse
from modules.shadowtrace.services.data_generator import LABEL_KEY
from modules.shadowtrace.services.detection_engine import benign_vs_suspicious_summary, compute_detection
from modules.shadowtrace.services.feature_extractor import extract_per_source_features
from modules.shadowtrace.services.graph_builder import build_graph_from_logs
from modules.shadowtrace.services import log_buffer
from modules.shadowtrace.utils.helpers import bump_analysis_revision, set_last_analysis, set_last_logs


def _strip_internal_labels(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != LABEL_KEY} for row in rows]


def validate_log_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return Pydantic-normalized rows and per-row error strings (skipped rows)."""
    good: list[dict[str, Any]] = []
    bad: list[str] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            bad.append(f"row {i}: not an object")
            continue
        try:
            le = LogEntry.model_validate(row)
            good.append(le.model_dump())
        except Exception as e:
            bad.append(f"row {i}: {e}")
    return good, bad


def run_full_analysis(raw_rows: list[dict[str, Any]]) -> AnalyzeResponse:
    """
    Expect dicts shaped like LogEntry (after optional internal label strip).
    Mutates session: last logs, last analysis, revision counter.
    """
    stripped = _strip_internal_labels(raw_rows)
    clean, _errs = validate_log_rows(stripped)
    if not clean:
        raise ValueError("No valid log rows after validation.")

    set_last_logs(clean)

    feat_df, aux = extract_per_source_features(clean)
    G, _ = build_graph_from_logs(clean, None)
    node_scores, ranked = compute_detection(G, feat_df, clean)
    _, graph_payload = build_graph_from_logs(clean, node_scores)

    top_ips = {d.source_ip for d in ranked[:8]}
    b_vs = benign_vs_suspicious_summary(feat_df, top_ips)

    src_nodes = [n for n in graph_payload.nodes if n.type == "source"]
    sus_n = sum(1 for n in src_nodes if n.is_suspicious)
    top = ranked[0] if ranked else None

    t_min = min((r["timestamp"] for r in clean), default=None)
    t_max = max((r["timestamp"] for r in clean), default=None)

    summary = SummaryResponse(
        total_nodes=len(graph_payload.nodes),
        total_edges=len(graph_payload.edges),
        source_node_count=len(src_nodes),
        suspicious_count=sus_n,
        top_suspect=top.source_ip if top else None,
        top_confidence=top.confidence if top else 0.0,
        total_requests=len(clean),
        time_range={"start": t_min, "end": t_max},
        ranked_suspicious=ranked,
    )

    export = {
        "version": "shadowtrace-ai-1.0",
        "ranked_suspicious": [r.model_dump() for r in ranked],
        "graph_metrics": graph_payload.metrics,
        "feature_snapshot": {ip: node_scores.get(ip, {}) for ip in list(node_scores)[:20]},
    }

    resp = AnalyzeResponse(
        graph=graph_payload,
        summary=summary,
        timeline=aux["timeline"],
        charts=aux["charts"],
        benign_vs_suspicious=b_vs,
        export=export,
    )
    payload = resp.model_dump()
    set_last_analysis(payload)
    log_buffer.buffer_replace(clean)
    bump_analysis_revision()
    return resp
