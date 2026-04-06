from pathlib import Path
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient
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

from gateway.app.deps import get_task_repository
from gateway.app.routers import tasks as tasks_router
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services.compose_service import ComposeResult
from gateway.app.utils.pipeline_config import parse_pipeline_config


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


def _patch_workbench_storage_dependencies(monkeypatch):
    monkeypatch.setattr(hf_router, "_scene_pack_info", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(hf_router, "_deliverable_url", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(hf_router, "_hf_persisted_audio_state", lambda *_args, **_kwargs: {"exists": False, "voiceover_url": None})


def test_hot_follow_workbench_ready_gate_backfills_compose_when_current_final_is_fresh(monkeypatch):
    task_id = "hf-workbench-ready-gate-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "pending",
            "voice_id": "mm_female_1",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 123456},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": True,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(hf_router, "_compute_composed_state", _fake_composed)
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("ready_gate", {}).get("compose_ready") is True
    assert data.get("ready_gate", {}).get("publish_ready") is True
    assert (data.get("line") or {}).get("line_id") == "hot_follow_line"
    assert ((data.get("line") or {}).get("hook_refs") or {}).get("status_policy_ref") == "gateway/app/services/status_policy/hot_follow_state.py"
    assert data.get("composed_ready") is True
    assert data.get("composed_reason") == "ready"
    assert str(data.get("final_video_url") or "").endswith(f"/v1/tasks/{task_id}/final")

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"


def test_hot_follow_workbench_compose_view_is_done_when_final_ready(monkeypatch):
    task_id = "hf-workbench-compose-done-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "pending",
            "voice_id": "mm_female_1",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "deliverables": [
                {"kind": "final", "status": "pending", "state": "pending", "url": None},
            ],
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 123456},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": True,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(hf_router, "_compute_composed_state", _fake_composed)
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("composed_ready") is True
    assert data.get("composed_reason") == "ready"

    compose_step = next(
        (x for x in (data.get("pipeline") or []) if str(x.get("key") or "").lower() == "compose"),
        {},
    )
    assert compose_step.get("status") == "done"
    assert ((data.get("compose") or {}).get("last") or {}).get("status") == "done"
    assert ((data.get("pipeline_legacy") or {}).get("compose") or {}).get("status") == "done"

    final_row = next(
        (x for x in (data.get("deliverables") or []) if str(x.get("kind") or "").lower() == "final"),
        {},
    )
    assert final_row.get("status") == "done"
    assert final_row.get("historical") is False


def test_hot_follow_workbench_vi_currentness_blocks_false_done_states(monkeypatch):
    task_id = "hf-workbench-vi-currentness-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "vi",
            "content_lang": "vi",
            "compose_status": "done",
            "compose_last_status": "done",
            "dub_status": "done",
            "voice_id": "vi_female_1",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_vi.mp3",
            "mm_audio_voice_id": "vi-VN-HoaiMyNeural",
            "mm_audio_provider": "azure-speech",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "mm_srt_path": f"deliver/tasks/{task_id}/vi.srt",
            "pipeline_config": {"translation_incomplete": "true"},
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 123456},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": True,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda task, _settings: {
            "audio_ready": bool(task.get("target_subtitle_current")),
            "audio_ready_reason": (
                "ready"
                if task.get("target_subtitle_current")
                else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
            ),
            "dub_current": bool(task.get("target_subtitle_current")),
            "dub_current_reason": (
                "ready"
                if task.get("target_subtitle_current")
                else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
            ),
            "resolved_voice": "vi-VN-HoaiMyNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "vi_female_1",
            "voiceover_url": "/v1/tasks/hf-workbench-vi-currentness-01/audio_mm",
            "deliverable_audio_done": True,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_hf_persisted_audio_state",
        lambda *_args, **_kwargs: {"exists": True, "voiceover_url": f"/v1/tasks/{task_id}/audio_mm"},
    )
    monkeypatch.setattr(hf_router, "_scene_pack_info", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(hf_router, "_deliverable_url", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(hf_router, "task_base_dir", lambda current_task_id: Path("/tmp") / current_task_id)
    monkeypatch.setattr(
        hf_router,
        "object_exists",
        lambda key: str(key).endswith(("origin.srt", "vi.srt", "final.mp4")),
    )
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(
        hf_router,
        "get_object_bytes",
        lambda _key: "1\n00:00:00,000 --> 00:00:02,000\n原始文案\n".encode("utf-8"),
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["subtitles"]["target_subtitle_current"] is False
    assert data["subtitles"]["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert data["ready_gate"]["subtitle_ready"] is False
    assert data["ready_gate"]["compose_ready"] is False

    dub_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "dub"), {})
    compose_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "compose"), {})
    assert dub_step.get("status") == "pending"
    assert compose_step.get("status") == "pending"


