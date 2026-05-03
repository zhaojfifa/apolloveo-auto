# Current Engineering Focus

## Current Stage

Factory Alignment Review Gate Active

## Current Main Line

- active architecture gate from `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- Plan A trial correction set from `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` complete (items §8.A, §8.B, §8.C, and §8.D all PASS; the fresh corrected Matrix Script trial sample is now fully briefed and the operations team may proceed with §7.1 sample creation per `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`)
- Matrix Script follow-up blocker review v1 from `docs/reviews/matrix_script_followup_blocker_review_v1.md` chain complete: §8.G (Phase B panel render correctness), §8.E (workbench shell line-conditional rendering), §8.F (opaque-ref discipline — Option F1 only; F2 / F3 rejected this wave), and §8.H (operator brief re-correction with binding product-meaning of `source_script_ref` — asset identity handle, not body-input, not publisher-URL ingestion, not currently dereferenced) all PASS; the Plan A Matrix Script trial corrections set §8.A–§8.H is now closed; per the user instruction landing §8.H, Matrix Script live-run BLOCK is released by virtue of §8.H land, subject to the eight conditions enumerated in the trial brief §12; live-trial execution by operations team against the §7.1 sample wave remains the Plan E pre-condition #1; Plan E retains Option F2 (in-product minting flow) as the eventual replacement for the §8.F / §8.H operator transitional convention `content://matrix-script/source/<token>`
- execution-path migration only under the current factory alignment gate
- live provider / media validation for Hot Follow Burmese (`my`) and Vietnamese (`vi`)
- action replica planning-to-runtime binding preparation without reopening Phase-2 foundation refactors

## Allowed Next Work

