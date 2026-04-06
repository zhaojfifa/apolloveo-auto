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

    def _boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["ffmpeg", "-i", "in.mp4", "out.mp4"],
            timeout=3,
            stderr="ffmpeg timeout stderr",
        )

    monkeypatch.setattr(subprocess, "run", _boom)

    with pytest.raises(HTTPException) as exc:
        svc._run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], "hf-timeout", "compose", timeout=3)

    detail = exc.value.detail
    assert detail["reason"] == "compose_timeout"
    assert "timed out after 3s" in detail["message"]
    assert "ffmpeg -i in.mp4 out.mp4" in detail["ffmpeg_cmd"]
    assert "timeout stderr" in detail["stderr_tail"]


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
