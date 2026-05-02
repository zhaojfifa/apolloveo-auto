# Plan B / C / D Contract Freeze Execution Log v1

Date: 2026-05-02
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave")
Authority: [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) §13
Scope: documentation / contract artifacts only — no code, no UI, no runtime change.

## 1. Reading Declaration

There is no top-level `CLAUDE.md` in this repository. The equivalent authority chain followed for this work:

- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) — engineering rules (router/service caps, contract-first, truth-source rules).
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — current stage and forbidden work list.
- [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md) — engineering index.
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) — active wave authority.
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) — gap review v1, the immediate driver for Plans B / C / D.
- Existing line contracts under `docs/contracts/digital_anchor/` and `docs/contracts/matrix_script/`.
- Existing factory generic contracts: `factory_delivery_contract_v1`, `factory_packet_envelope_contract_v1`, `factory_packet_validator_rules_v1`, `hot_follow_current_attempt_contract_v1`, `hot_follow_projection_rules_v1`, `hot_follow_ready_gate.yaml`.
- Product authorities: `docs/product/broll_asset_supply_freeze_v1.md`, `docs/product/asset_supply_matrix_v1.md`.
- Read-only code references: `gateway/app/services/operator_visible_surfaces/projections.py`, `gateway/app/services/matrix_script/create_entry.py`, `gateway/app/services/matrix_script/delivery_binding.py`.

## 2. Phase Confirmation

Phase = **Operator-Visible Surface Validation Wave** (per master plan v1.1 line 137 and gap review §3). Permitted next work per gap review §13: documentation / contract artifacts for Plans B / C / D, in parallel; Plan A waits on B + C + D; Plan E waits on A.

Forbidden in this wave (reasserted):

- Platform Runtime Assembly.
- Capability Expansion Gate (W2.2 / W2.3).
- New-line / third-line runtime loading.
- Frontend patching, UI implementation, or template edits.
- Any `.py` / `.html` change.
- Reopening Hot Follow business behavior.
- Mutation of frozen Matrix Script or Digital Anchor packet truth, schema, or sample.
- Vendor / model / provider / engine identifiers in any new contract (validator R3).
- State-shape fields on entry surfaces (validator R5).

## 3. Track 1 — Plan B Scope

Goal: return Matrix Script and Digital Anchor to packet truth at the contract layer. Four new contracts.

Contracts added (all `.md` under `docs/contracts/`):

| # | File | Purpose |
| - | ---- | ------- |
| B1 | [docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md](../contracts/digital_anchor/create_entry_payload_builder_contract_v1.md) | Single legal seeding path from closed entry field set → packet `line_specific_refs[]` skeleton. Mirrors the Matrix Script analogue at [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py) at the contract level. |
| B2 | [docs/contracts/digital_anchor/new_task_route_contract_v1.md](../contracts/digital_anchor/new_task_route_contract_v1.md) | Canonical `/tasks/digital-anchor/new` GET/POST route contract; declares deprecation of generic temp `/tasks/connect/digital_anchor/new`. Mirrors commit `4896f7c` for Matrix Script. |
| B3 | [docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md](../contracts/digital_anchor/publish_feedback_writeback_contract_v1.md) | Phase D.1 write-back direction for Digital Anchor publish feedback closure. Closed event set; append-only discipline; per-row scope (role + segment); UTC monotonic timestamping. |
| B4 | [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md) | Pins the artifact-lookup function shape that resolves the five `"artifact_lookup": "not_implemented_phase_c"` placeholders at [gateway/app/services/matrix_script/delivery_binding.py:93-125](../../gateway/app/services/matrix_script/delivery_binding.py:93). Failure mode: explicit `artifact_lookup_unresolved`; never throws, never fabricates. |

Validation notes:

- Every B contract carries an `Authority:` block citing the gap review v1 + the active wave authority.
- B1 reuses the entry contract's mapping table verbatim; no second mapping authored.
- B3 mirrors the Matrix Script Phase D.1 closure shape (closed `publish_status` enum `{pending, published, failed, retracted}`).
- B4 reuses Plan D's `final_provenance` enum verbatim on its `ArtifactHandle.provenance` field.
- No vendor / model / provider / engine identifier appears outside an explicit "MUST NOT" forbid-clause.

## 4. Track 2 — Plan C Scope

Goal: convert the B-roll product freeze into contract truth and pin scene-pack non-blocking explicitly. Three new contracts + two existing-file amendments.

Contracts added:

| # | File | Purpose |
| - | ---- | ------- |
| C1 | [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md) | Closed metadata schema for Asset Library objects (id, kind, line_availability, tags, provenance, version, quality_threshold, usage_limits, badges). Closed `kind` enum aggregates per-line asset kinds from `asset_supply_matrix_v1`. Closed facet set drawn from `broll_asset_supply_freeze_v1` §1. |
| C2 | [docs/contracts/promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md) | Closed request schema for operator-initiated promote intent. Source artifact remains immutable. No asset id returned synchronously. |
| C3 | [docs/contracts/promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md) | Append-only closure / audit trail. Closed `request_state` enum `{requested, approved, rejected}`. Closed `rejection_reason` taxonomy. Closed `event_kind` enum. Mirrors the Matrix Script closure pattern. |

