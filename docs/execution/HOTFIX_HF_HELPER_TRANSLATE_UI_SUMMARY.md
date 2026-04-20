# Hotfix: Hot Follow Helper Translate UI and Summary Follow-Up

Date: 2026-04-20

Branch: `hotfix/hf-helper-translate-ui-summary`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_line_contract_skill_readiness.md`

## Fix

This follow-up keeps handled helper translation failure readable and helper-scoped in the operator workbench.

Changes:

- The workbench translate helper now parses structured API errors and displays `detail.message` instead of raw JSON.
- Recoverable helper translation failure refreshes hub state without treating the structured response as an unhandled noisy UI path.
- The helper area renders the sanitized helper failure message from `subtitles.helper_translation.message`.
- Hot Follow route/advisory projection treats helper translation failure as active only while authoritative target subtitle truth is not ready.
- If a saved target subtitle exists, stale helper failure no longer drives the primary no-dub / `compose_no_tts` summary path.
- Stale `target_subtitle_empty` / `dub_input_empty` no-dub shadows are ignored when authoritative subtitle truth is ready.

## Not Fix

This is not PR-4 and does not refactor the four-layer state platform.

No changes were made to:

- compose ownership architecture from PR-3
- second-line onboarding
- OpenClaw
- task view contract redesign
- dubbing route redesign
- generic provider retry/fallback framework
- UI redesign

## Preserved Truth Rules

- Helper translation failure does not write target subtitle artifacts.
- Empty target subtitle remains empty until the operator saves target subtitle text.
- Manual subtitle save remains the path that clears stale helper/no-dub shadows and enables rerun dub.
- Genuine intentional no-dub/no-TTS routes keep the existing `compose_no_tts` behavior.

## Validation

Focused validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/hot_follow_route_state.py gateway/app/services/task_view.py skills/hot_follow/input_skill.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_subtitle_template_semantics.py gateway/app/services/tests/test_hot_follow_skills_advisory.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_subtitle_template_semantics.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py -q`

Result: `31 passed`.
