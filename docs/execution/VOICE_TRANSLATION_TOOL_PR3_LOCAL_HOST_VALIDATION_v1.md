# Voice Translation Tool PR-3 Local Host Validation v1

Date: 2026-05-24
Branch: `VoiceTrans`
Scope: standalone Voice Translation Tool only

## Goal

PR-3 narrows the operator flow around one practical question: whether Burmese
and Vietnamese output can sound like a local human host for short video or
product introduction scenarios.

Translation remains a separate editable stage. The main validation path is:

1. faithful semantic translation
2. humanized local-host speech rewrite
3. stable speech synthesis

## Operator UI Simplification

The UI now uses:

- 主播性别: `female | male`
- 表达风格: `natural | professional | engaging`
- 使用场景: `short_video_voiceover | product_intro`
- optional humanization prompt: `custom_humanize_prompt`

The primary action is `生成拟人语音`. Secondary actions are `仅翻译`,
`生成口播文本`, and `用编辑后的文本合成`.

The UI hides duplicated backend voices. If a target language maps female and
male to the same backend voice, only one public option is shown.

## Prompt Strategy

The speech rewrite prompt asks for local Burmese or Vietnamese human-host
delivery:

- avoid machine translation tone
- avoid overly written language
- keep short-video spoken delivery
- preserve product facts and core meaning
- do not invent claims
- for `product_intro + engaging`, allow moderate persuasive wording without
  changing facts
- treat speaker gender as delivery/voice selection only

Operator prompt notes are appended as humanization guidance and persisted in
the internal manifest.

## Humanized Strategy

Current strategy:

```text
gemini_rewrite_plus_tts
```

This means Gemini-optimized speech text plus the best available stable TTS path.
Gemini-native speech generation is not yet integrated in this branch, so the UI
does not promise provider-native speech.

## Manifest Fields

Internal manifests persist:

- `speaker_gender`
- `expression_style`
- `usage_scene`
- `custom_humanize_prompt`
- `humanized_strategy_backend_only`
- `stage_providers_backend_only`
- `stage_errors_backend_only`

Normal UI/API responses may show operator-selected gender/style/scene, but do
not expose provider/vendor/model identifiers or backend strategy fields.

## Boundary

No Hot Follow, Matrix Script, Digital Anchor, publish hub, line contract, or
production-line runtime code is touched by PR-3.

## Validation

`python3.11` is not installed in this local shell (`command not found`), so
focused validation was run with the available `python3` command.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m py_compile gateway/app/services/voice_tool/__init__.py gateway/app/services/voice_tool/models.py gateway/app/services/voice_tool/storage.py gateway/app/services/voice_tool/service.py gateway/app/routers/voice_tool.py gateway/app/providers/azure_speech.py
```

Result: PASS.

```text
env PYTHONPYCACHEPREFIX=/private/tmp/apolloveo_pycache python3 -m pytest -q gateway/app/services/tests/test_voice_tool_service.py
```

Result: `16 passed in 0.10s`.

## Remaining Limitation

The real quality gate is operator listening with live Burmese and Vietnamese
audio using the deployment runtime and configured speech credentials. This PR
keeps the validation flow minimal and does not add a persona or voice asset
management system.
