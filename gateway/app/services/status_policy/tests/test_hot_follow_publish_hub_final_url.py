from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.services import task_view_presenters as presenters


class _Repo:
    def __init__(self):
        self._rows = {}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        current = dict(self._rows.get(task_id) or {})
        current.update(fields or {})
        self._rows[task_id] = current
        return current


class _Binding:
    def to_payload(self):
        return {
            "line_id": "hot_follow_line",
            "sop_profile_ref": "docs/runbooks/hot_follow_sop.md",
        }


def _authoritative_publish_state(
    task_id: str,
    *,
    final_exists: bool,
    composed_ready: bool,
    compose_status: str,
    publish_ready: bool,
    audio_ready: bool,
    audio_ready_reason: str = "ready",
    composed_reason: str | None = None,
    selected_route: str = "tts_replace_route",
    no_dub_compose_allowed: bool = False,
    scene_pack_exists: bool = False,
    scene_pack_status: str = "pending",
) -> dict:
    final_url = f"/v1/tasks/{task_id}/final" if final_exists else None
    normalized_reason = composed_reason or ("ready" if composed_ready else "compose_not_done")
    return {
        "composed_ready": composed_ready,
        "composed_reason": normalized_reason,
        "compose_status": compose_status,
        "ready_gate": {
            "final_exists": final_exists,
            "compose_ready": composed_ready,
            "publish_ready": publish_ready,
            "audio_ready": audio_ready,
            "audio_ready_reason": audio_ready_reason,
            "compose_reason": normalized_reason,
            "blocking": [] if publish_ready else [normalized_reason],
            "selected_compose_route": selected_route,
            "no_dub_compose_allowed": no_dub_compose_allowed,
        },
        "final": {
            "exists": final_exists,
            "fresh": final_exists,
            "url": final_url,
            "key": f"deliver/tasks/{task_id}/final.mp4" if final_exists else None,
        },
        "historical_final": {"exists": False, "url": None},
        "final_fresh": final_exists,
        "final_stale_reason": None,
        "scene_pack": {
            "exists": scene_pack_exists,
            "status": scene_pack_status,
        },
        "deliverables": [
            {
                "kind": "final",
                "label": "Final Video",
                "title": "Final Video",
                "url": final_url,
                "open_url": final_url,
                "download_url": final_url,
                "status": "done" if final_exists else "pending",
                "state": "done" if final_exists else "pending",
            }
        ],
    }


