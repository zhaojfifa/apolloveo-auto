from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from gateway.app.services.compose_service import (
    ComposeInputProfile,
    ComposePlan,
    ComposePreflightDecision,
    ComposeResult,
    CompositionService,
    HotFollowComposeRequestContract,
)
from gateway.app.services.task_view_helpers import compute_composed_state, task_to_detail
from gateway.app.services.worker_gateway import WorkerExecutionMode, WorkerResult


def _profile(
    *,
    size: int = 20 * 1024 * 1024,
    duration: float = 30.0,
    height: int = 720,
    bitrate: int = 2_000_000,
    free_disk: int = 4 * 1024 * 1024 * 1024,
) -> ComposeInputProfile:
    return ComposeInputProfile(
        file_size_bytes=size,
        duration_sec=duration,
        width=1280,
        height=height,
        video_bitrate=bitrate,
        audio_stream_count=1,
        video_codec="h264",
        audio_codec="aac",
        estimated_working_set_bytes=size * 3,
        free_disk_bytes=free_disk,
    )


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
    assert detail["reason"] == "ffmpeg_timeout"
    assert detail["compose_failure_code"] == "ffmpeg_timeout"
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


def test_compose_preflight_small_input_direct(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())
    monkeypatch.setattr(svc, "_probe_video_profile", lambda *_args, **_kwargs: _profile())

    decision = svc._preflight_compose_input(
        "hf-small",
        tmp_path / "in.mp4",
        SimpleNamespace(),
        fallback_size=1024,
        fallback_duration=1.0,
    )

    assert decision.mode == "direct"
    assert decision.status == "pass"
    assert decision.reason is None


def test_compose_preflight_large_allowed_input_adapts(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())
    monkeypatch.setattr(svc, "_probe_video_profile", lambda *_args, **_kwargs: _profile(size=196 * 1024 * 1024))

    decision = svc._preflight_compose_input(
        "hf-large",
        tmp_path / "in.mp4",
        SimpleNamespace(),
        fallback_size=1024,
        fallback_duration=1.0,
    )

    assert decision.mode == "adapt"
    assert decision.status == "adapted"
    assert decision.reason == "input_requires_adaptation"


def test_compose_preflight_oversized_input_blocked(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())
    monkeypatch.setattr(svc, "_probe_video_profile", lambda *_args, **_kwargs: _profile(size=251 * 1024 * 1024))

    decision = svc._preflight_compose_input(
        "hf-oversized",
        tmp_path / "in.mp4",
        SimpleNamespace(),
        fallback_size=1024,
        fallback_duration=1.0,
    )

    assert decision.mode == "blocked"
    assert decision.reason == "input_too_large"


def test_compose_preflight_disk_insufficient_blocked(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())
    monkeypatch.setattr(svc, "_probe_video_profile", lambda *_args, **_kwargs: _profile(free_disk=1024))

    decision = svc._preflight_compose_input(
        "hf-disk",
        tmp_path / "in.mp4",
        SimpleNamespace(),
        fallback_size=1024,
        fallback_duration=1.0,
    )

    assert decision.mode == "blocked"
    assert decision.reason == "disk_insufficient"


def test_compose_adapt_generates_derived_input(monkeypatch, tmp_path):
    svc = CompositionService(storage=object(), settings=object())
    source = tmp_path / "input.mp4"
    source.write_bytes(b"source")
    decision = ComposePreflightDecision("adapt", "input_requires_adaptation", _profile(size=196 * 1024 * 1024))
    seen = {}

    def _run(cmd, *_args, **_kwargs):
        seen["cmd"] = cmd
        Path(cmd[-1]).write_bytes(b"adapted")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(svc, "_run_ffmpeg", _run)

    adapted = svc._adapt_compose_input("hf-adapt", "ffmpeg", source, tmp_path, decision)

    assert adapted.name == "video_input_adapted_720p.mp4"
    assert adapted.read_bytes() == b"adapted"
    assert "-map" in seen["cmd"]
    assert "scale=-2:min(720\\,ih)" in seen["cmd"]


def test_compose_timeout_failure_updates_are_not_left_running():
    updates = CompositionService.build_compose_failure_updates(
        {"reason": "ffmpeg_timeout", "message": "compose timed out", "compose_failure_code": "ffmpeg_timeout"}
    )

    assert updates["compose_status"] == "failed"
    assert updates["compose_last_status"] == "failed"
    assert updates["compose_failure_code"] == "ffmpeg_timeout"
    assert updates["compose_last_finished_at"]


def test_compose_failure_state_keeps_composed_state_loadable(monkeypatch):
    monkeypatch.setattr("gateway.app.services.task_view_helpers.object_exists", lambda key: str(key).endswith("raw.mp4"))
    task = {
        "task_id": "hf-compose-failed",
        "kind": "hot_follow",
        "raw_path": "deliver/tasks/hf-compose-failed/raw.mp4",
        "compose_status": "failed",
        "compose_last_status": "failed",
        "compose_error_reason": "disk_insufficient",
        "compose_failure_code": "disk_insufficient",
        "compose_failure_message": "compose input blocked by preflight: disk_insufficient",
        "compose_preflight_status": "blocked",
        "compose_preflight_reason": "disk_insufficient",
        "compose_input_profile": "blocked",
    }

    state = compute_composed_state(task, "hf-compose-failed")

    assert state["composed_ready"] is False
    assert state["composed_reason"] == "disk_insufficient"
    assert state["compose_failure_code"] == "disk_insufficient"


def test_compose_failure_state_keeps_task_detail_loadable(monkeypatch):
    monkeypatch.setattr("gateway.app.services.task_view_helpers.object_exists", lambda _key: False)
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "task_id": "hf-compose-detail-failed",
        "kind": "hot_follow",
        "created_at": now,
        "updated_at": now,
        "status": "failed",
        "compose_status": "blocked",
        "compose_last_status": "blocked",
        "compose_error_reason": "input_too_large",
        "compose_failure_code": "input_too_large",
        "compose_failure_message": "compose input blocked by preflight: input_too_large",
        "compose_preflight_status": "blocked",
        "compose_preflight_reason": "input_too_large",
        "compose_input_profile": "blocked",
    }

    detail = task_to_detail(task)

    assert detail.task_id == "hf-compose-detail-failed"
    assert detail.status == "failed"


def test_stale_running_compose_projects_failed_state(monkeypatch):
    monkeypatch.setattr("gateway.app.services.task_view_helpers.object_exists", lambda key: str(key).endswith("raw.mp4"))
    task = {
        "task_id": "hf-stale-running",
        "kind": "hot_follow",
        "raw_path": "deliver/tasks/hf-stale-running/raw.mp4",
        "compose_status": "running",
        "compose_last_status": "running",
        "compose_lock_until": None,
    }

    state = compute_composed_state(task, "hf-stale-running")

    assert state["compose_running_stale"] is True
    assert state["compose_failure_code"] == "compose_runtime_stale"
    assert state["composed_reason"] == "compose_runtime_stale"


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
