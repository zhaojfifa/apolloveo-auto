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


def test_compute_composed_state_uses_latest_compose_timestamps_to_clear_stale_projection(monkeypatch):
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-final-latest"},
    )
    monkeypatch.setattr(task_view_helpers, "media_meta_from_head", lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")))
    monkeypatch.setattr(
        "gateway.app.services.voice_state.collect_voice_execution_state",
        lambda _task, _settings: {"audio_ready": True, "audio_ready_reason": "ready"},
    )
    monkeypatch.setattr(task_view_helpers, "get_settings", lambda: SimpleNamespace())

    task = {
        "task_id": "hf-freshness-3",
        "final_video_key": "deliver/tasks/hf-freshness-3/final.mp4",
        "compose_status": "pending",
        "compose_last_status": "done",
        "audio_sha256": "audio-current",
        "final_source_audio_sha256": "audio-old",
        "dub_generated_at": "2026-03-21T10:00:00+00:00",
        "subtitles_override_updated_at": "2026-03-21T10:00:00+00:00",
        "compose_last_finished_at": "2026-03-21T10:02:00+00:00",
        "final_updated_at": "2026-03-21T10:02:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-freshness-3")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
    assert composed["composed_reason"] == "ready"


# ---------------------------------------------------------------------------
# Tests added for VeoSop05 hot-follow state reconciliation fix
# ---------------------------------------------------------------------------

def _setup_monkeypatches(monkeypatch):
    """Shared monkeypatch setup for compose freshness tests."""
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-v"},
    )
    monkeypatch.setattr(
        task_view_helpers,
        "media_meta_from_head",
        lambda meta: (int(meta.get("ContentLength") or 0), meta.get("Content-Type")),
    )
    monkeypatch.setattr(
        "gateway.app.services.voice_state.collect_voice_execution_state",
        lambda _task, _settings: {"audio_ready": True, "audio_ready_reason": "ready"},
    )
    monkeypatch.setattr(task_view_helpers, "get_settings", lambda: SimpleNamespace())


def test_compose_fresh_when_dub_generated_at_is_none(monkeypatch):
    """When dub_generated_at is None, compose should not be marked stale.

    Regression: coerce_datetime(None) returned datetime.now() causing the
    timestamp override to fail, making the final appear stale even when
    compose SHA matches.
    """
    _setup_monkeypatches(monkeypatch)
    task = {
        "task_id": "hf-coerce-1",
        "final_video_key": "deliver/tasks/hf-coerce-1/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "sha-match",
        "final_source_audio_sha256": "sha-match",
        # dub_generated_at intentionally absent
        # subtitles_override_updated_at intentionally absent
        "final_updated_at": "2026-03-20T12:00:00+00:00",
        "compose_last_finished_at": "2026-03-20T12:00:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-coerce-1")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
    assert composed["composed_reason"] == "ready"


def test_compose_fresh_timestamp_override_with_no_sha(monkeypatch):
    """Timestamp override clears staleness when compose finished after dub.

    When SHA tracking is absent (old compose), the timestamp comparison
    is the only override path.  dub_generated_at < compose_last_finished_at
    must clear the stale flag.
    """
    _setup_monkeypatches(monkeypatch)
    task = {
        "task_id": "hf-coerce-2",
        "final_video_key": "deliver/tasks/hf-coerce-2/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "sha-current",
        # final_source_audio_sha256 intentionally absent (old compose path)
        "dub_generated_at": "2026-03-20T10:00:00+00:00",
        "subtitles_override_updated_at": "2026-03-20T09:00:00+00:00",
        "compose_last_finished_at": "2026-03-20T12:00:00+00:00",
        "final_updated_at": "2026-03-20T12:00:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-coerce-2")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
    assert composed["composed_reason"] == "ready"


def test_compose_stale_cleared_after_successful_recompose_post_redub(monkeypatch):
    """Full re-dub → re-compose cycle: staleness must clear.

    Sequence: dub at T1 → compose at T2 (SHA match, timestamps correct).
    The final must be fresh, not stale-after-dub.
    """
    _setup_monkeypatches(monkeypatch)
    task = {
        "task_id": "hf-redub-recompose",
        "final_video_key": "deliver/tasks/hf-redub-recompose/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "sha-after-redub",
        "final_source_audio_sha256": "sha-after-redub",
        "dub_generated_at": "2026-03-21T08:00:00+00:00",
        "subtitles_override_updated_at": "2026-03-21T07:00:00+00:00",
        "final_source_subtitle_updated_at": "2026-03-21T07:00:00+00:00",
        "compose_last_finished_at": "2026-03-21T09:00:00+00:00",
        "final_updated_at": "2026-03-21T09:00:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-redub-recompose")

    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
    assert composed["composed_reason"] == "ready"


def test_compose_stale_persists_when_dub_after_compose(monkeypatch):
    """Final remains stale when dub happened AFTER the last compose."""
    _setup_monkeypatches(monkeypatch)
    task = {
        "task_id": "hf-stale-ok",
        "final_video_key": "deliver/tasks/hf-stale-ok/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "sha-new-dub",
        "final_source_audio_sha256": "sha-old-compose",
        "dub_generated_at": "2026-03-21T12:00:00+00:00",
        "subtitles_override_updated_at": "2026-03-21T07:00:00+00:00",
        "final_source_subtitle_updated_at": "2026-03-21T07:00:00+00:00",
        "compose_last_finished_at": "2026-03-21T09:00:00+00:00",
        "final_updated_at": "2026-03-21T09:00:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-stale-ok")

    assert composed["final"]["exists"] is True
    assert composed["final_fresh"] is False
    assert composed["final_stale_reason"] == "final_stale_after_dub"
    assert composed["composed_ready"] is False


def test_compose_fresh_with_empty_string_timestamps(monkeypatch):
    """Empty-string timestamps must not be coerced to datetime.now().

    Regression: coerce_datetime("") returned datetime.now(), which was always
    newer than compose_finished_at, preventing the override from clearing
    staleness.
    """
    _setup_monkeypatches(monkeypatch)
    task = {
        "task_id": "hf-empty-ts",
        "final_video_key": "deliver/tasks/hf-empty-ts/final.mp4",
        "compose_status": "done",
        "compose_last_status": "done",
        "audio_sha256": "sha-match",
        "final_source_audio_sha256": "sha-match",
        "dub_generated_at": "",
        "subtitles_override_updated_at": "",
        "compose_last_finished_at": "2026-03-21T09:00:00+00:00",
        "final_updated_at": "2026-03-21T09:00:00+00:00",
    }

    composed = task_view_helpers.compute_composed_state(task, "hf-empty-ts")

    assert composed["final_fresh"] is True
    assert composed["final_stale_reason"] is None
    assert composed["composed_ready"] is True
