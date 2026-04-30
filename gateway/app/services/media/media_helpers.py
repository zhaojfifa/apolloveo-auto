"""Media file helpers (M-02 absorption).

Attribution:
    Absorbed from SwiftCraft `backend/app/utils/media.py`
    Mapping row: docs/donor/swiftcraft_capability_mapping_v1.md M-02
    Donor commit pin: 62b6da0 (W1)
    Strategy: Wrap (file/upload + ffmpeg probe + thumbnail; behavior preserved)

Severance notes:
    - Donor cross-imported `app.models.task.InputMetadata` (SwiftCraft task model).
      Per Wave-1 red-line we do NOT pull in donor task / queue models. The dep
      is replaced with a local `MediaProbeResult` dataclass. Callers in Apollo
      adapt this into the appropriate `MediaResult`-shaped contract row at the
      adapter boundary (gateway adapter base / capability adapter); this module
      itself returns only the local primitive shape.
    - This file targets `gateway/app/services/media/media_helpers.py`. The
      pre-existing `gateway/app/services/media_helpers.py` (BGM upload, URL
      probe, pipeline merge) is a different surface — no name collision; no
      caller of the existing module needs to change.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MediaProbeResult:
    """Local, donor-severed shape for `probe_video` output.

    Replaces SwiftCraft `app.models.task.InputMetadata`. Pure data carrier; no
    persistence semantics. Apollo callers map this to the appropriate contract
    row at their own adapter boundary.
    """

    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_upload_file(upload_file, destination: Path) -> Path:
    ensure_dir(destination)
    suffix = Path(upload_file.filename or "").suffix
    file_path = destination / f"{uuid.uuid4().hex}{suffix}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


def probe_video(path: Path) -> Optional[MediaProbeResult]:
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams") or []
    format_info = data.get("format") or {}
    width = None
    height = None
    if streams:
        width = streams[0].get("width")
        height = streams[0].get("height")
    duration = None
    if format_info.get("duration"):
        try:
            duration = float(format_info["duration"])
        except ValueError:
            duration = None
    return MediaProbeResult(duration=duration, width=width, height=height)


def generate_thumbnail(video_path: Path, output_dir: Path) -> Optional[Path]:
    ensure_dir(output_dir)
    output_path = output_dir / f"{uuid.uuid4().hex}.jpg"
    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-ss", "00:00:01",
        "-frames:v", "1",
        str(output_path),
    ]
    try:
        subprocess.run(command, capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return output_path
