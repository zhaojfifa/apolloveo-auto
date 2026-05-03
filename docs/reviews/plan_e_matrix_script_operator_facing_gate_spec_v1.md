# Plan E — Matrix Script Operator-Facing Implementation Gate Spec v1

Date: 2026-05-03
Status: **Documentation only. No code, no UI, no contract, no schema, no test, no template change. No file moves. No directory restructure.** This document is the formal gate specification for the next operator-visible implementation wave. It defines the only allowed implementation scope, the binding forbidden scope, the PR slicing plan, the acceptance evidence, and the preserved freezes for **Matrix Script operator-facing implementation only**. It does not authorize any code change by itself; an implementation PR may begin only after this gate spec is reviewed and approved through its own approval block (§10).

Authority of creation:

- [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §3.1, §7.1, §7.2, §7.3, §7.6 — frozen next engineering sequence + sequence-wide red lines.
- [docs/execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md) §3 (operational definition of Plan E pre-condition #1) and §4 (Plan E gate-spec authoring authorization, signed 2026-05-03 by Jackie / Raobin / Alisa).
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](operations_upgrade_gap_review_and_ops_plan_v1.md) §11 "Plan E — Next Operator-visible Implementation Gate" + §13 final gate decision.
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) §6 / §7 (current wave permitted / forbidden scope).
- [docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md) (Matrix Script wave authority that this gate spec extends).
- [docs/architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) (gated by this gate spec's closure + a subsequent Plan E phase set; **NOT** unblocked here).
- [docs/architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) (gated by Platform Runtime Assembly signoff; **NOT** touched here).

If wording in this gate spec ever conflicts with any of the above, the underlying authority wins and this gate spec is updated.

---

## 0. Scope Disclaimer (binding)

This gate spec covers **Matrix Script operator-facing implementation** only. It is the **first** Plan E phase. It is not the entire historical Plan E candidate list from the gap review §11; the broader candidates (Digital Anchor B1/B2/B3 implementation, Asset Library / promote services + UI, L4 advisory producer/emitter, L3 `final_provenance` emitter, unified `publish_readiness` producer, workbench panel dispatch contract object conversion, operator-driven Phase B authoring) are **explicitly deferred** to subsequent Plan E phase gate specs that must be authored separately when their own pre-conditions are met.

This gate spec:

- authorizes implementation work **only** for the items enumerated in §3
- does **not** authorize any item enumerated in §4
- does **not** start Platform Runtime Assembly (any phase A–E)
- does **not** start Capability Expansion (any of W2.2 / W2.3 / durable persistence / runtime API / third line)
- does **not** unfreeze Digital Anchor in any way
- does **not** reopen Hot Follow business behavior
- does **not** mutate any frozen contract; if a contract amendment is required by an in-scope item, the amendment must land **first** in a documentation-only PR, with this gate spec updated to cite the amendment

---

## 1. Purpose

The purpose of this gate spec is to specify exactly what Matrix Script operator-facing implementation may be built next, so that:

1. The Operator-Visible Surface Validation Wave can close on Matrix Script becoming a fully operator-truth-bearing line — not "operator-visible contract + projection truth + inspect-only Delivery Center", which is the current state per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §10.
2. The transitional `<token>` operator-discipline convention pinned by §8.F / §8.H of [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.2 can be retired in favor of a product-owned minting flow (Option F2), without breaking forward compatibility for handles minted under the operator-discipline convention.
3. No implementation work outside the Matrix Script operator-facing scope is permitted to enter `main` under cover of this gate, preserving the Digital Anchor freeze, the Hot Follow baseline, the cross-line plumbing freeze, and the platform-runtime-assembly gate.
4. The PR slicing plan and acceptance evidence are pre-defined so that the Reviewer / Merge Owner can close the wave independently without scope creep.

This document is a **specification**, not an implementation; nothing is built by authoring it.

---

## 2. Entry Conditions

The Plan E Matrix Script operator-facing implementation phase MAY NOT begin before **all** of the following entry conditions hold. Each condition is verifiable from the listed artifact at the listed location; no condition is satisfied by assertion in this document.

| # | Entry condition | Verification artifact | Status as of 2026-05-03 |
| --- | --- | --- | --- |
| E1 | Plan A live-trial signed closeout recorded — capture template §6 carries date/time + signature/handle for Jackie / Raobin / Alisa; closeout verdict recorded by coordinator/architect/reviewer concurrence. | [PLAN_A_SIGNOFF_CHECKLIST_v1.md §6](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md), [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md §6](../execution/PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) | **SATISFIED** for gate-spec authoring (Jackie 2026-05-03 11:11; Raobin 2026-05-03 11:18; Alisa 2026-05-03 11:45) |
| E2 | Plan E pre-condition #1 satisfied per [PLAN_A_SIGNOFF_CHECKLIST_v1.md §3](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md) (5 conjunctive conditions: §12 conditions all `[x] yes`; sample-criterion boxes flipped or annotated `N/A — Plan E gated`; capture-template §6 fully signed; §7 handoff readiness; closeout verdict recorded). | [PLAN_A_SIGNOFF_CHECKLIST_v1.md §3](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md) | **SATISFIED** for gate-spec authoring per checklist §4 |
| E3 | Plan B / C / D contract freeze remains binding — no amendment except additive ones that this gate spec explicitly cites; no removal. | [PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) | **SATISFIED** (PR #80 / commit `6052014`; only additive Matrix Script §8.A / §8.C / §8.F addenda on `task_entry_contract_v1.md` and additive `Shared shell neutrality` addendum on `workbench_panel_dispatch_contract_v1.md`) |
| E4 | Matrix Script Plan A trial corrections §8.A → §8.H all PASS; Matrix Script live-run BLOCK released by virtue of §8.H land. | [ENGINEERING_STATUS.md "Current Completion"](../../ENGINEERING_STATUS.md) | **SATISFIED** |
| E5 | Hot Follow baseline preserved — no commits to `gateway/app/services/hot_follow_*`, `tasks.py` Hot Follow paths, or `hot_follow_api.py` business logic since `ca20c60` (2026-02-17), per gap review §4 + §7.1. | [operations_upgrade_gap_review_and_ops_plan_v1.md §4 / §7.1](operations_upgrade_gap_review_and_ops_plan_v1.md) | **SATISFIED** |
| E6 | Digital Anchor freeze preserved — no operator submission path; New-Tasks card and `/tasks/connect/digital_anchor/new` hidden / disabled / preview-labeled per Plan A §2.1 / §12 condition 2. | [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §3.2 / §3.3](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [PLAN_A_SIGNOFF_CHECKLIST_v1.md §1.2](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md) | **SATISFIED** |
| E7 | This gate spec reviewed and approved through its own approval block (§10) by architect (Raobin) and reviewer (Alisa). | This document §10 | **PENDING** — implementation is BLOCKED until this row flips |

When E1 → E7 all hold, and only then, an implementation PR within the §3 allowed scope MAY open. Until E7 is signed, no implementation work is authorized.

---

## 3. Allowed Implementation Scope for Matrix Script (binding, exhaustive)

This Plan E phase authorizes implementation of **only** the items enumerated below. Each item is bound to the contract truth that already exists; no contract is invented by this gate spec. Each item is operator-facing for Matrix Script specifically; cross-line plumbing is **not** in scope unless explicitly listed.

### 3.1 Item E.MS.1 — Matrix Script `result_packet_binding.artifact_lookup` implementation (B4)

- **What it is.** Replace the five `not_implemented_phase_c` placeholder rows currently emitted at [gateway/app/services/matrix_script/delivery_binding.py:93-125](../../gateway/app/services/matrix_script/delivery_binding.py) with a real artifact-lookup that resolves Matrix Script Delivery Center deliverable rows against L2 artifact facts per the contract.
- **Contract authority.** [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md) (Plan B B4; frozen 2026-05-02 in PR #80 / commit `6052014`).
- **Operator-visible result.** Matrix Script Delivery Center transitions from "inspect-only with `not_implemented_phase_c` placeholder rows" (Plan A §3.2 / §6.2) to "operator-truth: deliverable rows resolved to real artifact references". Operators may rely on Matrix Script Delivery Center for the variation-aware deliverable surface.
- **Operator-visible boundary preserved.** No row mutation; no operator-driven re-binding affordance; no manual artifact-lookup override; no provider/model surface; no Hot Follow Delivery Center change; no Digital Anchor Delivery Center change.
- **Pre-condition specific to this item.** None beyond E1 → E7. The contract is frozen and complete.

### 3.2 Item E.MS.2 — Matrix Script Option F2 in-product `content://` minting flow

- **What it is.** Implement the in-product minting service that mints opaque `content://matrix-script/source/<token>` handles on operator request, replacing the operator-discipline `<token>` convention pinned by §8.F / §8.H of the trial brief. The product owns `<token>` allocation and uniqueness; operators request a handle from a UI affordance instead of choosing `<token>` themselves.
- **Contract authority.** [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)" — specifically the `Operator transitional convention` sub-section that names Option F2 as "the eventual minting-service resolution path that replaces the operator-discipline `<token>` convention".
- **Operator-visible result.** `/tasks/matrix-script/new` form (or a small upstream affordance) gains an operator action that requests a fresh handle from the product; the operator then submits that handle in the `source_script_ref` field. The four-scheme accepted set (`content` / `task` / `asset` / `ref`) and the §8.A / §8.F shape rules are unchanged. Existing handles minted under the operator-discipline convention remain valid (no operator migration).
- **Operator-visible boundary preserved.** `source_script_ref` remains an asset identity handle (per §0.2 product-meaning); it is **not** turned into a body-input field, **not** a publisher-URL ingestion field, and **not** a currently dereferenced content address. The product owns `<token>` allocation; the product still does not dereference the handle to body content within this Plan E phase. Asset-Library-side promote / asset-library object service work is **not** included in this item.
- **Pre-condition specific to this item.** None beyond E1 → E7. The contract addendum is frozen and complete.

### 3.3 Item E.MS.3 — Matrix Script Delivery Center per-deliverable `required` / `blocking_publish` rendering (in-scope only because Item E.MS.1 demands a coherent delivery surface)

- **What it is.** Render the `required` and `blocking_publish` boolean fields per deliverable row on Matrix Script Delivery Center, sourced from the Plan C amendment to [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md). After Item E.MS.1 lands, deliverable rows resolve to real artifact references; this item makes the `required` / `blocking_publish` zoning visually meaningful on the Matrix Script Delivery Center.
- **Contract authority.** [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) Plan C amendment (`required` / `blocking_publish` / `scene_pack_blocking_allowed: false`); frozen 2026-05-02 in PR #80 / commit `6052014`.
- **Operator-visible result.** Matrix Script Delivery Center rows show "required (blocks publish)" vs "optional (never blocks publish)" zoning; scene-pack-style derivatives (if any are emitted by Matrix Script) are explicitly non-blocking per `scene_pack_blocking_allowed: false`.
- **Operator-visible boundary preserved.** Hot Follow Delivery Center is **not** changed by this item — Hot Follow's existing per-deliverable zoning logic stays as it is; the Matrix Script-specific renderer consumes the contract fields without re-touching Hot Follow code paths. Digital Anchor Delivery Center is **not** changed (Digital Anchor remains frozen, no operator submission path, so Digital Anchor Delivery Center is not reachable in this wave).
- **Pre-condition specific to this item.** Item E.MS.1 ships in the same wave (this item is operator-meaningless without resolved deliverable rows). May ship before, with, or after E.MS.1 within the same wave; if E.MS.1 is descoped, this item is also descoped.

### 3.4 Closed scope check (anti-creep)

The complete enumeration of in-scope items for this Plan E phase is exactly **{E.MS.1, E.MS.2, E.MS.3}**. Any item not in this set is governed by §4 (forbidden scope) and is BLOCKED from this wave. Reviewer / Merge Owner enforces this check on every PR.

---

## 4. Forbidden Scope (binding, exhaustive within Plan E candidate space)

This Plan E phase **does not** authorize implementation of any of the items below. Each is contract-frozen or contract-pending elsewhere and waits on its own subsequent Plan E phase gate spec, on a different wave, or on indefinite deferral. The list is binding; Reviewer / Merge Owner rejects any PR that lands one of these.

### 4.1 Forbidden — Digital Anchor implementation (preserves Digital Anchor freeze)

- Digital Anchor `create_entry_payload_builder` (Plan B B1) — contract at [docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md](../contracts/digital_anchor/create_entry_payload_builder_contract_v1.md); **no implementation in this Plan E phase**.
- Digital Anchor formal `/tasks/digital-anchor/new` route (Plan B B2) — contract at [docs/contracts/digital_anchor/new_task_route_contract_v1.md](../contracts/digital_anchor/new_task_route_contract_v1.md); **no implementation in this Plan E phase**.
- Digital Anchor Phase D.1 publish-feedback write-back (Plan B B3) — contract at [docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md](../contracts/digital_anchor/publish_feedback_writeback_contract_v1.md); **no implementation in this Plan E phase**.
- Digital Anchor Phase B render production path; Digital Anchor New-Tasks card promotion to operator-eligible; removal of the Plan A §2.1 hide guards or the temp `/tasks/connect/digital_anchor/new` route — **all forbidden**.
- Digital Anchor Delivery Center surface; Digital Anchor Workbench role/speaker panel mount; any operator submission affordance reaching Digital Anchor — **all forbidden**.

### 4.2 Forbidden — Cross-line operator-surface implementation (preserves no-platform-wide-expansion)

- Asset Library object service (no `gateway/app/services/asset_library/` runtime) — contract at [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md); **no implementation in this Plan E phase**.
- Asset Supply / B-roll page UI; per-line input/deliverable Asset Supply matrix surface beyond what is shipped; reference-into-task pre-population from Asset Library — **all forbidden**.
- Promote intent service / submit affordance — contract at [docs/contracts/promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md); **no implementation in this Plan E phase**.
- Promote closure service / admin review UI — contract at [docs/contracts/promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md); **no implementation in this Plan E phase**.
- Unified `publish_readiness` producer consumed by Board / Workbench / Delivery (D1) — contract at [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md); **no implementation in this Plan E phase** (Board / Workbench / Delivery continue to re-derive `publishable` independently per Plan A §6.2; this is drift-tolerated through this wave too).
- L3 `final_provenance` emitter (D2) — contract amendment on [docs/contracts/hot_follow_current_attempt_contract_v1.md](../contracts/hot_follow_current_attempt_contract_v1.md); **no implementation in this Plan E phase** (UI continues to infer current-vs-historical from `final_fresh` + timestamps per Plan A §5.2).
- Workbench panel dispatch contract OBJECT conversion (D3) — contract at [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md); the in-code dict at [gateway/app/services/operator_visible_surfaces/projections.py:239-246](../../gateway/app/services/operator_visible_surfaces/projections.py) stays as the dispatch source; **no conversion to a contract-loaded object in this Plan E phase**.
- L4 advisory producer / emitter (D4) — contract at [docs/contracts/l4_advisory_producer_output_contract_v1.md](../contracts/l4_advisory_producer_output_contract_v1.md); no `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` is created in this Plan E phase; advisory rows continue to be empty per Plan A §3.2 / §6.1.

### 4.3 Forbidden — Matrix Script scope creep (preserves Matrix Script frozen truth)

- Operator-driven Phase B authoring (axes / cells / slots authored on operator command) — pinned as Plan E future work in [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §"Phase B deterministic authoring (addendum, 2026-05-03)" but **NOT this Plan E phase**. The §8.C deterministic authoring continues to run once at task creation only; the panel stays read-only.
- Matrix Script `target_language` enum widening beyond `{mm, vi}` — **forbidden**; the closed set at [gateway/app/services/matrix_script/create_entry.py:44](../../gateway/app/services/matrix_script/create_entry.py) is part of the §8.A / §8.F-tightened entry contract.
- Matrix Script canonical-axes set widening beyond `{tone, audience, length}` — **forbidden** in this Plan E phase per the §8.C addendum.
- Matrix Script Workbench shell mutation (e.g. removing or weakening §8.E shared-shell suppression; re-introducing Hot Follow stage cards on `kind=matrix_script`) — **forbidden**; the §"Shared shell neutrality" addendum on `workbench_panel_dispatch_contract_v1.md` is binding.
- Matrix Script `source_script_ref` accepted-scheme set re-widening (e.g. re-adding `https` / `http` / `s3` / `gs`) — **forbidden** per §8.F. Option F2 (this Plan E phase) **mints into** the four opaque-by-construction schemes; it does not unfreeze the scheme set.
- Repurposing `source_script_ref` as a body-input field, publisher-URL ingestion field, or currently dereferenced content address — **forbidden** per §0.2 product-meaning.

### 4.4 Forbidden — Hot Follow mutation (preserves Hot Follow baseline)

- Any change to Hot Follow business behavior; any commit to `gateway/app/services/hot_follow_*`, `tasks.py` Hot Follow paths, `hot_follow_api.py` business logic, or `hot_follow_workbench.html` business behavior — **forbidden**.
- Any new Hot Follow feature; any cleanup of `tasks.py` (3,480 lines), `hot_follow_api.py` (2,325 lines), or `task_view.py::build_hot_follow_workbench_hub()` (492 lines) — **forbidden** (Hot Follow structural debt is deferred to Platform Runtime Assembly Wave per [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md)).
- Any change to Hot Follow Delivery Center per-deliverable zoning code paths — **forbidden** (Item E.MS.3 touches Matrix Script Delivery Center only).
- Any change to Hot Follow advisory rendering — **forbidden** (D4 producer is gated to a later Plan E phase, not this one).

### 4.5 Forbidden — Platform / capability / vendor (preserves Platform Runtime Assembly gate)

- Platform Runtime Assembly Phases A–E (Shared Logic Port Merge / Compose Service Extraction / Declarative Ready Gate / Runtime Assembly Skeleton / OpenClaw stub) — **forbidden**; gated on this Plan E phase + subsequent Plan E phases closing successfully, then a separate wave start authority per [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md). **Plan E does NOT equal Platform Runtime Assembly**.
- Capability Expansion (W2.2 Subtitles / Dub Provider; W2.3 Avatar / VideoGen / Storage Provider; durable persistence backend formalization; runtime API / callback handler formalization; third production line commissioning) — **forbidden**; gated on Platform Runtime Assembly signoff per [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md).
- Provider / model / vendor / engine controls or selectors on any operator-visible surface — **forbidden** at all phases per validator R3 ([docs/contracts/factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md) R3) and the design-handoff red line 6.
- Donor namespace import (`from swiftcraft.*`) — **forbidden** per [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md).
- React/Vite full frontend rebuild; cross-line studio shell; tool catalog page — **forbidden** per [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) and Plan A §4.1.
- Any routing change that exposes a discovery-only surface as operator-eligible (Asset Supply page; promote intent submit; Digital Anchor New-Tasks card click target; `/tasks/connect/digital_anchor/new`; Matrix Script Delivery Center placeholder rows promoted prematurely) — **forbidden**.

### 4.6 Forbidden — Implementation prep disguised as code slicing

- Authoring "skeleton" code paths, stub services, dead-code feature flags, or future-work scaffolding for §4.1 / §4.2 / §4.3 / §4.5 items under cover of an Item E.MS.* PR — **forbidden**. Each Item E.MS.* PR must touch only the surfaces, services, templates, and tests required by its own contract.
- Drawing in adjacent refactors (compose extraction, router thinning, panel dispatch contract-object conversion, ready-gate declarative conversion) under cover of an Item E.MS.* PR — **forbidden**. These are Platform Runtime Assembly items; they wait for that wave.

---

## 5. PR Slicing Plan

Each PR in this Plan E phase MUST be:

- **single-item:** touches exactly one of {E.MS.1, E.MS.2, E.MS.3}; cross-item dependencies are honored across PRs in the order below.
- **scope-fenced:** files touched are bounded by the per-item file-fence in §5.1 / §5.2 / §5.3; any deviation requires gate-spec amendment (a documentation-only PR).
- **regression-bounded:** business regression set defined per item in §5.4; merge gate per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md) requires the regression to be green.
- **independently revertable:** each PR may be rolled back without disturbing the other items; if Item E.MS.3 lands first, Item E.MS.1 must remain inspect-only-compatible behind it.
- **review-citable:** each PR cites this gate spec and the item-specific contract authority; the citation set is mandatory per [ENGINEERING_RULES.md §6, §9](../../ENGINEERING_RULES.md).

### 5.1 PR-1 — Item E.MS.1 (Matrix Script B4 artifact lookup)

- **Scope.** Implement the artifact-lookup function inside [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py) per [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md). Replace the five `not_implemented_phase_c` placeholder strings at lines 93 / 101 / 109 / 117 / 125 with real lookup output. Add a unit-test module exercising the lookup against fixture packets per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md).
- **Files allowed to change.**
  - `gateway/app/services/matrix_script/delivery_binding.py` (in-place replacement of placeholder rows).
  - One new test file under `gateway/app/services/tests/` (or augmentation of an existing matrix_script delivery test if present).
  - This gate spec (citation update only; closeout marker in §10).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. Any cross-line projection / advisory / publish_readiness file. Any Workbench template. Any router file beyond removing the `not_implemented_phase_c` consumer hint comment if present and trivial.
- **Contract changes.** None. The contract is frozen.
- **Operator-visible delta.** Matrix Script Delivery Center rows now resolve to real artifact references for variation deliverables; the placeholder strings disappear from the operator-visible payload for `kind=matrix_script` only.
- **Out-of-scope reminder.** No `required` / `blocking_publish` rendering on Delivery Center (that is Item E.MS.3); no operator-driven re-binding affordance; no provider/model surface; no Hot Follow Delivery Center change; no Digital Anchor Delivery Center change.

### 5.2 PR-2 — Item E.MS.2 (Matrix Script Option F2 in-product `content://` minting flow)

- **Scope.** Implement the in-product minting service per the §"Source script ref shape" addendum on [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md). Add a service that mints opaque `content://matrix-script/source/<token>` handles on operator request, with `<token>` allocated by the product. Add a small operator-facing affordance on the `/tasks/matrix-script/new` form (or upstream) that requests a fresh handle. Update the form's helper text to name the minting affordance alongside the operator transitional convention so existing handles minted under the operator-discipline convention remain valid.
- **Files allowed to change.**
  - One new service file under `gateway/app/services/matrix_script/` (e.g. `source_script_ref_minting.py` or similar; final naming chosen at PR time within the service directory).
  - `gateway/app/templates/matrix_script_new.html` (operator affordance + helper text update; constrained to the minting affordance only — no other field changes).
  - One or more router changes inside `gateway/app/routers/tasks.py` strictly limited to a new POST endpoint for minting (no Hot Follow router changes; no Digital Anchor router changes; no temp-route promotion).
  - One new test module under `gateway/app/services/tests/`.
  - The contract addendum on `task_entry_contract_v1.md` may be **extended** with an additive sub-section documenting the landed minting service shape (operator request envelope; product response envelope; `<token>` allocation policy; backward-compatibility statement). This contract extension is documentation-only and lands in PR-2 alongside the implementation.
  - This gate spec (citation update only; closeout marker in §10).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. Any cross-line projection / advisory / publish_readiness file. The §8.A `_validate_source_script_ref_shape` guard (it stays as is; minted handles must pass the same guard). The §8.F-tightened scheme set (it stays as `{content, task, asset, ref}`; the minting service mints into `content://` only).
- **Contract changes.** Additive sub-section on `task_entry_contract_v1.md` only; no replacement of existing rules; no removal; no scheme-set widening; no shape change to existing fields.
- **Operator-visible delta.** Operators may now click an affordance to request a fresh handle from the product; the form helper text describes both the minting affordance (preferred for new samples) and the operator transitional convention (still accepted; no migration required).
- **Out-of-scope reminder.** No Asset-Library-side interaction; no promote intent affordance; no asset-library object service; no asset-library page; no minting service for Hot Follow or Digital Anchor; no minting service for any non-`content://` scheme; no automatic resolution / dereferencing of minted handles to body content (the product still does not dereference handles in this Plan E phase).

### 5.3 PR-3 — Item E.MS.3 (Matrix Script Delivery Center per-deliverable `required` / `blocking_publish` rendering)

- **Scope.** Render `required` and `blocking_publish` per deliverable row on the Matrix Script Delivery Center surface only, sourced from the Plan C amendment to [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md). Make scene-pack-style derivatives explicitly non-blocking per `scene_pack_blocking_allowed: false`.
- **Files allowed to change.**
  - The Matrix Script Delivery Center projection / template path (typically `gateway/app/services/matrix_script/delivery_binding.py` row shape extension and the corresponding Delivery Center template — the exact path is identified at PR time, but it is constrained to Matrix Script-scoped surfaces).
  - One new test module under `gateway/app/services/tests/` covering the zoning rendering per row kind.
  - This gate spec (citation update only; closeout marker in §10).
- **Files NOT allowed to change.**
  - Any Hot Follow file (Hot Follow Delivery Center renders `required` / `blocking_publish` already through its own zoning logic — this PR is **not** authorized to touch that path; Hot Follow's logic stays as-is). Any Digital Anchor file. Any cross-line `derive_delivery_publish_gate` re-derivation in `projections.py` (that re-derivation stays independent until a later Plan E phase consolidates it; this PR consumes the contract fields on the Matrix Script row only).
- **Contract changes.** None. The contract amendment is frozen (Plan C).
- **Operator-visible delta.** Matrix Script Delivery Center rows now show explicit `required (blocks publish)` vs `optional (never blocks publish)` zoning, after Item E.MS.1 lands the resolved deliverable rows.
- **Out-of-scope reminder.** No unified `publish_readiness` producer; no L3 `final_provenance` emit; no cross-line consolidation of publishable re-derivation; no Hot Follow Delivery Center change.

### 5.4 Per-item business regression scope (mandatory per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md))

- **PR-1 (E.MS.1).** Hot Follow golden path (publish completes); Matrix Script Phase B inspection on a fresh contract-clean sample (axes/cells/slots resolve per §8.G); Matrix Script Delivery Center deliverable rows render real artifact references on the same sample (no `not_implemented_phase_c` strings observed on the Matrix Script payload); Hot Follow Delivery Center unchanged (rows render exactly as before — bytewise diff acceptable as evidence).
- **PR-2 (E.MS.2).** §8.A guard regression (body-text rejection on `source_script_ref` still HTTP 400); §8.F guard regression (publisher-URL / bucket-URI rejection still HTTP 400 with `"scheme is not recognised"`); minting affordance returns a `content://matrix-script/source/<product-minted-token>` handle that passes the §8.A + §8.F guards on round-trip; pre-§8.F operator-discipline handles (`content://matrix-script/source/op-token-001`) still accepted (no operator migration).
- **PR-3 (E.MS.3).** Matrix Script Delivery Center renders `required` / `blocking_publish` zoning correctly per row kind on a fresh contract-clean sample; scene-pack-style derivative (if any) is rendered as `optional, never blocks publish`; Hot Follow Delivery Center unchanged.

### 5.5 PR ordering

PR-1 lands first (operator-meaningful Delivery Center requires resolved rows). PR-3 lands second (zoning is operator-meaningless without resolved rows). PR-2 may land in parallel with PR-1 / PR-3 (the minting flow has no dependency on Delivery Center). All three may land in this Plan E phase wave, in any consistent order respecting the PR-1 → PR-3 dependency.

---

## 6. Acceptance Evidence

This Plan E phase closes only when **all** acceptance evidence below is recorded under [docs/execution/](../execution/) and signed off through the §10 approval block. Each row enumerates the closing artifact and the verification recipe.

| # | Acceptance row | Evidence artifact | Verification recipe |
| --- | --- | --- | --- |
| A1 | Item E.MS.1 implementation landed; `not_implemented_phase_c` placeholder rows retired from Matrix Script Delivery Center. | New execution log under `docs/execution/PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md`; PR commit SHA recorded; per-row before/after diff. | Static grep: `grep -n "not_implemented_phase_c" gateway/app/services/matrix_script/delivery_binding.py` returns zero matches. Live: a fresh contract-clean Matrix Script sample shows real artifact references in Delivery Center rows. |
| A2 | Item E.MS.2 implementation landed; in-product minting service operational; helper text updated; contract addendum extension landed in the same PR. | New execution log under `docs/execution/PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md`; PR commit SHA recorded. | Static: minting service request returns a `content://matrix-script/source/<product-minted-token>` handle that passes `_validate_source_script_ref_shape` and `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES`. Live: an operator submits a fresh sample using a minted handle; task creation succeeds; pre-§8.H operator-discipline handles still accepted on a separate sample. |
| A3 | Item E.MS.3 implementation landed; Matrix Script Delivery Center renders `required` / `blocking_publish` zoning correctly. | New execution log under `docs/execution/PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md`; PR commit SHA recorded. | Static: per-deliverable row carries `required` / `blocking_publish` derivable from the contract fields. Live: a Matrix Script Delivery Center page on a fresh sample shows the zoning per row kind; scene-pack-style derivative is `optional, never blocks publish`. |
| A4 | Hot Follow baseline preserved across PR-1 / PR-2 / PR-3. | Bytewise / behavioral regression report appended to each execution log. | Hot Follow golden path PASS on each PR; no commits to Hot Follow files; no Hot Follow Delivery Center change observed. |
| A5 | Digital Anchor freeze preserved across PR-1 / PR-2 / PR-3. | Per-PR confirmation appended to each execution log. | No commits to `gateway/app/services/digital_anchor/*` runtime; no commits to `gateway/app/templates/digital_anchor*`; no operator submission affordance for Digital Anchor reachable in the deployed environment; Plan A §2.1 hide guards still in force. |
| A6 | No forbidden item from §4 has landed. | Per-PR scope-fence check appended to each execution log; final closeout audit appended to a new aggregating execution log under `docs/execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md`. | Reviewer / Merge Owner audits each PR's file-touched list against §5.1 / §5.2 / §5.3; aggregating closeout confirms no §4 item present in the merged tree. |
| A7 | Plan E phase closeout signoff recorded. | `docs/execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md` §"Closeout signoff"; this gate spec §10 closeout marker filled. | Architect (Raobin) + Reviewer (Alisa) sign the closeout block; Operations team coordinator (Jackie) confirms operator-visible deltas observed in the trial environment. |

When A1 → A7 all hold, this Plan E phase is closed; the next Plan E phase gate spec MAY be authored (separately) for Digital Anchor or Asset Library or any other forbidden-this-wave item from §4. Platform Runtime Assembly remains BLOCKED until a separate "Plan E phases all closed + Platform Runtime Assembly start authority" decision is recorded.

---

## 7. Preserved Freezes (binding)

This Plan E phase preserves the following freezes. Each freeze is restated here so the Reviewer / Merge Owner enforces them on every PR; each freeze is bound to its native authority and cannot be relaxed by this gate spec.

### 7.1 Hot Follow baseline only, no behavior reopen

- Hot Follow remains the operational baseline line for ApolloVeo 2.0 per [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) and [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md). No commits to Hot Follow business behavior under this gate spec; the Hot Follow structural debt (`tasks.py` 3,480 lines / `hot_follow_api.py` 2,325 lines / `task_view.py::build_hot_follow_workbench_hub()` 492 lines) is **deferred to Platform Runtime Assembly Wave** and is out of scope for any Item E.MS.* PR.
- Hot Follow Delivery Center is **not** touched by Item E.MS.3; Hot Follow's existing per-deliverable zoning logic stays as it is.
- Hot Follow advisory rendering is **not** touched (D4 producer is gated to a later Plan E phase).
- Hot Follow's existing re-derivation of `publishable` / `publish_gate` continues; unification with Matrix Script is **not** in this Plan E phase.

### 7.2 Digital Anchor remains frozen / no submission path

- Digital Anchor remains inspect-only / contract-aligned per [unified map §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) and Plan A §2.1 / §12 condition 2.
- Digital Anchor New-Tasks card click target ([gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html)) and the temp `/tasks/connect/digital_anchor/new` route stay hidden / disabled / preview-labeled in the trial environment under Plan A §2.1.
- The formal `/tasks/digital-anchor/new` route is **not** implemented under this gate spec.
- Digital Anchor Phase D.1 publish-feedback write-back is **not** implemented under this gate spec.
- Digital Anchor `create_entry_payload_builder` is **not** implemented under this gate spec.
- Digital Anchor Phase B render production path is **not** built under this gate spec.
- Digital Anchor Workbench role/speaker panel is **not** mounted as an operator-facing surface under this gate spec.

### 7.3 No provider / model / vendor controls

- Provider / model / vendor / engine selectors / controls / consoles are **forbidden at all phases** per validator R3 ([docs/contracts/factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md) R3) and the design-handoff red line 6.
- Operator-visible payloads MUST NOT carry `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any donor namespace identifier per [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). Sanitization is enforced at the operator boundary at [gateway/app/services/operator_visible_surfaces/projections.py:36](../../gateway/app/services/operator_visible_surfaces/projections.py); this guard MUST NOT be relaxed by any Item E.MS.* PR.
- Donor namespace import (`from swiftcraft.*`) is **forbidden** per [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md).

### 7.4 No platform-wide expansion

- This gate spec authorizes Matrix Script operator-facing implementation **only**. It does not authorize Asset Library / promote / asset supply / cross-line publish_readiness producer / cross-line panel dispatch contract object / L4 advisory producer / L3 final_provenance emitter / Digital Anchor implementation.
- Each forbidden cross-line item waits for its **own** subsequent Plan E phase gate spec authoring step. There is no implicit promotion of any §4 item under cover of an Item E.MS.* PR.
- Frontend rebuild (React/Vite full); studio shell; tool catalog page; multi-tenant platform — **all forbidden** per [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) and Plan A §4.1.
- New / third production line commissioning — **forbidden** per [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md).

### 7.5 Plan E does NOT equal Platform Runtime Assembly

- Platform Runtime Assembly is a **separate wave** with its own authority at [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md). It is gated on Plan E phases closing **plus** a separate wave-start authority; its Phases A–E (Shared Logic Port Merge / Compose Service Extraction / Declarative Ready Gate / Runtime Assembly Skeleton / OpenClaw stub) are not touched under this gate spec.
- No "shared logic port merge" prep, "compose service extraction" prep, "declarative ready gate" prep, or "runtime assembly skeleton" prep is permitted under cover of an Item E.MS.* PR.
- Item E.MS.1 / E.MS.2 / E.MS.3 are operator-facing implementation steps for one production line; they do not advance the platform-runtime-assembly agenda. Reviewer / Merge Owner enforces this distinction on every PR.

---

## 8. Posture Preserved by This Gate Spec

| Posture element | State after this gate spec is authored | Authority pointer |
| --- | --- | --- |
| Hot Follow = operational baseline line | preserved — no behavior reopen authorized | [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Matrix Script = next operator-facing line | gate spec authored; implementation BLOCKED until §10 approval | [unified map §4.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Digital Anchor = inspect-only / contract-aligned, no operator submission this wave | preserved — explicit §4.1 + §7.2 forbiddens | [unified map §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Plan A live-trial signed closeout | satisfied for gate-spec authoring | [PLAN_A_SIGNOFF_CHECKLIST_v1.md §6](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md) |
| Plan E gate spec authoring (this document) | **AUTHORED** (this PR) | this gate spec |
| Plan E implementation | **BLOCKED** until §10 approval signoff | this gate spec §2 (E7) + §10 |
| Platform Runtime Assembly | **BLOCKED** until all Plan E phases close + separate wave-start authority | [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) |
| Capability Expansion (W2.2 / W2.3 / durable persistence / runtime API / third line) | **BLOCKED** until Platform Runtime Assembly signoff | [unified map §7.5](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) |
| Frontend patching beyond what is shipped | **BLOCKED** | [unified map §3.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) |
| Provider / model / vendor / engine controls | **forbidden** at all phases | [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), validator R3 |
| Donor namespace import | **forbidden** | [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md) |

---

## 9. What This Gate Spec Does NOT Do

- Does **NOT** implement Item E.MS.1 / E.MS.2 / E.MS.3. Implementation is BLOCKED until §10 approval is signed.
- Does **NOT** authorize any item enumerated in §4. Subsequent Plan E phases for those items require their own gate-spec authoring step under this same discipline.
- Does **NOT** start Platform Runtime Assembly. That wave has its own start authority and is gated on all Plan E phases closing.
- Does **NOT** start Capability Expansion. That wave is gated on Platform Runtime Assembly signoff.
- Does **NOT** unfreeze Digital Anchor. The Digital Anchor freeze stays in force; submission paths stay hidden / disabled / preview-labeled.
- Does **NOT** reopen Hot Follow business behavior. The Hot Follow baseline is preserved.
- Does **NOT** mutate any frozen contract. If an in-scope item requires a contract amendment, the amendment must land first in a documentation-only PR with this gate spec updated to cite the amendment.
- Does **NOT** flip Plan E pre-condition #1 — that is owned by [PLAN_A_SIGNOFF_CHECKLIST_v1.md §3](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md), which has already recorded satisfaction (see §2 entry condition E2 above).
- Does **NOT** modify [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](../execution/PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md), [PLAN_A_SIGNOFF_CHECKLIST_v1.md](../execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md), or [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) — those are upstream authorities that this gate spec consumes.
- Does **NOT** count as a "Plan E gate-spec for the entire Plan E candidate set"; it is the **first** Plan E phase, scoped to Matrix Script operator-facing implementation. Subsequent phases are explicitly out of scope.

---

## 10. Approval Signoff (gate-opening block)

This Plan E phase implementation is BLOCKED until the following block is fully signed. Implementation PRs MUST cite this signed block in their PR body.

```
Architect — Raobin
  Date / time:        <fill: yyyy-mm-dd hh:mm>
  Signature / handle: <fill: Raobin>
  Statement:          I confirm the §3 allowed scope is exhaustively bounded; the
                      §4 forbidden scope is exhaustively listed; the §5 PR slicing
                      plan respects ENGINEERING_RULES.md §1 / §3 / §4 / §6 / §10;
                      the §6 acceptance evidence is verifiable; the §7 preserved
                      freezes match the underlying authorities. I authorize
                      Matrix Script operator-facing implementation under the
                      bounds set by this gate spec only. No Digital Anchor
                      implementation, no platform-wide expansion, no Platform
                      Runtime Assembly is implied by this signoff.

Reviewer — Alisa
  Date / time:        <fill: yyyy-mm-dd hh:mm>
  Signature / handle: <fill: Alisa>
  Statement:          I confirm Plan E pre-condition #1 is satisfied per
                      PLAN_A_SIGNOFF_CHECKLIST_v1.md §3 + §6 (signed 2026-05-03).
                      I confirm the §3 / §4 split has no overlap. I authorize
                      independent merge-gate review of Item E.MS.1 / E.MS.2 /
                      E.MS.3 PRs against this gate spec; I will reject any PR
                      that lands a §4 item or that breaks a §7 freeze. Plan E
                      implementation gate is OPEN for the items in §3 only.

Operations team coordinator — Jackie
  Date / time:        <fill: yyyy-mm-dd hh:mm>
  Signature / handle: <fill: Jackie>
  Statement:          I confirm the Plan A §2.1 hide guards remain in force in
                      the trial environment for the duration of this Plan E
                      phase. I will validate operator-visible deltas of Item
                      E.MS.1 / E.MS.2 / E.MS.3 in the trial environment and
                      append observations to the per-item execution logs and the
                      aggregating PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md.
```

The implementation PR-1 / PR-2 / PR-3 MAY open only after architect + reviewer signoff lines above are filled and committed in a documentation-only PR. The coordinator signoff is required for the closeout per §6 row A7, not for the gate opening.

---

End of Plan E — Matrix Script Operator-Facing Implementation Gate Spec v1.
