# Hotfix: Hot Follow Helper Translate Failure

Date: 2026-04-20

Branch: `hotfix/hf-helper-translate-failure`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_line_contract_skill_readiness.md`

## Fix

This hotfix keeps helper translation failure separate from authoritative target subtitle truth.

Changes:

- Gemini/helper translation failure is persisted as helper state:
  - `subtitle_helper_status=failed`
  - `subtitle_helper_error_reason`
  - `subtitle_helper_error_message`
  - `subtitle_helper_provider`
  - `subtitle_helper_failed_at`
- Provider exhaustion errors are sanitized before reaching operator-facing payloads.
- The helper endpoint does not write translated target subtitle artifacts on failure.
- Target subtitle truth remains authoritative: empty stays empty until the operator saves target subtitle text.
- Voice-led helper translation failure no longer projects as a primary no-dub/no-TTS terminal path.
- Manual non-empty subtitle save clears stale helper failure and stale empty-dub skip flags, preserving the save -> rerun dub path.

## Not Fix

This is not PR-4 and does not refactor the four-layer state platform.

No changes were made to:

- compose ownership architecture from PR-3
- second-line onboarding
- OpenClaw
- subtitle visual tuning
- dubbing route redesign
- generic provider fallback framework
- UI redesign

## Operator Behavior

When helper translation fails because Gemini returns 429/resource exhaustion:

- the helper response uses a readable error message
- raw provider JSON is not exposed as the operator message
- the workbench subtitle helper state carries the sanitized failure
- advisory prefers `retry_translate_or_edit_subtitle`
- `compose_no_tts` is not recommended as the primary path for voice-led content caused by helper translation failure

Genuine intentional no-dub/no-TTS routes still keep the existing `compose_no_tts` behavior.

## Validation

Focused validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/hot_follow_helper_translation.py gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/hot_follow_route_state.py gateway/app/services/task_view.py gateway/app/services/hot_follow_workbench_presenter.py skills/hot_follow/input_skill.py skills/hot_follow/routing_skill.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_voice_led_does_not_recommend_no_tts_compose gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_hot_follow_live_muted_no_tts_route_recommends_compose_no_tts -q`

Result: `4 passed`.

## Follow-Up

PR-4 should still handle broader four-layer state boundary tightening. This hotfix only prevents helper/provider failure from being misreported as a no-dub terminal route.
