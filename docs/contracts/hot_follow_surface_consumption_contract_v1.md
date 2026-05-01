# Hot Follow Surface Consumption Contract v1

Status: Wave 0 frozen
Owner layer: L4 presentation and surface shaping

## Governing Sources

- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/design/README.md`
- `docs/design/surface_workbench_lowfi_v1.md`
- `docs/runbooks/ops/hot_follow_delivery_sop.md`
- `docs/runbooks/ops/hot_follow_publish_sop.md`

## Purpose

Freeze how Hot Follow surfaces consume route and CurrentAttempt truth after the
Wave 1 L3 rebuild. This contract applies to workbench, publish, task detail,
operator summary, advisory, and frontend render logic.

## Canonical Surface Input Set

Every Hot Follow surface consumes:

```yaml
surface_inputs:
  task_identity: object
  line_identity: object
  l1_pipeline_rows: object
  l2_artifact_facts: object
  l3_current_attempt: hot_follow_current_attempt_contract_v1
  ready_gate: object
  operator_summary: object
  advisory: object|null
  final: current fresh final object
  historical_final: previous final object|null
  deliverables: object
```

## Surface Rules

1. Workbench, publish, and task detail must share the same authoritative
   projection path before surface-specific aliases are applied.
   Governing source: `docs/contracts/workbench_hub_response.contract.md`.

2. L4 may format, group, label, and hide/show controls. L4 may not mutate repo
   state, artifact facts, CurrentAttempt, route truth, or ready-gate truth.
   Governing sources: `docs/contracts/four_layer_state_contract.md`, `docs/contracts/status_ownership_matrix.md`.

3. Frontend may render status and enable/disable controls only from ready gate,
   CurrentAttempt, artifact facts, and explicit command availability. It may not
   author a local business state machine.
   Governing sources: `docs/design/README.md`, `docs/design/surface_workbench_lowfi_v1.md`.

4. Helper translation status may be shown as advisory or helper lane status. It
   must not become workbench/publish blocking truth once CurrentAttempt says
   mainline truth is valid.
   Governing sources: `docs/contracts/hot_follow_state_machine_contract_v1.md`, `docs/contracts/workbench_hub_response.contract.md`.

5. Scene pack and pack status may remain visible as optional deliverables. Their
   absence must not block publish when current final and ready gate are ready.
   Governing sources: `docs/product/asset_supply_matrix_v1.md`, `docs/runbooks/ops/hot_follow_delivery_sop.md`, `docs/runbooks/ops/hot_follow_publish_sop.md`.

## Required Surface Sections

Workbench and publish responses must expose or alias:

- task identity / line identity
- input summary
- pipeline rows
- subtitles section
- audio section
- final and historical final distinction
- deliverables
- ready gate
- artifact facts
- CurrentAttempt
- operator summary
- advisory when available
- explicit route commands available to the operator

## CTA Rules

### Compose CTA

Enabled only from:

- `current_attempt.compose_execute_allowed=true`
- compose not currently running
- required operator confirmation satisfied when applicable

Disabled reason must come from:

- `current_attempt.compose_reason`
- ready-gate blocking reason
- explicit command availability

### Materialize Target Subtitle CTA

Available when:

- selected route is `tts_replace_route`
- source subtitle/text exists
- target subtitle is not authoritative/current

### Re-enter Subtitle/Dub Flow CTA

Available when:

- selected route is `preserve_source_route`
- operator chooses explicit re-entry

The CTA invokes route command/event semantics; it does not directly rewrite L3.

## Forbidden Surface Behavior

- recomputing `selected_compose_route`
- recomputing `compose_allowed`
- recomputing `dub_current`
- promoting `origin.srt` to target subtitle readiness
- treating helper failure as route truth
- using historical final as current-ready truth
- post-gate mutation of ready-gate or CurrentAttempt fields
- frontend-only route changes

## Wave 2 Requirement

Wave 2 must convert ready-gate signal extraction, operator summary, workbench,
publish, task-detail, and frontend consumption to this contract. Any temporary
compatibility alias must read from L2/L3/L4 canonical inputs and must not write
truth.
