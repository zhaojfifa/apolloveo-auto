from pathlib import Path
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.deps import get_task_repository
from gateway.app.lines.base import LineRegistry
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.routers import tasks as tasks_router
from gateway.app.services import hot_follow_skills_advisory as skills_advisory
from gateway.app.services.hot_follow_route_state import build_hot_follow_current_attempt_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


class _Repo:
    def __init__(self):
        self._rows = {}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        cur = dict(self._rows.get(task_id) or {})
        cur.update(fields or {})
        self._rows[task_id] = cur
        return cur


def _patch_workbench_dependencies(monkeypatch):
    monkeypatch.setattr(hf_router, "_scene_pack_info", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(hf_router, "_deliverable_url", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(hf_router, "_hf_persisted_audio_state", lambda *_args, **_kwargs: {"exists": False, "voiceover_url": None})
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "missing",
            "dub_current": False,
            "dub_current_reason": "missing",
            "resolved_voice": None,
            "actual_provider": None,
            "requested_voice": None,
        },
    )


def _advisory_payload(
    *,
    ready_gate=None,
    artifact_facts=None,
    current_attempt=None,
    operator_summary=None,
):
    return {
        "kind": "hot_follow",
        "ready_gate": ready_gate or {},
        "artifact_facts": artifact_facts or {},
        "current_attempt": current_attempt or {},
        "operator_summary": operator_summary or {},
        "pipeline": [],
        "pipeline_legacy": {},
        "deliverables": [],
        "media": {},
        "source_video": {},
    }


def test_hot_follow_advisory_bundle_resolves_from_line_contract():
    line = LineRegistry.for_kind("hot_follow")

    bundle = skills_advisory.resolve_hot_follow_skills_bundle(line)

    assert bundle is not None
    assert bundle.bundle_id == "hot_follow_skills_v1"
    assert bundle.bundle_ref == "skills/hot_follow"
    assert bundle.hook_kind == "advisory_runtime"


def test_hot_follow_advisory_v0_recommends_recompose_for_stale_final():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-recompose", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": False,
                "publish_ready": False,
                "blocking": ["compose_not_done", "final_stale"],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "pending",
                "requires_recompose": True,
                "final_stale_reason": "final_stale_after_dub",
                "current_subtitle_source": "mm.srt",
            },
            operator_summary={"last_successful_output_available": True},
        ),
    )

    assert advisory == {
        "id": "hf_advisory_recompose_required",
        "kind": "operator_guidance",
        "level": "warning",
        "recommended_next_action": "recompose_final",
        "operator_hint": "recompose recommended",
        "explanation": "当前字幕或配音已更新，建议重新合成最终视频以生成最新版本。",
        "evidence": {
            "final_exists": True,
            "compose_status": "pending",
            "final_stale_reason": "final_stale_after_dub",
            "blocking": ["compose_not_done", "final_stale"],
        },
    }


def test_hot_follow_advisory_v0_recommends_subtitle_review_when_missing():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-subtitle", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "audio_ready": False,
                "compose_ready": False,
                "publish_ready": False,
                "blocking": ["compose_not_done", "subtitle_not_ready"],
            },
            artifact_facts={
                "final_exists": False,
                "audio_exists": False,
                "subtitle_exists": False,
            },
            current_attempt={
                "audio_ready": False,
                "compose_status": "never",
                "requires_recompose": False,
            },
        ),
    )

    assert advisory == {
        "id": "hf_advisory_review_subtitles",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "review_subtitles",
        "operator_hint": "subtitle review recommended",
        "explanation": "当前主字幕还未准备完成，建议先检查并保存 mm.srt 后再继续后续链路。",
        "evidence": {
            "subtitle_ready": False,
            "subtitle_ready_reason": "subtitle_missing",
            "subtitle_exists": False,
        },
    }


def test_hot_follow_advisory_v0_projects_compose_blocked_before_recompose():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-compose-blocked", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": False,
                "compose_blocked": True,
                "compose_blocked_reason": "bitrate_too_high",
                "publish_ready": False,
                "blocking": ["bitrate_too_high"],
            },
            artifact_facts={
                "final_exists": False,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "blocked",
                "compose_reason": "bitrate_too_high",
                "compose_blocked_terminal": True,
                "requires_recompose": True,
                "final_stale_reason": "final_stale_after_dub",
                "current_subtitle_source": "mm.srt",
            },
        ),
    )

    assert advisory == {
        "id": "hf_advisory_compose_blocked",
        "kind": "operator_guidance",
        "level": "warning",
        "recommended_next_action": "resolve_compose_input",
        "operator_hint": "compose input blocked",
        "explanation": "当前合成输入已被线路策略阻断：bitrate_too_high。请调整素材后再尝试合成。",
        "evidence": {
            "compose_blocked": True,
            "compose_blocked_reason": "bitrate_too_high",
            "compose_status": "blocked",
            "blocking": ["bitrate_too_high"],
        },
    }


