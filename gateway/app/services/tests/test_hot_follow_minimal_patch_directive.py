from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gateway.app.services.hot_follow_flow_actions import (
    LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW,
    MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
    TargetSubtitleMaterializationFailure,
    local_preserve_to_subtitle_dub_flow,
    materialize_target_subtitle_from_origin,
)
from gateway.app.services.hot_follow_helper_translation import helper_translate_success_updates
from gateway.app.services.hot_follow_translation_pending import hot_follow_translation_waiting_diagnostic
from gateway.app.services.source_audio_policy import source_audio_policy_from_task


ORIGIN_SRT = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
VI_SRT = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str):
        return dict(self.task) if self.task.get("task_id") == task_id else None

    def upsert(self, task_id: str, updates: dict):
        assert task_id == self.task["task_id"]
        self.task.update(updates)


def _hash(text: str | None) -> str | None:
    return f"hash:{len(str(text or ''))}"


def test_phase_a_materialize_target_subtitle_from_origin_writes_authoritative_vi_srt():
    task_id = "hf-minimal-url-materialize"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "vi",
        "content_lang": "vi",
        "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
        "origin_subtitle_artifact_exists": True,
        "target_subtitle_current": False,
        "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
        "subtitle_helper_status": "ready",
        **helper_translate_success_updates(input_text=ORIGIN_SRT, translated_text=VI_SRT, target_lang="vi"),
    }
    repo = _Repo(task)

    saved = materialize_target_subtitle_from_origin(
        task_id,
        task,
        repo=repo,
        origin_text=ORIGIN_SRT,
        target_lang="vi",
        expected_origin_key=task["origin_srt_path"],
        expected_subtitle_source="vi.srt",
        translate_origin_srt_fn=lambda origin_text, target_lang: VI_SRT,
        persist_artifact_fn=lambda text: f"deliver/tasks/{task_id}/vi.srt",
        content_hash_fn=_hash,
    )

    assert saved["subtitle_stage_owner"] == "hot_follow_subtitle_stage_v1"
    assert saved["subtitle_stage_action"] == MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN
    assert saved["subtitles_override_mode"] == MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN
    assert saved["target_subtitle_materialization_action"] == MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN
    assert saved["target_subtitle_materialization_status"] == "ready"
    assert saved["mm_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["vi_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["target_subtitle_materialized"] is True
    assert saved["target_subtitle_authoritative_source"] is True
    assert saved["target_subtitle_current"] is True


def test_phase_a_origin_srt_alone_and_helper_success_do_not_write_target_truth():
    updates = helper_translate_success_updates(input_text=ORIGIN_SRT, translated_text=VI_SRT, target_lang="vi")

    assert "target_subtitle_current" not in updates
    assert "target_subtitle_materialized" not in updates
    assert "mm_srt_path" not in updates
    assert "vi_srt_path" not in updates


def test_phase_a_materialization_failure_is_typed_for_stale_source():
    task_id = "hf-minimal-stale-source"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "vi",
        "origin_srt_path": f"deliver/tasks/{task_id}/origin-new.srt",
    }
    repo = _Repo(task)

    with pytest.raises(TargetSubtitleMaterializationFailure) as exc:
        materialize_target_subtitle_from_origin(
            task_id,
            task,
            repo=repo,
            origin_text=ORIGIN_SRT,
            target_lang="vi",
            expected_origin_key=f"deliver/tasks/{task_id}/origin-old.srt",
            expected_subtitle_source="vi.srt",
            translate_origin_srt_fn=lambda origin_text, target_lang: VI_SRT,
            persist_artifact_fn=lambda text: f"deliver/tasks/{task_id}/vi.srt",
            content_hash_fn=_hash,
        )

    assert exc.value.code == "stale_source"


def test_phase_b_translation_waiting_detector_distinguishes_active_from_stale():
    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    active = hot_follow_translation_waiting_diagnostic(
        {
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "subtitles_status": "running",
            "updated_at": (now - timedelta(seconds=30)).isoformat(),
        },
        now_fn=lambda: now,
        stale_after_seconds=300,
    )
    stale = hot_follow_translation_waiting_diagnostic(
        {
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "subtitles_status": "pending",
            "updated_at": (now - timedelta(hours=2)).isoformat(),
        },
        now_fn=lambda: now,
        stale_after_seconds=300,
    )

    assert active["classification"] == "active_translation_running"
    assert active["active"] is True
    assert active["stale"] is False
    assert stale["classification"] == "stale_pending_without_progress"
    assert stale["active"] is False
    assert stale["stale"] is True


def test_phase_c_local_preserve_to_subtitle_dub_flow_queues_materialization_without_subtitle_truth():
    task_id = "hf-minimal-local-switch"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "source_type": "local",
        "platform": "local",
        "config": {"source_audio_policy": "preserve"},
        "pipeline_config": {"source_audio_policy": "preserve", "bgm_strategy": "keep"},
        "target_subtitle_current": False,
        "target_subtitle_materialized": False,
        "dub_status": "skipped",
        "compose_status": "done",
    }
    repo = _Repo(task)

    updated = local_preserve_to_subtitle_dub_flow(repo, task_id, task, reason="operator requested dub")

    assert updated["hot_follow_flow_stage_action"] == LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW
    assert source_audio_policy_from_task(updated) == "mute"
    assert updated["target_subtitle_materialization_action"] == MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN
    assert updated["target_subtitle_materialization_status"] == "pending"
    assert updated["target_subtitle_current"] is False
    assert updated["target_subtitle_materialized"] is False
    assert updated["dub_status"] == "pending"
    assert updated["compose_status"] == "pending"
