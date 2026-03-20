import asyncio
from pathlib import Path
import sys
import types
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import tasks as tasks_router
from gateway.app.routers import hot_follow_api as hf_router


def _settings():
    return SimpleNamespace(
        edge_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
        },
        azure_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
        },
        dub_provider="azure-speech",
        azure_speech_key="test-key",
        azure_speech_region="eastasia",
    )


def test_fresh_matching_male_artifact_is_current_even_if_tokens_are_stale(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))

    task = {
        "task_id": "hf-male",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/hf-male/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-ThihaNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
            "tts_request_token": "newer",
            "tts_completed_token": "older",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["requested_voice"] == "mm_male_1"
    assert state["resolved_voice"] == "my-MM-ThihaNeural"
    assert state["actual_provider"] == "azure-speech"
    assert state["audio_ready"] is True
    assert state["audio_ready_reason"] == "ready"
    assert state["dub_current"] is True
    assert state["dub_current_reason"] == "ready"
    assert str(state["voiceover_url"]).endswith("/v1/tasks/hf-male/audio_mm")
    assert state["deliverable_audio_done"] is True


def test_stale_female_artifact_is_not_current_for_male_request(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))

    task = {
        "task_id": "hf-stale",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "failed",
        "mm_audio_key": "deliver/tasks/hf-stale/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
            "tts_request_token": "newer",
            "tts_completed_token": "older",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "dub_not_done"
    assert state["dub_current"] is False
    assert state["voiceover_url"] is None
    assert state["deliverable_audio_done"] is True


def test_previous_final_can_coexist_with_failed_current_redub(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(tasks_router, "object_exists", lambda key: str(key).endswith(("audio_mm.mp3", "final.mp4")))
    monkeypatch.setattr(
        tasks_router,
        "object_head",
        lambda key: {
            "ContentLength": "4096" if str(key).endswith("audio_mm.mp3") else "8192",
            "Content-Type": "audio/mpeg" if str(key).endswith("audio_mm.mp3") else "video/mp4",
        },
    )
    monkeypatch.setattr(
        tasks_router,
        "media_meta_from_head",
        lambda meta: (int(meta.get("ContentLength") or 0), str(meta.get("Content-Type") or "")),
    )
    # Also patch on hf_router since _collect_hot_follow_workbench_ui lives there
    monkeypatch.setattr(hf_router, "get_settings", _settings)
    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key).endswith(("audio_mm.mp3", "final.mp4")))
    monkeypatch.setattr(
        hf_router,
        "object_head",
        lambda key: {
            "ContentLength": "4096" if str(key).endswith("audio_mm.mp3") else "8192",
            "Content-Type": "audio/mpeg" if str(key).endswith("audio_mm.mp3") else "video/mp4",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "media_meta_from_head",
        lambda meta: (int(meta.get("ContentLength") or 0), str(meta.get("Content-Type") or "")),
    )

    task = {
        "task_id": "hf-rerun",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "failed",
        "compose_status": "done",
        "final_video_key": "deliver/tasks/hf-rerun/final.mp4",
        "mm_audio_key": "deliver/tasks/hf-rerun/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
        },
    }

    payload = hf_router._collect_hot_follow_workbench_ui(task, _settings())
    assert payload["final_exists"] is True
    assert payload["audio_ready"] is False
    assert payload["dub_current"] is False


def test_rerun_presentation_reports_last_final_and_current_failure():
    task = {
        "task_id": "hf-rerun-presentation",
        "updated_at": "2026-03-14T10:00:00+00:00",
    }
    voice_state = {
        "audio_ready": False,
        "audio_ready_reason": "dub_not_done",
        "dub_current": False,
        "dub_current_reason": "dub_not_done",
        "requested_voice": "mm_male_1",
        "resolved_voice": "my-MM-ThihaNeural",
        "actual_provider": "azure-speech",
    }
    final_info = {
        "exists": True,
        "url": "/v1/tasks/hf-rerun-presentation/final",
        "asset_version": "etag-123",
        "updated_at": "2026-03-14T09:55:00+00:00",
    }

    presentation = hf_router._hf_rerun_presentation_state(task, voice_state, final_info, "failed")

    assert presentation["last_successful_output"]["final_exists"] is True
    assert presentation["last_successful_output"]["final_url"] == "/v1/tasks/hf-rerun-presentation/final"
    assert presentation["current_attempt"]["dub_status"] == "failed"
    assert presentation["current_attempt"]["audio_ready"] is False
    assert presentation["current_attempt"]["dub_current"] is False
    assert presentation["current_attempt"]["requested_voice"] == "mm_male_1"


