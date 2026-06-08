"""Tests for the Matrix Script voiceover capability (real TTS narration + honest status).

Uses injected async synth callables — no network, no secret — to prove the resolution
order and the honest status taxonomy. A "synth" writes a real (tiny) file to stand in for
provider audio; failures raise.
"""
from __future__ import annotations

import os

from gateway.app.services.matrix_script import voiceover_capability as vc


def _writer(content: bytes = b"RIFFfakewav"):
    async def _synth(*args, **kwargs):
        out = args[2]  # (text, voice, out_path, ...)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(content)
    return _synth


def _raiser(exc: Exception):
    async def _synth(*args, **kwargs):
        raise exc
    return _synth


def test_generated_via_edge_when_no_azure_creds(tmp_path) -> None:
    out = str(tmp_path / "n.mp3")
    res = vc.synthesize_narration(
        "海边圣女果，关注了解更多。", out, env={},
        azure_synth=_raiser(AssertionError("azure should not be called")),
        edge_synth=_writer(),
    )
    assert res.status == vc.STATUS_GENERATED
    assert res.provider == vc.PROVIDER_EDGE
    assert res.generated is True
    assert res.audio_path == out and os.path.getsize(out) > 0
    assert res.operator_label_zh == "旁白已生成"


def test_generated_via_azure_when_creds_present(tmp_path) -> None:
    out = str(tmp_path / "n.mp3")
    edge_called = {"n": 0}

    async def _edge(*a, **k):
        edge_called["n"] += 1

    res = vc.synthesize_narration(
        "narration", out,
        env={"AZURE_SPEECH_KEY": "k", "AZURE_SPEECH_REGION": "eastus"},
        azure_synth=_writer(), edge_synth=_edge,
    )
    assert res.status == vc.STATUS_GENERATED
    assert res.provider == vc.PROVIDER_AZURE
    assert edge_called["n"] == 0  # azure success short-circuits the keyless fallback


def test_blocked_credential_missing_when_no_creds_and_edge_fails(tmp_path) -> None:
    out = str(tmp_path / "n.mp3")
    res = vc.synthesize_narration(
        "narration", out, env={},
        azure_synth=_raiser(AssertionError("azure should not run without creds")),
        edge_synth=_raiser(RuntimeError("403 provider")),
    )
    assert res.status == vc.STATUS_BLOCKED_CREDENTIAL_MISSING
    assert res.provider == vc.PROVIDER_NONE
    assert res.audio_path is None
    assert res.generated is False
    assert "已保留静音" in res.operator_label_zh


def test_blocked_provider_fail_when_azure_creds_but_all_fail(tmp_path) -> None:
    out = str(tmp_path / "n.mp3")
    res = vc.synthesize_narration(
        "narration", out,
        env={"AZURE_SPEECH_KEY": "k", "AZURE_SPEECH_REGION": "eastus"},
        azure_synth=_raiser(RuntimeError("azure down")),
        edge_synth=_raiser(RuntimeError("edge 403")),
    )
    assert res.status == vc.STATUS_BLOCKED_PROVIDER_FAIL
    assert res.provider == vc.PROVIDER_NONE


def test_empty_text_blocked(tmp_path) -> None:
    res = vc.synthesize_narration("   ", str(tmp_path / "n.mp3"), env={})
    assert res.status == vc.STATUS_BLOCKED_PROVIDER_FAIL
    assert res.provider == vc.PROVIDER_NONE


def test_status_dict_is_operator_safe() -> None:
    res = vc.VoiceoverOutcome(vc.STATUS_GENERATED, vc.PROVIDER_EDGE, "/x.mp3")
    d = res.to_status_dict()
    assert d == {
        "capability": "voiceover",
        "status": "generated",
        "generated": True,
        "operator_label_zh": "旁白已生成",
    }
    # no provider brand / secret leaked into the operator-safe status dict
    blob = str(d).lower()
    for token in ("azure", "edge", "key", "region", "/x.mp3"):
        assert token not in blob


def test_azure_credentials_present_helper() -> None:
    assert vc.azure_credentials_present({"AZURE_SPEECH_KEY": "k", "AZURE_SPEECH_REGION": "r"})
    assert not vc.azure_credentials_present({"AZURE_SPEECH_KEY": "k"})
    assert not vc.azure_credentials_present({})
