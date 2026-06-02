"""Matrix Script cleanup tests for the retired minimal-result Workbench action.

The minimal-result service/route remains available as a retained result-chain
capability, but the standalone Workbench card and button are no longer part of
the operator-primary UI. Operators use the A 主视频结果 PR-A action and I 交付入口.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG, reason="ffmpeg/ffprobe not installed; real-render route test skipped (no fake final.mp4)"
)


def test_standalone_minimal_result_action_removed_from_workbench() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    assert 'data-role="matrix-script-minimal-result-action"' not in src
    assert 'data-role="ms-minimal-result-trigger"' not in src
    assert "生成本地最小成片" not in src
    assert "/minimal-result" not in src[src.find('ops_workbench_panel.panel_kind == "matrix_script"'):]


def test_primary_workbench_action_is_pr_a_operator_preview() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    assert 'data-role="ms-acc-generate"' in src
    assert "/tomato-real-result" in src
    assert 'data-role="ms-main-video-result-acceptance"' in src
    assert 'data-role="ms-section-delivery-entry-acceptance"' in src


def test_cleanup_keeps_no_provider_or_publish_leakage_in_primary_branch() -> None:
    src = _WORKBENCH.read_text(encoding="utf-8")
    start = src.index('ops_workbench_panel.panel_kind == "matrix_script"')
    end = src.index('data-role="op-console-ms-technical-diagnostics-fold"', start)
    primary = src[start:end].lower()
    for token in (
        "provider_url", "temporary_url", "download_url", "publish_url",
        "publish_status", "artifact_key", "r2_key", "model_id", "credit",
    ):
        assert token not in primary


class _StubRepo:
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


@_skip_no_ffmpeg
def test_retained_minimal_result_route_still_returns_local_workspace_payload(tmp_path, monkeypatch) -> None:
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover
        pytest.skip("FastAPI TestClient not importable")
    from gateway.app.deps import get_task_repository
    from gateway.app.routers import matrix_script_minimal_result as route_module

    monkeypatch.setattr(
        route_module, "resolve_minimal_result_output_dir", lambda task_id: str(tmp_path / task_id)
    )
    task = {"task_id": "ms-act-1", "kind": "matrix_script", "config": {"entry": {"topic": "三步搞定脚本", "target_platform": "抖音"}}}
    repo = _StubRepo({"ms-act-1": task})
    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(route_module.api_router)
    client = TestClient(app)

    body = client.post("/api/matrix-script/ms-act-1/minimal-result").json()
    assert body["has_result"] is True
    assert body["storage_scope"] == "local_workspace"
    assert body["official_publish_ready"] is False
    blob = str(body).lower()
    for token in ("akool", "provider_url", "publish_url", "publish_status", "artifact_key", "r2_key", "download_url", "http://", "https://"):
        assert token not in blob
    assert repo.mutations == []
    assert os.path.exists(body["final_video_path"])
