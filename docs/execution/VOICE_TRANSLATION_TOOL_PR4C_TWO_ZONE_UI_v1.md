# Voice Translation Tool PR-4C Two-Zone UI v1

Date: 2026-05-24
Branch: `VoiceTrans`
Scope: standalone Voice Translation Tool UI/workflow only

## UI Change

PR-4C simplifies the operator page from a visible three-stage text pipeline to
two functional zones:

1. `① 翻译：生成目标语言文本`
   - source text
   - source language
   - target language
   - editable target-language translation result
   - `生成翻译`
2. `② 拟人配音：生成本地真人主播感语音`
   - uses the edited target-language text from zone 1
   - speaker gender
   - expression style
   - usage scene
   - speed
   - distinct supported host voice option
   - optional humanization prompt
   - `生成拟人配音`
   - audio preview and MP3 download
   - feedback form

The top-level shortcut `一键翻译并拟人配音` remains available and fills the
target-language text plus audio output while preserving the two-zone layout.

## Hidden Internal Text

The backend still runs translation -> speech rewrite -> synthesis. Operators no
longer manage speech rewrite as a required visible layer. The generated
humanized speech text is available only in the collapsed block:

```text
查看本次拟人优化文本
```

It is collapsed by default.

## Minimal Wiring

`POST /api/voice-tool/speech-rewrite` now persists the edited translated text
back to the existing job before writing the generated speech text. This keeps
the job manifest aligned with the operator-confirmed text used for dubbing.

Provider routing and enum values are unchanged.

## Boundary

No Hot Follow, Matrix Script, Digital Anchor, publish hub, line contract, or
production-line runtime code is touched. Provider/vendor/model IDs remain
hidden from UI and public payloads.

## Validation

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/routers/voice_tool.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: `16 passed in 0.09s`.

Provider visibility check over template/router/public storage payload:

```text
rg -n "provider_used_backend_only|stage_providers_backend_only|stage_errors_backend_only|humanized_strategy_backend_only|gemini|azure|vendor|model" gateway/app/templates/voice_tool.html gateway/app/routers/voice_tool.py gateway/app/services/voice_tool/storage.py
```

Result: no UI/router/public payload exposure.
