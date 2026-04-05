"""Rolling in-memory buffer for streaming / append ingest (real-time style)."""

from __future__ import annotations

import os
from collections import deque
from typing import Any

_MAX = int(os.environ.get("SHADOWTRACE_BUFFER_MAX", "100000"))

_buffer: deque[dict[str, Any]] = deque(maxlen=_MAX)


def buffer_clear() -> None:
    _buffer.clear()


def buffer_replace(rows: list[dict[str, Any]]) -> int:
    _buffer.clear()
    return buffer_extend(rows)


def buffer_extend(rows: list[dict[str, Any]]) -> int:
    for r in rows:
        _buffer.append(r)
    return len(_buffer)


def buffer_snapshot() -> list[dict[str, Any]]:
    return list(_buffer)


def buffer_len() -> int:
    return len(_buffer)
