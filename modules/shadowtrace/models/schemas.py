"""Pydantic models for API requests and responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    source_ip: str
    destination_service: str
    endpoint: str
    timestamp: str
    headers: dict[str, str] = Field(default_factory=dict)
    user_agent: str = ""
    method: str = "GET"
    status_code: int = 200
    request_size: int = 0
    response_time_ms: float = 0.0


class GenerateDataRequest(BaseModel):
    num_logs: int = Field(default=1200, ge=50, le=10000)
    seed: int | None = None


class AnalyzeRequest(BaseModel):
    logs: list[LogEntry]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    total_requests: int = 0
    avg_interval_sec: float | None = None
    anomaly_score: float | None = None
    behavior_score: float | None = None
    graph_score: float | None = None
    final_score: float | None = None
    fingerprint_id: str | None = None
    cluster_id: int | None = None
    is_suspicious: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: int
    methods: list[str] = Field(default_factory=list)


class GraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metrics: dict[str, Any] = Field(default_factory=dict)


class SuspiciousNodeDetail(BaseModel):
    source_ip: str
    confidence: float
    graph_score: float
    behavior_score: float
    anomaly_score: float
    final_score: float
    explanation: str
    fingerprint_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class SummaryResponse(BaseModel):
    total_nodes: int
    total_edges: int
    source_node_count: int
    suspicious_count: int
    top_suspect: str | None = None
    top_confidence: float = 0.0
    total_requests: int
    time_range: dict[str, str | None]
    ranked_suspicious: list[SuspiciousNodeDetail] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    graph: GraphPayload
    summary: SummaryResponse
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    charts: dict[str, Any] = Field(default_factory=dict)
    benign_vs_suspicious: dict[str, Any] = Field(default_factory=dict)
    export: dict[str, Any] = Field(default_factory=dict)
