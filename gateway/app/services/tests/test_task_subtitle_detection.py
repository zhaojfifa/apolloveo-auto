from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from gateway.app.services import task_subtitle_detection


def test_detect_subtitle_streams_extracts_subtitle_rows(tmp_path):
    raw_file = tmp_path / "raw.mp4"
    raw_file.write_bytes(b"video")

    result = task_subtitle_detection.detect_subtitle_streams(
        raw_file,
        which=lambda _name: "/usr/bin/ffprobe",
        run=lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "streams": [
                        {"index": 0, "codec_type": "video", "codec_name": "h264"},
                        {"index": 2, "codec_type": "subtitle", "codec_name": "mov_text", "tags": {"language": "en"}},
                    ]
                }
            ),
            stderr="",
        ),
    )

    assert result["status"] == "ok"
    assert result["has_subtitle_stream"] is True
    assert result["subtitle_streams"] == [
        {
            "index": 2,
            "codec_name": "mov_text",
            "codec_type": "subtitle",
            "tags": {"language": "en"},
        }
    ]


def test_get_subtitle_detection_prefers_cache(tmp_path):
    cache_path = tmp_path / "subtitle_streams.json"
    cached = {"status": "ok", "has_subtitle_stream": False, "subtitle_streams": []}
    cache_path.write_text(json.dumps(cached), encoding="utf-8")

    result = task_subtitle_detection.get_subtitle_detection(
        "task-1",
        cache_path_loader=lambda _task_id: cache_path,
        raw_path_loader=lambda _task_id: Path("/should/not/be/read"),
        detect_subtitle_streams_loader=lambda _raw_path: {"status": "wrong"},
    )

    assert result == cached