def test_hot_follow_advisory_v0_projects_no_dub_terminal_not_review_subtitles():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-no-dub-terminal", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "audio_ready": False,
                "compose_ready": False,
                "no_dub_compose_allowed": True,
                "no_dub_reason": "bgm_only_no_tts",
                "publish_ready": False,
                "blocking": ["compose_not_done"],
            },
            artifact_facts={
                "final_exists": False,
                "audio_exists": False,
                "subtitle_exists": False,
            },
            current_attempt={
                "audio_ready": False,
                "compose_status": "pending",
                "requires_recompose": False,
                "no_dub_route_terminal": True,
                "subtitle_terminal_state": "no_dub_route_terminal",
            },
        ),
    )

    assert advisory == {
        "id": "hf_advisory_no_dub_route_terminal",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "compose_no_tts",
        "operator_hint": "no TTS compose route",
        "explanation": "当前素材已进入无 TTS 合成路径：bgm_only_no_tts。可继续合成保留原音或背景音版本。",
        "evidence": {
            "no_dub_route_terminal": True,
            "subtitle_terminal_state": "no_dub_route_terminal",
            "no_dub_compose_allowed": True,
            "no_dub_reason": "bgm_only_no_tts",
        },
    }


def test_hot_follow_live_muted_no_tts_route_recommends_compose_no_tts():
    artifact_facts = {
        "final_exists": False,
        "audio_exists": False,
        "subtitle_exists": False,
        "audio_lane_mode": "muted_no_tts",
        "tts_voiceover_exists": False,
        "audio_lane": {
            "mode": "muted_no_tts",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_key": None,
            "bgm_configured": False,
            "no_tts": True,
        },
        "compose_input": {
            "mode": "unknown",
            "blocked": False,
            "reason": None,
            "profile": {},
            "source": "none",
        },
        "selected_compose_route": {
            "name": "no_tts_compose_route",
            "required_artifacts": ["compose_input"],
            "optional_artifacts": ["target_subtitle", "scene_pack"],
            "irrelevant_artifacts": ["tts_voiceover", "bgm", "source_audio_preserved"],
            "allow_conditions": ["compose_input_ready", "no_tts_compose_selected"],
            "blocked_conditions": ["compose_input_blocked", "no_tts_not_selected"],
        },
    }
    state = compute_hot_follow_state(
        {"task_id": "hf-live-muted-no-tts", "kind": "hot_follow"},
        {
            "task_id": "hf-live-muted-no-tts",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "subtitle_artifact_exists": False,
            },
            "audio": {
                "status": "pending",
                "audio_ready": False,
                "audio_ready_reason": "dub_not_done",
                "dub_current": False,
                "no_dub": False,
            },
            "artifact_facts": artifact_facts,
        },
    )
    ready_gate = state["ready_gate"]
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state=state["audio"],
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_artifact_exists": False,
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
        },
        dub_status="running",
        compose_status="pending",
        composed_reason=ready_gate["compose_reason"],
        artifact_facts=artifact_facts,
    )

    assert artifact_facts["audio_lane"]["mode"] == "muted_no_tts"
    assert current_attempt["no_dub_route_terminal"] is True
    assert ready_gate["selected_compose_route"] == "no_tts_compose_route"
    assert ready_gate["compose_allowed"] is True
    assert ready_gate["no_tts_compose_allowed"] is True
    assert "subtitle_not_ready" not in ready_gate["blocking"]
    assert "voiceover_missing" not in ready_gate["blocking"]

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-live-muted-no-tts", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate=ready_gate,
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
        ),
    )

    assert advisory["recommended_next_action"] == "compose_no_tts"
    assert advisory["evidence"]["selected_compose_route"] == "no_tts_compose_route"


