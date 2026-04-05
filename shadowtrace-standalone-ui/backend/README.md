# ShadowTrace AI — Backend

FastAPI service for log ingestion, graph construction (NetworkX), feature extraction, and fusion-based command-node attribution.

## Run locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base: `http://127.0.0.1:8000` — OpenAPI docs at `/docs`.

## Modules

| Path | Role |
|------|------|
| `app/routes/generate.py` | Synthetic log generation |
| `app/routes/analyze.py` | End-to-end pipeline |
| `app/routes/graph.py` | Cached graph + summary |
| `app/services/data_generator.py` | Benign + hidden C2 traffic |
| `app/services/feature_extractor.py` | Per-source behavioral features |
| `app/services/fingerprinting.py` | Stable fingerprint IDs |
| `app/services/graph_builder.py` | NetworkX → JSON graph |
| `app/services/detection_engine.py` | Centrality + behavior + IsolationForest |

## Endpoints

- `GET /health` — Liveness
- `POST /generate-data` — Synthetic dataset (`num_logs`, optional `seed`)
- `POST /analyze` — `{ "logs": [ ... ] }` → graph + scores + charts
- `GET /graph` — Last analysis graph payload
- `GET /summary` — Last analysis summary
- `GET /export` — Last ranked export JSON (for downloads)
- `GET /snapshot` — Full last analysis (graph + charts + timeline)
- `GET /ingest/status` — Buffer rows, revision, watch dir
- `POST /ingest/upload` — Multipart `file` + `?mode=replace|append`
- `DELETE /ingest/buffer` — Clear buffer

**Watch folder (optional):** `SHADOWTRACE_WATCH_DIR=../ingest_drop` (from `backend/`), `SHADOWTRACE_WATCH_MODE=append|replace`, `SHADOWTRACE_BUFFER_MAX=100000`.
