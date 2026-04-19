from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from gateway.app.services.compose_service import (
    ComposePlan,
    ComposeResult,
    CompositionService,
    HotFollowComposeRequestContract,
    _WorkspaceFiles,
)
from gateway.app.services.task_view_helpers import compose_error_parts
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


def test_build_compose_failure_updates_persists_stable_failure_code_and_clears_lock():
    updates = CompositionService.build_compose_failure_updates(
        {"reason": "timeout", "message": "worker timed out"}
    )

    assert updates["compose_status"] == "failed"
    assert updates["compose_error_reason"] == "ffmpeg_timeout"
    assert updates["compose_failure_code"] == "ffmpeg_timeout"
    assert updates["compose_failure_message"] == "worker timed out"
    assert updates["compose_lock_until"] is None
    assert compose_error_parts(updates) == ("ffmpeg_timeout", "worker timed out")


def test_compose_resource_guard_blocks_insufficient_workspace_disk(tmp_path, monkeypatch):
    svc = CompositionService(storage=object(), settings=object())
    video = tmp_path / "video_input.mp4"
    video.write_bytes(b"0" * 1024)
    ws = _WorkspaceFiles(
        task_id="hf-resource-guard",
        tmp=tmp_path,
        video_input_path=video,
        voice_path=None,
        final_path=tmp_path / "final.mp4",
        subtitle_path=None,
        bgm_path=None,
        fontsdir=tmp_path,
        ffmpeg="ffmpeg",
        video_duration=1.0,
        voice_duration=1.0,
        compose_policy="match_video",
    )

    class _Usage:
        free = 128 * 1024 * 1024

    monkeypatch.setattr("gateway.app.services.compose_service.shutil.disk_usage", lambda _path: _Usage())

    with pytest.raises(HTTPException) as exc:
        svc._guard_workspace_resources("hf-resource-guard", {}, ws)

    assert exc.value.detail["reason"] == "disk_insufficient"
