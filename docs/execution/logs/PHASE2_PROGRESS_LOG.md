# Phase-2 Progress Log

## Phase-2 Milestone Closure

Date: 2026-04-07

Closure note:

- annotated milestone tag created: `VeoPhase2-Foundation`
- Phase-2 milestone branch `VeoPhase2-SkillsWorker` merged into `main`
- Phase-3 execution/validation branch created: `VeoPhase3-ExecValidation`

Closure boundary:

- no new runtime refactor was started in the closure task
- Phase-2 remains frozen as the foundation baseline for skills, worker gateway, and planning-first structures
- next work moves to execution-path migration and live business validation

## PR-9 Action Replica Planning Asset View MVP

Date: 2026-04-07

This node completed:

- introduced a code-level `action_replica_line` planning asset baseline
- introduced planning asset models for `ReplicaIdentity`, `Wardrobe`, `HandProp`, `RoleBinding`, and `ShotBinding`
- introduced planning-side relationship binding between identity, wardrobe, prop, role, and shot structures
- introduced a small execution-mapping skeleton that converts planning assets into future execution needs without writing truth

Scope boundary:

- planning-first only
- no UI shell or workbench expansion
- no Action Replica execution overhaul
- no provider migration

Intentionally not done:

- did not introduce Action Replica routes or editor UI
- did not bind planning assets into repo truth
- did not move worker/provider execution into Action Replica planning
- did not start generator or publish-path implementation

Verification:

- action replica planning view can build identity / wardrobe / prop / role / shot structures
- candidate and linked asset refs remain dual-state after linking
- usage index stays line-scoped and run-scoped
- execution-need mapping prefers linked refs and keeps planning ownership only
- existing Script Video planning, Hot Follow skills, Worker Gateway, and import smoke remain green

Remaining risks:

- current mapping skeleton is intentionally non-executable and does not submit worker requests
- there is still no Action Replica line runtime binding or editor surface
- planning assets remain in-memory service structures only in this PR

## PR-8 Script Video Planning Layer MVP

Date: 2026-04-07

This node completed:

- introduced a code-level `script_video_line` planning draft baseline
- introduced candidate-vs-linked asset dual-state in executable planning code
- introduced line-scoped planning usage indexing hooks
- introduced a minimal prompt template registry skeleton for planning use

Scope boundary:

- planning-first only
- no studio shell or project/chapter navigation
- no execution truth writes
- no provider migration

Intentionally not done:

- did not introduce planning routes or UI
- did not bind planning drafts into repo truth
- did not start Action Replica execution or asset view work
- did not migrate worker/provider paths

Verification:

- planning registry resolves the default `script_video_line` template family
- planning service builds draft/segment/shot/entity structures
- candidate and linked assets remain dual-state after linking
- planning usage index remains line-scoped and run-scoped
- existing Hot Follow skills/worker/import smoke regressions remain green

Remaining risks:

- current planning service is intentionally deterministic and hint-driven, not a full script extraction pipeline
- prompt template registry is a skeleton, not a broad prompt product system
- route/UI/editor integration is deferred by design

## PR-7 Worker Gateway MVP

Date: 2026-04-07

This node completed:

- introduced explicit Worker Gateway request / result runtime objects
- introduced execution-mode support for `internal`, `external`, and `hybrid`
- added a minimal gateway registry and dispatcher
- routed Hot Follow compose FFmpeg execution through the Worker Gateway internal adapter
- aligned Hot Follow line metadata so `worker_profile_ref` points to the runtime worker contract

Scope boundary:

- kept the change narrow to execution boundary
- preserved repo truth, deliverable truth, publish truth, and status truth outside the gateway
- did not start a broad provider rewrite

Intentionally not done:

- did not migrate every provider-backed path into Worker Gateway
- did not introduce OpenClaw runtime integration
- did not add new business features or UI work
- did not let Worker Gateway perform repo or status writes

Verification:

- Worker Gateway registry dispatch is covered for external/hybrid mode selection
- internal subprocess adapter timeout surface is covered
- compose `_run_ffmpeg(...)` now executes through Worker Gateway in tests
- Hot Follow publish/workbench line binding and import smoke remain green

Remaining risks:

- the only live execution path in this PR is compose FFmpeg internal execution
- external and hybrid modes are real runtime contract types, but broader provider migration is still deferred
- parse / ASR / TTS provider branching remains outside the gateway for now

## PR-6 Hot Follow Skills Runtime MVP

Date: 2026-04-07

This node completed:

- introduced a minimal line-scoped skills runtime loader
- added the first live Hot Follow skills bundle at `skills/hot_follow`
- moved Hot Follow advisory judgment into `input / routing / quality / recovery` stage modules
- updated Hot Follow line metadata so `skills_bundle_ref` points to the real runtime bundle path

Scope boundary:

- kept the runtime narrow to Hot Follow
- preserved current advisory/workbench behavior
- kept all status, deliverable, publish, and sink writes outside skills

Intentionally not done:

- did not implement worker gateway
- did not introduce a generic multi-line plugin platform
- did not move compose or publish truth ownership into skills
- did not start planning-line runtimeization

