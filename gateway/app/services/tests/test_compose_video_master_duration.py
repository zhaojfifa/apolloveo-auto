from __future__ import annotations

import subprocess
from pathlib import Path

from gateway.app.services import compose_service as compose_module
from gateway.app.services.compose_service import CompositionService, _ComposeInputs, _WorkspaceFiles


def _make_inputs() -> _ComposeInputs:
    return _ComposeInputs(
        video_key="deliver/tasks/hf/video.mp4",
        audio_key="deliver/tasks/hf/voice.mp3",
        subtitle_only_compose=False,
        voice_state={},
        bgm_key=None,
        bgm_mix=0.35,
        source_audio_policy="mute",
        source_audio_available=False,
        overlay_subtitles=False,
        strip_subtitle_streams=True,
        cleanup_mode="none",
        target_lang="mm",
        freeze_tail_enabled=False,
        freeze_tail_cap_sec=8.0,
        compose_policy="match_video",
        ffmpeg="ffmpeg",
    )


def _make_workspace(tmp_path: Path, *, video_duration: float, voice_duration: float) -> _WorkspaceFiles:
    video_path = tmp_path / "video.mp4"
    voice_path = tmp_path / "voice.mp3"
    final_path = tmp_path / "final.mp4"
    video_path.write_bytes(b"video")
    voice_path.write_bytes(b"voice")
    return _WorkspaceFiles(
        task_id="hf-compose-duration",
        tmp=tmp_path,
        video_input_path=video_path,
        voice_path=voice_path,
        final_path=final_path,
        subtitle_path=None,
        bgm_path=None,
        fontsdir=tmp_path,
        ffmpeg="ffmpeg",
        video_duration=video_duration,
        voice_duration=voice_duration,
        compose_policy="match_video",
        overlay_subtitles=False,
    )


def test_voice_only_compose_pads_short_audio_to_video_duration(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=8.0, voice_duration=2.4)
    inputs = _make_inputs()
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_only(ws, inputs)

    cmd_text = " ".join(captured)
    assert "-shortest" not in captured
    assert "apad,atrim=0:8.000" in cmd_text


def test_voice_only_compose_trims_long_audio_to_video_duration(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=5.0, voice_duration=9.0)
    inputs = _make_inputs()
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_only(ws, inputs)

    cmd_text = " ".join(captured)
    assert "-shortest" not in captured
    assert "atrim=0:5.000" in cmd_text
    assert "afade=t=out:st=4.650:d=0.35" in cmd_text


def test_mute_source_audio_policy_keeps_voice_only_compose_without_source_audio(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=8.0, voice_duration=2.4)
    inputs = _make_inputs()
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_only(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]" not in cmd_text
    assert "-map [mix]" in cmd_text


def test_preserve_source_audio_policy_mixes_voice_with_source_audio_bed(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=8.0, voice_duration=2.4)
    inputs = _make_inputs()
    inputs.source_audio_policy = "preserve"
    inputs.source_audio_available = True
    inputs.bgm_mix = 0.0
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_source_audio(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]aformat" in cmd_text
    assert "volume=0.350" in cmd_text
    assert "[1:a]aformat" in cmd_text
    assert "amix=inputs=2" in cmd_text
    assert "-an" not in captured


def test_preserve_source_audio_policy_carries_source_audio_for_subtitle_only_compose(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=8.0, voice_duration=0.0)
    ws.voice_path = None
    inputs = _make_inputs()
    inputs.audio_key = None
    inputs.subtitle_only_compose = True
    inputs.source_audio_policy = "preserve"
    inputs.source_audio_available = True
    inputs.bgm_mix = 0.0
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_subtitle_only(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]aformat" in cmd_text
    assert "volume=0.350" in cmd_text
    assert "-map [mix]" in cmd_text
    assert "-an" not in captured


