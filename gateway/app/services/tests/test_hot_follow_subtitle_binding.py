from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import subtitle_helpers
from gateway.app.services import task_view_presenters
from gateway.app.services import task_view_workbench_contract
from gateway.app.services import compose_service as compose_module
from gateway.app.services.compose_service import (
    ComposeResult,
    CompositionService,
    _ComposeInputs,
    _WorkspaceFiles,
    _with_live_hot_follow_subtitle_currentness,
    compose_subtitle_vf,
    optimize_hot_follow_subtitle_layout_srt,
)
from gateway.app.utils.pipeline_config import parse_pipeline_config


def _hash16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _compose_inputs() -> _ComposeInputs:
    return _ComposeInputs(
        video_key="video-key",
        audio_key="audio-key",
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
    )


def test_authority_false_subtitle_lane_does_not_emit_burn_source(monkeypatch):
    target_text = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
    target_currentness = {
        "target_subtitle_current": False,
        "target_subtitle_current_reason": "target_subtitle_not_authoritative",
        "target_subtitle_authoritative_source": False,
        "target_subtitle_source_copy": False,
    }
    task = {
        "task_id": "hf-url-authority-false",
        "kind": "hot_follow",
        "target_lang": "vi",
        "vi_srt_path": "deliver/tasks/hf-url-authority-false/vi.srt",
        "final_source_subtitle_storage_key": "deliver/tasks/hf-url-authority-false/final/vi.srt",
    }

    monkeypatch.setattr(subtitle_helpers, "hf_load_origin_subtitles_text", lambda _task: "source")
    monkeypatch.setattr(subtitle_helpers, "hf_load_normalized_source_text", lambda *_args, **_kwargs: "source")
    monkeypatch.setattr(subtitle_helpers, "hf_load_subtitles_text", lambda *_args, **_kwargs: target_text)
    monkeypatch.setattr(subtitle_helpers, "hf_target_subtitle_currentness_state", lambda *_args, **_kwargs: target_currentness)
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: True)

    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "source")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "source")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda *_args, **_kwargs: target_text)
    monkeypatch.setattr(hf_router, "_hf_target_subtitle_currentness_state", lambda *_args, **_kwargs: target_currentness)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)

    service_lane = subtitle_helpers.hf_subtitle_lane_state("hf-url-authority-false", dict(task))
    router_lane = hf_router._hf_subtitle_lane_state("hf-url-authority-false", dict(task))

    for lane in (service_lane, router_lane):
        assert lane["target_subtitle_authoritative_source"] is False
        assert lane["target_subtitle_current"] is False
        assert lane["actual_burn_subtitle_source"] is None
        assert lane["dub_input_text"] == ""


def test_router_subtitle_wrappers_delegate_to_service_consumers(monkeypatch):
    subtitle_sentinel = {
        "subtitle_ready": False,
        "hot_follow_process_state": {"lane_state": "voice_led_tts_route"},
    }
    route_sentinel = {
        "content_mode": "voice_led",
        "hot_follow_process_state": subtitle_sentinel["hot_follow_process_state"],
    }

    monkeypatch.setattr(hf_router, "_svc_hf_subtitle_lane_state", lambda task_id, task: subtitle_sentinel)
    monkeypatch.setattr(
        hf_router,
        "_svc_hf_dual_channel_state",
        lambda task_id, task, subtitle_lane, *, subtitles_step_done=True: route_sentinel,
    )

    assert hf_router._hf_subtitle_lane_state("hf-router-consumer", {"kind": "hot_follow"}) is subtitle_sentinel
    assert (
        hf_router._hf_dual_channel_state(
            "hf-router-consumer",
            {"kind": "hot_follow"},
            subtitle_sentinel,
        )
        is route_sentinel
    )


def test_subtitle_helper_sources_are_canonical_process_outputs(monkeypatch):
    target_text = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
    monkeypatch.setattr(subtitle_helpers, "hf_load_origin_subtitles_text", lambda _task: "source")
    monkeypatch.setattr(subtitle_helpers, "hf_load_normalized_source_text", lambda *_args, **_kwargs: "source")
    monkeypatch.setattr(subtitle_helpers, "hf_load_subtitles_text", lambda *_args, **_kwargs: target_text)
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: True)
    monkeypatch.setattr(
        subtitle_helpers,
        "hf_target_subtitle_currentness_state",
        lambda *_args, **_kwargs: {
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
            "target_subtitle_authoritative_source": True,
            "target_subtitle_source_copy": False,
        },
    )

    lane = subtitle_helpers.hf_subtitle_lane_state(
        "hf-helper-consumer",
        {
            "task_id": "hf-helper-consumer",
            "kind": "hot_follow",
            "target_lang": "vi",
            "vi_srt_path": "deliver/tasks/hf-helper-consumer/vi.srt",
        },
    )

    process_state = lane["hot_follow_process_state"]
    assert process_state["target_subtitle_authoritative_current"] is True
    assert process_state["actual_burn_subtitle_source"] == "vi.srt"
    assert lane["actual_burn_subtitle_source"] == process_state["actual_burn_subtitle_source"]
    assert lane["current_subtitle_source"] == process_state["current_subtitle_source"]


def test_subtitle_helper_no_dub_terminal_comes_from_process_reducer(monkeypatch):
    monkeypatch.setattr(subtitle_helpers, "hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(subtitle_helpers, "hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(subtitle_helpers, "hf_load_subtitles_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: False)

    lane = subtitle_helpers.hf_subtitle_lane_state(
        "hf-helper-no-dub",
        {
            "task_id": "hf-helper-no-dub",
            "kind": "hot_follow",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
        },
    )

    process_state = lane["hot_follow_process_state"]
    route = subtitle_helpers.hf_dual_channel_state("hf-helper-no-dub", {"kind": "hot_follow"}, lane)
    assert process_state["lane_state"] == "no_dub_no_tts_route"
    assert process_state["subtitle_process_state"] == "subtitle_skipped_terminal"
    assert route["hot_follow_process_state"] is process_state
    assert route["content_mode"] == "silent_candidate"


class _FakeStorage:
    def __init__(self, subtitle_text: str):
        self.subtitle_text = subtitle_text

    def download_file(self, key: str, destination_path: str) -> None:
        path = Path(destination_path)
        if key == "video-key":
            path.write_bytes(b"video-bytes")
            return
        if key == "audio-key":
            path.write_bytes(b"audio-bytes")
            return
        if key == "subtitle-key":
            path.write_text(self.subtitle_text, encoding="utf-8")
            return
        raise AssertionError(f"unexpected key {key}")

    def upload_file(self, file_path: str, key: str, content_type: str | None = None) -> str:
        _ = (file_path, content_type)
        return key


class _Repo:
    def __init__(self, row: dict):
        self.row = dict(row)

    def get(self, task_id):
        if task_id != self.row.get("task_id"):
            return None
        return dict(self.row)

    def upsert(self, task_id, fields):
        assert task_id == self.row.get("task_id")
        self.row.update(fields or {})
        return dict(self.row)


def test_sync_saved_target_subtitle_reuploads_when_existing_mm_srt_differs(monkeypatch, tmp_path):
    uploads: list[tuple[str, str]] = []

    class _Workspace:
        def __init__(self, _task_id: str, target_lang: str | None = None):
            _ = target_lang
            self.mm_srt_path = tmp_path / "subtitles" / "mm.srt"

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        uploads.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_srt_to_txt", lambda _text: "")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"content_length": 12})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _head: (12, None))
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda _key: b"old subtitle")
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)

    task = {"task_id": "hf-bind-1", "mm_srt_path": "deliver/tasks/hf-bind-1/mm.srt"}
    saved_text = "new 30s subtitle payload"

    synced_key = hf_router._hf_sync_saved_target_subtitle_artifact("hf-bind-1", task, saved_text)

    assert synced_key == "deliver/tasks/hf-bind-1/mm.srt"
    assert uploads == [("mm.srt", saved_text)]
    assert task["mm_srt_path"] == "deliver/tasks/hf-bind-1/mm.srt"


