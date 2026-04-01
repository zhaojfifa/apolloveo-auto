from pathlib import Path
import sys
import types
from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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


def test_hot_follow_new_routes_render_without_template_signature_error():
    from gateway.app.routers import hot_follow_ui

    app = FastAPI()

    calls = []

    def _fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        _ = (request, headers)
        calls.append({"name": name, "ctx": dict(ctx or {}), "status_code": status_code})
        return HTMLResponse("<div id='hf-create'></div>", status_code=status_code)

    hot_follow_ui.render_template = _fake_render_template
    app.include_router(hot_follow_ui.router)

    with TestClient(app) as client:
        res_primary = client.get("/tasks/hot/new")
        res_locale = client.get("/tasks/hot/new?ui_locale=zh")

    assert res_primary.status_code == 200
    assert res_locale.status_code == 200
    assert "hf-create" in res_primary.text
    assert "hf-create" in res_locale.text
    assert len(calls) == 2
    assert all(call["name"] == "hot_follow_new.html" for call in calls)
    assert all("language_profiles" in call["ctx"] for call in calls)
    vi_profile = next(
        profile
        for profile in calls[-1]["ctx"]["language_profiles"]
        if str(profile.get("target_lang")) == "vi"
    )
    assert vi_profile["display_name"] == "Tiếng Việt"
    assert vi_profile["allowed_voice_options"] == ["vi_female_1", "vi_male_1"]


def test_hot_follow_new_template_contains_link_and_local_source_controls():
    src = Path("gateway/app/templates/hot_follow_new.html").read_text(encoding="utf-8", errors="ignore")

    assert 'name="source_mode"' in src
    assert 'value="link"' in src
    assert 'value="local"' in src
    assert 'id="hf-local-file"' in src
    assert 'id="hf-source-lang"' in src


def test_hot_follow_local_upload_creates_normal_hot_follow_task(monkeypatch, tmp_path):
    from gateway.app.routers import hot_follow_api as hf_router
    from gateway.app.utils.pipeline_config import parse_pipeline_config

    class _Repo:
        def __init__(self):
            self.items = {}

        def create(self, payload):
            self.items[payload["task_id"]] = dict(payload)

        def get(self, task_id):
            item = self.items.get(task_id)
            return dict(item) if item else None

        def upsert(self, task_id, updates):
            cur = dict(self.items.get(task_id) or {})
            cur.update(dict(updates or {}))
            self.items[task_id] = cur

    repo = _Repo()
    app = FastAPI()
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[hf_router.get_task_repository] = lambda: repo

    def _fake_save_upload_to_paths(*, upload, inputs_path, raw_path_target, max_bytes):
        data = upload.file.read()
        assert len(data) <= max_bytes
        inputs_path.parent.mkdir(parents=True, exist_ok=True)
        inputs_path.write_bytes(data)
        if raw_path_target != inputs_path:
            raw_path_target.write_bytes(data)
        return len(data)

    monkeypatch.setattr(hf_router, "_save_upload_to_paths", _fake_save_upload_to_paths)
    monkeypatch.setattr(hf_router, "assert_local_video_ok", lambda _path: (1024, 1.2))
    monkeypatch.setattr(hf_router, "probe_subtitles", lambda _path: {"subtitle_track_kind": "none"})
    monkeypatch.setattr(hf_router, "raw_path", lambda task_id: tmp_path / task_id / "raw" / "raw.mp4")
    monkeypatch.setattr(
        hf_router,
        "_task_to_detail",
        lambda task: {
            "task_id": str(task.get("task_id")),
            "title": task.get("title"),
            "kind": task.get("kind"),
            "source_url": task.get("source_url"),
            "platform": task.get("platform"),
            "category_key": task.get("category_key"),
            "content_lang": task.get("content_lang"),
            "ui_lang": task.get("ui_lang") or "zh",
            "face_swap_enabled": False,
            "status": task.get("status") or "pending",
            "created_at": task.get("created_at") or "2026-04-01T00:00:00+00:00",
            "raw_path": f"/v1/tasks/{task.get('task_id')}/raw" if task.get("raw_path") else None,
            "pipeline_config": parse_pipeline_config(task.get("pipeline_config")),
        },
    )
    monkeypatch.setattr(
        hf_router,
        "upload_task_artifact",
        lambda _task, _path, artifact_name, task_id=None: f"deliver/tasks/{task_id}/{artifact_name}",
    )

    with TestClient(app) as client:
        res = client.post(
            "/api/hot_follow/tasks/local_upload",
            files={"file": ("demo.mp4", BytesIO(b"fake-video"), "video/mp4")},
            data={
                "target_lang": "vi",
                "source_lang": "en",
                "voice_id": "vi_female_1",
                "process_mode": "smart_rewrite",
                "publish_account": "account_a",
                "task_title": "Local HF",
                "ui_lang": "zh",
            },
        )

    assert res.status_code == 200, res.text
    payload = res.json()
    task_id = payload["task_id"]
    stored = repo.get(task_id)
    assert stored is not None
    assert stored["kind"] == "hot_follow"
    assert stored["category_key"] == "hot_follow"
    assert stored["platform"] == "local"
    assert stored["source_type"] == "local"
    assert stored["source_filename"] == "demo.mp4"
    assert stored["raw_path"] == f"deliver/tasks/{task_id}/raw.mp4"
    assert payload["raw_path"] == f"/v1/tasks/{task_id}/raw"
    assert parse_pipeline_config(stored.get("pipeline_config")).get("ingest_mode") == "local"
    assert parse_pipeline_config(stored.get("pipeline_config")).get("source_language_hint") == "en"
    assert parse_pipeline_config(stored.get("pipeline_config")).get("process_mode") == "smart_rewrite"
    assert parse_pipeline_config(stored.get("pipeline_config")).get("publish_account") == "account_a"
