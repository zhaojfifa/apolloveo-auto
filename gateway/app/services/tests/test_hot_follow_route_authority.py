from __future__ import annotations

from gateway.app.services.contract_runtime.current_attempt_runtime import selected_route_from_state
from gateway.app.services.hot_follow_process_state import reduce_hot_follow_process_state
from gateway.app.services.hot_follow_route_authority import (
    HOT_FOLLOW_ROUTE_OWNER,
    SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW,
    materialize_local_tts_subtitle_route_action,
)
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_current_attempt_summary
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_operator_summary
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.utils.pipeline_config import parse_pipeline_config


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str):
        return dict(self.task) if self.task.get("task_id") == task_id else None

    def upsert(self, task_id: str, updates: dict):
        assert task_id == self.task["task_id"]
        self.task.update(updates)


def _compose_input() -> dict:
    return {"mode": "direct", "ready": True, "blocked": False}


def _preserve_audio_lane() -> dict:
    return {
        "mode": "source_audio_preserved_no_tts",
        "tts_voiceover_exists": False,
        "source_audio_policy": "preserve",
        "source_audio_preserved": True,
        "bgm_configured": False,
        "no_tts": True,
    }


def _subtitle_waiting() -> dict:
    return {
        "subtitle_ready": False,
        "subtitle_artifact_exists": False,
        "target_subtitle_current": False,
        "target_subtitle_authoritative_source": False,
        "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
        "parse_source_text": "source transcript",
        "edited_text": "",
        "srt_text": "",
        "dub_input_text": "",
    }


def test_formal_local_route_action_switches_preserve_testing_path_to_tts_flow():
    task_id = "hf-local-route-action"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "source_type": "local",
            "platform": "local",
            "config": {"source_audio_policy": "preserve"},
            "pipeline_config": {"source_audio_policy": "preserve", "bgm_strategy": "keep"},
            "dub_status": "skipped",
            "compose_status": "done",
            "final_fresh": True,
        }
    )

    updated = materialize_local_tts_subtitle_route_action(
        repo,
        task_id,
        repo.get(task_id),
        reason="operator wants translated dub",
    )

    assert updated["hot_follow_route_decision_owner"] == HOT_FOLLOW_ROUTE_OWNER
    assert updated["hot_follow_route_stage_action"] == SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW
    assert updated["hot_follow_route_target"] == "tts_replace_route"
    assert source_audio_policy_from_task(updated) == "mute"
    assert parse_pipeline_config(updated["pipeline_config"])["source_audio_policy"] == "mute"
    assert updated["dub_status"] == "pending"
    assert updated["compose_status"] == "pending"
    assert updated["final_fresh"] is False
    assert updated["final_stale_reason"] == "route_changed_to_tts_subtitle_flow"


def test_route_surfaces_consume_formal_route_truth_after_local_switch():
    task = {
        "task_id": "hf-local-route-unified",
        "kind": "hot_follow",
        "source_type": "local",
        "platform": "local",
        "hot_follow_route_decision_owner": HOT_FOLLOW_ROUTE_OWNER,
        "hot_follow_route_stage_action": SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW,
        "hot_follow_route_target": "tts_replace_route",
    }
    artifact_facts = {
        "compose_input": _compose_input(),
        "audio_lane": _preserve_audio_lane(),
        "hot_follow_route_decision_owner": HOT_FOLLOW_ROUTE_OWNER,
        "hot_follow_route_stage_action": SWITCH_LOCAL_TO_TTS_SUBTITLE_FLOW,
        "hot_follow_route_target": "tts_replace_route",
        "helper_translate_failed": True,
        "helper_translate_failed_voice_led": True,
        "helper_translate_status": "failed",
        "helper_translate_output_state": "helper_output_unavailable",
    }
    audio = {
        "audio_ready": False,
        "audio_ready_reason": "audio_missing",
        "dub_current": False,
        "no_dub": False,
        "no_dub_reason": None,
    }
    subtitles = {
        **_subtitle_waiting(),
        "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
    }

    process_state = reduce_hot_follow_process_state(
        task=task,
        state={"artifact_facts": artifact_facts, "audio": audio, "subtitles": subtitles},
    )
    route = selected_route_from_state(
        task,
        {"hot_follow_process_state": process_state, "artifact_facts": artifact_facts, "audio": audio, "subtitles": subtitles},
    )
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state=audio,
        subtitle_lane=subtitles,
        dub_status="pending",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=False,
    )
    ready_state = compute_hot_follow_state(
        task,
        {
            "task_id": task["task_id"],
            "subtitles": subtitles,
            "audio": audio,
            "artifact_facts": artifact_facts,
            "hot_follow_process_state": process_state,
            "current_attempt": current_attempt,
            "final": {"exists": False},
        },
    )
    operator_summary = build_hot_follow_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
        subtitle_ready=False,
    )

    assert process_state["selected_compose_route"] == "tts_replace_route"
    assert route["name"] == "tts_replace_route"
    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert ready_state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert operator_summary["selected_compose_route"] == "tts_replace_route"
    assert operator_summary["route_decision_owner"] == HOT_FOLLOW_ROUTE_OWNER
    assert process_state["no_dub"] is False
    assert current_attempt["no_dub_route_terminal"] is False
    assert ready_state["ready_gate"]["no_tts_compose_allowed"] is False
    assert current_attempt["helper_translate_failed"] is True
    assert current_attempt["compose_allowed"] is False
    assert current_attempt["compose_allowed_reason"] == "target_subtitle_translation_incomplete"


def test_preserve_source_testing_route_still_valid_without_switch_action():
    subtitles = _subtitle_waiting()
    artifact_facts = {"compose_input": _compose_input(), "audio_lane": _preserve_audio_lane()}
    audio = {"audio_ready": False, "audio_ready_reason": "audio_missing", "dub_current": False}

    process_state = reduce_hot_follow_process_state(
        task={"task_id": "hf-preserve-valid", "kind": "hot_follow"},
        state={"artifact_facts": artifact_facts, "audio": audio, "subtitles": subtitles},
    )
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state=audio,
        subtitle_lane=subtitles,
        dub_status="pending",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=False,
    )

    assert process_state["selected_compose_route"] == "preserve_source_route"
    assert current_attempt["selected_compose_route"] == "preserve_source_route"
    assert process_state["no_dub"] is True
    assert current_attempt["no_dub_route_terminal"] is True
