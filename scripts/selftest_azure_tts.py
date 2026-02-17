#!/usr/bin/env python
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from gateway.app.providers.azure_speech import generate_audio_azure_speech


async def _main() -> int:
    key = os.getenv("AZURE_SPEECH_KEY", "").strip()
    region = os.getenv("AZURE_SPEECH_REGION", "").strip()
    out_format = os.getenv("AZURE_TTS_OUTPUT_FORMAT", "audio-24khz-48kbitrate-mono-mp3").strip()
    voice = os.getenv("AZURE_TTS_TEST_VOICE", "my-MM-NilarNeural").strip()

    if not key or not region:
        print("missing required env: AZURE_SPEECH_KEY / AZURE_SPEECH_REGION", file=sys.stderr)
        return 2

    out_path = Path("/tmp/azure_tts.mp3")
    text = "Azure speech self test"

    try:
        await generate_audio_azure_speech(
            text,
            voice,
            str(out_path),
            speech_key=key,
            speech_region=region,
            output_format=out_format,
        )
    except Exception as exc:
        print(f"azure tts selftest failed: {exc}", file=sys.stderr)
        return 1

    if (not out_path.exists()) or out_path.stat().st_size <= 1024:
        print("azure tts selftest failed: output missing/too small", file=sys.stderr)
        return 1

    print(f"azure tts selftest ok: {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