- execution-path migration only where it is required for live validation
- live provider / media validation for `my` and `vi`
- action replica planning-to-runtime binding preparation only when it does not bypass the new-line onboarding gate
- scoped docs / runbook / verification maintenance tied to Phase-3 execution validation
- docs / runbook / validation maintenance tied to Phase-2 controlled execution
- Plan A live-trial signed closeout recorded on 2026-05-03 by Jackie / Raobin / Alisa per `docs/execution/PLAN_A_SIGNOFF_CHECKLIST_v1.md` §6; Plan E pre-condition #1 satisfied for gate-spec authoring purposes per checklist §3 + §4
- Plan E gate spec for Matrix Script operator-facing implementation authored at `docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md` (with execution log at `docs/execution/PLAN_E_GATE_SPEC_AUTHORING_EXECUTION_LOG_v1.md`); this is the **first** Plan E phase, scoped exclusively to Matrix Script operator-facing implementation (E.MS.1 = B4 artifact lookup; E.MS.2 = Option F2 in-product `content://` minting flow; E.MS.3 = Matrix Script Delivery Center per-deliverable `required` / `blocking_publish` rendering); subsequent Plan E phases for Digital Anchor / Asset Library / promote services / L4 advisory producer / L3 `final_provenance` emitter / unified `publish_readiness` producer / workbench panel dispatch contract object / operator-driven Phase B authoring are explicitly deferred and require their own future gate-spec authoring step under the same discipline
- Plan E gate spec §10 architect (Raobin) + reviewer (Alisa) signoff filled and committed on 2026-05-03 per `0b73644`; entry condition E7 SATISFIED; Plan E implementation gate OPEN for §3 items only (E.MS.1 / E.MS.2 / E.MS.3)
- Plan E PR-1 / Item E.MS.1 (Matrix Script B4 `result_packet_binding.artifact_lookup`) implementation landed on 2026-05-04 with execution log at `docs/execution/PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md`; merged into `main` as commit `7a1e7a6` (PR #100); new dedicated test file `gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py` (30/30 cases passing on local Python 3.9.6); `not_implemented_phase_c` placeholders retired across all five Matrix Script Delivery Center rows in favor of contract-pinned `artifact_lookup` results (today: `artifact_lookup_unresolved` because L3 `final_provenance` emitter remains forbidden in this Plan E phase per gate spec §4.2; future Plan E phases that land D2 will populate real `ArtifactHandle` mappings without B4 code change); no Hot Follow / Digital Anchor / cross-line file touched; no contract / schema / sample / template mutation; gate spec §6 row A1 PASS
- Plan E PR-2 / Item E.MS.2 (Matrix Script Option F2 in-product `content://` minting flow) implementation landed on 2026-05-04 with execution log at `docs/execution/PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md`; merged into `main` as commit `2822ad0` (PR #101); new minting service module `gateway/app/services/matrix_script/source_script_ref_minting.py` exposing `mint_source_script_ref(*, requested_by=None)` allocating a `mint-<16-hex-chars>` UUID4-derived opaque token wrapped in `content://matrix-script/source/<token>`; new matrix-script-scoped JSON POST endpoint at `/tasks/matrix-script/source-script-refs/mint` inside `gateway/app/routers/tasks.py`; new "铸造句柄" operator affordance + helper text + small inline JS progressive-enhancement on `gateway/app/templates/matrix_script_new.html`; additive contract sub-section §"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)" appended to `docs/contracts/matrix_script/task_entry_contract_v1.md`; new dedicated import-light test module `gateway/app/services/tests/test_matrix_script_f2_minting_flow.py` (35/35 cases passing); `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` unchanged at `(content, task, asset, ref)`; `_validate_source_script_ref_shape` unchanged; §0.2 product-meaning of `source_script_ref` preserved; no Hot Follow / Digital Anchor / cross-line file touched; gate spec §6 row A2 PASS
- Plan E PR-3 / Item E.MS.3 (Matrix Script Delivery Center per-deliverable `required` / `blocking_publish` zoning) implementation landed on 2026-05-04 with execution log at `docs/execution/PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md`; extended `gateway/app/services/matrix_script/delivery_binding.py` with module constant `SCENE_PACK_BLOCKING_ALLOWED = False`, private helper `_clamp_blocking_publish` (defensively enforcing the contract validator invariant `required=false ⇒ blocking_publish=false`), and the additive `blocking_publish` field on every Matrix Script Delivery Center deliverable row per the Plan C amendment to `docs/contracts/factory_delivery_contract_v1.md`; Matrix Script line policy applied — variation_manifest + slot_bundle = required+blocking; subtitle_bundle + audio_preview = required-mirror; scene_pack hardcoded `required=False, blocking_publish=False` per the §"Scene-Pack Non-Blocking Rule" independent of any per-task `pack` capability flag; existing PR-1 row-key-set assertion minimally updated to accept the additive field; new dedicated import-light test module `gateway/app/services/tests/test_matrix_script_delivery_zoning.py` (16/16 cases passing — per-row zoning on canonical sample, clamp helper unit tests, validator invariant cross-row check, scene-pack contract enforcement under adversarial `pack.required=True`, subtitles + dub capability flag negative-path zoning, surface integration sanity); 81/81 PASS overall on local Python 3.9.6 (16 PR-3 + 30 PR-1 B4 + 35 PR-2 F2); no Hot Follow / Digital Anchor / cross-line file touched; no contract / schema / sample / template mutation; gate spec §6 row A3 PASS; rows A4 (Hot Follow golden-path live regression — coordinator-side check) and A5 (per-PR Digital Anchor freeze confirmation) and A6 (aggregating closeout audit) and A7 (closeout signoff from Raobin / Alisa / Jackie) remain pending; the **implementation phase** of Plan E for Matrix Script operator-facing scope (E.MS.1 / E.MS.2 / E.MS.3) is now complete pending those non-implementation closeout steps
- documentation re-anchoring under `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` §3.3 (the next-wave engineering navigation anchor at `docs/execution/MATRIX_SCRIPT_NEXT_WAVE_START_NOTE_v1.md` is itself an instance; the Plan E gate spec is also a documentation-only authoring instance; **neither** unblocks Plan E implementation, **neither** starts Platform Runtime Assembly)
- evidence write-back on already-shipped corrections (no contract / runtime change)
- W2.1 B1–B4 architect / reviewer signoff (paperwork only; implementation already green)

## Forbidden Work

- generic agent platform build
- second production line business rollout
- second/new production line onboarding before factory alignment gate prerequisites clear
- OpenClaw expansion beyond boundary preparation
- broad studio shell / product-shell import
- unrelated runtime rewrites
- reopening Phase-2 foundation refactors in the same task
- new line-specific logic in `tasks.py`
- new mixed four-layer projection expansion in `task_view.py`
- Plan E implementation (Matrix Script operator-facing items E.MS.1 / E.MS.2 / E.MS.3 included) until `docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md` §10 architect (Raobin) + reviewer (Alisa) signoff lines are filled and committed; the gate spec is authored but the implementation gate is not yet OPEN
- any item enumerated in `docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md` §4 forbidden scope — Digital Anchor B1 / B2 / B3 / formal route / Phase D.1 / Phase B render (preserves Digital Anchor freeze); Asset Library object service / Asset Supply page / promote intent service / promote closure service / unified `publish_readiness` producer / L3 `final_provenance` emitter / workbench panel dispatch contract object conversion / L4 advisory producer-emitter (preserves no-platform-wide-expansion guard); Matrix Script operator-driven Phase B authoring / `target_language` widening / canonical-axes widening / `source_script_ref` scheme-set re-widening / repurposing as body-input or URL-ingestion or dereferenced content address (preserves Matrix Script frozen truth); Hot Follow business-behavior reopen / Hot Follow Delivery Center mutation / Hot Follow advisory rendering / Hot Follow file-size cleanup (preserves Hot Follow baseline; structural debt deferred to Platform Runtime Assembly Wave); Platform Runtime Assembly Phases A–E / Capability Expansion W2.2 / W2.3 / durable persistence / runtime API / third production line commissioning (preserves the Platform-Runtime-Assembly-then-Capability-Expansion sequence); provider/model/vendor/engine controls / donor namespace import / React-Vite full frontend rebuild / discovery-only surface promotion to operator-eligible

## Merge Gates

- business regression is mandatory
- verification baseline is mandatory
- relevant PRs must cite `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` and appendices
- scope boundary must be stated
- progress log / execution docs must be updated when stage semantics change

## Structural Risk Reminders

- do not let `tasks.py` regrow
- do not let bridge / compatibility files become new God files
- do not reintroduce router-to-router coupling
- do not let presentation drift away from artifact truth
- do not let skills or workers become hidden truth writers

## Cross-Cutting Cognition Map

Default project orientation entry: `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`. Read after the root indexes and the docs indexes, before drilling into per-bucket authority, to confirm wave / line / surface position and the frozen next engineering sequence. Authority of creation: `docs/reviews/apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md`.
