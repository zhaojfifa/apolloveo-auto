# PR-4 Hot Follow Ready-Gate Projection Tightening

Date: 2026-04-21

Branch: `pr/four-layer-ready-gate-tightening`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/HOT_FOLLOW_LINE_FOUR_STATE_REVIEW.md`

## Scope

This PR-4 step tightens only Hot Follow presentation and advisory projection.

It keeps lower-layer artifact, currentness, ready-gate, and attempt truth as the source of decision fields. Workbench, operator summary, and advisory must project those fields without re-deriving business state from raw payload fragments.

## Fix

- Workbench compose projection now preserves ready-gate terminal states:
  - blocked compose input projects `blocked`
  - compose input derive failure projects `failed`
  - compose execution failure projects `failed`
  - pending remains only for non-terminal not-ready compose
- Operator summary now binds recommendations to `current_attempt` terminal/required flags instead of recomputing no-dub or subtitle paths from raw `no_dub` and `subtitle_ready` inputs.
- Advisory input now treats `current_attempt` and `operator_summary` as the decision surface. Raw `ready_gate`, `artifact_facts`, `no_dub`, and subtitle readiness fields no longer generate advisory business recommendations by themselves.
- Focused regression coverage now verifies that raw ready-gate no-dub/subtitle facts are ignored unless they have already been projected into the current attempt/operator summary surface.

## Not Fix

- This does not refactor `task_view.py` into explicit L1/L2/L3/L4 response models.
- This does not remove router compatibility helpers.
- This does not rename legacy `mm_*` fields.
- This does not introduce a second line, generic line runtime, or OpenClaw runtime.
- This does not change subtitle save/currentness ownership or compose execution ownership.

## Follow-Up

- Continue reducing mixed four-layer logic in workbench assembly.
- Move remaining deliverable projection toward an explicit contract-first response model.
- Keep advisory and skills read-only; they must not become hidden state writers or hidden business truth engines.
- Add live validation evidence for a real Hot Follow task covering source subtitles, target subtitle translation, dub, compose, publish/final existence, and blocked/failed/pending terminal display consistency.

## Second-Line Gate

Second-line onboarding remains blocked.

PR-4 improves Hot Follow projection discipline, but the factory alignment gate still requires tighter runtime boundaries before a new production line can be added as normal work.

## Validation

Local validation for this step:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/hot_follow_route_state.py gateway/app/services/hot_follow_workbench_presenter.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py skills/hot_follow/input_skill.py skills/hot_follow/routing_skill.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`
- `git diff --check`

Live validation is required before merge preparation.
