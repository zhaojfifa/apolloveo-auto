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

## Operator-Visible Surfaces Phase 3B — UI / Presenter Minimal Wiring

Date: 2026-05-01

This node wired the Phase 3A projection module into live presenter / API
/ template surfaces for Board, Workbench, Delivery, and the Hot Follow
panel. Strictly additive: no truth moved, no packet mutation, no IA
redesign, no B-roll wiring.

Files added:

- `gateway/app/services/operator_visible_surfaces/wiring.py` —
  presenter-side adapter mapping existing task / authoritative-state
  shapes onto the projection module's inputs
- `tests/contracts/operator_visible_surfaces/test_wiring.py` —
  11 wiring-layer cases (board row, workbench bundle, publish-hub bundle,
  packet-envelope fallback, vendor-key sanitisation)

Files modified:

- `gateway/app/services/operator_visible_surfaces/__init__.py` —
  re-exports the wiring helpers
- `gateway/app/services/task_router_presenters.py` — adds `publishable`,
  `head_reason`, and `board_bucket` to each Board row, and attaches
  `operator_surfaces` to `task_json` for Workbench
- `gateway/app/services/task_view_presenters.py` — attaches
  `operator_surfaces` to the Hot Follow publish-hub payload
- `gateway/app/templates/tasks.html` — Board bucket legend (All /
  Blocked / Ready / Publishable), per-row bucket badge + head-reason
  chip, bucket filter wired into existing `applyFilters()` JS
- `gateway/app/templates/task_workbench.html` — operator surface strip
  (L3 publish-gate, board bucket, line-panel kind), additive
  line-specific panel mount slot, Hot Follow right-rail panel mount
  (subtitle authority / source / dub-compose legality / helper)
- `gateway/app/templates/task_publish_hub.html` — publish-gate strip
  with publish-status mirror (status / channel / link / last_published_at)
  and a `renderOperatorSurfaces(data.operator_surfaces || {})` consumer
- `gateway/app/services/tests/test_task_router_presenters.py` —
  augments existing `test_build_tasks_page_rows_preserves_board_payload_shape`
  to assert the additive Board projection keys, plus two new presenter
  cases for Board projection and Workbench `operator_surfaces`

What is now live (operator surfaces consume Phase 3A projections):

- **Board** — `publishable` boolean + `head_reason` chip + `board_bucket`
  enum land on every Board row; UI gains a Blocked / Ready / Publishable
  filter; bucket and head-reason badges render per row.
- **Workbench** — `task_json.operator_surfaces` carries the full
  `project_operator_surfaces(...)` shape; template renders the L3
  publish-gate strip, the line-specific panel mount slot (driven only by
  `line_specific_refs[]`), and the Hot Follow right-rail panel when
  `panel_kind == "hot_follow"`.
- **Delivery** — publish-hub payload carries
  `operator_surfaces.delivery.{publish_gate, publish_gate_head_reason,
  publish_status_mirror}` plus the same line-specific panel resolver
  shape; template renders the single derived publish-gate and the
  read-only publish-status mirror; existing Final / Required / Optional
  zoning continues to come from the existing deliverables contract.
- **Hot Follow panel** — explained-only right-rail surface mounted via
  the same Workbench resolver when a `hot_follow_subtitle_authority` /
  `hot_follow_dub_compose_legality` ref is present on the packet; never
  authors truth.

Tests:

- `python3.11 -m pytest tests/contracts/operator_visible_surfaces/ -q`
  → **39 passed** (28 Phase 3A + 11 Phase 3B wiring cases)
