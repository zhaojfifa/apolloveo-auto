from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

from gateway.app.services.compose_service import (
    ComposePlan,
    ComposeInputProfile,
    ComposeResult,
    CompositionService,
    HotFollowComposeRequestContract,
    _ComposeInputs,
)
from gateway.app.services.worker_gateway import WorkerExecutionMode, WorkerResult


def test_prepare_hot_follow_compose_task_returns_mutations_without_repo_writes():
    task = {
        "task_id": "hf-compose-1",
        "kind": "hot_follow",
        "content_lang": "mm",
        "target_lang": "mm",
        "config": {},
        "compose_plan": {"overlay_subtitles": True},
        "scene_outputs": [],
    }
    svc = CompositionService(storage=object(), settings=object())

    current, request_updates, compose_plan = svc.prepare_hot_follow_compose_task(
        task,
        HotFollowComposeRequestContract(
            bgm_mix=0.5,
            overlay_subtitles=False,
            freeze_tail_enabled=True,
            force=False,
        ),
    )

    assert isinstance(compose_plan, ComposePlan)
    assert request_updates["config"]["bgm"]["mix_ratio"] == 0.5
    assert request_updates["compose_plan"]["freeze_tail_enabled"] is True
    assert request_updates["compose_plan"]["overlay_subtitles"] is False
    assert compose_plan.freeze_tail_enabled is True
    assert compose_plan.overlay_subtitles is False
    assert compose_plan.compose_policy == "freeze_tail"
    assert current["config"]["bgm"]["mix_ratio"] == 0.5
    assert current["compose_plan"]["freeze_tail_enabled"] is True


def test_compose_lock_active_detects_future_lock():
    svc = CompositionService(storage=object(), settings=object())
    task = {
        "task_id": "hf-compose-locked",
        "compose_lock_until": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
    }

    assert svc.compose_lock_active(task) is True
    assert svc.build_compose_lock_body("hf-compose-locked")["error"] == "compose_in_progress"


def test_recover_stale_running_compose_marks_terminal_when_worker_is_gone():
    stale_started_at = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

    updates = CompositionService.recover_stale_running_compose(
        "hf-stale-compose",
        {
            "task_id": "hf-stale-compose",
            "compose_status": "running",
            "compose_last_status": "running",
            "compose_last_started_at": stale_started_at,
            "final_video_key": "deliver/tasks/hf-stale-compose/final.mp4",
        },
        lock_active=False,
        object_exists_fn=lambda _key: False,
        stale_after_sec=0,
    )

    assert updates is not None
    assert updates["compose_status"] == "failed"
    assert updates["compose_last_status"] == "failed"
    assert updates["compose_error_reason"] == "compose_stale_running_recovered"
    assert updates["compose_lock_until"] is None


def test_large_local_compose_input_derives_safe_video_before_merge(tmp_path, monkeypatch):
    svc = CompositionService(storage=object(), settings=object())
    source = tmp_path / "video_input.mp4"
    source.write_bytes(b"x" * 128)
    derived = tmp_path / "video_input_safe.mp4"
    commands = []

    def _fake_run(cmd, task_id, purpose, *, timeout=None):
        commands.append((cmd, purpose, timeout))
        if purpose == "derive_compose_input":
            derived.write_bytes(b"safe-video")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(svc, "_run_ffmpeg", _fake_run)
    monkeypatch.setattr("gateway.app.services.compose_service.assert_local_video_ok", lambda path: (Path(path).stat().st_size, 8.0))
    monkeypatch.setattr(
        svc,
        "_probe_video_profile",
        lambda _task_id, path, size, duration: ComposeInputProfile(
            size_bytes=size,
            duration_sec=duration,
            width=1080,
            height=1920,
            bit_rate=1_000_000,
            pix_fmt="yuv420p",
        ),
    )
    monkeypatch.setenv("HF_COMPOSE_DERIVE_MIN_BYTES", "64")
    monkeypatch.setenv("HF_COMPOSE_DERIVE_MIN_BITRATE", "1")
    monkeypatch.setenv("HF_COMPOSE_DERIVE_MIN_PIXELS", "1")

    safe_path, safe_profile, warning = svc._derive_safe_compose_input(
        "hf-large-input",
        {"task_id": "hf-large-input", "pipeline_config": {"ingest_mode": "local"}},
        _ComposeInputs(
            video_key="video",
            audio_key="audio",
            subtitle_only_compose=False,
            voice_state={"audio_ready": True},
            bgm_key=None,
            bgm_mix=0.3,
            source_audio_policy="mute",
            source_audio_available=False,
            overlay_subtitles=True,
            strip_subtitle_streams=True,
            cleanup_mode="none",
            target_lang="mm",
            freeze_tail_enabled=False,
            freeze_tail_cap_sec=8.0,
            compose_policy="match_video",
            ffmpeg="ffmpeg",
        ),
        source,
        tmp_path,
        ComposeInputProfile(size_bytes=128, duration_sec=8.0, width=4096, height=2160, bit_rate=30_000_000),
    )

    assert safe_path == derived
    assert safe_profile.size_bytes == len(b"safe-video")
    assert warning == "large local input derived for stable compose"
    assert commands[0][1] == "derive_compose_input"
    assert "-map" in commands[0][0]
    assert "force_divisible_by=2" in commands[0][0][commands[0][0].index("-vf") + 1]


