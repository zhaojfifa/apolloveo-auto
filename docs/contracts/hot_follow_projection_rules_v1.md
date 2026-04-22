# Hot Follow Projection Rules v1

Date: 2026-04-22
Status: Draft for Phase 2 contract-driven upgrade

## Purpose

Define the minimum contract objects required so publish/workbench/task detail
can consume one authoritative projection path instead of hardcoding separate
state control logic in routers and services.

## Projection Source Contract

```yaml
projection_source_contract:
  task_ref: repo task row
  l1:
    pipeline_step_status:
      parse_status: string
      subtitles_status: string
      dub_status: string
      compose_status: string
      scenes_status: string
  l2:
    artifact_facts:
      final_exists: boolean
      final_fresh: boolean
      subtitle_exists: boolean
      audio_exists: boolean
      scene_pack_exists: boolean
      compose_input:
        mode: string
        ready: boolean
        blocked: boolean
        reason: string|null
      audio_lane:
        mode: string
        source_audio_preserved: boolean
        tts_voiceover_exists: boolean
        bgm_configured: boolean
  l3:
    current_attempt:
      audio_ready: boolean
      audio_ready_reason: string
      dub_current: boolean
      dub_current_reason: string
      selected_compose_route: string
      compose_input_ready: boolean
      compose_execute_allowed: boolean
      requires_redub: boolean
      requires_recompose: boolean
  output:
    ready_gate: object
    operator_summary: object
    advisory: object|null
```

Rule:

- projection sources are authoritative inputs only
- no surface may add competing truth fields upstream of ready-gate evaluation

## Ready Gate Rule Contract

```yaml
ready_gate_rule_contract:
  inputs:
    - l2.artifact_facts
    - l3.current_attempt
  outputs:
    publish_ready: boolean
    compose_ready: boolean
    audio_ready: boolean
    subtitle_ready: boolean
    compose_reason: string
    blocking: [string]
  invariants:
    - final fresh current output dominates stale compatibility hints
    - helper translation cannot override valid target subtitle truth
    - scene_pack pending is advisory-only for final-ready publishability
```

## Publish Surface Rule Contract

```yaml
publish_surface_rule_contract:
  consumes:
    - ready_gate
    - final
    - historical_final
    - deliverables
    - scene_pack
  derives:
    final_url: from authoritative final only
    composed_ready: from ready_gate/authoritative state only
    scene_pack_pending_reason: advisory only
  forbidden:
    - recompute audio_ready from legacy payload aliases
    - recompute compose_status from stale publish-only helpers
    - flip publish_ready false after ready_gate from scene_pack pending
```

## Workbench Surface Rule Contract

```yaml
workbench_surface_rule_contract:
  consumes:
    - l1 pipeline rows
    - l2 artifact_facts
    - l3 current_attempt
    - ready_gate
    - operator_summary
    - advisory
  derives:
    pipeline presentation
    compose_allowed projection aliases
    UI-friendly line metadata
  forbidden:
    - mutate authoritative projection after ready-gate computation
    - override final/audio/subtitle truth from compatibility fallback aliases
```

## Blocking-Reason Mapping Contract

```yaml
blocking_reason_mapping_contract:
  source: ready_gate.blocking
  maps:
    compose_input_derive_failed: terminal compose input failure
    compose_input_blocked: route/input blocked
    compose_not_done: compose not yet complete
    audio_not_ready: current audio lane not ready
    subtitle_missing: target subtitle missing
  non_blocking:
    scenes.running: advisory
    scenes.not_ready: advisory
    helper_translate_failed_after_target_ready: advisory
```

## Rule Set

1. Publish, workbench, and task detail must consume the same projection source
   contract.
2. Compatibility adapters may normalize shape but may not replace L2/L3 truth.
3. Ready gate is the only contract object allowed to summarize publish-ready
   truth.
4. Deliverable lists and publish deliverable maps are surface adapters, not
   truth sources.
5. Historical final may be shown, but it may not satisfy current-ready publish
   truth when current freshness is false.

## Migration Intention

Near-term runtime intention:

- keep existing business behavior
- move surface-specific rewrites out of routers
- keep workbench/publish adapters thin over one projection path

Later intention:

- express these rule contracts in editable contract objects rather than hardcoded
  Python branches

## How This Reduces Silicon-Parallel Drift

- It gives each surface the same projection inputs, so publish/workbench stop
  drifting when one adapter evolves and the other does not.
- It localizes compatibility-only shape adaptation and blocks it from becoming a
  hidden truth writer.
- It turns blocking reasons into named contract outputs, which reduces ad hoc
  remapping in routers and presenters.
