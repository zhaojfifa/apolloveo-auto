"""Unit tests for M-02 media_helpers (donor-absorbed file).

Targets `gateway.app.services.media.media_helpers` (not the existing
`gateway.app.services.media_helpers` BGM module — different surface).

Donor commit pin: 62b6da0 (W1).
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

from gateway.app.services.media import media_helpers as mh


class _FakeUpload:
    def __init__(self, filename: str, payload: bytes):
        self.filename = filename
        self.file = io.BytesIO(payload)


def test_ensure_dir_creates_nested(tmp_path: Path):
    target = tmp_path / "a" / "b" / "c"
    mh.ensure_dir(target)
    assert target.is_dir()


def test_save_upload_file_writes_with_random_name(tmp_path: Path):
    upload = _FakeUpload("hello.mp4", b"binary-bytes")
    out = mh.save_upload_file(upload, tmp_path / "uploads")
    assert out.parent == tmp_path / "uploads"
    assert out.suffix == ".mp4"
    assert out.read_bytes() == b"binary-bytes"


def test_save_upload_file_handles_missing_filename(tmp_path: Path):
    upload = _FakeUpload("", b"x")
    out = mh.save_upload_file(upload, tmp_path / "u")
    assert out.suffix == ""
    assert out.read_bytes() == b"x"


def test_probe_video_severed_from_swiftcraft_inputmetadata(tmp_path: Path, monkeypatch):
    """Acceptance: M-02 must not pull in `app.models.task.InputMetadata`.

    The donor module imported `from app.models.task import InputMetadata`.
    We assert (a) the local `MediaProbeResult` shape is what gets returned,
    and (b) the source file contains no SwiftCraft `app.models` reference.
    """
    payload = (
        '{"streams":[{"width":1920,"height":1080}],'
        '"format":{"duration":"12.5"}}'
    )

    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

    monkeypatch.setattr(mh.subprocess, "run", fake_run)
    result = mh.probe_video(tmp_path / "v.mp4")
    assert isinstance(result, mh.MediaProbeResult)
    assert result.width == 1920
    assert result.height == 1080
    assert result.duration == 12.5

    # Severance assertion: the donor `app.models.task` import must not be
    # present in the absorbed module's runtime namespace, and the symbol
    # `InputMetadata` must not be re-exported.
    assert not hasattr(mh, "InputMetadata")
    import sys
    assert "app.models.task" not in sys.modules
    # Spot-check imports list does not name the donor module.
    import ast
    tree = ast.parse(Path(mh.__file__).read_text(encoding="utf-8"))
    imported = {
        getattr(node, "module", None)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "app.models.task" not in imported
    assert "app.models" not in imported


def test_probe_video_returns_none_when_ffprobe_missing(tmp_path: Path, monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        raise FileNotFoundError("no ffprobe")

    monkeypatch.setattr(mh.subprocess, "run", fake_run)
    assert mh.probe_video(tmp_path / "v.mp4") is None


def test_probe_video_handles_invalid_duration(tmp_path: Path, monkeypatch):
    payload = (
        '{"streams":[{"width":640,"height":480}],'
        '"format":{"duration":"not-a-number"}}'
    )

    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

    monkeypatch.setattr(mh.subprocess, "run", fake_run)
    out = mh.probe_video(tmp_path / "v.mp4")
    assert out is not None
    assert out.duration is None
    assert out.width == 640
    assert out.height == 480


def test_generate_thumbnail_returns_none_on_failure(tmp_path: Path, monkeypatch):
    def fake_run(cmd, capture_output, check):
        raise FileNotFoundError("no ffmpeg")

    monkeypatch.setattr(mh.subprocess, "run", fake_run)
    assert mh.generate_thumbnail(tmp_path / "v.mp4", tmp_path / "thumbs") is None


def test_generate_thumbnail_returns_path_on_success(tmp_path: Path, monkeypatch):
    def fake_run(cmd, capture_output, check):
        # Simulate ffmpeg writing the thumbnail file.
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"\xff\xd8\xff")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(mh.subprocess, "run", fake_run)
    out = mh.generate_thumbnail(tmp_path / "v.mp4", tmp_path / "thumbs")
    assert out is not None
    assert out.suffix == ".jpg"
    assert out.exists()
