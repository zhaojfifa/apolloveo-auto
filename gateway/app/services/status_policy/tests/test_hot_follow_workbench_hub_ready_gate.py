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
from gateway.app.services.compose_helpers import task_compose_lock
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
                else (
                    "waiting_for_target_subtitle_translation"
                    if str(task.get("target_subtitle_current_reason") or "") == "target_subtitle_translation_incomplete"
                    else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
                )
            ),
            "dub_current": bool(task.get("target_subtitle_current")),
            "dub_current_reason": (
                "ready"
                if task.get("target_subtitle_current")
                else (
                    "waiting_for_target_subtitle_translation"
                    if str(task.get("target_subtitle_current_reason") or "") == "target_subtitle_translation_incomplete"
                    else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
                )
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
    assert data["subtitles"]["status"] == "pending"
    assert data["subtitles"]["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation"
    assert data["subtitles"]["helper_translation"]["status"] == "pending"
    assert data["subtitles"]["helper_translation"]["visibility"] == "pending_provider_work"
    assert data["ready_gate"]["subtitle_ready"] is False
    assert data["ready_gate"]["compose_ready"] is False
    assert data["ready_gate"]["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation"

    dub_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "dub"), {})
    compose_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "compose"), {})
    assert dub_step.get("status") == "pending"
    assert compose_step.get("status") == "pending"


def test_hot_follow_workbench_myanmar_currentness_blocks_false_done_states(monkeypatch):
    task_id = "hf-workbench-mm-currentness-01"
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
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "mm_audio_voice_id": "my-MM-NilarNeural",
            "mm_audio_provider": "azure-speech",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "mm_srt_path": f"deliver/tasks/{task_id}/mm.srt",
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
                else (
                    "waiting_for_target_subtitle_translation"
                    if str(task.get("target_subtitle_current_reason") or "") == "target_subtitle_translation_incomplete"
                    else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
                )
            ),
            "dub_current": bool(task.get("target_subtitle_current")),
            "dub_current_reason": (
                "ready"
                if task.get("target_subtitle_current")
                else (
                    "waiting_for_target_subtitle_translation"
                    if str(task.get("target_subtitle_current_reason") or "") == "target_subtitle_translation_incomplete"
                    else str(task.get("target_subtitle_current_reason") or "target_subtitle_not_current")
                )
            ),
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
            "voiceover_url": "/v1/tasks/hf-workbench-mm-currentness-01/audio_mm",
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
        lambda key: str(key).endswith(("origin.srt", "mm.srt", "final.mp4")),
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
    assert data["subtitles"]["status"] == "pending"
    assert data["subtitles"]["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation"
    assert data["ready_gate"]["subtitle_ready"] is False
    assert data["ready_gate"]["compose_ready"] is False
    assert data["ready_gate"]["publish_ready"] is False
    assert data["ready_gate"]["audio_ready_reason"] == "waiting_for_target_subtitle_translation"

    dub_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "dub"), {})
    compose_step = next((row for row in (data.get("pipeline") or []) if row.get("key") == "compose"), {})
    assert dub_step.get("status") == "pending"
    assert compose_step.get("status") == "pending"