def test_preserve_source_audio_policy_keeps_source_bed_audible_when_uploaded_bgm_muted(tmp_path, monkeypatch):
    service = CompositionService(storage=object(), settings=object())
    ws = _make_workspace(tmp_path, video_duration=8.0, voice_duration=2.4)
    bgm_path = tmp_path / "bgm.mp3"
    bgm_path.write_bytes(b"bgm")
    ws.bgm_path = bgm_path
    inputs = _make_inputs()
    inputs.source_audio_policy = "preserve"
    inputs.source_audio_available = True
    inputs.bgm_key = "deliver/tasks/hf/bgm/user_bgm.mp3"
    inputs.bgm_mix = 0.0
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_source_audio_bgm(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]aformat" in cmd_text
    assert "volume=0.350" in cmd_text
    assert "[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.0" in cmd_text
    assert "amix=inputs=3" in cmd_text
    assert "-an" not in captured


def _patch_validate_input_deps(monkeypatch):
    monkeypatch.setattr(
        compose_module,
        "_with_live_hot_follow_subtitle_currentness",
        lambda _task_id, task: dict(task),
    )
    monkeypatch.setattr(
        compose_module,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {"audio_ready": True, "audio_ready_reason": "ready"},
    )
    monkeypatch.setattr(compose_module, "object_exists", lambda _key: True)
    monkeypatch.setattr(compose_module, "assert_artifact_ready", lambda **_kwargs: None)
    monkeypatch.setattr(compose_module.shutil, "which", lambda _name: "/usr/bin/ffmpeg")


def _patch_validate_input_deps_no_voice(monkeypatch):
    monkeypatch.setattr(
        compose_module,
        "_with_live_hot_follow_subtitle_currentness",
        lambda _task_id, task: dict(task),
    )
    monkeypatch.setattr(
        compose_module,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
        },
    )
    monkeypatch.setattr(compose_module, "object_exists", lambda _key: True)
    monkeypatch.setattr(compose_module, "assert_artifact_ready", lambda **_kwargs: None)
    monkeypatch.setattr(compose_module.shutil, "which", lambda _name: "/usr/bin/ffmpeg")


