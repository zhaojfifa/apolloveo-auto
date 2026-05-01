# Evidence: Operator-Visible Surface Wiring Feasibility v1

Date: 2026-05-01
For: `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
Type: Diagnosis evidence (no code change, no test run)

## Authority documents read

| Document | Purpose |
| --- | --- |
| `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md` | Frozen v1 surface scope |
| `docs/reviews/architect_phase2_lowfi_review_v1.md` | CONDITIONAL PASS + three engineering confirmation items |
| `docs/design/surface_task_area_lowfi_v1.md` | Board IA |
| `docs/design/surface_workbench_lowfi_v1.md` | Workbench IA + line_specific_refs mount |
| `docs/design/surface_delivery_center_lowfi_v1.md` | Delivery IA + zoning A/B/C/D |
| `docs/design/panel_hot_follow_subtitle_authority_lowfi_v1.md` | Hot Follow line panel ref bindings |

## Code evidence — Board derived gate / blocker

| Claim | File:line | Note |
| --- | --- | --- |
| `ready_gate.publish_ready` and `ready_gate.compose_ready` are L4-derived | `gateway/app/services/contract_runtime/ready_gate_runtime.py:119-134` | `evaluate_contract_ready_gate(task, state)` |
| `ready_gate.blocking[]` is the canonical priority-sorted blocker list | `gateway/app/services/contract_runtime/ready_gate_runtime.py:78,86,100` | mutated during gate evaluation |
| Blocker reasons are canonicalized for safe verbatim UI pass-through | `gateway/app/services/contract_runtime/ready_gate_runtime.py:55` | `blocking_runtime.canonicalize()` |
| Status ownership for `blocking[]` and `*_reason` fields | `docs/contracts/status_ownership_matrix.md:43` | authoritative |

Conclusion: Board `Blocker:` chip text is **Ready now**; `publishable` boolean is **Additive-fixable** as a derived projection over the above.

## Code evidence — Delivery zoning + publish mirror

| Claim | File:line | Note |
| --- | --- | --- |
| Per-deliverable `required: bool` enables Required vs Optional zoning | `gateway/app/services/matrix_script/delivery_binding.py:86-127` | explicit per-item |
| Optional deliverables are non-blocking by contract | `docs/contracts/factory_delivery_contract_v1.md:40` | "optional pack / scene-pack / archive outputs may remain non-blocking" |
| Optional kinds visible today | `gateway/app/static/js/hot_follow_delivery.js:89-91` | `scene_pack`, `pack_zip`, `edit_bundle_zip` |
| Publish status is task-owned, not packet-owned | `docs/contracts/status_ownership_matrix.md:39` | `publish_status` lives on task |
| Packet envelope forbids operational truth fields | `docs/contracts/factory_packet_envelope_contract_v1.md:96` | forbidden-key set |
| Publish-feedback closure exists for digital_anchor (Phase D.1) | `gateway/app/services/digital_anchor/publish_feedback_closure.py` | task-side, not packet-side |
| Publish-feedback closure exists for matrix_script (Phase D.1) | indexed in `docs/execution/apolloveo_2_0_evidence_index_v1.md` | `tests/contracts/matrix_script/test_publish_feedback_closure_phase_d1.py` |

Conclusion: Delivery Final / Required / Optional zoning is **Ready now**. Single derived publish gate and last-publish mirror are **Additive-fixable** by reading existing task-side publish-feedback closure into the delivery presenter.

## Code evidence — Workbench line_specific_refs[]

| Claim | File:line | Note |
| --- | --- | --- |
| `line_specific_refs[]` declared with `ref_id` enum on matrix_script packet schema | `schemas/packets/matrix_script/packet.schema.json:30-76` | enum: `matrix_script_variation_matrix`, `matrix_script_slot_pack` |
| Same shape on digital_anchor packet schema | `schemas/packets/digital_anchor/packet.schema.json` | enum referenced by delivery binding |
| Per-ref_id lookup helper pattern | `gateway/app/services/matrix_script/delivery_binding.py:16-20`; `gateway/app/services/matrix_script/workbench_variation_surface.py:16-18` | linear search; promote to shared resolver |
| L2 artifact-fact projection (final/subtitle/audio/pack/manifest) | `gateway/app/services/status_policy/hot_follow_state.py:22,36,52,98-120` | already projected |
| L2 contract definition | `docs/contracts/four_layer_state_contract.md:48-61` | "what artifacts exist + freshness metadata" |
| L3 `current_attempt` dataclass with all required fields | `gateway/app/services/contract_runtime/current_attempt_runtime.py:30-65` | `HotFollowCurrentAttempt` |
| L3 contract | `docs/contracts/hot_follow_current_attempt_contract_v1.md:38-71` | frozen shape |
| L3 projection assembly into presenter | `gateway/app/services/task_view_presenters.py:268-275` | exposed to UI presenter |

Field-by-field cross-check (design ↔ code) — all present:

```
id                         <- contract_version
gate_state                 <- route_allowed, compose_allowed, compose_execute_allowed
advisory                   <- compose_reason, blocking[]
requires_redub             <- requires_redub
requires_recompose         <- requires_recompose
current_subtitle_source    <- target_subtitle_source
dub_current                <- dub_current
compose_status             <- compose_input_ready, compose_execute_allowed
```

Conclusion: Workbench mount resolution + L2 facts strip + L3 attempt strip are **Ready now**.

## Code evidence — Operator-payload hygiene

| Claim | File:line | Note |
| --- | --- | --- |
| Validator forbids vendor / model / provider / engine identifiers in operator-visible packet payload | `gateway/app/services/packet/validator.py:202` | forbidden-key set: `{"vendor_id","model_id","provider","provider_id","engine_id"}` |
| Rule R3: vendor pins forbidden | `docs/contracts/factory_packet_validator_rules_v1.md` | authoritative |
| Envelope rule | `docs/contracts/factory_packet_envelope_contract_v1.md:96` | enforces R3 at envelope level |
| No operator presenter reads vendor fields | `gateway/app/services/task_view_presenters.py`; `gateway/app/services/task_view_workbench_contract.py`; `gateway/app/services/matrix_script/delivery_binding.py`; `gateway/app/services/digital_anchor/delivery_binding.py` | confirmed by survey |

Conclusion: **Ready now**; no leak found in any operator-visible projection.

## Verdict matrix

| Confirmation item from review | Verdict |
| --- | --- |
| A. Board `publishable` boolean | Additive-fixable |
| A. Validator head-reason verbatim | Ready now |
| B. Single derived publish gate | Additive-fixable |
| B. Last-publish status / channel mirror | Additive-fixable (read from task) |
| B. Optional items independent of gate | Ready now |
| C. `line_specific_refs[]` resolver dispatch | Ready now (refactor to shared resolver) |
| C. Matrix Script ref_id enums present | Ready now |
| C. Digital Anchor ref_id enums present | Ready now |
| C. Hot Follow ref_id enums present | Ready now |
| C. L2 artifact-facts shape stable | Ready now |
| C. L3 `current_attempt` shape stable | Ready now |
| D. No vendor/model/provider/engine leak | Ready now |

## Out of scope (explicit)

- B-roll Action Area and B-roll filter API are **not** diagnosed — blocked on product freeze of the seven B-roll open questions per `docs/reviews/architect_phase2_lowfi_review_v1.md` §"Product Freeze Items".
- No code, schema, or test changes were made.
- No four-layer authority moved.