def test_rerun_presentation_reports_current_success_without_regressing_baseline():
    task = {
        "task_id": "hf-success-presentation",
        "updated_at": "2026-03-14T10:00:00+00:00",
    }
    voice_state = {
        "audio_ready": True,
        "audio_ready_reason": "ready",
        "dub_current": True,
        "dub_current_reason": "ready",
        "requested_voice": "mm_female_1",
        "resolved_voice": "my-MM-NilarNeural",
        "actual_provider": "azure-speech",
    }
    final_info = {
        "exists": True,
        "url": "/v1/tasks/hf-success-presentation/final",
        "asset_version": "etag-456",
        "updated_at": "2026-03-14T09:58:00+00:00",
    }

    presentation = hf_router._hf_rerun_presentation_state(task, voice_state, final_info, "done")

    assert presentation["last_successful_output"]["final_exists"] is True
    assert presentation["current_attempt"]["dub_status"] == "done"
    assert presentation["current_attempt"]["audio_ready"] is True
    assert presentation["current_attempt"]["dub_current"] is True
    assert presentation["current_attempt"]["resolved_voice"] == "my-MM-NilarNeural"


def test_artifact_facts_and_operator_summary_keep_previous_final_visible():
    artifact_facts = hf_router._hf_artifact_facts(
        "hf-rerun-presentation",
        {},
        final_info={
            "exists": True,
            "url": "/v1/tasks/hf-rerun-presentation/final",
            "asset_version": "etag-123",
            "updated_at": "2026-03-14T09:55:00+00:00",
        },
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack={"download_url": "/v1/tasks/hf-rerun-presentation/pack"},
    )
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "dub_current_reason": "dub_not_done",
            "requested_voice": "mm_male_1",
            "resolved_voice": "my-MM-ThihaNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={"actual_burn_subtitle_source": "mm.srt"},
        dub_status="failed",
        compose_status="pending",
        composed_reason="audio_not_ready",
    )
    operator_summary = hf_router._hf_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
    )

    assert artifact_facts["final_exists"] is True
    assert artifact_facts["final_url"] == "/v1/tasks/hf-rerun-presentation/final"
    assert artifact_facts["audio_exists"] is False
    assert artifact_facts["subtitle_exists"] is True
    assert artifact_facts["pack_exists"] is True
    assert current_attempt["dub_status"] == "failed"
    assert current_attempt["compose_status"] == "pending"
    assert current_attempt["current_subtitle_source"] == "mm.srt"
    assert operator_summary["last_successful_output_available"] is True
    assert operator_summary["current_attempt_failed"] is True
    assert operator_summary["show_previous_final_as_primary"] is True


def test_artifact_facts_and_operator_summary_preserve_voice_led_success_baseline():
    artifact_facts = hf_router._hf_artifact_facts(
        "hf-success-presentation",
        {},
        final_info={
            "exists": True,
            "url": "/v1/tasks/hf-success-presentation/final",
            "asset_version": "etag-456",
            "updated_at": "2026-03-14T09:58:00+00:00",
        },
        persisted_audio={"exists": True, "voiceover_url": "/v1/tasks/hf-success-presentation/audio_mm"},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack=None,
    )
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={"actual_burn_subtitle_source": "mm.srt"},
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
    )
    operator_summary = hf_router._hf_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
    )

    assert artifact_facts["audio_exists"] is True
    assert artifact_facts["audio_url"] == "/v1/tasks/hf-success-presentation/audio_mm"
    assert current_attempt["requires_recompose"] is False
    assert current_attempt["compose_reason"] == "ready"
    assert operator_summary["last_successful_output_available"] is True
    assert operator_summary["current_attempt_failed"] is False
    assert operator_summary["show_previous_final_as_primary"] is False


def test_source_audio_lane_summary_distinguishes_voice_led_and_silent_candidates():
    voice_led = hf_router._hf_source_audio_lane_summary(
        {"title": "standard talking head"},
        {"content_mode": "voice_led", "speech_detected": True},
    )
    silent = hf_router._hf_source_audio_lane_summary(
        {"title": "ASMR product showcase"},
        {"content_mode": "silent_candidate", "speech_detected": False},
    )

    assert voice_led["source_audio_lane"] == "speech_primary"
    assert voice_led["speech_presence"] == "high"
    assert silent["source_audio_lane"] == "silent_candidate"
    assert silent["audio_mix_mode"] == "silent_or_fx"


