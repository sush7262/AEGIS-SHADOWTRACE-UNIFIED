"""Cached graph and summary endpoints (last successful analysis)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.utils.helpers import get_last_analysis

router = APIRouter(tags=["graph"])


@router.get("/graph")
def get_graph():
    data = get_last_analysis()
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No analysis yet. POST /analyze or use Generate Data in the UI first.",
        )
    return {"graph": data["graph"], "summary": data.get("summary")}


@router.get("/summary")
def get_summary():
    data = get_last_analysis()
    if not data:
        raise HTTPException(status_code=404, detail="No analysis cached.")
    return data.get("summary", {})


@router.get("/snapshot")
def get_full_snapshot():
    """Full last analysis (graph, summary, timeline, charts) for live UI polling."""
    data = get_last_analysis()
    if not data:
        raise HTTPException(status_code=404, detail="No analysis cached.")
    return data


@router.get("/export")
def export_analysis():
    """Download-friendly JSON snapshot of the last ranked attribution."""
    data = get_last_analysis()
    if not data:
        raise HTTPException(status_code=404, detail="No analysis cached.")
    return data.get("export", {})
