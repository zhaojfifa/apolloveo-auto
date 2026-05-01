# Operator-Visible Surface Wiring Feasibility Memo v1

Date: 2026-05-01
Status: Diagnosis only — no implementation, no UI wiring
Authority cited: `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`, `docs/reviews/architect_phase2_lowfi_review_v1.md`
Scope: Board / Workbench / Delivery / Hot Follow panel only — B-roll out of scope until product freeze of seven open questions
Evidence: `docs/execution/evidence/operator_visible_surface_wiring_feasibility_v1.md`

## 1. Summary

Engineering has performed the wiring-feasibility diagnosis required by the Architect's CONDITIONAL PASS on Phase 2 Low-fi IA. Backend projection truth is **broadly wiring-ready** for Board / Workbench / Delivery / Hot Follow panel against the current gateway. There are **no authority risks** that would force the UI to invent truth or that would force packet truth to grow new operational fields. There are three **additive-fixable gaps**, all expressible as derived projections over fields that already exist in `ready_gate` / `factory_delivery_contract` / packet `line_specific_refs[]`. Operator-visible payload hygiene is enforced at the validator (`gateway/app/services/packet/validator.py:202`) — no vendor / model / provider / engine / raw provider route fields leak into operator surfaces today.

Verdict per surface:

- Board state buckets — **Ready now** for `blocked` / `ready` rendering; `publishable` bucket is **Additive-fixable** (single derived boolean over existing `ready_gate` outputs).
- Workbench skeleton (four generic panels + L2 facts strip + L3 attempt strip + single line-specific slot) — **Ready now**.
- Delivery Final / Required / Optional zoning — **Ready now**. Publish-status mirror — **Additive-fixable** (single derived gate; last-publish status read from task, not packet).
- Hot Follow line panel mounted via `line_specific_refs[ref_id]` — **Ready now**.
- B-roll wiring — **Out of scope** (blocked on product freeze).

No code changes are proposed in this memo. Recommended minimal wiring path (§7) is the smallest projection-only footprint that unblocks Phase-3 wiring without reopening packet truth or four-layer authority.

## 2. Files read

- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/reviews/architect_phase2_lowfi_review_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`
- `docs/design/surface_workbench_lowfi_v1.md`
- `docs/design/surface_delivery_center_lowfi_v1.md`
- `docs/design/panel_hot_follow_subtitle_authority_lowfi_v1.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `CURRENT_ENGINEERING_FOCUS.md`

## 3. Files inspected (gateway / projector / delivery / workbench / packet code)

- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/matrix_script/delivery_binding.py`
- `gateway/app/services/matrix_script/workbench_variation_surface.py`
- `gateway/app/services/digital_anchor/delivery_binding.py`
- `gateway/app/services/packet/validator.py`
- `schemas/packets/matrix_script/packet.schema.json`
- `schemas/packets/digital_anchor/packet.schema.json`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_current_attempt_contract_v1.md`

## 4. Ready now

These items can be wired against current gateway projections with no schema or truth-ownership change. UI work is still gated on the design hold; "Ready now" describes backend readiness only.

