"""Matrix Script real operator trial orchestrator tests (PR-17R).

Real-render paths require ffmpeg (skipped without it; never a fake final.mp4).
Akool one-shot is exercised via a fake transport — no live call in CI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    SecretRef,
    SecretResolver,
)
from gateway.app.services.matrix_script.akool_real_gate import AKOOL_REAL_FLAG_ENV
from gateway.app.services.matrix_script.minimal_result_artifact_staging import (
    InMemoryArtifactSink,
)
from gateway.app.services.matrix_script.real_trial_orchestrator import (
    RealTrialError,
    real_trial_result_to_payload,
    run_matrix_script_real_trial,
)
from gateway.app.services.providers.akool import AkoolHttpResponse
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    ffmpeg_available,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PUBLISH_HUB = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"

_FFMPEG = ffmpeg_available()
_skip_no_ffmpeg = pytest.mark.skipif(not _FFMPEG, reason="ffmpeg/ffprobe not installed (no fake final.mp4)")


class _Resolver(SecretResolver):
    def __init__(self, key: Optional[str]):
        self._key = key

    def resolve(self, ref: SecretRef) -> Optional[str]:
        return self._key


class _Transport:
    def __init__(self, responses: List[AkoolHttpResponse]):
        self._responses = list(responses)

    def __call__(self, request):
        return self._responses.pop(0)


def _task():
    return {"task_id": "ms-trial-1", "kind": "matrix_script", "config": {"entry": {"topic": "三步搞定脚本", "target_platform": "抖音"}}}


def _success_transport():
    return _Transport([
        AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "job-1", "status": 1}}),
        AkoolHttpResponse(200, {"code": 1000, "data": {"video_status": 3, "video_url": "https://tmp.akool/x.mp4"}}),
    ])


# ---------------------------------------------------------------------------
# input validation (no ffmpeg)
# ---------------------------------------------------------------------------


def test_rejects_non_mapping_task(tmp_path) -> None:
    with pytest.raises(RealTrialError):
        run_matrix_script_real_trial("x", str(tmp_path), sink=InMemoryArtifactSink())


def test_rejects_bad_sink(tmp_path) -> None:
    with pytest.raises(RealTrialError):
        run_matrix_script_real_trial(_task(), str(tmp_path), sink=object())


def test_ffmpeg_missing_raises_no_fake(tmp_path, monkeypatch) -> None:
    from gateway.app.services.matrix_script import minimal_result_loop as loop
    monkeypatch.setattr(loop, "ffmpeg_available", lambda: False)
    out = str(tmp_path / "t")
    with pytest.raises(FFmpegUnavailableError):
        run_matrix_script_real_trial(_task(), out, sink=InMemoryArtifactSink(), env={})
    assert not os.path.exists(os.path.join(out, "final", "final.mp4"))


# ---------------------------------------------------------------------------
# gate off / on-not-wired / on-success (ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_gate_off_fallback_staged_candidate(tmp_path) -> None:
    sink = InMemoryArtifactSink()
    r = run_matrix_script_real_trial(_task(), str(tmp_path / "a"), sink=sink, env={})
    assert r.gate_enabled is False and r.real_oneshot_used is False
    assert r.generation_provider == "none"
    assert r.official_publish_ready is False
    assert r.delivery_block["storage_scope"] == "artifact_staged"
    assert r.delivery_block["delivery_candidate"] is True
    assert r.blocked_reason_zh and "兜底" in r.blocked_reason_zh


@_skip_no_ffmpeg
def test_gate_on_not_wired_blocked_but_staged(tmp_path) -> None:
    r = run_matrix_script_real_trial(
        _task(), str(tmp_path / "b"), sink=InMemoryArtifactSink(),
        env={AKOOL_REAL_FLAG_ENV: "1"}, resolver=_Resolver("k"),
        akool_credentials=AdapterCredentials(resolver=_Resolver("k")), akool_transport=None,
    )
    assert r.gate_enabled is True and r.real_oneshot_used is False
    assert r.generation_provider == "none"
    assert r.blocked_reason_zh and "兜底" in r.blocked_reason_zh
    assert r.delivery_block["storage_scope"] == "artifact_staged"


@_skip_no_ffmpeg
def test_gate_on_fake_success_marks_real_oneshot(tmp_path) -> None:
    r = run_matrix_script_real_trial(
        _task(), str(tmp_path / "c"), sink=InMemoryArtifactSink(),
        env={AKOOL_REAL_FLAG_ENV: "true"}, resolver=_Resolver("k"),
        akool_credentials=AdapterCredentials(resolver=_Resolver("k")), akool_transport=_success_transport(),
    )
    assert r.gate_enabled is True and r.real_oneshot_used is True
    assert r.generation_provider == "real_oneshot_attempted"
    assert r.official_publish_ready is False


# ---------------------------------------------------------------------------
# artifact refs + leakage (ffmpeg)
# ---------------------------------------------------------------------------


@_skip_no_ffmpeg
def test_artifact_refs_present_and_no_provider_leak(tmp_path) -> None:
    r = run_matrix_script_real_trial(
        _task(), str(tmp_path / "d"), sink=InMemoryArtifactSink(),
        env={AKOOL_REAL_FLAG_ENV: "1"}, resolver=_Resolver("k"),
        akool_credentials=AdapterCredentials(resolver=_Resolver("k")), akool_transport=_success_transport(),
    )
    b = r.delivery_block
    for key in ("final_video_artifact_ref", "manifest_artifact_ref", "subtitles_artifact_ref", "audio_artifact_ref"):
        assert str(b[key]).startswith("artifact://")
    payload = real_trial_result_to_payload(r)
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url", "publish_url", "publish_status", "model_id", "credit", "http://", "https://"):
        assert token not in blob, f"trial payload leaks '{token}'"


@_skip_no_ffmpeg
def test_payload_has_no_publish_or_provider_keys(tmp_path) -> None:
    r = run_matrix_script_real_trial(_task(), str(tmp_path / "e"), sink=InMemoryArtifactSink(), env={})
    payload = real_trial_result_to_payload(r)
    for forbidden_key in ("publish_url", "publish_status", "download_url", "provider_url", "temporary_url", "final_video_key"):
        assert forbidden_key not in payload
    assert payload["official_publish_ready"] is False


# ---------------------------------------------------------------------------
# Delivery template staged-candidate (criterion 12, static)
# ---------------------------------------------------------------------------


def test_publish_hub_has_staged_candidate_block() -> None:
    src = _PUBLISH_HUB.read_text(encoding="utf-8")
    assert 'data-role="matrix-script-dc-staged-candidate"' in src
    assert "{% if ms_staged.has_result %}" in src
    assert 'data-role="ms-dc-staged-final-ref"' in src
    assert 'data-role="ms-dc-staged-publish-ready"' in src
    assert "暂存为交付候选" in src


def test_publish_hub_staged_block_gated_and_leak_free() -> None:
    src = _PUBLISH_HUB.read_text(encoding="utf-8")
    ms_gate = src.find("ms_pub.is_matrix_script")
    anchor = src.find('data-role="matrix-script-dc-staged-candidate"')
    assert ms_gate != -1 and anchor != -1 and ms_gate < anchor
    gate = src.find("{% if ms_staged.has_result %}")
    end = src.find("{% endif %}", anchor)
    block = src[gate:end].lower()
    for token in ("akool", "provider_url", "temporary_url", "download_url", "publish_url", "publish_status", "model_id", "credit", "http://", "https://"):
        assert token not in block, f"staged block leaks '{token}'"