def test_workdir_space_guard_blocks_before_heavy_compose(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())

    monkeypatch.setattr(
        "gateway.app.services.compose_service.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": 10})(),
    )

    with pytest.raises(HTTPException) as exc:
        svc._guard_workdir_space(
            "hf-disk-guard",
            tmp_path,
            ComposeInputProfile(size_bytes=1024 * 1024 * 1024, duration_sec=60.0, bit_rate=20_000_000),
        )

    assert exc.value.detail["reason"] == "compose_insufficient_disk"


def test_derive_failure_updates_persist_compose_input_terminal_policy():
    updates = CompositionService.build_compose_failure_updates(
        {
            "reason": "compose_input_derive_failed",
            "message": "derived compose input is not encoder-safe",
            "failure_code": "derive_not_encoder_safe",
            "compose_input_profile": {"width": 1081, "height": 1921, "pix_fmt": "yuv422p"},
            "safe_key": "video_input_safe.mp4",
        }
    )

    policy = updates["compose_input_policy"]
    assert updates["compose_status"] == "failed"
    assert policy == {
        "mode": "derive_failed",
        "source": "derived_safe",
        "profile": {"width": 1081, "height": 1921, "pix_fmt": "yuv422p"},
        "safe_key": "video_input_safe.mp4",
        "reason": "derived compose input is not encoder-safe",
        "failure_code": "derive_not_encoder_safe",
    }


def test_build_hot_follow_compose_response_preserves_success_shape():
    svc = CompositionService(storage=object(), settings=object())

    result = svc.build_hot_follow_compose_response(
        "hf-compose-ok",
        final_key="deliver/tasks/hf-compose-ok/final.mp4",
        compose_status="done",
        hub={"task_id": "hf-compose-ok", "kind": "hot_follow"},
        line={"line_id": "hot_follow_line", "sop_profile_ref": "docs/runbooks/hot_follow_sop.md"},
    )

    assert result.status_code == 200
    assert result.body["task_id"] == "hf-compose-ok"
    assert result.body["final_key"] == "deliver/tasks/hf-compose-ok/final.mp4"
    assert result.body["compose_status"] == "done"
    assert result.body["hub"]["kind"] == "hot_follow"
    assert result.body["line"]["line_id"] == "hot_follow_line"


def test_run_ffmpeg_timeout_raises_structured_http_exception(monkeypatch):
    svc = CompositionService(storage=object(), settings=object())

    class _Gateway:
        def execute(self, request):
            return WorkerResult(
                request_id=request.request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                result="timeout",
                attempt_facts={"worker_mode": "internal"},
                output_facts={"returncode": None},
                error={"reason": "timeout", "message": "worker timed out after 3s"},
                retry_hint={"retryable": False},
                raw_output={"stderr": "ffmpeg timeout stderr"},
            )

    monkeypatch.setattr("gateway.app.services.compose_service.get_worker_gateway", lambda: _Gateway())

    with pytest.raises(HTTPException) as exc:
        svc._run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], "hf-timeout", "compose", timeout=3)

    detail = exc.value.detail
    assert detail["reason"] == "compose_timeout"
    assert "timed out after 3s" in detail["message"]
    assert "ffmpeg -i in.mp4 out.mp4" in detail["ffmpeg_cmd"]
    assert "timeout stderr" in detail["stderr_tail"]


def test_run_ffmpeg_executes_through_worker_gateway(monkeypatch):
    svc = CompositionService(storage=object(), settings=object())
    seen = {}

    class _Gateway:
        def execute(self, request):
            seen["request"] = request
            return WorkerResult(
                request_id=request.request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                result="success",
                attempt_facts={"worker_mode": "internal"},
                output_facts={"returncode": 0},
                retry_hint={"retryable": False},
                raw_output={"stdout": "ok", "stderr": ""},
            )

    monkeypatch.setattr("gateway.app.services.compose_service.get_worker_gateway", lambda: _Gateway())

    proc = svc._run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], "hf-worker", "compose")

    assert proc.returncode == 0
    assert proc.stdout == "ok"
    assert seen["request"].line_id == "hot_follow_line"
    assert seen["request"].step_id == "compose"
    assert seen["request"].worker_capability == "ffmpeg"
    assert seen["request"].execution_mode == WorkerExecutionMode.INTERNAL


def test_compose_result_keeps_updates_and_final_reference():
    result = ComposeResult(
        updates={"compose_status": "done", "final_video_key": "deliver/tasks/hf/final.mp4"},
        final_key="deliver/tasks/hf/final.mp4",
        final_url="/v1/tasks/hf/final",
        compose_status="done",
    )

    assert result.updates["compose_status"] == "done"
    assert result.final_key.endswith("/final.mp4")
    assert result.final_url == "/v1/tasks/hf/final"
    assert result.compose_status == "done"