def test_hot_follow_workbench_translation_incomplete_does_not_project_stale_empty_no_dub(monkeypatch):
    task_id = "hf-workbench-mm-translation-unresolved-no-dub"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "mm",
            "content_lang": "mm",
            "dub_status": "failed",
            "voice_id": "mm_female_1",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "subtitles_status": "pending",
            "pipeline_config": {
                "translation_incomplete": "true",
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
            },
            "dub_skip_reason": "target_subtitle_empty",
            "events": [
                {
                    "code": "post.dub.fail",
                    "message": "reason=target_subtitle_translation_incomplete",
                }
            ],
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "not_ready",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "compose_error_reason": None,
            "compose_error_message": None,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "waiting_for_target_subtitle_translation",
            "dub_current": False,
            "dub_current_reason": "waiting_for_target_subtitle_translation",
            "voiceover_url": None,
            "deliverable_audio_done": False,
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "mm_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "task_base_dir", lambda current_task_id: Path("/tmp") / current_task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key).endswith("origin.srt"))
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(
        hf_router,
        "get_object_bytes",
        lambda _key: "1\n00:00:00,000 --> 00:00:02,000\nvoice led transcript\n".encode("utf-8"),
    )
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        hf_router,
        "_hf_load_origin_subtitles_text",
        lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\nvoice led transcript\n",
    )
    monkeypatch.setattr(
        hf_router,
        "_hf_load_normalized_source_text",
        lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\nvoice led transcript\n",
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["subtitles"]["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert data["subtitles"]["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation"
    assert data["subtitles"]["helper_translation"]["status"] == "pending"
    assert data["subtitles"]["helper_translation"]["visibility"] == "pending_provider_work"
    assert data["artifact_facts"]["selected_compose_route"]["name"] == "tts_replace_route"
    assert data["current_attempt"]["selected_compose_route"] == "tts_replace_route"
    assert data["current_attempt"]["subtitle_translation_waiting_retryable"] is True
    assert data["current_attempt"]["dub_status"] == "pending"
    assert data["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert data["ready_gate"]["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation"
    assert data["ready_gate"]["audio_ready_reason"] == "waiting_for_target_subtitle_translation"
    assert data["no_dub"] is False
    assert data["no_dub_reason"] is None
    subtitle_deliverable = next(item for item in data.get("deliverables") or [] if item.get("kind") == "subtitle")
    audio_deliverable = next(item for item in data.get("deliverables") or [] if item.get("kind") == "audio")
    assert subtitle_deliverable["status"] == "pending"
    assert subtitle_deliverable["state"] == "pending"
    assert audio_deliverable["status"] == "pending"
    assert audio_deliverable["state"] == "pending"
    assert "等待" in data["operator_summary"]["recommended_next_action"]
    assert data["advisory"]["recommended_next_action"] == "wait_or_retry_translation"


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


def test_hot_follow_workbench_pack_error_does_not_pollute_parse_pipeline(monkeypatch):
    task_id = "hf-workbench-pack-error-isolation-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "failed",
            "last_step": "pack",
            "parse_status": "done",
            "pack_status": "failed",
            "pack_error": "request model invalid",
            "error_message": "request model invalid",
            "raw_path": f"deliver/tasks/{task_id}/raw/raw.mp4",
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

    parse_step = next((x for x in (data.get("pipeline") or []) if x.get("key") == "parse"), {})
    pack_step = next((x for x in (data.get("pipeline") or []) if x.get("key") == "pack"), {})
    assert parse_step.get("status") == "done"
    assert parse_step.get("error") is None
    assert pack_step.get("status") == "failed"
    assert pack_step.get("error") == "request model invalid"


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


def test_hot_follow_workbench_does_not_hydrate_timing_only_target_artifact(monkeypatch):
    task_id = "hf-workbench-empty-target"
    repo = _Repo()
    target_key = f"deliver/tasks/{task_id}/mm.srt"
    origin_key = f"deliver/tasks/{task_id}/origin.srt"
    timing_only_srt = "1\n00:00:00,000 --> 00:00:02,000\n\n"
    store = {
        target_key: timing_only_srt.encode("utf-8"),
        origin_key: "1\n00:00:00,000 --> 00:00:02,000\nvoice led source\n".encode("utf-8"),
    }
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "my",
            "subtitles_status": "done",
            "origin_srt_path": origin_key,
            "mm_srt_path": target_key,
            "compose_status": "pending",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "not_ready",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "compose_error_reason": None,
            "compose_error_message": None,
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda task_id: Path("/tmp") / task_id / "override.srt")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    subtitles = data.get("subtitles") or {}
    assert subtitles.get("primary_editable_text") == ""
    assert subtitles.get("srt_text") == ""
    assert subtitles.get("edited_text") == ""
    assert subtitles.get("dub_input_text") == ""
    assert subtitles.get("subtitle_ready") is False
    assert subtitles.get("target_subtitle_current") is False
    assert subtitles.get("target_subtitle_current_reason") == "subtitle_missing"

    subtitle_deliverable = next(item for item in data.get("deliverables") or [] if item.get("kind") == "subtitle")
    assert subtitle_deliverable.get("status") == "pending"
    assert subtitle_deliverable.get("state") == "pending"
    assert subtitle_deliverable.get("url") is None
    assert subtitle_deliverable.get("open_url") is None
    assert subtitle_deliverable.get("download_url") is None

    artifact_facts = data.get("artifact_facts") or {}
    assert artifact_facts.get("subtitle_exists") is False
    assert artifact_facts.get("subtitle_url") is None
    assert (data.get("ready_gate") or {}).get("subtitle_ready") is False
    assert data.get("no_dub") is False


def test_hot_follow_workbench_resolves_subtitles_terminal_success_when_authoritative_truth_is_current(monkeypatch):
    task_id = "hf-workbench-subtitles-terminal-success"
    repo = _Repo()
    target_key = f"deliver/tasks/{task_id}/vi.srt"
    target_srt = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "vi",
            "content_lang": "vi",
            "subtitles_status": "failed",
            "subtitles_error": "翻译服务当前额度不足或请求过多，请稍后重试。",
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "翻译服务当前额度不足或请求过多，请稍后重试。",
            "mm_srt_path": target_key,
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
            "dub_skip_reason": "target_subtitle_empty",
            "dub_status": "done",
            "voice_id": "vi_female_1",
            "dub_provider": "azure-speech",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_vi.mp3",
            "mm_audio_provider": "azure-speech",
            "mm_audio_voice_id": "vi-VN-HoaiMyNeural",
            "config": {
                "tts_requested_voice": "vi_female_1",
                "tts_resolved_voice": "vi-VN-HoaiMyNeural",
                "tts_provider": "azure-speech",
                "tts_voiceover_key": f"deliver/tasks/{task_id}/audio_vi.mp3",
            },
            "events": [
                {
                    "code": "post.dub.skip",
                    "message": "reason=target_subtitle_empty",
                }
            ],
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "not_ready",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "compose_error_reason": None,
            "compose_error_message": None,
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
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio",
            "resolved_voice": "vi-VN-HoaiMyNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "vi_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in {target_key, f"deliver/tasks/{task_id}/audio_vi.mp3"})
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: target_srt.encode("utf-8") if str(key) == target_key else b"")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: target_srt)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\n你好\n")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    subtitles = data.get("subtitles") or {}
    helper = subtitles.get("helper_translation") or {}
    pipeline_rows = data.get("pipeline") or []
    subtitles_row = next(row for row in pipeline_rows if row.get("key") == "subtitles")

    assert subtitles.get("subtitle_ready") is True
    assert subtitles.get("target_subtitle_current") is True
    assert subtitles.get("target_subtitle_authoritative_source") is True
    assert subtitles.get("edited_text") == target_srt
    assert subtitles_row.get("status") == "done"
    assert subtitles_row.get("state") == "done"
    assert subtitles_row.get("error") is None
    assert helper.get("failed") is True
    assert helper.get("reason") == "helper_translate_provider_exhausted"
    assert data.get("audio_ready") is True
    assert data.get("dub_current") is True
    assert data.get("no_dub") is False
    assert data.get("no_dub_reason") is None


