"""Unit tests for M-01 ffmpeg_localization helpers.

Verifies the pure helpers and the subprocess plumbing (using monkeypatched
`subprocess.run`/`Popen`) — no real ffmpeg is required.

Donor commit pin: 62b6da0 (W1).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from gateway.app.services.media import ffmpeg_localization as ff


def test_tail_truncates_to_last_n_chars():
    assert ff._tail("abcdef", n=3) == "def"
    assert ff._tail("abc", n=10) == "abc"
    assert ff._tail("", n=5) == ""
    assert ff._tail(None, n=5) == ""  # type: ignore[arg-type]


def test_normalize_cmd_handles_bytes_and_paths(tmp_path: Path):
    cmd = ["ffmpeg", b"-i", tmp_path / "in.wav", 42]
    norm = ff._normalize_cmd(cmd)
    assert norm[0] == "ffmpeg"
    assert norm[1] == "-i"
    assert norm[2].endswith("in.wav")
    assert norm[3] == "42"


def test_fmt_cmd_decodes_bytes_and_paths(tmp_path: Path):
    out = ff._fmt_cmd(["ffmpeg", b"-i", tmp_path / "x.wav"])
    assert "ffmpeg" in out
    assert "-i" in out
    assert "x.wav" in out


def test_run_cmd_success_invokes_subprocess_run(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, check, timeout):
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        return subprocess.CompletedProcess(cmd, 0, stdout="42.5\n", stderr="")

    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    cp = ff._run_cmd(["ffprobe", "-x"], label="t", timeout_sec=7)
    assert cp.stdout.strip() == "42.5"
    assert captured["timeout"] == 7
    assert captured["cmd"][0] == "ffprobe"


def test_probe_duration_sec_returns_float(monkeypatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="3.250\n", stderr="")
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    assert ff.probe_duration_sec(tmp_path / "f.wav") == pytest.approx(3.25)


def test_probe_duration_sec_returns_none_on_failure(monkeypatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        raise FileNotFoundError("no ffprobe")
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    assert ff.probe_duration_sec(tmp_path / "f.wav") is None


def test_audio_rms_db_parses_stderr(monkeypatch, tmp_path: Path):
    stderr = "...\nRMS level dB: -20.5\nRMS level dB: -22.5\n"

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr=stderr)
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    assert ff.audio_rms_db(tmp_path / "f.wav") == pytest.approx(-21.5)


def test_audio_peak_db_uses_max(monkeypatch, tmp_path: Path):
    stderr = "Peak level dB: -10.0\nPeak level dB: -3.5\n"

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr=stderr)
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    assert ff.audio_peak_db(tmp_path / "f.wav") == pytest.approx(-3.5)


def test_probe_av_streams_parses_json(monkeypatch, tmp_path: Path):
    payload = (
        '{"streams":[{"codec_type":"video","codec_name":"h264"},'
        '{"codec_type":"audio","codec_name":"aac"},'
        '{"codec_type":"subtitle","codec_name":"mov_text"}]}'
    )

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    out = ff.probe_av_streams(tmp_path / "v.mp4")
    assert out["has_audio"] is True
    assert out["has_subtitle_stream"] is True
    assert out["audio_codecs"] == ["aac"]
    assert out["subtitle_codecs"] == ["mov_text"]


def test_probe_av_streams_returns_default_on_failure(monkeypatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        raise FileNotFoundError("no ffprobe")
    monkeypatch.setattr(ff.subprocess, "run", fake_run)
    out = ff.probe_av_streams(tmp_path / "v.mp4")
    assert out == {
        "has_audio": False,
        "has_subtitle_stream": False,
        "subtitle_codecs": [],
        "audio_codecs": [],
    }


def test_speech_ratio_handles_no_duration(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ff, "probe_duration_sec", lambda p, on_log=None: None)
    ratio, silence, audio = ff.speech_ratio_from_silencedetect(tmp_path / "f.wav")
    assert ratio is None
    assert silence == 0.0
    assert audio is None


def test_run_ffmpeg_raises_on_nonzero_returncode(monkeypatch):
    class FakeProc:
        returncode = 2

        def __init__(self):
            self.pid = 12345

        def communicate(self, timeout=None):
            return ("", "boom\n")

    monkeypatch.setattr(ff.subprocess, "Popen", lambda *a, **k: FakeProc())
    with pytest.raises(RuntimeError, match="failed rc=2"):
        ff.run_ffmpeg(["ffmpeg", "-i", "x.wav"], timeout_sec=5, tag="t")


def test_run_ffmpeg_succeeds_silently(monkeypatch):
    class FakeProc:
        returncode = 0

        def __init__(self):
            self.pid = 1

        def communicate(self, timeout=None):
            return ("", "")

    monkeypatch.setattr(ff.subprocess, "Popen", lambda *a, **k: FakeProc())
    # Should not raise.
    ff.run_ffmpeg(["ffmpeg"], timeout_sec=5, tag="t")
