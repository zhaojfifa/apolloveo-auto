from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.routers import tasks as tasks_router
from gateway.app.services.compose_input_policy import evaluate_compose_input_policy
from gateway.app.services.compose_service import HotFollowComposeRequestContract


class _Repo:
    def __init__(self, rows: dict[str, dict] | None = None):
        self._rows = {key: dict(value) for key, value in (rows or {}).items()}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        current = dict(self._rows.get(task_id) or {})
        current.update(fields or {})
        self._rows[task_id] = current
        return dict(current)


def _compose_request() -> HotFollowComposeRequestContract:
    return HotFollowComposeRequestContract(force=True)


def _compose_kwargs(repo: _Repo):
    return {
        "repo": repo,
        "hub_loader": lambda task_id, current_repo: {"task_id": task_id, "task": current_repo.get(task_id)},
        "subtitle_resolver": lambda _task, _task_id: "",
        "subtitle_only_check": lambda _task: False,
        "revision_snapshot": lambda _task: {},
        "lipsync_runner": lambda _task_id, _enabled: None,
    }


def test_compose_input_policy_direct_allows_baseline_safe_portrait_shortvideo():
    decision = evaluate_compose_input_policy(
        {
            "compose_input_probe": {
                "width": 720,
                "height": 1280,
                "file_size_bytes": 2_700_000,
                "duration_sec": 23.85,
                "video_bitrate": 778_928,
                "free_disk_bytes": 4 * 1024 * 1024 * 1024,
            }
        }
    )

    assert decision.mode == "direct"
    assert decision.reason is None
    assert decision.profile is not None
    assert decision.profile.orientation == "portrait"


def test_compose_input_policy_blocks_by_pixel_budget_not_portrait_height():
    direct = evaluate_compose_input_policy(
        {
            "compose_input_probe": {
                "width": 720,
                "height": 1280,
                "file_size_bytes": 2_700_000,
                "duration_sec": 23.85,
                "video_bitrate": 778_928,
            }
        }
    )
    heavy = evaluate_compose_input_policy(
        {
            "compose_input_probe": {
                "width": 2160,
                "height": 3840,
                "file_size_bytes": 120_000_000,
                "duration_sec": 60,
                "video_bitrate": 6_000_000,
            }
        }
    )

    assert direct.mode == "direct"
    assert heavy.mode == "blocked"
    assert heavy.reason == "resolution_too_high"


def test_hot_follow_compose_blocked_preflight_fast_fails_before_lock_and_retries_without_409(monkeypatch):
    task_id = "hf-compose-policy-blocked"
    repo = _Repo(
        {
            task_id: {
                "task_id": task_id,
                "kind": "hot_follow",
                "content_lang": "mm",
                "target_lang": "mm",
                "config": {},
                "compose_input_probe": {
                    "width": 1920,
                    "height": 1080,
                    "file_size_bytes": 300 * 1024 * 1024,
                    "duration_sec": 30,
                    "video_bitrate": 2_000_000,
                },
            }
        }
    )
    called = {"compose": 0}

    def _compose_should_not_run(self, *args, **kwargs):
        called["compose"] += 1
        raise AssertionError("compose should not run for blocked preflight")

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())
    monkeypatch.setattr(
        "gateway.app.services.compose_service.CompositionService.resolve_fresh_final_key",
        lambda self, *args, **kwargs: None,
    )
    monkeypatch.setattr("gateway.app.services.compose_service.CompositionService.compose", _compose_should_not_run)

    first = hf_router._execute_hot_follow_compose_contract(
        task_id,
        repo.get(task_id),
        _compose_request(),
        **_compose_kwargs(repo),
    )
    second = hf_router._execute_hot_follow_compose_contract(
        task_id,
        repo.get(task_id),
        _compose_request(),
        **_compose_kwargs(repo),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.body["compose_status"] == "blocked"
    assert first.body["compose_allowed"] is False
    assert first.body["compose_allowed_reason"] == "input_too_large"
    saved = repo.get(task_id)
    assert saved["compose_status"] == "blocked"
    assert saved["compose_lock_until"] is None
    assert called["compose"] == 0


def test_tasks_compose_keeps_real_concurrent_compose_as_409(monkeypatch):
    task_id = "hf-compose-policy-running"
    repo = _Repo(
        {
            task_id: {
                "task_id": task_id,
                "kind": "hot_follow",
                "compose_lock_until": (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
            }
        }
    )
    monkeypatch.setattr(tasks_router, "get_storage_service", lambda: object())

    result = tasks_router._execute_compose_task_contract(
        task_id,
        repo.get(task_id),
        _compose_request(),
        **_compose_kwargs(repo),
    )

    assert result.status_code == 409
    assert result.body["error"] == "compose_in_progress"


def test_heavy_compose_failure_releases_lock_and_retry_is_not_false_409(monkeypatch):
    task_id = "hf-compose-heavy-failsafe"
    repo = _Repo(
        {
            task_id: {
                "task_id": task_id,
                "kind": "hot_follow",
                "content_lang": "mm",
                "target_lang": "mm",
                "config": {},
                "compose_input_probe": {
                    "width": 720,
                    "height": 1280,
                    "file_size_bytes": 196 * 1024 * 1024,
                    "duration_sec": 120,
                    "video_bitrate": 6_000_000,
                },
            }
        }
    )
    calls = {"compose": 0}

    def _compose_fails(self, *args, **kwargs):
        calls["compose"] += 1
        raise HTTPException(
            status_code=507,
            detail={"reason": "resource_exhausted", "message": "ffmpeg exhausted compose resources"},
        )

    monkeypatch.setattr(hf_router, "get_storage_service", lambda: object())
    monkeypatch.setattr(
        "gateway.app.services.compose_service.CompositionService.resolve_fresh_final_key",
        lambda self, *args, **kwargs: None,
    )
    monkeypatch.setattr("gateway.app.services.compose_service.CompositionService.compose", _compose_fails)

    for _ in range(2):
        with pytest.raises(HTTPException) as exc:
            hf_router._execute_hot_follow_compose_contract(
                task_id,
                repo.get(task_id),
                _compose_request(),
                **_compose_kwargs(repo),
            )
        assert exc.value.status_code == 507
        assert exc.value.detail["reason"] == "resource_exhausted"

    saved = repo.get(task_id)
    assert saved["compose_status"] == "failed"
    assert saved["compose_failure_code"] == "resource_exhausted"
    assert saved["compose_lock_until"] is None
    assert calls["compose"] == 2