def test_sync_saved_target_subtitle_reuploads_vi_artifact_for_vi_task(monkeypatch, tmp_path):
    uploads: list[tuple[str, str]] = []

    class _Workspace:
        def __init__(self, _task_id: str, target_lang: str | None = None):
            assert target_lang == "vi"
            self.mm_srt_path = tmp_path / "subtitles" / "vi.srt"

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        uploads.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_srt_to_txt", lambda _text: "")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)

    task = {"task_id": "hf-bind-vi", "target_lang": "vi", "mm_srt_path": "deliver/tasks/hf-bind-vi/vi.srt"}
    saved_text = "new 30s vietnamese subtitle payload"

    synced_key = hf_router._hf_sync_saved_target_subtitle_artifact("hf-bind-vi", task, saved_text)

    assert synced_key == "deliver/tasks/hf-bind-vi/vi.srt"
    assert uploads == [("vi.srt", saved_text)]
    assert task["mm_srt_path"] == "deliver/tasks/hf-bind-vi/vi.srt"


def test_save_authoritative_target_subtitle_delegates_to_single_owner(monkeypatch):
    repo = _Repo({"task_id": "hf-owner", "kind": "hot_follow", "target_lang": "vi"})
    seen: dict[str, object] = {}

    def _persist(task_id, task, **kwargs):
        seen["task_id"] = task_id
        seen["task"] = dict(task)
        seen["kwargs"] = dict(kwargs)
        return {"task_id": task_id, "subtitles_status": "ready"}

    monkeypatch.setattr(hf_router, "persist_hot_follow_authoritative_target_subtitle", _persist)

    saved = hf_router._hf_save_authoritative_target_subtitle(
        "hf-owner",
        repo.get("hf-owner"),
        text="1\n00:00:00,000 --> 00:00:02,000\nXin chao\n",
        text_mode="manual_edit",
        repo=repo,
    )

    assert saved["subtitles_status"] == "ready"
    assert seen["task_id"] == "hf-owner"
    assert dict(seen["kwargs"])["text_mode"] == "manual_edit"


def test_save_authoritative_target_subtitle_rejects_source_copy_before_success(monkeypatch):
    repo = _Repo(
        {
            "task_id": "hf-source-copy",
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-source-copy/origin.srt",
        }
    )
    source_srt = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"

    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: source_srt)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(
        hf_router,
        "_hf_sync_saved_target_subtitle_artifact",
        lambda *_args, **_kwargs: pytest.fail("source-copy subtitle must not persist authoritative success"),
    )

    with pytest.raises(HTTPException) as exc_info:
        hf_router._hf_save_authoritative_target_subtitle(
            "hf-source-copy",
            repo.get("hf-source-copy"),
            text=source_srt,
            text_mode="manual_edit",
            repo=repo,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["reason"] == "target_subtitle_source_copy"


def test_resolve_target_srt_key_prefers_vi_artifact_before_legacy_mm_fallback(monkeypatch):
    monkeypatch.setattr(
        hf_router,
        "_hf_sync_saved_target_subtitle_artifact",
        lambda _task_id, _task, saved_text=None: "deliver/tasks/hf-bind-vi/mm.srt",
    )
    monkeypatch.setattr(
        hf_router,
        "object_exists",
        lambda key: str(key) in {
            "deliver/tasks/hf-bind-vi/vi.srt",
            "deliver/tasks/hf-bind-vi/mm.srt",
        },
    )

    task = {
        "task_id": "hf-bind-vi",
        "target_lang": "vi",
        "target_subtitle_current": True,
        "mm_srt_path": "deliver/tasks/hf-bind-vi/vi.srt",
    }

    resolved_key = hf_router._resolve_target_srt_key(task, "hf-bind-vi", "vi")

    assert resolved_key == "deliver/tasks/hf-bind-vi/vi.srt"


def test_resolve_target_srt_key_blocks_vi_compose_when_target_subtitle_not_current(monkeypatch):
    monkeypatch.setattr(
        hf_router,
        "_hf_subtitle_lane_state",
        lambda _task_id, _task: {"target_subtitle_current": False},
    )

    task = {
        "task_id": "hf-bind-vi-stale",
        "target_lang": "vi",
        "mm_srt_path": "deliver/tasks/hf-bind-vi-stale/vi.srt",
    }

    resolved_key = hf_router._resolve_target_srt_key(task, "hf-bind-vi-stale", "vi")

    assert resolved_key is None


def test_subtitle_lane_keeps_target_editor_empty_when_only_origin_exists(monkeypatch):
    store = {
        "deliver/tasks/hf-origin-only/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\n\xe4\xbd\xa0\xe5\xa5\xbd\n",
    }

    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(subtitle_helpers, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-origin-only",
        {
            "task_id": "hf-origin-only",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-origin-only/origin.srt",
        },
    )

    assert lane["raw_source_text"]
    assert lane["parse_source_text"] == lane["raw_source_text"]
    assert lane["parse_source_role"] == "subtitle_source_helper"
    assert lane["parse_source_authoritative_for_target"] is False
    assert lane["edited_text"] == ""
    assert lane["primary_editable_text"] == ""
    assert lane["srt_text"] == ""
    assert lane["dub_input_text"] == ""
    assert lane["dub_input_source"] is None
    assert lane["subtitle_ready"] is False


def test_subtitle_lane_does_not_treat_timing_only_target_artifact_as_existing_truth(monkeypatch):
    store = {
        "deliver/tasks/hf-empty-target/mm.srt": b"1\n00:00:00,000 --> 00:00:02,000\n\n",
    }

    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(subtitle_helpers, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-empty-target",
        {
            "task_id": "hf-empty-target",
            "target_lang": "my",
            "mm_srt_path": "deliver/tasks/hf-empty-target/mm.srt",
        },
    )

    assert lane["srt_text"] == ""
    assert lane["primary_editable_text"] == ""
    assert lane["subtitle_artifact_exists"] is False
    assert lane["subtitle_ready"] is False
    assert lane["target_subtitle_current"] is False
    assert lane["target_subtitle_current_reason"] == "subtitle_missing"
    assert lane["dub_input_text"] == ""


def test_subtitle_lane_reads_local_authoritative_target_when_storage_copy_missing(monkeypatch, tmp_path):
    task_id = "hf-local-authoritative-target"
    target_srt = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
    origin_srt = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"

    class _Workspace:
        def __init__(self, _task_id: str, target_lang: str | None = None):
            _ = target_lang
            assert _task_id == task_id
            self.mm_srt_path = tmp_path / "subtitles" / "vi.srt"
            self.origin_srt_path = tmp_path / "subs" / "origin.srt"

    workspace = _Workspace(task_id, "vi")
    workspace.mm_srt_path.parent.mkdir(parents=True, exist_ok=True)
    workspace.origin_srt_path.parent.mkdir(parents=True, exist_ok=True)
    workspace.mm_srt_path.write_text(target_srt, encoding="utf-8")
    workspace.origin_srt_path.write_text(origin_srt, encoding="utf-8")

    monkeypatch.setattr(subtitle_helpers, "Workspace", _Workspace)
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: tmp_path / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        task_id,
        {
            "task_id": task_id,
            "target_lang": "vi",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "mm_srt_path": f"deliver/tasks/{task_id}/vi.srt",
        },
    )

    assert "你好" in lane["raw_source_text"]
    assert "Xin chao" in lane["edited_text"]
    assert lane["srt_text"] == lane["edited_text"]
    assert lane["primary_editable_text"] == lane["edited_text"]
    assert lane["subtitle_artifact_exists"] is True
    assert lane["target_subtitle_authoritative_source"] is True
    assert lane["target_subtitle_current"] is True
    assert lane["target_subtitle_current_reason"] == "ready"
    assert lane["subtitle_ready"] is True
    assert "Xin chao" in lane["dub_input_text"]
    assert lane["dub_input_source"] == "target_subtitle"


