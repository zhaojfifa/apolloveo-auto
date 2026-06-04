from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import os
import pytest

from gateway.app.services.matrix_script import auto_preview_generation as auto
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod
from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    InMemoryArtifactSink,
    StagingError,
)
from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_FFMPEG = ffmpeg_available()
_ASSETS = os.path.isdir(plan_mod.default_asset_dir()) and all(
    os.path.exists(os.path.join(plan_mod.default_asset_dir(), shot.asset_filename))
    for shot in plan_mod.TOMATO_SHOTS
)
_skip_no_ffmpeg = pytest.mark.skipif(not _FFMPEG, reason="ffmpeg/ffprobe not installed")
_skip_no_assets = pytest.mark.skipif(not _ASSETS, reason="MS-TOMATO-BEACH-001 asset pack not present")


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
    assert status.get("completed_at")
    # Async lifecycle: the background job writes running (started_at) first, then
    # the terminal succeeded + staged candidate — two durable config updates.
    assert len(repo.updates) == 2
    first_status = repo.updates[0][1]["config"][auto.AUTO_PREVIEW_STATUS_KEY]
    assert first_status["status"] == auto.STATUS_RUNNING
    assert first_status.get("started_at")
    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert cfg[auto.STAGED_CANDIDATE_KEY]["has_result"] is True
    assert cfg[auto.STAGED_CANDIDATE_KEY]["preview_url"].endswith(
        "/tomato-real-result/preview/final.mp4"
    )
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_SUCCEEDED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] != auto.STATUS_RUNNING


@_skip_no_ffmpeg
@_skip_no_assets
def test_trigger_initial_preview_real_success_persists_valid_preview(monkeypatch, tmp_path: Path) -> None:
    task = _task()
    repo = _Repo(task)
    output_dir = tmp_path / "tomato"

    monkeypatch.setattr(auto, "_resolve_tomato_output_dir", lambda _task_id: str(output_dir))
    monkeypatch.setattr(auto, "_build_tomato_sink", lambda _task_id: InMemoryArtifactSink())

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    final_path = output_dir / "final" / "final.mp4"
    manifest_path = output_dir / "manifest.json"

    assert status["status"] == auto.STATUS_SUCCEEDED
    assert status["status"] != auto.STATUS_RUNNING
    assert final_path.exists()
    assert manifest_path.exists()
    auto.validate_tomato_result_artifacts(SimpleNamespace(final_video_path=str(final_path)))  # type: ignore[arg-type]
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_SUCCEEDED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False
    staged = cfg[auto.STAGED_CANDIDATE_KEY]
    assert staged["preview_url"] == (
        "/api/matrix-script/ms-auto-1/tomato-real-result/preview/final.mp4"
    )
    assert staged["delivery_candidate"] is True
    assert staged["official_publish_ready"] is False


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
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["error_summary"] == auto.OPERATOR_SAFE_GENERATION_FAILURE
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["stage"] == "generation"
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] != auto.STATUS_RUNNING


def test_trigger_initial_preview_validation_failure_never_persists_candidate(monkeypatch) -> None:
    task = _task()
    repo = _Repo(task)

    def _invalid(_task):
        raise auto.AutoPreviewValidationError("final_video_too_small")

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _invalid)

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert status["status"] == auto.STATUS_FAILED
    assert auto.STAGED_CANDIDATE_KEY not in cfg
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["stage"] == "validation"
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["error_summary"] == auto.OPERATOR_SAFE_GENERATION_FAILURE
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False


def test_trigger_initial_preview_staging_failure_never_stays_running(monkeypatch) -> None:
    task = _task()
    repo = _Repo(task)

    def _staging_failure(_task):
        raise StagingError("stage failed")

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _staging_failure)

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert status["status"] == auto.STATUS_FAILED
    assert status["stage"] == "staging"
    assert auto.STAGED_CANDIDATE_KEY not in cfg
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["stage"] == "staging"
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] != auto.STATUS_RUNNING


def test_trigger_initial_preview_persistence_failure_finalizes_failed(monkeypatch) -> None:
    class _PersistenceFailRepo(_Repo):
        def update(self, task_id: str, patch: dict[str, Any]) -> Dict[str, Any]:
            config = patch.get("config") or {}
            if auto.STAGED_CANDIDATE_KEY in config:
                raise RuntimeError("cannot persist staged candidate")
            return super().update(task_id, patch)

    task = _task()
    repo = _PersistenceFailRepo(task)

    def _fake_payload(_task):
        return {
            "has_result": True,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": "/api/matrix-script/ms-auto-1/tomato-real-result/preview/final.mp4",
        }

    monkeypatch.setattr(auto, "build_matrix_script_tomato_preview_payload", _fake_payload)

    status = auto.trigger_matrix_script_initial_preview_generation(task, repo)

    stored = repo.get("ms-auto-1") or {}
    cfg = stored["config"]
    assert status["status"] == auto.STATUS_FAILED
    assert status["stage"] == "persistence"
    assert auto.STAGED_CANDIDATE_KEY not in cfg
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["status"] == auto.STATUS_FAILED
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["stage"] == "persistence"
    assert cfg[auto.AUTO_PREVIEW_STATUS_KEY]["official_publish_ready"] is False


def test_build_preview_payload_normalizes_object_shaped_task(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_run(task, output_dir, *, sink):
        seen["task"] = task
        seen["output_dir"] = output_dir
        seen["sink"] = sink
        return {"result": "ok"}

    monkeypatch.setattr(auto, "run_tomato_real_result", _fake_run)
    monkeypatch.setattr(auto, "validate_tomato_result_artifacts", lambda _result: None)
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


def test_validate_tomato_result_artifacts_rejects_invalid_final_video(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    final_path = final_dir / "final.mp4"
    final_path.write_bytes(b"bad")
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")

    result = SimpleNamespace(final_video_path=str(final_path))

    try:
        auto.validate_tomato_result_artifacts(result)  # type: ignore[arg-type]
    except auto.AutoPreviewValidationError as exc:
        assert str(exc) == "final_video_too_small"
    else:  # pragma: no cover
        raise AssertionError("invalid final.mp4 was accepted")


def test_validate_tomato_result_artifacts_accepts_valid_final_and_manifest(monkeypatch, tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    final_path = final_dir / "final.mp4"
    final_path.write_bytes(b"x" * (auto.MIN_FINAL_VIDEO_BYTES + 1))
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    result = SimpleNamespace(final_video_path=str(final_path))

    monkeypatch.setattr(auto, "probe_duration_seconds", lambda _path: 12.0)
    monkeypatch.setattr(auto, "_probe_has_video_stream", lambda _path: True)

    auto.validate_tomato_result_artifacts(result)  # type: ignore[arg-type]


def test_validate_tomato_result_artifacts_rejects_missing_manifest(monkeypatch, tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    final_path = final_dir / "final.mp4"
    final_path.write_bytes(b"x" * (auto.MIN_FINAL_VIDEO_BYTES + 1))
    result = SimpleNamespace(final_video_path=str(final_path))

    monkeypatch.setattr(auto, "probe_duration_seconds", lambda _path: 12.0)
    monkeypatch.setattr(auto, "_probe_has_video_stream", lambda _path: True)

    try:
        auto.validate_tomato_result_artifacts(result)  # type: ignore[arg-type]
    except auto.AutoPreviewValidationError as exc:
        assert str(exc) == "manifest_missing"
    else:  # pragma: no cover
        raise AssertionError("missing manifest was accepted")
