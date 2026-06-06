"""Matrix Script first-preview ASYNC state machine (New Task → Workbench).

Covers the lifecycle correction that moves first-preview generation OFF the
``POST /tasks/matrix-script/new`` request thread:

    POST new -> create task -> persist queued -> dispatch background generation
              -> redirect Workbench immediately -> Workbench polls status
              -> succeeded (inline video) / failed (retry) / stale->retry_required

The synchronous render path was what produced 502s and tasks stuck in
``preview_generation_running``; these tests pin the queued/running/terminal
lifecycle, the projection-side stale guard (never endless generating), the
operator-safe poll endpoint, and the no-leakage / official_publish_ready=false
boundary.

Boundary: Matrix-Script-scoped only — no Hot Follow / Digital Anchor /
artifact_storage / schema / Akool / provider surface is touched.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router
from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import operator_workbench_view as owv

CONTRACT_CLEAN_REF = "content://matrix-script/source/async-fresh-001"
TOPIC = "async lifecycle fresh sample"

_FORM = {
    "topic": TOPIC,
    "source_script_ref": CONTRACT_CLEAN_REF,
    "source_language": "zh",
    "target_language": "mm",
    "target_platform": "TikTok",
    "variation_target_count": "4",
}


class _Repo:
    """In-memory repo that round-trips create/get and merges update patches."""

    def __init__(self) -> None:
        self._rows: Dict[str, Dict[str, Any]] = {}

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = dict(payload)
        self._rows[str(row["task_id"])] = row
        return row

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        row = self._rows.get(str(task_id))
        return dict(row) if row is not None else None

    def update(self, task_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        row = self._rows[str(task_id)]
        row.update(patch)
        return dict(row)


# --------------------------------------------------------------------------- #
# Route lifecycle: New Task POST is fast, defers generation, persists queued.
# --------------------------------------------------------------------------- #


def _client(monkeypatch, repo: _Repo, *, raise_server: bool = True) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "off")
    app.dependency_overrides[get_task_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=raise_server)


def test_new_task_returns_fast_and_does_not_run_generation_inline(monkeypatch) -> None:
    """If generation ran inline, a raising generator would block the redirect.

    The generator is dispatched to the background, so a raise inside it can
    never turn the New Task POST into a 5xx — the operator still gets a 303.
    """
    repo = _Repo()
    calls: list[str] = []

    def _exploding_trigger(task, _repo):
        calls.append(str(task.get("task_id")))
        raise RuntimeError("ffmpeg would run here — must be off the request path")

    monkeypatch.setattr(
        tasks_router, "trigger_matrix_script_initial_preview_generation", _exploding_trigger
    )
    client = _client(monkeypatch, repo, raise_server=False)
    try:
        resp = client.post("/tasks/matrix-script/new", data=_FORM, follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 303, resp.text
    assert "created=matrix_script" in resp.headers["location"]
    # Generation was dispatched (background), not skipped.
    assert calls, "background generation was never dispatched"


def test_new_task_persists_queued_state(monkeypatch) -> None:
    repo = _Repo()
    monkeypatch.setattr(
        tasks_router,
        "trigger_matrix_script_initial_preview_generation",
        lambda task, _repo: {"status": "stubbed"},
    )
    client = _client(monkeypatch, repo, raise_server=False)
    try:
        resp = client.post("/tasks/matrix-script/new", data=_FORM, follow_redirects=False)
        task_id = resp.headers["location"].split("/tasks/")[1].split("?")[0]
        stored = repo.get(task_id) or {}
    finally:
        app.dependency_overrides.clear()

    cfg = stored.get("config") or {}
    initial = cfg.get(auto.AUTO_PREVIEW_STATUS_KEY) or {}
    assert initial.get("status") == auto.STATUS_QUEUED
    assert initial.get("queued_at")
    assert initial.get("official_publish_ready") is False
    assert auto.STAGED_CANDIDATE_KEY not in cfg


# --------------------------------------------------------------------------- #
# Background job transitions: queued/running -> succeeded / failed.
# --------------------------------------------------------------------------- #


def _task(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"task_id": "ms-async-1", "kind": "matrix_script", "config": config or {}}


def test_enqueue_then_trigger_succeeds_with_staged_candidate(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task())

    def _fake_payload(generated_task):
        return {
            "has_result": True,
            "operator_usable": True,
            "technical_preview": False,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": "/api/matrix-script/ms-async-1/tomato-real-result/preview/final.mp4",
        }

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _fake_payload)

    queued = auto.enqueue_matrix_script_initial_preview_generation(repo.get("ms-async-1"), repo)
    assert queued["status"] == auto.STATUS_QUEUED

    status = auto.trigger_matrix_script_initial_preview_generation(repo.get("ms-async-1"), repo)
    assert status["status"] == auto.STATUS_SUCCEEDED
    assert status.get("completed_at")

    cfg = (repo.get("ms-async-1") or {})["config"]
    assert cfg[auto.STAGED_CANDIDATE_KEY]["preview_url"].endswith("/final.mp4")
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_SUCCEEDED


def test_trigger_failure_finalizes_failed_never_running(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task())

    def _fail(_task):
        raise RuntimeError("sample failure")

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _fail)
    status = auto.trigger_matrix_script_initial_preview_generation(repo.get("ms-async-1"), repo)

    cfg = (repo.get("ms-async-1") or {})["config"]
    assert status["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] != auto.STATUS_RUNNING
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY].get("failed_at")
    assert auto.STAGED_CANDIDATE_KEY not in cfg


def test_trigger_corrupt_final_video_transitions_to_failed(monkeypatch) -> None:
    repo = _Repo()
    repo.create(_task())

    def _raise_validation(_task):
        raise auto.AutoPreviewValidationError("final_video_too_small")

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _raise_validation)
    status = auto.trigger_matrix_script_initial_preview_generation(repo.get("ms-async-1"), repo)

    cfg = (repo.get("ms-async-1") or {})["config"]
    assert status["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["stage"] == "validation"
    assert auto.STAGED_CANDIDATE_KEY not in cfg


# --------------------------------------------------------------------------- #
# Workbench projection: queued/running poll, success inline, failure retry,
# stale running -> retry_required (never endless generating).
# --------------------------------------------------------------------------- #


def _now() -> datetime:
    return datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


def _view_for(status_payload: Dict[str, Any], *, now: datetime) -> Dict[str, Any]:
    task = {"kind": "matrix_script", "config": {auto.AUTO_PREVIEW_STATUS_KEY: status_payload}}
    return owv.build_matrix_script_operator_workbench_view(task, now=now)


def test_workbench_queued_state_renders_polling(monkeypatch) -> None:
    now = _now()
    view = _view_for({"status": auto.STATUS_QUEUED, "queued_at": now.isoformat()}, now=now)
    mr = view["main_result"]
    assert mr["status"] == auto.STATUS_QUEUED
    assert mr["poll"] is True
    assert mr["operator_usable"] is False
    assert mr["preview_url"] is None
    assert mr["official_publish_ready"] is False


def test_workbench_running_fresh_renders_polling() -> None:
    now = _now()
    started = (now - timedelta(seconds=30)).isoformat()
    view = _view_for({"status": auto.STATUS_RUNNING, "started_at": started}, now=now)
    mr = view["main_result"]
    assert mr["status"] == auto.STATUS_RUNNING
    assert mr["poll"] is True


def test_workbench_success_renders_inline_video() -> None:
    now = _now()
    task = {
        "kind": "matrix_script",
        "config": {
            auto.STAGED_CANDIDATE_KEY: {
                "has_result": True,
                "operator_usable": True,
                "delivery_candidate": True,
                "official_publish_ready": False,
                "preview_url": "/api/matrix-script/x/tomato-real-result/preview/final.mp4",
            }
        },
    }
    view = owv.build_matrix_script_operator_workbench_view(task, now=now)
    mr = view["main_result"]
    assert mr["operator_usable"] is True
    assert mr["poll"] is False
    assert mr["preview_url"].endswith("/final.mp4")
    assert view["delivery"]["preview_url"].endswith("/final.mp4")
    assert mr["official_publish_ready"] is False


def test_workbench_failed_renders_retry() -> None:
    now = _now()
    view = _view_for(
        {
            "status": auto.STATUS_FAILED,
            "failed_at": now.isoformat(),
            "error_summary": auto.OPERATOR_SAFE_GENERATION_FAILURE,
        },
        now=now,
    )
    mr = view["main_result"]
    assert mr["status"] == auto.STATUS_FAILED
    assert mr["poll"] is False
    assert mr["blocked_reason"] == auto.OPERATOR_SAFE_GENERATION_FAILURE


def test_workbench_stale_running_becomes_retry_required_not_endless() -> None:
    now = _now()
    started = (now - timedelta(seconds=owv.RUNNING_STALE_SECONDS + 60)).isoformat()
    view = _view_for({"status": auto.STATUS_RUNNING, "started_at": started}, now=now)
    mr = view["main_result"]
    # Stale guard: a worker that died mid-run must never read as endless generating.
    assert mr["status"] == owv.STATUS_PREVIEW_GENERATION_RETRY_REQUIRED
    assert mr["poll"] is False
    assert mr["blocked_reason"]


def test_workbench_stale_queued_becomes_retry_required() -> None:
    now = _now()
    queued_at = (now - timedelta(seconds=owv.RUNNING_STALE_SECONDS + 1)).isoformat()
    view = _view_for({"status": auto.STATUS_QUEUED, "queued_at": queued_at}, now=now)
    assert view["main_result"]["status"] == owv.STATUS_PREVIEW_GENERATION_RETRY_REQUIRED
    assert view["main_result"]["poll"] is False


def test_workbench_view_has_no_provider_or_publish_leakage() -> None:
    now = _now()
    view = _view_for({"status": auto.STATUS_RUNNING, "started_at": now.isoformat()}, now=now)
    blob = str(view).lower()
    for token in owv._FORBIDDEN_TOKENS:
        assert token not in blob
    assert view["main_result"]["official_publish_ready"] is False
    assert view["delivery"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# Poll endpoint: operator-safe status target the Workbench polls.
# --------------------------------------------------------------------------- #


def test_status_endpoint_reports_queued_poll_true(monkeypatch) -> None:
    repo = _Repo()
    # The endpoint uses real wall-clock for the stale guard, so the queued_at
    # must be recent (a fixed past timestamp would project to retry_required).
    fresh_queued_at = datetime.now(timezone.utc).isoformat()
    repo.create(_task({auto.AUTO_PREVIEW_STATUS_KEY: {"status": auto.STATUS_QUEUED, "queued_at": fresh_queued_at}}))
    client = _client(monkeypatch, repo)
    try:
        resp = client.get("/api/matrix-script/ms-async-1/initial-preview-status")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == auto.STATUS_QUEUED
    assert body["poll"] is True
    assert body["official_publish_ready"] is False


def test_status_endpoint_reports_success_with_preview_url(monkeypatch) -> None:
    repo = _Repo()
    repo.create(
        _task(
            {
                auto.STAGED_CANDIDATE_KEY: {
                    "has_result": True,
                    "operator_usable": True,
                    "delivery_candidate": True,
                    "official_publish_ready": False,
                    "preview_url": "/api/matrix-script/ms-async-1/tomato-real-result/preview/final.mp4",
                }
            }
        )
    )
    client = _client(monkeypatch, repo)
    try:
        resp = client.get("/api/matrix-script/ms-async-1/initial-preview-status")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["poll"] is False
    assert body["operator_usable"] is True
    assert body["preview_url"].endswith("/final.mp4")


def test_status_endpoint_rejects_non_matrix_script_task(monkeypatch) -> None:
    repo = _Repo()
    repo.create({"task_id": "hf-1", "kind": "hot_follow", "config": {}})
    client = _client(monkeypatch, repo)
    try:
        resp = client.get("/api/matrix-script/hf-1/initial-preview-status")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 400


def test_status_endpoint_missing_task_is_404(monkeypatch) -> None:
    repo = _Repo()
    client = _client(monkeypatch, repo)
    try:
        resp = client.get("/api/matrix-script/nope/initial-preview-status")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404
