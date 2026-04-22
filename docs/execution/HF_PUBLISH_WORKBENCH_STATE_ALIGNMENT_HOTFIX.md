# HF Publish / Workbench State Alignment Hotfix

Date: 2026-04-22
Branch: `VeoBase01-hotfix-hf-publish-workbench-state-alignment`

## Root Cause

The Hot Follow publish surface was seeded from a legacy-compatible publish payload that still carried stale compatibility fallbacks for compose/audio readiness.

The concrete failure mode was:

- publish seeded `composed_ready`, `composed_reason`, `audio_ready`, and `compose_status` from publish-side fallback projection
- workbench seeded readiness from richer L2/L3 surfaces: `artifact_facts`, `current_attempt`, `audio`, `subtitles`, and `ready_gate`
- when a final-ready task already had `final.exists=true`, `compose_status=done`, and `ready_gate.publish_ready=true`, publish could still downgrade the same task to `missing_voiceover`, `audio_not_ready`, and `compose_status=pending`

This created a split-brain between publish and workbench for the same task truth.

## Fault Layer

The bug was in state projection, not business execution.

- L1 `pipeline_step_status`: not changed
- L2 `artifact_facts`: publish was not consuming the same artifact truth as workbench
- L3 `current_attempt`: publish was not consuming the same current runtime resolution as workbench
- L4 presentation / ready gate / publish surface: publish recomputed contradictory readiness from stale compatibility fields

The hotfix closes the publish-side L2/L3 projection gap so L4 now consumes the same authoritative surfaces as workbench.

## Files Changed

- `gateway/app/services/task_view.py`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
- `docs/execution/HF_PUBLISH_WORKBENCH_STATE_ALIGNMENT_HOTFIX.md`

## Change Summary

### `gateway/app/services/task_view.py`

- added a Hot Follow publish projection helper that rebuilds publish-side `audio`, `subtitles`, `artifact_facts`, `current_attempt`, `operator_summary`, `final`, `historical_final`, `final_fresh`, and `compose_status` from the same projection inputs used by workbench
- updated `build_hot_follow_publish_hub(...)` to enrich the publish payload with those authoritative L2/L3 surfaces before running `compute_hot_follow_state(...)`
- ensured publish final URL and `final_mp4` deliverable projection are refreshed from the authoritative final projection before ready-gate evaluation

### `gateway/app/routers/tasks.py`

- changed generic Hot Follow publish routes to delegate to `build_hot_follow_publish_hub(...)` instead of returning the raw publish payload directly
- non-Hot-Follow routes remain unchanged

### `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`

- kept route-level publish-hub readiness coverage
- added regression coverage for the exact contradiction class where publish starts stale but authoritative L2/L3 truth says final-ready
- added generic route coverage so Hot Follow publish no longer bypasses the aligned projection builder

## Why This Is Projection-Only

This hotfix does not change:

- translation logic
- helper translation logic
- target subtitle save contract
- dub logic
- compose logic
- ffmpeg behavior
- worker execution
- Hot Follow line business rules

The only change is how publish-side state is projected and derived before ready-gate evaluation.

Explicit statement: no translation/dub/compose business logic was changed.

## Validation Evidence

### Static validation

- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile gateway/app/services/task_view.py gateway/app/routers/tasks.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
- `git diff --check`

### Focused pytest

- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_task_router_presenters.py`
- result: `60 passed`

### Live-equivalent publish/workbench comparison

Local repository task storage is empty in this workspace:

- `shortvideo.db` exists but `select count(*) from tasks;` returns `0`

Because task `9c755859d049` is not locally available, direct replay of that real task was not possible in this workspace.

A live in-process builder comparison was run against a `9c755859d049`-equivalent final-ready task shape with the same contradiction class:

- publish seed started stale: `composed_ready=false`, `composed_reason=missing_voiceover`, `audio_ready=false`, `compose_status=pending`
- authoritative L2/L3 state said final-ready: `final.exists=true`, `compose_status=done`, `audio_ready=true`, `publish_ready=true`

Observed result after the hotfix:

- publish: `final_exists=true`, `compose_status=done`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_reason=ready`
- workbench: `final_exists=true`, `compose_status=done`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_reason=ready`

This confirms publish and workbench now converge on the same final-ready projection for the affected task shape.
