"""Synthetic network/API logs: benign noise + one hidden C2-style beaconing client."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any

# Internal label for validation only (stripped before API response unless debug)
LABEL_KEY = "_shadowtrace_label"

SERVICES = [
    "api.payments.internal",
    "auth.sso.corp",
    "cdn.static.edge",
    "search.index.svc",
    "notify.push.gateway",
    "inventory.wms.local",
    "hr.portal.app",
    "telemetry.metrics",
    "files.drive.internal",
    "crm.sync.worker",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) Safari/605.1.15",
    "okhttp/4.12.0",
    "curl/8.4.0",
    "python-requests/2.31.0",
    "Go-http-client/2.0",
    "Microsoft-Delivery-Optimization/10.0",
    "DatadogAgent/7.50.0",
]

METHODS_WEIGHT = [("GET", 0.55), ("POST", 0.3), ("PUT", 0.08), ("DELETE", 0.07)]


def _pick_method(rng: random.Random) -> str:
    u = rng.random()
    acc = 0.0
    for m, w in METHODS_WEIGHT:
        acc += w
        if u <= acc:
            return m
    return "GET"


def _benign_headers(rng: random.Random) -> dict[str, str]:
    keys_pool = [
        ("Accept", ["application/json", "text/html", "*/*"]),
        ("Content-Type", ["application/json", "text/plain"]),
        ("X-Request-Id", []),
        ("X-Forwarded-For", []),
        ("Accept-Language", ["en-US", "en-GB", "fr-FR"]),
        ("Cache-Control", ["no-cache", "max-age=0"]),
    ]
    rng.shuffle(keys_pool)
    n = rng.randint(2, 5)
    out: dict[str, str] = {}
    for i in range(n):
        k, vals = keys_pool[i % len(keys_pool)]
        if not vals:
            out[k] = f"{rng.randint(1, 1_000_000):06x}"
        else:
            out[k] = rng.choice(vals)
    return out


def _c2_headers(rng: random.Random, template: list[tuple[str, str]]) -> dict[str, str]:
    """Stable ordering with mild jitter on values."""
    out: dict[str, str] = {}
    for k, v in template:
        if k == "X-Session":
            out[k] = f"sess-{rng.randint(100, 199)}"  # narrow band
        elif k == "X-Trace":
            out[k] = v
        else:
            out[k] = v
    return out


def generate_synthetic_logs(num_logs: int = 1200, seed: int | None = None) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    base = datetime(2026, 4, 4, 8, 0, 0, tzinfo=timezone.utc)

    # Vary org size each run → graph node count changes (not stuck at ~55).
    pool_n = 28 + rng.randint(0, 58)  # 28–86 candidate IPs before dedupe
    benign_subnet = [f"10.0.{rng.randint(1, 220)}.{rng.randint(1, 250)}" for _ in range(pool_n)]
    c2_ip = "10.0.77.13"  # hidden in plain sight among 10.0.x.x
    if c2_ip not in benign_subnet:
        benign_subnet[rng.randrange(len(benign_subnet))] = c2_ip
    benign_subnet = list(set(benign_subnet))
    if c2_ip not in benign_subnet:
        benign_subnet.append(c2_ip)

    # Benign traffic only touches a random subset of services this "day" → fewer/more svc nodes.
    svc_pick_n = rng.randint(5, len(SERVICES))
    active_services = rng.sample(SERVICES, k=svc_pick_n)

    # C2 uses a fixed header template (ordered) — slight value reuse
    c2_header_template = [
        ("Accept", "*/*"),
        ("Content-Type", "application/octet-stream"),
        ("X-Trace", "st-7f3a"),
        ("X-Session", "sess-100"),
        ("User-Context", "batch-sync"),
    ]

    logs: list[dict[str, Any]] = []
    t_cursor = base

    c2_quota = max(40, min(num_logs - 20, int(num_logs * 0.09)))
    c2_interval_base = 58 + rng.randint(0, 8)
    eligible = list(range(int(num_logs * 0.06), num_logs))
    rng.shuffle(eligible)
    c2_positions = set(eligible[:c2_quota])

    for i in range(num_logs):
        is_c2 = i in c2_positions

        if is_c2:
            src = c2_ip
            # Blend: mostly one service but occasional decoy hits
            if rng.random() < 0.78:
                svc = "telemetry.metrics"
                ep = rng.choice(["/v1/batch", "/v1/ingest", "/v1/ping"])
            else:
                svc = rng.choice(["cdn.static.edge", "search.index.svc"])
                ep = rng.choice(["/health", "/assets/x", "/query"])
            method = "POST" if rng.random() < 0.65 else "GET"
            ua = "python-requests/2.31.0" if rng.random() < 0.85 else "curl/8.4.0"
            headers = _c2_headers(rng, c2_header_template)
            jitter = rng.gauss(0, 4)
            delta = max(5.0, c2_interval_base + jitter)
            status = 200 if rng.random() < 0.92 else 204
            req_size = int(rng.gauss(900, 120))
            rtt = max(8.0, rng.gauss(35, 6))
            label = "c2"
        else:
            src = rng.choice(benign_subnet)
            if src == c2_ip:
                src = rng.choice([x for x in benign_subnet if x != c2_ip] or benign_subnet)
            svc = rng.choice(active_services)
            ep = rng.choice(
                ["/v1/list", "/v2/item", "/search", "/upload", "/health", "/metrics", "/user/profile"]
            )
            method = _pick_method(rng)
            ua = rng.choice(USER_AGENTS)
            headers = _benign_headers(rng)
            delta = rng.expovariate(1.0 / 25.0) + rng.uniform(0.5, 6.0)
            status = rng.choices([200, 201, 304, 404, 500], weights=[0.82, 0.08, 0.05, 0.03, 0.02])[0]
            req_size = int(rng.lognormvariate(6, 1.2))
            rtt = max(5.0, rng.gauss(85, 55))
            label = "benign"

        t_cursor += timedelta(seconds=delta)
        entry = {
            "source_ip": src,
            "destination_service": svc,
            "endpoint": ep,
            "timestamp": t_cursor.isoformat().replace("+00:00", "Z"),
            "headers": headers,
            "user_agent": ua,
            "method": method,
            "status_code": status,
            "request_size": max(32, req_size),
            "response_time_ms": round(rtt, 2),
            LABEL_KEY: label,
        }
        logs.append(entry)

    rng.shuffle(logs)
    logs.sort(key=lambda x: x["timestamp"])

    return logs


def strip_internal_labels(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean = []
    for row in logs:
        d = {k: v for k, v in row.items() if k != LABEL_KEY}
        clean.append(d)
    return clean


def logs_fingerprint(logs: list[dict[str, Any]]) -> str:
    raw = json.dumps(logs[:50], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
