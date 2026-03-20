## Hot Follow State Reconciliation Notes (2026-03-21)

### Problem

Hot Follow workbench currently carries multiple state layers for dubbing and compose:

- execution write layer in router / service code
- freshness projection layer in `task_view_helpers`
- ready-gate normalization layer in `status_policy`
- hub presentation / compatibility overlay layer in `hot_follow_api`

This layering is necessary for backward compatibility, but it creates drift risk when
the same concept is represented at multiple levels.

### Confirmed Drift Pattern

The redub path has two different truths that must coexist:

1. Historical compose/final truth
   - previous compose attempt succeeded
   - previous final artifact still exists
   - previous final may remain downloadable/viewable as historical output

2. Current attempt truth
   - new dub artifact is now current
   - old final is stale against new audio/subtitle inputs
   - current compose must return to `pending`
   - recompose is required before a new current final exists

If the current-attempt invalidation is not written explicitly, or if presentation
layers overwrite historical success with current pending semantics, operators see
contradictory signals like:

- `compose.last.finished_at` exists
- `artifact_facts.final_exists = true`
- but current compose/final state reads as fully missing

### Fix Applied In This Round

#### 1. Redub success now invalidates current compose explicitly

In `gateway/app/routers/tasks.py`, successful redub write paths now set:

- `compose_status = pending`
- `compose_error = null`
- `compose_error_reason = null`

This happens without deleting historical compose metadata such as:

- `compose_last_status`
- `compose_last_started_at`
- `compose_last_finished_at`

#### 2. Ready-gate normalization no longer rewrites historical compose result

In `gateway/app/services/status_policy/hot_follow_state.py`,
`_apply_gate_side_effects(...)` no longer overwrites `compose.last.status` to
`pending` when compose is merely stale/not ready.

This keeps the distinction:

- current compose status = pending
- last compose attempt status = done

#### 3. Hub consistency guard no longer erases historical compose success

In `gateway/app/routers/hot_follow_api.py`, the non-ready branch of the hub
consistency guard no longer rewrites `compose.last.status` to `pending`.

This preserves historical compose lifecycle evidence while still exposing the
current final as stale / pending refresh.

### Current Semantics To Preserve

#### Historical / artifact layer

- `artifact_facts.final_exists`
- `historical_final`
- `compose.last.*`

These describe the latest successful historical output and lifecycle evidence.

#### Current fresh-final layer

- `final.exists`
- `final_fresh`
- `final_stale_reason`
- `compose_status`
- `current_attempt.requires_recompose`
- `ready_gate.compose_ready`

These describe whether the current subtitle/audio revision already has a fresh final.

### Next Engineering Optimization

The next cleanup should reduce layered drift by making one projection layer
authoritative for current compose/final state, and treating router compatibility
helpers as presentation-only.

Recommended focus:

1. Keep `compute_composed_state(...)` as the sole projector for current final freshness.
2. Keep `compose.last.*` strictly historical and never reuse it as current readiness.
3. Audit hub overlay helpers so they do not write operational fields.
4. Add explicit test fixtures for:
   - redub success + stale final
   - successful recompose promotion
   - historical final visible while current final is stale
   - current pending compose without losing historical compose lifecycle

### Cross-File State Call Chain

#### A. Re-dub success -> current compose invalidation

1. `gateway/app/routers/tasks.py::_run_dub_job(...)`
   - writes current audio execution state:
   - `dub_status`
   - `audio_sha256`
   - `dub_generated_at`
   - `mm_audio_*`
   - `compose_status = pending`
   - clears `compose_error*`

2. `gateway/app/services/task_view_helpers.py::compute_composed_state(...)`
   - compares current audio/subtitle revision against:
   - `final_source_audio_sha256`
   - `final_source_subtitle_updated_at`
   - `final_updated_at`
   - derives:
   - `final_fresh`
   - `final_stale_reason`
   - `composed_ready`
   - `composed_reason`
   - `final`

3. `gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state(...)`
   - resolves artifact evidence
   - evaluates ready gate
   - mutates:
   - `compose_status`
   - `pipeline.compose`
   - `deliverables.final`
   - `ready_gate`

4. `gateway/app/routers/hot_follow_api.py::get_hot_follow_workbench_hub(...)`
   - builds workbench payload
   - computes presentation aggregates:
   - `artifact_facts`
   - `current_attempt`
   - `operator_summary`
   - `historical_final`
   - applies UI overlay

