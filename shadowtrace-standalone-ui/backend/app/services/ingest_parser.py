"""Parse JSON array, wrapped object, or NDJSON from raw bytes."""

from __future__ import annotations

import json
from typing import Any


def parse_ingest_bytes(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        return []

    # Single JSON array or { "logs": [...] }
    try:
        doc = json.loads(text)
        if isinstance(doc, list):
            return [x for x in doc if isinstance(x, dict)]
        if isinstance(doc, dict) and "logs" in doc and isinstance(doc["logs"], list):
            return [x for x in doc["logs"] if isinstance(x, dict)]
        if isinstance(doc, dict):
            return [doc]
    except json.JSONDecodeError:
        pass

    # NDJSON
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except json.JSONDecodeError:
            continue
    return rows