| Item | Source field / projection | Authority |
| --- | --- | --- |
| Board `blocked` / `ready` bucket projection | `ready_gate.compose_ready`, `ready_gate.publish_ready`, `ready_gate.blocking[]` | `gateway/app/services/contract_runtime/ready_gate_runtime.py:57-117` |
| Board `Blocker:` chip text (verbatim, operator-safe) | `ready_gate.blocking[]` after `blocking_runtime.canonicalize()` | `gateway/app/services/contract_runtime/ready_gate_runtime.py:55,78,86,100`; `docs/contracts/status_ownership_matrix.md:43` |
| Workbench four generic panels + capability spine | `binding.capability_plan[]` + `evidence.*` from packet envelope | `docs/contracts/factory_packet_envelope_contract_v1.md`; `gateway/app/services/task_view_workbench_contract.py` |
| Workbench L2 artifact-facts strip (`final` / `subtitle` / `audio` / `pack` / `manifest` presence chips) | `final.exists`, `final.url`, `final.sha256`, `origin_srt_path`, `mm_srt_path`, `subtitles_content_hash`, `subtitles_override_updated_at`, `dub_source_audio_fit_max_speed` | `gateway/app/services/status_policy/hot_follow_state.py:22,36,52,98-120`; `docs/contracts/four_layer_state_contract.md:48-61` |
| Workbench L3 `current_attempt.*` strip | `HotFollowCurrentAttempt` dataclass + presenter projection | `gateway/app/services/contract_runtime/current_attempt_runtime.py:30-65`; `gateway/app/services/task_view_presenters.py:268-275`; `docs/contracts/hot_follow_current_attempt_contract_v1.md:38-71` |
| Workbench `line_specific_refs[]` mount resolver (per-line dispatch on `ref_id`) | Linear search over `packet.line_specific_refs[]` matching the design's frozen `ref_id` enums | `gateway/app/services/matrix_script/delivery_binding.py:16-20`; `gateway/app/services/matrix_script/workbench_variation_surface.py:16-18`; `schemas/packets/matrix_script/packet.schema.json:30-76`; `schemas/packets/digital_anchor/packet.schema.json` |
| Delivery Final / Required / Optional zoning + per-deliverable `required` flag | `factory_delivery_contract` deliverables with explicit `required: bool` | `gateway/app/services/matrix_script/delivery_binding.py:86-127`; `docs/contracts/factory_delivery_contract_v1.md:40` |
| Hot Follow panel mount (`hot_follow_subtitle_authority`, `hot_follow_dub_compose_legality`) | Same `line_specific_refs[]` resolver path | `schemas/packets/hot_follow/...` (resolver pattern shared) |
| Operator-payload hygiene (no `vendor_id` / `model_id` / `provider_id` / `engine_id` / raw provider route) | Validator forbidden-key set | `gateway/app/services/packet/validator.py:202`; `docs/contracts/factory_packet_envelope_contract_v1.md:96`; `docs/contracts/factory_packet_validator_rules_v1.md` (R3) |

L3 `current_attempt` field-by-field mapping (all present in code today):

| Design-required field | Backing field on `HotFollowCurrentAttempt` | File |
| --- | --- | --- |
| `id` | `contract_version` (per-line attempt identity) | `gateway/app/services/contract_runtime/current_attempt_runtime.py:30-65` |
| `gate_state` | `route_allowed`, `compose_allowed`, `compose_execute_allowed` | same |
| `advisory` | `compose_reason`, `blocking[]` (canonicalized) | same |
| `requires_redub` | present (line 53) | same |
| `requires_recompose` | present (line 54) | same |
| `current_subtitle_source` | `target_subtitle_source` (line 41) | same |
| `dub_current` | present (line 45) | same |
| `compose_status` | `compose_input_ready`, `compose_execute_allowed` (lines 47-50) | same |

`ref_id` enum readiness for Workbench dispatch:

| Line | Required `ref_id` literals | Present in schema |
| --- | --- | --- |
| matrix_script | `matrix_script_variation_matrix`, `matrix_script_slot_pack` | YES — `schemas/packets/matrix_script/packet.schema.json:30-76` |
| digital_anchor | `digital_anchor_role_pack`, `digital_anchor_speaker_plan` | YES — `schemas/packets/digital_anchor/packet.schema.json` |
| hot_follow | `hot_follow_subtitle_authority`, `hot_follow_dub_compose_legality` | YES — referenced by current panel design and consumed by the same resolver pattern |

## 5. Additive-fixable gaps

These are projection-only additions. Each derives from fields that already exist; none changes packet truth, line closure truth, or four-layer authority. Each can be added as a derived projection (L4 read-side) without writing back to L2/L3.

### Gap A1 — Per-packet `publishable` boolean for Board's third bucket

- **What's missing:** A single explicit `publishable` field on the Board-card projection. Today this state is implicit in the conjunction of `ready_gate.publish_ready`, `ready_gate.compose_ready`, and absence of `ready_gate.blocking[]`.
- **Authoritative source:** `ready_gate.*` (already L4-derived).
- **Additive shape:** `board_card.publishable: bool = ready_gate.publish_ready and ready_gate.compose_ready and not ready_gate.blocking`. Sibling `board_card.head_reason: str | null` derived from the first canonicalized `ready_gate.blocking[]` entry (or specific `*_reason` field).
- **Why additive:** The boolean is a derived view of L4 fields already projected; it does not move authority from `ready_gate_runtime` into the UI and does not introduce new truth. Doc deferral path is honored: if the projection is absent at wiring time, the design states the `publishable` bucket renders empty.

### Gap A2 — Single derived publish gate on Delivery

