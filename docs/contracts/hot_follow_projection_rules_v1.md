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

## Projection Dominance Contract

```yaml
projection_dominance_contract:
  final_exists_plus_current_attempt_ready_dominates_publish_truth: true
  scene_pack_pending_non_blocking_when_publish_ready: true
  compatibility_fields_cannot_override_authoritative_truth: true
```

## Final Precedence Contract

```yaml
final_precedence_contract:
  surface_selection:
    prefer_current_final_when_exists: true
    fallback_to_historical_final_when_current_absent: true
    historical_final_never_satisfies_current_ready_truth: true
```

## Compose Route / Reason Contract

```yaml
compose_route_reason_contract:
  compose_input_terminal_modes:
    derive_failed: compose_input_derive_failed
    blocked: compose_input_blocked
  compose_exec_failed_statuses:
    - failed
    - error
  no_tts_route_reason_by_route:
    preserve_source_route: source_audio_preserved_no_tts
    bgm_only_route: bgm_only_no_tts
    no_tts_compose_route: compose_no_tts
  compose_allowed_reason:
    allowed_no_dub: no_dub_inputs_ready
    allowed_default: voiceover_ready
    blocked_default: route_not_allowed
    blocked_fields:
      - compose_allowed_reason
      - compose_reason
```

## Blocking-Reason Mapping Contract

```yaml
blocking_reason_mapping_contract:
  source: ready_gate.blocking
  maps:
    missing_voiceover: voiceover_missing
    voiceover_missing: voiceover_missing
    audio_not_ready: audio_not_ready
    audio_not_done: audio_not_done
    compose_input_not_ready: compose_input_not_ready
    compose_input_derive_failed: compose_input_derive_failed
    compose_input_blocked: compose_input_blocked
    compose_exec_failed: compose_exec_failed
    compose_not_done: compose_not_done
    subtitle_missing: subtitle_missing
    subtitle_not_ready: subtitle_not_ready
    final_stale: final_stale
    scenes.running: scenes.running
    scenes.failed: scenes.failed
    scenes_not_ready: scenes.not_ready
    scenes.not_ready: scenes.not_ready
  aliases:
    missing_voiceover: voiceover_missing
    scenes_not_ready: scenes.not_ready
  non_blocking:
    scenes.running: advisory
    scenes.not_ready: advisory
    scenes.failed: advisory
    helper_translate_failed_after_target_ready: advisory
  metadata:
    compose_not_done:
      class: blocking
      suppress_when_publish_ready: true
      priority: 40
    voiceover_missing:
      class: blocking
      suppress_when_publish_ready: true
      priority: 60
    audio_not_ready:
      class: blocking
      suppress_when_publish_ready: true
      priority: 50
    audio_not_done:
      class: blocking
      suppress_when_publish_ready: true
      priority: 55
    compose_input_not_ready:
      class: blocking
      priority: 30
    compose_input_blocked:
      class: blocking
      priority: 10
    compose_input_derive_failed:
      class: blocking
      priority: 5
    compose_exec_failed:
      class: blocking
      priority: 15
    final_stale:
      class: blocking
      priority: 20
    subtitle_missing:
      class: blocking
      priority: 70
    subtitle_not_ready:
      class: blocking
      priority: 70
    scenes.running:
      class: advisory
      suppress_when_publish_ready: true
    scenes.not_ready:
      class: advisory
      suppress_when_publish_ready: true
    scenes.failed:
      class: advisory
      suppress_when_publish_ready: true
    helper_translate_failed_after_target_ready:
      class: advisory
      suppress_when_publish_ready: true
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
