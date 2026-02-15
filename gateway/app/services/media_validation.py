from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


MIN_AUDIO_BYTES = 1024
MIN_AUDIO_DURATION_SEC = 0.1
MIN_VIDEO_BYTES = 10 * 1024
MIN_VIDEO_DURATION_SEC = 0.1


def deliver_key(task_id: str, name: str) -> str:
    return f"deliver/tasks/{task_id}/{name}"


def probe_duration_seconds(path: str | Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0.0
    p = Path(path)
    if not p.exists():
        return 0.0
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        str(p),
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return 0.0
        payload = json.loads(proc.stdout or "{}")
        duration = float((payload.get("format") or {}).get("duration") or 0.0)
        return duration if duration > 0 else 0.0
    except Exception:
        return 0.0


def file_size_bytes(path: str | Path) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    try:
        return int(p.stat().st_size)
    except Exception:
        return 0


def media_meta_from_head(meta: dict | None) -> tuple[int, str | None]:
    if not isinstance(meta, dict):
        return 0, None
    try:
        size = int(meta.get("content_length") or 0)
    except Exception:
        size = 0
    ctype = meta.get("content_type")
    return size, (str(ctype) if ctype else None)


def assert_local_audio_ok(path: str | Path) -> tuple[int, float]:
    size = file_size_bytes(path)
    dur = probe_duration_seconds(path)
    if size < MIN_AUDIO_BYTES or dur <= MIN_AUDIO_DURATION_SEC:
        raise ValueError("EMPTY_OR_INVALID_AUDIO")
    return size, dur


def assert_local_video_ok(path: str | Path) -> tuple[int, float]:
    size = file_size_bytes(path)
    dur = probe_duration_seconds(path)
    if size < MIN_VIDEO_BYTES or dur <= MIN_VIDEO_DURATION_SEC:
        raise ValueError("EMPTY_OR_INVALID_VIDEO")
    return size, dur


def assert_artifact_ready(
    *,
    kind: str,
    key: str | None,
    exists_fn,
    head_fn,
) -> tuple[int, str | None]:
    if not key:
        raise ValueError(f"{kind}_MISSING")
    if not exists_fn(key):
        raise ValueError(f"{kind}_MISSING")
    size, ctype = media_meta_from_head(head_fn(key))
    min_bytes = MIN_AUDIO_BYTES if kind == "audio" else MIN_VIDEO_BYTES
    if size < min_bytes:
        raise ValueError(f"{kind}_INVALID")
    return size, ctype