def test_subtitle_lane_preserves_translation_incomplete_reason_over_generic_missing(monkeypatch):
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-target-translation-incomplete",
        {
            "task_id": "hf-target-translation-incomplete",
            "target_lang": "vi",
            "mm_srt_path": "deliver/tasks/hf-target-translation-incomplete/vi.srt",
            "pipeline_config": {"translation_incomplete": "true"},
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
        },
    )

    assert lane["edited_text"] == ""
    assert lane["subtitle_ready"] is False
    assert lane["subtitle_ready_reason"] == "target_subtitle_translation_incomplete"
    assert lane["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert lane["dub_input_text"] == ""


def test_sync_saved_target_subtitle_artifact_refuses_semantically_empty_srt(monkeypatch):
    monkeypatch.setattr(hf_router, "upload_task_artifact", lambda *_args, **_kwargs: pytest.fail("empty target subtitle must not upload"))
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)

    task = {
        "task_id": "hf-empty-sync",
        "kind": "hot_follow",
        "mm_srt_path": "deliver/tasks/hf-empty-sync/mm.srt",
    }

    key = hf_router._hf_sync_saved_target_subtitle_artifact(
        "hf-empty-sync",
        task,
        "1\n00:00:00,000 --> 00:00:02,000\n\n",
    )

    assert key is None
    assert task["mm_srt_path"] == "deliver/tasks/hf-empty-sync/mm.srt"


def test_translate_subtitles_helper_only_does_not_persist_target_subtitle(monkeypatch):
    task_id = "hf-helper-translate-only"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
        }
    )

    monkeypatch.setattr(
        hf_router,
        "translate_segments_with_gemini",
        lambda segments, target_lang: {1: "cai nay"},
    )
    monkeypatch.setattr(
        hf_router,
        "_hf_sync_saved_target_subtitle_artifact",
        lambda *_args, **_kwargs: pytest.fail("helper-only translation must not persist target subtitle"),
    )

    data = hf_router.translate_hot_follow_subtitles(
        task_id,
        hf_router.HotFollowTranslateRequest(text="this", target_lang="vi", input_source="helper_only_text"),
        repo=repo,
    )

    assert data["input_source"] == "helper_only_text"
    assert data["persisted"] is False
    assert data["translated_text"] == "cai nay"
    saved = repo.get(task_id) or {}
    assert saved.get("mm_srt_path") is None
    assert saved["subtitle_helper_status"] == "ready"
    assert saved["subtitle_helper_input_text"] == "this"
    assert saved["subtitle_helper_translated_text"] == "cai nay"
    assert saved["subtitle_helper_target_lang"] == "vi"
    assert saved.get("subtitle_helper_error_reason") is None