def test_hot_follow_workbench_stale_final_is_historical_only_after_redub(monkeypatch):
    task_id = "hf-workbench-stale-final-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "done",
            "compose_last_status": "done",
            "voice_id": "mm_female_1",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "deliverables": [
                {"kind": "final", "status": "done", "state": "done", "url": f"/v1/tasks/{task_id}/final"},
            ],
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_stale_after_dub",
            "final": {"exists": False, "fresh": False, "url": None, "size_bytes": 123456, "stale_reason": "final_stale_after_dub"},
            "historical_final": {"exists": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 123456},
            "final_fresh": False,
            "final_stale_reason": "final_stale_after_dub",
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("composed_ready") is False
    assert data.get("composed_reason") == "final_stale_after_dub"
    assert (data.get("final") or {}).get("exists") is False
    assert ((data.get("historical_final") or {}).get("exists")) is True
    assert ((data.get("artifact_facts") or {}).get("final_exists")) is True
    assert ((data.get("current_attempt") or {}).get("requires_recompose")) is True
    assert ((data.get("ready_gate") or {}).get("compose_ready")) is False
    assert ((data.get("ready_gate") or {}).get("publish_ready")) is False

    final_row = next(
        (x for x in (data.get("deliverables") or []) if str(x.get("kind") or "").lower() == "final"),
        {},
    )
    assert final_row.get("status") == "pending"
    assert final_row.get("historical") is True


def test_hot_follow_workbench_mm_stale_dub_downgrades_audio_step(monkeypatch):
    task_id = "hf-workbench-mm-stale-dub-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "mm",
            "content_lang": "mm",
            "compose_status": "pending",
            "compose_last_status": "pending",
            "dub_status": "done",
            "voice_id": "mm_male_1",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "mm_audio_voice_id": "my-MM-ThihaNeural",
            "mm_audio_provider": "azure-speech",
            "mm_srt_path": f"deliver/tasks/{task_id}/mm.srt",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "audio_not_ready",
            "final": {"exists": False, "fresh": False, "url": None, "size_bytes": None},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_stale_after_subtitles",
            "dub_current": False,
            "dub_current_reason": "dub_stale_after_subtitles",
            "resolved_voice": "my-MM-ThihaNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_male_1",
            "voiceover_url": None,
            "deliverable_audio_done": True,
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    dub_step = next(
        (x for x in (data.get("pipeline") or []) if str(x.get("key") or "").lower() == "dub"),
        {},
    )
    assert dub_step.get("status") != "done"
    assert data.get("audio", {}).get("audio_ready") is False
    assert data.get("audio", {}).get("audio_ready_reason") == "dub_stale_after_subtitles"


def test_patch_hot_follow_audio_config_persists_speed_and_backfills_old_dub_speed_snapshot(monkeypatch):
    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-audio-speed-config",
                "kind": "hot_follow",
                "target_lang": "mm",
                "dub_provider": "azure-speech",
                "voice_id": "mm_female_1",
                "mm_audio_key": "deliver/tasks/hf-audio-speed-config/audio_mm.mp3",
                "pipeline_config": {"audio_fit_max_speed": "1.25"},
                "config": {
                    "tts_requested_voice": "mm_female_1",
                    "tts_resolved_voice": "my-MM-NilarNeural",
                    "tts_provider": "azure-speech",
                },
            }

        def get(self, task_id):
            assert task_id == "hf-audio-speed-config"
            return dict(self.task)

    repo = _Repo()
    monkeypatch.setattr(
        hf_router,
        "_policy_upsert",
        lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates),
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda task, _settings: {
            "voiceover_url": None,
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "expected_provider": "azure-speech",
        },
    )

    result = hf_router.patch_hot_follow_audio_config(
        "hf-audio-speed-config",
        hf_router.HotFollowAudioConfigRequest(audio_fit_max_speed=1.45),
        repo=repo,
    )

    assert parse_pipeline_config(repo.task["pipeline_config"])["audio_fit_max_speed"] == "1.45"
    assert result["audio_config"]["audio_fit_max_speed"] == 1.45
    assert repo.task["dub_source_audio_fit_max_speed"] == "1.25"


def test_hot_follow_workbench_hub_echoes_current_speed_and_stale_speed_reason(monkeypatch):
    task_id = "hf-workbench-speed-stale-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "mm",
            "content_lang": "mm",
            "compose_status": "done",
            "compose_last_status": "done",
            "dub_status": "done",
            "voice_id": "mm_female_1",
            "pipeline_config": {"audio_fit_max_speed": "1.45"},
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "mm_audio_voice_id": "my-MM-NilarNeural",
            "mm_audio_provider": "azure-speech",
            "mm_srt_path": f"deliver/tasks/{task_id}/mm.srt",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "audio_not_ready",
            "final": {"exists": False, "fresh": False, "url": None, "size_bytes": None},
            "historical_final": {"exists": False, "url": None, "size_bytes": None},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda task, _settings: {
            "audio_ready": False,
            "audio_ready_reason": "dub_stale_after_speed_change",
            "dub_current": False,
            "dub_current_reason": "dub_stale_after_speed_change",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
            "voiceover_url": None,
            "deliverable_audio_done": True,
            "current_audio_fit_max_speed": "1.45",
            "dub_source_audio_fit_max_speed": "1.25",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("audio", {}).get("audio_fit_max_speed") == 1.45
    assert data.get("audio", {}).get("audio_ready_reason") == "dub_stale_after_speed_change"
    assert data.get("audio", {}).get("current_audio_fit_max_speed") == "1.45"
    assert data.get("audio", {}).get("dub_source_audio_fit_max_speed") == "1.25"
    assert data.get("ready_gate", {}).get("compose_ready") is False


def test_hot_follow_workbench_parse_uses_raw_artifacts_over_failed_legacy_status(monkeypatch):
    task_id = "hf-workbench-parse-facts-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "parse_status": "failed",
            "raw_path": f"deliver/tasks/{task_id}/raw/raw.mp4",
            "deliverables": [
                {"kind": "raw_video", "status": "done", "state": "done", "url": f"/v1/tasks/{task_id}/raw"},
            ],
        },
    )

    monkeypatch.setattr(hf_router, "_compute_composed_state", lambda *_args, **_kwargs: {"composed_ready": False, "composed_reason": "not_ready", "final": {"exists": False}, "compose_error_reason": None, "compose_error_message": None})
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key).endswith("raw.mp4"))
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    parse_step = next(
        (x for x in (data.get("pipeline") or []) if str(x.get("key") or "").lower() == "parse"),
        {},
    )
    assert parse_step.get("status") == "done"
    assert parse_step.get("message") == "raw=ready"
    assert ((data.get("pipeline_legacy") or {}).get("parse") or {}).get("status") == "done"