Verification:

- bundle loader resolves `skills/hot_follow` from live line binding
- existing Hot Follow advisory outputs remain stable in tests
- workbench payload still attaches advisory as read-only secondary guidance
- import smoke and line binding tests remain green

Remaining risks:

- current loader is intentionally minimal and line-scoped; generic multi-line expansion is deferred
- only advisory-oriented strategy logic moved in this PR; broader execution routing stays for PR-7
- top-level engineering focus still needs explicit branch-stage alignment if Phase-2 implementation broadens further

## PR-5 Phase-2 Docs / Contracts / ADR Freeze

Date: 2026-04-07

This node completed:

- froze the Phase-2 Skills Runtime contract baseline
- froze the Phase-2 Worker Gateway runtime contract baseline
- froze the planning-first contracts for `script_video_line` and `action_replica_line`
- froze the Phase-2 ADR and execution runbook
- added a dedicated Phase-2 progress log and updated docs indexes for discoverability

Scope boundary:

- docs-first only
- no runtime code changes
- no Skills Runtime implementation
- no Worker Gateway implementation
- no planning UI shell

Intentionally not done:

- did not start PR-6 skills bundle code
- did not start PR-7 worker gateway code
- did not bind planning contracts into runtime
- did not change Hot Follow business behavior

Verification:

- confirmed all new docs files exist in the expected buckets
- updated docs index / ADR index / execution log index to include Phase-2 materials
- reviewed contract boundaries against existing Phase-1 line/ready-gate/status ownership baseline

Remaining risks:

- top-level engineering focus still reflects the post-VeoSop05 continuation stage and will need explicit alignment before broad Phase-2 implementation lands
- the new contracts are frozen before runtime implementation, so some fields remain hook-only until PR-6/PR-7
- planning contracts intentionally remain non-executable until later PRs

## Packet Gate — Matrix Script + Digital Anchor PM Sample Pass-Through

Date: 2026-04-26

This node completed:

- shipped `gateway/app/services/packet/envelope.py` (PacketValidationReport / Violation / Advisory dataclasses)
- shipped `gateway/app/services/packet/validator.py` implementing E1–E5 envelope structural rules and R1–R5 content rules per `docs/contracts/factory_packet_envelope_contract_v1.md` and `docs/contracts/factory_packet_validator_rules_v1.md`
- registered `matrix_script` and `digital_anchor` in `LINE_IDS` and confirmed all eleven `CAPABILITY_KINDS` cover the new lines (`variation`, `speaker`, `avatar`, `lip_sync` already present — no kind additions required)
- ran `pytest tests/contracts/packet_validator/test_pm_samples.py -v` → **6 passed in 0.14s** on Python 3.9.6 / pytest 8.4.2
- persisted green validator reports to `docs/execution/logs/packet_validator_matrix_script_v1.json` and `docs/execution/logs/packet_validator_digital_anchor_v1.json` (`ok=true`, `violations=[]`, `rule_versions={"rules":"v1","envelope":"v1"}`)
- updated `docs/execution/apolloveo_2_0_evidence_index_v1.md` to point at the new validator/runtime/report evidence and resolved the two corresponding evidence gaps

Scope boundary:

- no donor absorption — `swiftcraft` token is rejected by R3 vendor-leak check, never written
- no provider/vendor implementation — capability adapters / routing untouched
- no Hot Follow business changes — Hot Follow remains the reference line only
- validator is read-only: no L1/L2/L3/L4 state, no mutation of input packet
- minimal-support principle observed: only constants registry (`LINE_IDS`) and the missing implementation modules were added; no schema redesign

Outstanding:

- onboarding gate (`onboarding_gate.py`) consumption of these reports is still pending
- line-specific contracts under `docs/contracts/matrix_script/` and `docs/contracts/digital_anchor/` are referenced by the samples but not yet authored — currently unblocked because R1 only resolves `generic_refs[]`; will become a blocker when E3-derived line-specific path resolution is tightened

## Operator-Visible Surface Wiring Feasibility Memo (Phase 2 Low-fi CONDITIONAL PASS follow-up)

Date: 2026-05-01

This node completed (diagnosis only — no code, no UI wiring, no schema change):