def test_translate_subtitles_helper_failure_preserves_authoritative_outputs(monkeypatch):
    task_id = "hf-helper-failure-mainline-safe"
    target_srt = "deliver/tasks/hf-helper-failure-mainline-safe/vi.srt"
    audio_key = "deliver/tasks/hf-helper-failure-mainline-safe/audio_vi.mp3"
    final_key = "deliver/tasks/hf-helper-failure-mainline-safe/final.mp4"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "mm_srt_path": target_srt,
            "mm_audio_key": audio_key,
            "final_video_key": final_key,
            "subtitles_status": "ready",
            "dub_status": "ready",
            "compose_status": "ready",
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
            "dub_current": True,
            "compose_ready": True,
            "publish_ready": True,
        }
    )

    def _raise_resource_exhausted(*_args, **_kwargs):
        raise hf_router.GeminiSubtitlesError(
            'Gemini HTTP 429: {"error":{"status":"RESOURCE_EXHAUSTED","message":"quota exhausted"}}'
        )

    monkeypatch.setattr(hf_router, "translate_segments_with_gemini", _raise_resource_exhausted)
    monkeypatch.setattr(
        hf_router,
        "_hf_sync_saved_target_subtitle_artifact",
        lambda *_args, **_kwargs: pytest.fail("helper failure must not sync target subtitle artifacts"),
    )

    with pytest.raises(HTTPException) as exc_info:
        hf_router.translate_hot_follow_subtitles(
            task_id,
            hf_router.HotFollowTranslateRequest(text="helper candidate", target_lang="vi", input_source="helper_only_text"),
            repo=repo,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["reason"] == "helper_translate_provider_exhausted"
    saved = repo.get(task_id) or {}
    assert saved["subtitle_helper_status"] == "failed"
    assert saved["subtitle_helper_error_reason"] == "helper_translate_provider_exhausted"
    assert saved["subtitle_helper_input_text"] == "helper candidate"
    assert saved["subtitle_helper_target_lang"] == "vi"
    assert saved["mm_srt_path"] == target_srt
    assert saved["mm_audio_key"] == audio_key
    assert saved["final_video_key"] == final_key
    assert saved["subtitles_status"] == "ready"
    assert saved["dub_status"] == "ready"
    assert saved["compose_status"] == "ready"
    assert saved["target_subtitle_current"] is True
    assert saved["dub_current"] is True
    assert saved["compose_ready"] is True
    assert saved["publish_ready"] is True


def test_translate_subtitles_helper_repeat_on_already_current_task_is_idempotent_success(monkeypatch):
    task_id = "hf-helper-repeat-already-current"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "subtitles_status": "ready",
            "dub_status": "ready",
            "compose_status": "ready",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "retry later",
            "subtitle_helper_input_text": "this is you",
            "subtitle_helper_translated_text": "đây là bạn",
            "subtitle_helper_target_lang": "vi",
            "mm_srt_path": f"deliver/tasks/{task_id}/vi.srt",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_vi.mp3",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "publish_ready": True,
            "compose_ready": True,
            "dub_current": True,
        }
    )

    monkeypatch.setattr(
        hf_router,
        "translate_segments_with_gemini",
        lambda *_args, **_kwargs: pytest.fail("idempotent repeat must not invoke helper provider"),
    )

    data = hf_router.translate_hot_follow_subtitles(
        task_id,
        hf_router.HotFollowTranslateRequest(text="this is you", target_lang="vi", input_source="helper_only_text"),
        repo=repo,
    )

    assert data["result"] == "resolved_with_warning"
    assert data["single_flight"] == "noop_cached"
    assert data["translated_text"] == "đây là bạn"
    assert data["helper_translation"]["status"] == "helper_resolved_with_retryable_provider_warning"
    assert data["helper_translation"]["warning_only"] is True
    saved = repo.get(task_id) or {}
    assert saved["target_subtitle_current"] is True
    assert saved["target_subtitle_authoritative_source"] is True
    assert saved["publish_ready"] is True


def test_translate_subtitles_helper_repeat_dedupes_same_in_flight_request(monkeypatch):
    task_id = "hf-helper-repeat-dedupe"
    text = "this is you"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "subtitles_status": "ready",
            "dub_status": "ready",
            "compose_status": "ready",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "retry later",
            "subtitle_helper_input_text": text,
            "subtitle_helper_translated_text": "đây là bạn",
            "subtitle_helper_target_lang": "vi",
            "mm_srt_path": f"deliver/tasks/{task_id}/vi.srt",
            "mm_audio_key": f"deliver/tasks/{task_id}/audio_vi.mp3",
            "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            "publish_ready": True,
            "compose_ready": True,
            "dub_current": True,
        }
    )

    fingerprint = hf_router._hf_helper_translate_request_fingerprint(
        task_id=task_id,
        source_text=text,
        target_lang="vi",
        input_source="helper_only_text",
    )
    lock = hf_router._hf_helper_translate_request_lock(fingerprint)
    assert lock.acquire(blocking=False) is True
    try:
        monkeypatch.setattr(
            hf_router,
            "translate_segments_with_gemini",
            lambda *_args, **_kwargs: pytest.fail("deduped repeat must not invoke helper provider"),
        )
        data = hf_router.translate_hot_follow_subtitles(
            task_id,
            hf_router.HotFollowTranslateRequest(text=text, target_lang="vi", input_source="helper_only_text"),
            repo=repo,
        )
    finally:
        lock.release()

    assert data["result"] == "resolved_with_warning"
    assert data["single_flight"] == "deduped_in_flight"
    assert data["helper_translation"]["status"] == "helper_resolved_with_retryable_provider_warning"
    saved = repo.get(task_id) or {}
    assert saved["target_subtitle_current"] is True
    assert saved["target_subtitle_authoritative_source"] is True


def test_helper_translation_projection_stays_helper_layer_only():
    section = task_view_workbench_contract._subtitles_section(
        task={"task_id": "hf-helper-projection", "subtitles_error": None},
        subtitle_lane={
            "helper_translate_status": "helper_output_resolved",
            "helper_translate_output_state": "helper_output_resolved",
            "helper_translate_provider_health": "provider_ok",
            "helper_translate_composite_state": None,
            "helper_translate_failed": False,
            "helper_translate_provider": "gemini",
            "helper_translate_input_text": "helper candidate",
            "helper_translate_translated_text": "ung vien ho tro",
            "helper_translate_target_lang": "vi",
            "primary_editable_text": "1\n00:00:00,000 --> 00:00:01,000\nmain subtitle\n",
            "primary_editable_format": "srt",
            "dub_input_text": "main subtitle",
            "dub_input_source": "target_subtitle",
            "subtitle_ready": True,
            "target_subtitle_current": True,
        },
        subtitles_state="ready",
        origin_text="source subtitle",
        subtitles_text="target subtitle",
        normalized_source_text="normalized source",
    )

    assert section["helper_translation"] == {
        "status": "helper_output_resolved",
        "output_state": "helper_output_resolved",
        "provider_health": "provider_ok",
        "composite_state": None,
        "failed": False,
        "reason": None,
        "message": None,
        "provider": "gemini",
        "visibility": None,
        "retryable": False,
        "terminal": False,
        "warning_only": False,
        "input_text": "helper candidate",
        "translated_text": "ung vien ho tro",
        "target_lang": "vi",
    }
    assert "main subtitle" in section["primary_editable_text"]
    assert section["dub_input_source"] == "target_subtitle"


