"""Optional filesystem watcher: drop JSON/JSONL into a folder → append/replace buffer + analyze."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from modules.shadowtrace.services.analysis_pipeline import run_full_analysis, validate_log_rows
from modules.shadowtrace.services.ingest_parser import parse_ingest_bytes
from modules.shadowtrace.services import log_buffer
from modules.shadowtrace.utils.helpers import get_session

_DEBOUNCE_SEC = 0.75
_extensions = (".json", ".jsonl")


class _Handler(FileSystemEventHandler):
    def __init__(self, on_file: Callable[[str], None]) -> None:
        super().__init__()
        self._on_file = on_file
        self._lock = threading.Lock()
        self._pending: dict[str, float] = {}

    def on_modified(self, event):  # type: ignore[override]
        self._handle(event)

    def on_created(self, event):  # type: ignore[override]
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        path = getattr(event, "src_path", "") or ""
        if not str(path).lower().endswith(_extensions):
            return
        with self._lock:
            self._pending[path] = time.time()

    def flush_due(self):
        now = time.time()
        with self._lock:
            due = [p for p, t in self._pending.items() if now - t >= _DEBOUNCE_SEC]
            for p in due:
                self._pending.pop(p, None)
        for p in due:
            self._on_file(p)


def _process_watch_file(path: str, watch_mode: str) -> None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        return
    rows = parse_ingest_bytes(data)
    if not rows:
        return
    good, _bad = validate_log_rows(rows)
    if not good:
        return
    if watch_mode == "replace":
        log_buffer.buffer_replace(good)
    else:
        log_buffer.buffer_extend(good)
    snap = log_buffer.buffer_snapshot()
    if not snap:
        return
    try:
        run_full_analysis(snap)
    except ValueError:
        return
    sess = get_session()
    sess["last_ingest_source"] = f"watch:{Path(path).name}"
    sess["last_ingest_at"] = time.time()


class WatchController:
    def __init__(self) -> None:
        self._observer: Observer | None = None
        self._timer: threading.Timer | None = None
        self._handler: _Handler | None = None
        self._watch_dir: str | None = None
        self._watch_mode: str = "append"

    def start(self, directory: str, watch_mode: str = "append") -> bool:
        self.stop()
        path = Path(directory).resolve()
        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)

        self._watch_dir = str(path)
        self._watch_mode = watch_mode
        sess = get_session()
        sess["watch_dir"] = self._watch_dir
        sess["watch_active"] = True

        def on_file(p: str):
            _process_watch_file(p, self._watch_mode)

        self._handler = _Handler(on_file)
        self._observer = Observer()
        self._observer.schedule(self._handler, self._watch_dir, recursive=False)
        self._observer.start()

        def tick():
            if self._handler:
                self._handler.flush_due()
            if self._observer and self._observer.is_alive():
                t = threading.Timer(0.5, tick)
                self._timer = t
                t.daemon = True
                t.start()

        tick()
        return True

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)
            self._observer = None
        self._handler = None
        get_session()["watch_active"] = False


_controller = WatchController()


def start_folder_watch_from_env() -> None:
    d = os.environ.get("SHADOWTRACE_WATCH_DIR", "").strip()
    if not d:
        return
    mode = os.environ.get("SHADOWTRACE_WATCH_MODE", "append").strip().lower()
    if mode not in ("append", "replace"):
        mode = "append"
    _controller.start(d, mode)


def stop_folder_watch() -> None:
    _controller.stop()
