"""Matrix Script minimal result orchestrator tests (Phase 3 PR-10R).

Logic-tier tests always run; the real-render assertions skip without ffmpeg
(a fake final.mp4 is never fabricated).
"""
from __future__ import annotations

import inspect
import json
import os

import pytest

from gateway.app.services.matrix_script import (
    minimal_result_orchestrator as orchestrator_module,
)
from gateway.app.services.matrix_script.minimal_result_orchestrator import (
    MinimalResultOrchestratorError,
    run_matrix_script_task_minimal_result,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    MatrixScriptMinimalResultSurfaceView,
    minimal_result_surface_view_to_dict,
)
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    ffmpeg_available,
    probe_duration_seconds,
)

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG, reason="ffmpeg/ffprobe not installed; real-render tests skipped (no fake final.mp4)"
)


def _task():
    return {
        "task_id": "ms-orch-1",
        "kind": "matrix_script",
        "config": {
            "entry": {
                "topic": "三步搞定短视频脚本",
                "operator_notes": "展示痛点\n演示操作\n对比效果",
                "audience_hint": "新手创作者",
                "target_platform": "抖音",
            }
        },
    }


# ---------------------------------------------------------------------------
# input validation + ffmpeg-missing behavior (always run)
# ---------------------------------------------------------------------------


def test_rejects_non_mapping_task(tmp_path) -> None:
    with pytest.raises(MinimalResultOrchestratorError):
        run_matrix_script_task_minimal_result("nope", str(tmp_path))  # type: ignore[arg-type]


def test_ffmpeg_missing_raises_and_writes_no_final(tmp_path, monkeypatch) -> None:
    # patch the service-layer ffmpeg gate used inside run_matrix_script_minimal_result
    from gateway.app.services.matrix_script import minimal_result_service as svc
    monkeypatch.setattr(svc, "ffmpeg_available", lambda: False)
    out_dir = str(tmp_path / "orch")
    with pytest.raises(FFmpegUnavailableError):
        run_matrix_script_task_minimal_result(_task(), out_dir)
    assert not os.path.exists(os.path.join(out_dir, "final", "final.mp4"))


# ---------------------------------------------------------------------------
# import-boundary guard (always run)
# ---------------------------------------------------------------------------


def test_module_has_no_ui_router_or_forbidden_imports() -> None:
    src = inspect.getsource(orchestrator_module)
    assert "providers.akool" not in src
    assert "workers.adapters" not in src
    assert "import httpx" not in src
    for token in (
        "import artifact_storage",
        "artifact_storage import",
        "upload_artifact(",
        "get_download_url(",
        "gateway.app.routers",
        "gateway.app.templates",
        "gateway.app.services.packet",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"orchestrator leaks into {token}"


# ---------------------------------------------------------------------------
# full chain (skipped without ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_task_produces_surface_view_with_real_final_mp4(tmp_path) -> None:
    out_dir = str(tmp_path / "matrix_script_result")
    view = run_matrix_script_task_minimal_result(_task(), out_dir, target_duration_seconds=8.0)

    assert isinstance(view, MatrixScriptMinimalResultSurfaceView)
    assert view.has_result is True
    assert view.official_publish_ready is False
    assert view.storage_scope == "local_workspace"
    assert view.operator_note and "尚未进入正式交付存储" in view.operator_note
    assert view.line_id == "matrix_script"

    # real final.mp4 exists + ffprobe-readable
    assert os.path.exists(view.final_video_path) and os.path.getsize(view.final_video_path) > 0
    assert probe_duration_seconds(view.final_video_path) > 0

    # manifest produced by the underlying loop
    assert os.path.exists(os.path.join(out_dir, "manifest.json"))


@_skip_no_ffmpeg
def test_surface_view_has_no_provider_or_truth_leak(tmp_path) -> None:
    view = run_matrix_script_task_minimal_result(_task(), str(tmp_path / "r"), target_duration_seconds=8.0)
    blob = json.dumps(minimal_result_surface_view_to_dict(view), ensure_ascii=False).lower()
    for token in (
        "akool", "provider_url", "temporary_url", "download_url", "vendor",
        "model_id", "credit", "provider_task_id", "artifact_key", "r2_key",
        "publish_url", "publish_status", "http://", "https://",
    ):
        assert token not in blob, f"surface leaks '{token}'"


@_skip_no_ffmpeg
def test_chain_is_deterministic_in_structure(tmp_path) -> None:
    a = run_matrix_script_task_minimal_result(_task(), str(tmp_path / "a"), target_duration_seconds=8.0)
    b = run_matrix_script_task_minimal_result(_task(), str(tmp_path / "b"), target_duration_seconds=8.0)
    assert a.shot_count == b.shot_count
    assert a.has_result == b.has_result is True
    assert a.duration_seconds == b.duration_seconds
