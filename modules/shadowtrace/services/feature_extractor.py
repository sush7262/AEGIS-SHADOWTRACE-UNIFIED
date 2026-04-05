"""Per-source behavioral and metadata features for detection and charts."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from modules.shadowtrace.services.data_generator import LABEL_KEY


def _parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def extract_per_source_features(logs: list[dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Returns feature DataFrame indexed by source_ip and chart-friendly aggregates."""
    rows = []
    for row in logs:
        label = row.get(LABEL_KEY, "unknown")
        rows.append(
            {
                "source_ip": row["source_ip"],
                "destination_service": row["destination_service"],
                "endpoint": row["endpoint"],
                "timestamp": row["timestamp"],
                "headers": row.get("headers") or {},
                "user_agent": row.get("user_agent") or "",
                "method": row.get("method") or "GET",
                "status_code": int(row.get("status_code") or 200),
                "request_size": float(row.get("request_size") or 0),
                "response_time_ms": float(row.get("response_time_ms") or 0),
                LABEL_KEY: label,
            }
        )
    df = pd.DataFrame(rows)
    df["_ts"] = df["timestamp"].apply(_parse_ts)
    df = df.sort_values("_ts")

    per_source: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    for ts, sub in df.groupby(df["_ts"].dt.floor("1min")):
        timeline.append(
            {
                "bucket": ts.isoformat().replace("+00:00", "Z"),
                "requests": int(len(sub)),
                "unique_sources": int(sub["source_ip"].nunique()),
            }
        )

    for ip, g in df.groupby("source_ip"):
        g = g.sort_values("_ts")
        ts_vals = g["_ts"].astype("int64") / 1e9
        intervals = np.diff(ts_vals) if len(ts_vals) > 1 else np.array([])

        req_count = len(g)
        svc_counts = g["destination_service"].value_counts(normalize=True)
        ep_counts = g["endpoint"].value_counts(normalize=True)
        header_sigs = [tuple(h.keys()) for h in g["headers"]]
        sig_ctr = Counter(header_sigs)
        dom_sig = sig_ctr.most_common(1)[0][0] if sig_ctr else tuple()
        dom_sig_ratio = sig_ctr.most_common(1)[0][1] / req_count if sig_ctr else 0.0

        # Header value repetition (full header dict as string)
        hdr_strs = [str(sorted(h.items())) for h in g["headers"]]
        hdr_ctr = Counter(hdr_strs)
        hdr_repeat_ratio = hdr_ctr.most_common(1)[0][1] / req_count if hdr_ctr else 0.0

        ua_list = g["user_agent"].tolist()
        ua_ctr = Counter(ua_list)
        ua_diversity = len(ua_ctr) / max(1, req_count)

        if len(intervals) > 1:
            mean_i = float(np.mean(intervals))
            std_i = float(np.std(intervals))
            cv = float(std_i / mean_i) if mean_i > 1e-6 else 0.0
            # Consistency: low CV = more beacon-like
            interval_consistency = 1.0 / (1.0 + cv)
            burstiness = float(np.percentile(intervals, 90) / (np.percentile(intervals, 10) + 1e-6))
        else:
            mean_i = 0.0
            std_i = 0.0
            interval_consistency = 0.0
            burstiness = 1.0

        # Endpoint concentration (Herfindahl)
        ep_hhi = float((ep_counts**2).sum()) if len(ep_counts) else 0.0
        svc_hhi = float((svc_counts**2).sum()) if len(svc_counts) else 0.0

        size_mean = float(g["request_size"].mean())
        size_std = float(g["request_size"].std() or 0.0)
        rtt_mean = float(g["response_time_ms"].mean())
        rtt_std = float(g["response_time_ms"].std() or 0.0)

        benign_like = (g[LABEL_KEY] == "benign").mean() if LABEL_KEY in g.columns else 0.0

        per_source.append(
            {
                "source_ip": ip,
                "request_count": req_count,
                "unique_services": int(g["destination_service"].nunique()),
                "unique_endpoints": int(g["endpoint"].nunique()),
                "mean_interval_sec": mean_i,
                "std_interval_sec": std_i,
                "interval_consistency": interval_consistency,
                "burstiness": min(20.0, burstiness) / 20.0,
                "dominant_header_signature": "|".join(dom_sig),
                "header_order_concentration": dom_sig_ratio,
                "header_value_repetition": hdr_repeat_ratio,
                "ua_diversity": ua_diversity,
                "endpoint_concentration_hhi": ep_hhi,
                "service_concentration_hhi": svc_hhi,
                "request_size_mean": size_mean,
                "request_size_std": size_std,
                "response_time_mean": rtt_mean,
                "response_time_std": rtt_std,
                "intervals_list": intervals.tolist() if len(intervals) else [],
                "user_agents_list": ua_list,
                "endpoints_list": g["endpoint"].tolist(),
                "_benign_fraction": float(benign_like),
            }
        )

    feat_df = pd.DataFrame(per_source).set_index("source_ip")
    chart_data = {
        "request_frequency": feat_df["request_count"].sort_values(ascending=False).head(25).to_dict(),
        "interval_consistency": feat_df["interval_consistency"].sort_values(ascending=False).head(25).to_dict(),
        "header_concentration": feat_df["header_order_concentration"]
        .sort_values(ascending=False)
        .head(25)
        .to_dict(),
        "endpoint_hhi": feat_df["endpoint_concentration_hhi"].sort_values(ascending=False).head(25).to_dict(),
    }
    return feat_df, {"timeline": timeline, "charts": chart_data}
