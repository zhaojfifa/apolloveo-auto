# Voice Translation Tool MVP Review And Operator Note v1

Date: 2026-05-22
Status: implementation note for standalone internal operator tool
Branch: `VoiceTrans` independent validation branch; not merged into `main`.

## Branch Validation Boundary

`VoiceTrans` is reserved for Burmese / Vietnamese Voice Translation Tool
operator validation and Gemini / Azure backend capability checks. Follow-up
changes on this branch must stay narrow to operational validation needs and
must not expand the tool into Hot Follow, Matrix Script, Digital Anchor,
publish hub, production-line runtime, or any line contract.

## Reading Declaration

Root indexes read first:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`

Docs indexes read second:

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Minimum task-specific authority selected:

- `ENGINEERING_RULES.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`
- `PROJECT_RULES.md`
- `apolloveo_current_architecture_and_state_baseline.md`

Why sufficient: the task is a standalone internal Tool Backstage capability, not
a production-line runtime, state/projection, packet, ready-gate, or line
contract change. The selected authority establishes the router/service boundary,
provider-control red line, auth expectations, no-new-line constraint, and
validation discipline. No missing authority file was encountered.

## Review Report

### Gemini

Existing reusable capability:

- `gateway/app/services/providers/gemini/translate.py`
- `gateway/app/services/workers/adapters/gemini/understanding.py`
- env names in `gateway/app/config.py`: `GEMINI_API_KEY`,
  `GEMINI_MODEL`, `GEMINI_BASE_URL`

Reuse decision: reuse the side-effect-free Gemini text translation client from
`services/providers/gemini`. The voice tool service injects or constructs this
client and keeps provider/model identity out of the HTTP/UI response. The
backend manifest records provider use only in `provider_used_backend_only`.

### Azure Speech

Existing reusable capability:

- `gateway/app/providers/azure_speech.py`
- `gateway/app/services/dubbing.py`
- env names in `gateway/app/config.py`: `AZURE_SPEECH_KEY`,
  `AZURE_SPEECH_REGION`, `AZURE_TTS_OUTPUT_FORMAT`,
  `azure_tts_voice_map`

Reuse decision: reuse Azure Speech as the MVP TTS backend. A compatible optional
`rate` argument was added so `slow` / `normal` / `fast` presets can map into
SSML prosody. Existing callers remain valid because the new argument is
optional.

Voice presets map internally:

- Burmese female/natural: `mm_female_1`
- Burmese male: `mm_male_1`
- Vietnamese female/natural: `vi_female_1`
- Vietnamese male: `vi_male_1`

### Artifacts

Existing storage helpers support uploaded task artifacts and presigned download
URLs, but this MVP requested a standalone local layout rather than a production
task artifact.

Reuse decision: create an isolated local artifact writer under
`gateway/app/services/voice_tool/storage.py`. It writes:

```text
{WORKSPACE_ROOT}/artifacts/voice_tool/{job_id}/
  source.txt
  translated.txt
  speech_text.txt
  output.mp3
  output.wav optional
  manifest.json
  feedback.json optional
```

This avoids creating a task, line contract, or publish deliverable.

### Auth And Routes

Existing auth is enforced globally by `gateway/app/main.py` middleware. The new
page and API additionally use `require_operator_session`.

Routes added:

- `GET /voice-tool`
- `POST /api/voice-tool/translate`
- `POST /api/voice-tool/synthesize`
- `POST /api/voice-tool/generate`
- `GET /api/voice-tool/jobs/{job_id}`
- `GET /api/voice-tool/download/{job_id}`
- `POST /api/voice-tool/feedback`

No Hot Follow, Matrix Script, Digital Anchor, publish hub, production-line
runtime, or task-system route is modified.

## Operator Flow

1. Open `/voice-tool`.
2. Paste source text.
3. Select source language, target language, style, voice, and speed.
4. Use `Generate` for translation plus audio, or `Translate Only` to review the
   generated text before synthesis.
5. Edit `Translated Text` or `Speech Text` if needed.
6. Use `Synthesize Edited Text`.
7. Preview audio in the browser and download MP3.
8. Submit feedback scores and comments for the job.

Provider, vendor, model, and engine IDs are intentionally not shown in the UI.

## Validation Evidence

Focused tests added:

- `gateway/app/services/tests/test_voice_tool_service.py`

Coverage:

- request validation for supported languages and feedback score range
- Gemini/Azure provider boundary hidden from public payload
- artifact writing for source, translated text, speech text, output audio, and
  manifest
- feedback persistence to `feedback.json` and manifest summary
- sample `generate` runs for Burmese and Vietnamese using injected fake Gemini
  and fake TTS adapters

Commands run locally:

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/services/voice_tool/__init__.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py gateway/app/routers/voice_tool.py gateway/app/providers/azure_speech.py gateway/app/main.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: `7 passed in 0.08s`.

```text
git diff --check
```

Result: PASS.

Live provider generation was not run in this implementation note because it
requires configured `GEMINI_API_KEY`, `AZURE_SPEECH_KEY`, and
`AZURE_SPEECH_REGION` plus network access. The code path is covered through
injected provider fakes; an operator can run live validation from `/voice-tool`
once credentials are present.

Full application import was not used as a validation command on this local
Python 3.9 interpreter because pre-existing modules (`gateway/app/auth.py` and
`gateway/app/config.py`) evaluate PEP-604 annotations at import time without
`from __future__ import annotations`. This is the same local interpreter
limitation already tracked in prior execution notes; it is not introduced by
the voice tool files.

Attempted local server command:

```text
env AUTH_MODE=off PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m uvicorn gateway.app.main:app --host 127.0.0.1 --port 8017
```

Result: blocked by the same pre-existing Python 3.9 import-time PEP-604 error
in `gateway/app/auth.py`.

Full app/server smoke for `/voice-tool` must be completed under Python 3.11 or
the project-standard runtime/container before any merge decision. Required
runtime smoke remains: start `gateway.app.main:app`, verify `GET /voice-tool`,
generate Burmese and Vietnamese samples, verify job lookup/download, and submit
feedback persistence through the HTTP API.

## Scope Boundary

This MVP does not:

- create a production line
- create or mutate line contracts
- create a parallel task system
- change Hot Follow behavior
- change Matrix Script behavior
- change Digital Anchor behavior
- expose provider/vendor/model selectors in the UI
