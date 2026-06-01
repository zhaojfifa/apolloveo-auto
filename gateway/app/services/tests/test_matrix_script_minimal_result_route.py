"""HTTP-boundary tests for the Matrix Script minimal-result route (PR-12R).

Builds a minimal FastAPI app with only this router (mirrors the closure-API
test harness) so the full app/main need not import. The real-render path runs
only when ffmpeg is present; ffmpeg-missing → HTTP 503 with no fake final.mp4.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import pytest

from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG, reason="ffmpeg/ffprobe not installed; real-render route tests skipped (no fake final.mp4)"
)


class _StubRepo:
    """Minimal ITaskRepository-shaped stub that records mutation attempts."""

    def __init__(self, tasks: Dict[str, Dict[str, Any]]):
        self._tasks = tasks
        self.mutations: list[str] = []

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def create(self, task):  # pragma: no cover
        self.mutations.append("create")
        raise NotImplementedError

    def update(self, task_id, patch):  # pragma: no cover
        self.mutations.append("update")
        raise NotImplementedError

    def list(self):  # pragma: no cover
        return list(self._tasks.values())


def _matrix_task(task_id: str = "ms-route-1") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "kind": "matrix_script",
        "config": {
            "entry": {
                "topic": "三步搞定短视频脚本",
                "operator_notes": "展示痛点\n演示操作\n对比效果",
                "target_platform": "抖音",
            }
        },
    }


def _build(repo: _StubRepo, tmp_path, monkeypatch):
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover
        return None
    from gateway.app.deps import get_task_repository
    from gateway.app.routers import matrix_script_minimal_result as route_module

    # isolate output to a temp dir — never the real workspace
    monkeypatch.setattr(
        route_module,
        "resolve_minimal_result_output_dir",
        lambda task_id: str(tmp_path / task_id),
    )
    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(route_module.api_router)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# rejection + ffmpeg-missing (always run)
# ---------------------------------------------------------------------------


def test_non_matrix_script_task_rejected(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"hf-1": {"task_id": "hf-1", "kind": "hot_follow"}})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("FastAPI TestClient not importable")
    resp = client.post("/api/matrix-script/hf-1/minimal-result")
    assert resp.status_code == 400


def test_unknown_task_returns_404(tmp_path, monkeypatch) -> None:
    client = _build(_StubRepo({}), tmp_path, monkeypatch)
    if client is None:
        pytest.skip("FastAPI TestClient not importable")
    resp = client.post("/api/matrix-script/missing/minimal-result")
    assert resp.status_code == 404


def test_ffmpeg_missing_returns_503_and_no_fake_final(tmp_path, monkeypatch) -> None:
    from gateway.app.services.matrix_script import minimal_result_service as svc
    monkeypatch.setattr(svc, "ffmpeg_available", lambda: False)
    repo = _StubRepo({"ms-route-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("FastAPI TestClient not importable")
    resp = client.post("/api/matrix-script/ms-route-1/minimal-result")
    assert resp.status_code == 503
    assert not os.path.exists(str(tmp_path / "ms-route-1" / "final" / "final.mp4"))
    # route read the task only — no repository mutation
    assert repo.mutations == []


# ---------------------------------------------------------------------------
# full real path (skipped without ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_route_returns_surface_payload_for_matrix_task(tmp_path, monkeypatch) -> None:
    repo = _StubRepo({"ms-route-1": _matrix_task()})
    client = _build(repo, tmp_path, monkeypatch)
    if client is None:
        pytest.skip("FastAPI TestClient not importable")
    resp = client.post("/api/matrix-script/ms-route-1/minimal-result")
    assert resp.status_code == 200
    body = resp.json()

    assert body["has_result"] is True
    assert body["line_id"] == "matrix_script"
    assert body["storage_scope"] == "local_workspace"
    assert body["official_publish_ready"] is False
    assert body["result_status"] == "generated"
    assert body["final_video_path"].endswith("final.mp4")
    assert "尚未进入正式交付存储" in body["operator_note"]

    # leakage discipline
    blob = (str(body)).lower()
    for token in (
        "akool", "provider_url", "temporary_url", "download_url", "vendor",
        "model_id", "credit", "provider_task_id", "artifact_key", "r2_key",
        "publish_url", "publish_status", "http://", "https://",
    ):
        assert token not in blob, f"route payload leaks '{token}'"
    for forbidden_key in ("artifact_key", "r2_key", "download_url", "publish_url", "publish_status", "final_video_key"):
        assert forbidden_key not in body

    # real artifact exists on disk
    assert os.path.exists(body["final_video_path"]) and os.path.getsize(body["final_video_path"]) > 0
    # no repository mutation
    assert repo.mutations == []