def test_hot_follow_workbench_recovers_current_audio_preview_and_clears_stale_failed_residue(monkeypatch):
    task_id = "hf-workbench-audio-preview-recovery"
    repo = _Repo()
    target_key = f"deliver/tasks/{task_id}/vi.srt"
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "vi",
            "content_lang": "vi",
            "subtitles_status": "ready",
            "mm_srt_path": target_key,
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "翻译服务当前额度不足或请求过多，请稍后重试。",
            "dub_status": "failed",
            "dub_error": "stale audio generation failure",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
            "dub_skip_reason": "target_subtitle_empty",
            "voice_id": "vi_female_1",
            "dub_provider": "azure-speech",
            "mm_audio_key": f"deliver/tasks/{task_id}/voiceover/audio_vi.dry.mp3",
            "mm_audio_provider": "azure-speech",
            "mm_audio_voice_id": "vi-VN-HoaiMyNeural",
            "config": {
                "tts_requested_voice": "vi_female_1",
                "tts_resolved_voice": "vi-VN-HoaiMyNeural",
                "tts_provider": "azure-speech",
                "tts_voiceover_key": f"deliver/tasks/{task_id}/voiceover/audio_vi.dry.mp3",
            },
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "not_ready",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "compose_error_reason": None,
            "compose_error_message": None,
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
            "deliverable_audio_done": True,
            "voiceover_url": None,
            "resolved_voice": "vi-VN-HoaiMyNeural",
            "actual_provider": "azure-speech",
            "requested_voice": "vi_female_1",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in {target_key, f"deliver/tasks/{task_id}/voiceover/audio_vi.dry.mp3"})
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda _key: b"1\n00:00:00,000 --> 00:00:02,000\nXin chao\n")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\n你好\n")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    audio = data.get("audio") or {}
    media = data.get("media") or {}
    dub_row = next(row for row in (data.get("pipeline") or []) if row.get("key") == "dub")
    helper = ((data.get("subtitles") or {}).get("helper_translation") or {})

    assert audio.get("audio_ready") is True
    assert audio.get("dub_current") is True
    assert audio.get("error") in {None, ""}
    assert audio.get("voiceover_url") == f"/v1/tasks/{task_id}/audio_mm"
    assert audio.get("tts_voiceover_url") == f"/v1/tasks/{task_id}/audio_mm"
    assert audio.get("dub_preview_url") == f"/v1/tasks/{task_id}/audio_mm"
    assert media.get("voiceover_url") == f"/v1/tasks/{task_id}/audio_mm"
    assert dub_row.get("status") == "done"
    assert data.get("no_dub") is False
    assert data.get("no_dub_reason") is None
    assert helper.get("failed") is True


