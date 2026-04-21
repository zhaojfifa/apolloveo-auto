# PR4 Four-Layer State Tightening V2

Date: 2026-04-21

Branch: `pr/four-layer-ready-gate-tightening-v2`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_router_service_state_dependency_map.md`
- `docs/execution/ROOT_CAUSE_HF_TARGET_SUBTITLE_SAVE_CONTRACT.md`
- `docs/execution/HF_TARGET_SUBTITLE_FOLLOWUP_SPLIT_BRAIN_FIX.md`
- `docs/execution/HF_SOURCE_SUBTITLE_TRANSLATION_BINDING_FIX.md`

## Goal

Restart PR-4 cleanly from latest `main` and tighten the Hot Follow four-layer state boundaries without changing subtitle translation, target subtitle persistence, helper translation, dubbing, compose execution, or any other Hot Follow business-path behavior.

This branch is explicitly business-safety-first. If any state/presenter change causes source-subtitle -> target-subtitle -> dub -> compose regression, the offending commit must be reverted from this branch immediately.

## Scope

Allowed scope in this PR:

1. ready-gate terminal projection tightening
2. current-attempt projection tightening
3. operator-summary binding to attempt projection
4. advisory binding to current-attempt projection
5. pending / failed / blocked consistency cleanup
6. execution note and focused regression coverage for the above

## Explicitly Forbidden Scope

This PR does not touch:

- subtitle translation input/source logic
- source subtitle -> target subtitle behavior
- helper translation behavior
- target subtitle save contract
- dubbing business path
- compose execution business logic
- any Hot Follow functional-path change
- any second-line / Avatar / Localization / OpenClaw work
- any generic Skills platformization

## Fix

Implemented in this branch:

1. `fix(workbench): tighten ready_gate terminal compose projection`
   - workbench compose/final projection now preserves ready-gate terminal `blocked` and `failed` states instead of collapsing every non-ready outcome to `pending`
   - added focused workbench regressions for blocked and derive-failed compose terminals

2. `fix(presenter): bind current_attempt and operator_summary to attempt truth`
   - `current_attempt` now carries the attempt-local subtitle / no-dub context needed by presenter logic
   - `operator_summary` now derives attempt guidance from `current_attempt` instead of side-channel booleans
   - router compatibility wrapper was kept aligned

3. `fix(advisory): bind advisory inputs to current_attempt only`
   - advisory skill input now treats `current_attempt` as the primary source for route, no-dub, compose-input, and terminal attempt facts
   - contradictory `ready_gate` data no longer overrides current-attempt route truth inside advisory routing
   - added advisory regressions for current-attempt precedence

4. `fix(presenter): align pending failed blocked projection states`
   - board / summaries presenters now bind Hot Follow compose projection from computed state for `pending`, `failed`, `blocked`, and `done`, instead of only backfilling `done`
   - added presenter regressions for blocked / failed compose projection on board and summary surfaces

## Not-Fix

This PR does not solve:

- remaining router/service decomposition in `tasks.py` or `hot_follow_api.py`
- generic line/runtime platformization
- deliverable-profile runtime binding beyond current Hot Follow surfaces
- subtitle translation bridge improvements
- subtitle save-contract evolution
- helper/provider recovery changes
- dub-path or compose-path orchestration redesign

## Follow-Up

Remaining follow-up after this branch:

- real Hot Follow live validation on at least one task before merge
- any future cleanup that removes more duplicated router compatibility projections must remain separate from business-path work
- broader factory-alignment structural closure remains outside this PR

## Test Validation

Focused regressions run during this branch:

After Commit 1:

```bash
python3.11 -m pytest \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py \
  gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py
```

After Commit 2:

```bash
python3.11 -m pytest \
  gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py \
  gateway/app/services/tests/test_hot_follow_artifact_facts.py \
  gateway/app/services/tests/test_task_router_presenters.py
```

After Commit 3:

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py
```

After Commit 4:

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_task_router_presenters.py \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py \
  gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py
```

Guardrail checks run with each scoped change:

```bash
python3.11 -m py_compile <changed python files>
git diff --check
```

Observed result for the focused suites above: passed locally on Python `3.11.15`.

## Live Validation

Live validation is still required and is not yet complete on this branch.

Before merge, validate on at least one real Hot Follow task:

### A. Business path must still work

1. source subtitle exists
2. translate to target language writes target subtitle correctly
3. helper-only translation remains helper-only
4. rerun dub works
5. compose works
6. final exists when expected

### B. State / presenter alignment must hold

7. blocked terminal shows blocked, not pending
8. derive-failed terminal shows failed, not pending
9. exec-failed terminal shows failed, not pending
10. pending state clears stale failed shadow
11. operator_summary is consistent with current_attempt only
12. advisory is consistent with current_attempt only
13. workbench / ready_gate / advisory / operator_summary do not contradict each other

## Rollback Rule If Business Path Regresses

If any commit in this branch causes a Hot Follow business-path regression in:

- source subtitle extraction
- target subtitle generation
- helper translation submission or helper-only behavior
- subtitle save/write path
- rerun dub
- compose execution

Then stop immediately and revert the offending commit from this branch before continuing any architecture cleanup.

## Merge Rule

Do not merge this PR until:

- all focused regressions pass
- required live validation passes
- no Hot Follow business regression is observed
- this execution note is complete

## Status Note

Second-line onboarding remains blocked.
