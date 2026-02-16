import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EdgeTTSError(RuntimeError):
    pass

async def generate_audio_edge_tts(text: str, voice: str, output_path: str) -> None:
    try:
        import edge_tts  # type: ignore
    except Exception as e:
        raise EdgeTTSError(f"TTS_DEP_MISSING: edge-tts not installed ({e})") from e

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(str(out))
    except Exception as e:
        raise EdgeTTSError(str(e)) from e
