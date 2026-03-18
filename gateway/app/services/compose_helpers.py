"""Compose flow-control helpers: locks, retry response, audio-fit algorithms.

Extracted from tasks.py as part of Phase 1.3 Port Merge.
"""
from __future__ import annotations

import threading
from typing import Any

from fastapi.responses import JSONResponse

from gateway.app.core.constants import COMPOSE_RETRY_AFTER_MS

# ── Per-task compose locks (module-level state) ──────────────────────────────
_COMPOSE_LOCKS_GUARD = threading.Lock()
_COMPOSE_LOCKS: dict[str, threading.Lock] = {}


def task_compose_lock(task_id: str) -> threading.Lock:
    """Return (or create) a per-task mutex that prevents concurrent composition."""
    with _COMPOSE_LOCKS_GUARD:
        lock = _COMPOSE_LOCKS.get(task_id)
        if lock is None:
            lock = threading.Lock()
            _COMPOSE_LOCKS[task_id] = lock
        return lock


def compose_in_progress_response(task_id: str) -> JSONResponse:
    """409 response indicating an ongoing compose for *task_id*."""
    return JSONResponse(
        status_code=409,
        content={
            "error": "compose_in_progress",
            "status": "running",
            "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
            "task_id": task_id,
        },
    )


# ── Audio-fit speed algorithms ───────────────────────────────────────────────

def build_atempo_chain(speed: float) -> str:
    """Build an ffmpeg ``atempo`` filter chain for the given *speed* multiplier."""
    try:
        value = float(speed)
    except Exception:
        value = 1.0
    value = max(0.5, min(100.0, value))
    factors: list[float] = []
    while value > 2.0:
        factors.append(2.0)
        value /= 2.0
    while value < 0.5:
        factors.append(0.5)
        value /= 0.5
    factors.append(value)
    parts: list[str] = []
    for factor in factors:
        if abs(factor - 2.0) < 1e-9:
            parts.append("atempo=2.0")
        elif abs(factor - 0.5) < 1e-9:
            parts.append("atempo=0.5")
        else:
            parts.append(f"atempo={factor:.6f}")
    return ",".join(parts)


def resolve_audio_fit_max_speed(pipeline_config: dict | None) -> tuple[float, str]:
    """Return ``(max_speed, source)`` from a pipeline config dict."""
    cfg = pipeline_config or {}
    raw = cfg.get("audio_fit_max_speed")
    source = "default"
    if raw in (None, "", "null"):
        speed = 1.25
    else:
        source = "operator"
        try:
            speed = float(raw)
        except Exception:
            speed = 1.25
    speed = max(1.0, min(2.0, speed))
    return speed, source


def compute_audio_fit_speeds(
    source_duration_sec: float,
    dubbed_duration_sec: float,
    max_speed: float,
) -> tuple[float, float]:
    """Return ``(need_speed, applied_speed)`` for audio-fit."""
    try:
        source = float(source_duration_sec)
    except Exception:
        source = 0.0
    try:
        dubbed = float(dubbed_duration_sec)
    except Exception:
        dubbed = 0.0
    safe_source = max(source, 1e-6)
    need_speed = max(1.0, dubbed / safe_source)
    applied_speed = min(max(1.0, float(max_speed or 1.25)), need_speed)
    return need_speed, applied_speed
