"""Real-time style ingest: multipart file upload + buffer status."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from modules.shadowtrace.services.analysis_pipeline import run_full_analysis, validate_log_rows
from modules.shadowtrace.services.ingest_parser import parse_ingest_bytes
from modules.shadowtrace.services import log_buffer
from modules.shadowtrace.utils.helpers import get_analysis_revision, get_session

router = APIRouter(prefix="/ingest", tags=["ingest"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.get("/status")
def ingest_status():
    s = get_session()
    return {
        "buffer_rows": log_buffer.buffer_len(),
        "analysis_revision": get_analysis_revision(),
        "watch_dir": s.get("watch_dir"),
        "watch_active": bool(s.get("watch_active")),
        "last_ingest_source": s.get("last_ingest_source"),
        "last_ingest_at": s.get("last_ingest_at"),
    }


@router.delete("/buffer")
def clear_buffer():
    log_buffer.buffer_clear()
    get_session()["last_ingest_source"] = "manual_clear"
    return {"ok": True, "buffer_rows": 0}


@router.post("/upload")
def ingest_upload(
    file: UploadFile = File(...),
    mode: Literal["replace", "append"] = Query("replace", description="Replace buffer or append for rolling window"),
):
    import time

    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File larger than {MAX_UPLOAD_BYTES} bytes")
    rows = parse_ingest_bytes(raw)
    if not rows:
        raise HTTPException(status_code=400, detail="No JSON rows parsed from file (expect array, {logs:[]}, or NDJSON).")

    good, bad = validate_log_rows(rows)
    if not good:
        raise HTTPException(
            status_code=422,
            detail={"message": "No valid log rows", "errors": bad[:50], "error_count": len(bad)},
        )

    if mode == "replace":
        log_buffer.buffer_replace(good)
    else:
        log_buffer.buffer_extend(good)

    snap = log_buffer.buffer_snapshot()
    try:
        resp = run_full_analysis(snap)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    sess = get_session()
    sess["last_ingest_source"] = f"upload:{file.filename}"
    sess["last_ingest_at"] = time.time()

    return {
        "ok": True,
        "mode": mode,
        "parsed_rows": len(rows),
        "accepted_rows": len(good),
        "skipped_rows": len(bad),
        "buffer_rows": log_buffer.buffer_len(),
        "warnings": bad[:20],
        "revision": get_analysis_revision(),
        "analysis": resp.model_dump(),
    }
