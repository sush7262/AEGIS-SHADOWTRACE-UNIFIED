"""Synthetic log generation endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import GenerateDataRequest
from app.services.data_generator import generate_synthetic_logs, strip_internal_labels
from app.utils.helpers import set_last_logs

router = APIRouter(tags=["generate"])


@router.post("/generate-data")
def generate_data(body: GenerateDataRequest | None = None):
    """Create synthetic benign + blended C2 traffic for demo runs."""
    body = body or GenerateDataRequest()
    raw = generate_synthetic_logs(num_logs=body.num_logs, seed=body.seed)
    clean = strip_internal_labels(raw)
    set_last_logs(clean)
    return {
        "ok": True,
        "count": len(clean),
        "logs": clean,
        "message": "Synthetic dataset ready. POST /analyze with { \"logs\": [...] } or use dashboard Generate + Analyze.",
    }
