"""Matrix Script minimal result loop tests (Phase 3 PR-4R).

Two tiers:

- ffmpeg-independent logic (always runs): SRT building, manifest assembly,
  forbidden-token guard, ffmpeg-missing behavior, no-provider-import guard.
- full render (skipped when ffmpeg/ffprobe are absent): proves a real,
  ffprobe-readable ``final.mp4`` plus the full artifact tree is produced. A
  fake ``final.mp4`` is never created — the loop raises when ffmpeg is missing.
"""
from __future__ import annotations

import inspect
import json
import os

import pytest

from gateway.app.services.matrix_script import minimal_result_loop as loop_module
from gateway.app.services.matrix_script import simple_scene_renderer as renderer_module
from gateway.app.services.matrix_script.minimal_result_loop import (
    AUDIO_STRATEGY,
    GENERATION_PROVIDER,
    SCENE_STRATEGY,
    build_manifest_dict,
    build_srt,
    run_minimal_result_loop,
)
from gateway.app.services.matrix_script.shot_plan_builder import build_shot_plan
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    ffmpeg_available,
)

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(
    not _FFMPEG, reason="ffmpeg/ffprobe not installed; real-render tests skipped (no fake final.mp4)"
)


def _outline():
    return {
        "hook": "前 3 秒讲清楚价值",
        "body": ["展示痛点", "演示操作", "对比效果"],
        "cta": "评论区告诉我你的需求",
    }


def _plan(**kw):
    return build_shot_plan(_outline(), task_id=kw.get("task_id", "task-1"), target_duration_seconds=kw.get("dur", 8.0))


# ---------------------------------------------------------------------------
# SRT building (ffmpeg-independent)
# ---------------------------------------------------------------------------


def test_build_srt_has_one_cue_per_shot_and_is_deterministic() -> None:
    plan = _plan()
    srt_a = build_srt(plan)
    srt_b = build_srt(plan)
    assert srt_a == srt_b
    # one numeric index line per shot
    indices = [ln for ln in srt_a.splitlines() if ln.strip().isdigit()]
    assert len(indices) == len(plan.shots)
    assert "-->" in srt_a
    assert srt_a.splitlines()[1].startswith("00:00:00,000 -->")


def test_build_srt_timestamps_are_monotonic() -> None:
    plan = _plan()
    arrows = [ln for ln in build_srt(plan).splitlines() if "-->" in ln]
    starts = [ln.split(" --> ")[0] for ln in arrows]
    assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# manifest assembly (ffmpeg-independent)
# ---------------------------------------------------------------------------


def test_build_manifest_dict_shape_and_strategies() -> None:
    plan = _plan()
    manifest = build_manifest_dict(
        plan=plan,
        scene_clip_relpaths=[f"shots/scene_{i:03d}.mp4" for i in range(1, len(plan.shots) + 1)],
        audio_relpath="audio/narration.wav",
        subtitle_relpath="subtitles/subtitles.srt",
        final_video_relpath="final/final.mp4",
    )
    assert manifest["shot_count"] == len(plan.shots)
    assert manifest["final_video_path"] == "final/final.mp4"
    assert manifest["scene_strategy"] == SCENE_STRATEGY == "ffmpeg_color_card"
    assert manifest["audio_strategy"] == AUDIO_STRATEGY == "silent_fallback"
    assert manifest["generation_provider"] == GENERATION_PROVIDER == "none"
    assert len(manifest["scene_clip_paths"]) == len(plan.shots)


def test_manifest_has_no_provider_or_truth_leak_tokens() -> None:
    plan = _plan(task_id="t")
    manifest = build_manifest_dict(
        plan=plan,
        scene_clip_relpaths=["shots/scene_001.mp4"],
        audio_relpath="audio/narration.wav",
        subtitle_relpath="subtitles/subtitles.srt",
        final_video_relpath="final/final.mp4",
    )
    blob = json.dumps(manifest, ensure_ascii=False).lower()
    for token in (
        "akool",
        "provider_url",
        "temporary_url",
        "download_url",
        "provider_task_id",
        "vendor",
        "model_id",
        "credit",
        "http://",
        "https://",
    ):
        assert token not in blob, f"manifest leaks '{token}'"


