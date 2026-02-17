# Azure Speech TTS (Render)

This project supports `azure-speech` as a first-class dub provider.

## Required env vars

- `DUB_PROVIDER=azure-speech`
- `AZURE_SPEECH_KEY=<your azure speech key>`
- `AZURE_SPEECH_REGION=<region, e.g. eastasia>`

## Optional env vars

- `AZURE_TTS_OUTPUT_FORMAT=audio-24khz-48kbitrate-mono-mp3`

## Provider aliases

The dub provider resolver accepts:

- `azure-speech`
- `azure`
- `azure_tts`

## Edge fallback behavior

If provider is `edge-tts` and synthesis fails with handshake/403 errors, the service retries once with
`azure-speech` when Azure env vars are configured.

## Self-test

Run:

```bash
python scripts/selftest_azure_tts.py
```

Success writes `/tmp/azure_tts.mp3` and exits `0`.
