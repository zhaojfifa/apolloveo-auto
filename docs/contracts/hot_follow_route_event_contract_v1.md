# Hot Follow Route Event Contract v1

Status: Wave 0 frozen
Owner layer: L1 route command/event write path

## Governing Sources

- `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/hot_follow_business_flow_v1.md`

## Purpose

Freeze explicit Hot Follow route command/event semantics before Wave 1 runtime
work. Route truth must not be silently migrated or independently reinterpreted
by L3 or L4 consumers.

## Formal Routes

Wave 0 freezes exactly these canonical route names:

- `tts_replace_route`
- `preserve_source_route`

No other route name is a Wave 1 route-truth output unless this contract is
versioned.

## Route Commands

### `enter_tts_replace_route`

Intent:

- enter URL main flow or explicit local re-entry flow
- require formal target subtitle materialization before dub
- require current TTS dub before compose unless a later contract version
  explicitly adds another legal branch

Required command payload:

```yaml
command: enter_tts_replace_route
task_id: string
requested_by: operator|system_service
reason: url_main_flow|local_preserve_reentry|retry_after_materialization|manual_operator_command
source_route: preserve_source_route|null
target_route: tts_replace_route
occurred_at: timestamp
```

### `enter_preserve_source_route`

Intent:

- enter local preserve flow
- allow compose from raw/source video with preserved source audio
- keep helper translation auxiliary
- keep subtitle/dub flow inactive until explicit re-entry

Required command payload:

```yaml
command: enter_preserve_source_route
task_id: string
requested_by: operator|system_service
reason: local_preserve_source_audio|operator_preserve_original_audio
source_route: tts_replace_route|null
target_route: preserve_source_route
occurred_at: timestamp
```

## Route Event Record

Accepted commands produce route events:

```yaml
route_event:
  event_id: string
  task_id: string
  event_type: route_entered
  route: tts_replace_route|preserve_source_route
  previous_route: tts_replace_route|preserve_source_route|null
  reason: string
  actor: operator|system_service
  occurred_at: timestamp
  contract_version: hot_follow_route_event_contract_v1
```

## Ownership Rules

1. Route events are route-truth writes.
   Governing source: `docs/contracts/status_ownership_matrix.md`.

2. L3 CurrentAttempt consumes the latest accepted route event and may not
   silently replace it with a route inferred from helper state, stale no-dub
   residue, subtitle existence, or surface heuristics.
   Governing sources: `docs/contracts/hot_follow_state_machine_contract_v1.md`, `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`.

3. L4 ready gate, operator summary, advisory, workbench, publish, and task
   detail consume L3 route truth and may not create a competing route.
   Governing sources: `docs/contracts/four_layer_state_contract.md`, `docs/contracts/workbench_hub_response.contract.md`.

4. Helper translation never writes route events.
   Governing sources: `docs/architecture/hot_follow_business_flow_v1.md`, `docs/contracts/hot_follow_state_machine_contract_v1.md`.

## Allowed Transitions

| From | To | Allowed only by |
| --- | --- | --- |
| `null` | `tts_replace_route` | task creation for URL main flow or default voice-led task |
| `null` | `preserve_source_route` | local preserve source-audio command |
| `preserve_source_route` | `tts_replace_route` | explicit local re-entry command |
| `tts_replace_route` | `preserve_source_route` | explicit preserve-source command before compose acceptance |

## Forbidden Transitions

- L3 read-time migration from `preserve_source_route` to `tts_replace_route`
  merely because target subtitles become visible.
- L3 read-time migration from `tts_replace_route` to `preserve_source_route`
  because helper translation failed.
- L4 projection migration between routes.
- Frontend-only route changes without accepted command/event writeback.

## Wave 1 Requirement

Wave 1 implementation must either persist route events directly or define a
temporary compatibility read model with the same single-writer semantics and a
documented removal path. It may not keep route truth as a multi-surface
inference.
