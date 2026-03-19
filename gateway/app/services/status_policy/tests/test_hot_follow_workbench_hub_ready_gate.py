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
            "final": {"exists": True},
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": True, "url": None, "size_bytes": 0},
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(hf_router, "_compute_composed_state", _fake_composed)
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
            "deliverables": [
                {"kind": "final", "status": "pending", "state": "pending", "url": None},
            ],
            "final": {"exists": True},
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": True, "url": None, "size_bytes": 0},
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(hf_router, "_compute_composed_state", _fake_composed)
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