def test_translate_subtitles_source_lane_persists_full_target_srt(monkeypatch, tmp_path):
    task_id = "hf-source-lane-translate"
    source_srt = (
        "1\n00:00:00,000 --> 00:00:02,000\n你好\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\n再见\n"
    )
    uploads: list[tuple[str, str]] = []

    class _Workspace:
        def __init__(self, _task_id: str, target_lang: str | None = None):
            assert _task_id == task_id
            assert target_lang == "vi"
            self.mm_srt_path = tmp_path / "subtitles" / "vi.srt"

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        uploads.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "dub_status": "skipped",
            "dub_skip_reason": "target_subtitle_empty",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
        }
    )

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda _task_id: tmp_path / "override.srt")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(subtitle_helpers, "hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(subtitle_helpers, "hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_srt_to_txt", lambda text: "Xin chao\nTam biet")
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)
    monkeypatch.setattr(
        hf_router,
        "translate_segments_with_gemini",
        lambda segments, target_lang: {1: "Xin chao", 2: "Tam biet"},
    )

    data = hf_router.translate_hot_follow_subtitles(
        task_id,
        hf_router.HotFollowTranslateRequest(target_lang="vi", input_source="source_subtitle_lane"),
        repo=repo,
    )

    assert data["input_source"] == "source_subtitle_lane"
    assert data["persisted"] is True
    assert "00:00:00,000 --> 00:00:02,000" in data["translated_text"]
    assert "Xin chao" in data["translated_text"]
    assert "Tam biet" in data["translated_text"]
    assert uploads[0][0] == "vi.srt"
    assert "Xin chao" in uploads[0][1]
    saved = repo.get(task_id) or {}
    assert saved["mm_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["target_subtitle_current"] is True
    assert saved["target_subtitle_current_reason"] == "ready"
    assert saved["dub_status"] == "pending"
    assert saved.get("dub_skip_reason") is None


def test_translate_subtitles_source_lane_failure_records_helper_telemetry_only(monkeypatch, tmp_path):
    task_id = "hf-source-lane-provider-failure"
    source_srt = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": f"deliver/tasks/{task_id}/origin.srt",
            "subtitles_status": "running",
            "dub_status": "skipped",
            "dub_skip_reason": "target_subtitle_empty",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
        }
    )

    def _raise_resource_exhausted(*_args, **_kwargs):
        raise hf_router.GeminiSubtitlesError(
            'Gemini HTTP 429: {"error":{"status":"RESOURCE_EXHAUSTED","message":"quota exhausted"}}'
        )

    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda _task_id: tmp_path / "override.srt")
    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(subtitle_helpers, "hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(subtitle_helpers, "hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "translate_segments_with_gemini", _raise_resource_exhausted)

    with pytest.raises(HTTPException) as exc_info:
        hf_router.translate_hot_follow_subtitles(
            task_id,
            hf_router.HotFollowTranslateRequest(target_lang="vi", input_source="source_subtitle_lane"),
            repo=repo,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["reason"] == "helper_translate_provider_exhausted"
    saved = repo.get(task_id) or {}
    assert saved["subtitle_helper_status"] == "failed"
    assert saved["subtitle_helper_error_reason"] == "helper_translate_provider_exhausted"
    assert saved["subtitle_helper_provider"] == "gemini"
    assert saved["subtitle_helper_input_text"] == source_srt.strip()
    assert saved["subtitles_status"] == "running"
    assert "subtitles_error_reason" not in saved
    assert "target_subtitle_current" not in saved
    assert "target_subtitle_current_reason" not in saved
    assert "compose_ready" not in saved
    assert "publish_ready" not in saved

    lane = hf_router._hf_subtitle_lane_state(task_id, saved)
    assert lane["helper_translate_failed"] is True
    assert lane["subtitle_ready"] is False
    assert lane["subtitle_ready_reason"] == "helper_translate_provider_exhausted"
    assert lane["target_subtitle_current_reason"] == "helper_translate_provider_exhausted"
    assert lane["dub_input_text"] == ""

    ui = task_view_presenters.collect_hot_follow_workbench_ui(
        saved,
        settings=None,
        subtitle_lane_loader=lambda *_args, **_kwargs: lane,
        dual_channel_state_loader=lambda *_args, **_kwargs: {"content_mode": "silent_candidate"},
        source_audio_lane_loader=lambda *_args, **_kwargs: {},
        screen_text_candidate_loader=lambda *_args, **_kwargs: {},
        voice_execution_state_loader=lambda *_args, **_kwargs: {},
        pipeline_state_loader=lambda *_args, **_kwargs: ("failed", {}),
        object_exists_fn=lambda _key: False,
        source_audio_semantics_loader=lambda *_args, **_kwargs: {},
    )
    assert ui["no_dub"] is False
    assert ui["no_dub_reason"] is None


def test_translate_subtitles_source_lane_failure_preserves_current_target_subtitle(monkeypatch):
    task_id = "hf-source-lane-provider-failure-current-target"
    source_srt = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
    target_srt = f"deliver/tasks/{task_id}/vi.srt"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
            "mm_srt_path": target_srt,
            "subtitles_status": "failed",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "dub_status": "skipped",
            "dub_skip_reason": "target_subtitle_empty",
            "pipeline_config": {"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
            "publish_ready": True,
        }
    )

    def _raise_resource_exhausted(*_args, **_kwargs):
        raise hf_router.GeminiSubtitlesError(
            'Gemini HTTP 429: {"error":{"status":"RESOURCE_EXHAUSTED","message":"quota exhausted"}}'
        )

    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: source_srt)
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "translate_segments_with_gemini", _raise_resource_exhausted)
    monkeypatch.setattr(
        hf_router,
        "_hf_subtitle_lane_state",
        lambda *_args, **_kwargs: {
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
            "edited_text": "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n",
        },
    )

    with pytest.raises(HTTPException):
        hf_router.translate_hot_follow_subtitles(
            task_id,
            hf_router.HotFollowTranslateRequest(target_lang="vi", input_source="source_subtitle_lane"),
            repo=repo,
        )

    saved = repo.get(task_id) or {}
    assert saved["subtitle_helper_status"] == "failed"
    assert saved["subtitle_helper_error_reason"] == "helper_translate_provider_exhausted"
    assert saved["subtitles_status"] == "failed"
    assert saved["target_subtitle_current"] is True
    assert saved["target_subtitle_authoritative_source"] is True
    assert saved["target_subtitle_current_reason"] == "ready"
    assert saved["publish_ready"] is True
    assert saved["dub_status"] == "skipped"
    assert saved.get("dub_skip_reason") == "target_subtitle_empty"
    pipeline = parse_pipeline_config(saved.get("pipeline_config"))
    assert pipeline["no_dub"] == "true"
    assert pipeline["dub_skip_reason"] == "target_subtitle_empty"


