from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.deps import get_task_repository
from gateway.app.routers import tasks as tasks_router
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import task_view as task_view_module


class _Repo:
    def __init__(self):
        self._rows = {}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        cur = dict(self._rows.get(task_id) or {})
        cur.update(fields or {})
        self._rows[task_id] = cur
        return cur


def test_hot_follow_publish_hub_includes_final_preview_url_and_ready(monkeypatch):
    task_id = "hf-publish-hub-final-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "scenes_status": "running",
            "compose_status": "pending",
            "compose_last_status": "pending",
        },
    )

    monkeypatch.setattr(
        hf_router,
        "_publish_hub_payload",
        lambda _task: {
            "task_id": task_id,
            "media": {
                "final_video_url": f"/v1/tasks/{task_id}/final",
                "final_url": f"/v1/tasks/{task_id}/final",
                "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
            },
            "final_url": f"/v1/tasks/{task_id}/final",
            "final_video_url": f"/v1/tasks/{task_id}/final",
            "deliverables": {
                "final_mp4": {"label": "final.mp4", "url": f"/v1/tasks/{task_id}/final"},
            },
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final"},
            "historical_final": {"exists": True, "url": f"/v1/tasks/{task_id}/final"},
            "final_fresh": True,
            "final_stale_reason": None,
            "audio": {
                "status": "done",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "tts_voice": "mm_female_1",
            },
            "subtitles": {
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "edited_text": "stub subtitle",
            },
            "scene_pack": {"exists": False, "status": "running"},
            "scene_pack_pending_reason": "scenes.running",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "_build_hot_follow_publish_hub",
        lambda current_task_id, repo, **kwargs: task_view_module.build_hot_follow_publish_hub(
            current_task_id,
            repo=repo,
            publish_payload_builder=kwargs["publish_payload_builder"],
            backfill_compose_done=kwargs["backfill_compose_done"],
            settings_loader=lambda: object(),
            subtitle_lane_loader=lambda _task_id, _task: {
                "primary_editable_text": "stub subtitle",
                "primary_editable_format": "srt",
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "subtitle_artifact_exists": True,
                "actual_burn_subtitle_source": "mm.srt",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "dub_input_text": "stub subtitle",
            },
            composed_state_loader=lambda _task, _task_id: {
                "composed_ready": True,
                "composed_reason": "ready",
                "final": {
                    "exists": True,
                    "fresh": True,
                    "url": f"/v1/tasks/{task_id}/final",
                    "asset_version": "final-v1",
                },
                "historical_final": {"exists": False},
                "final_fresh": True,
                "final_stale_reason": None,
            },
            pipeline_state_loader=lambda _task, step, *, composed=None: {
                "subtitles": ("done", "subtitle=ready"),
                "audio": ("done", "audio=ready"),
                "compose": ("done", "final=ready"),
            }[step],
            dual_channel_state_loader=lambda *_args, **_kwargs: {"content_mode": "voice_led"},
            audio_config_loader=lambda _task: {
                "tts_voice": "mm_female_1",
                "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
                "tts_voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
                "tts_voiceover_ready": True,
                "source_audio_policy": "replace",
            },
            voice_execution_state_loader=lambda _task, _settings: {
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "deliverable_audio_done": True,
                "dub_current": True,
                "dub_current_reason": "ready",
                "requested_voice": "mm_female_1",
                "resolved_voice": "mm_female_1",
                "actual_provider": "test",
            },
            persisted_audio_state_loader=lambda _task_id, _task: {
                "exists": True,
                "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
            },
            scene_pack_info_loader=lambda _task, _task_id: {"exists": False, "status": "running"},
            subtitles_text_loader=lambda _task_id, _task: "stub subtitle",
            presentation_aggregates_loader=lambda *_args, **_kwargs: (
                {
                    "final_exists": True,
                    "final_url": f"/v1/tasks/{task_id}/final",
                    "audio_exists": True,
                    "audio_url": f"/v1/tasks/{task_id}/audio_mm",
                    "subtitle_exists": True,
                    "subtitle_url": f"/v1/tasks/{task_id}/subs_mm",
                    "compose_input": {"mode": "direct", "ready": True, "blocked": False, "derive_failed": False},
                    "compose_input_mode": "direct",
                    "compose_input_ready": True,
                    "compose_input_blocked": False,
                    "compose_input_derive_failed": False,
                    "compose_input_reason": None,
                    "audio_lane": {"tts_voiceover_exists": True, "source_audio_preserved": False, "bgm_configured": False, "no_tts": False},
                    "selected_compose_route": {"name": "tts_replace_route"},
                },
                {
                    "dub_status": "done",
                    "audio_ready": True,
                    "audio_ready_reason": "ready",
                    "dub_current": True,
                    "dub_current_reason": "ready",
                    "compose_status": "done",
                    "compose_reason": "ready",
                    "selected_compose_route": "tts_replace_route",
                    "compose_allowed": True,
                    "compose_input_ready": True,
                    "compose_execute_allowed": True,
                    "requires_recompose": False,
                },
                {
                    "last_successful_output_available": True,
                    "current_attempt_failed": False,
                    "show_previous_final_as_primary": False,
                    "recommended_next_action": "current final is ready",
                },
            ),
            resolve_final_url_loader=lambda _task_id, _payload: f"/v1/tasks/{task_id}/final",
        ),
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/publish_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["media"]["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert data["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("line") or {}).get("line_id") == "hot_follow_line"
    assert (data.get("line") or {}).get("sop_profile_ref") == "docs/runbooks/hot_follow_sop.md"
    assert data["composed_ready"] is True
    assert data["composed_reason"] == "ready"
    assert data.get("ready_gate", {}).get("publish_ready") is True
    assert data["scene_pack_pending_reason"] in {"scenes.running", "scenes.not_ready", "scenes.failed"}
    assert (data.get("deliverables", {}).get("final_mp4") or {}).get("url") == data["final_video_url"]

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"


def test_build_hot_follow_publish_hub_reprojects_final_ready_truth_from_authoritative_state():
    task_id = "hf-publish-hub-final-contradiction-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "pending",
        },
    )

    def _pipeline_state(_task, step, *, composed=None):
        table = {
            "subtitles": ("done", "subtitle=ready"),
            "audio": ("done", "audio=ready"),
            "compose": ("done", "final=ready"),
        }
        return table[step]

    payload = task_view_module.build_hot_follow_publish_hub(
        task_id,
        repo=repo,
        publish_payload_builder=lambda _task: {
            "task_id": task_id,
            "media": {
                "final_video_url": f"/v1/tasks/{task_id}/final",
                "final_url": f"/v1/tasks/{task_id}/final",
            },
            "final_url": f"/v1/tasks/{task_id}/final",
            "final_video_url": f"/v1/tasks/{task_id}/final",
            "deliverables": {
                "final_mp4": {"label": "final.mp4", "url": f"/v1/tasks/{task_id}/final"},
            },
            "composed_ready": False,
            "composed_reason": "missing_voiceover",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final"},
            "historical_final": {"exists": False},
            "final_fresh": True,
            "final_stale_reason": None,
            "audio": {
                "status": "pending",
                "audio_ready": False,
                "audio_ready_reason": "audio_not_ready",
            },
            "subtitles": {
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
            },
        },
        backfill_compose_done=lambda *_args, **_kwargs: False,
        settings_loader=lambda: object(),
        subtitle_lane_loader=lambda _task_id, _task: {
            "primary_editable_text": "stub subtitle",
            "primary_editable_format": "srt",
            "subtitle_ready": True,
            "subtitle_ready_reason": "ready",
            "subtitle_artifact_exists": True,
            "actual_burn_subtitle_source": "mm.srt",
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
            "dub_input_text": "stub subtitle",
        },
        composed_state_loader=lambda _task, _task_id: {
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {
                "exists": True,
                "fresh": True,
                "url": f"/v1/tasks/{task_id}/final",
                "asset_version": "final-v1",
            },
            "historical_final": {"exists": False},
            "final_fresh": True,
            "final_stale_reason": None,
        },
        pipeline_state_loader=_pipeline_state,
        dual_channel_state_loader=lambda *_args, **_kwargs: {"content_mode": "voice_led"},
        audio_config_loader=lambda _task: {
            "tts_voice": "mm_female_1",
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
            "tts_voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
            "tts_voiceover_ready": True,
            "source_audio_policy": "replace",
        },
        voice_execution_state_loader=lambda _task, _settings: {
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "deliverable_audio_done": True,
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "mm_female_1",
            "actual_provider": "test",
        },
        persisted_audio_state_loader=lambda _task_id, _task: {
            "exists": True,
            "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
        },
        scene_pack_info_loader=lambda _task, _task_id: {"exists": False, "status": "pending"},
        subtitles_text_loader=lambda _task_id, _task: "stub subtitle",
        presentation_aggregates_loader=lambda *_args, **_kwargs: (
            {
                "final_exists": True,
                "final_url": f"/v1/tasks/{task_id}/final",
                "audio_exists": True,
                "audio_url": f"/v1/tasks/{task_id}/audio_mm",
                "subtitle_exists": True,
                "subtitle_url": f"/v1/tasks/{task_id}/subs_mm",
                "compose_input": {"mode": "direct", "ready": True, "blocked": False, "derive_failed": False},
                "compose_input_mode": "direct",
                "compose_input_ready": True,
                "compose_input_blocked": False,
                "compose_input_derive_failed": False,
                "compose_input_reason": None,
                "audio_lane": {"tts_voiceover_exists": True, "source_audio_preserved": False, "bgm_configured": False, "no_tts": False},
                "selected_compose_route": {"name": "tts_replace_route"},
            },
            {
                "dub_status": "done",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "compose_status": "done",
                "compose_reason": "ready",
                "selected_compose_route": "tts_replace_route",
                "compose_allowed": True,
                "compose_input_ready": True,
                "compose_execute_allowed": True,
                "requires_recompose": False,
            },
            {
                "last_successful_output_available": True,
                "current_attempt_failed": False,
                "show_previous_final_as_primary": False,
                "recommended_next_action": "current final is ready",
            },
        ),
        resolve_final_url_loader=lambda _task_id, _payload: f"/v1/tasks/{task_id}/final",
    )

    assert payload["final"]["exists"] is True
    assert payload["composed_ready"] is True
    assert payload["composed_reason"] == "ready"
    assert payload["compose_status"] == "done"
    assert payload["audio"]["audio_ready"] is True
    assert payload["ready_gate"]["compose_ready"] is True
    assert payload["ready_gate"]["publish_ready"] is True
    assert payload["ready_gate"]["audio_ready"] is True
    assert payload["final_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert (payload["deliverables"]["final_mp4"] or {}).get("url", "").endswith(f"/v1/tasks/{task_id}/final")


def test_generic_v1_publish_hub_uses_hot_follow_projection_builder(monkeypatch):
    task_id = "hf-publish-hub-generic-route-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "id": task_id,
            "kind": "hot_follow",
            "status": "processing",
        },
    )

    monkeypatch.setattr(
        tasks_router,
        "build_hot_follow_publish_hub",
        lambda current_task_id, repo=None: {
            "task_id": current_task_id,
            "composed_ready": True,
            "ready_gate": {"publish_ready": True},
            "line": {"line_id": "hot_follow_line"},
        },
    )

    app = FastAPI()
    app.include_router(tasks_router.pages_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/v1/tasks/{task_id}/publish_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["task_id"] == task_id
    assert data["composed_ready"] is True
    assert data["ready_gate"]["publish_ready"] is True
    assert data["line"]["line_id"] == "hot_follow_line"