Existing-file amendments (additive only):

| File | Amendment |
| ---- | --------- |
| [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) | Added §"Per-Deliverable Required / Blocking Fields" pinning `required: bool` + `blocking_publish: bool` per row. Added §"Scene-Pack Non-Blocking Rule" pinning `scene_pack_blocking_allowed: false` (Plan C §C4 + Plan D §D1 D-related fields). |
| [docs/contracts/hot_follow_projection_rules_v1.md](../contracts/hot_follow_projection_rules_v1.md) | Added §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment, 2026-05-02)" cross-referencing the factory delivery amendment, pinning Hot Follow scene-pack non-blocking explicitly at the projection layer. |

Validation notes:

- Every C contract carries an `Authority:` block citing the gap review v1 + the active wave authority + the product freeze.
- C1 closed `kind` enum traces verbatim to `asset_supply_matrix_v1` §"Input asset kinds" + `broll_asset_supply_freeze_v1` §7.
- C1/C2/C3 license, reuse_policy, source enums trace verbatim to `broll_asset_supply_freeze_v1` §3.
- Asset/Artifact boundary is binding across C1/C2/C3 — assets exist only via promote acceptance.

## 5. Track 3 — Plan D Scope

Goal: anchor Workbench / Board / Delivery to one shared L4 contract. Three new contracts + one existing-file amendment.

Contracts added:

| # | File | Purpose |
| - | ---- | ------- |
| D1 | [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md) | Single L4 producer contract. Inputs: `ready_gate` + L2 `final_fresh` + L3 `final_provenance` + `delivery_binding.deliverables[]` (with `required` + `blocking_publish` per Plan C/D amendments). Output: `{publishable, head_reason (closed enum), blocking_advisories[]}`. Single-producer rule binds Board / Workbench / Delivery as consumers. |
| D3 | [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) | Closed `ref_id → panel_kind` map (six pairs verified verbatim against [gateway/app/services/operator_visible_surfaces/projections.py:239-246](../../gateway/app/services/operator_visible_surfaces/projections.py:239)). Closed-by-default rule; new line cannot mount without contract amendment. |
| D4 | [docs/contracts/l4_advisory_producer_output_contract_v1.md](../contracts/l4_advisory_producer_output_contract_v1.md) | Pins `emit_advisories(l3_current_attempt, ready_gate) -> list[Advisory]` shape. Closed advisory id set is the verbatim taxonomy frozen at `hot_follow_projection_rules_v1.md:272-335`. Pure projection; no I/O; no truth invention. |

Existing-file amendment (additive only):

| File | Amendment |
| ---- | --------- |
| [docs/contracts/hot_follow_current_attempt_contract_v1.md](../contracts/hot_follow_current_attempt_contract_v1.md) | Added `final_provenance: current\|historical` field to the L3 `current_attempt` shape, plus a §"`final_provenance` Field (Plan D Amendment, 2026-05-02)" section pinning producer/consumer rules. The Plan B B4 contract reuses the same enum on its `ArtifactHandle.provenance` field. |

Validation notes:

- Every D contract carries an `Authority:` block citing the gap review v1 + the active wave authority.
- D1 closed `head_reason` enum is exhaustive over the declared input space.
- D1's single-producer rule explicitly forbids per-surface fallback derivation.
- D3 dispatch map verified against in-code dict; no entries invented or dropped.
- D4 advisory taxonomy is verbatim from the existing projection rules file; no new advisory codes minted.

## 6. Validation

### 6.1 File placement

All twelve documentation artifacts live under `docs/contracts/` (line-namespaced for the four B contracts; flat for cross-line C / D contracts). The execution log lives under `docs/execution/`. Naming follows the repo convention (`*_contract_v1.md`, `*_LOG_v1.md`).

### 6.2 Forbidden-key audit

```
grep -InE '(vendor_id|model_id|provider_id|engine_id|raw_provider_route|donor_|swiftcraft_)' \
  docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md \
  docs/contracts/digital_anchor/new_task_route_contract_v1.md \
  docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md \
  docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md \
  docs/contracts/asset_library_object_contract_v1.md \
  docs/contracts/promote_request_contract_v1.md \
  docs/contracts/promote_feedback_closure_contract_v1.md \
  docs/contracts/publish_readiness_contract_v1.md \
  docs/contracts/workbench_panel_dispatch_contract_v1.md \
  docs/contracts/l4_advisory_producer_output_contract_v1.md
```

Result: every match is inside an explicit "MUST NOT", "Forbidden", or "never" clause that declares the forbidden vocabulary itself. No new contract introduces a vendor/model/provider/engine/donor identifier as a positive field, response, or example.

### 6.3 State-shape audit

Entry / intent contracts (B1, B2, C2): no `status`, `ready`, `done`, `current_attempt`, `final_ready`, `publishable`, `delivery_ready` field appears as a positive input/output field. Where these tokens appear, they are inside explicit forbid-clauses. Validator R5 satisfied.

