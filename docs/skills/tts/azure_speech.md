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
PYTHONPATH=. ./venv/bin/python scripts/selftest_azure_tts.py
```

Success writes `/tmp/azure_tts.mp3` and exits `0`.

## 401 auth failures

If dubbing fails with `TTS_AZURE_HTTP_401`, treat it as an Azure auth/config issue first:

- verify `AZURE_SPEECH_KEY` is the active Speech resource key
- verify `AZURE_SPEECH_REGION` matches that same Speech resource
- verify the runtime is calling the regional speech endpoint shown in the error text
- if env was just changed, restart the app so cached settings reload before retrying dub

Current runtime also sends:

- `Ocp-Apim-Subscription-Key`
- `Ocp-Apim-Subscription-Region`
- `User-Agent: ApolloVeo-HotFollow/azure-speech`