def test_manifest_guard_rejects_injected_provider_token() -> None:
    from gateway.app.services.matrix_script.minimal_result_loop import _assert_no_forbidden_tokens

    with pytest.raises(ValueError):
        _assert_no_forbidden_tokens({"x": "powered by akool"})


# ---------------------------------------------------------------------------
# ffmpeg-missing behavior — never fake a final.mp4
# ---------------------------------------------------------------------------


def test_loop_raises_when_ffmpeg_missing_and_writes_no_final(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(loop_module, "ffmpeg_available", lambda: False)
    out_dir = str(tmp_path / "result")
    with pytest.raises(FFmpegUnavailableError):
        run_minimal_result_loop(_outline(), out_dir, task_id="t")
    # no fake final.mp4 may exist
    assert not os.path.exists(os.path.join(out_dir, "final", "final.mp4"))


def test_renderer_calls_raise_when_ffmpeg_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(renderer_module, "ffmpeg_path", lambda: None)
    monkeypatch.setattr(renderer_module, "ffprobe_path", lambda: None)
    with pytest.raises(FFmpegUnavailableError):
        renderer_module.render_color_scene_clip(
            str(tmp_path / "x.mp4"), duration_seconds=1.0, width=64, height=64, color="navy"
        )


# ---------------------------------------------------------------------------
# import-boundary guard
# ---------------------------------------------------------------------------


def test_modules_have_no_akool_provider_or_storage_dependency() -> None:
    for mod in (loop_module, renderer_module):
        src = inspect.getsource(mod)
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
        ):
            assert token not in src, f"module leaks into {token}"


# ---------------------------------------------------------------------------
# full real-render path (skipped without ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_full_loop_produces_real_playable_final_mp4(tmp_path) -> None:
    out_dir = str(tmp_path / "matrix_script_result")
    result = run_minimal_result_loop(_outline(), out_dir, task_id="task-1", target_duration_seconds=8.0)

    # directory tree
    assert os.path.isdir(os.path.join(out_dir, "shots"))
    assert os.path.isdir(os.path.join(out_dir, "audio"))
    assert os.path.isdir(os.path.join(out_dir, "subtitles"))
    assert os.path.isdir(os.path.join(out_dir, "final"))

    # scene clips exist and are non-empty
    assert len(result.scene_clip_paths) >= 4
    for clip in result.scene_clip_paths:
        assert os.path.exists(clip) and os.path.getsize(clip) > 0

    # audio + subtitles
    assert os.path.exists(result.audio_path) and os.path.getsize(result.audio_path) > 0
    assert os.path.exists(result.subtitle_path) and os.path.getsize(result.subtitle_path) > 0

    # final.mp4 exists, non-empty, ffprobe-readable with positive duration
    assert os.path.exists(result.final_video_path)
    assert os.path.getsize(result.final_video_path) > 0
    duration = renderer_module.probe_duration_seconds(result.final_video_path)
    assert duration > 0

    # manifest.json
    assert os.path.exists(result.manifest_path)
    with open(result.manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["shot_count"] == len(result.scene_clip_paths)
    assert manifest["final_video_path"] == os.path.relpath(result.final_video_path, out_dir)
    assert manifest["generation_provider"] == "none"
    blob = json.dumps(manifest, ensure_ascii=False).lower()
    assert "akool" not in blob and "http://" not in blob and "https://" not in blob


@_skip_no_ffmpeg
def test_full_loop_is_deterministic_in_structure(tmp_path) -> None:
    out_a = str(tmp_path / "a")
    out_b = str(tmp_path / "b")
    ra = run_minimal_result_loop(_outline(), out_a, task_id="t", target_duration_seconds=8.0)
    rb = run_minimal_result_loop(_outline(), out_b, task_id="t", target_duration_seconds=8.0)
    assert ra.manifest["manifest_id"] == rb.manifest["manifest_id"]
    assert ra.manifest["scene_clip_paths"] == rb.manifest["scene_clip_paths"]
    assert ra.manifest["shot_count"] == rb.manifest["shot_count"]