- read the five Phase-2 low-fi design docs (`ApolloVeo_Operator_Visible_Surfaces_v1.md`, `surface_task_area_lowfi_v1.md`, `surface_workbench_lowfi_v1.md`, `surface_delivery_center_lowfi_v1.md`, `panel_hot_follow_subtitle_authority_lowfi_v1.md`) and the Architect CONDITIONAL PASS (`docs/reviews/architect_phase2_lowfi_review_v1.md`)
- inspected current gateway / projector / delivery / workbench / packet code: `ready_gate_runtime.py`, `current_attempt_runtime.py`, `status_policy/hot_follow_state.py`, `task_view_presenters.py`, `task_view_workbench_contract.py`, `matrix_script/delivery_binding.py`, `matrix_script/workbench_variation_surface.py`, `digital_anchor/delivery_binding.py`, `packet/validator.py`, and packet schemas under `schemas/packets/`
- verified the three Engineering Wiring Confirmation items from the review against actual code paths (line-anchored)
- shipped the wiring feasibility memo: `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
- shipped the diagnosis evidence: `docs/execution/evidence/operator_visible_surface_wiring_feasibility_v1.md`
- updated the evidence index: `docs/execution/apolloveo_2_0_evidence_index_v1.md`

Verdict (per memo §1):

- Board `blocked` / `ready` rendering, validator head-reason verbatim chip, Workbench four-panel skeleton + L2 facts strip + L3 `current_attempt` strip + `line_specific_refs[]` mount, Delivery Final / Required / Optional zoning, Hot Follow line panel mount, and operator-payload hygiene → **Ready now** at the backend projection layer
- Board `publishable` bucket boolean, single derived Delivery publish gate, Delivery last-publish-status mirror → **Additive-fixable** as derived projections over existing `ready_gate.*`, `factory_delivery_contract.deliverables[]`, and task-side publish-feedback closure records — no packet truth, no four-layer authority, no truth ownership change
- B-roll wiring → **Out of scope** until product freezes the seven open B-roll questions (`docs/design/broll_asset_supply_lowfi_v1.md`)

Scope boundary (hard stop honored):

- no UI implementation
- no field implementation
- no B-roll wiring
- no packet / line closure / four-layer truth change
- no L4 derived state written back into L2/L3
- design hold preserved; Phase 3 wiring not started

Outstanding (blocking next commissioning step):

- product freeze of the seven B-roll open questions per `docs/reviews/architect_phase2_lowfi_review_v1.md` §"Product Freeze Items"
- next commissioning instruction before any code lands against the Recommended Minimal Wiring Path in §7 of the memo

## Operator-Visible Surfaces Phase 3A — Minimal Wiring

Date: 2026-05-01

This node completed the minimal additive-projection wiring authorized by
the wiring feasibility memo. No truth moved, no packet mutation, no UI
implementation, no B-roll wiring.

Files added:

- `gateway/app/services/operator_visible_surfaces/__init__.py`
- `gateway/app/services/operator_visible_surfaces/projections.py`
- `tests/contracts/operator_visible_surfaces/__init__.py`
- `tests/contracts/operator_visible_surfaces/test_projections.py`

No existing files modified.

Projection-gap closure landed (per memo §5):

- Gap A1 — `derive_board_publishable(ready_gate)` projects per-packet
  `publishable` boolean + `head_reason` from `ready_gate.*` only
- Gap A2 — `derive_delivery_publish_gate(ready_gate, l2_facts)` projects
  a single Delivery `publish_gate` from `ready_gate.publish_ready` /
  `compose_ready` / `blocking[]` + L2 `final.exists` / `final_stale_reason`;
  optional items (scene_pack, pack_zip, edit_bundle_zip, helper /
  attribution exports) are excluded by construction
- Gap A3 — `derive_delivery_publish_status_mirror(closure)` reads only the
  task-side `publish_feedback_closure_v1` (matrix_script aggregate or
  digital_anchor flat) and never returns a packet field

Workbench mount resolver:

- `resolve_line_specific_panel(packet)` + `PANEL_REF_DISPATCH` enum cover
  the six frozen ref_ids (matrix_script_variation_matrix,
  matrix_script_slot_pack, digital_anchor_role_pack,
  digital_anchor_speaker_plan, hot_follow_subtitle_authority,
  hot_follow_dub_compose_legality); ref payloads are sanitized through
  `sanitize_operator_payload(...)` before reaching the operator surface

Combined entry: `project_operator_surfaces(...)` returns the four surface
payloads (Board / Workbench / Delivery / Hot Follow panel) in one call.

Tests:

- `python3 -m pytest tests/contracts/operator_visible_surfaces/ -q` →
  **28 passed in 0.03s**
- `python3 -m pytest tests/contracts/ -q` → **158 passed in 0.29s**
  (no regression)

Red lines verified:

- no provider / model / vendor / engine / raw_provider_route in operator
  payload — `FORBIDDEN_OPERATOR_KEYS` enforced at surface boundary as
  defense-in-depth on top of validator R3
  (`gateway/app/services/packet/validator.py:202`)
- no UI-authored truth — Workbench mount returns `panel_kind=None` when
  no known ref_id is present
- no packet truth mutation — module is read-only
- no publish-status written onto packet envelope — mirror reads task-side
  closure only (`docs/contracts/status_ownership_matrix.md:39`)
- optional items never block publish — asserted by
  `test_optional_items_never_block_publish_gate`
- no B-roll wiring

What remains blocked:

- B-roll Action Area + B-roll filter API — still gated on product freeze
  of the seven open questions
  (`docs/reviews/architect_phase2_lowfi_review_v1.md` §"Product Freeze Items")
- Phase 3B (UI wiring) — not started; consumer wiring of
  `project_operator_surfaces(...)` into live presenter/API response shape
  is deferred until next commissioning instruction
- evidence: `docs/execution/evidence/operator_visible_surfaces_phase_3a_minimal_wiring_v1.md`