def test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty(monkeypatch, tmp_path):
    task_id = "hf-source-lane-normalized"
    normalized_srt = (
        "1\n00:00:00,000 --> 00:00:02,000\n完整中文来源\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\n第二句\n"
    )
    uploads: list[tuple[str, str]] = []

    class _Workspace:
        def __init__(self, _task_id: str, target_lang: str | None = None):
            assert _task_id == task_id
            assert target_lang == "vi"
            self.mm_srt_path = tmp_path / "subtitles" / "vi.srt"

    def _fake_upload(_task, local_path, artifact_name, task_id=None, **_kwargs):
        uploads.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "target_lang": "vi",
        }
    )

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda _task_id: tmp_path / "override-normalized.srt")
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda *_args, **_kwargs: normalized_srt)
    monkeypatch.setattr(hf_router, "_srt_to_txt", lambda text: "Day du nguon tieng Trung\nCau thu hai")
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)
    monkeypatch.setattr(
        hf_router,
        "translate_segments_with_gemini",
        lambda segments, target_lang: {1: "Day du nguon tieng Trung", 2: "Cau thu hai"},
    )

    data = hf_router.translate_hot_follow_subtitles(
        task_id,
        hf_router.HotFollowTranslateRequest(target_lang="vi", input_source="source_subtitle_lane"),
        repo=repo,
    )

    assert data["input_source"] == "source_subtitle_lane"
    assert data["persisted"] is True
    assert "00:00:00,000 --> 00:00:02,000" in data["translated_text"]
    assert "Day du nguon tieng Trung" in data["translated_text"]
    assert uploads[0][0] == "vi.srt"
    saved = repo.get(task_id) or {}
    assert saved["mm_srt_path"] == f"deliver/tasks/{task_id}/vi.srt"
    assert saved["target_subtitle_current"] is True


def test_subtitle_lane_marks_preserved_source_audio_parse_as_helper_only(monkeypatch):
    store = {
        "deliver/tasks/hf-preserve-source/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\nlyric source line\n",
    }

    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(subtitle_helpers, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-preserve-source",
        {
            "task_id": "hf-preserve-source",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-preserve-source/origin.srt",
            "pipeline_config": {
                "parse_source_mode": "preserved_source_audio_helper",
                "parse_source_role": "preserved_source_audio_helper",
                "parse_source_authoritative_for_target": "false",
                "target_subtitle_authoritative": "false",
            },
        },
    )

    assert lane["raw_source_text"]
    assert lane["parse_source_text"] == lane["raw_source_text"]
    assert lane["parse_source_role"] == "preserved_source_audio_helper"
    assert lane["parse_source_authoritative_for_target"] is False
    assert lane["edited_text"] == ""
    assert lane["primary_editable_text"] == ""
    assert lane["dub_input_text"] == ""
    assert lane["subtitle_ready"] is False


def test_subtitle_parse_lane_does_not_read_from_bgm_lane(monkeypatch):
    store = {
        "deliver/tasks/hf-bgm-parse/bgm.mp3": b"not subtitle text",
    }

    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(subtitle_helpers, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-bgm-parse",
        {
            "task_id": "hf-bgm-parse",
            "target_lang": "mm",
            "config": {"bgm": {"bgm_key": "deliver/tasks/hf-bgm-parse/bgm.mp3"}},
        },
    )

    assert lane["raw_source_text"] == ""
    assert lane["normalized_source_text"] == ""
    assert lane["parse_source_text"] == ""
    assert lane["parse_source_role"] == "none"