def test_helper_translate_failure_voice_led_does_not_recommend_no_tts_compose():
    artifact_facts = {
        "final_exists": False,
        "audio_exists": False,
        "subtitle_exists": False,
        "helper_translate_failed": True,
        "helper_translate_failed_voice_led": True,
        "helper_translate_error_reason": "helper_translate_provider_exhausted",
        "helper_translate_error_message": "翻译服务当前额度不足或请求过多，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。",
        "audio_lane": {
            "mode": "muted_no_tts",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_configured": False,
            "no_tts": True,
        },
        "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        "selected_compose_route": {"name": "tts_replace_route"},
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "target_subtitle_empty",
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_artifact_exists": False,
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
            "parse_source_text": "voice-led source transcript",
        },
        dub_status="skipped",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["subtitle_terminal_state"] == "helper_translate_failed_terminal"

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-helper-translate-failed", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": False,
                "subtitle_ready_reason": "target_subtitle_empty",
                "audio_ready": False,
                "audio_ready_reason": "target_subtitle_empty",
                "compose_allowed": False,
                "compose_ready": False,
                "no_tts_compose_allowed": False,
                "no_dub_compose_allowed": False,
                "selected_compose_route": "tts_replace_route",
                "blocking": ["subtitle_not_ready", "voiceover_missing"],
            },
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
        ),
    )

    assert advisory["id"] == "hf_advisory_helper_translate_failed"
    assert advisory["recommended_next_action"] == "retry_translate_or_edit_subtitle"
    assert advisory["recommended_next_action"] != "compose_no_tts"
    assert advisory["evidence"]["selected_compose_route"] == "tts_replace_route"


def test_helper_translate_failure_with_saved_target_subtitle_stays_helper_scoped():
    artifact_facts = {
        "final_exists": False,
        "audio_exists": False,
        "subtitle_exists": True,
        "helper_translate_failed": True,
        "helper_translate_failed_voice_led": True,
        "helper_translate_error_reason": "helper_translate_provider_exhausted",
        "helper_translate_error_message": "翻译服务当前额度不足或请求过多，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。",
        "audio_lane": {
            "mode": "muted_no_tts",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_configured": False,
            "no_tts": True,
        },
        "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        "selected_compose_route": {"name": "no_tts_compose_route"},
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_artifact_exists": True,
            "edited_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "srt_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "dub_input_text": "မင်္ဂလာပါ",
            "parse_source_text": "voice-led source transcript",
        },
        dub_status="skipped",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=False,
    )

    assert current_attempt["helper_translate_failed"] is False
    assert current_attempt["helper_translate_failed_voice_led"] is False
    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["subtitle_terminal_state"] is None

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-helper-failure-saved-subtitle", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "compose_allowed": False,
                "compose_ready": False,
                "no_tts_compose_allowed": False,
                "no_dub_compose_allowed": False,
                "selected_compose_route": "tts_replace_route",
                "blocking": ["voiceover_missing"],
            },
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
        ),
    )

    assert advisory["recommended_next_action"] == "refresh_dub"
    assert advisory["recommended_next_action"] != "compose_no_tts"
    assert advisory["id"] != "hf_advisory_helper_translate_failed"
    assert advisory["evidence"]["selected_compose_route"] == "tts_replace_route"


def test_first_tts_failure_stays_retriable_not_no_tts_terminal():
    artifact_facts = {
        "final_exists": False,
        "audio_exists": False,
        "subtitle_exists": True,
        "audio_lane": {
            "mode": "muted_no_tts",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_configured": False,
            "no_tts": True,
        },
        "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        "selected_compose_route": {"name": "no_tts_compose_route"},
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "TTS_FAILED:EMPTY_OR_INVALID_AUDIO",
            "dub_current": False,
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_artifact_exists": True,
            "edited_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "srt_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "dub_input_text": "မင်္ဂလာပါ",
        },
        dub_status="failed",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["tts_lane_expected"] is True
    assert current_attempt["retriable_dub_failure"] is True
    assert current_attempt["current_attempt_failure_class"] == "retriable_dub_failure"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["no_tts_compose_allowed"] is False
    assert current_attempt["compose_execute_allowed"] is False

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-first-tts-failure", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": False,
                "audio_ready_reason": "TTS_FAILED:EMPTY_OR_INVALID_AUDIO",
                "compose_allowed": False,
                "compose_ready": False,
                "publish_ready": False,
                "no_tts_compose_allowed": False,
                "no_dub_compose_allowed": False,
                "selected_compose_route": "tts_replace_route",
                "blocking": ["voiceover_missing"],
            },
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
        ),
    )

    assert advisory["id"] == "hf_advisory_retriable_dub_failure"
    assert advisory["recommended_next_action"] == "retry_or_inspect_dub"
    assert advisory["recommended_next_action"] != "compose_no_tts"
    assert advisory["evidence"]["selected_compose_route"] == "tts_replace_route"


