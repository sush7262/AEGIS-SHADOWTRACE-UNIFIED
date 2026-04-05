"""Full analysis pipeline: features, graph, detection, charts."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analysis_pipeline import run_full_analysis

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest):
    logs = [row.model_dump() for row in body.logs]
    return run_full_analysis(logs)
