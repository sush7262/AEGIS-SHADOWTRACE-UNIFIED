"""Stable per-source fingerprints from headers, timing, endpoints, and UA."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


def header_key_signature(headers: dict[str, str]) -> str:
    return "|".join(headers.keys())


def header_value_repetition_ratio(rows: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    sigs = [tuple(sorted(h.items())) for h in rows]
    c = Counter(sigs)
    top = c.most_common(1)[0][1]
    return top / len(rows)


def interval_signature(intervals: list[float], bins: int = 8) -> str:
    if not intervals:
        return "none"
    avg = sum(intervals) / len(intervals)
    if avg <= 0:
        return "flat"
    # Quantize coefficient of variation into a short token
    import math

    var = sum((x - avg) ** 2 for x in intervals) / max(1, len(intervals) - 1)
    std = math.sqrt(var)
    cv = std / avg if avg else 0.0
    q = int(min(bins - 1, max(0, cv * bins / 2)))
    return f"cv{q}"


def endpoint_pattern(endpoints: list[str], top_k: int = 4) -> str:
    ctr = Counter(endpoints)
    parts = [f"{ep}:{n}" for ep, n in ctr.most_common(top_k)]
    return ">".join(parts)


def ua_pattern(user_agents: list[str]) -> str:
    ctr = Counter(user_agents)
    top = ctr.most_common(1)
    if not top:
        return "unknown"
    ua, n = top[0]
    ratio = n / len(user_agents)
    return f"{ua[:48]}|{ratio:.2f}"


def build_fingerprint_id(
    header_sig: str,
    ua_pat: str,
    int_sig: str,
    ep_pat: str,
) -> str:
    raw = f"{header_sig}::{ua_pat}::{int_sig}::{ep_pat}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def fingerprint_bundle_for_source(features: dict[str, Any]) -> dict[str, Any]:
    hs = features.get("dominant_header_signature") or ""
    ua = ua_pattern(features.get("user_agents_list") or [])
    intervals = features.get("intervals_list") or []
    int_sig = interval_signature(intervals)
    eps = features.get("endpoints_list") or []
    ep_pat = endpoint_pattern(eps)
    fid = build_fingerprint_id(hs, ua, int_sig, ep_pat)
    return {
        "fingerprint_id": fid,
        "header_signature": hs,
        "interval_signature": int_sig,
        "endpoint_pattern": ep_pat,
        "ua_pattern": ua,
    }


def serialize_for_export(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))