def test_hot_follow_workbench_subtitles_keep_srt_as_primary_editable_object(monkeypatch):
    task_id = "hf-workbench-subtitles-srt-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "mm_srt_path": f"deliver/tasks/{task_id}/subs/mm.srt",
        },
    )
    mm_srt = "1\n00:00:00,000 --> 00:00:02,000\n缅文字幕\n"
    origin_srt = "1\n00:00:00,000 --> 00:00:02,000\n原始字幕\n"

    monkeypatch.setattr(hf_router, "_compute_composed_state", lambda *_args, **_kwargs: {"composed_ready": False, "composed_reason": "not_ready", "final": {"exists": False}, "compose_error_reason": None, "compose_error_message": None})
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: mm_srt)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: origin_srt)
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: origin_srt)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    subtitles = data.get("subtitles") or {}
    assert subtitles.get("primary_editable_format") == "srt"
    assert subtitles.get("primary_editable_text") == mm_srt
    assert subtitles.get("srt_text") == mm_srt
    assert subtitles.get("edited_text") == mm_srt
    assert subtitles.get("dub_input_text") == mm_srt
    assert subtitles.get("dub_input_format") == "srt"


def test_hot_follow_workbench_hub_survives_optional_presentation_aggregation_failure(monkeypatch):
    task_id = "hf-workbench-presentation-safe-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "target_lang": "mm",
            "title": "safe fallback",
        },
    )

    monkeypatch.setattr(hf_router, "_hf_artifact_facts", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
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
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("artifact_facts") == {}
    assert data.get("current_attempt") == {}
    assert data.get("operator_summary") == {}


def test_hot_follow_compose_rejects_stale_revision_submission(monkeypatch):
    task_id = "hf-compose-revision-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "subtitles_override_updated_at": "2026-03-14T10:00:00+00:00",
            "audio_sha256": "audio-current",
        },
    )

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.post(
            f"/api/hot_follow/tasks/{task_id}/compose",
            json={
                "expected_subtitle_updated_at": "2026-03-14T09:00:00+00:00",
                "expected_audio_sha256": "audio-current",
            },
        )

    assert res.status_code == 409
    detail = res.json().get("detail") or {}
    assert detail.get("reason") == "compose_revision_mismatch"


def test_hot_follow_compose_route_applies_service_updates_outside_compose_service(monkeypatch):
    task_id = "hf-compose-route-success-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "my",
            "content_lang": "my",
            "compose_plan": {"overlay_subtitles": True},
        },
    )

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())
    monkeypatch.setattr(hf_router.CompositionService, "resolve_fresh_final_key", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        hf_router.CompositionService,
        "compose",
        lambda self, _task_id, _task, **_kwargs: ComposeResult(
            updates={
                "compose_status": "done",
                "compose_last_status": "done",
                "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
                "final_video_path": f"deliver/tasks/{task_id}/final.mp4",
                "status": "ready",
                "last_step": "compose",
            },
            final_key=f"deliver/tasks/{task_id}/final.mp4",
            final_url=f"/v1/tasks/{task_id}/final",
            compose_status="done",
        ),
    )
    monkeypatch.setattr(
        hf_router,
        "_service_build_hot_follow_workbench_hub",
        lambda current_task_id, repo=None: {"task_id": current_task_id, "compose_status": (repo.get(current_task_id) or {}).get("compose_status")},
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.post(f"/api/hot_follow/tasks/{task_id}/compose", json={})

    assert res.status_code == 200
    data = res.json()
    assert data["compose_status"] == "done"
    assert data["final_key"] == f"deliver/tasks/{task_id}/final.mp4"
    assert (data["hub"] or {}).get("compose_status") == "done"

    saved = repo.get(task_id) or {}
    assert saved["compose_status"] == "done"
    assert saved["final_video_key"] == f"deliver/tasks/{task_id}/final.mp4"
