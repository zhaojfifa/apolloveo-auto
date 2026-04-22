from __future__ import annotations

from fastapi import HTTPException
import pytest

import gateway.app.services.task_download_views as views
from gateway.app.services.task_download_views import (
    build_deliverable_download_redirect,
    build_not_ready_response,
    require_storage_key,
)


def test_require_storage_key_returns_existing_key(monkeypatch):
    monkeypatch.setattr(views, "object_exists", lambda key: key == "deliver/tasks/hf-1/raw.mp4")

    key = require_storage_key({"raw_path": "deliver/tasks/hf-1/raw.mp4"}, "raw_path", "missing")

    assert key == "deliver/tasks/hf-1/raw.mp4"


def test_require_storage_key_raises_for_missing_key(monkeypatch):
    monkeypatch.setattr(views, "object_exists", lambda _key: False)

    with pytest.raises(HTTPException) as excinfo:
        require_storage_key({"raw_path": "deliver/tasks/hf-1/raw.mp4"}, "raw_path", "missing")

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "missing"


def test_build_not_ready_response_keeps_task_status_shape():
    response = build_not_ready_response(
        {
            "task_id": "hf-1",
            "subtitles_status": "done",
            "dub_status": "pending",
            "scenes_status": "pending",
            "pack_status": "pending",
            "publish_status": "pending",
        },
        "pack",
        ["pack_key"],
        extra={"repair_attempted": True},
    )

    assert response.status_code == 409
    assert response.body
    assert b"repair_attempted" in response.body


def test_build_deliverable_download_redirect_uses_current_hot_follow_voiceover(monkeypatch):
    monkeypatch.setattr(views, "get_settings", lambda: object())
    monkeypatch.setattr(
        views,
        "hf_current_voiceover_asset",
        lambda _task_id, _task, _settings: {"key": "deliver/tasks/hf-1/current-audio.mp3"},
    )
    monkeypatch.setattr(views, "object_exists", lambda key: key == "deliver/tasks/hf-1/current-audio.mp3")
    monkeypatch.setattr(
        views,
        "get_download_url",
        lambda key, **kwargs: f"https://example.com/{key}?filename={kwargs.get('filename')}",
    )

    response = build_deliverable_download_redirect(
        "hf-1",
        {
            "task_id": "hf-1",
            "kind": "hot_follow",
            "target_lang": "vi",
        },
        "mm_audio",
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("deliver/tasks/hf-1/current-audio.mp3?filename=audio_vi.mp3")
