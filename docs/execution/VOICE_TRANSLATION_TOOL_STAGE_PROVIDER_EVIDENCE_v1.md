# Voice Translation Tool Stage Provider Evidence v1

Date: 2026-05-24
Branch: `VoiceTrans`
Scope: standalone Voice Translation Tool only

## Requested Jobs

- `vt_8459393085d9430c9d66e2f7f2f93826`
- `vt_a432c0c2264344e4ae945b8c0554d083`

The requested job manifests were not present in this local workspace. Checked
the default local artifact root and common runtime roots:

- `data_debug/artifacts/voice_tool`
- `/opt/render/project/src/video_workspace`
- `/opt/render/project/src`
- `/Users/jackie/code`
- `/private/tmp`

Because the concrete `manifest.json` files are unavailable locally, the job
specific synthesis failure reason for `vt_8459393085d9430c9d66e2f7f2f93826`
cannot be recovered from this checkout. This patch adds internal stage error
persistence for future synthesis failures.

## Current Provider Routing

1. `semantic_translation`: `gemini`
2. `speech_rewrite`: `gemini`
3. `speech_synthesis`: `azure_speech`

`voice_mode=stable` uses Azure TTS for synthesis.

`voice_mode=humanized` is not Gemini-native speech generation. It uses Gemini
speech-text rewriting plus Azure TTS synthesis. The UI label is intentionally
`拟人增强（口播文本优化）` so it does not overpromise provider-native speech.

## Manifest Evidence Schema

Internal manifests now include stage-level provider evidence:

```json
{
  "stage_providers_backend_only": {
    "semantic_translation": "gemini",
    "speech_rewrite": "gemini",
    "speech_synthesis": "azure_speech"
  }
}
```

Future synthesis failures also persist:

```json
{
  "stage_errors_backend_only": {
    "speech_synthesis": "..."
  }
}
```

These fields are manifest/internal review evidence only. They are not exposed
through normal UI or `public_job_payload` API responses.

## Voice Mapping Evidence

For Burmese, current defaults resolve as:

- `natural` -> `my-MM-NilarNeural`
- `female` -> `my-MM-NilarNeural`
- `male` -> `my-MM-ThihaNeural`

Because `natural` and `female` map to the same backend voice, public voice
options are deduplicated per target language. The UI should not present
duplicate mapped presets as different voices. If deployment env overrides map
all presets to the same backend voice, only one public option is returned.

## Speech Variants Evidence

`POST /api/voice-tool/speech-variants` is implemented. If a job manifest has
an empty `speech_variants` object, that means style comparison was not generated
for that job or the job was created before the variants endpoint was used.

## Boundary Check

No Hot Follow, Matrix Script, Digital Anchor, publish hub, line contract, or
production-line runtime code is touched by this evidence patch.

## Validation

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/services/voice_tool/__init__.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py gateway/app/routers/voice_tool.py gateway/app/providers/azure_speech.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: `12 passed in 0.11s`.

```text
git diff --check
```

Result: PASS.
