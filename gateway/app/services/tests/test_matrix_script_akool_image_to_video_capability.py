"""Tests for the Matrix Script Akool image_to_video capability (real one-shot wiring).

All provider interaction is exercised through injected transport / hoster / downloader —
no network, no secret. Verifies the env-resolution gate, the honest status taxonomy, and
the no-leak guarantee.
"""
from __future__ import annotations

import os
import subprocess

import pytest

from gateway.app.services.matrix_script import akool_image_to_video_capability as ak
from gateway.app.services.providers.akool import AkoolHttpResponse
from gateway.app.services.matrix_script.simple_scene_renderer import ffmpeg_available

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(not _FFMPEG, reason="ffmpeg not installed")

_ENABLED = {"MATRIX_SCRIPT_AKOOL_REAL": "true", "AKOOL_API_KEY": "k", "AKOOL_API_BASE_URL": "https://openapi.akool.com"}


def _host(task_id, shot_id, path):
    return "https://hosted/" + os.path.basename(path)


def _create_then(read_body):
    calls = {"n": 0}

    def transport(req):
        calls["n"] += 1
        if req.method == "POST":
            return AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "job-1", "status": 1}})
        return AkoolHttpResponse(200, read_body)
    return transport


def _png(tmp_path):
    src = str(tmp_path / "s.png")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x568:d=1",
                    "-frames:v", "1", src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return src


def _dl_makes_clip(url, out):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=640x480:rate=24:duration=2", out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# ----------------------------------------------------------------- gate (pure)

def test_disabled_when_flag_off() -> None:
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip="y", task_id="t", shot_id="shot02",
        env={"AKOOL_API_KEY": "k"},  # flag off
    )
    assert res.status == ak.STATUS_CREDENTIAL_MISSING
    assert res.provider_attempted is False


def test_credential_missing_when_no_key() -> None:
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip="y", task_id="t", shot_id="shot02",
        env={"MATRIX_SCRIPT_AKOOL_REAL": "true"},  # flag on, no key
    )
    assert res.status == ak.STATUS_CREDENTIAL_MISSING
    assert res.provider_attempted is False


# --------------------------------------------------- one-shot (ffmpeg-gated)

@_skip_no_ffmpeg
def test_provider_success_downloads_and_normalizes(tmp_path) -> None:
    res = ak.generate_shot_clip_akool(
        still_path=_png(tmp_path), out_clip=str(tmp_path / "shot.mp4"),
        task_id="t", shot_id="shot02", env=_ENABLED,
        transport=_create_then({"code": 1000, "data": {"video_status": 3, "video": "https://tmp/x.mp4"}}),
        host_image=_host, download=_dl_makes_clip,
    )
    assert res.status == ak.STATUS_PROVIDER_SUCCESS and res.succeeded
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,codec_name,avg_frame_rate",
                        "-of", "csv=p=0", res.clip_path], capture_output=True, text=True)
    assert p.stdout.strip() == "h264,1080,1920,30/1"


def test_provider_failed_status(tmp_path) -> None:
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip=str(tmp_path / "s.mp4"), task_id="t", shot_id="shot02",
        env=_ENABLED, transport=_create_then({"code": 1000, "data": {"video_status": 4}}),
        host_image=_host, download=_dl_makes_clip,
    )
    assert res.status == ak.STATUS_PROVIDER_FAILED and res.provider_attempted is True
    assert res.clip_path is None


def test_timeout(tmp_path) -> None:
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip=str(tmp_path / "s.mp4"), task_id="t", shot_id="shot02",
        env=_ENABLED, transport=_create_then({"code": 1000, "data": {"video_status": 2}}),
        host_image=_host, download=_dl_makes_clip, poll_max_seconds=0.0,
    )
    assert res.status == ak.STATUS_TIMEOUT and res.provider_attempted is True


def test_policy_blocked_on_quota(tmp_path) -> None:
    def transport(req):
        # create returns insufficient-credit code → AkoolError(QUOTA) → policy_blocked
        return AkoolHttpResponse(200, {"code": 1104, "data": {}})
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip=str(tmp_path / "s.mp4"), task_id="t", shot_id="shot02",
        env=_ENABLED, transport=transport, host_image=_host, download=_dl_makes_clip,
    )
    assert res.status == ak.STATUS_POLICY_BLOCKED


def test_no_secret_or_vendor_leak_in_result(tmp_path) -> None:
    res = ak.generate_shot_clip_akool(
        still_path="x", out_clip=str(tmp_path / "s.mp4"), task_id="t", shot_id="shot02",
        env=_ENABLED, transport=_create_then({"code": 1000, "data": {"video_status": 4}}),
        host_image=_host, download=_dl_makes_clip,
    )
    blob = (str(res.to_status_dict()) + res.redacted_detail + res.operator_label_zh).lower()
    for token in ("akool", "x-api-key", "https://", "video_url", "openapi", "k="):
        assert token not in blob
