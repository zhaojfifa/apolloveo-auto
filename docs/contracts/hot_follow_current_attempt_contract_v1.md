# Hot Follow CurrentAttempt Contract v1

Status: Wave 0 frozen
Owner layer: L3 current attempt

## Governing Sources

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_state_commit_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`

## Purpose

Freeze the typed L3 CurrentAttempt contract for the Hot Follow rebuild. Wave 1
must create one producer for this object. L4 consumers must stop deriving these
fields independently.

## Inputs

CurrentAttempt consumes:

- latest route event/read model from `hot_follow_route_event_contract_v1`
- L1 step statuses
- L2 artifact facts
- authoritative target subtitle currentness
- authoritative target subtitle source validation
- helper side-channel state as diagnostic input only
- voice/audio state
- compose input facts
- final freshness facts

CurrentAttempt does not mutate any input.

## Required Shape

```yaml
current_attempt:
  contract_version: hot_follow_current_attempt_contract_v1
  task_id: string
  selected_compose_route: tts_replace_route|preserve_source_route
  route_allowed: boolean
  route_allowed_reason: string
  subtitle_required: boolean
  subtitle_process_state: string
  subtitle_ready: boolean
  subtitle_ready_reason: string
  target_subtitle_authoritative_current: boolean
  target_subtitle_source: string|null
  helper_side_channel_state:
    output_state: string|null
    provider_health: string|null
    warning_only: boolean
    blocks_mainline_truth: false
  dub_process_state: string
  audio_ready: boolean
  audio_ready_reason: string
  dub_current: boolean
  dub_current_reason: string
  compose_input_ready: boolean
  compose_allowed: boolean
  compose_execute_allowed: boolean
  compose_reason: string
  requires_redub: boolean
  requires_recompose: boolean
  final_fresh: boolean
  final_stale_reason: string|null
```

## Allowed Subtitle Process States

- `subtitle_not_required_for_route`
- `subtitle_source_missing`
- `subtitle_source_available`
- `target_subtitle_materialization_running`
- `target_subtitle_materialization_stale_pending`
- `target_subtitle_authoritative_current`
- `subtitle_terminal_failure`

Mapping rules:

- `origin.srt` or source text alone may produce `subtitle_source_available`,
  never `target_subtitle_authoritative_current`.
- target subtitle truth requires the commit contract:
  persisted target text, persisted target artifact, source/currentness
  validation, `target_subtitle_current=true`, and
  `target_subtitle_authoritative_source=true`.
- preserve route may produce `subtitle_not_required_for_route`.

## Allowed Dub Process States

- `dub_not_required_for_route`
- `dub_waiting_for_target_subtitle`
- `dub_running`
- `dub_ready_current`
- `dub_stale_after_subtitle_change`
- `dub_retryable_failure`
- `dub_terminal_failure`

Mapping rules:

- `preserve_source_route` produces `dub_not_required_for_route`.
- `tts_replace_route` requires authoritative/current target subtitle before
  current dub can be ready.
- audio artifact existence alone does not imply `dub_ready_current`.

## Allowed Compose States

CurrentAttempt exposes compose through:

- `compose_input_ready`
- `compose_allowed`
- `compose_execute_allowed`
- `compose_reason`
- `requires_recompose`

Mapping rules:

- `compose_execute_allowed=true` only when route is allowed and compose input is
  ready.
- historical final cannot clear `requires_recompose` when the current final is
  stale.
- L4 cannot override compose legality.

## Dominance Rules

1. Persisted route event wins over route inference.
2. Target subtitle commit truth wins over helper history.
3. Fresh current final plus current attempt readiness wins over stale
   compatibility aliases.
4. Scene pack and pack status are advisory for current final readiness.
5. Preserve-source legality remains valid when helper translation fails, as
   long as route event and compose input facts allow preserve compose.

## Producer Rule

There must be exactly one L3 producer for CurrentAttempt in Wave 1. Any legacy
function that emits overlapping fields must become either:

- an input fact producer,
- a compatibility adapter reading CurrentAttempt, or
- deleted in a later wave.

## Consumer Rule

Ready gate, operator summary, advisory, workbench, publish, task-detail, and
frontend surfaces consume this object. They do not recompute route or attempt
truth.
