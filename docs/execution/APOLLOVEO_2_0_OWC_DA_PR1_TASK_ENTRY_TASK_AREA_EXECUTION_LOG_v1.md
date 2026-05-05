# ApolloVeo 2.0 · OWC-DA PR-1 — Digital Anchor Task Entry + Task Area Convergence — Execution Log v1

Date: 2026-05-05
Status: Engineering complete on branch `claude/agitated-lederberg-6be462`; PR opening pending.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC), Phase OWC-DA.
Phase Gate: [docs/reviews/owc_da_gate_spec_v1.md](../reviews/owc_da_gate_spec_v1.md) (architect Raobin + reviewer Alisa signed; coordinator Jackie + product manager standby per §10).
Predecessors: OWC authority/gate normalization PR (#121, squash commit `27aa950`); OWC-MS PR-1/2/3 + Closeout (all merged 2026-05-04 / 2026-05-05); Operator Capability Recovery PR-1..PR-4 (all merged 2026-05-04).

## 1. Scope

OWC-DA PR-1 is the first of three implementation PRs in the Operator Workflow Convergence Wave for Digital Anchor. It lands the OWC-DA gate spec §3 Task Area scope:

- **DA-W1 — Task entry workspace convergence**. The Tasks-Newtasks card → formal `/tasks/digital-anchor/new` entry chain was already shipped by Operator Capability Recovery PR-4 (merged 2026-05-04). PR-1 owns the post-create card body on `gateway/app/templates/tasks.html`: an operator-language eight-field card per `docs/product/digital_anchor_product_flow_v1.md` §5.2 — 任务标题 / Role Profile / Scene Template / Target Language / 当前版本状态 / 当前阻塞项 / 交付包状态 / 最近更新.
- **DA-W2 — Task Area eight-stage projection**. Read-only derivation from `roles[]` / `segments[]` skeleton state + L1 step status + L3 current attempt + closure events into the eight Digital Anchor stages per `digital_anchor_product_flow` §5.1: 输入已提交 / 内容结构已生成 / 场景计划已生成 / 角色 / 声音已绑定 / 多语言版本生成中 / 合成完成 / 可交付 / 已归档.

Out of scope (carried by OWC-DA PR-2 / PR-3 + later phases):
- Workbench five-panel convergence (DA-W3 / DA-W4 / DA-W5 / DA-W6 / DA-W7) — OWC-DA PR-2.
- Delivery Pack assembly view (DA-W8) + 发布回填 closure rendering (DA-W9) — OWC-DA PR-3.
- Asset Supply select-side bindings — OWC-DA PR-2 (consume only the existing PR-2 read-only browse).
- Hot Follow modifications — out of all OWC scope (Hot Follow baseline byte-isolated).
- Matrix Script modifications — out of all OWC-DA scope (OWC-MS landing byte-isolated).
- Plan A live-trial reopen — OWC-DA does NOT open trial (gate spec §11).

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md` (with §13 Product-Flow Module Presence)
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 OWC wave authority
- `docs/reviews/owc_da_gate_spec_v1.md` §3 (DA-W1 + DA-W2 binding scope) / §4 (forbidden scope) / §5 (PR slicing + per-PR file isolation) / §7 (preserved freezes) / §10 (signoff state — architect + reviewer SIGNED, coordinator + PM STANDBY)
- `docs/reviews/owc_ms_gate_spec_v1.md` (read-only — predecessor pattern reference; NOT touched by this PR)
- `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md` (predecessor docs PR pattern)

### 2.3 Line-specific execution authority (binding)
- `docs/product/digital_anchor_product_flow_v1.md` §5.1 (任务阶段) / §5.2 (任务卡片核心字段) / §5.3 (任务区与资产区边界 — informational)

### 2.4 Factory-wide / surface authority (read-only)
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/handoffs/apolloveo_2_0_design_handoff_v1.md`

### 2.5 Existing code surfaces consumed
- `gateway/app/services/digital_anchor/closure_binding.py` (Recovery PR-4 — read-only via `get_closure_view_for_task`; the wrapper NEVER calls `get_or_create_for_task` on the Task Area path so the in-process closure store is not lazily mutated)
- `gateway/app/services/digital_anchor/publish_feedback_closure.py` (Phase D.0/D.1 closure shape — read-only consumer; the closed `feedback_closure_records[].record_kind == "archive_action"` enum is the only closure-side trigger used for stage derivation)
- `gateway/app/services/digital_anchor/create_entry.py` (Recovery PR-4 — `config.entry` shape + closed entry-field set; consumed read-only)
- `gateway/app/services/operator_visible_surfaces/projections.py::derive_board_publishable` (existing wiring; `board_bucket` is the unified `publish_readiness` producer surface consumed by 当前版本状态 per PR-1 reminder #1)
- `gateway/app/services/task_router_presenters.py::build_tasks_page_rows` (cross-cutting wiring seam; new digital_anchor branch added strictly parallel to the matrix_script branch)
- `gateway/app/templates/tasks.html` (digital-anchor-gated `{% elif line_id == "digital_anchor" and da_owc.is_digital_anchor %}` block)
- `gateway/app/services/matrix_script/task_area_convergence.py` (read-only — pattern reference for the helper API + Task Area discipline; NOT modified)

### 2.6 Conflicts found
- None. The PR-4 Digital Anchor row already carries `kind == "digital_anchor"` plus the seeded `line_specific_refs[]` skeletons, `config.entry` populated by the closed eleven-field create-entry payload, and `next_surfaces` workbench / delivery hrefs. The `board_bucket` field is set on every row by `build_board_row_projection` regardless of line. The new branch reads only those existing fields and the read-only closure view.

## 3. Files Changed

### New files
- `gateway/app/services/digital_anchor/task_area_convergence.py` — projection module exposing `derive_digital_anchor_eight_stage_state(row, *, closure=None)`, `derive_digital_anchor_card_summary(row, *, closure=None)`, and `derive_digital_anchor_card_summary_for_task(row)`. Read-only over row + closure view; no mutation; no contract / packet / schema change. Implements the eight stages and the eight card fields against the existing four-layer state and Phase D.0/D.1 closure shape. Closes the user-mandated PR-1 reminders verbatim:
  - **Reminder #1** — 当前版本状态 derives from `row["board_bucket"]` only (the unified `publish_readiness` producer's surface).
  - **Reminder #2** — 交付包状态 stays tracked-gap with the closed `DELIVERY_PACK_STATE_GATED_BY_DA_W8` sentinel + Chinese tooltip naming DA-W8 as the future fine-grained source.
  - **Reminder #3** — eight-stage projection degrades gracefully when `closure is None` and uses only observable signals (`board_bucket` / `final.exists` / `compose_status` / `roles[]` / `segments[]` / `scene_binding_hint` / `feedback_closure_records[].record_kind == "archive_action"`); no late-stage truth invented.
- `gateway/app/services/tests/test_digital_anchor_task_area_convergence.py` — 42 import-light test cases (≥25 floor per gate spec §5.2) covering: (i) EIGHT_STAGES authority parity with product-flow §5.1 labels; (ii) eight stage projections (one per stage incl. archived precedence over deliverable, archive-via-closure-record path, in_progress / queued compose status synonyms, scene+roles vs roles-only ordering, role+segments → role_voice_bound); (iii) `stage_index` ordering invariant; (iv) non-digital_anchor row isolation for the eight-stage projection (hot_follow + matrix_script + missing-kind cases); (v) graceful closure=None degradation invariant (reminder #3 verbatim); (vi) eight-field card label invariants (Chinese labels per §5.2 + English Role Profile / Scene Template / Target Language per source authority); (vii) field value derivations (title, role_profile_ref, scene_binding_hint, target_language, head_reason translation, raw fall-through for unknown codes, last_update_at preference order); (viii) 当前版本状态 board_bucket-only derivation (reminder #1 verbatim) including unknown-bucket clamp to `ready`; (ix) 交付包状态 tracked-gap discipline (reminder #2 verbatim) including DA-W8 sentinel + tooltip; (x) action affordance hrefs from `next_surfaces` + `/tasks/{task_id}` fallback; (xi) cross-line isolation (helper returns `{}` for hot_follow / matrix_script / missing-kind rows); (xii) sanitization (no vendor / model_id / provider / engine / swiftcraft tokens in keys or repr); (xiii) line-id alias-aware case-insensitive recognition; (xiv) wrapper closure read discipline (no lazy create on in-process store); (xv) wrapper picks up existing closure archive record via the read path; (xvi) anti-mutation invariants on row + closure inputs.
- `docs/execution/APOLLOVEO_2_0_OWC_DA_PR1_TASK_ENTRY_TASK_AREA_EXECUTION_LOG_v1.md` — this file.

### Modified files
- `gateway/app/services/task_router_presenters.py` — added one import block (`from gateway.app.services.digital_anchor.task_area_convergence import derive_digital_anchor_card_summary_for_task`) and one new `if kind_value == "digital_anchor":` branch inside `build_tasks_page_rows` strictly parallel to the existing `matrix_script` branch. The branch attaches the additional row keys (`kind`, `line_specific_refs`, `config`, `packet`, `updated_at`, `last_generated_at`, `archived`, `final`) needed by the projection plus the `digital_anchor_task_area_convergence` projection key. Hot Follow / Matrix Script / baseline branches unchanged.
- `gateway/app/templates/tasks.html` — extended the existing per-card switch with one new `{% elif line_id == "digital_anchor" and da_owc.is_digital_anchor %}` block strictly between the existing matrix_script branch and the existing `{% else %}` fallback. The block renders: (i) the eight-field operator-language card body with `data-role="da-*"` anchors (8 fields × distinct anchor); (ii) the eight-stage badge with `data-role="da-eight-stage"`; (iii) operator action affordances `进入工作台` / `跳交付中心` (`data-role="da-action-workbench"` / `da-action-delivery"`) + delete action; (iv) per-row Jinja extraction `{% set da_owc = it.digital_anchor_task_area_convergence or {} %}` + `{% set da_eight_stage = da_owc.eight_stage or {} %}`. The `{% else %}` baseline fallback (Hot Follow + baseline rows) is bytewise unchanged.

### NOT modified (preserved freezes per gate spec §7)
- Hot Follow source files (any path containing `hot_follow`).
- Matrix Script source files (any path under `gateway/app/services/matrix_script/` and any matrix-script template branch).
- Asset Supply files (`gateway/app/services/asset/*`) — read-only consumption is OWC-DA PR-2 scope.
- Any contract under `docs/contracts/`.
- Any sample under `schemas/`.
- Any worker / runtime / capability-adapter file.
- Workbench template (`task_workbench.html`) — out of scope for PR-1 (DA-W3..W7 land in OWC-DA PR-2).
- Publish hub template (`task_publish_hub.html`) — out of scope for PR-1 (DA-W8 + DA-W9 land in OWC-DA PR-3).
- `gateway/app/services/digital_anchor/closure_binding.py` — closure binding preserved (read-only consumer added).
- `gateway/app/services/digital_anchor/publish_feedback_closure.py` — closure shape preserved.
- `gateway/app/services/digital_anchor/create_entry.py` — create-entry payload preserved.
- `gateway/app/services/digital_anchor/workbench_role_speaker_surface.py` — workbench surface preserved (DA-W3 surface).
- `gateway/app/services/digital_anchor/delivery_binding.py` — delivery projection preserved (DA-W8 surface).
- OWC-MS landing surfaces (`task_area_convergence.py`, `task_card_summary.py`, etc.) — Matrix Script byte-stable.
- Plan A trial readiness documents — not touched.
- Plan E phase closeout signoff blocks (A7 / UA7 / RA7) — independently pending; this PR does NOT advance them.
- OWC-MS Closeout signoff block (MS-A7) — independently pending; this PR does NOT advance it.

## 4. Why scope is minimal and isolated

OWC-DA gate spec §5.1 (per-PR file isolation contract) requires:

- Service files: only `gateway/app/services/digital_anchor/*` and the cross-cutting wiring seam files. ✅ Only `task_area_convergence.py` (new) under `digital_anchor/` + `task_router_presenters.py` (the named cross-cutting wiring seam) touched.
- Templates: only the new `_da_kind == "digital_anchor"` block in `tasks.html`. ✅ The `tasks.html` change is one new `{% elif %}` block plus four new `{% set %}` extractions; the existing matrix_script branch and the existing `{% else %}` fallback are bytewise unchanged.
- Tests: each new service module gets a dedicated import-light test file under `gateway/app/services/tests/`. ✅ `test_digital_anchor_task_area_convergence.py` is the dedicated module (42 cases).
- Hot Follow files: byte-stable. ✅ Verified by `git diff --stat`.
- Matrix Script files: byte-stable. ✅ Verified by `git diff --stat`.
- Asset Supply files: read-only consumption only. ✅ No Asset Supply file imported or referenced.

The presenter branch is strictly parallel to the existing matrix_script branch (no shared state, no cross-line consolidation). The template branch is strictly parallel to the existing matrix_script `{% if %}` block (no shared markup expansion). The helper module imports only from within `digital_anchor/` and uses standard library / typing only — no donor namespace, no provider client, no FastAPI types in the projection layer.

## 5. Tests Run

Local Python 3.9.6 (`python3 -V` → `Python 3.9.6`):

| Suite | Command | Result |
| --- | --- | --- |
| OWC-DA PR-1 dedicated | `python3 -m pytest gateway/app/services/tests/test_digital_anchor_task_area_convergence.py -v` | **42/42 PASS** |
| Digital Anchor adjacent (create_entry / closure_binding / workspace_wiring / surface_boundary) | `python3 -m pytest gateway/app/services/tests/test_digital_anchor_create_entry.py gateway/app/services/tests/test_digital_anchor_closure_binding.py gateway/app/services/tests/test_digital_anchor_workspace_wiring.py gateway/app/services/tests/test_digital_anchor_surface_boundary.py` | All PASS (no regression) |
| Matrix Script Task Area + Task Card Summary | `python3 -m pytest gateway/app/services/tests/test_matrix_script_task_area_convergence.py gateway/app/services/tests/test_matrix_script_task_card_summary.py` | All PASS (no regression) |
| Aggregate import-light DA + MS Task Area set | (combined invocation of the four DA + two MS suites above) | **164/164 PASS** |
| Cross-line + Plan E + closure HTTP wiring set (16 files) | `python3 -m pytest test_matrix_script_b4_artifact_lookup test_matrix_script_closure_api test_matrix_script_closure_binding test_matrix_script_closure_publish_hub_wiring test_matrix_script_closure_surface_boundary test_matrix_script_delivery_backfill_view test_matrix_script_delivery_comprehension test_matrix_script_delivery_copy_bundle_view test_matrix_script_delivery_zoning test_matrix_script_workbench_template_intact test_matrix_script_publish_hub_pr3_wiring test_matrix_script_workbench_pr2_wiring test_digital_anchor_closure_api test_digital_anchor_new_task_route_shape test_publish_readiness_unified_producer test_publish_readiness_surface_alignment` | **253 PASS / 23 SKIP / 0 FAIL** (skips are HTTP cases auto-skipping when FastAPI TestClient is unavailable on the local env) |

### 5.1 Environment limitation note (per ENGINEERING_RULES.md §10)

`gateway/app/services/tests/test_new_tasks_surface.py` and `gateway/app/services/tests/test_task_router_presenters.py` block at collection on local Python 3.9 due to a pre-existing PEP-604 `str | None` syntax in `gateway/app/config.py:43` that requires Python 3.10+. Verified pre-existing on `origin/main` at `6825005` via `git stash --include-untracked` + re-run + `git stash pop`. This is an environment limitation, **not** a code regression caused by PR-1 (mirrors the documented environment limitation noted in CURRENT_ENGINEERING_FOCUS.md for Plan E PR-1 / PR-2 / PR-3 + OWC-MS PR-1 / PR-2 / PR-3). CI on Python 3.10+ runs these suites against the new helper without modification.

## 6. Hard-Discipline Audit

| Discipline (gate spec §4 / user PR-1 reminders) | Audit |
| --- | --- |
| §4.1 No Digital Anchor packet truth mutation | ✅ Helper is read-only over packet view; no write path; tests assert anti-mutation invariant on row + closure inputs |
| §4.1 No `roles[]` / `segments[]` operator authoring | ✅ Helper reads `_has_authored_roles` / `_has_authored_segments` as boolean checks only; no enumeration writes; no operator-authoring affordance in template |
| §4.1 No closed-enum widening on `task_entry_contract_v1` or D.1 `event_kind` set | ✅ No contract file edited; the additive `review_zone` enum on D.1 closure event payload is OWC-DA PR-2 / DA-W7 scope and is NOT introduced here |
| §4.1 No reopening of PR-4 reviewer-fail correction items | ✅ `closure_binding.py` / `create_entry.py` / `delivery_binding.py` byte-stable |
| §4.1 No new authoritative truth source for publishability | ✅ 当前版本状态 reads `row["board_bucket"]` only — the unified `publish_readiness` producer's surface (PR-1 reminder #1 verbatim) |
| §4.2 No Hot Follow file touched | ✅ `git diff --stat` confirms zero `hot_follow*` paths in the change set |
| §4.2 No Matrix Script file touched | ✅ `git diff --stat` confirms zero `matrix_script` paths in the change set |
| §4.2 No cross-cutting wiring change outside per-line gates | ✅ The presenter change is gated inside `if kind_value == "digital_anchor":`; the template change is gated inside `{% elif line_id == "digital_anchor" and da_owc.is_digital_anchor %}` |
| §4.3 No Platform Runtime Assembly Phases A–E | ✅ No platform-wide / runtime-assembly file touched |
| §4.3 No Capability Expansion W2.2 / W2.3 / durable persistence / runtime API / third production line | ✅ No expansion-gated module touched |
| §4.3 No Plan A live-trial reopen | ✅ No trial doc touched; PR-5 NOT-READY remains in force |
| §4.3 No new operator-eligible discovery surface promotion | ✅ The card body activates an already-shipped formal route (PR-4); no discovery-only surface promoted |
| §4.4 No avatar platform / role catalog / scene catalog UI | ✅ No catalog UI introduced; Role Profile / Scene Template fields render the existing `config.entry.role_profile_ref` / `scene_binding_hint` operator hints only |
| §4.4 No provider / model / vendor / engine controls | ✅ Sanitization assertion `test_card_emits_no_provider_or_swiftcraft_identifier_in_value_repr` enforces the absence of `vendor_id` / `model_id` / `provider_id` / `engine_id` / `swiftcraft` tokens in the helper output |
| §4.4 No donor namespace import | ✅ `grep -n "from swiftcraft" gateway/app/services/digital_anchor/task_area_convergence.py` → empty |
| §4.4 No DAM / admin UI | ✅ No admin-side surface introduced |
| §4.4 No React / Vite full rebuild or new component framework / new build dependency | ✅ Pure Jinja additions; no new JS framework; no new build dependency |
| §4.4 No durable persistence | ✅ Helper reads from in-process closure binding only (PR-4 in-process store unchanged) |
| §4.4 No bundling of DA-W* slices into a single PR | ✅ Only DA-W1 + DA-W2 land here per gate spec §5 PR slicing |
| §4.5 No closeout-signoff coupling | ✅ This PR does not advance any prior closeout signoff (Plan E A7 / UA7 / RA7 / OWC-MS Closeout MS-A7 all remain independently pending in Raobin / Alisa / Jackie / PM queue) |
| Reminder #1 — 当前版本状态 reads board_bucket only | ✅ `_current_version_state` reads `row["board_bucket"]` exclusively; test `test_card_current_version_state_derives_from_board_bucket_only` enforces the closed mapping over all three buckets |
| Reminder #2 — 交付包状态 coarse / tracked-gap | ✅ `delivery_pack_state_value: None` + `delivery_pack_state_gated_by: DELIVERY_PACK_STATE_GATED_BY_DA_W8` + tooltip naming DA-W8; test `test_card_delivery_pack_state_is_tracked_gap_with_da_w8_sentinel` enforces |
| Reminder #3 — eight-stage degrades gracefully when closure is None | ✅ Test `test_stage_handles_closure_none_gracefully_without_invented_truth` enforces; only `archive_action` closure record drives a late stage when closure is present |

## 7. Acceptance Evidence Mapping (gate spec §6)

| Row | Check | Status (this PR) |
| --- | --- | --- |
| DA-A1 | OWC-DA PR-1 (DA-W1 + DA-W2) implementation green and merged | engineering green; merge pending PR open + review |
| DA-A2 | OWC-DA PR-2 (DA-W3..W7) implementation green and merged | NOT YET STARTED (per gate spec §5 ordering) |
| DA-A3 | OWC-DA PR-3 (DA-W8 + DA-W9) implementation green and merged | NOT YET STARTED (per gate spec §5 ordering) |
| DA-A4 | Hot Follow baseline preserved (golden-path live regression) | preserved by file isolation in this PR; coordinator confirmation block lands at OWC-DA Closeout |
| DA-A5 | Matrix Script preservation per PR (OWC-MS landing + §8.A–§8.H truth byte-stable) | preserved by file isolation in this PR (`git diff --stat` confirms zero matrix_script paths touched) |
| DA-A6 | §4 forbidden-scope audit (full pass on §4.1–§4.5) | §6 audit table above shows ✅ on every sub-section for this PR's surface |
| DA-A7 | OWC-DA Closeout signoff (Architect Raobin + Reviewer Alisa + Coordinator Jackie + Product Manager) | NOT YET STARTED (closeout PR opens after PR-3 merges) |
| DA-A8 | Product-Flow Module Presence rule (ENGINEERING_RULES §13) verified for each DA-W* slice | DA-W1 + DA-W2 modules are operator-visible on `tasks.html` per the new branch; reviewer audit at OWC-DA Closeout |

## 8. Stop Conditions Encountered

None. No required convergence triggered packet / schema / sample / template-truth mutation; no required projection needed second authoritative producer; no Hot Follow / Matrix Script file touch needed; no Asset Supply expansion needed; no avatar platform / role catalog / scene catalog UI needed; no contract authoring outside scope. The eight-stage projection degrades gracefully on every input combination tested.

## 9. PR Slicing Discipline

Per gate spec §5: this PR is **OWC-DA PR-1** (DA-W1 + DA-W2). PR-2 (DA-W3..W7) and PR-3 (DA-W8 + DA-W9) remain to be authored sequentially after PR-1 merges + reviews. No bundling.

## 10. Subsequent Steps (informational only — none authorized by this PR)

1. OWC-DA PR-1 review by architect (Raobin) + reviewer (Alisa) + coordinator (Jackie) per gate spec §9. Apply the five-row review (R1 contract / R2 byte-isolation / R3 forbidden-scope / R4 unified-producer consumption / R5 product-flow module presence).
2. After OWC-DA PR-1 merges to `main`, OWC-DA PR-2 (DA-W3..W7) MAY open per gate spec §5 ordering — but only after explicit user hand-off.
3. After OWC-DA PR-2 + PR-3 merge, OWC-DA Closeout PR aggregates DA-A1..DA-A8.
4. After OWC-DA Closeout signs, the trial re-entry review may be authored to update `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` §0 sample-validity criteria for product-flow module presence (gate spec §11).
5. Plan A live-trial reopen remains BLOCKED until step 4 lands.
6. Platform Runtime Assembly Wave remains BLOCKED gated on Plan A live-trial closeout.
7. Capability Expansion remains BLOCKED gated on Platform Runtime Assembly signoff.

This PR does NOT open trial. This PR does NOT open Platform Runtime Assembly. This PR does NOT open Capability Expansion. This PR does NOT advance any prior closeout signoff.
