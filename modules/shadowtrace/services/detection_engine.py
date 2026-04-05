"""Graph + behavior + anomaly fusion for C2-style source attribution."""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from modules.shadowtrace.models.schemas import SuspiciousNodeDetail
from modules.shadowtrace.services.fingerprinting import fingerprint_bundle_for_source
from modules.shadowtrace.utils.helpers import clamp01


def _normalize_series(s: pd.Series) -> pd.Series:
    if s.empty or s.max() == s.min():
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def compute_detection(
    G: nx.Graph,
    feat_df: pd.DataFrame,
    logs: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[SuspiciousNodeDetail]]:
    """Returns per-source-ip score dict and ranked suspicious list."""
    sources = [n for n, d in G.nodes(data=True) if d.get("entity_type") == "source"]
    ip_list = [n.replace("ip:", "", 1) for n in sources]

    # Graph-derived scores per source IP node
    deg = nx.degree_centrality(G)
    bet = nx.betweenness_centrality(G, weight="weight", normalized=True)
    try:
        pr = nx.pagerank(G, weight="weight")
    except Exception:
        pr = {n: 0.0 for n in G.nodes}

    graph_rows = []
    for ip in ip_list:
        nid = f"ip:{ip}"
        # Emphasize bridge-like role and weighted activity
        wdeg = float(sum(G[nid][nb]["weight"] for nb in G.neighbors(nid))) if nid in G else 0.0
        graph_rows.append(
            {
                "source_ip": ip,
                "deg_c": deg.get(nid, 0.0),
                "bet_c": bet.get(nid, 0.0),
                "pr_c": pr.get(nid, 0.0),
                "wdeg": wdeg,
            }
        )
    gr = pd.DataFrame(graph_rows).set_index("source_ip")
    gr["graph_raw"] = (
        0.35 * _normalize_series(gr["deg_c"])
        + 0.35 * _normalize_series(gr["bet_c"])
        + 0.15 * _normalize_series(gr["pr_c"])
        + 0.15 * _normalize_series(gr["wdeg"])
    )

    # Align feature frame
    X = feat_df.reindex(ip_list).fillna(0.0)

    behavior_raw = (
        0.22 * _normalize_series(X["interval_consistency"])
        + 0.18 * _normalize_series(X["header_order_concentration"])
        + 0.18 * _normalize_series(X["header_value_repetition"])
        + 0.14 * _normalize_series(X["endpoint_concentration_hhi"])
        + 0.12 * (1.0 - _normalize_series(X["ua_diversity"]))
        + 0.10 * _normalize_series(X["service_concentration_hhi"])
        + 0.06 * (1.0 - _normalize_series(X["burstiness"]))
    )

    # Anomaly detection on scaled feature matrix
    feature_cols = [
        "request_count",
        "interval_consistency",
        "header_order_concentration",
        "header_value_repetition",
        "endpoint_concentration_hhi",
        "service_concentration_hhi",
        "ua_diversity",
        "burstiness",
        "request_size_mean",
        "response_time_mean",
    ]
    M = X.reindex(columns=feature_cols).fillna(0.0).values
    if len(M) < 5:
        anomaly_score = np.zeros(len(M))
    else:
        scaler = StandardScaler()
        Ms = scaler.fit_transform(M)
        iso = IsolationForest(
            n_estimators=200,
            contamination=0.08,
            random_state=42,
        )
        pred = iso.fit_predict(Ms)
        # decision_function: lower = more anomalous -> map to 0..1 suspicious
        raw = iso.decision_function(Ms)
        ar = (raw.max() - raw) / (raw.max() - raw.min() + 1e-9)
        anomaly_score = np.clip(ar, 0, 1)
        # Boost labeled outliers slightly
        anomaly_score = np.where(pred == -1, np.minimum(1.0, anomaly_score + 0.12), anomaly_score)

    anomaly_series = pd.Series(anomaly_score, index=ip_list)

    # Small k-means on sources for fingerprint clusters
    cluster_id: dict[str, int] = {}
    if len(M) >= 4:
        k = min(5, max(2, len(M) // 8))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(StandardScaler().fit_transform(M))
        for i, ip in enumerate(ip_list):
            cluster_id[ip] = int(labels[i])

    final_graph = gr["graph_raw"].reindex(ip_list).fillna(0.0).map(clamp01)
    final_behavior = behavior_raw.reindex(ip_list).fillna(0.0).map(clamp01)
    final_anomaly = anomaly_series.reindex(ip_list).fillna(0.0).map(clamp01)

    final = 0.4 * final_graph + 0.4 * final_behavior + 0.2 * final_anomaly

    ranked = final.sort_values(ascending=False)
    threshold = ranked.quantile(0.92) if len(ranked) > 5 else ranked.max() * 0.85
    suspicious_ips = ranked[ranked >= threshold].index.tolist()
    if not suspicious_ips:
        suspicious_ips = [ranked.index[0]]

    node_scores: dict[str, dict[str, Any]] = {}
    details: list[SuspiciousNodeDetail] = []

    for ip in ip_list:
        row = X.loc[ip]
        feats_dict = row.to_dict()
        fp = fingerprint_bundle_for_source(feats_dict)
        gsc = float(final_graph.loc[ip])
        bsc = float(final_behavior.loc[ip])
        asc = float(final_anomaly.loc[ip])
        fsc = float(final.loc[ip])
        is_sus = ip in suspicious_ips or fsc >= threshold

        node_scores[ip] = {
            "graph_score": gsc,
            "behavior_score": bsc,
            "anomaly_score": asc,
            "final_score": fsc,
            "fingerprint_id": fp["fingerprint_id"],
            "cluster_id": cluster_id.get(ip),
            "is_suspicious": bool(is_sus),
            "avg_interval_sec": float(row.get("mean_interval_sec") or 0.0),
            "evidence": {
                "interval_consistency": float(row.get("interval_consistency") or 0),
                "header_order_concentration": float(row.get("header_order_concentration") or 0),
                "header_value_repetition": float(row.get("header_value_repetition") or 0),
                "endpoint_concentration_hhi": float(row.get("endpoint_concentration_hhi") or 0),
                "ua_diversity": float(row.get("ua_diversity") or 0),
                "request_count": int(row.get("request_count") or 0),
            },
        }

    for ip in ranked.index:
        sc = node_scores[ip]
        conf = 100.0 * clamp01(sc["final_score"] * 1.05)
        expl = _build_explanation(ip, sc, X.loc[ip])
        details.append(
            SuspiciousNodeDetail(
                source_ip=ip,
                confidence=round(conf, 1),
                graph_score=round(sc["graph_score"], 4),
                behavior_score=round(sc["behavior_score"], 4),
                anomaly_score=round(sc["anomaly_score"], 4),
                final_score=round(sc["final_score"], 4),
                explanation=expl,
                fingerprint_id=sc.get("fingerprint_id"),
                evidence=sc.get("evidence", {}),
            )
        )

    # Keep only top 15 in API list
    details = sorted(details, key=lambda d: d.final_score, reverse=True)[:15]
    return node_scores, details


def _build_explanation(ip: str, sc: dict[str, Any], row: pd.Series) -> str:
    parts: list[str] = []
    ev = sc.get("evidence", {})
    if sc["graph_score"] >= 0.55:
        parts.append("unusually high graph influence relative to peers")
    if ev.get("interval_consistency", 0) >= 0.55:
        parts.append("highly regular beacon-like request intervals")
    if ev.get("header_order_concentration", 0) >= 0.55 or ev.get("header_value_repetition", 0) >= 0.55:
        parts.append("repeated header ordering and metadata reuse")
    if ev.get("endpoint_concentration_hhi", 0) >= 0.45:
        parts.append("tight concentration on a small set of endpoints")
    if sc["anomaly_score"] >= 0.55:
        parts.append("multivariate anomaly vs typical enterprise clients")
    if not parts:
        parts.append("composite risk from blended graph, behavior, and anomaly signals")

    head = (
        f"Source {ip} shows {', '.join(parts)}, consistent with hidden command-and-control or automated callback behavior."
    )
    return head


def benign_vs_suspicious_summary(
    feat_df: pd.DataFrame,
    suspicious_ips: set[str],
) -> dict[str, Any]:
    if feat_df.empty:
        return {}
    sus = feat_df.reindex(list(suspicious_ips)).dropna(how="all")
    ben = feat_df.drop(index=[i for i in suspicious_ips if i in feat_df.index], errors="ignore")
    if ben.empty:
        ben = feat_df

    def pack(df: pd.DataFrame) -> dict[str, float]:
        if df.empty:
            return {}
        return {
            "avg_interval_consistency": float(df["interval_consistency"].mean()),
            "avg_header_concentration": float(df["header_order_concentration"].mean()),
            "avg_endpoint_hhi": float(df["endpoint_concentration_hhi"].mean()),
            "avg_request_count": float(df["request_count"].mean()),
        }

    return {
        "suspicious": pack(sus),
        "benign_sample": pack(ben.head(max(10, len(ben)))),
    }
