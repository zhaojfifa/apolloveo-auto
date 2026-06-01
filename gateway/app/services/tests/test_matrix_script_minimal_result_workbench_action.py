"""Matrix Script Workbench minimal-result action MVP tests (Phase 3 PR-13R).

Static template assertions over the new Workbench trigger block + an
ffmpeg-gated end-to-end through the PR-12R route proving the rendered payload
is local-workspace, not-publish-ready, and leak-free.
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


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(workbench_source: str) -> str:
    start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    end = workbench_source.find(
        "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}",
        start,
    )
    assert start != -1 and end != -1
    return workbench_source[start:end]


@pytest.fixture(scope="module")
def action_block(matrix_branch: str) -> str:
    anchor = matrix_branch.find('data-role="matrix-script-minimal-result-action"')
    assert anchor != -1, "minimal-result action block missing from matrix_script branch"
    gate = matrix_branch.rfind("{% if ms_main_video_result.is_matrix_script %}", 0, anchor)
    end = matrix_branch.find("{% endif %}", anchor)
    # extend to the endif that closes this block (after the <script>)
    end = matrix_branch.find("{% endif %}", matrix_branch.find("</script>", anchor))
    assert gate != -1 and end != -1
    return matrix_branch[gate : end + len("{% endif %}")]


# ---------------------------------------------------------------------------
# (1)(2)(3) action present, posts to the route, renders the result label
# ---------------------------------------------------------------------------


def test_workbench_has_generate_button(action_block: str) -> None:
    assert "生成本地最小成片" in action_block
    assert 'data-role="ms-minimal-result-trigger"' in action_block


def test_action_posts_to_minimal_result_route(action_block: str) -> None:
    assert 'data-endpoint="/api/matrix-script/' in action_block
    assert "/minimal-result" in action_block
    assert "fetch(" in action_block
    assert "method: 'POST'" in action_block


def test_action_renders_local_result_label(action_block: str) -> None:
    assert "本地最小成片" in action_block
    assert 'data-role="ms-minimal-result-action-output"' in action_block
    assert 'data-role="ms-minimal-result-action-status"' in action_block


# ---------------------------------------------------------------------------
# (4)(5) result surfaces storage_scope + official_publish_ready
# ---------------------------------------------------------------------------


def test_action_surfaces_storage_scope_and_publish_ready(action_block: str) -> None:
    assert "d.storage_scope" in action_block
    assert "存储范围" in action_block
    assert "d.official_publish_ready" in action_block
    assert "正式交付就绪" in action_block


# ---------------------------------------------------------------------------
# (6)(7)(8) no leakage in the action block
# ---------------------------------------------------------------------------


def test_action_block_is_leak_free(action_block: str) -> None:
    lowered = action_block.lower()
    for token in (
        "akool", "provider", "vendor", "model_id", "credit",
        "publish_url", "publish_status", "artifact_key", "r2_key", "download_url",
        ".mp4", "http://", "https://",
    ):
        assert token not in lowered, f"action block leaks '{token}'"
    for tag in ("<video", "<iframe", "<source "):
        assert tag not in action_block, f"action block contains forbidden tag {tag}"


# ---------------------------------------------------------------------------
# (10) gated to matrix_script (Hot Follow / Digital Anchor unaffected)
# ---------------------------------------------------------------------------


def test_action_block_is_gated_to_matrix_script(workbench_source: str) -> None:
    ms_start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    da_start = workbench_source.find('ops_workbench_panel.panel_kind == "digital_anchor"')
    action = workbench_source.find('data-role="matrix-script-minimal-result-action"')
    assert ms_start != -1 and action != -1
    # action lives inside the matrix_script branch, before the digital_anchor branch
    assert ms_start < action < da_start


def test_action_block_gated_by_is_matrix_script(action_block: str) -> None:
    assert action_block.startswith("{% if ms_main_video_result.is_matrix_script %}")


# ---------------------------------------------------------------------------
# (9) section order A–J preserved
# ---------------------------------------------------------------------------


def test_primary_section_order_preserved(matrix_branch: str) -> None:
    anchors = [
        "matrix-script-main-video-result",
        "matrix-script-section-script-understanding",
        "matrix-script-section-generation-plan",
        "matrix-script-section-video-versions",
        "op-console-ms-technical-diagnostics-fold",
    ]
    positions = [matrix_branch.find(f'data-role="{a}"') for a in anchors]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# end-to-end via the route (skipped without ffmpeg)
# ---------------------------------------------------------------------------


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
def test_action_endpoint_returns_local_workspace_payload(tmp_path, monkeypatch) -> None:
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
    assert repo.mutations == []  # route does not mutate task/publish state
    assert os.path.exists(body["final_video_path"])
