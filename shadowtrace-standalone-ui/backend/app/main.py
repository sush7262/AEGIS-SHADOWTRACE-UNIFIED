"""ShadowTrace AI — FastAPI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analyze, generate, graph, ingest
from app.services.folder_watch import start_folder_watch_from_env, stop_folder_watch


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_folder_watch_from_env()
    yield
    stop_folder_watch()


app = FastAPI(
    title="ShadowTrace AI",
    description="Attribution and command-node discovery over noisy API/network logs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5175",
        "http://127.0.0.1:5176",
        "http://localhost:5176",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(analyze.router)
app.include_router(graph.router)
app.include_router(ingest.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "shadowtrace-ai", "version": "1.0.0"}
