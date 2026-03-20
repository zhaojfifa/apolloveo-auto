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
