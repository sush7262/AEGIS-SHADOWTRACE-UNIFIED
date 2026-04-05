"""Shared helpers and in-memory session cache for demo/analysis runs."""

from __future__ import annotations

from typing import Any

_cache: dict[str, Any] = {}


def get_session() -> dict[str, Any]:
    return _cache.setdefault("session", {})


def bump_analysis_revision() -> int:
    s = get_session()
    n = int(s.get("analysis_revision", 0)) + 1
    s["analysis_revision"] = n
    return n


def get_analysis_revision() -> int:
    return int(get_session().get("analysis_revision", 0))


def set_last_analysis(payload: dict[str, Any]) -> None:
    get_session()["last_analysis"] = payload


def get_last_analysis() -> dict[str, Any] | None:
    return get_session().get("last_analysis")


def set_last_logs(logs: list[dict[str, Any]]) -> None:
    get_session()["last_logs"] = logs


def get_last_logs() -> list[dict[str, Any]] | None:
    return get_session().get("last_logs")


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    if b == 0:
        return default
    return a / b
