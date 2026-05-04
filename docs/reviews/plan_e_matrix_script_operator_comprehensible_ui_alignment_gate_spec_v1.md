# Plan E — Matrix Script Operator-Comprehensible UI Alignment Gate Spec v1

Date: 2026-05-04
Status: Gate-opening signoff completed on 2026-05-04 by Architect (Raobin) and Reviewer (Alisa). Entry condition C6 is now SATISFIED. Implementation remains limited to §3 allowed scope only. **Documentation only. No code, no UI, no contract, no schema, no test, no template change. No file moves. No directory restructure.** This document is the formal gate specification for the **second** Plan E phase scoped to Matrix Script. It defines the only allowed UI/workflow-comprehension scope required to move the line from "engineering-valid / operator-visible / contract-correct" to "operator-comprehensible / usable", while preserving every existing freeze. The §10 approval block is now signed by Architect (Raobin) and Reviewer (Alisa); implementation MAY proceed strictly within §3 once this signoff PR merges to main.

Authority of creation:

- [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §3.1 (current wave permitted action), §4.2 (Matrix Script line state), §6.2 (missing operator surface, Plan E gating), §7.2 (Plan E gate-spec step), §7.6 (sequence-wide red lines).
- [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](plan_e_matrix_script_operator_facing_gate_spec_v1.md) — first Plan E phase gate spec (engineering-complete; A7 closeout signoff intentionally pending). This document is the **successor phase** gate spec for the same line; it does **not** re-author or supersede that gate spec.
- [docs/execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) — first-phase closeout audit; A7 paperwork open; engineering verdicts A1/A2/A3/A5/A6 PASS, A4 PASS-by-file-isolation pending coordinator golden-path sign.
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](operations_upgrade_gap_review_and_ops_plan_v1.md) §11 (Plan E candidate set) + §13 (final gate decision).
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) §6 / §7 (current wave permitted / forbidden scope).
- [docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md) — Matrix Script wave authority that this gate spec extends in operator-comprehensibility direction only.
- [docs/architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) (gated by all Plan E phases closing **plus** a separate wave-start authority; **NOT** unblocked here).
- [docs/architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) (gated by Platform Runtime Assembly signoff; **NOT** touched here).
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md), [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md), [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md), [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) (read-only consumed; not mutated by this gate spec).
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 / §0.2 (sample-validity + product-meaning of `source_script_ref`; binding consumer of this phase's helper-text / labelling work).

If wording in this gate spec ever conflicts with any of the above, the underlying authority wins and this gate spec is updated.

---

## 0. Scope Disclaimer (binding)

This gate spec covers **Matrix Script operator-comprehensible UI alignment** only. It is the **second** Plan E phase scoped to Matrix Script. It is not the entire historical Plan E candidate set from the gap review §11; the broader candidates (Digital Anchor B1/B2/B3 implementation, Asset Library / promote services + UI, L4 advisory producer/emitter, L3 `final_provenance` emitter, unified `publish_readiness` producer, workbench panel dispatch contract object conversion, operator-driven Phase B authoring) remain **explicitly deferred** to subsequent Plan E phase gate specs that must be authored separately when their own pre-conditions are met.

This gate spec:

- authorizes implementation work **only** for the comprehension-layer items enumerated in §3
- does **not** authorize any item enumerated in §4
- does **not** force or accelerate the first-phase A7 closeout signoff — that signoff remains owned by Raobin / Alisa / Jackie via [docs/execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §3 and is intentionally pending
- does **not** start Platform Runtime Assembly (any phase A–E)
- does **not** start Capability Expansion (any of W2.2 / W2.3 / durable persistence / runtime API / third line)
- does **not** unfreeze Digital Anchor in any way
- does **not** reopen Hot Follow business behavior
- does **not** mutate any frozen contract; if a comprehension-layer item requires a contract amendment, the amendment must land **first** in a documentation-only PR with this gate spec updated to cite it
- is **not** a frontend rebuild; UI work is bounded to wording / grouping / labelling / surface-order / affordance-clarity changes on Matrix Script-scoped surfaces only

---

## 1. Purpose

### 1.1 Why current Matrix Script is engineering-valid but still not operator-comprehensible

After the first Plan E phase (E.MS.1 / E.MS.2 / E.MS.3), Matrix Script is:

- **contract-correct** — `task_entry_contract_v1` (with §8.A / §8.C / §8.F / §8.H addenda), `variation_matrix_contract_v1`, `slot_pack_contract_v1`, `workbench_variation_surface_contract_v1`, `delivery_binding_contract_v1`, `result_packet_binding_artifact_lookup_contract_v1`, and the Plan C amendment to `factory_delivery_contract_v1` are all frozen, additively extended only, and consumed by the runtime;
- **operator-visible** — entry surface mounted at `/tasks/matrix-script/new`; Phase B variation panel mounts on `kind=matrix_script`; Delivery Center rows resolve to real artifact references (or contract-enumerated `artifact_lookup_unresolved` sentinels — never `not_implemented_phase_c`); per-deliverable `required` / `blocking_publish` zoning rendered;
- **trial-pre-conditioned** — Plan A live-trial signed closeout recorded; Matrix Script live-run BLOCK released subject to the eight conditions in trial brief §12.

Matrix Script is **not yet** operator-comprehensible because the surfaces above expose contract truth in shapes that engineering can validate but operations cannot read without the trial brief at their elbow. Specific gaps observed in Plan A live-run capture and the closeout audit:

- **Entry surface** — the `source_script_ref` field is named, validated, and helper-text-described per §8.D / §8.F / §8.H, but operators must read multiple addendum paragraphs to learn that this is an asset identity handle and not a body input. The "铸造句柄" affordance from PR-2 is correct but discoverability and ordering on the form are not yet aligned to "what does the operator do first".
- **Workbench (Phase B variation panel)** — the Axes table renders human-readable values per §8.G, but the panel's information hierarchy still follows the contract-internal field order (axes → cells → slots) rather than the operator question order ("what variations am I producing? in which language? against which slots?"). The panel does not visibly tell the operator what their next action is or whether one is required.
- **Delivery Center** — per-row `required` / `blocking_publish` zoning is now contract-pinned and rendered (PR-3), but the operator-facing language ("required (blocks publish)" vs "optional (never blocks publish)") is engineering-truthful and not yet zoned visually so an operator sees "these rows must be green to publish" at a glance.
- **Publish gate** — when `publishable=false`, the explanation surfaces re-derived `publish_gate` reasons but in contract field shorthand (`final_fresh`, `delivery_required_unresolved`, `scene_pack_blocking_disallowed`) rather than operator-language reasons ("仍在生成 / 必交付物缺失 / 配套素材未阻塞").
- **Operator action zoning** — affordances on Matrix Script surfaces are present but not visually grouped by "what you do here" vs "what the system shows you", so operators cannot tell where to focus when a sample misbehaves.

These are not contract defects. They are presentation-layer comprehension gaps. The first Plan E phase intentionally bounded itself to contract-bound truth; this phase is the only authorized way to close the comprehension gap without breaking that boundary.

### 1.2 Why this phase is required before closeout signoff is meaningful

The first-phase A7 closeout signoff (per [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §3) asks Jackie to confirm that "operator-visible deltas of Item E.MS.1 / E.MS.2 / E.MS.3 [are] observed in the trial environment". Operations can confirm the deltas exist; they cannot yet confirm operations is **able to use the line without a coordinator at the elbow**. Forcing A7 signoff before this comprehension phase lands would either:

- record a false-positive operator-readiness confirmation, or
- force operations to write coordinator-side workarounds into the closeout document, polluting the audit trail with non-engineering scope.

Authoring this comprehension-phase gate spec **first**, then landing the in-scope changes, then signing both the first-phase A7 closeout **and** this phase's closeout in their natural order, is the only sequence that preserves audit integrity. Specifically:

- this gate spec being authored does **not** flip A7 (it stays pending);
- this phase's implementation landing does **not** flip A7 (the first phase's evidence is independent);
- A7 may be signed at any point Jackie / Raobin / Alisa choose, before, during, or after this phase, on its own evidence;
- this phase's closeout (a separate document at phase-close time) is the only authoritative record of "operator-comprehensible" status.

The user-mandated posture for this gate spec is therefore: **A7 stays pending; this gate spec is authored as the next allowed gate-spec step, independently of A7 timing**.

---

## 2. Entry Conditions

This Plan E comprehension phase MAY NOT begin implementation before **all** of the following entry conditions hold. Each condition is verifiable from the listed artifact at the listed location.

| # | Entry condition | Verification artifact | Status as of 2026-05-04 |
| --- | --- | --- | --- |
| C1 | First Plan E phase (E.MS.1 / E.MS.2 / E.MS.3) engineering complete — all three implementation PRs merged and per-PR execution logs filed. | [PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md), [PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md), [PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md) | **SATISFIED** (PR #100 / `7a1e7a6`; PR #101 / `2822ad0`; PR #102 / `edc9fae`) |
| C2 | No forbidden-scope regression has landed since first-phase closeout audit (per first-phase gate spec §4 walked at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §2.6). | [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §2.6](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) | **SATISFIED** at audit baseline `edc9fae`; reviewer re-walks §4 at this gate spec's §10 signoff time |
| C3 | Hot Follow baseline preserved — no commits to `gateway/app/services/hot_follow_*`, `tasks.py` Hot Follow paths, `hot_follow_api.py` business logic, `hot_follow_workbench.html`, or Hot Follow Delivery Center per-deliverable zoning code paths since first-phase closeout audit. | [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §2.4.1](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md), [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) | **SATISFIED** at audit baseline `edc9fae`; reviewer re-confirms at §10 signoff time |
| C4 | Digital Anchor freeze preserved — no operator submission path; Plan A §2.1 hide guards (Digital Anchor New-Tasks card click target + temp `/tasks/connect/digital_anchor/new`) still in force. | [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §3.2 / §3.3](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §2.5](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) | **SATISFIED** |
| C5 | First-phase A7 closeout signoff status is **either** (a) signed by Raobin / Alisa / Jackie per [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md), **or** (b) intentionally pending with no in-flight A7 work being forced by this gate spec. Either state satisfies C5; this gate spec does **not** require A7 to be signed before opening, but it also does **not** sign A7. | [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) | **SATISFIED** under (b) — A7 intentionally pending; this gate spec authoring does not advance A7 paperwork |
| C6 | This gate spec reviewed and approved through its own approval block (§10) by Architect (Raobin) and Reviewer (Alisa). Operations team coordinator (Jackie) signs the closeout block per §6 row UA7, not the gate-opening block. | This document §10 | **SATISFIED** (Raobin 2026-05-04 14:05; Alisa 2026-05-04 14:18) — implementation gate OPEN for §3 items only on signoff-PR merge to `main` |

When C1 → C6 all hold, and only then, an implementation PR within the §3 allowed scope MAY open. Until C6 is signed, no implementation work is authorized. C5's "either signed or intentionally pending" wording is binding: this phase's implementation **MUST NOT** make first-phase A7 signoff a hidden pre-condition; A7 is independent paperwork on independent evidence.

---

## 3. Allowed Implementation Scope (binding, exhaustive)

This Plan E comprehension phase authorizes implementation of **only** the items enumerated below. Each item is bound to existing contract truth; no contract is invented by this gate spec. Each item is operator-facing for **Matrix Script** specifically; cross-line plumbing is **not** in scope unless explicitly listed (and none is).

The complete enumeration is exactly **{UA.1, UA.2, UA.3, UA.4, UA.5, UA.6}**. Any item not in this set is governed by §4 (forbidden scope) and is BLOCKED.

### 3.1 Item UA.1 — Matrix Script entry-surface comprehension improvements

- **What it is.** Re-order, re-group, and re-label fields and helper text on [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) so an operator can answer the three operator questions ("what kind of source am I bringing?" → "how do I express it as a handle?" → "what variations / language do I want?") in surface-order, without reading the trial brief alongside the form. The §8.A `_validate_source_script_ref_shape` guard, the §8.F-tightened scheme set, the form `pattern` constraint, and `maxlength=512` cap are unchanged. The PR-2 minting affordance ("铸造句柄") is re-positioned for discoverability and re-labelled in operator language ("申请新的句柄" or equivalent operator-readable phrasing chosen at PR time within operator-language scope), but its endpoint contract and behavior are unchanged.
- **Contract authority.** [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (read-only; consumed for shape rules and §0.2 product-meaning binding).
- **Operator-visible result.** A first-time operator can submit a contract-clean Matrix Script sample using only the form (and the minting affordance) without consulting the trial brief; helper text reads in operator language; field order matches the operator question order.
- **Operator-visible boundary preserved.** No new accepted scheme; no new field; no relaxation of guards; no contract mutation; no new endpoint; no Hot Follow / Digital Anchor template touched.
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.2 Item UA.2 — Matrix Script Workbench information hierarchy / task-next-step clarity

- **What it is.** Re-arrange the Matrix Script Phase B variation panel's section ordering and visible labels inside [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) (Matrix Script panel block only) so the operator reads "task identity → variation summary → axes → cells → slots → next action (if any)" in surface-order instead of the contract-internal field order. Where no operator action is required, the panel must visibly say so ("此阶段无需操作 / Phase B 已自动生成"). Where an action exists in this phase's scope (none beyond entry-surface follow-through; operator-driven Phase B authoring remains forbidden per §4.3), it is visually distinguished from system-shown information.
- **Contract authority.** [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md), [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) (read-only; the §"Shared shell neutrality" addendum from §8.E is preserved verbatim).
- **Operator-visible result.** An operator opening the Matrix Script Workbench knows in one read what the system has produced (axes / cells / slots) and what (if anything) the operator must do next; the §8.G human-readable axis-value rendering is preserved; the §8.E whitelist `{% if task.kind == "hot_follow" %}` shell suppression is preserved verbatim.
- **Operator-visible boundary preserved.** No projection mutation; no new contract field; no operator-driven Phase B authoring affordance (forbidden per §4.3); no Hot Follow shell content reintroduced on `kind=matrix_script`; no new `panel_kind` enum value; the closed dispatch map and `ref_id` set are unchanged.
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.3 Item UA.3 — Matrix Script variation panel readability improvements

- **What it is.** Improve the visible readability of the Phase B Axes table and the cell-to-slot mapping rendered inside the Matrix Script variation panel: column-header labels in operator language; cell-count summary ("共 N 组变体") visible without scrolling; slot rows grouped by axis tuple instead of flat slot-id ordering when the variation count exceeds a threshold chosen at PR time within readability scope (the threshold is presentation-only; no contract field consulted beyond the existing `variation_target_count` and `cells[i].script_slot_ref ↔ slots[i].slot_id` pairing rule from §8.C). The §8.G item-access pattern (`axis["values"]`) is preserved verbatim; the regression test added under §8.G stays green.
- **Contract authority.** [docs/contracts/matrix_script/variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md), [docs/contracts/matrix_script/slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md) (read-only).
- **Operator-visible result.** A 12-cell variation matrix is readable without horizontal scroll on standard trial-environment widths; row grouping makes the axis × slot relationship visually obvious; an operator can confirm "every cell maps to one slot, every slot has one body_ref" in one read.
- **Operator-visible boundary preserved.** No change to canonical axes set `{tone, audience, length}` (forbidden widening per §4.3); no change to `variation_target_count` semantics; no operator-driven cell editing; no slot mutation affordance; no contract or schema mutation; no `body_ref` template change.
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.4 Item UA.4 — Matrix Script Delivery Center operator-language alignment

- **What it is.** Re-label the per-row zoning rendered by Item E.MS.3 from engineering-truthful phrasing ("required (blocks publish)" vs "optional (never blocks publish)") to operator-language phrasing chosen at PR time within operator-readability scope (e.g. "必交付 · 阻塞发布" vs "可选 · 不阻塞发布", or equivalent — final wording fixed at PR time and recorded in this gate spec's closeout). Add a one-line section header on Matrix Script Delivery Center explaining "这些必交付物的产出与状态决定本任务能否发布". The contract-pinned `required` / `blocking_publish` field reads from [factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) Plan C amendment are unchanged; the row order, the row count, and the `matrix_script_scene_pack` HARDCODED `required=False, blocking_publish=False` rule from PR-3 are preserved verbatim.
- **Contract authority.** [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) Plan C amendment (read-only); [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md) (read-only).
- **Operator-visible result.** An operator looking at Matrix Script Delivery Center reads "必交付 / 可选 / 阻塞 / 不阻塞" zoning in one glance; the section header explains what blocks publish; the `matrix_script_scene_pack` row visibly reads as "可选 · 不阻塞发布" per the §"Scene-Pack Non-Blocking Rule".
- **Operator-visible boundary preserved.** Hot Follow Delivery Center is **not** changed (Hot Follow's existing zoning logic stays as is per first-phase gate spec §7.1). Digital Anchor Delivery Center is **not** changed (Digital Anchor remains frozen). No `derive_delivery_publish_gate` re-derivation in `projections.py` is touched (preserves the forbidden D1 unified `publish_readiness` producer per first-phase gate spec §4.2).
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.5 Item UA.5 — Publish-blocking explanation clarity

- **What it is.** When Matrix Script `publishable=false`, replace the contract-shorthand reasons rendered to the operator (`final_fresh`, `delivery_required_unresolved`, `scene_pack_blocking_disallowed`, etc.) with operator-language explanations that point at the surface where the operator can act (or can confirm "等待系统完成" if no operator action is possible). The reasons are derived only from existing Matrix Script projection truth — no new producer service, no cross-line `publish_readiness` consolidation, no new contract field, no new derivation rule. A small Matrix Script-scoped helper (placement chosen at PR time within Matrix Script-scoped surface scope) translates the existing reason codes to operator-language strings.
- **Contract authority.** [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md), [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (read-only). The unified `publish_readiness` producer (D1) and L4 advisory producer (D4) remain forbidden in this Plan E phase per first-phase gate spec §4.2; this item does not implement either, and does not re-derive `publishable` cross-line — it consumes Matrix Script-side existing reason codes only.
- **Operator-visible result.** When publish is blocked on a Matrix Script task, the operator reads "为什么不能发布 → 我能做什么" in operator language without consulting engineering documentation.
- **Operator-visible boundary preserved.** No unified `publish_readiness` producer; no L3 `final_provenance` emit; no L4 advisory producer; no Hot Follow advisory rendering touched; no cross-line consolidation; no new contract field; no schema mutation. The reason-code set consumed is exactly what Matrix Script projection emits today.
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.6 Item UA.6 — Operator action zoning / affordance clarity (Matrix Script-scoped surfaces)

- **What it is.** Visually group Matrix Script-scoped surfaces (entry form, Workbench Phase B panel, Delivery Center) into "what you do here" (operator-action zone) vs "what the system shows you" (system-state zone) using existing markup and styling primitives only — no new component framework, no new style system, no React/Vite footprint, no design-system migration. Where an action exists in this phase's scope (entry form submission, minting affordance, publish trigger when permitted), it sits in the operator-action zone with consistent affordance shape; system-shown information sits in the system-state zone. The zoning is presentation-only; no projection / contract / endpoint change.
- **Contract authority.** None mutated; this item is presentation-only over the contracts named in UA.1 / UA.2 / UA.3 / UA.4 / UA.5.
- **Operator-visible result.** An operator opening any Matrix Script-scoped surface knows in one glance which region accepts their input and which region only shows status; affordance shape (button vs text vs link) consistently signals intent across the three Matrix Script surfaces.
- **Operator-visible boundary preserved.** No Hot Follow surface re-zoned (Hot Follow stays as is per first-phase gate spec §7.1). No Digital Anchor surface re-zoned (Digital Anchor remains frozen). No cross-line shared-shell zoning change (the §8.E whitelist `{% if task.kind == "hot_follow" %}` and the `Shared shell neutrality` addendum on `workbench_panel_dispatch_contract_v1.md` are preserved verbatim). No new component library; no React/Vite full rebuild (forbidden per first-phase gate spec §4.5 + Operator-Visible Surface Validation Wave 指挥单 §7).
- **Pre-condition specific to this item.** None beyond C1 → C6.

### 3.7 Closed scope check (anti-creep)

The complete enumeration is exactly **{UA.1, UA.2, UA.3, UA.4, UA.5, UA.6}**. Reviewer / Merge Owner enforces this check on every PR. Final wording chosen at PR time for any operator-language label is recorded in this gate spec's closeout document; the gate spec itself fixes the *scope* of the wording change, not the verbatim string.

---

## 4. Forbidden Scope (binding, exhaustive within Plan E candidate space)

This Plan E comprehension phase **does not** authorize implementation of any of the items below. Each is contract-frozen or contract-pending elsewhere and waits on its own subsequent Plan E phase gate spec, on a different wave, or on indefinite deferral. The list is binding; Reviewer / Merge Owner rejects any PR that lands one of these.

### 4.1 Forbidden — Hot Follow reopen (preserves Hot Follow baseline)

- Any change to Hot Follow business behavior; any commit to `gateway/app/services/hot_follow_*`, `tasks.py` Hot Follow paths, `hot_follow_api.py` business logic, `hot_follow_workbench.html` business behavior — **forbidden**.
- Any new Hot Follow feature; any cleanup of `tasks.py` (3,480 lines), `hot_follow_api.py` (2,325 lines), or `task_view.py::build_hot_follow_workbench_hub()` (492 lines) — **forbidden** (Hot Follow structural debt is deferred to Platform Runtime Assembly Wave per [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md)).
- Any change to Hot Follow Delivery Center per-deliverable zoning code paths or operator-language labels — **forbidden** (UA.4 touches Matrix Script Delivery Center only; Hot Follow's labelling stays as is).
- Any change to Hot Follow advisory rendering, Hot Follow Workbench information hierarchy, Hot Follow entry form labels, Hot Follow publish-blocking explanations — **forbidden**; Hot Follow's existing operator-comprehension state is the operational baseline and is preserved verbatim by this gate spec.

### 4.2 Forbidden — Digital Anchor unfreeze (preserves Digital Anchor freeze)

- Digital Anchor `create_entry_payload_builder` (Plan B B1), formal `/tasks/digital-anchor/new` route (Plan B B2), Phase D.1 publish-feedback write-back (Plan B B3), Phase B render production path, New-Tasks card promotion to operator-eligible, Workbench role/speaker panel mount as operator-facing surface, Delivery Center surface, any operator submission affordance reaching Digital Anchor — **all forbidden**.
- Any change to Digital Anchor templates / runtime / routes / contracts; any removal or weakening of Plan A §2.1 hide guards on the Digital Anchor New-Tasks card click target ([gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html)) or the temp `/tasks/connect/digital_anchor/new` route — **forbidden**.
- Any operator-language re-labelling of Digital Anchor surfaces — **forbidden**; Digital Anchor remains inspect-only / contract-aligned with no operator-facing comprehension work in this wave.

### 4.3 Forbidden — Matrix Script truth / scope creep (preserves Matrix Script frozen truth)

- Operator-driven Phase B authoring (axes / cells / slots authored on operator command) — pinned as Plan E future work in [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §"Phase B deterministic authoring (addendum, 2026-05-03)" but **NOT this Plan E phase**. The §8.C deterministic authoring continues to run once at task creation only; the panel stays read-only at the projection level — UA.2 / UA.3 may re-arrange its **rendering** but **MUST NOT** introduce any cell / slot / axis edit affordance.
- Matrix Script `target_language` enum widening beyond `{mm, vi}` — **forbidden**.
- Matrix Script canonical-axes set widening beyond `{tone, audience, length}` — **forbidden**.
- Matrix Script `source_script_ref` accepted-scheme set re-widening (re-adding `https` / `http` / `s3` / `gs`) — **forbidden** per §8.F. UA.1 may re-position / re-label the minting affordance and helper text; it **MUST NOT** widen the scheme set.
- Repurposing `source_script_ref` as a body-input field, publisher-URL ingestion field, or currently dereferenced content address — **forbidden** per §0.2 product-meaning. UA.1 helper-text re-wording must preserve the asset-identity-handle binding verbatim in meaning.
- Matrix Script Workbench shell mutation (removing or weakening §8.E shared-shell suppression; re-introducing Hot Follow stage cards on `kind=matrix_script`) — **forbidden**; the §"Shared shell neutrality" addendum on `workbench_panel_dispatch_contract_v1.md` is binding.
- Mutation of `not_implemented_phase_c` retirement guarantee from PR-1 (E.MS.1); mutation of the additive `blocking_publish` field on Matrix Script Delivery Center rows from PR-3 (E.MS.3); mutation of the minting service's `mint-<16-hex-chars>` token shape from PR-2 (E.MS.2) — **all forbidden**; this phase is presentation-layer only over PR-1/2/3 truth.

### 4.4 Forbidden — Platform Runtime Assembly work (preserves Platform Runtime Assembly gate)

- Platform Runtime Assembly Phases A–E (Shared Logic Port Merge / Compose Service Extraction / Declarative Ready Gate / Runtime Assembly Skeleton / OpenClaw stub) — **forbidden**; gated on **all** Plan E phases closing **plus** a separate wave-start authority per [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md). **Plan E does NOT equal Platform Runtime Assembly**; this comprehension phase is a Plan E phase, not a Platform Runtime Assembly preparation step.
- Compose extraction prep, router thinning prep, declarative ready-gate prep, runtime-assembly-skeleton prep — **forbidden**; no UA.* PR may draw these in.

### 4.5 Forbidden — Capability Expansion work (preserves Capability Expansion gate)

- Capability Expansion (W2.2 Subtitles / Dub Provider; W2.3 Avatar / VideoGen / Storage Provider; durable persistence backend formalization; runtime API / callback handler formalization; third production line commissioning) — **forbidden**; gated on Platform Runtime Assembly signoff per [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md).

### 4.6 Forbidden — Provider / model / vendor controls (validator R3 + design-handoff red line 6)

- Provider / model / vendor / engine selectors / controls / consoles on any operator-visible surface — **forbidden at all phases** per validator R3 ([docs/contracts/factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md) R3) and the design-handoff red line 6.
- Operator-visible payloads MUST NOT carry `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any donor namespace identifier per [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). The sanitization guard at [gateway/app/services/operator_visible_surfaces/projections.py:36](../../gateway/app/services/operator_visible_surfaces/projections.py) MUST NOT be relaxed by any UA.* PR.
- Donor namespace import (`from swiftcraft.*`) — **forbidden** per [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md).

### 4.7 Forbidden — Cross-line consolidation (preserves no-platform-wide-expansion)

- Asset Library object service (no `gateway/app/services/asset_library/` runtime), Asset Supply / B-roll page UI, promote intent service / submit affordance, promote closure service / admin review UI — **all forbidden** in this Plan E phase; each item has its own contract truth and waits for its own subsequent Plan E phase gate-spec authoring step.
- Unified `publish_readiness` producer (D1), L3 `final_provenance` emitter (D2), workbench panel dispatch contract OBJECT conversion (D3), L4 advisory producer / emitter (D4) — **all forbidden** in this Plan E phase. UA.5 may translate Matrix Script-side existing reason codes to operator-language strings on the Matrix Script-scoped surface; it **MUST NOT** consolidate `publishable` re-derivation across Board / Workbench / Delivery, **MUST NOT** emit `final_provenance` from L3, **MUST NOT** convert the in-code dict at [gateway/app/services/operator_visible_surfaces/projections.py:239-246](../../gateway/app/services/operator_visible_surfaces/projections.py) to a contract-loaded object, and **MUST NOT** create `gateway/app/services/operator_visible_surfaces/advisory_emitter.py`.

### 4.8 Forbidden — Contract truth mutation without separate authority

- Any mutation to `task_entry_contract_v1`, `variation_matrix_contract_v1`, `slot_pack_contract_v1`, `workbench_variation_surface_contract_v1`, `delivery_binding_contract_v1`, `result_packet_binding_artifact_lookup_contract_v1`, `factory_delivery_contract_v1`, `workbench_panel_dispatch_contract_v1`, or any other frozen contract under cover of a UA.* PR — **forbidden**. If any UA.* item appears to require a contract change, the PR is rejected and the contract amendment must land first as a documentation-only PR with this gate spec updated to cite the amendment.
- Any new contract addendum authored under cover of a UA.* PR (versus a separate documentation-only PR) — **forbidden**. The presentation-layer scope of UA.1 → UA.6 does not require a contract addendum; if the implementation discovers it does, scope re-fence is mandatory.

### 4.9 Forbidden — Frontend rebuild disguised as comprehension work

- React/Vite full frontend rebuild, cross-line studio shell, tool catalog page, multi-tenant platform shell, design-system migration, new component framework, new style system — **all forbidden** per [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) and Plan A §4.1.
- New JavaScript bundle, new build-step dependency, new package added to the gateway runtime under cover of a UA.* PR — **forbidden**. UA.1 / UA.2 / UA.3 / UA.4 / UA.5 / UA.6 use existing markup and styling primitives only; the small inline progressive-enhancement `<script>` from PR-2 is the existing JS footprint baseline and is not expanded.

### 4.10 Forbidden — Forced first-phase A7 closeout signing

- Any UA.* PR that lands a flip of the first-phase A7 closeout signoff at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) under cover of "comprehension phase landed" — **forbidden**. A7 is independent paperwork on independent evidence; this comprehension phase has its own closeout (UA7) on its own evidence. Reviewer / Merge Owner rejects any PR that touches the first-phase A7 signoff block.

### 4.11 Forbidden — Implementation prep disguised as code slicing

- Authoring "skeleton" code paths, stub services, dead-code feature flags, or future-work scaffolding for §4.1 / §4.2 / §4.3 / §4.4 / §4.5 / §4.6 / §4.7 items under cover of a UA.* PR — **forbidden**. Each UA.* PR must touch only the surfaces / templates / tests required by its own §3 item.
- Drawing in adjacent refactors (compose extraction, router thinning, panel dispatch contract-object conversion, ready-gate declarative conversion, projection re-derivation consolidation) under cover of a UA.* PR — **forbidden**. These wait for Platform Runtime Assembly Wave or for their own subsequent Plan E phase gate spec.

---

## 5. PR Slicing Plan

Each PR in this Plan E comprehension phase MUST be:

- **single-item:** touches exactly one of {UA.1, UA.2, UA.3, UA.4, UA.5, UA.6}; cross-item dependencies are honored across PRs.
- **scope-fenced:** files touched are bounded by the per-item file-fence in §5.1 → §5.6; any deviation requires gate-spec amendment (a documentation-only PR).
- **operator-visible:** each PR produces a directly observable operator-language / operator-comprehension delta on a Matrix Script-scoped surface; if the delta is not operator-visible the PR is mis-scoped.
- **independently revertable:** each PR may be rolled back without disturbing the others; comprehension improvements are additive over PR-1/2/3 truth and remain bytewise-clean against Hot Follow / Digital Anchor.
- **truth-preserving:** each PR preserves the contract field reads, the projection field shapes, and the endpoint contracts unchanged; presentation-layer only.
- **review-citable:** each PR cites this gate spec and the item-specific contract authority; the citation set is mandatory per [ENGINEERING_RULES.md §6, §9](../../ENGINEERING_RULES.md).

### 5.1 PR-UA1 — Item UA.1 (Matrix Script entry-surface comprehension)

- **Scope.** Re-order, re-group, re-label fields and helper text on `gateway/app/templates/matrix_script_new.html`. Re-position and re-label the PR-2 minting affordance for discoverability in operator language. No router change; no service change; no contract change.
- **Files allowed to change.**
  - `gateway/app/templates/matrix_script_new.html` (markup re-order + label/helper-text re-wording only).
  - One new test module (or augmentation of an existing matrix-script entry-surface test) under `gateway/app/services/tests/` asserting key operator-language strings render and the §8.A / §8.F guards still reject the same negative-path inputs.
  - This gate spec (citation update only; closeout marker in §10.1).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. `gateway/app/services/matrix_script/create_entry.py` (the constants `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` and the `_validate_source_script_ref_shape` guard stay verbatim). `gateway/app/services/matrix_script/source_script_ref_minting.py` (the minting service shape stays verbatim). `gateway/app/routers/tasks.py` (no router change). Any contract file (no addendum under cover of UA.1).
- **Contract changes.** None.
- **Operator-visible delta.** A first-time operator can submit a contract-clean Matrix Script sample using only the form; helper text reads in operator language; field order matches the operator question order; the minting affordance is discoverable.
- **Out-of-scope reminder.** No new endpoint; no new accepted scheme; no §8.A / §8.F / §8.H truth weakening; no Hot Follow entry-form change.

### 5.2 PR-UA2 — Item UA.2 (Workbench information hierarchy / next-step clarity)

- **Scope.** Re-arrange the Matrix Script Phase B variation panel block inside `gateway/app/templates/task_workbench.html` so the operator reads "task identity → variation summary → axes → cells → slots → next action (if any)" in surface-order; visibly state "此阶段无需操作" where no operator action exists in this phase's scope. Preserve §8.E whitelist gate, §8.G item-access pattern, and the `panel_kind="matrix_script"` mount.
- **Files allowed to change.**
  - `gateway/app/templates/task_workbench.html` (Matrix Script panel block re-order + visible-state-language additions only; the §8.E `{% if task.kind == "hot_follow" %}` whitelist gate around the four Hot Follow-only template regions is preserved verbatim).
  - One new test module (or augmentation of `test_matrix_script_workbench_dispatch.py` / `test_matrix_script_phase_b_authoring.py`) asserting the new section order and the new visible-state-language strings render on a fresh contract-clean `kind=matrix_script` sample, and that the §8.E forbidden-token list (28 tokens) remains absent on `kind=matrix_script`.
  - This gate spec (citation update only; closeout marker in §10.1).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. `gateway/app/services/operator_visible_surfaces/projections.py` (no projection mutation; no panel dispatch contract-object conversion). `gateway/app/services/matrix_script/phase_b_authoring.py` (no axes / cells / slots authoring change). Any contract file. Any router file.
- **Contract changes.** None.
- **Operator-visible delta.** Matrix Script Workbench reads in operator question order; "next action / no action" state is visibly stated on every fresh contract-clean sample.
- **Out-of-scope reminder.** No operator-driven Phase B authoring affordance (forbidden per §4.3); no Hot Follow stage cards reintroduced on `kind=matrix_script`; no new `panel_kind` enum value.

### 5.3 PR-UA3 — Item UA.3 (Variation panel readability)

- **Scope.** Improve the Phase B Axes table readability and the cell-to-slot mapping rendering inside `gateway/app/templates/task_workbench.html` (Matrix Script panel block only). Operator-language column headers; visible cell-count summary; axis-tuple grouping when variation count exceeds the readability threshold. Preserve §8.G item-access pattern and the existing axes-table regression test.
- **Files allowed to change.**
  - `gateway/app/templates/task_workbench.html` (Matrix Script Axes table + cell-to-slot rendering only).
  - One new test module asserting the operator-language headers, the visible cell-count summary, and the axis-tuple grouping render on a fresh contract-clean sample with `variation_target_count = 12`, while the §8.G axes-table render-correctness test stays green.
  - This gate spec (citation update only; closeout marker in §10.1).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. `gateway/app/services/matrix_script/phase_b_authoring.py` (no canonical-axes widening; no `body_ref` template change). Any contract file. Any router file. The §8.G item-access pattern (`axis["values"]`) is preserved verbatim.
- **Contract changes.** None.
- **Operator-visible delta.** A 12-cell variation matrix is readable without horizontal scroll; row grouping makes axis × slot relationship visually obvious.
- **Out-of-scope reminder.** No canonical-axes widening; no operator-driven cell editing; no slot mutation affordance; no `body_ref` template change.

### 5.4 PR-UA4 — Item UA.4 (Matrix Script Delivery Center operator-language alignment)

- **Scope.** Re-label the per-row zoning rendered by Item E.MS.3 from engineering-truthful phrasing to operator-language phrasing on Matrix Script Delivery Center rows only. Add a one-line operator-language section header. Preserve the contract-pinned `required` / `blocking_publish` reads, the row order, the row count, and the `matrix_script_scene_pack` HARDCODED `required=False, blocking_publish=False` rule from PR-3.
- **Files allowed to change.**
  - The Matrix Script Delivery Center template file (path identified at PR time; constrained to Matrix Script-scoped surfaces).
  - `gateway/app/services/matrix_script/delivery_binding.py` ONLY for an operator-language label-string-mapping helper if the cleanest implementation puts the mapping in the projection layer; no field shape change; no `_clamp_blocking_publish` mutation; no `SCENE_PACK_BLOCKING_ALLOWED` mutation; no new field on the closed key set.
  - One new test module asserting the operator-language labels render on every row kind on a fresh contract-clean sample, that the `matrix_script_scene_pack` row reads as the operator-language equivalent of "可选 · 不阻塞发布", and that the contract-pinned `required` / `blocking_publish` field reads are unchanged.
  - This gate spec (citation update only; closeout marker in §10.1; final operator-language label strings recorded in the closeout document at PR time).
- **Files NOT allowed to change.**
  - Any Hot Follow file (Hot Follow Delivery Center keeps its existing labels per first-phase gate spec §7.1 + §4.1 of this gate spec). Any Digital Anchor file. `gateway/app/services/operator_visible_surfaces/projections.py::derive_delivery_publish_gate` (no cross-line consolidation per §4.7). Any contract file (no Plan C amendment mutation; no `factory_delivery_contract_v1.md` change).
- **Contract changes.** None.
- **Operator-visible delta.** Matrix Script Delivery Center rows read "必交付 / 可选 / 阻塞 / 不阻塞" zoning in operator language; section header explains what blocks publish.
- **Out-of-scope reminder.** No Hot Follow Delivery Center re-labelling; no cross-line consolidation; no D1 unified `publish_readiness` producer.

### 5.5 PR-UA5 — Item UA.5 (Publish-blocking explanation clarity)

- **Scope.** When Matrix Script `publishable=false`, render operator-language explanations of the blocking reasons sourced only from existing Matrix Script projection truth. A small Matrix Script-scoped helper translates the existing reason codes to operator-language strings; no new reason code; no cross-line consolidation; no new contract field.
- **Files allowed to change.**
  - The Matrix Script-scoped surface that renders the `publish_gate` reasons today (path identified at PR time; constrained to Matrix Script-scoped surfaces).
  - A new Matrix Script-scoped helper module (placement chosen at PR time within `gateway/app/services/matrix_script/` or the corresponding template-helper location) that maps existing reason codes to operator-language strings.
  - One new test module asserting that for each Matrix Script-side reason code in the existing emitted set, the operator-language string renders correctly on a fresh contract-clean adverse-state sample, and that no new reason code is introduced.
  - This gate spec (citation update only; closeout marker in §10.1; final operator-language reason strings recorded in the closeout document at PR time).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. `gateway/app/services/operator_visible_surfaces/projections.py` cross-line `publishable` re-derivation paths (no D1 consolidation per §4.7). `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (does not exist; UA.5 does **not** create it). Any contract file.
- **Contract changes.** None.
- **Operator-visible delta.** When publish is blocked on a Matrix Script task, the operator reads "为什么不能发布 → 我能做什么" in operator language.
- **Out-of-scope reminder.** No D1 unified `publish_readiness` producer; no D4 L4 advisory producer / emitter; no D2 L3 `final_provenance` emitter; no Hot Follow advisory rendering touched.

### 5.6 PR-UA6 — Item UA.6 (Operator action zoning / affordance clarity)

- **Scope.** Visually group Matrix Script-scoped surfaces into "what you do here" vs "what the system shows you" using existing markup and styling primitives only. Consistent affordance shape across the three Matrix Script surfaces.
- **Files allowed to change.**
  - The Matrix Script-scoped templates already touched by PR-UA1 / PR-UA2 / PR-UA3 / PR-UA4 / PR-UA5 (re-grouping markup only; no new component; no new style system).
  - One new test module asserting the operator-action zone vs system-state zone classification renders on each Matrix Script-scoped surface and that affordance shape is consistent across the three surfaces.
  - This gate spec (citation update only; closeout marker in §10.1).
- **Files NOT allowed to change.**
  - Any Hot Follow file. Any Digital Anchor file. The cross-line shared shell (`task_workbench.html` outside the Matrix Script panel block; `tasks_newtasks.html`). Any contract file. Any router file. Any new package added to the gateway runtime (no React/Vite footprint; no design-system migration).
- **Contract changes.** None.
- **Operator-visible delta.** Operator-action zone vs system-state zone is visible at a glance on every Matrix Script-scoped surface; affordance shape is consistent.
- **Out-of-scope reminder.** No cross-line shared-shell zoning change; no new component library; no React/Vite full rebuild.

### 5.7 Per-item business regression scope (mandatory per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md))

- **PR-UA1.** Hot Follow golden path PASS unchanged; Matrix Script entry submission PASS on a fresh contract-clean sample using only the re-worded form; §8.A body-text rejection still HTTP 400; §8.F publisher-URL / bucket-URI rejection still HTTP 400 with `"scheme is not recognised"`; minting affordance still returns a `content://matrix-script/source/<product-minted-token>` handle; pre-§8.F operator-discipline handles still accepted.
- **PR-UA2.** Hot Follow golden path PASS unchanged; Matrix Script Workbench mounts on a fresh contract-clean `kind=matrix_script` sample; the §8.E forbidden-token list (28 tokens) remains absent in the visible HTML on `kind=matrix_script`; the §8.G axes-table render-correctness regression test stays green.
- **PR-UA3.** Hot Follow golden path PASS unchanged; Matrix Script Workbench Axes table renders human-readable values for all three canonical axes (`tone` / `audience` / `length`) per §8.G; 12-cell variation matrix renders without horizontal scroll on standard trial-environment widths.
- **PR-UA4.** Hot Follow golden path PASS unchanged; Hot Follow Delivery Center bytewise unchanged; Matrix Script Delivery Center renders operator-language `required` / `blocking_publish` zoning on every row kind; `matrix_script_scene_pack` reads as the operator-language equivalent of "可选 · 不阻塞发布"; PR-3 contract-pinned field reads unchanged.
- **PR-UA5.** Hot Follow golden path PASS unchanged; Hot Follow advisory rendering unchanged; for each Matrix Script-side reason code in the existing emitted set, the operator-language string renders correctly on a fresh contract-clean adverse-state sample; no new reason code introduced; cross-line `publishable` re-derivation unchanged.
- **PR-UA6.** Hot Follow golden path PASS unchanged; Matrix Script-scoped operator-action zone vs system-state zone classification renders on each Matrix Script-scoped surface; no Hot Follow surface re-zoned; no Digital Anchor surface re-zoned.

### 5.8 PR ordering

PR-UA1 lands first (entry surface is the operator's first contact). PR-UA2 lands second (Workbench is the operator's second contact). PR-UA3 may land in parallel with PR-UA2 (both touch the Workbench panel block, so a contention-resolution merge plan is recorded at PR-UA3 open time; if contention is unmanageable, PR-UA3 lands strictly after PR-UA2). PR-UA4 and PR-UA5 may land in parallel with PR-UA1 / PR-UA2 / PR-UA3 (different surfaces). PR-UA6 lands last (zoning consolidates over the surfaces touched by PR-UA1 → PR-UA5; if PR-UA6 lands before PR-UA1 / PR-UA2 / PR-UA3 / PR-UA4 / PR-UA5, the unfinished surfaces remain ungrouped, which is acceptable but operator-visibly incomplete).

---

## 6. Acceptance Evidence

This Plan E comprehension phase closes only when **all** acceptance evidence below is recorded under [docs/execution/](../execution/) and signed off through the §10.2 closeout signoff block. Each row enumerates the closing artifact and the verification recipe.

| # | Acceptance row | Evidence artifact | Verification recipe |
| --- | --- | --- | --- |
| UA1-A | Item UA.1 implementation landed; entry-surface comprehension delta operator-observable. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA1_ENTRY_COMPREHENSION_EXECUTION_LOG_v1.md` (authored at PR-UA1 land time); PR commit SHA recorded; before/after screenshot capture appended. | Live: a first-time operator (per coordinator standard) submits a contract-clean Matrix Script sample using only the re-worded form, without consulting the trial brief; submission PASSes guards. Static: §8.A / §8.F regression cases PASS unchanged. |
| UA2-A | Item UA.2 implementation landed; Workbench information hierarchy + next-step clarity operator-observable. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA2_WORKBENCH_HIERARCHY_EXECUTION_LOG_v1.md`; PR commit SHA recorded; before/after screenshot capture appended. | Live: an operator opens the Matrix Script Workbench on a fresh sample and reads section order "task identity → variation summary → axes → cells → slots → next action (if any)" without prompting. Static: §8.E forbidden-token list absent on `kind=matrix_script`; §8.G axes-table regression PASS. |
| UA3-A | Item UA.3 implementation landed; variation panel readability operator-observable. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA3_VARIATION_READABILITY_EXECUTION_LOG_v1.md`; PR commit SHA recorded. | Live: a 12-cell variation matrix on a fresh sample renders without horizontal scroll on standard trial-environment widths; row grouping is visually obvious. Static: canonical-axes set unchanged at `{tone, audience, length}`. |
| UA4-A | Item UA.4 implementation landed; Matrix Script Delivery Center operator-language zoning observable. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA4_DELIVERY_LANGUAGE_EXECUTION_LOG_v1.md`; PR commit SHA recorded; final operator-language label strings recorded in this gate spec's closeout document. | Live: Matrix Script Delivery Center rows read operator-language `必交付 / 可选 / 阻塞 / 不阻塞` (or final agreed strings) on every row kind; `matrix_script_scene_pack` reads as the operator-language equivalent of "可选 · 不阻塞发布". Static: PR-3 contract field reads unchanged. |
| UA5-A | Item UA.5 implementation landed; publish-blocking operator-language explanation observable. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA5_PUBLISH_EXPLANATION_EXECUTION_LOG_v1.md`; PR commit SHA recorded; final operator-language reason strings recorded in this gate spec's closeout document. | Live: when Matrix Script publish is blocked on a fresh contract-clean adverse-state sample, the operator reads "为什么不能发布 → 我能做什么" in operator language. Static: no new reason code introduced; cross-line `publishable` re-derivation unchanged. |
| UA6-A | Item UA.6 implementation landed; operator-action zoning observable across Matrix Script-scoped surfaces. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_UA6_ACTION_ZONING_EXECUTION_LOG_v1.md`; PR commit SHA recorded. | Live: an operator opens each Matrix Script-scoped surface and visibly distinguishes "what you do here" from "what the system shows you" without prompting. Static: no Hot Follow surface re-zoned; no Digital Anchor surface re-zoned. |
| HF-PRES | Hot Follow baseline preserved across PR-UA1 → PR-UA6. | Bytewise / behavioral regression report appended to each per-PR execution log. | Hot Follow golden path PASS on each PR; no commits to Hot Follow files; no Hot Follow Delivery Center change observed; Hot Follow advisory rendering unchanged; Hot Follow Workbench unchanged. |
| DA-PRES | Digital Anchor freeze preserved across PR-UA1 → PR-UA6. | Per-PR confirmation appended to each per-PR execution log. | No commits to `gateway/app/services/digital_anchor/*` runtime; no commits to `gateway/app/templates/digital_anchor*`; Plan A §2.1 hide guards still in force; no operator submission affordance for Digital Anchor reachable in the deployed environment. |
| FORBID | No forbidden item from §4 has landed. | Per-PR scope-fence check appended to each per-PR execution log; final closeout audit appended to a new aggregating execution log under `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_ALIGNMENT_PHASE_CLOSEOUT_v1.md`. | Reviewer / Merge Owner audits each PR's file-touched list against §5.1 → §5.6; aggregating closeout confirms no §4 item present in the merged tree. The first-phase A7 closeout signoff block is **not** touched by any UA.* PR (per §4.10). |
| UA7 | This phase closeout signoff recorded by Architect (Raobin) + Reviewer (Alisa); Operations team coordinator (Jackie) confirms operator-comprehension deltas observed in the trial environment. | `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_ALIGNMENT_PHASE_CLOSEOUT_v1.md` §"Closeout signoff"; this gate spec §10.1 closeout marker filled. | Architect + Reviewer + Coordinator sign the closeout block on its own evidence (UA1-A → UA6-A + HF-PRES + DA-PRES + FORBID). UA7 is independent of first-phase A7 — both signoffs may exist in either order; neither is a precondition for the other. |

When UA1-A → UA6-A + HF-PRES + DA-PRES + FORBID + UA7 all hold, this Plan E comprehension phase is closed; the next Plan E phase gate spec MAY be authored (separately) for any §4 item, subject to its own pre-conditions. Platform Runtime Assembly remains BLOCKED until **all** Plan E phases close **plus** a separate "Plan E phases all closed + Platform Runtime Assembly start authority" decision is recorded.

---

## 7. Preserved Freezes (binding, restated)

This Plan E comprehension phase preserves the following freezes verbatim. Each freeze is bound to its native authority and cannot be relaxed by this gate spec.

### 7.1 Hot Follow baseline unchanged

- Hot Follow remains the operational baseline line for ApolloVeo 2.0 per [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). No commits to Hot Follow business behavior under this gate spec; the Hot Follow structural debt (`tasks.py` 3,480 lines / `hot_follow_api.py` 2,325 lines / `task_view.py::build_hot_follow_workbench_hub()` 492 lines) is **deferred to Platform Runtime Assembly Wave** and is out of scope for any UA.* PR.
- Hot Follow Delivery Center labels, Hot Follow Workbench information hierarchy, Hot Follow entry form labels, Hot Follow advisory rendering, Hot Follow publish-blocking explanations are **unchanged** by this gate spec. Hot Follow's existing operator-comprehension state is preserved verbatim as the operational baseline.

### 7.2 Digital Anchor frozen

- Digital Anchor remains inspect-only / contract-aligned per [unified map §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) and Plan A §2.1 / §12 condition 2.
- Digital Anchor New-Tasks card click target ([gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html)) and the temp `/tasks/connect/digital_anchor/new` route stay hidden / disabled / preview-labeled in the trial environment under Plan A §2.1.
- The formal `/tasks/digital-anchor/new` route, Phase D.1 publish-feedback write-back, `create_entry_payload_builder`, Phase B render production path, Workbench role/speaker panel mount as operator-facing surface, Delivery Center surface — **all unchanged** by this gate spec. No Digital Anchor surface is re-labelled / re-grouped / re-zoned by any UA.* PR.

### 7.3 No platform-wide expansion

- This gate spec authorizes Matrix Script operator-comprehensible UI alignment **only**. It does not authorize Asset Library / promote / asset supply / cross-line publish_readiness producer / cross-line panel dispatch contract object / L4 advisory producer / L3 final_provenance emitter / Digital Anchor implementation.
- Each forbidden cross-line item waits for its **own** subsequent Plan E phase gate spec authoring step. There is no implicit promotion of any §4 item under cover of a UA.* PR.
- Frontend rebuild (React/Vite full); studio shell; tool catalog page; multi-tenant platform — **all forbidden** per [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) and Plan A §4.1. UA.6 uses existing markup and styling primitives only; no new component framework / style system / build dependency.
- New / third production line commissioning — **forbidden** per [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md).

### 7.4 Plan E does NOT equal Platform Runtime Assembly

- Platform Runtime Assembly is a **separate wave** with its own authority at [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md). It is gated on **all** Plan E phases closing **plus** a separate wave-start authority; its Phases A–E (Shared Logic Port Merge / Compose Service Extraction / Declarative Ready Gate / Runtime Assembly Skeleton / OpenClaw stub) are not touched under this gate spec.
- No "shared logic port merge" prep, "compose service extraction" prep, "declarative ready gate" prep, or "runtime assembly skeleton" prep is permitted under cover of a UA.* PR.
- UA.1 → UA.6 are operator-comprehension steps for one production line; they do not advance the platform-runtime-assembly agenda.

### 7.5 No provider / model / vendor controls

- Provider / model / vendor / engine selectors / controls / consoles are **forbidden at all phases** per validator R3 ([docs/contracts/factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md) R3) and the design-handoff red line 6.
- Operator-visible payloads MUST NOT carry `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any donor namespace identifier per [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). The sanitization guard at [gateway/app/services/operator_visible_surfaces/projections.py:36](../../gateway/app/services/operator_visible_surfaces/projections.py) MUST NOT be relaxed by any UA.* PR.

### 7.6 First-phase A7 closeout signoff remains intentionally pending

- The first-phase A7 closeout signoff at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) remains owned by Raobin / Alisa / Jackie on the first phase's own evidence. This comprehension-phase gate spec **does not** force, accelerate, condition, or tie its own opening or closing to A7. A7 may be signed at any point Raobin / Alisa / Jackie choose; this phase's UA7 closeout is independent of A7.

---

## 8. Posture Preserved by This Gate Spec

| Posture element | State after this gate spec is authored | Authority pointer |
| --- | --- | --- |
| Hot Follow = operational baseline line | preserved — no behavior reopen authorized; no comprehension-layer change | [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), §7.1 of this gate spec |
| Matrix Script = current next operator-facing line | first-phase engineering complete; second-phase (this gate spec) authored; implementation BLOCKED until §10 approval | [unified map §4.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [first-phase gate spec](plan_e_matrix_script_operator_facing_gate_spec_v1.md), this gate spec §2 / §10 |
| Digital Anchor = inspect-only / contract-aligned, no operator submission this wave | preserved — explicit §4.2 + §7.2 forbiddens | [unified map §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), §7.2 of this gate spec |
| Plan E first-phase engineering | COMPLETE (PR #100 / PR #101 / PR #102) | [first-phase closeout §2.1 / §2.2 / §2.3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) |
| Plan E first-phase closeout signoff (A7) | INTENTIONALLY PENDING — not touched by this gate spec | [first-phase closeout §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md), §7.6 of this gate spec |
| Plan E comprehension-phase gate spec (this document) | **AUTHORED + SIGNED OPEN** (Raobin 2026-05-04 14:05; Alisa 2026-05-04 14:18) | this gate spec §10 |
| Plan E comprehension-phase implementation | gate OPEN for §3 items only on signoff-PR merge to `main`; first UA.* implementation PR may open thereafter | this gate spec §2 (C6) + §10 |
| Platform Runtime Assembly | **BLOCKED** until **all** Plan E phases close + separate wave-start authority | [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) |
| Capability Expansion (W2.2 / W2.3 / durable persistence / runtime API / third line) | **BLOCKED** until Platform Runtime Assembly signoff | [unified map §7.5](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) |
| Frontend patching beyond what is shipped | **BLOCKED** beyond the §3 Matrix Script-scoped comprehension scope | [unified map §3.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [Operator-Visible Surface Validation Wave 指挥单 §7](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md), §7.3 of this gate spec |
| Provider / model / vendor / engine controls | **forbidden** at all phases | [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), validator R3, §7.5 of this gate spec |
| Donor namespace import | **forbidden** | [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md) |

---

## 9. What This Gate Spec Does NOT Do

- Does **NOT** implement Item UA.1 → UA.6. Implementation is BLOCKED until §10 approval is signed.
- Does **NOT** authorize any item enumerated in §4. Subsequent Plan E phases for those items require their own gate-spec authoring step under the same discipline.
- Does **NOT** force, accelerate, condition, or tie its own opening or closing to the first-phase A7 closeout signoff at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3](../execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md). A7 is independent paperwork on independent evidence.
- Does **NOT** start Platform Runtime Assembly. That wave has its own start authority and is gated on **all** Plan E phases closing **plus** a separate wave-start authority.
- Does **NOT** start Capability Expansion. That wave is gated on Platform Runtime Assembly signoff.
- Does **NOT** unfreeze Digital Anchor. The Digital Anchor freeze stays in force; submission paths stay hidden / disabled / preview-labeled.
- Does **NOT** reopen Hot Follow business behavior; does **NOT** re-label Hot Follow surfaces; does **NOT** re-group Hot Follow surfaces; does **NOT** re-zone Hot Follow surfaces.
- Does **NOT** mutate any frozen contract. If an in-scope item requires a contract amendment, the amendment must land first in a documentation-only PR with this gate spec updated to cite the amendment.
- Does **NOT** modify [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](plan_e_matrix_script_operator_facing_gate_spec_v1.md) or any first-phase per-PR execution log.
- Does **NOT** count as a "Plan E gate spec for the entire Plan E candidate set"; it is the **second** Plan E phase, scoped exclusively to Matrix Script operator-comprehensible UI alignment. Subsequent phases for Digital Anchor / Asset Library / promote / L4 advisory / L3 final_provenance / unified publish_readiness / panel dispatch contract object / operator-driven Phase B authoring are explicitly out of scope.

---

## 10. Approval Signoff (gate-opening block)

This Plan E comprehension phase implementation is BLOCKED until the following block is fully signed. Implementation PRs MUST cite this signed block in their PR body.

```
Architect — Raobin
  Date / time:        2026-05-04 14:05
  Signature / handle: Raobin
  Statement:          I confirm the §3 allowed scope is exhaustively bounded
                      to UA.1 / UA.2 / UA.3 / UA.4 / UA.5 / UA.6 only;
                      the §4 forbidden scope is explicitly preserved;
                      the §5 PR slicing plan is single-item, scope-fenced,
                      operator-visible, independently revertable, and
                      truth-preserving; the §6 acceptance evidence is
                      verifiable; the §7 preserved freezes remain binding;
                      and the first-phase A7 closeout signoff at
                      PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md §3
                      is **not** touched by this gate-spec opening or by
                      any UA.* PR. I authorize Matrix Script
                      operator-comprehensible UI alignment implementation
                      under this gate spec only. No Digital Anchor
                      implementation, no Hot Follow behavior reopen, no
                      Hot Follow comprehension-layer change, no platform-wide
                      expansion, no Platform Runtime Assembly, and no
                      forced first-phase A7 signing are implied by this signoff.

Reviewer — Alisa
  Date / time:        2026-05-04 14:18
  Signature / handle: Alisa
  Statement:          I confirm the C1 → C5 entry conditions hold per the
                      cited artifacts; C5 is satisfied under "intentionally
                      pending" — this gate spec does not advance first-phase
                      A7 paperwork. I confirm the §3 allowed scope and §4
                      forbidden scope have no overlap. I authorize independent
                      merge-gate review of UA.1 / UA.2 / UA.3 / UA.4 / UA.5 /
                      UA.6 PRs against this gate spec, and I will reject any
                      PR that lands a §4 item, breaks a §7 freeze, or touches
                      the first-phase A7 signoff block. The Plan E
                      comprehension-phase implementation gate is OPEN for
                      the items in §3 only.

Operations team coordinator — Jackie
  Date / time:        <fill — yyyy-mm-dd hh:mm>
  Signature / handle: <fill>
  Statement:          I confirm the Plan A §2.1 hide guards remain in
                      force in the trial environment for the duration of
                      this Plan E comprehension phase. I will validate
                      operator-comprehension deltas of UA.1 → UA.6 in the
                      trial environment and append observations to the
                      per-item execution logs and the aggregating
                      PLAN_E_MATRIX_SCRIPT_UI_ALIGNMENT_PHASE_CLOSEOUT_v1.md.
                      I confirm this gate spec does not require, accelerate,
                      or modify the first-phase A7 closeout signoff;
                      A7 stays in my own pending queue and will be signed
                      on its own evidence in its own time.
```

Coordinator-side signoff is **intentionally left as `<fill>` placeholder** — per §10 last paragraph, the coordinator signoff is required for the closeout per §6 row UA7, not for the gate opening. Per the user-mandated step-1 scope, the coordinator-side closeout stays intentionally pending unless the gate spec explicitly requires it for opening (it does not).

The implementation PRs MAY open only after architect + reviewer signoff lines above are filled and committed in a documentation-only PR. The coordinator signoff is required for the closeout per §6 row UA7, not for the gate opening.

### 10.1 Closeout marker (filled at phase closeout)

Closeout aggregating audit: `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_ALIGNMENT_PHASE_CLOSEOUT_v1.md` (authored at phase-close time).

| Acceptance row | Verdict | Evidence |
| --- | --- | --- |
| UA1-A — Item UA.1 entry-surface comprehension | `<fill at PR-UA1 land>` | `<execution log path; PR commit SHA>` |
| UA2-A — Item UA.2 Workbench information hierarchy | `<fill at PR-UA2 land>` | `<execution log path; PR commit SHA>` |
| UA3-A — Item UA.3 variation panel readability | `<fill at PR-UA3 land>` | `<execution log path; PR commit SHA>` |
| UA4-A — Item UA.4 Delivery Center operator-language alignment | `<fill at PR-UA4 land>` | `<execution log path; PR commit SHA>` (final operator-language label strings recorded here) |
| UA5-A — Item UA.5 publish-blocking explanation clarity | `<fill at PR-UA5 land>` | `<execution log path; PR commit SHA>` (final operator-language reason strings recorded here) |
| UA6-A — Item UA.6 operator-action zoning / affordance clarity | `<fill at PR-UA6 land>` | `<execution log path; PR commit SHA>` |
| HF-PRES — Hot Follow baseline preserved | `<fill at phase close>` | `<aggregating closeout doc path>` |
| DA-PRES — Digital Anchor freeze preserved | `<fill at phase close>` | `<aggregating closeout doc path>` |
| FORBID — No §4 forbidden item landed | `<fill at phase close>` | `<aggregating closeout doc path>` |
| UA7 — Closeout signoff recorded | `<fill at phase close>` | `<aggregating closeout doc §"Closeout signoff">` |

Implementation phase status (this closeout marker, updated 2026-05-04 at gate-opening signoff): the gate spec is **AUTHORED + SIGNED OPEN** (Architect Raobin 2026-05-04 14:05; Reviewer Alisa 2026-05-04 14:18); implementation MAY proceed strictly within §3 once this signoff PR merges to `main`. Coordinator (Jackie) signoff remains intentionally `<fill>` because §10 binds the coordinator signoff to §6 row UA7 (closeout), not to gate-opening. First-phase A7 signoff status is **independent** and remains intentionally pending: this gate spec did not touch it and does not advance it.

---

End of Plan E — Matrix Script Operator-Comprehensible UI Alignment Gate Spec v1.
