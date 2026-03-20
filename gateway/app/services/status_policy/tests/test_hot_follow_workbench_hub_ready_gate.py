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
from gateway.app.services import task_view_helpers
from gateway.app.services import voice_state as voice_state_service


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
    monkeypatch.setattr(
        hf_router,
        "_hf_persisted_audio_state",
        lambda *_args, **_kwargs: {"exists": False, "voiceover_url": None},
    )
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4"},
    )
    monkeypatch.setattr(task_view_helpers, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))


def test_hot_follow_workbench_ready_gate_backfills_compose_when_final_exists(monkeypatch):
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
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "final": {"exists": True},
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": True,
            "composed_reason": "ready",
            "final_fresh": True,
            "final": {"exists": True, "url": None, "size_bytes": 0},
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
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
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
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "deliverables": [
                {"kind": "final", "status": "pending", "state": "pending", "url": None},
            ],
            "final": {"exists": True},
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": True,
            "composed_reason": "ready",
            "final_fresh": True,
            "final": {"exists": True, "url": None, "size_bytes": 0},
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
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
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


def test_hot_follow_workbench_promotes_fresh_final_after_successful_recompose(monkeypatch):
    task_id = "hf-workbench-recompose-promoted-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "done",
            "compose_last_started_at": "2026-03-21T10:00:00+00:00",
            "compose_last_finished_at": "2026-03-21T10:01:00+00:00",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "final_updated_at": "2026-03-21T10:01:00+00:00",
            "final_asset_version": "etag-final-new",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "mm_audio_provider": "azure-speech",
            "mm_audio_voice_id": "my-MM-NilarNeural",
            "dub_status": "done",
            "audio_sha256": "audio-new",
            "final_source_audio_sha256": "audio-new",
            "subtitles_override_updated_at": "2026-03-21T09:59:00+00:00",
            "final_source_subtitle_updated_at": "2026-03-21T09:59:00+00:00",
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
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        hf_router,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-final-new"},
    )
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        task_view_helpers,
        "object_head",
        lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4", "etag": "etag-final-new"},
    )
    monkeypatch.setattr(task_view_helpers, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(
        "gateway.app.services.voice_state.collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("final_fresh") is True
    assert data.get("final_stale_reason") is None
    assert data.get("composed_ready") is True
    assert data.get("ready_gate", {}).get("compose_ready") is True
    assert str(data.get("compose_status") or "").lower() == "done"
    assert (data.get("current_attempt") or {}).get("compose_status") == "done"
    assert (data.get("current_attempt") or {}).get("requires_recompose") is False
    assert data.get("final_exists") is True
    assert (data.get("final") or {}).get("exists") is True
    assert str(data.get("final_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("artifact_facts") or {}).get("final_exists") is True

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status") or "").lower() == "done"
    assert str(saved.get("compose_last_status") or "").lower() == "done"


def test_hot_follow_workbench_recomputes_composed_after_state_normalization(monkeypatch):
    task_id = "hf-workbench-recompose-recompute-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "done",
            "compose_last_started_at": "2026-03-21T10:00:00+00:00",
            "compose_last_finished_at": "2026-03-21T10:01:00+00:00",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "dub_status": "done",
            "audio_sha256": "audio-new",
            "final_source_audio_sha256": "audio-new",
            "subtitles_override_updated_at": "2026-03-21T09:59:00+00:00",
            "final_source_subtitle_updated_at": "2026-03-21T09:59:00+00:00",
        },
    )

    composed_calls = {"count": 0}

    def _sequenced_composed(_task, _task_id):
        composed_calls["count"] += 1
        if composed_calls["count"] == 1:
            return {
                "composed_ready": False,
                "composed_reason": "final_stale_after_dub",
                "final_fresh": False,
                "final_stale_reason": "final_stale_after_dub",
                "final": {"exists": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 8192},
                "compose_error_reason": None,
                "compose_error_message": None,
                "raw_exists": True,
                "voice_exists": True,
            }
        return {
            "composed_ready": True,
            "composed_reason": "ready",
            "final_fresh": True,
            "final_stale_reason": None,
            "final": {"exists": True, "url": f"/v1/tasks/{task_id}/final", "size_bytes": 8192},
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(hf_router, "_compute_composed_state", _sequenced_composed)
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert composed_calls["count"] >= 2
    assert data.get("composed_ready") is True
    assert data.get("final_fresh") is True
    assert data.get("ready_gate", {}).get("compose_ready") is True
    assert str(data.get("compose_status") or "").lower() == "done"
    compose_step = next(
        (x for x in (data.get("pipeline") or []) if str(x.get("key") or "").strip().lower() == "compose"),
        {},
    )
    assert compose_step.get("status") == "done"
    assert (data.get("current_attempt") or {}).get("requires_recompose") is False
    assert (data.get("current_attempt") or {}).get("compose_status") == "done"
    assert data.get("final_exists") is True
    assert (data.get("final") or {}).get("exists") is True
    assert str(data.get("final_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert str(data.get("final_video_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("artifact_facts") or {}).get("final_exists") is True


def test_hot_follow_workbench_overlay_cannot_rewrite_successful_current_final_to_stale(monkeypatch):
    task_id = "hf-workbench-overlay-success-01"
    repo = _Repo()
    ready_voice_state = {
        "audio_ready": True,
        "audio_ready_reason": "ready",
        "dub_current": True,
        "dub_current_reason": "ready",
        "requested_voice": "mm_female_1",
        "resolved_voice": "my-MM-NilarNeural",
        "actual_provider": "azure-speech",
        "deliverable_audio_done": True,
        "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
    }
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "done",
            "compose_last_finished_at": "2026-03-21T10:01:00+00:00",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "dub_status": "done",
            "audio_sha256": "audio-new",
            "final_source_audio_sha256": "audio-new",
            "subtitles_override_updated_at": "2026-03-21T09:59:00+00:00",
            "final_source_subtitle_updated_at": "2026-03-21T09:59:00+00:00",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_safe_collect_hot_follow_workbench_ui",
        lambda *_args, **_kwargs: {
            "compose_status": "pending",
            "final_exists": False,
            "final_url": None,
            "final_video_url": None,
            "composed_ready": False,
            "composed_reason": "final_stale_after_dub",
            "final_fresh": False,
            "final_stale_reason": "final_stale_after_dub",
            "current_attempt": {"compose_status": "pending", "requires_recompose": True},
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: dict(ready_voice_state),
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: dict(ready_voice_state),
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert str(data.get("compose_status") or "").lower() == "done"
    assert data.get("composed_ready") is True
    assert data.get("final_fresh") is True
    assert (data.get("final") or {}).get("exists") is True
    assert str(data.get("final_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert str(data.get("final_video_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("current_attempt") or {}).get("requires_recompose") is False


def test_hot_follow_workbench_promotes_current_final_when_latest_compose_is_newer_than_inputs(monkeypatch):
    task_id = "hf-workbench-latest-compose-wins-01"
    repo = _Repo()
    ready_voice_state = {
        "audio_ready": True,
        "audio_ready_reason": "ready",
        "dub_current": True,
        "dub_current_reason": "ready",
        "requested_voice": "mm_female_1",
        "resolved_voice": "my-MM-NilarNeural",
        "actual_provider": "azure-speech",
        "deliverable_audio_done": True,
        "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
    }
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "done",
            "compose_last_status": "done",
            "compose_last_finished_at": "2026-03-21T10:01:00+00:00",
            "final_updated_at": "2026-03-21T10:01:00+00:00",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "dub_status": "done",
            "audio_sha256": "audio-new",
            "final_source_audio_sha256": "audio-old",
            "dub_generated_at": "2026-03-21T09:59:00+00:00",
            "subtitles_override_updated_at": "2026-03-21T10:00:00+00:00",
            "final_source_subtitle_updated_at": "2026-03-21T09:30:00+00:00",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: dict(ready_voice_state),
    )
    monkeypatch.setattr(
        voice_state_service,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: dict(ready_voice_state),
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("ready_gate", {}).get("compose_ready") is True
    assert data.get("composed_ready") is True
    assert data.get("composed_reason") == "ready"
    assert str(data.get("compose_status") or "").lower() == "done"
    assert (((data.get("compose") or {}).get("last") or {}).get("status")) == "done"
    assert data.get("final_exists") is True
    assert (data.get("final") or {}).get("exists") is True
    assert str(data.get("final_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert str(data.get("final_video_url") or "").endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("current_attempt") or {}).get("compose_status") == "done"
    assert (data.get("current_attempt") or {}).get("requires_recompose") is False


def test_hot_follow_workbench_marks_old_final_stale_after_redub(monkeypatch):
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
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
            "mm_audio_provider": "azure-speech",
            "mm_audio_voice_id": "my-MM-NilarNeural",
            "dub_status": "done",
            "audio_sha256": "audio-new",
            "final_source_audio_sha256": "audio-old",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_compute_composed_state",
        lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_stale_after_dub",
            "final_fresh": False,
            "final_stale_reason": "final_stale_after_dub",
            "final": {"exists": True, "url": None, "size_bytes": 8192},
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
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
            "deliverable_audio_done": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_hf_persisted_audio_state",
        lambda *_args, **_kwargs: {"exists": True, "voiceover_url": f"/v1/tasks/{task_id}/audio_mm"},
    )
    _patch_workbench_storage_dependencies(monkeypatch)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "8192", "Content-Type": "video/mp4"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (8192, "video/mp4"))
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("ready_gate", {}).get("compose_ready") is False
    assert data.get("composed_ready") is False
    assert data.get("composed_reason") == "final_stale_after_dub"
    assert str(data.get("compose_status") or "").lower() == "pending"
    assert (data.get("current_attempt") or {}).get("compose_status") == "pending"
    assert (data.get("current_attempt") or {}).get("requires_recompose") is True
    assert (((data.get("compose") or {}).get("last") or {}).get("status")) == "done"
    assert (data.get("operator_summary") or {}).get("recommended_next_action") == "当前配音已更新，建议重新合成最终视频以生成最新版本。"
    assert data.get("final_exists") is False
    assert (data.get("final") or {}).get("exists") is False
    assert (data.get("historical_final") or {}).get("exists") is True
    assert data.get("final_url") is None
    assert ((data.get("media") or {}).get("final_url")) is None
    assert (data.get("artifact_facts") or {}).get("final_exists") is True
    compose_step = next(
        (x for x in (data.get("pipeline") or []) if str(x.get("key") or "").strip().lower() == "compose"),
        {},
    )
    assert compose_step.get("status") == "pending"
    final_row = next(
        (x for x in (data.get("deliverables") or []) if str(x.get("kind") or "").strip().lower() == "final"),
        {},
    )
    assert final_row.get("status") == "pending"
    assert final_row.get("historical") is True
    assert str(final_row.get("url") or "").endswith(f"/v1/tasks/{task_id}/final")


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
