from __future__ import annotations

import asyncio

import httpx
import pytest

from gateway.app.providers.azure_speech import (
    AzureSpeechError,
    generate_audio_azure_speech,
    resolve_azure_speech_auth,
)


class _FakeAsyncClient:
    def __init__(self, *, captured: dict, response: httpx.Response):
        self._captured = captured
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, *, content=None, headers=None):
        self._captured["url"] = url
        self._captured["content"] = content
        self._captured["headers"] = dict(headers or {})
        return self._response


def test_resolve_azure_speech_auth_rejects_blank_values():
    with pytest.raises(AzureSpeechError, match="AZURE_SPEECH_KEY"):
        resolve_azure_speech_auth(speech_key="   ", speech_region="eastasia")

    with pytest.raises(AzureSpeechError, match="AZURE_SPEECH_REGION"):
        resolve_azure_speech_auth(speech_key="test-key", speech_region="   ")


def test_generate_audio_azure_speech_strips_auth_values_and_uses_expected_endpoint(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    response = httpx.Response(200, content=b"fake-mp3-bytes")
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **_kwargs: _FakeAsyncClient(captured=captured, response=response),
    )

    out_path = tmp_path / "azure.mp3"
    asyncio.run(
        generate_audio_azure_speech(
            "hello from azure",
            "my-MM-NilarNeural",
            str(out_path),
            speech_key="  test-key  ",
            speech_region=" EastAsia ",
        )
    )

    assert out_path.read_bytes() == b"fake-mp3-bytes"
    assert captured["url"] == "https://eastasia.tts.speech.microsoft.com/cognitiveservices/v1"
    assert captured["headers"]["Ocp-Apim-Subscription-Key"] == "test-key"


def test_generate_audio_azure_speech_401_error_is_actionable(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    response = httpx.Response(401, text="Unauthorized")
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **_kwargs: _FakeAsyncClient(captured=captured, response=response),
    )

    with pytest.raises(AzureSpeechError) as exc:
        asyncio.run(
            generate_audio_azure_speech(
                "hello from azure",
                "my-MM-NilarNeural",
                str(tmp_path / "azure.mp3"),
                speech_key="test-key",
                speech_region="eastasia",
            )
        )

    message = str(exc.value)
    assert "TTS_AZURE_HTTP_401" in message
    assert "AZURE_SPEECH_KEY" in message
    assert "AZURE_SPEECH_REGION" in message
    assert "region=eastasia" in message