def test_voice_led_retry_success_resolves_tts_replace_and_final_ready():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "voiceover_url": "/audio.mp3",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_artifact_exists": True,
            "edited_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "srt_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n",
            "dub_input_text": "မင်္ဂလာပါ",
        },
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        artifact_facts={
            "final_exists": True,
            "audio_exists": True,
            "subtitle_exists": True,
            "audio_lane": {
                "mode": "tts_voiceover_only",
                "tts_voiceover_exists": True,
                "source_audio_policy": "mute",
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": False,
            },
            "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        },
        no_dub=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["audio_ready"] is True
    assert current_attempt["compose_status"] == "done"
    assert current_attempt["retriable_dub_failure"] is False

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-retry-success", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": True,
                "publish_ready": True,
                "blocking": [],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt=current_attempt,
            operator_summary={"last_successful_output_available": True},
        ),
    )

    assert advisory["recommended_next_action"] == "continue_qa"
    assert advisory["evidence"]["selected_compose_route"] == "tts_replace_route"


def test_hot_follow_advisory_legal_no_tts_route_beats_refresh_dub():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-no-tts-priority", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "compose_allowed": True,
                "compose_ready": False,
                "publish_ready": False,
                "compose_blocked": False,
                "no_tts_compose_allowed": True,
                "no_dub_compose_allowed": True,
                "selected_compose_route": "no_tts_compose_route",
                "no_dub_reason": "compose_no_tts",
                "blocking": ["compose_not_done"],
            },
            artifact_facts={
                "final_exists": False,
                "audio_exists": False,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": False,
                "compose_allowed": True,
                "no_tts_compose_allowed": True,
                "no_dub_compose_allowed": True,
                "selected_compose_route": "no_tts_compose_route",
                "no_dub_route_terminal": True,
                "compose_status": "pending",
                "requires_recompose": False,
                "current_subtitle_source": "mm.srt",
            },
        ),
    )

    assert advisory["recommended_next_action"] == "compose_no_tts"


def test_hot_follow_advisory_prefers_compose_input_fix_over_recompose():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-compose-input-fix", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": False,
                "publish_ready": False,
                "compose_allowed": True,
                "compose_route_allowed": True,
                "compose_input_ready": False,
                "compose_execute_allowed": False,
                "compose_input_mode": "derive_failed",
                "compose_input_reason": "derive_not_encoder_safe",
                "compose_input_derive_failed_terminal": True,
                "compose_reason": "compose_input_derive_failed",
                "blocking": ["compose_input_derive_failed"],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
                "compose_input_mode": "derive_failed",
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "failed",
                "compose_route_allowed": True,
                "compose_input_ready": False,
                "compose_execute_allowed": False,
                "compose_input_derive_failed_terminal": True,
                "requires_recompose": True,
                "current_subtitle_source": "mm.srt",
            },
        ),
    )

    assert advisory["recommended_next_action"] == "retry_after_compose_input_fix"
    assert advisory["id"] == "hf_advisory_compose_input_unready"


def test_hot_follow_advisory_v0_recommends_continue_qa_when_final_is_ready():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-final-ready", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={
                "subtitle_ready": True,
                "audio_ready": True,
                "compose_ready": True,
                "publish_ready": True,
                "blocking": [],
            },
            artifact_facts={
                "final_exists": True,
                "audio_exists": True,
                "subtitle_exists": True,
            },
            current_attempt={
                "audio_ready": True,
                "compose_status": "done",
                "requires_recompose": False,
                "current_subtitle_source": "mm.srt",
            },
            operator_summary={"last_successful_output_available": True},
        ),
    )

    assert advisory == {
        "id": "hf_advisory_final_ready",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "continue_qa",
        "operator_hint": "no further action currently required",
        "explanation": "当前成片已可用，可继续做字幕、配音或成片 QA 复核。",
        "evidence": {
            "final_exists": True,
            "compose_ready": True,
            "publish_ready": True,
            "last_successful_output_available": True,
        },
    }


def test_hot_follow_advisory_v0_noops_for_non_hot_follow_kind():
    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "skills-noop-non-hf", "kind": "avatar"},
        _advisory_payload(
            ready_gate={"subtitle_ready": True},
            artifact_facts={"final_exists": True},
            current_attempt={"audio_ready": True},
        ),
    )

    assert advisory is None