def test_subtitle_parse_lane_does_not_read_from_preserved_source_audio_lane(monkeypatch):
    store = {
        "deliver/tasks/hf-preserve-parse/source_audio.mp3": b"not subtitle text",
    }

    monkeypatch.setattr(subtitle_helpers, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(subtitle_helpers, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(subtitle_helpers, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-preserve-parse",
        {
            "task_id": "hf-preserve-parse",
            "target_lang": "mm",
            "config": {
                "source_audio_policy": "preserve",
                "source_audio_key": "deliver/tasks/hf-preserve-parse/source_audio.mp3",
            },
        },
    )

    assert lane["raw_source_text"] == ""
    assert lane["normalized_source_text"] == ""
    assert lane["parse_source_text"] == ""
    assert lane["parse_source_role"] == "none"


def test_myanmar_dub_input_does_not_fallback_to_source_when_target_missing(monkeypatch):
    store = {
        "deliver/tasks/hf-mm-dub/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\n\xe5\x8e\x9f\xe5\xa7\x8b\xe6\x96\x87\xe6\xa1\x88\n",
    }

    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    dub_text = hf_router._hf_dub_input_text(
        "hf-mm-dub",
        {
            "task_id": "hf-mm-dub",
            "target_lang": "mm",
            "origin_srt_path": "deliver/tasks/hf-mm-dub/origin.srt",
        },
    )

    assert dub_text == ""


def test_vi_dub_input_does_not_fallback_to_source_when_target_missing(monkeypatch):
    store = {
        "deliver/tasks/hf-vi-dub/origin.srt": b"1\n00:00:00,000 --> 00:00:02,000\n\xe4\xbd\xa0\xe5\xa5\xbd\n",
    }

    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    dub_text = hf_router._hf_dub_input_text(
        "hf-vi-dub",
        {
            "task_id": "hf-vi-dub",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-vi-dub/origin.srt",
        },
    )

    assert dub_text == ""


def test_vi_compose_subtitle_filter_does_not_add_black_cover_box(tmp_path):
    subtitle_path = tmp_path / "vi.srt"
    subtitle_path.write_text("1\n00:00:00,000 --> 00:00:02,000\nXin chao\n", encoding="utf-8")

    vf = compose_subtitle_vf(subtitle_path, tmp_path, "bottom_mask", "vi")

    assert "drawbox=" in vf
    assert "subtitles='" in vf
    assert "color=black@0.92" not in vf
    assert "color=black@0.96" not in vf


def test_bottom_mask_uses_feathered_bottom_band_cleanup():
    vf = compose_module.source_subtitle_cover_filter("bottom_mask", target_lang="my")

    assert vf.count("drawbox=") == 4
    assert "y=ih*0.850" in vf
    assert "h=ih*0.150" in vf
    assert "color=black@0.68" in vf
    assert "color=black@0.22" in vf
    assert "color=black@0.06" in vf


def test_safe_band_uses_wider_feathered_cleanup():
    vf = compose_module.source_subtitle_cover_filter("safe_band", target_lang="vi")

    assert vf.count("drawbox=") == 4
    assert "y=ih*0.820" in vf
    assert "h=ih*0.180" in vf
    assert "color=black@0.56" in vf
    assert "color=black@0.20" in vf
    assert "color=black@0.05" in vf


@pytest.mark.parametrize(
    ("target_lang", "source_line"),
    [
        ("zh", "这是一条明显过长的中文字幕需要在最终烧录时被更自然地分成两行显示"),
        ("en", "This is a deliberately long English subtitle line that should be wrapped into a more readable two-line layout for final compose"),
        ("my", "ဤစာကြောင်းသည် နောက်ဆုံးဗီဒီယိုစာတန်းထိုးတွင် ဖတ်ရလွယ်ကူစေရန် နှစ်ကြောင်းအတွင်း ပြန်စီရမည့် မြန်မာစာတန်းဖြစ်သည်"),
        ("vi", "Day la mot cau phu de tieng Viet rat dai can duoc chia thanh hai dong de de doc hon trong ban ghi cuoi"),
    ],
)
def test_optimize_hot_follow_subtitle_layout_caps_common_path_to_two_lines(target_lang, source_line):
    source = f"1\n00:00:00,000 --> 00:00:04,000\n{source_line}\n"

    result = optimize_hot_follow_subtitle_layout_srt(source, target_lang)

    body_lines = [line for line in result.splitlines() if line and not line.isdigit() and '-->' not in line]
    assert 1 <= len(body_lines) <= 2
    assert "".join(body_lines).replace(" ", "") in source_line.replace(" ", "")


def test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow(tmp_path):
    subtitle_path = tmp_path / "mm.srt"
    subtitle_path.write_text("1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n", encoding="utf-8")

    vf = compose_subtitle_vf(subtitle_path, tmp_path, "none", "my")

    assert "Alignment=2" in vf
    assert "FontSize=14.0" in vf
    assert "ScaleY" not in vf
    assert "MarginV=18" in vf
    assert "WrapStyle=1" in vf


def test_subtitle_render_signature_tracks_minimal_retune_defaults():
    signature = compose_module.subtitle_render_signature(target_lang="vi", cleanup_mode="none")

    assert "size=13.2" in signature
    assert "margin_v=18" in signature
    assert "line_width=22.00" in signature
    assert "scale_y" not in signature


def test_prepare_workspace_rewrites_local_burn_subtitles_for_layout(monkeypatch, tmp_path):
    subtitle_text = (
        "1\n00:00:00,000 --> 00:00:03,000\n"
        "This is a deliberately long English subtitle line that should wrap for safer bottom placement\n"
    )
    svc = CompositionService(storage=_FakeStorage(subtitle_text), settings=object())

    monkeypatch.setattr(compose_module, "object_head", lambda _key: {})
    monkeypatch.setattr(compose_module, "assert_local_video_ok", lambda _path: (1024, 6.0))
    monkeypatch.setattr(compose_module, "assert_local_audio_ok", lambda _path: (256, 6.0))
    monkeypatch.setattr(compose_module, "sha256_file", lambda _path: "subtitle-sha")

    inputs = _compose_inputs()
    inputs.target_lang = "en"
    task = {"task_id": "hf-layout-en", "subtitles_content_hash": _hash16(subtitle_text)}

    ws = svc._prepare_workspace(
        "hf-layout-en",
        task,
        inputs,
        tmp_path,
        subtitle_resolver=lambda *_args, **_kwargs: "subtitle-key",
    )

    assert ws.subtitle_path is not None
    body_lines = [
        line
        for line in ws.subtitle_path.read_text(encoding="utf-8").splitlines()
        if line and not line.isdigit() and "-->" not in line
    ]
    assert len(body_lines) == 2


def test_compose_refreshes_live_vi_subtitle_currentness_before_voice_ready(monkeypatch):
    monkeypatch.setattr(
        "gateway.app.services.hot_follow_runtime_bridge.compat_hot_follow_subtitle_lane_state",
        lambda _task_id, _task: {
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
        },
    )

    refreshed = _with_live_hot_follow_subtitle_currentness(
        "hf-vi-compose-live",
        {
            "task_id": "hf-vi-compose-live",
            "kind": "hot_follow",
            "target_lang": "vi",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
        },
    )

    assert refreshed["target_subtitle_current"] is True
    assert refreshed["target_subtitle_current_reason"] == "ready"


def test_validate_inputs_uses_live_vi_subtitle_currentness(monkeypatch):
    seen: dict[str, object] = {}
    svc = CompositionService(storage=object(), settings=object())

    monkeypatch.setattr(
        "gateway.app.services.hot_follow_runtime_bridge.compat_hot_follow_subtitle_lane_state",
        lambda _task_id, _task: {
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
        },
    )
    def _fake_collect_voice_execution_state(task, _settings):
        seen["task"] = dict(task)
        return {"audio_ready": True, "audio_ready_reason": "ready"}

    monkeypatch.setattr(
        compose_module,
        "collect_voice_execution_state",
        _fake_collect_voice_execution_state,
    )
    monkeypatch.setattr(compose_module, "assert_artifact_ready", lambda **_kwargs: None)
    monkeypatch.setattr(compose_module.shutil, "which", lambda _name: "/usr/bin/ffmpeg")

    inputs = svc._validate_inputs(
        "hf-vi-compose-validate",
        {
            "task_id": "hf-vi-compose-validate",
            "kind": "hot_follow",
            "target_lang": "vi",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "mute_video_key": "video-key",
            "mm_audio_key": "audio-key",
            "compose_plan": {},
            "config": {},
        },
        lambda *_args, **_kwargs: False,
    )

    assert seen["task"]["target_subtitle_current"] is True
    assert seen["task"]["target_subtitle_current_reason"] == "ready"
    assert inputs.voice_state["audio_ready"] is True


def test_compose_passes_live_vi_task_to_prepare_workspace(monkeypatch, tmp_path):
    seen: dict[str, object] = {}
    svc = CompositionService(storage=object(), settings=object())

    monkeypatch.setattr(
        compose_module,
        "_with_live_hot_follow_subtitle_currentness",
        lambda _task_id, task: {
            **task,
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
        },
    )
    monkeypatch.setattr(
        CompositionService,
        "_validate_inputs",
        lambda self, _task_id, _task, _subtitle_only_check: _ComposeInputs(
            video_key="video-key",
            audio_key="audio-key",
            subtitle_only_compose=False,
            voice_state={"audio_ready": True},
            bgm_key=None,
            bgm_mix=0.3,
            source_audio_policy="mute",
            source_audio_available=False,
            overlay_subtitles=True,
            strip_subtitle_streams=True,
            cleanup_mode="none",
            target_lang="vi",
            freeze_tail_enabled=False,
            freeze_tail_cap_sec=8.0,
            compose_policy="match_video",
            ffmpeg="ffmpeg",
        ),
    )

    def _fake_prepare(self, _task_id, task, _inputs, _tmp, _subtitle_resolver):
        seen["task"] = dict(task)
        final_path = tmp_path / "final.mp4"
        return _WorkspaceFiles(
            task_id="hf-vi-compose-subtitle",
            tmp=tmp_path,
            video_input_path=tmp_path / "video.mp4",
            voice_path=tmp_path / "voice.mp3",
            final_path=final_path,
            subtitle_path=tmp_path / "subs_target.srt",
            bgm_path=None,
            fontsdir=tmp_path,
            ffmpeg="ffmpeg",
            video_duration=8.0,
            voice_duration=8.0,
            compose_policy="match_video",
            subtitle_key="deliver/tasks/hf-vi-compose-subtitle/vi.srt",
            subtitle_object_etag=None,
            subtitle_content_hash=None,
            subtitle_sha256=None,
            compose_warning=None,
            ffmpeg_cmd_used="ffmpeg -i ...",
            overlay_subtitles=True,
        )

    monkeypatch.setattr(CompositionService, "_prepare_workspace", _fake_prepare)
    monkeypatch.setattr(CompositionService, "_compose_voice_only", lambda self, _ws, _inputs: None)
    monkeypatch.setattr(
        CompositionService,
        "_validate_and_probe_output",
        lambda self, _task_id, ws, _inputs: (ws.final_path, 12000, 8.0, None),
    )
    monkeypatch.setattr(
        CompositionService,
        "_upload_and_verify",
        lambda self, _task_id, _task, _final_path, **_kwargs: {"compose_status": "done"},
    )

    result = svc.compose(
        "hf-vi-compose-subtitle",
        {
            "task_id": "hf-vi-compose-subtitle",
            "kind": "hot_follow",
            "target_lang": "vi",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
        },
        subtitle_resolver=lambda task, _task_code, _lang: "deliver/tasks/hf-vi-compose-subtitle/vi.srt"
        if task.get("target_subtitle_current")
        else None,
        subtitle_only_check=lambda *_args, **_kwargs: False,
    )

    assert result.compose_status == "done"
    assert result.updates["compose_status"] == "done"
    assert seen["task"]["target_subtitle_current"] is True
    assert seen["task"]["target_subtitle_current_reason"] == "ready"


def test_prepare_workspace_records_actual_downloaded_subtitle_snapshot(monkeypatch, tmp_path):
    subtitle_text = "latest authoritative subtitle"
    task = {"subtitles_content_hash": _hash16(subtitle_text)}
    svc = CompositionService(storage=_FakeStorage(subtitle_text), settings=object())

    monkeypatch.setattr(compose_module, "assert_local_video_ok", lambda _path: (123, 7.0))
    monkeypatch.setattr(compose_module, "assert_local_audio_ok", lambda _path: (123, 9.0))
    monkeypatch.setattr(compose_module, "object_head", lambda key: {"etag": "subtitle-etag"} if key == "subtitle-key" else None)

    ws = svc._prepare_workspace(
        "hf-bind-2",
        task,
        _compose_inputs(),
        tmp_path,
        lambda *_args: "subtitle-key",
    )

    assert ws.subtitle_key == "subtitle-key"
    assert ws.subtitle_object_etag == "subtitle-etag"
    assert ws.subtitle_content_hash == _hash16(subtitle_text)
    assert ws.subtitle_sha256
    assert ws.subtitle_path is not None
    rendered_lines = [
        line
        for line in ws.subtitle_path.read_text(encoding="utf-8").splitlines()
        if line and not line.isdigit() and "-->" not in line
    ]
    assert 1 <= len(rendered_lines) <= 2
    assert "".join(rendered_lines).replace(" ", "") in subtitle_text.replace(" ", "")


def test_prepare_workspace_rejects_mismatched_downloaded_subtitle_payload(monkeypatch, tmp_path):
    task = {"subtitles_content_hash": _hash16("latest subtitle")}
    svc = CompositionService(storage=_FakeStorage("stale subtitle"), settings=object())

    monkeypatch.setattr(compose_module, "assert_local_video_ok", lambda _path: (123, 7.0))
    monkeypatch.setattr(compose_module, "assert_local_audio_ok", lambda _path: (123, 9.0))
    monkeypatch.setattr(compose_module, "object_head", lambda _key: {"etag": "subtitle-etag"})

    with pytest.raises(HTTPException) as exc:
        svc._prepare_workspace(
            "hf-bind-3",
            task,
            _compose_inputs(),
            tmp_path,
            lambda *_args: "subtitle-key",
        )

    assert exc.value.detail["reason"] == "subtitle_revision_mismatch"
    assert "expected" in exc.value.detail["message"]


def test_upload_and_verify_uses_workspace_subtitle_snapshot_without_nameerror(monkeypatch, tmp_path):
    svc = CompositionService(storage=_FakeStorage("unused"), settings=object())
    final_path = tmp_path / "final.mp4"
    final_path.write_bytes(b"0" * 12000)
    task = {
        "audio_sha256": "AUDIO_SHA",
        "dub_generated_at": "2026-03-21T11:12:00+00:00",
        "subtitles_override_updated_at": "2026-03-21T11:13:00+00:00",
    }
    ws = _WorkspaceFiles(
        task_id="hf-bind-upload",
        tmp=tmp_path,
        video_input_path=tmp_path / "video.mp4",
        voice_path=tmp_path / "voice.mp3",
        final_path=final_path,
        subtitle_path=tmp_path / "subs_target.srt",
        bgm_path=None,
        fontsdir=tmp_path,
        ffmpeg="ffmpeg",
        video_duration=8.0,
        voice_duration=8.0,
        compose_policy="match_video",
        subtitle_key="deliver/tasks/hf-bind-upload/mm.srt",
        subtitle_object_etag="etag-sub",
        subtitle_content_hash="HASH_LATEST",
        subtitle_sha256="sha256-sub",
        compose_warning=None,
        ffmpeg_cmd_used="ffmpeg -i ...",
        overlay_subtitles=True,
    )

    monkeypatch.setattr(compose_module, "object_exists", lambda _key: True)
    monkeypatch.setattr(compose_module, "object_head", lambda _key: {"content_length": 12000, "etag": "etag-final"})
    monkeypatch.setattr(compose_module, "media_meta_from_head", lambda _head: (12000, None))

    updates = svc._upload_and_verify(
        "hf-bind-upload",
        task,
        final_path,
        ws=ws,
        final_size=12000,
        final_duration=8.0,
        compose_started_at="2026-03-21T11:14:00+00:00",
        compose_policy=ws.compose_policy,
        freeze_tail_cap_sec=8.0,
        compose_warning=None,
        ffmpeg_cmd_used=ws.ffmpeg_cmd_used,
    )

    assert isinstance(updates, ComposeResult)
    assert updates.compose_status == "done"
    assert updates.updates["final_source_subtitles_content_hash"] == "HASH_LATEST"
    assert updates.updates["final_source_subtitle_storage_key"] == "deliver/tasks/hf-bind-upload/mm.srt"
    assert updates.updates["final_source_subtitle_storage_etag"] == "etag-sub"
    assert updates.updates["final_source_subtitle_sha256"] == "sha256-sub"