#### B. Recompose success -> current final promotion

1. `gateway/app/services/compose_service.py::run_hot_follow_compose(...)`
   - writes compose lifecycle:
   - `compose_status = running`
   - `compose_last_status = running`
   - timestamps / errors / lock
   - on success writes:
   - `final_video_key`
   - `final_source_audio_sha256`
   - `final_source_subtitle_updated_at`
   - final artifact metadata

2. `gateway/app/services/task_view_helpers.py::compute_composed_state(...)`
   - re-projects current final freshness from persisted compose snapshot + artifact truth

3. `gateway/app/services/task_view_helpers.py::backfill_compose_done_if_final_ready(...)`
   - compatibility write-back when final is already fresh

4. `gateway/app/routers/hot_follow_api.py::get_hot_follow_workbench_hub(...)`
   - recomputes composed after normalization/backfill
   - projects current final and historical final separately

### Impact Radius

Changing the current-final / compose-state projection impacts these files directly:

- `gateway/app/routers/tasks.py`
- `gateway/app/services/compose_service.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/routers/hot_follow_api.py`

It also impacts compatibility consumers through the bridge:

- `gateway/app/services/hot_follow_runtime_bridge.py`

And it affects these semantic consumers:

- workbench task card
- compose CTA enable/disable state
- final preview selection
- deliverables final row state
- `operator_summary`
- `current_attempt`
- `artifact_facts`
- `ready_gate`

### Blocking Risk Checkpoints

To avoid state propagation blockage, any future change in this area must preserve:

1. Current attempt state and historical success state are different layers.
   - `compose_status` is current
   - `compose.last.*` is historical lifecycle

2. Historical final existence and current fresh final existence are different layers.
   - `artifact_facts.final_exists` / `historical_final.exists`
   - `final.exists` / `final_fresh`

3. Overlay helpers must remain presentation-only.
   - `_safe_collect_hot_follow_workbench_ui(...)`
   - `_merge_workbench_ui_overlay(...)`
   must not rewrite operational truth

4. Compose and dub write paths must explicitly invalidate or promote state.
   - redub success must invalidate current final
   - successful compose must promote current final

5. Any new caller through the compatibility bridge must not bypass recomputation.
   - `hot_follow_runtime_bridge.py` still routes into router-owned logic
   - this is a temporary risk surface until ownership is fully moved out of router layer

---

### VeoSop05: coerce_datetime(None) → NOW fix (2026-03-21)

#### Root Cause

`coerce_datetime(None)` and `coerce_datetime("")` both returned `datetime.now(timezone.utc)`.
In `compute_composed_state`, the timestamp override that clears staleness used
`coerce_datetime` on `dub_generated_at` and `subtitles_override_updated_at`. When either
field was `None` or empty, the result was NOW — which was always newer than any historical
`compose_last_finished_at`, causing the override to fail silently.

This meant: after a successful recompose (post-re-dub), if one of the input timestamps
was missing, the timestamp override could not clear the stale flag. The system then fell
back to SHA comparison, which worked when both SHAs existed. But when SHA tracking was
incomplete (old compose paths, or `final_source_audio_sha256` not persisted), the
final remained incorrectly marked as `final_stale_after_dub` even though compose had
already incorporated the latest inputs.

#### Fix Applied

1. **`task_view_helpers.py::compute_composed_state`** — guarded `coerce_datetime` calls
   with truthiness checks (`if _raw_dub_at else None`), preventing None/empty → NOW.

2. **`task_view_helpers.py::compute_composed_state`** — changed the timestamp override
   from blanket "clear all staleness" to per-input: audio staleness is only cleared when
   `dub_generated_at` is known and compose is newer; subtitle staleness only when
   `subtitles_override_updated_at` is known and compose is newer. SHA-based detection
   remains authoritative when available.

3. **`hot_follow_api.py::_hf_pipeline_state`** — preserved compose step "done" status
   when `task.compose_status` is "done", even when the composed snapshot says the final
   is stale. The pipeline step status reflects execution outcome, not input freshness.

#### Verification

- Interpreter: `./venv/bin/python` (Python 3.11.15)
- All 8 compose freshness unit tests pass (5 new)
- All 10 workbench hub ready-gate integration tests pass
- Full verification baseline: 0 new failures (14 pre-existing, unchanged)
- `py_compile` clean on both modified source files