def test_hot_follow_workbench_preserve_source_route_does_not_project_target_subtitle_authority_failure(monkeypatch):
    task_id = "hf-workbench-preserve-source-contract"
    repo = _Repo()
    origin_key = f"deliver/tasks/{task_id}/origin.srt"
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "vi",
            "content_lang": "vi",
            "subtitles_status": "ready",
            "subtitles_error": None,
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            "origin_srt_path": origin_key,
            "pipeline_config": {
                "parse_source_mode": "preserved_source_audio_helper",
                "parse_source_role": "preserved_source_audio_helper",
                "parse_source_authoritative_for_target": "false",
                "target_subtitle_authoritative": "false",
                "source_audio_policy": "preserve",
            },
            "config": {"source_audio_policy": "preserve"},
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "not_ready",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "compose_error_reason": None,
            "compose_error_message": None,
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
            "dub_current_reason": "audio_missing",
            "deliverable_audio_done": False,
            "voiceover_url": None,
            "resolved_voice": None,
            "actual_provider": "azure-speech",
            "requested_voice": None,
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) == origin_key)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda _key: b"1\n00:00:00,000 --> 00:00:02,000\nlyric source line\n")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "1\n00:00:00,000 --> 00:00:02,000\nlyric source line\n")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    subtitles = data.get("subtitles") or {}
    subtitles_row = next(row for row in (data.get("pipeline") or []) if row.get("key") == "subtitles")
    ready_gate = data.get("ready_gate") or {}

    assert subtitles_row.get("status") == "done"
    assert subtitles_row.get("error") in {None, ""}
    assert subtitles.get("target_subtitle_current") is False
    assert subtitles.get("target_subtitle_current_reason") == "preserve_source_route_no_target_subtitle_required"
    assert ready_gate.get("selected_compose_route") == "preserve_source_route"
    assert ready_gate.get("compose_allowed") is True
    assert ready_gate.get("no_dub_reason") == "source_audio_preserved_no_tts"


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