def test_hot_follow_advisory_v0_safe_fallback_on_hook_failure(monkeypatch):
    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", lambda _input: (_ for _ in ()).throw(RuntimeError("boom")))

    advisory = skills_advisory.maybe_build_hot_follow_advisory(
        {"task_id": "hf-skills-v0-safe-fallback", "kind": "hot_follow"},
        _advisory_payload(
            ready_gate={"subtitle_ready": True},
            artifact_facts={"final_exists": True},
            current_attempt={"audio_ready": True},
        ),
    )

    assert advisory is None


def test_hot_follow_advisory_noop_preserves_workbench_payload(monkeypatch):
    task_id = "hf-skills-noop-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "target_lang": "mm",
            "title": "skills noop",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": False, "fresh": False, "url": None},
            "historical_final": {"exists": False, "url": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": False,
            "voice_exists": False,
        },
    )
    _patch_workbench_dependencies(monkeypatch)
    monkeypatch.setattr(skills_advisory, "maybe_resolve_contract_advisory", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", lambda _input: None)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert "advisory" not in data
    artifact_facts = data.get("artifact_facts") or {}
    assert artifact_facts == {
        "final_exists": False,
        "final_url": None,
        "final_updated_at": None,
        "final_asset_version": None,
        "audio_exists": False,
        "audio_url": None,
        "subtitle_exists": False,
        "subtitle_url": None,
        "helper_translate_failed": False,
        "helper_translate_failed_voice_led": False,
        "helper_translate_error_reason": None,
        "helper_translate_error_message": None,
        "pack_exists": False,
        "pack_url": None,
        "compose_input": {
            "mode": "unknown",
            "blocked": False,
            "ready": False,
            "derive_failed": False,
            "reason": None,
            "failure_code": None,
            "profile": {},
            "safe_key": None,
            "source": "none",
        },
        "compose_input_mode": "unknown",
        "compose_input_blocked": False,
        "compose_input_ready": False,
        "compose_input_derive_failed": False,
        "compose_input_reason": None,
        "compose_input_failure_code": None,
        "compose_input_safe_key": None,
        "audio_lane": {
            "mode": "muted_no_tts",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_key": None,
            "bgm_configured": False,
            "no_tts": True,
        },
        "audio_lane_mode": "muted_no_tts",
        "tts_voiceover_exists": False,
        "selected_compose_route": {
            "name": "no_tts_compose_route",
            "required_artifacts": ["compose_input"],
            "optional_artifacts": ["target_subtitle", "scene_pack"],
            "irrelevant_artifacts": ["tts_voiceover", "bgm", "source_audio_preserved"],
            "allow_conditions": ["compose_input_ready", "no_tts_compose_selected"],
            "blocked_conditions": ["compose_input_blocked", "no_tts_not_selected"],
        },
    }


def test_hot_follow_advisory_result_attaches_to_workbench_payload(monkeypatch):
    task_id = "hf-skills-advisory-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "target_lang": "mm",
            "title": "skills advisory",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": False, "fresh": False, "url": None},
            "historical_final": {"exists": False, "url": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": False,
            "voice_exists": False,
        },
    )
    _patch_workbench_dependencies(monkeypatch)
    monkeypatch.setattr(skills_advisory, "maybe_resolve_contract_advisory", lambda *_args, **_kwargs: None)

    captured = {}

    def _fake_advisory(advisory_input):
        captured.update(advisory_input)
        return {
            "id": "hf_advisory_v0",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "noop",
            "operator_hint": "safe",
            "explanation": "read only",
            "evidence": {"source": "test"},
        }

    monkeypatch.setattr(skills_advisory, "_HOT_FOLLOW_ADVISORY_HOOK", _fake_advisory)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert captured["task"]["task_id"] == task_id
    assert captured["line"]["line_id"] == "hot_follow_line"
    assert captured["line"]["skills_bundle_ref"] == "skills/hot_follow"
    assert "ready_gate" in captured
    assert "artifact_facts" in captured
    assert "current_attempt" in captured
    assert "operator_summary" in captured
    assert data.get("advisory") == {
        "id": "hf_advisory_v0",
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "noop",
        "operator_hint": "safe",
        "explanation": "read only",
        "evidence": {
            "source": "test",
            "selected_compose_route": "no_tts_compose_route",
        },
    }