def test_screen_text_candidate_summary_prefers_normalized_text_for_subtitle_led():
    candidate = hf_router._hf_screen_text_candidate_summary(
        {
            "normalized_source_text": "候选字幕",
            "raw_source_text": "原始文本",
        },
        {
            "onscreen_text_detected": True,
            "onscreen_text_density": "high",
            "content_mode": "subtitle_led",
        },
    )

    assert candidate["screen_text_candidate"] == "候选字幕"
    assert candidate["screen_text_candidate_source"] == "normalized_source"
    assert candidate["screen_text_candidate_confidence"] == "high"
    assert candidate["screen_text_candidate_mode"] == "subtitle_led"


def test_operator_summary_prefers_recompose_when_current_dub_is_ready_but_final_is_stale():
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={"actual_burn_subtitle_source": "mm.srt"},
        dub_status="done",
        compose_status="done",
        composed_reason="final_stale_after_dub",
    )

    operator_summary = hf_router._hf_operator_summary(
        artifact_facts={"final_exists": True},
        current_attempt=current_attempt,
        no_dub=False,
    )

    assert current_attempt["requires_recompose"] is True
    assert operator_summary["recommended_next_action"] == "当前配音已更新，建议重新合成最终视频以生成最新版本。"


def test_collect_hot_follow_workbench_ui_does_not_keep_no_dub_when_audio_is_current(monkeypatch):
    monkeypatch.setattr(hf_router, "get_settings", _settings)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, _task: "")

    task = {
        "task_id": "hf-a9-ui",
        "kind": "hot_follow",
        "target_lang": "mm",
        "title": "silent candidate but current dub exists",
        "dub_status": "done",
        "voice_id": "mm_female_1",
        "dub_provider": "azure-speech",
        "mm_audio_key": "deliver/tasks/hf-a9-ui/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "mm_srt_path": "deliver/tasks/hf-a9-ui/mm.srt",
        "config": {
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
        },
        "pipeline_config": {"no_dub": "true"},
    }

    payload = hf_router._collect_hot_follow_workbench_ui(task, _settings())

    assert payload["audio_ready"] is True
    assert payload["dub_current"] is True
    assert payload["subtitle_artifact_exists"] is True
    assert payload["actual_burn_subtitle_source"] == "mm.srt"
    assert payload["no_dub"] is False
    assert payload["no_dub_reason"] is None


def test_sync_saved_target_subtitle_artifact_writes_canonical_mm_srt(monkeypatch, tmp_path):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (0, None))

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    uploaded = []

    def _fake_upload(task, local_path, artifact_name, task_id=None, **_kwargs):
        uploaded.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)

    task = {"task_id": "hf-sync", "kind": "hot_follow"}
    key = hf_router._hf_sync_saved_target_subtitle_artifact(
        "hf-sync",
        task,
        "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n",
    )

    assert key == "deliver/tasks/hf-sync/mm.srt"
    assert task["mm_srt_path"] == "deliver/tasks/hf-sync/mm.srt"
    assert uploaded[0][0] == "mm.srt"
    assert "မင်္ဂလာပါ" in uploaded[0][1]
    assert uploaded[1][0] == "mm.txt"
    assert "မင်္ဂလာပါ" in uploaded[1][1]