def test_hot_follow_compose_failure_finalizes_releases_lock_and_allows_retry(monkeypatch):
    task_id = "hf-compose-heavy-timeout-01"
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
    calls = {"compose": 0}

    def _compose_once_then_success(self, _task_id, _task, **_kwargs):
        calls["compose"] += 1
        if calls["compose"] == 1:
            raise hf_router.HTTPException(
                status_code=409,
                detail={"reason": "compose_timeout", "message": "heavy compose timed out"},
            )
        return ComposeResult(
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
        )

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())
    monkeypatch.setattr(hf_router.CompositionService, "resolve_fresh_final_key", lambda *args, **kwargs: None)
    monkeypatch.setattr(hf_router.CompositionService, "compose", _compose_once_then_success)
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
        failed = client.post(f"/api/hot_follow/tasks/{task_id}/compose", json={})
        assert failed.status_code == 409
        saved_after_failure = repo.get(task_id) or {}
        assert saved_after_failure["compose_status"] == "failed"
        assert saved_after_failure["compose_last_status"] == "failed"
        assert saved_after_failure["compose_error_reason"] == "compose_timeout"
        assert saved_after_failure.get("compose_lock_until") is None
        assert task_compose_lock(task_id).locked() is False

        retried = client.post(f"/api/hot_follow/tasks/{task_id}/compose", json={})
        assert retried.status_code == 200

    saved_after_retry = repo.get(task_id) or {}
    assert calls["compose"] == 2
    assert saved_after_retry["compose_status"] == "done"
    assert saved_after_retry["final_video_key"] == f"deliver/tasks/{task_id}/final.mp4"


def test_hot_follow_compose_derive_failure_persists_compose_input_truth_and_allows_retry(monkeypatch):
    task_id = "hf-compose-derive-failed-retry-01"
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
    calls = {"compose": 0}

    def _compose_once_then_success(self, _task_id, _task, **_kwargs):
        calls["compose"] += 1
        if calls["compose"] == 1:
            raise hf_router.HTTPException(
                status_code=409,
                detail={
                    "reason": "compose_input_derive_failed",
                    "message": "derived compose input is not encoder-safe",
                    "failure_code": "derive_not_encoder_safe",
                    "compose_input_profile": {"width": 1081, "height": 1921, "pix_fmt": "yuv422p"},
                    "safe_key": "video_input_safe.mp4",
                },
            )
        return ComposeResult(
            updates={
                "compose_status": "done",
                "compose_last_status": "done",
                "compose_input_policy": {
                    "mode": "derived_ready",
                    "source": "derived_safe",
                    "profile": {"width": 1080, "height": 1920, "pix_fmt": "yuv420p"},
                    "safe_key": "video_input_safe.mp4",
                    "reason": "large_local_input_derived",
                    "failure_code": None,
                },
                "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
                "final_video_path": f"deliver/tasks/{task_id}/final.mp4",
                "status": "ready",
                "last_step": "compose",
            },
            final_key=f"deliver/tasks/{task_id}/final.mp4",
            final_url=f"/v1/tasks/{task_id}/final",
            compose_status="done",
        )

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())
    monkeypatch.setattr(hf_router.CompositionService, "resolve_fresh_final_key", lambda *args, **kwargs: None)
    monkeypatch.setattr(hf_router.CompositionService, "compose", _compose_once_then_success)
    monkeypatch.setattr(
        hf_router,
        "_service_build_hot_follow_workbench_hub",
        lambda current_task_id, repo=None: {
            "task_id": current_task_id,
            "compose_status": (repo.get(current_task_id) or {}).get("compose_status"),
            "artifact_facts": {
                "compose_input": (repo.get(current_task_id) or {}).get("compose_input_policy") or {}
            },
        },
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        failed = client.post(f"/api/hot_follow/tasks/{task_id}/compose", json={})
        assert failed.status_code == 409
        saved_after_failure = repo.get(task_id) or {}
        assert saved_after_failure["compose_status"] == "failed"
        assert saved_after_failure["compose_error_reason"] == "compose_input_derive_failed"
        assert saved_after_failure.get("compose_lock_until") is None
        assert task_compose_lock(task_id).locked() is False
        failed_policy = saved_after_failure.get("compose_input_policy") or {}
        assert failed_policy["mode"] == "derive_failed"
        assert failed_policy["source"] == "derived_safe"
        assert failed_policy["failure_code"] == "derive_not_encoder_safe"

        retried = client.post(f"/api/hot_follow/tasks/{task_id}/compose", json={})
        assert retried.status_code == 200

    saved_after_retry = repo.get(task_id) or {}
    assert calls["compose"] == 2
    assert saved_after_retry["compose_status"] == "done"
    assert saved_after_retry["compose_input_policy"]["mode"] == "derived_ready"


def test_hot_follow_compose_recovers_stale_running_before_false_409(monkeypatch):
    task_id = "hf-compose-stale-running-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "target_lang": "my",
            "content_lang": "my",
            "compose_status": "running",
            "compose_last_status": "running",
            "compose_last_started_at": "2026-04-19T00:00:00+00:00",
            "compose_lock_until": "2099-01-01T00:00:00+00:00",
            "compose_plan": {"overlay_subtitles": True},
        },
    )

    monkeypatch.setenv("HF_COMPOSE_STALE_RUNNING_SEC", "0")
    monkeypatch.setattr("gateway.app.services.compose_service.object_exists", lambda _key: False)
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
    saved = repo.get(task_id) or {}
    assert saved["compose_status"] == "done"
    assert saved.get("compose_lock_until") is None


