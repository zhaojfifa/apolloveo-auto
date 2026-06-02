from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

from gateway.app.services.matrix_script import auto_preview_generation as auto


class _Repo:
    def __init__(self, task: Dict[str, Any]):
        self.task = dict(task)
        self.updates: list[tuple[str, dict[str, Any]]] = []

    def get(self, task_id: str) -> Dict[str, Any] | None:
        if self.task.get("task_id") != task_id:
            return None
        return dict(self.task)

    def update(self, task_id: str, patch: dict[str, Any]) -> Dict[str, Any]:
        assert task_id == self.task["task_id"]
        self.updates.append((task_id, patch))
        self.task.update(patch)
        return dict(self.task)


def _task() -> Dict[str, Any]:
    return {
        "task_id": "ms-auto-1",
        "kind": "matrix_script",
        "config": {"entry": {"topic": "海边与圣女果"}},
    }


def test_trigger_initial_preview_persists_staged_candidate(monkeypatch) -> None:
    task = _task()
    repo = _Repo(task)

    def _fake_payload(generated_task):
        assert generated_task["task_id"] == "ms-auto-1"
        return {
            "has_result": True,
            "operator_usable": True,
            "technical_preview": False,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": "/api/matrix-script/ms-auto-1/tomato-real-result/preview/final.mp4",
        }

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _fake_payload)

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    assert status["status"] == auto.STATUS_SUCCEEDED
    assert len(repo.updates) == 2
    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert cfg[auto.STAGED_CANDIDATE_KEY]["has_result"] is True
    assert cfg[auto.STAGED_CANDIDATE_KEY]["preview_url"].endswith(
        "/tomato-real-result/preview/final.mp4"
    )
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_SUCCEEDED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False


def test_trigger_initial_preview_persists_failure(monkeypatch) -> None:
    task = _task()
    repo = _Repo(task)

    def _fail(_task):
        raise RuntimeError("sample failure")

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _fail)

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    assert status["status"] == auto.STATUS_FAILED
    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert auto.STAGED_CANDIDATE_KEY not in cfg
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_FAILED
    assert "sample failure" in cfg[auto.AUTO_PREVIEW_STATUS_KEY]["error"]
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False


def test_build_preview_payload_normalizes_object_shaped_task(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_run(task, output_dir, *, sink):
        seen["task"] = task
        seen["output_dir"] = output_dir
        seen["sink"] = sink
        return {"result": "ok"}

    monkeypatch.setattr(auto, "run_tomato_real_result", _fake_run)
    monkeypatch.setattr(auto, "tomato_result_to_payload", lambda _result: {"has_result": True})
    monkeypatch.setattr(auto, "_build_tomato_sink", lambda task_id: {"task_id": task_id})
    monkeypatch.setattr(auto, "assert_no_delivery_view_forbidden_tokens", lambda _payload: None)

    payload = auto.build_matrix_script_tomato_preview_payload(
        SimpleNamespace(task_id="ms-object-1", config={"entry": {"topic": "demo"}})
    )

    assert seen["task"]["task_id"] == "ms-object-1"
    assert seen["task"]["config"]["entry"]["topic"] == "demo"
    assert payload["preview_url"] == (
        "/api/matrix-script/ms-object-1/tomato-real-result/preview/final.mp4"
    )
