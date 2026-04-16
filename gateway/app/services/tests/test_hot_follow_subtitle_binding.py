from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from gateway.app.routers import hot_follow_api as hf_router
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

    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key) in store)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda key: store[str(key)])
    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)

    lane = hf_router._hf_subtitle_lane_state(
        "hf-origin-only",
        {
            "task_id": "hf-origin-only",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-origin-only/origin.srt",
        },
    )

    assert lane["raw_source_text"]
    assert lane["edited_text"] == ""
    assert lane["primary_editable_text"] == ""
    assert lane["srt_text"] == ""
    assert lane["subtitle_ready"] is False


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
    assert "FontSize=16" in vf
    assert "MarginV=18" in vf
    assert "WrapStyle=1" in vf


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