Exception explicitly accounted for: B1's output payload carries `status: "pending"` as a **task-repository row column** (mirroring the existing Matrix Script `create_entry.py` payload). This is documented in B1 §"Outputs (closed)" as a repository column, NOT packet truth, and the seeded packet itself carries no `status` field. Validator R5 boundary is preserved.

### 6.4 Wave-authority alignment

Every new contract restates the wave's BLOCKED list (Platform Runtime Assembly, Capability Expansion, third-line onboarding, frontend patching) in a §"What this contract does NOT do" section.

### 6.5 Code-untouched audit

```
$ git status --short
 M docs/contracts/factory_delivery_contract_v1.md
 M docs/contracts/hot_follow_current_attempt_contract_v1.md
 M docs/contracts/hot_follow_projection_rules_v1.md
?? docs/contracts/asset_library_object_contract_v1.md
?? docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md
?? docs/contracts/digital_anchor/new_task_route_contract_v1.md
?? docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md
?? docs/contracts/l4_advisory_producer_output_contract_v1.md
?? docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md
?? docs/contracts/promote_feedback_closure_contract_v1.md
?? docs/contracts/promote_request_contract_v1.md
?? docs/contracts/publish_readiness_contract_v1.md
?? docs/contracts/workbench_panel_dispatch_contract_v1.md
```

Zero `.py`, `.html`, `.tsx`, `.yaml`, or schema-file changes. All twelve modified or new files are `.md` documentation under `docs/`.

### 6.6 Cross-reference integrity

- B1 references B2 and the existing Phase A entry contract; both files exist.
- B2 references B1 and the Matrix Script alignment evidence doc; both exist.
- B3 references Phase D.0 closure contract + Matrix Script analogue; both exist.
- B4 references Plan D `final_provenance` (D2 amendment to hot_follow_current_attempt) + the future `publish_readiness_contract_v1` (D1); D1 is created in this same wave.
- C1/C2/C3 cross-reference each other; all three created in this wave.
- C4 amendment (in factory_delivery + hot_follow_projection_rules) cross-references Plan D D1.
- D1 references C/D amendments (`required`, `blocking_publish`, `scene_pack_blocking_allowed`, `final_provenance`); all present.
- D3 references in-code map at `projections.py:239-246`; map verified verbatim.
- D4 references advisory taxonomy at `hot_follow_projection_rules_v1.md:272-335`; verified verbatim.

## 7. Remaining Blockers

- Plan A (Ops Trial Readiness) is contract-ready; gated on review/acceptance of Plans B + C + D.
- Plan E (next operator-visible implementation gate) requires Plan A executed and trial write-up filed before opening.
- Implementation of any contract above is **gated to Plan E** — no implementation in this wave.
- The `not_implemented_phase_c` placeholder string at [gateway/app/services/matrix_script/delivery_binding.py:93-125](../../gateway/app/services/matrix_script/delivery_binding.py:93) is contract-resolved by B4 but remains in code until Plan E.
- Per-line `final_provenance` analogues for Matrix Script and Digital Anchor delivery binding contracts (per gap review §13 Plan D2 replication directive) are scheduled for Plan E or the next contract wave; the canonical enum is now frozen by the Plan D amendment to `hot_follow_current_attempt_contract_v1.md`, so the per-line replication is mechanical.

## 8. Final Gate Decision

- **Plan B contract freeze:** PASS
  - B1 (Digital Anchor create-entry payload builder contract): PASS
  - B2 (Digital Anchor `/tasks/digital-anchor/new` route contract): PASS
  - B3 (Digital Anchor Phase D.1 publish-feedback write-back contract): PASS
  - B4 (Matrix Script `result_packet_binding` artifact-lookup contract): PASS
- **Plan C contract freeze:** PASS
  - C1 (asset_library_object_contract_v1): PASS
  - C2 (promote_request_contract_v1): PASS
  - C3 (promote_feedback_closure_contract_v1): PASS
  - C4 (explicit `scene_pack_blocking_allowed: false` amendment to factory_delivery + projection_rules): PASS
- **Plan D contract freeze:** PASS
  - D1 (publish_readiness_contract_v1, unified L4): PASS
  - D2 (`final_provenance` L3 field amendment to hot_follow_current_attempt_contract_v1): PASS
  - D3 (workbench_panel_dispatch_contract_v1): PASS
  - D4 (l4_advisory_producer_output_contract_v1): PASS
- **Plan A readiness:** YES (all of B + C + D contract-frozen; Plan A may now be authored as the next contract wave per gap review §13)
- **Runtime Assembly:** BLOCKED (reasserted; no work permitted until this wave green + Plan A executed + Plan E gate opens)
- **Capability Expansion:** BLOCKED (reasserted; W2.2 / W2.3 forbidden until Platform Runtime Assembly signed off)
- **Frontend patching:** BLOCKED (reasserted; UI implementation gated to Plan E acceptance)

End of execution log.
