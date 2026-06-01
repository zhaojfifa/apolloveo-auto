"""HTTP-boundary tests for the Matrix Script real-trial route (PR-17R)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import pytest

from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    InMemoryArtifactSink,
)
from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(not _FFMPEG, reason="ffmpeg/ffprobe not installed (no fake final.mp4)")


class _StubRepo:
    def __init__(self, tasks: Dict[str, Dict[str, Any]]):
        self._tasks = tasks
        self.mutations: list[str] = []

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def create(self, task):  # pragma: no cover
        self.mutations.append("create"); raise NotImplementedError

    def update(self, task_id, patch):  # pragma: no cover
        self.mutations.append("update"); raise NotImplementedError

    def list(self):  # pragma: no cover
        return list(self._tasks.values())


def _matrix_task(task_id="ms-rt-1"):
    return {"task_id": task_id, "kind": "matrix_script", "config": {"entry": {"topic": "三步搞定脚本", "target_platform": "抖音"}}}


def _build(repo, tmp_path, monkeypatch):
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover
        return None
    from gateway.app.deps import get_task_repository
    from gateway.app.routers import matrix_script_real_trial as route_module

    monkeypatch.setattr(route_module, "resolve_real_trial_output_dir", lambda task_id: str(tmp_path / task_id))
    monkeypatch.setattr(route_module, "build_real_trial_sink", lambda task_id: InMemoryArtifactSink())
    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(route_module.api_router)
    return TestClient(app)


def test_non_matrix_task_rejected(tmp_path, monkeypatch) -> None:
    client = _build(_StubRepo({"hf": {"task_id": "hf", "kind": "hot_follow"}}), tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    assert client.post("/api/matrix-script/hf/real-trial").status_code == 400


def test_unknown_task_404(tmp_path, monkeypatch) -> None:
    client = _build(_StubRepo({}), tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    assert client.post("/api/matrix-script/missing/real-trial").status_code == 404


def test_ffmpeg_missing_returns_503_no_fake(tmp_path, monkeypatch) -> None:
    from gateway.app.services.matrix_script import minimal_result_loop as loop
    monkeypatch.setattr(loop, "ffmpeg_available", lambda: False)
    repo = _StubRepo({"ms-rt-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    resp = client.post("/api/matrix-script/ms-rt-1/real-trial")
    assert resp.status_code == 503
    assert not os.path.exists(str(tmp_path / "ms-rt-1" / "final" / "final.mp4"))
    assert repo.mutations == []


@_skip_no_ffmpeg
def test_real_trial_returns_staged_candidate_payload(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"ms-rt-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    resp = client.post("/api/matrix-script/ms-rt-1/real-trial")
    assert resp.status_code == 200
    body = resp.json()
    assert body["storage_scope"] == "artifact_staged"
    assert body["delivery_candidate"] is True
    assert body["official_publish_ready"] is False
    assert body["generation_provider"] in ("none", "real_oneshot_attempted")
    assert str(body["final_video_artifact_ref"]).startswith("artifact://")
    blob = str(body).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url", "publish_url", "publish_status", "model_id", "credit", "http://", "https://"):
        assert token not in blob
    assert repo.mutations == []  # route does not mutate task/publish state


@_skip_no_ffmpeg
def test_real_trial_payload_has_browser_preview_url(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"ms-rt-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    body = client.post("/api/matrix-script/ms-rt-1/real-trial").json()
    # operator-accessible preview link present; dedicated gateway endpoint
    assert body.get("preview_url"), "preview_url missing from real-trial payload"
    assert str(body["preview_url"]) == "/api/matrix-script/ms-rt-1/real-trial/preview/final.mp4"
    for token in ("provider_url", "temporary_url", "publish_url", "publish_status", "download_url"):
        assert token not in str(body)
    # the preview endpoint streams the staged final.mp4 (browser-openable)
    pv = client.get(body["preview_url"])
    assert pv.status_code == 200
    assert pv.headers.get("content-type", "").startswith("video/mp4")
    assert len(pv.content) > 0


def test_real_trial_preview_404_when_not_generated(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"ms-rt-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("no TestClient")
    # no POST run → no staged final.mp4 → preview 404 (never a fake)
    pv = client.get("/api/matrix-script/ms-rt-1/real-trial/preview/final.mp4")
    assert pv.status_code in (404, 302)
