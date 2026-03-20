from __future__ import annotations

import logging
from pathlib import Path
from xml.sax.saxutils import escape

import httpx


logger = logging.getLogger(__name__)


class AzureSpeechError(RuntimeError):
    """Raised when Azure Speech TTS fails."""


def resolve_azure_speech_auth(*, speech_key: str | None, speech_region: str | None) -> tuple[str, str]:
    key = str(speech_key or "").strip()
    if not key:
        raise AzureSpeechError("TTS_AZURE_CONFIG_MISSING: missing AZURE_SPEECH_KEY")
    region = _normalize_region(speech_region)
    if not region:
        raise AzureSpeechError("TTS_AZURE_CONFIG_MISSING: missing AZURE_SPEECH_REGION")
    return key, region


def _voice_locale(voice: str) -> str:
    # Voice format is typically like: my-MM-NilarNeural
    parts = (voice or "").split("-")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return f"{parts[0]}-{parts[1]}"
    return "en-US"


def _build_ssml(text: str, voice: str) -> str:
    locale = _voice_locale(voice)
    return (
        '<speak version="1.0" xml:lang="en-US">'
        f'<voice xml:lang="{locale}" name="{escape(voice)}">{escape(text)}</voice>'
        "</speak>"
    )


def _normalize_region(speech_region: str) -> str:
    return str(speech_region or "").strip().lower()


def _build_endpoint(speech_region: str) -> str:
    region = _normalize_region(speech_region)
    return f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"


async def generate_audio_azure_speech(
    text: str,
    voice: str,
    output_path: str,
    *,
    speech_key: str,
    speech_region: str,
    output_format: str = "audio-24khz-48kbitrate-mono-mp3",
) -> None:
    speech_key, speech_region = resolve_azure_speech_auth(
        speech_key=speech_key,
        speech_region=speech_region,
    )
    if not text or not text.strip():
        raise AzureSpeechError("TTS_EMPTY_TEXT: empty text")
    if not voice or not voice.strip():
        raise AzureSpeechError("TTS_AZURE_VOICE_MISSING: missing voice")

    endpoint = _build_endpoint(speech_region)
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": output_format or "audio-24khz-48kbitrate-mono-mp3",
    }
    ssml = _build_ssml(text.strip(), voice.strip())

    timeout = httpx.Timeout(60.0, connect=15.0)
    logger.info(
        "AZURE_TTS_CONNECT",
        extra={
            "azure_region": speech_region,
            "azure_endpoint": endpoint,
            "azure_voice": voice.strip(),
            "azure_output_format": headers["X-Microsoft-OutputFormat"],
        },
    )
    try:
        async with httpx.AsyncClient(timeout=timeout, http2=False, follow_redirects=True, trust_env=False) as client:
            resp = await client.post(endpoint, content=ssml.encode("utf-8"), headers=headers)
    except httpx.HTTPError as exc:
        logger.warning(
            "AZURE_TTS_CONNECT_FAIL",
            extra={
                "azure_region": speech_region,
                "azure_endpoint": endpoint,
                "azure_voice": voice.strip(),
                "error": str(exc),
            },
        )
        raise AzureSpeechError(f"TTS_AZURE_CONNECT_FAIL:{exc}") from exc
    if resp.status_code < 200 or resp.status_code >= 300:
        preview = (resp.text or "").strip().replace("\n", " ")[:400]
        if resp.status_code == 401:
            message = (
                "TTS_AZURE_HTTP_401: Azure Speech returned 401 Unauthorized; "
                "check AZURE_SPEECH_KEY and AZURE_SPEECH_REGION for an active matching key-region pair "
                f"(region={speech_region})"
            )
            if preview:
                message = f"{message}; provider_message={preview}"
            raise AzureSpeechError(message)
        raise AzureSpeechError(f"TTS_AZURE_HTTP_{resp.status_code}: {preview}")
    if not resp.content:
        raise AzureSpeechError("TTS_EMPTY_AUDIO: azure-speech returned empty payload")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