- `python3.11 -m pytest tests/contracts/ -q` → **169 passed**
  (no regression vs Phase 3A's 158)
- `python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py -q`
  → **all green** (existing presenter regression preserved; +2 new cases)

Red lines preserved:

- no provider / model / vendor / engine / raw_provider_route in any
  operator-visible payload — projection's `sanitize_operator_payload`
  remains the boundary; wiring layer adds no new keys
- no UI-authored truth — Workbench mount slot is empty when no known
  `line_specific_refs[]` ref is present; templates render projection
  output only
- no packet truth mutation — wiring helper takes Mappings and returns
  new dicts; never mutates inputs
- no publish-status written onto packet envelope — Delivery mirror is
  derived from task-side closure (currently passed as `None` since the
  closure is not materialised on the live Hot Follow task surface yet;
  mirror returns the empty `not_published` shape and remains read-only)
- no recomputation of gate / current-attempt truth in UI — templates
  display projection output only
- optional items never block publish — gate excludes them by
  construction, asserted by `test_publish_hub_bundle_optional_items_never_block_gate`
- no B-roll wiring — no B-roll surfaces, no B-roll Action Area, no
  B-roll filter API in this wave
- no new page tree, no Matrix Script / Digital Anchor / Hot Follow
  truth redesign, no W2.2 / W2.3 / third production line expansion

What remains blocked:

- B-roll Action Area + B-roll filter API — still gated on product
  freeze of the seven open questions
- Platform Runtime Assembly — explicitly not started per directive
- Wiring of the live `publish_feedback_closure` into the Delivery
  mirror — pass-through path is in place but the closure is not yet
  surfaced on the Hot Follow task; the mirror returns the empty
  `not_published` shape until that materialisation lands
- Live mounting of Matrix Script / Digital Anchor line-specific panels
  via real packets — mount resolver works; production tasks do not
  carry packets today, so `panel_kind=None` is the natural empty result

Evidence: `docs/execution/evidence/operator_visible_surfaces_phase_3b_ui_presenter_wiring_v1.md`

## B-roll / Asset Supply Product Freeze

Date: 2026-05-01

This node completed the product-freeze pass for the B-roll / Asset Supply
surface. No B-roll wiring, UI implementation, runtime truth, packet/schema
change, or Platform Runtime Assembly work was started.

Files read:

- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/design/broll_asset_supply_lowfi_v1.md`
- `docs/reviews/architect_phase2_lowfi_review_v1.md`
- `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

Files created:

- `docs/product/broll_asset_supply_freeze_v1.md`
- `docs/execution/evidence/broll_asset_supply_product_freeze_v1.md`

Files updated:

- `docs/design/broll_asset_supply_lowfi_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

Frozen product decisions:

- Filter taxonomy keeps all eight first-class facets for first B-roll
  wiring: `line`, `topic`, `style`, `language`, `role_id`, `scene`,
  `variation_axis`, `quality_threshold`; all except `quality_threshold`
  allow multi-select.
- Promote semantics are async review-gated create-new-asset intent. The
  operator receives request status, not immediate reusable asset truth.
- Mandatory license/source/reuse fields and the `source`, `license`, and
  `reuse_policy` enums are frozen.
- Canonical/reusable marking is admin-only state with operator-visible
  read-only badges. Canonical is not equal to reusable.
- Detail actions `archive`, `deprecate`, `supersede`, `unlink`, and
  `replace_preview` move to the admin management control page and are not
  operator-visible B-roll actions.
- Artifact-to-asset hand-off is explicit promote intent only; Asset Library
  creation happens after review and never mutates the source artifact.
- Reference-into-task pre-population mapping is frozen for `role_ref`,
  `reference_video`, `template`, `variation_axis`, `background`, `broll`,
  `product_shot`, `scene_pack_ref`, and `audio_ref`.

Deferred:

- facet value administration UI
- bulk asset import
- bulk promote
- asset versioning as the primary promote path
- operator-side archive/deprecate/supersede/unlink/replace-preview
- provider/tool/runtime metadata on the asset surface

Result:

- B-roll wiring may open next after review acceptance of the freeze, but only
  under a fresh commissioning instruction and only as projection/intent
  consumption. No UI truth ownership, packet/schema redesign, Platform
  Runtime Assembly, W2.2/W2.3, or provider/model/vendor surface exposure is
  unlocked by this product-freeze step.

## New Tasks Card-Based Line Entry Rollback

Date: 2026-05-01

This node rolled back `/tasks/newtasks` from the semi-workbench intake form
to a card-based line selection page, then aligned the active `/tasks` Board
taxonomy with the same line vocabulary. Scope was limited to Board taxonomy
and New Tasks entry consistency.

Files changed:

- `gateway/app/services/task_semantics.py`
- `gateway/app/templates/tasks.html`
- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`
- `docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

What changed:

- `/tasks/newtasks` is card-based selection only again.
- New Tasks renders four entries: 热点跟拍 (`hot_follow`), 矩阵脚本
  (`matrix_script`), 数字人IP (`digital_anchor`), 基础剪辑 (`baseline`).
- Workbench-like inline fields, target-language controls, helper translation
  textarea, envelope counters, and `generic_refs` / `line_specific_refs`
  display were removed from New Tasks.
- `/tasks` line tabs and task-card labels now use the same active taxonomy:
  全部场景 / 热点跟拍 / 矩阵脚本 / 数字人IP / 基础剪辑.
- `/tasks` continues to link its top-right new-task action to
  `/tasks/newtasks`.
- `/tasks/new`, `/tasks/avatar/new`, `/tasks/hot/new`, and
  `/tasks/baseline/new` remain compatibility / next-step paths and do not
  define the primary operator-visible taxonomy.

Tests:

- `python3.11 -m pytest gateway/app/services/tests/test_new_tasks_surface.py -q`
  → **3 passed**

Red lines preserved:

- Board change limited to line taxonomy/filter labels
- no Workbench change
- no Delivery change
- no Hot Follow panel change
- no B-roll change
- no provider/model/vendor controls
- no packet/schema change

## New Tasks Strict Card Link Correction

Date: 2026-05-01

This node corrected the active `/tasks/newtasks` page only. It restored the
original New Tasks card visual/layout baseline and fixed the primary card links
so no visible card routes into disabled legacy scene paths.

Files changed:

- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`
- `docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

What changed:

- `/tasks/newtasks` again uses the original `wizard-wrap` / `wizard-card` /
  `icon-box` visual structure, original title spacing, original card border /
  radius / shadow weight, original CTA rhythm, and original bottom guidance
  section style.
- New Tasks remains card-grid selection only and does not contain inline forms,
  target-language inputs, helper translation textareas, envelope counters, or
  generic/line-specific ref displays.
- Visible cards are 数字人IP (`digital_anchor`), 热点跟拍 (`hot_follow`),
  矩阵脚本 (`matrix_script`), and 基础剪辑 (`baseline`).
- Card targets are now:
  - 数字人IP -> `/tasks/new?line=digital_anchor`
  - 热点跟拍 -> `/tasks/new?line=hot_follow`
  - 矩阵脚本 -> `/tasks/new?line=matrix_script`
  - 基础剪辑 -> `/tasks/new?line=baseline`
- `/tasks/avatar/new`, `/tasks/apollo-avatar/new`, `/tasks/hot/new`, and
  `/tasks/baseline/new` are not used as primary New Tasks card targets.

Tests:

- `python3.11 -m pytest gateway/app/services/tests/test_new_tasks_surface.py gateway/app/services/tests/test_task_router_presenters.py -q`
  -> **35 passed**

Red lines preserved:

- no Board redesign
- no Workbench change
- no Delivery change
- no Hot Follow panel change
- no B-roll change
- no provider/model/vendor controls
- no packet/schema/runtime change
- no language logic change
- no Platform Runtime Assembly
- no language-system redesign; target-language behavior remains limited to
  the existing Burmese / Vietnamese scope

Evidence: `docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md`

## Surface Connect-First Routing

Date: 2026-05-01

This node ran the narrow connect-first wave. Hot Follow was attached to its
formal route chain, while Matrix Script and Digital Anchor received explicit
temporary connected paths so the operator-visible flow is reachable without
using disabled legacy routes or debug panels.

Supersession note (2026-05-02): Matrix Script has since been promoted to the
formal create-entry route `/tasks/matrix-script/new`; only Digital Anchor
remains on the temporary connected create path. See
`docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md`.

Files changed:

- `gateway/app/routers/tasks.py`
- `gateway/app/templates/tasks_connected_placeholder.html`
- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`
- `docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

Final New Tasks card targets:

- 数字人IP (`digital_anchor`) -> `/tasks/connect/digital_anchor/new`
- 热点跟拍 (`hot_follow`) -> `/tasks/hot/new`
- 矩阵脚本 (`matrix_script`) -> `/tasks/connect/matrix_script/new`
- 基础剪辑 (`baseline`) -> `/tasks/baseline/new`

Formal vs temporary:

- `hot_follow`: formal chain `/tasks/hot/new?ui_locale=zh` ->
  `/tasks/{task_id}` (`hot_follow_workbench.html`) ->
  `/tasks/{task_id}/publish` (`hot_follow_publish.html`)
- `matrix_script`: temporary connected chain
  `/tasks/connect/matrix_script/new?ui_locale=zh` ->
  `/tasks/connect/matrix_script/workbench?ui_locale=zh` ->
  `/tasks/connect/matrix_script/publish?ui_locale=zh`
- `digital_anchor`: temporary connected chain
  `/tasks/connect/digital_anchor/new?ui_locale=zh` ->
  `/tasks/connect/digital_anchor/workbench?ui_locale=zh` ->
  `/tasks/connect/digital_anchor/publish?ui_locale=zh`
- `baseline`: compatibility chain via `/tasks/baseline/new?ui_locale=zh`

Placeholder rules:

- temporary pages visibly say "当前接通版本"
- temporary pages identify the line id and page role
- temporary pages do not claim final production-line capability
- temporary pages do not introduce task truth or deliverable truth

Tests:

- `python3.11 -m pytest gateway/app/services/tests/test_new_tasks_surface.py gateway/app/services/tests/test_task_router_presenters.py -q`
  -> **38 passed**

Red lines preserved:

- no New Tasks layout redesign
- no Board redesign
- no Workbench architecture redesign
- no Delivery redesign
- no B-roll work
- no packet/schema/runtime truth change
- no provider/model/vendor/engine exposure
- no language logic change
- no Platform Runtime Assembly

Evidence: `docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md`
