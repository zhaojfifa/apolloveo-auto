# Skills Runtime Contract

## 1. Purpose

This document freezes the Phase-2 runtime boundary for Skills as a strategy layer.

It exists to make later implementation explicit and narrow:

- Skills Runtime is line-scoped
- Skills Runtime is composable
- Skills Runtime is not a business-truth writer
- Skills Runtime does not replace line contract, status policy, deliverable ownership, or asset sink ownership

This contract is a Phase-2 baseline, not proof that a generalized runtime already exists.

## 2. Role In The Factory

Skills Runtime sits between:

- line-aware orchestration
- worker gateway execution
- read-only runtime facts

It may interpret, advise, rank, or route.

It may not:

- write repo truth directly
- write deliverable truth directly
- write asset sink truth directly
- finalize ready-gate truth directly
- finalize task status directly

## 3. Runtime Position

Canonical order:

1. line binding resolves the current production line
2. orchestration builds a read-only state snapshot
3. skills runtime consumes the snapshot and returns strategy output
4. orchestration decides whether to call worker gateway / service execution
5. status policy derives currentness and gate state from accepted truth

This means Skills Runtime is upstream of execution decisions, but downstream of line binding.

## 4. Bundle Structure

The minimum line bundle shape is:

```text
skills/<line_id>/
  input_skill.py
  routing_skill.py
  quality_skill.py
  recovery_skill.py
  config/
    defaults.yaml
```

The first line expected to consume this shape is:

- `hot_follow_line`

Live Phase-2 MVP bundle:

- `skills/hot_follow/input_skill.py`
- `skills/hot_follow/routing_skill.py`
- `skills/hot_follow/quality_skill.py`
- `skills/hot_follow/recovery_skill.py`
- `skills/hot_follow/config/defaults.yaml`

## 5. Loader Boundary

Skills Runtime loader input must include:

- line binding metadata
- task kind / line id
- read-only task snapshot
- read-only artifact facts
- read-only derived currentness / ready-gate input facts
- optional operator request context

Minimal request shape:

```json
{
  "line_id": "hot_follow_line",
  "task_kind": "hot_follow",
  "task_id": "task-id",
  "bundle_ref": "skills/hot_follow",
  "skill_stage": "input|routing|quality|recovery",
  "state_snapshot": {
    "task": {},
    "artifact_facts": {},
    "derived_facts": {},
    "operator_context": {}
  }
}
```

## 6. Allowed Outputs

Skills Runtime may return only strategy outputs.

Allowed output classes:

- normalized interpretation
- routing recommendation
- provider preference recommendation
- quality note
- compliance note
- recovery recommendation
- operator advisory
- execution intent proposal

Minimal result shape:

```json
{
  "line_id": "hot_follow_line",
  "skill_stage": "routing",
  "result_kind": "strategy_output",
  "recommendations": {
    "provider_hint": "azure_speech",
    "compose_mode_hint": "subtitle",
    "recovery_path": "retry_dub"
  },
  "evidence": [
    "target subtitle is current",
    "voice config is valid"
  ],
  "warnings": [],
  "blocking": false
}
```

Allowed semantics:

- propose
- rank
- hint
- explain
- warn

Disallowed semantics:

- persist canonical truth
- mutate accepted deliverable references
- flip primary task state
- promote publish truth
- sink assets

## 7. Skill Stage Intent

### 7.1 Input Skill

Purpose:

- interpret entry context
- normalize ingest hints
- classify content mode inputs

### 7.2 Routing Skill

Purpose:

- choose recommended execution path
- select worker/provider preference hints
- resolve no-dub or standard-dub advisories when the line allows it

### 7.3 Quality Skill

Purpose:

- assess subtitle / dub / compose risk signals
- emit review and readability advisories

### 7.4 Recovery Skill

Purpose:

- suggest next retry / rollback / operator action
- not to perform retries directly

## 8. Truth Ownership Boundary

Skills Runtime must never become a hidden truth layer.

It cannot directly own:

- `task.status`
- `task.last_step`
- `error_reason` / `error_message`
- canonical deliverable keys
- ready-gate derived fields
- stale/currentness fields
- publish truth
- asset sink truth

Orchestration and status policy remain the owners of these writes or derivations.

## 9. Relation To Worker Gateway

Skills Runtime may prepare a worker request recommendation.

It may not:

- submit worker results as final truth
- bypass worker gateway error contract
- hide timeouts or transport failures

Worker Gateway is execution.
Skills Runtime is strategy.

## 10. Relation To Planning

Phase-2 planning layers such as `script_video_line` planning and `action_replica_line` planning assets may later use Skills Runtime for:

- extraction guidance
- candidate ranking
- recovery suggestions

But planning drafts remain separate from execution truth.

## 11. Failure And Fallback

If skills runtime fails:

- main line execution must still be able to continue through a deterministic fallback when the line allows it
- failures must surface as advisory/runtime errors, not silent truth mutation
- lack of a bundle must not fabricate a false-ready state

Fallback policy:

- line/service orchestration may continue with default deterministic behavior
- missing skill output is not itself accepted truth

## 12. Hot Follow Phase-2 Scope

For `hot_follow_line`, Phase-2 runtimeization is intentionally narrow:

- load a real bundle path
- move clearly strategy-only judgment into skills modules
- keep truth writes outside skills
- preserve existing behavior

This contract does not authorize:

- a generalized agent platform
- studio shell import
- second production line implementation in the same PR