- **What's missing:** A single boolean `delivery.publish_gate` plus a single `delivery.publish_gate_head_reason` mirroring the Board chip text. Today the gate is implicit in `ready_gate.{compose_ready, compose_allowed, compose_execute_allowed, publish_ready}` plus final-freshness checks.
- **Authoritative source:** `ready_gate.*` (already L4-derived) + L2 `final.*` freshness facts.
- **Additive shape:** AND of (`compose_ready`, `publish_ready`, `final.exists`, no `final_stale_reason`); head reason = first canonicalized blocker. Optional items (`scene_pack`, `pack_zip`, `edit_bundle_zip`, helper / attribution exports) are explicitly **excluded** from the AND inputs and continue to be enumerated separately via the existing `required: bool` flag on `factory_delivery_contract` deliverables.
- **Why additive:** Both inputs already exist; no new field on the packet, no truth ownership change. Delivery remains a read-only mirror.

### Gap A3 — L4 publish-feedback mirror surfaced on Delivery zone D

- **What's missing:** A read-only mirror of `last_publish_timestamp`, `publish_status`, `publish_channel` reachable from the Delivery surface.
- **Authoritative source:** Publish status is **task-owned** (`docs/contracts/status_ownership_matrix.md:39`), not packet-owned, and is already produced by Phase D.1 publish-feedback closure write-back for matrix_script and digital_anchor (`gateway/app/services/digital_anchor/publish_feedback_closure.py`; matrix_script Phase D.1 evidence in index).
- **Additive shape:** Delivery presenter selects the existing task-side publish-feedback closure record into a `delivery.publish_status_mirror.{last_published_at, status, channel}` projection. No write-back, no packet mutation.
- **Why additive:** Reads task truth that already exists; respects the rule that packet envelope must not carry operational publish status.

## 6. Authority risks / blocked items

None for Board / Workbench / Delivery / Hot Follow panel.

The single observed authority hazard would be **writing publish-status fields onto the packet envelope**. The packet envelope contract (`docs/contracts/factory_packet_envelope_contract_v1.md:96`) and forbidden-metadata flags (`delivery_ready`, `final_ready`, `publishable`, `done`, `phase`) explicitly forbid this. Gap A3 above avoids the hazard by reading task-side publish-feedback closure rather than mutating the packet.

Out-of-scope (explicitly NOT diagnosed in this memo, per the directive):

- B-roll Action Area (Reference / Promote / Mark canonical / Link) and B-roll filter API — blocked on product freeze of the seven open questions in `docs/design/broll_asset_supply_lowfi_v1.md` and the architect review §"Product Freeze Items".

## 7. Recommended minimal wiring path

Projection-only, additive, no truth movement. Each step independently shippable. **No work is started by this memo** — this is the path that, when commissioning resumes, would minimize risk.

1. **Board card projection extension.** Add `board_card.publishable` and `board_card.head_reason` as derived fields in the existing task-view presenter (`gateway/app/services/task_view_presenters.py`), reading `ready_gate.*` already produced by `ready_gate_runtime`. No new state, no new write path. Behind a presenter-level feature flag if desired.
2. **Delivery publish-gate projection.** Add `delivery.publish_gate` + `delivery.publish_gate_head_reason` to the delivery binding presenter for each line (`gateway/app/services/matrix_script/delivery_binding.py`, `gateway/app/services/digital_anchor/delivery_binding.py`, plus the equivalent path for hot_follow). Optional items continue to surface via existing `required: bool` and are excluded from the gate inputs.
3. **Delivery publish-status mirror projection.** Project the existing task-side publish-feedback closure record into the delivery presenter as `delivery.publish_status_mirror.*`. No write path is added.
4. **Workbench `line_specific_refs[]` resolver registry.** Promote the per-line ad-hoc `_line_ref(packet, ref_id)` lookups into a single shared resolver returning `{panel_kind, ref_payload}` for the design's frozen ref_id enums. This is a refactor of existing code, not new truth.

Each of these items maps 1:1 to a confirmation item from the architect review §"Engineering Wiring Confirmation Items" and removes the corresponding gating risk for Phase-3 UI wiring.

## 8. State sync write-back completed

- Wrote this memo: `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
- Wrote evidence: `docs/execution/evidence/operator_visible_surface_wiring_feasibility_v1.md`
- Updated active execution log: `docs/execution/logs/PHASE2_PROGRESS_LOG.md` (new node "Phase 2 Operator-Visible Surface Wiring Feasibility Memo")
- Updated evidence index: `docs/execution/apolloveo_2_0_evidence_index_v1.md` (new row under Phase 2 design / wiring evidence)

## Hard stop

Per the directive, work stops here. No frontend implementation, no field implementation, no B-roll wiring. Awaiting product freeze of the seven B-roll open questions and the next commissioning instruction.
