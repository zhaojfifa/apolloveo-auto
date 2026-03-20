from __future__ import annotations

from types import SimpleNamespace

from gateway.app.services import task_view_helpers


def test_compute_composed_state_marks_final_stale_when_audio_sha_changes(monkeypatch):
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-final"},
    )
    monkeypatch.setattr(task_view_helpers, "media_meta_from_head", lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")))
    monkeypatch.setattr(
        "gateway.app.services.voice_state.collect_voice_execution_state",
        lambda _task, _settings: {"audio_ready": True, "audio_ready_reason": "ready"},
    )
    monkeypatch.setattr(
        task_view_helpers,
        "get_settings",
        lambda: SimpleNamespace(),
    )

    task = {
        "task_id": "hf-freshness-1",
        "final_video_key": "deliver/tasks/hf-freshness-1/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "audio-current",
        "final_source_audio_sha256": "audio-old",
        "subtitles_override_updated_at": "2026-03-20T10:00:00+00:00",
        "final_source_subtitle_updated_at": "2026-03-20T10:00:00+00:00",
        "final_updated_at": "2026-03-20T10:01:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-freshness-1")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is False
    assert composed["final_stale_reason"] == "final_stale_after_dub"
    assert composed["composed_ready"] is False
    assert composed["composed_reason"] == "final_stale_after_dub"


def test_compute_composed_state_promotes_fresh_final_after_successful_recompose(monkeypatch):
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-final-new"},
    )
    monkeypatch.setattr(task_view_helpers, "media_meta_from_head", lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")))
    monkeypatch.setattr(
        "gateway.app.services.voice_state.collect_voice_execution_state",
        lambda _task, _settings: {"audio_ready": True, "audio_ready_reason": "ready"},
    )
    monkeypatch.setattr(task_view_helpers, "get_settings", lambda: SimpleNamespace())

    task = {
        "task_id": "hf-freshness-2",
        "final_video_key": "deliver/tasks/hf-freshness-2/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "audio-current",
        "final_source_audio_sha256": "audio-current",
        "subtitles_override_updated_at": "2026-03-21T10:00:00+00:00",
        "final_source_subtitle_updated_at": "2026-03-21T10:00:00+00:00",
        "final_updated_at": "2026-03-21T10:02:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-freshness-2")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
    assert composed["composed_reason"] == "ready"
