"""Tiny NDJSON logger used for debug-mode instrumentation.

This is intentionally dependency-free and best-effort: any logging failure is
silently ignored so Harbor trials are not disrupted.
"""

from __future__ import annotations

import json
import time
from contextvars import ContextVar
from typing import Any

_LOG_PATH = "/Users/asanshaygupta/Documents/Codes/Stanford/Research/sgicl/.cursor/debug.log"

_SESSION_ID = "debug-session"
_RUN_ID: ContextVar[str] = ContextVar("icicl_debug_run_id", default="unknown")


def set_run_id(run_id: str) -> None:
    _RUN_ID.set(run_id)


def get_run_id() -> str:
    return _RUN_ID.get()


def log(
    *,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> None:
    """Append one NDJSON line to the debug log (best-effort)."""
    payload = {
        "sessionId": _SESSION_ID,
        "runId": run_id or get_run_id(),
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        return
