"""Matrix Script minimal result internal command tests (Phase 3 PR-11R)."""
from __future__ import annotations

import inspect
import json
import os

import pytest

from gateway.app.services.matrix_script import minimal_result_command as command_module
from gateway.app.services.matrix_script.minimal_result_command import (
    MatrixScriptMinimalResultCommand,
    MinimalResultCommandError,
    run_minimal_result_command,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    MatrixScriptMinimalResultSurfaceView,
    minimal_result_surface_view_to_dict,
)
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    ffmpeg_available,
)

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG,
    reason="ffmpeg/ffprobe not installed; real-render tests skipped (no fake final.mp4)",
)


def _task(**overrides):
    base = {
        "task_id": "ms-cmd-1",
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
    base.update(overrides)
    return base


def _surface(path: str = "/tmp/ms/final/final.mp4") -> MatrixScriptMinimalResultSurfaceView:
    return MatrixScriptMinimalResultSurfaceView(
        task_id="ms-cmd-1",
        line_id="matrix_script",
        has_result=True,
        result_status="generated",
        final_video_label="本地最小成片",
        final_video_path=path,
        manifest_path="/tmp/ms/manifest.json",
        duration_seconds=8.0,
        shot_count=5,
        storage_scope="local_workspace",
        official_publish_ready=False,
        operator_note="已生成本地最小成片，尚未进入正式交付存储",
    )


def test_valid_matrix_script_task_triggers_command_and_returns_surface_view(
    tmp_path, monkeypatch
) -> None:
    calls = []

    def fake_orchestrator(task, output_dir, *, aspect_ratio, target_duration_seconds):
        calls.append((task, os.fspath(output_dir), aspect_ratio, target_duration_seconds))
        return _surface(str(tmp_path / "final" / "final.mp4"))

    monkeypatch.setattr(
        command_module, "run_matrix_script_task_minimal_result", fake_orchestrator
    )
    view = run_minimal_result_command(
        _task(),
        tmp_path / "out",
        requested_by="internal-test",
        target_duration_seconds=8.0,
    )
    assert isinstance(view, MatrixScriptMinimalResultSurfaceView)
    assert view.has_result is True
    assert view.official_publish_ready is False
    assert calls == [(_task(), os.fspath(tmp_path / "out"), "9:16", 8.0)]


@_skip_no_ffmpeg
def test_final_mp4_exists_when_ffmpeg_is_available(tmp_path) -> None:
    view = run_minimal_result_command(
        _task(), tmp_path / "real", target_duration_seconds=8.0
    )
    assert view.has_result is True
    assert view.official_publish_ready is False
    assert os.path.exists(view.final_video_path)
    assert os.path.getsize(view.final_video_path) > 0


def test_class_wrapper_returns_surface_view(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        command_module,
        "run_matrix_script_task_minimal_result",
        lambda task, output_dir, *, aspect_ratio, target_duration_seconds: _surface(
            str(tmp_path / "v.mp4")
        ),
    )
    view = MatrixScriptMinimalResultCommand().run(_task(), tmp_path / "out")
    assert isinstance(view, MatrixScriptMinimalResultSurfaceView)
    assert view.has_result is True


@pytest.mark.parametrize(
    "task",
    [
        {"kind": "hot_follow", "config": {}},
        {"line_id": "digital_anchor", "config": {}},
        {"config": {"entry": {"line_id": "hot_follow"}}},
        {},
    ],
)
def test_non_matrix_script_task_is_rejected(task, tmp_path) -> None:
    with pytest.raises(MinimalResultCommandError):
        run_minimal_result_command(task, tmp_path / "out")


def test_missing_output_dir_fails_clearly() -> None:
    with pytest.raises(MinimalResultCommandError, match="output_dir"):
        run_minimal_result_command(_task(), None)
    with pytest.raises(MinimalResultCommandError, match="output_dir"):
        run_minimal_result_command(_task(), "")


def test_invalid_requested_by_fails_clearly(tmp_path) -> None:
    with pytest.raises(MinimalResultCommandError, match="requested_by"):
        run_minimal_result_command(_task(), tmp_path / "out", requested_by="")


def test_no_route_template_artifact_storage_or_forbidden_imports() -> None:
    src = inspect.getsource(command_module)
    for token in (
        "gateway.app.routers",
        "gateway.app.templates",
        "import artifact_storage",
        "artifact_storage import",
        "upload_artifact(",
        "get_download_url(",
        "gateway.app.services.packet",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
        "providers.akool",
        "workers.adapters",
        "import httpx",
        "import requests",
        "os.environ",
        "os.getenv",
    ):
        assert token not in src, f"command module leaks into {token}"


def test_no_akool_provider_vendor_model_credit_leakage() -> None:
    blob = json.dumps(minimal_result_surface_view_to_dict(_surface()), ensure_ascii=False).lower()
    for token in (
        "akool",
        "provider_url",
        "temporary_url",
        "download_url",
        "vendor",
        "model_id",
        "credit",
        "provider_task_id",
        "artifact_key",
        "r2_key",
        "publish_url",
        "publish_status",
        "http://",
        "https://",
    ):
        assert token not in blob, f"surface leaks '{token}'"


def test_ffmpeg_missing_never_fabricates_final_mp4(tmp_path, monkeypatch) -> None:
    def fake_orchestrator(task, output_dir, *, aspect_ratio, target_duration_seconds):
        raise FFmpegUnavailableError("ffmpeg unavailable")

    monkeypatch.setattr(
        command_module, "run_matrix_script_task_minimal_result", fake_orchestrator
    )
    out_dir = tmp_path / "missing"
    with pytest.raises(FFmpegUnavailableError):
        run_minimal_result_command(_task(), out_dir)
    assert not os.path.exists(out_dir / "final" / "final.mp4")
