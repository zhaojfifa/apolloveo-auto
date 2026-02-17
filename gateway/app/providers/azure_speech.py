from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import httpx


class AzureSpeechError(RuntimeError):
    """Raised when Azure Speech TTS fails."""


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


async def generate_audio_azure_speech(
    text: str,
    voice: str,
    output_path: str,
    *,
    speech_key: str,
    speech_region: str,
    output_format: str = "audio-24khz-48kbitrate-mono-mp3",
) -> None:
    if not speech_key:
        raise AzureSpeechError("TTS_AZURE_CONFIG_MISSING: missing AZURE_SPEECH_KEY")
    if not speech_region:
        raise AzureSpeechError("TTS_AZURE_CONFIG_MISSING: missing AZURE_SPEECH_REGION")
    if not text or not text.strip():
        raise AzureSpeechError("TTS_EMPTY_TEXT: empty text")
    if not voice or not voice.strip():
        raise AzureSpeechError("TTS_AZURE_VOICE_MISSING: missing voice")

    endpoint = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": output_format or "audio-24khz-48kbitrate-mono-mp3",
    }
    ssml = _build_ssml(text.strip(), voice.strip())

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(endpoint, content=ssml.encode("utf-8"), headers=headers)
    if resp.status_code < 200 or resp.status_code >= 300:
        preview = (resp.text or "").strip().replace("\n", " ")[:400]
        raise AzureSpeechError(f"TTS_AZURE_HTTP_{resp.status_code}: {preview}")
    if not resp.content:
        raise AzureSpeechError("TTS_EMPTY_AUDIO: azure-speech returned empty payload")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
