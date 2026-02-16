#!/usr/bin/env bash
set -euo pipefail

echo "[smoke_dub] checking edge_tts import..."
python -c "import edge_tts; print('edge_tts import OK')"

echo "[smoke_dub] generating sample mp3..."
python - <<'PY'
import asyncio
from pathlib import Path

from gateway.app.providers.edge_tts import generate_audio_edge_tts
from gateway.app.services.media_validation import MIN_AUDIO_BYTES

out = Path("tmp/smoke_edge_tts.mp3")
out.parent.mkdir(parents=True, exist_ok=True)

async def main():
    await generate_audio_edge_tts("This is a smoke test for edge tts.", "en-US-JennyNeural", str(out))

asyncio.run(main())
size = out.stat().st_size if out.exists() else 0
print(f"[smoke_dub] output={out} bytes={size}")
if size < MIN_AUDIO_BYTES:
    raise SystemExit(f"audio too small: {size} < {MIN_AUDIO_BYTES}")
PY

echo "[smoke_dub] OK"