def test_publish_hub_uses_authoritative_final_ready_state_for_local_upload_preserve(monkeypatch):
    task_id = "7852ffeefdf9"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "title": "local upload sample",
            "compose_status": "pending",
            "compose_last_status": "pending",
        },
    )
    authoritative_state = _authoritative_publish_state(
        task_id,
        final_exists=True,
        composed_ready=True,
        compose_status="done",
        publish_ready=True,
        audio_ready=True,
        selected_route="preserve_source_route",
        no_dub_compose_allowed=True,
        scene_pack_exists=False,
        scene_pack_status="running",
    )

    monkeypatch.setattr(
        presenters,
        "_build_hot_follow_authoritative_state",
        lambda current_task_id, current_repo, **_kwargs: (
            current_repo.get(current_task_id),
            {},
            authoritative_state,
        ),
    )

    def _backfill(current_repo, current_task_id, _task, composed_ready):
        assert composed_ready is True
        current_repo.upsert(
            current_task_id,
            {"compose_status": "done", "compose_last_status": "done"},
        )
        return True

    data = presenters.build_hot_follow_publish_hub(
        task_id,
        repo,
        backfill_compose_done=_backfill,
        line_binding_loader=lambda _task: _Binding(),
    )

    assert data["final"]["exists"] is True
    assert data["composed_ready"] is True
    assert data["compose_status"] == "done"
    assert data["ready_gate"]["audio_ready"] is True
    assert data["ready_gate"]["publish_ready"] is True
    assert data["ready_gate"]["selected_compose_route"] == "preserve_source_route"
    assert data["ready_gate"]["blocking"] == []
    assert data["scene_pack_pending_reason"] == "scenes.running"
    assert data["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert (data["deliverables"]["final_mp4"]["url"]).endswith(f"/v1/tasks/{task_id}/final")

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"


def test_publish_hub_uses_authoritative_final_ready_state_for_url_tts_only(monkeypatch):
    task_id = "01f530caabf5"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "title": "url sample",
            "source_url": "https://example.test/video",
            "compose_status": "pending",
        },
    )
    authoritative_state = _authoritative_publish_state(
        task_id,
        final_exists=True,
        composed_ready=True,
        compose_status="done",
        publish_ready=True,
        audio_ready=True,
        selected_route="tts_replace_route",
    )

    monkeypatch.setattr(
        presenters,
        "_build_hot_follow_authoritative_state",
        lambda current_task_id, current_repo, **_kwargs: (
            current_repo.get(current_task_id),
            {},
            authoritative_state,
        ),
    )

    data = presenters.build_hot_follow_publish_hub(
        task_id,
        repo,
        backfill_compose_done=lambda *_args, **_kwargs: False,
        line_binding_loader=lambda _task: _Binding(),
    )

    assert data["final"]["exists"] is True
    assert data["composed_ready"] is True
    assert data["composed_reason"] == "ready"
    assert data["compose_status"] == "done"
    assert data["ready_gate"]["publish_ready"] is True
    assert data["ready_gate"]["audio_ready"] is True
    assert "missing_voiceover" not in data["ready_gate"]["blocking"]
    assert "audio_not_ready" not in data["ready_gate"]["blocking"]
    assert "compose_not_done" not in data["ready_gate"]["blocking"]


def test_publish_hub_keeps_scene_pack_pending_non_blocking_when_final_ready(monkeypatch):
    task_id = "hf-scene-pack-pending"
    repo = _Repo()
    repo.upsert(task_id, {"task_id": task_id, "kind": "hot_follow"})
    authoritative_state = _authoritative_publish_state(
        task_id,
        final_exists=True,
        composed_ready=True,
        compose_status="done",
        publish_ready=True,
        audio_ready=True,
        scene_pack_exists=False,
        scene_pack_status="pending",
    )

    monkeypatch.setattr(
        presenters,
        "_build_hot_follow_authoritative_state",
        lambda current_task_id, current_repo, **_kwargs: (
            current_repo.get(current_task_id),
            {},
            authoritative_state,
        ),
    )

    data = presenters.build_hot_follow_publish_hub(
        task_id,
        repo,
        backfill_compose_done=lambda *_args, **_kwargs: False,
        line_binding_loader=lambda _task: _Binding(),
    )

    assert data["final"]["exists"] is True
    assert data["ready_gate"]["publish_ready"] is True
    assert data["scene_pack_pending_reason"] == "scenes.not_ready"


def test_publish_hub_keeps_in_progress_state_when_final_absent(monkeypatch):
    task_id = "hf-compose-running"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "compose_status": "running",
            "compose_last_status": "running",
        },
    )
    authoritative_state = _authoritative_publish_state(
        task_id,
        final_exists=False,
        composed_ready=False,
        compose_status="pending",
        publish_ready=False,
        audio_ready=True,
        composed_reason="compose_not_done",
        selected_route="tts_replace_route",
    )

    monkeypatch.setattr(
        presenters,
        "_build_hot_follow_authoritative_state",
        lambda current_task_id, current_repo, **_kwargs: (
            current_repo.get(current_task_id),
            {},
            authoritative_state,
        ),
    )

    data = presenters.build_hot_follow_publish_hub(
        task_id,
        repo,
        backfill_compose_done=lambda *_args, **_kwargs: False,
        line_binding_loader=lambda _task: _Binding(),
    )

    assert data["final"]["exists"] is False
    assert data["composed_ready"] is False
    assert data["compose_status"] == "pending"
    assert data["ready_gate"]["audio_ready"] is True
    assert data["ready_gate"]["publish_ready"] is False
    assert "compose_not_done" in data["ready_gate"]["blocking"]
