# Publish Readiness Contract v1 (Unified L4)

Date: 2026-05-02
Status: Plan D contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only. Implementation gated to Plan E.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §10 + §13 Plan D
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/hot_follow_current_attempt_contract_v1.md` (L3, with Plan D `final_provenance` amendment)
- `docs/contracts/hot_follow_ready_gate.yaml` (L4 ready gate)
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md` (with Plan C/D `required` + `blocking_publish` + `scene_pack_blocking_allowed: false` amendments)
- Reference: `gateway/app/services/operator_visible_surfaces/projections.py:51-131` (today's three independent re-derivations: `derive_board_publishable`, `derive_delivery_publish_gate`, plus Board's `task_router_presenters.py::build_tasks_page_rows`)

## Purpose

Pin the **single L4 producer contract** for `publishable`. Today, the Board, Workbench, and Delivery surfaces each compute publish-readiness from `ready_gate` + L2 facts via three separate paths (gap review §10.6). This drift risk grows whenever the rule moves. This contract freezes one producer with one input/output shape; the three surfaces become consumers, not derivers.

This contract does not implement the producer. It pins the shape any future producer (and consumer) MUST honor.

## Ownership

- Owner: contract layer (Plan D).
- Future runtime producer: a single function under `gateway/app/services/operator_visible_surfaces/` (likely `publish_readiness.py`; gated to Plan E).
- Future runtime consumers: Board (`gateway/app/routers/task_router_presenters.py::build_tasks_page_rows`), Workbench, Delivery (`gateway/app/services/operator_visible_surfaces/projections.py::derive_delivery_publish_gate`). These three sites MUST converge on this single producer; they MUST NOT carry their own derivation paths after Plan E lands.
- Non-owners: workers, vendor adapters, frontend platform, packet validator (publish readiness is L4 projection, not packet truth).

## Inputs

| Input                          | Source layer | Source contract                                                                 |
| ------------------------------ | ------------ | ------------------------------------------------------------------------------- |
| `ready_gate`                   | L4           | `docs/contracts/hot_follow_ready_gate.yaml` and per-line analogues              |
| `l2_facts.final_fresh`         | L2           | line state services (`gateway/app/services/status_policy/hot_follow_state.py`, line analogues) |
| `l2_facts.final_stale_reason`  | L2           | as above                                                                        |
| `l3_current_attempt.final_provenance` | L3    | `hot_follow_current_attempt_contract_v1.md` (Plan D amendment) and per-line analogues |
| `delivery_binding.deliverables[]` | derived from packet `binding` + line `delivery_binding_contract` | each row carries `kind`, `required: bool`, `blocking_publish: bool` per Plan C/D amendments to `factory_delivery_contract_v1` |

The producer reads these inputs; it never reads vendor/model/provider identifiers, never resolves storage providers, never calls workers.

## Output

```
PublishReadiness = {
  publishable:           boolean,
  head_reason:           enum (closed; below) | null,
  blocking_advisories:   array of advisory_ref,        # references the Plan D advisory producer output
  consumed_inputs:       {                             # echoed for surface debug; never authoritative
    ready_gate_publish_ready:  boolean,
    ready_gate_compose_ready:  boolean,
    final_fresh:               boolean,
    final_provenance:          "current" | "historical" | null,
    blocking_count:            integer
  }
}
```

### Closed `head_reason` enum

```
{
  publishable_ok,                   # publishable=true (head_reason MAY be null in this case)
  ready_gate_blocking,              # ready_gate.blocking[] non-empty; head reason copied from blocking[0]
  publish_not_ready,                # ready_gate.publish_ready=false and no blocking[]
  compose_not_ready,                # ready_gate.compose_ready=false and no blocking[]
  final_missing,                    # l2_facts.final_fresh=false because final does not exist
  final_stale,                      # l2_facts.final_fresh=false with a stale reason
  final_provenance_historical,      # final exists and fresh, but L3 final_provenance="historical"
  required_deliverable_missing,     # a deliverable row with required=true is unresolved
  required_deliverable_blocking,    # a deliverable row with blocking_publish=true is in a blocking state
  unresolved                        # producer cannot determine readiness from inputs (defensive)
}
```

When `publishable=true`, `head_reason` MAY be `null` or `publishable_ok`. When `publishable=false`, `head_reason` MUST be one of the non-OK values.

### Output discipline

- Every `head_reason` value MUST be reachable from the input shape; the producer MUST NOT invent a reason outside this enum.
- `blocking_advisories[]` carries refs into the Plan D `l4_advisory_producer_output_contract_v1.md` taxonomy. The producer does NOT mint new advisory codes.
- `consumed_inputs` is debug-echo only; surfaces MUST NOT use it as authority. Authority lives in `publishable` + `head_reason`.

## Single-producer rule (normative)

1. Board (`build_tasks_page_rows`) MUST consume this producer's output instead of calling `derive_board_publishable` independently.
2. Workbench MUST consume this producer's output for any "publishable" indication.
3. Delivery (`derive_delivery_publish_gate`) MUST consume this producer's output instead of re-combining `ready_gate` + L2 `final_fresh` locally.
4. After Plan E lands, the three legacy derivation paths MUST be deleted (or thinned to thin pass-through wrappers with explicit deletion notes per ENGINEERING_RULES §7 "Compatibility Rules").
5. Per-surface fallback derivation is forbidden. A surface that cannot reach the producer MUST render a "publishable=null / unresolved" indication, not invent its own publishable boolean.

## Forbidden in producer path

- vendor / model / provider / engine identifiers in inputs, intermediate state, or outputs;
- packet mutation;
- closure (publish-feedback) mutation;
- worker / adapter calls (BLOCKED until Platform Runtime Assembly opens);
- new advisory codes outside the Plan D advisory producer's frozen taxonomy;
- truth invention — every `publishable` value and every `head_reason` MUST be derivable from declared inputs.

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in input/output schema.
- Validator R5: `publishable` is L4 projection, not a packet field; the closed `head_reason` enum is L4-side.
- The `final_provenance` field consumed from L3 MUST be the closed enum frozen by the Plan D amendment to `hot_follow_current_attempt_contract_v1.md` — the producer does not invent its own provenance vocabulary.

## Acceptance

This contract is green when:

1. Inputs and outputs are exactly the closed shapes declared above; no addition.
2. The closed `head_reason` enum is exhaustive for the declared input space.
3. The single-producer rule binds Board / Workbench / Delivery as consumers.
4. No forbidden field appears anywhere on the surface.
5. Per-surface fallback derivation is declared forbidden.

## What this contract does NOT do

- Does not implement the producer (Plan E only).
- Does not implement the legacy-path deletions (Plan E only).
- Does not change ready_gate semantics.
- Does not change L2 fact computation.
- Does not introduce new advisory codes.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/hot_follow_current_attempt_contract_v1.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/workbench_panel_dispatch_contract_v1.md`
- `docs/contracts/l4_advisory_producer_output_contract_v1.md`
- `gateway/app/services/operator_visible_surfaces/projections.py` (read-only reference; today's three derivation paths)
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
