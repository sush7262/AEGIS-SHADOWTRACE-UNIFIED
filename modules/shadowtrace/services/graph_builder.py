"""Build NetworkX interaction graph and export D3-friendly JSON."""

from __future__ import annotations

from typing import Any

import networkx as nx
from modules.shadowtrace.models.schemas import GraphEdge, GraphNode, GraphPayload


def build_graph_from_logs(
    logs: list[dict[str, Any]],
    node_scores: dict[str, dict[str, Any]] | None = None,
) -> tuple[nx.Graph, GraphPayload]:
    """
    Bipartite-style undirected graph: source_ip <-> destination_service.
    Node ids prefixed to avoid collisions: ip:10.0.1.1 and svc:api.foo
    """
    G = nx.Graph()
    edge_counts: dict[tuple[str, str], int] = {}
    edge_methods: dict[tuple[str, str], list[str]] = {}

    for row in logs:
        sip = row["source_ip"]
        svc = row["destination_service"]
        sid = f"ip:{sip}"
        tid = f"svc:{svc}"
        key = (sid, tid) if sid < tid else (tid, sid)
        a, b = key
        edge_counts[key] = edge_counts.get(key, 0) + 1
        edge_methods.setdefault(key, []).append(row.get("method") or "GET")

        G.add_node(sid, entity_type="source", label=sip)
        G.add_node(tid, entity_type="service", label=svc)

    for (a, b), w in edge_counts.items():
        G.add_edge(a, b, weight=w)

    # Degree / centrality on combined graph
    deg = nx.degree_centrality(G)
    bet = nx.betweenness_centrality(G, weight="weight", normalized=True)
    try:
        pr = nx.pagerank(G, weight="weight")
    except Exception:
        pr = {n: 0.0 for n in G.nodes}

    req_per_source: dict[str, int] = {}
    for row in logs:
        sip = row["source_ip"]
        req_per_source[sip] = req_per_source.get(sip, 0) + 1

    nodes_out: list[GraphNode] = []
    for n, attr in G.nodes(data=True):
        et = attr.get("entity_type", "unknown")
        raw_label = attr.get("label", n)
        scores = {}
        if node_scores and et == "source":
            scores = node_scores.get(raw_label, {})
        elif node_scores and et == "service":
            scores = node_scores.get(n, {})

        is_suspicious = bool(scores.get("is_suspicious", False))
        meta = {
            "entity_type": et,
            "weighted_degree": float(sum(G[n][nb]["weight"] for nb in G.neighbors(n))),
        }
        gn = GraphNode(
            id=n,
            label=raw_label,
            type=et,
            total_requests=int(req_per_source.get(raw_label, 0)) if et == "source" else 0,
            avg_interval_sec=scores.get("avg_interval_sec"),
            anomaly_score=scores.get("anomaly_score"),
            behavior_score=scores.get("behavior_score"),
            graph_score=scores.get("graph_score"),
            final_score=scores.get("final_score"),
            fingerprint_id=scores.get("fingerprint_id"),
            cluster_id=scores.get("cluster_id"),
            is_suspicious=is_suspicious,
            metadata={
                **meta,
                "degree_centrality": round(float(deg.get(n, 0.0)), 6),
                "betweenness": round(float(bet.get(n, 0.0)), 6),
                "pagerank": round(float(pr.get(n, 0.0)), 6),
            },
        )
        nodes_out.append(gn)

    edges_out: list[GraphEdge] = []
    for u, v, data in G.edges(data=True):
        w = int(data.get("weight", 1))
        key = (u, v) if u < v else (v, u)
        methods = list(set(edge_methods.get(key, [])))[:12]
        edges_out.append(GraphEdge(source=u, target=v, weight=w, methods=methods))

    metrics = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "density": float(nx.density(G)) if G.number_of_nodes() > 1 else 0.0,
    }

    return G, GraphPayload(nodes=nodes_out, edges=edges_out, metrics=metrics)


def subgraph_for_sources(G: nx.Graph, source_ips: list[str]) -> nx.Graph:
    """Induced subgraph on source nodes + their service neighbors."""
    ids = {f"ip:{ip}" for ip in source_ips}
    nbrs = set(ids)
    for i in ids:
        if i in G:
            nbrs.update(G.neighbors(i))
    return G.subgraph(nbrs).copy()
