from __future__ import annotations

import subprocess
from pathlib import Path

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
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_voice_source_audio(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]aformat" in cmd_text
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
    captured: list[str] = []

    def _fake_run_ffmpeg(cmd, task_id, purpose, *, timeout=None):
        captured.extend(cmd)
        ws.final_path.write_bytes(b"final")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(service, "_run_ffmpeg", _fake_run_ffmpeg)

    service._compose_subtitle_only(ws, inputs)

    cmd_text = " ".join(captured)
    assert "[0:a]aformat" in cmd_text
    assert "-map [mix]" in cmd_text
    assert "-an" not in captured