def test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt(monkeypatch, tmp_path):
    class _Repo:
        def __init__(self):
            self.task = {"task_id": "hf-save", "kind": "hot_follow", "subtitles_status": "pending"}

        def get(self, task_id):
            assert task_id == "hf-save"
            return dict(self.task)

    repo = _Repo()

    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (0, None))

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda task_id: tmp_path / task_id / "override.srt")
    (tmp_path / "hf-save").mkdir(parents=True, exist_ok=True)
    (tmp_path / "hf-save" / "override.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nexisting\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, task: Path(tmp_path / "hf-save" / "override.srt").read_text(encoding="utf-8"))
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_policy_upsert", lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates))
    monkeypatch.setattr(hf_router, "upload_task_artifact", lambda _task, _local_path, artifact_name, task_id=None, **_kwargs: f"deliver/tasks/{task_id}/{artifact_name}")

    payload = hf_router.HotFollowSubtitlesRequest(
        srt_text="1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n"
    )
    result = hf_router.patch_hot_follow_subtitles("hf-save", payload, repo=repo)

    assert repo.task["mm_srt_path"] == "deliver/tasks/hf-save/mm.srt"
    assert result["subtitles"]["srt_text"].strip().endswith("မင်္ဂလာပါ")


def test_hot_follow_rerun_forces_redub_even_when_voice_is_unchanged(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_subtitle_lane_state", lambda *_args, **_kwargs: {"dub_input_text": "မင်္ဂလာပါ"})
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_dual_channel_state", lambda *_args, **_kwargs: {"content_mode": "voice_led"})

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.base_dir = base
            self.mm_audio_primary_path = base / "audio_primary.wav"
            self.mm_audio_mp3_path = base / "audio.mp3"
            self.mm_audio_legacy_path = base / "audio_legacy.wav"
            self.mm_audio_path = base / "audio.wav"

        def mm_audio_exists(self):
            return False

    monkeypatch.setattr(tasks_router, "Workspace", _Workspace)

    def _fake_upsert(repo, task_id, updates, **_kwargs):
        assert task_id == repo.task["task_id"]
        repo.task.update(updates)
        return repo.task

    monkeypatch.setattr(tasks_router, "_policy_upsert", _fake_upsert)

    captured = {}

    async def _fake_run_dub_step_ssot(task_adapter):
        captured["force_dub"] = bool(getattr(task_adapter, "force_dub", False))
        raise RuntimeError("stop_after_force_capture")

    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", _fake_run_dub_step_ssot)

    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-force",
                "kind": "hot_follow",
                "target_lang": "mm",
                "voice_id": "mm_female_1",
                "dub_provider": "azure-speech",
                "mm_audio_key": "deliver/tasks/hf-force/audio_mm.mp3",
                "config": {
                    "tts_requested_voice": "mm_female_1",
                    "tts_resolved_voice": "my-MM-NilarNeural",
                    "tts_provider": "azure-speech",
                },
            }
            self.session = SimpleNamespace(expire_all=lambda: None)

        def get(self, _task_id):
            return self.task

    repo = _Repo()
    payload = tasks_router.DubProviderRequest(
        provider="azure-speech",
        voice_id="mm_female_1",
        mm_text="မင်္ဂလာပါ",
        force=True,
    )

    with pytest.raises(tasks_router.HTTPException) as exc:
        asyncio.run(tasks_router._run_dub_job("hf-force", payload, repo))

    assert exc.value.status_code == 500
    assert captured["force_dub"] is True


def test_hot_follow_azure_auth_failure_keeps_audio_missing_and_surfaces_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_subtitle_lane_state", lambda *_args, **_kwargs: {"dub_input_text": "မင်္ဂလာပါ"})
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_dual_channel_state", lambda *_args, **_kwargs: {"content_mode": "voice_led"})
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: None)
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (0, None))

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.base_dir = base
            self.mm_audio_primary_path = base / "audio_primary.wav"
            self.mm_audio_mp3_path = base / "audio.mp3"
            self.mm_audio_legacy_path = base / "audio_legacy.wav"
            self.mm_audio_path = base / "audio.wav"

        def mm_audio_exists(self):
            return False

    monkeypatch.setattr(tasks_router, "Workspace", _Workspace)

    def _fake_upsert(repo, task_id, updates, **_kwargs):
        assert task_id == repo.task["task_id"]
        repo.task.update(updates)
        return repo.task

    monkeypatch.setattr(tasks_router, "_policy_upsert", _fake_upsert)

    async def _fake_run_dub_step_ssot(_task_adapter):
        raise RuntimeError(
            "TTS_AZURE_HTTP_401: Azure Speech returned 401 Unauthorized; "
            "check AZURE_SPEECH_KEY and AZURE_SPEECH_REGION for an active matching key-region pair "
            "and restart the app if env was changed after startup "
            "(region=eastasia endpoint=https://eastasia.tts.speech.microsoft.com/cognitiveservices/v1)"
        )

    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", _fake_run_dub_step_ssot)

    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-auth-fail",
                "kind": "hot_follow",
                "target_lang": "mm",
                "subtitles_status": "ready",
                "voice_id": "mm_female_1",
                "dub_provider": "azure-speech",
                "config": {
                    "tts_requested_voice": "mm_female_1",
                    "tts_resolved_voice": "my-MM-NilarNeural",
                    "tts_provider": "azure-speech",
                },
            }
            self.session = SimpleNamespace(expire_all=lambda: None)

        def get(self, _task_id):
            return dict(self.task)

    repo = _Repo()
    payload = tasks_router.DubProviderRequest(
        provider="azure-speech",
        voice_id="mm_female_1",
        mm_text="မင်္ဂလာပါ",
        force=True,
    )

    with pytest.raises(tasks_router.HTTPException) as exc:
        asyncio.run(tasks_router._run_dub_job("hf-auth-fail", payload, repo))

    assert exc.value.status_code == 500
    assert "TTS_AZURE_HTTP_401" in repo.task["dub_error"]
    assert "AZURE_SPEECH_KEY" in repo.task["dub_error"]
    assert "restart the app if env was changed after startup" in repo.task["dub_error"]

    state = tasks_router._collect_voice_execution_state(repo.task, _settings())

    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "audio_missing"
    assert state["resolved_voice"] == "my-MM-NilarNeural"
    assert state["actual_provider"] == "azure-speech"