def test_hot_follow_helper_translate_429_persists_sanitized_helper_failure(monkeypatch):
    task_id = "hf-helper-translate-429"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "my",
            "content_lang": "my",
        },
    )

    def _raise_resource_exhausted(*_args, **_kwargs):
        raise hf_router.GeminiSubtitlesError(
            'Gemini HTTP 429: {"error":{"status":"RESOURCE_EXHAUSTED","message":"quota exhausted"}}'
        )

    monkeypatch.setattr(hf_router, "translate_segments_with_gemini", _raise_resource_exhausted)

    app = FastAPI()
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.post(
            f"/api/hot_follow/tasks/{task_id}/translate_subtitles",
            json={"text": "1\n00:00:00,000 --> 00:00:01,000\nhello\n", "target_lang": "my"},
        )

    assert res.status_code == 409
    detail = res.json()["detail"]
    assert detail["reason"] == "helper_translate_provider_exhausted"
    assert detail["provider"] == "gemini"
    assert "RESOURCE_EXHAUSTED" not in detail["message"]
    assert "{" not in detail["message"]

    saved = repo.get(task_id) or {}
    assert saved["subtitle_helper_status"] == "failed"
    assert saved["subtitle_helper_error_reason"] == "helper_translate_provider_exhausted"
    assert "{" not in saved["subtitle_helper_error_message"]
    assert not saved.get("mm_srt_path")


def test_manual_subtitle_save_clears_helper_translate_failure(monkeypatch, tmp_path):
    task_id = "hf-helper-manual-save"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "ready",
            "target_lang": "my",
            "content_lang": "my",
            "mm_srt_path": f"deliver/tasks/{task_id}/my.srt",
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "翻译服务当前额度不足或请求过多，请稍后重试。",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
            "dub_status": "skipped",
        },
    )

    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(hf_router, "_hf_sync_saved_target_subtitle_artifact", lambda *_args, **_kwargs: f"deliver/tasks/{task_id}/my.srt")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)

    app = FastAPI()
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.patch(
            f"/api/hot_follow/tasks/{task_id}/subtitles",
            json={"srt_text": "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n"},
        )

    assert res.status_code == 200
    saved = repo.get(task_id) or {}
    assert saved["subtitle_helper_status"] == "resolved"
    assert saved.get("subtitle_helper_error_reason") is None
    assert saved.get("subtitle_helper_error_message") is None
    assert saved["dub_status"] == "pending"
    assert "no_dub" not in saved["pipeline_config"]
    assert "dub_skip_reason" not in saved["pipeline_config"]
