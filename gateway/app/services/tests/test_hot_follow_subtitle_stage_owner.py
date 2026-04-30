from __future__ import annotations

from gateway.app.services.hot_follow_subtitle_authority import (
    helper_translation_telemetry_updates,
    persist_hot_follow_authoritative_target_subtitle,
)
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_current_attempt_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.voice_state import hf_dub_matches_current_subtitle


VI_SRT = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
ZH_SRT = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str):
        return dict(self.task) if self.task.get("task_id") == task_id else None

    def upsert(self, task_id: str, updates: dict):
        assert self.task.get("task_id") == task_id
        self.task.update(updates)


def test_manual_save_materializes_authoritative_current_vi_srt():
    task_id = "hf-stage-vi"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "dub_status": "done",
            "mm_audio_key": f"deliver/tasks/{task_id}/voiceover/audio_mm.dry.mp3",
            "subtitles_content_hash": "OLD",
            "dub_source_subtitles_content_hash": "OLD",
        }
    )

    saved = persist_hot_follow_authoritative_target_subtitle(
        task_id,
        repo.get(task_id),
        repo=repo,
        text=VI_SRT,
        text_mode="manual_target_subtitle_save",
        target_lang="vi",
        source_texts=(ZH_SRT,),
        expected_subtitle_source="vi.srt",
        persist_artifact_fn=lambda _text: f"deliver/tasks/{task_id}/vi.srt",
        content_hash_fn=lambda _text: "NEW",
        now_fn=lambda: "2026-04-30T01:00:00+00:00",
    )

    assert saved["subtitle_stage_owner"] == "hot_follow_subtitle_stage_v1"
    assert saved["subtitle_stage_action"] == "manual_target_subtitle_materialize"
    assert saved["origin_subtitle_artifact_exists"] is True
    assert saved["target_subtitle_artifact_exists"] is True
    assert saved["target_subtitle_materialized"] is True
    assert saved["target_subtitle_authoritative_source"] is True
    assert saved["target_subtitle_current"] is True
    assert saved["target_subtitle_current_reason"] == "ready"
    assert saved["mm_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["vi_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["subtitles_content_hash"] == "NEW"
    assert saved["dub_status"] == "pending"
    assert saved["mm_audio_key"] is None
    assert saved["dub_source_subtitles_content_hash"] is None


def test_helper_telemetry_cannot_promote_or_close_subtitle_truth():
    updates = helper_translation_telemetry_updates(
        "hf-helper",
        {"task_id": "hf-helper", "kind": "hot_follow"},
        helper_updates={
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitles_status": "ready",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_materialized": True,
            "mm_srt_path": "deliver/tasks/hf-helper/vi.srt",
        },
    )

    assert updates == {
        "subtitle_helper_status": "failed",
        "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
    }


def test_helper_pending_unavailable_exhausted_never_counts_as_subtitle_closure_truth():
    for status, output_state, reason in (
        ("helper_output_pending", "helper_output_pending", "helper_translate_pending"),
        ("helper_output_unavailable", "helper_output_unavailable", "helper_translate_failed"),
        ("failed", "helper_output_unavailable", "helper_translate_provider_exhausted"),
    ):
        current_attempt = build_hot_follow_current_attempt_summary(
            voice_state={
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "dub_current": False,
            },
            subtitle_lane={
                "subtitle_ready": False,
                "subtitle_artifact_exists": False,
                "target_subtitle_current": False,
                "target_subtitle_authoritative_source": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "parse_source_text": ZH_SRT,
                "helper_translate_status": status,
                "helper_translate_output_state": output_state,
                "helper_translate_error_reason": reason,
            },
            dub_status="pending",
            compose_status="pending",
            composed_reason="compose_not_done",
            artifact_facts={
                "helper_translate_status": status,
                "helper_translate_output_state": output_state,
                "helper_translate_error_reason": reason,
                "compose_input": {"mode": "direct", "ready": True, "blocked": False},
                "audio_lane": {
                    "tts_voiceover_exists": False,
                    "source_audio_preserved": False,
                    "bgm_configured": False,
                    "no_tts": False,
                },
            },
        )

        assert current_attempt["audio_ready"] is False
        assert current_attempt["compose_execute_allowed"] is False
        assert current_attempt["current_subtitle_source"] is None


def test_audio_currentness_depends_on_authoritative_current_subtitle_truth():
    matches, reason = hf_dub_matches_current_subtitle(
        {
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "subtitles_content_hash": "HASH",
            "dub_source_subtitles_content_hash": "HASH",
        }
    )

    assert matches is False
    assert reason == "subtitle_missing"


def test_compose_readiness_depends_on_authoritative_current_subtitle_and_current_audio():
    state = compute_hot_follow_state(
        {"task_id": "hf-compose-stage", "kind": "hot_follow"},
        {
            "task_id": "hf-compose-stage",
            "final": {"exists": True, "fresh": True},
            "subtitles": {
                "subtitle_artifact_exists": True,
                "subtitle_ready": True,
                "target_subtitle_current": True,
                "target_subtitle_authoritative_source": True,
                "actual_burn_subtitle_source": "vi.srt",
            },
            "audio": {
                "status": "done",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "voiceover_url": "/v1/tasks/hf-compose-stage/audio_mm",
            },
            "artifact_facts": {
                "final_exists": True,
                "compose_input": {"mode": "direct", "ready": True, "blocked": False},
                "audio_lane": {
                    "tts_voiceover_exists": True,
                    "source_audio_preserved": False,
                    "bgm_configured": False,
                    "no_tts": False,
                },
            },
        },
    )

    assert state["ready_gate"]["subtitle_ready"] is True
    assert state["ready_gate"]["audio_ready"] is True
    assert state["ready_gate"]["compose_ready"] is True
