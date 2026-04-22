"""Subtitle-stream detection helpers for task routers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def subtitle_cache_path(task_id: str, *, task_base_dir_loader: Callable[[str], Path]) -> Path:
    return task_base_dir_loader(task_id) / "subtitle_streams.json"


def detect_subtitle_streams(
    raw_file: Path,
    *,
    which: Callable[[str], str | None],
    run,
    json_loads: Callable[[str], Any] = json.loads,
) -> dict[str, Any]:
    if not raw_file.exists():
        return {"status": "unknown", "reason": "raw_missing"}

    ffprobe = which("ffprobe")
    if not ffprobe:
        return {"status": "unknown", "reason": "ffprobe_missing"}

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        str(raw_file),
    ]
    proc = run(cmd, stdout=-1, stderr=-1, text=True)
    if proc.returncode != 0:
        return {"status": "unknown", "reason": "ffprobe_failed"}

    try:
        payload = json_loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "unknown", "reason": "ffprobe_bad_json"}

    streams = payload.get("streams", []) or []
    subtitle_streams = [stream for stream in streams if stream.get("codec_type") == "subtitle"]
    minimal_streams = [
        {
            "index": stream.get("index"),
            "codec_name": stream.get("codec_name"),
            "codec_type": stream.get("codec_type"),
            "tags": stream.get("tags") or {},
        }
        for stream in subtitle_streams
    ]
    return {
        "status": "ok",
        "has_subtitle_stream": bool(subtitle_streams),
        "subtitle_streams": minimal_streams,
    }


def get_subtitle_detection(
    task_id: str,
    *,
    cache_path_loader: Callable[[str], Path],
    raw_path_loader: Callable[[str], Path],
    detect_subtitle_streams_loader: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    cache_path = cache_path_loader(task_id)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    result = detect_subtitle_streams_loader(raw_path_loader(task_id))
    try:
        cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return result
