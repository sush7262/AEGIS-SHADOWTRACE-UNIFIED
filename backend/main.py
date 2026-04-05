from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from contextlib import asynccontextmanager

# Import ShadowTrace modules
import sys
from pathlib import Path

# Add the project root to sys.path so we can import 'modules'
sys.path.append(str(Path(__file__).parent.parent))

from modules.shadowtrace.routes import analyze, generate, graph, ingest
from modules.shadowtrace.services.folder_watch import start_folder_watch_from_env, stop_folder_watch

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize ShadowTrace folder watch if enabled
    if os.getenv("ENABLE_SHADOWTRACE", "true").lower() == "true":
        # We might need to configure the watch folder path
        # For now, let's look for 'ingest_drop' in current or parent dir
        watch_path = Path(__file__).parent.parent / "ingest_drop"
        if not watch_path.exists():
            watch_path.mkdir(exist_ok=True)
        # Note: start_folder_watch_from_env reads from ENV
        os.environ["SHADOWTRACE_WATCH_DIR"] = str(watch_path)
        start_folder_watch_from_env()
    yield
    if os.getenv("ENABLE_SHADOWTRACE", "true").lower() == "true":
        stop_folder_watch()

app = FastAPI(
    title="AEGIS Unified Backend",
    description="Unified security intelligence platform combining AEGIS Forensics and ShadowTrace AI.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AEGIS Legacy Support (Serving CSVs) ---

@app.get("/{filename}.csv")
async def get_csv(filename: str):
    """Serves the CSV files for the original AEGIS dashboard."""
    # Look for files in project root
    file_path = Path(__file__).parent.parent / f"{filename}.csv"
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"CSV file {filename}.csv not found at {file_path}")

# --- ShadowTrace AI Modules ---

# Wrap ShadowTrace routers with /api/shadowtrace prefix
app.include_router(generate.router, prefix="/api/shadowtrace", tags=["shadowtrace"])
app.include_router(analyze.router, prefix="/api/shadowtrace", tags=["shadowtrace"])
app.include_router(graph.router, prefix="/api/shadowtrace", tags=["shadowtrace"])
app.include_router(ingest.router, prefix="/api/shadowtrace", tags=["shadowtrace"])

@app.get("/health")
@app.get("/api/shadowtrace/health")
def health():
    return {
        "status": "ok",
        "system": "AEGIS Unified",
        "shadowtrace_enabled": os.getenv("ENABLE_SHADOWTRACE", "true").lower() == "true"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
