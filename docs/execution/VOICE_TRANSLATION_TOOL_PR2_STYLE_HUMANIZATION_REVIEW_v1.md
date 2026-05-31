# Voice Translation Tool PR-2 Style Humanization Review v1

Date: 2026-05-24
Branch: `VoiceTrans`
Status: standalone validation-branch patch

## Operator Feedback Summary

Operators reported that most expression styles produced similar output, with
only `sales` visibly different. Voice presets also sounded too similar and kept
a strong TTS feel. AI Studio prompt tuning produced more human-like Burmese and
Vietnamese speech text than the MVP's local string shaping.

## Root Cause Diagnosis

The MVP had a valid shell and artifact boundary, but the language pipeline was
too shallow:

- Gemini was used for translation, but `style_preset` was mixed into the
  translation request.
- `speech_text` was created by a small local cleanup helper instead of a second
  Gemini prompt rewrite stage.
- `natural` mapped to the same Azure voice as `female`, so the UI could present
  options that were not truly different.

## PR-2 Pipeline Design

The standalone tool now treats generation as three explicit stages:

1. Semantic translation: `source_text -> translated_text`
   - faithful meaning
   - no style prompt pollution
2. Speech rewrite: `translated_text + target_language + style_preset + voice_mode -> speech_text`
   - Gemini prompt rewrite
   - style-specific spoken expression
   - Burmese / Vietnamese natural-local phrasing rules
3. Speech synthesis: `speech_text + voice_preset + speed + voice_mode -> audio`
   - stable Azure TTS path remains the synthesis backend
   - `humanized` currently improves the speech text path; it does not claim a
     new native speech synthesis provider

## Gemini Speech Rewrite Prompt Strategy

Prompt templates are closed by `style_preset`:

- `natural_human`: conversational, less written, local human speech
- `sales`: persuasive marketing / conversion tone without inventing facts
- `explainer`: clear, structured explanation
- `news`: formal, objective broadcast style
- `calm`: gentle, clear, slower and steady expression

Language-specific rules for Burmese and Vietnamese require:

- preserve meaning
- avoid over-literal translation
- use natural local phrasing
- keep text suitable for spoken delivery
- avoid unsupported factual claims
- keep length close to the translated text unless the style requires mild
  expansion

## Azure Voice Mapping Audit Result

The prior mapping made `natural` resolve to the same backend voice as `female`.
PR-2 keeps backend enum values stable, but the public options surface now
deduplicates options that resolve to the same backend voice. The UI loads voice
options per target language and does not present duplicate-sounding presets as
separate choices.

## UI/API Boundary

Added:

- `voice_mode`: closed enum `stable | humanized`
- `GET /api/voice-tool/options`
- `POST /api/voice-tool/speech-variants`
- UI button: `生成不同风格口播文本`

Provider/vendor/model IDs remain hidden from UI and normal API responses.

## Runtime Validation

Local focused validation:

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/services/voice_tool/__init__.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py gateway/app/routers/voice_tool.py gateway/app/providers/azure_speech.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: recorded in PR validation output.

Observed result: `11 passed in 0.11s`.

Full app/server smoke still requires Python 3.11 or the project-standard
runtime/container. This branch does not patch unrelated Python 3.9 app-wide
typing compatibility.

## Remaining Limitations

- `humanized` mode currently means Gemini speech-text rewrite plus best
  available stable TTS. It is not Gemini-native speech synthesis.
- Live Burmese / Vietnamese quality still requires operator listening tests with
  real `GEMINI_API_KEY`, `AZURE_SPEECH_KEY`, and `AZURE_SPEECH_REGION`.
- This remains a standalone validation tool and does not enter production-line
  runtime.