def test_preserve_source_audio_policy_uses_raw_video_instead_of_mute_video(monkeypatch):
    _patch_validate_input_deps(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    inputs = service._validate_inputs(
        "hf-preserve-raw-input",
        {
            "task_id": "hf-preserve-raw-input",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf-preserve-raw-input/raw.mp4",
            "mute_video_key": "deliver/tasks/hf-preserve-raw-input/mute.mp4",
            "mm_audio_key": "deliver/tasks/hf-preserve-raw-input/audio_mm.mp3",
            "config": {"bgm": {"strategy": "keep"}},
            "pipeline_config": {"has_audio": "true"},
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: False,
    )

    assert inputs.video_key == "deliver/tasks/hf-preserve-raw-input/raw.mp4"
    assert inputs.source_audio_policy == "preserve"
    assert inputs.source_audio_available is True


def test_compose_voice_input_uses_dry_tts_key_not_legacy_audio_lane(monkeypatch):
    _patch_validate_input_deps(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    task_id = "hf-dry-compose-input"
    inputs = service._validate_inputs(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "raw_path": f"deliver/tasks/{task_id}/raw.mp4",
            "mute_video_key": f"deliver/tasks/{task_id}/mute.mp4",
            "mm_audio_key": f"deliver/tasks/{task_id}/bgm/source_audio.mp3",
            "config": {
                "bgm": {
                    "strategy": "keep",
                    "bgm_key": f"deliver/tasks/{task_id}/bgm/source_audio.mp3",
                },
                "tts_voiceover_key": f"deliver/tasks/{task_id}/voiceover/audio_mm.dry.mp3",
            },
            "pipeline_config": {"has_audio": "true"},
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: False,
    )

    assert inputs.audio_key == f"deliver/tasks/{task_id}/voiceover/audio_mm.dry.mp3"
    assert inputs.video_key == f"deliver/tasks/{task_id}/raw.mp4"
    assert inputs.source_audio_policy == "preserve"


def test_mute_source_audio_policy_keeps_mute_video_input(monkeypatch):
    _patch_validate_input_deps(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    inputs = service._validate_inputs(
        "hf-mute-input",
        {
            "task_id": "hf-mute-input",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf-mute-input/raw.mp4",
            "mute_video_key": "deliver/tasks/hf-mute-input/mute.mp4",
            "mm_audio_key": "deliver/tasks/hf-mute-input/audio_mm.mp3",
            "config": {"bgm": {"strategy": "replace"}},
            "pipeline_config": {"has_audio": "true"},
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: False,
    )

    assert inputs.video_key == "deliver/tasks/hf-mute-input/mute.mp4"
    assert inputs.source_audio_policy == "mute"
    assert inputs.source_audio_available is False


def test_no_dub_mute_compose_allows_missing_tts(monkeypatch):
    _patch_validate_input_deps_no_voice(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    inputs = service._validate_inputs(
        "hf-empty-dub-mute",
        {
            "task_id": "hf-empty-dub-mute",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf-empty-dub-mute/raw.mp4",
            "mute_video_key": "deliver/tasks/hf-empty-dub-mute/mute.mp4",
            "config": {"source_audio_policy": "mute"},
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
                "source_audio_policy": "mute",
            },
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: True,
    )

    assert inputs.audio_key is None
    assert inputs.subtitle_only_compose is True
    assert inputs.video_key == "deliver/tasks/hf-empty-dub-mute/mute.mp4"
    assert inputs.source_audio_policy == "mute"


def test_no_dub_preserve_compose_allows_missing_tts_with_source_audio(monkeypatch):
    _patch_validate_input_deps_no_voice(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    inputs = service._validate_inputs(
        "hf-empty-dub-preserve",
        {
            "task_id": "hf-empty-dub-preserve",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf-empty-dub-preserve/raw.mp4",
            "mute_video_key": "deliver/tasks/hf-empty-dub-preserve/mute.mp4",
            "config": {"source_audio_policy": "preserve"},
            "pipeline_config": {
                "has_audio": "true",
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
                "source_audio_policy": "preserve",
            },
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: True,
    )

    assert inputs.audio_key is None
    assert inputs.subtitle_only_compose is True
    assert inputs.video_key == "deliver/tasks/hf-empty-dub-preserve/raw.mp4"
    assert inputs.source_audio_policy == "preserve"
    assert inputs.source_audio_available is True


def test_no_dub_compose_skips_missing_subtitle_overlay(monkeypatch, tmp_path):
    class _Storage:
        def download_file(self, key: str, destination_path: str) -> None:
            assert key == "deliver/tasks/hf-empty-dub/raw.mp4"
            Path(destination_path).write_bytes(b"video")

    monkeypatch.setattr(compose_module, "assert_local_video_ok", lambda _path: (1200, 6.0))
    monkeypatch.setattr(compose_module, "object_head", lambda _key: {})

    service = CompositionService(storage=_Storage(), settings=object())
    inputs = _make_inputs()
    inputs.video_key = "deliver/tasks/hf-empty-dub/raw.mp4"
    inputs.audio_key = None
    inputs.subtitle_only_compose = True
    inputs.overlay_subtitles = True

    ws = service._prepare_workspace(
        "hf-empty-dub",
        {"task_id": "hf-empty-dub", "kind": "hot_follow"},
        inputs,
        tmp_path,
        subtitle_resolver=lambda *_args, **_kwargs: None,
    )

    assert ws.voice_path is None
    assert ws.subtitle_path is None
    assert ws.overlay_subtitles is False
    assert ws.compose_warning == "subtitle_overlay_skipped_empty_no_dub"


def test_preserve_source_audio_policy_disables_source_lane_when_probe_says_no_audio(monkeypatch):
    _patch_validate_input_deps(monkeypatch)
    service = CompositionService(storage=object(), settings=object())

    inputs = service._validate_inputs(
        "hf-preserve-no-source-audio",
        {
            "task_id": "hf-preserve-no-source-audio",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf-preserve-no-source-audio/raw.mp4",
            "mute_video_key": "deliver/tasks/hf-preserve-no-source-audio/mute.mp4",
            "mm_audio_key": "deliver/tasks/hf-preserve-no-source-audio/audio_mm.mp3",
            "config": {"bgm": {"strategy": "keep"}},
            "pipeline_config": {"has_audio": "false"},
            "compose_plan": {},
        },
        lambda *_args, **_kwargs: False,
    )

    assert inputs.video_key == "deliver/tasks/hf-preserve-no-source-audio/raw.mp4"
    assert inputs.source_audio_policy == "preserve"
    assert inputs.source_audio_available is False
