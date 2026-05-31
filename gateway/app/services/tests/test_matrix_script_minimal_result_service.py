"""Matrix Script minimal result service bridge tests (Phase 3 PR-5R).

Two tiers:
- ffmpeg-independent: request validation, outline derivation from a task-like
  fixture, ffmpeg-missing behavior (no fake final.mp4), import-boundary guard.
- full render (skipped without ffmpeg): proves the service produces a real,
  ffprobe-readable final.mp4 + manifest from a task fixture and returns a
  correct summary.
"""
from __future__ import annotations

import inspect
import json
import os

import pytest

from gateway.app.services.matrix_script import minimal_result_service as service_module
from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultRequest,
    MatrixScriptMinimalResultService,
    MatrixScriptMinimalResultSummary,
    MinimalResultServiceError,
    derive_outline_from_task,
    run_matrix_script_minimal_result,
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


def _task_fixture():
    # task-like fixture mirroring the Matrix Script create_entry shape
    return {
        "task_id": "ms-demo-1",
        "kind": "matrix_script",
        "config": {
            "entry": {
                "topic": "三步搞定短视频脚本",
                "operator_notes": "展示痛点\n演示操作\n对比效果",
                "audience_hint": "新手创作者",
                "tone_hint": "干货直给",
                "target_platform": "抖音",
                "target_language": "mm",
            }
        },
    }


def _outline():
    return {"hook": "前 3 秒讲清楚价值", "body": ["展示痛点", "演示操作"], "cta": "关注了解更多"}


# ---------------------------------------------------------------------------
# request validation (ffmpeg-independent)
# ---------------------------------------------------------------------------


def test_request_requires_outline_or_task() -> None:
    with pytest.raises(MinimalResultServiceError):
        MatrixScriptMinimalResultRequest(output_dir="/tmp/x")


def test_request_rejects_empty_output_dir() -> None:
    with pytest.raises(MinimalResultServiceError):
        MatrixScriptMinimalResultRequest(output_dir="", outline=_outline())


# ---------------------------------------------------------------------------
# outline derivation from a task-like fixture (ffmpeg-independent)
# ---------------------------------------------------------------------------


def test_derive_outline_from_task_is_deterministic_and_structured() -> None:
    a = derive_outline_from_task(_task_fixture())
    b = derive_outline_from_task(_task_fixture())
    assert a == b
    assert a["hook"] == "三步搞定短视频脚本"
    assert "展示痛点" in a["body"]
    assert "抖音" in a["cta"]


def test_derive_outline_handles_sparse_task() -> None:
    outline = derive_outline_from_task({"config": {"entry": {}}})
    assert outline["hook"]
    assert isinstance(outline["body"], list) and outline["body"]
    assert outline["cta"]


def test_derive_outline_rejects_non_mapping() -> None:
    with pytest.raises(MinimalResultServiceError):
        derive_outline_from_task("not a mapping")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ffmpeg-missing behavior — never fake a final.mp4
# ---------------------------------------------------------------------------


def test_service_raises_when_ffmpeg_missing_and_writes_no_final(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(service_module, "ffmpeg_available", lambda: False)
    out_dir = str(tmp_path / "svc")
    req = MatrixScriptMinimalResultRequest(output_dir=out_dir, task=_task_fixture())
    with pytest.raises(FFmpegUnavailableError):
        run_matrix_script_minimal_result(req)
    assert not os.path.exists(os.path.join(out_dir, "final", "final.mp4"))


# ---------------------------------------------------------------------------
# import-boundary guard
# ---------------------------------------------------------------------------


def test_service_module_has_no_akool_provider_or_storage_dependency() -> None:
    src = inspect.getsource(service_module)
    assert "providers.akool" not in src
    assert "workers.adapters" not in src
    assert "import httpx" not in src
    assert "from swiftcraft" not in src
    assert "import swiftcraft" not in src
    for token in (
        "import artifact_storage",
        "artifact_storage import",
        "upload_artifact(",
        "get_download_url(",
        "gateway.app.routers",
        "gateway.app.services.packet",
        "gateway.app.services.hot_follow",
        "gateway.app.services.digital_anchor",
    ):
        assert token not in src, f"service leaks into {token}"


# ---------------------------------------------------------------------------
# full real-render path (skipped without ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_service_produces_real_final_mp4_from_task_fixture(tmp_path) -> None:
    out_dir = str(tmp_path / "matrix_script_result")
    req = MatrixScriptMinimalResultRequest(
        output_dir=out_dir, task=_task_fixture(), target_duration_seconds=8.0
    )
    summary = MatrixScriptMinimalResultService().run(req)

    assert isinstance(summary, MatrixScriptMinimalResultSummary)
    # final.mp4 exists, non-empty, ffprobe-readable
    assert os.path.exists(summary.final_video_path) and os.path.getsize(summary.final_video_path) > 0
    assert probe_duration_seconds(summary.final_video_path) > 0
    assert summary.duration_seconds > 0

    # manifest exists and references final video path
    assert os.path.exists(summary.manifest_path)
    with open(summary.manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["final_video_path"] == os.path.relpath(summary.final_video_path, out_dir)

    # subtitles + audio exist
    assert os.path.exists(summary.subtitles_path) and os.path.getsize(summary.subtitles_path) > 0
    assert os.path.exists(summary.audio_path) and os.path.getsize(summary.audio_path) > 0

    # summary fields
    assert summary.task_id == "ms-demo-1"
    assert summary.shot_count >= 4
    assert summary.generation_provider == "none"
    assert summary.scene_strategy == "ffmpeg_color_card"
    assert summary.audio_strategy == "silent_fallback"


@_skip_no_ffmpeg
def test_service_no_provider_leakage_in_summary_and_manifest(tmp_path) -> None:
    out_dir = str(tmp_path / "r")
    summary = run_matrix_script_minimal_result(
        MatrixScriptMinimalResultRequest(output_dir=out_dir, outline=_outline(), target_duration_seconds=8.0)
    )
    blob = repr(summary).lower()
    with open(summary.manifest_path, encoding="utf-8") as fh:
        blob += json.dumps(json.load(fh), ensure_ascii=False).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url", "vendor", "model_id", "credit", "http://", "https://"):
        assert token not in blob, f"leaks '{token}'"


@_skip_no_ffmpeg
def test_service_is_deterministic_for_same_task(tmp_path) -> None:
    s_a = run_matrix_script_minimal_result(
        MatrixScriptMinimalResultRequest(output_dir=str(tmp_path / "a"), task=_task_fixture(), target_duration_seconds=8.0)
    )
    s_b = run_matrix_script_minimal_result(
        MatrixScriptMinimalResultRequest(output_dir=str(tmp_path / "b"), task=_task_fixture(), target_duration_seconds=8.0)
    )
    assert s_a.shot_count == s_b.shot_count
    assert s_a.duration_seconds == s_b.duration_seconds
    assert s_a.generation_provider == s_b.generation_provider == "none"
