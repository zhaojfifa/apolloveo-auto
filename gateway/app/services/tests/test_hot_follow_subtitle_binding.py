from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import compose_service as compose_module
from gateway.app.services.compose_service import CompositionService, _ComposeInputs, _WorkspaceFiles


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
        overlay_subtitles=True,
        strip_subtitle_streams=True,
        cleanup_mode="none",
        target_lang="mm",
        freeze_tail_enabled=False,
        freeze_tail_cap_sec=8.0,
        compose_policy="match_video",
        ffmpeg="ffmpeg",
    )


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


def test_sync_saved_target_subtitle_reuploads_when_existing_mm_srt_differs(monkeypatch, tmp_path):
    uploads: list[tuple[str, str]] = []

    class _Workspace:
        def __init__(self, _task_id: str):
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
    assert ws.subtitle_path.read_text(encoding="utf-8") == subtitle_text


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

    assert updates["compose_status"] == "done"
    assert updates["final_source_subtitles_content_hash"] == "HASH_LATEST"
    assert updates["final_source_subtitle_storage_key"] == "deliver/tasks/hf-bind-upload/mm.srt"
    assert updates["final_source_subtitle_storage_etag"] == "etag-sub"
    assert updates["final_source_subtitle_sha256"] == "sha256-sub"
