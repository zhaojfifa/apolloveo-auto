# Voice Translation Tool PR-4 Stage Workflow UI v1

Date: 2026-05-24
Branch: `VoiceTrans`
Scope: standalone Voice Translation Tool UI/workflow only

## Workflow Change

The operator UI is now organized around the backend's three visible stages:

1. `① 翻译原文`
   - inputs: source text, source language, target language
   - action: `生成翻译`
   - output: editable translated text
2. `② 优化为本地真人口播`
   - inputs: editable translated text, speaker gender, expression style,
     usage scene, optional humanization note
   - action: `生成口播文本`
   - output: editable speech text
3. `③ 生成配音并试听`
   - inputs: editable speech text, speed, distinct supported speaker voice,
     voice mode
   - action: `生成配音`
   - output: audio preview and MP3 download
4. `④ 反馈评分`
   - feedback includes naturalness, human-likeness, publish readiness,
     translation accuracy, speed, voice fit, failure reason, and comment

The top-level shortcut `一键生成拟人语音` still runs the full translation ->
speech rewrite -> synthesis flow and fills all visible outputs.

## Editability

- Stage 1 translated text remains editable before Stage 2.
- Stage 2 speech text remains editable before Stage 3.
- Stage 1 action updates only the translated text area in the UI.
- Stage 2 action generates speech text from the edited translated text.
- Stage 3 action generates audio from the edited speech text.

## Boundary

This patch does not change provider routing, backend enum values, line
contracts, or production runtime integration. No provider/vendor/model IDs are
shown in the UI or public payload.

## Validation

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/routers/voice_tool.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: `16 passed in 0.10s`.

Provider visibility check over the template/router/public storage payload:

```text
rg -n "provider_used_backend_only|stage_providers_backend_only|stage_errors_backend_only|humanized_strategy_backend_only|gemini|azure|vendor|model" gateway/app/templates/voice_tool.html gateway/app/routers/voice_tool.py gateway/app/services/voice_tool/storage.py
```

Result: no UI/router/public payload exposure.

Local app startup attempt:

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m uvicorn gateway.app.main:app --port 8011
```

Result: blocked by the pre-existing Python 3.9 runtime mismatch in
`gateway/app/auth.py` (`str | None` import-time failure). This PR does not patch
unrelated app-wide Python 3.9 compatibility. Full `/voice-tool` browser smoke
should run under Python 3.11 or the project-standard runtime/container.
