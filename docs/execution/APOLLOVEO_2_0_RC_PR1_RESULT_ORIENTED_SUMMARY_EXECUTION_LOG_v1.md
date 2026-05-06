# RC PR-1 Execution Log — Matrix Script Result-Capability Recovery (RC-R6)

Date: 2026-05-06
Status: Implementation green; PR open. Engineering only — operator-comprehension demonstration (RC-A5) recorded in §6 below.
Wave: ApolloVeo 2.0 Matrix Script Result-Capability Recovery Wave (Track B).
Phase: RC PR-1 — Result-oriented Task Area / Workbench summary projection.
Authority: [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) §3 RC-R6 + §5 RC PR-1.

---

## 1. Reading Declaration

Authority files read before authoring this implementation, in `CLAUDE.md` §2 boot order:

1. `CLAUDE.md` — bootloader.
2. `ENGINEERING_RULES.md` — engineering governance, §13 Product-Flow Module Presence.
3. `CURRENT_ENGINEERING_FOCUS.md` — current-stage preamble (post §10 signoff).
4. `ENGINEERING_STATUS.md` — head completion log.
5. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` §7.
6. `docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md`.
7. `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` (binding scope).
8. `docs/product/matrix_script_product_flow_v1.md`.

Implementation surface mapped via the existing OWC-MS PR-1 helpers (`task_area_convergence.py` — eight-stage state) and OWC-MS PR-2 helpers (`qc_diagnostics_view.py` — `HEAD_REASON_LABELS_ZH` + `_ready_gate_explanation`). No second producer introduced.

---

## 2. RC-R / RC-A Scope Covered

### 2.1 RC-R items in scope (this PR only)

- **RC-R6 — Blocked / next-action state** — every Matrix Script Task Area card and the Matrix Script Workbench summary header now exposes one of three operator-language statements: `ready: do X next`, `blocked: missing Y`, or `completed`. Each statement carries a concrete next-action sentence and an explicit missing-items list.

### 2.2 RC-R items explicitly NOT in scope (per gate spec §5 ordering)

- RC-R1, RC-R2, RC-R3 — readable script / variant candidate package (RC PR-2).
- RC-R4 — recommended-version actionable lane (RC PR-3).
- RC-R5, RC-R7, RC-R8 — delivery-ready package + publish/backfill readiness + no-fake-`final_video` audit (RC PR-4).

### 2.3 Acceptance rows targeted by this PR

- **RC-A1** — RC PR-1 implementation green and merged. Evidence: this execution log + diff + PR # + squash commit (recorded by Closeout when paperwork lands).
- **RC-A5 (this PR's slice)** — operator-comprehension demonstration recorded in §6 below.
- Forbidden-scope audit rows (RC-A6 / RC-A7 / RC-A8 / RC-A9 / RC-A10 / RC-A11 / RC-A12) are aggregated at Closeout; per-PR evidence is recorded in §4 below.

---

## 3. Files Changed

| File | Kind | Purpose |
| --- | --- | --- |
| `gateway/app/services/matrix_script/result_status_view.py` | new | RC-R6 helper: `derive_matrix_script_task_area_result_status` + `derive_matrix_script_workbench_result_summary` + `derive_matrix_script_task_area_result_status_for_task` (closure read-only convenience wrapper). Closed `STATUS_KINDS = {ready, blocked, completed}` enum; per-stage operator-language framing in `STAGE_TO_RESULT`; closed `head_reason → next-action` map in `WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH`. |
| `gateway/app/services/task_router_presenters.py` | edit | New import + one-line call inside the existing `kind_value == "matrix_script"` branch; assigns `row["matrix_script_result_status"]`. No edits outside the matrix_script gate. |
| `gateway/app/services/operator_visible_surfaces/wiring.py` | edit | Inside the existing `panel_kind == "matrix_script"` branch (already gated), adds `bundle["workbench"]["matrix_script_result_summary"]` from `derive_matrix_script_workbench_result_summary(publish_readiness, workbench_panel)`. Consumes the same `publish_readiness` dict already computed for `qc_diagnostics_view`; no second producer. |
| `gateway/app/templates/tasks.html` | edit | Inside the existing `{% if line_id == "matrix_script" %}` block, adds one new `data-role="ms-result-status"` row between the OWC field row and the lanes block. Hot Follow / Digital Anchor / baseline branches byte-stable. |
| `gateway/app/templates/task_workbench.html` | edit | Inside the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` block, sets `ms_result_summary` and adds one new `data-role="ms-comp-result-status"` block at the head of the comprehension panel. |
| `gateway/app/services/tests/test_matrix_script_result_status_view.py` | new | 45 dedicated import-light cases (gate spec §5.2 ≥25 floor: PASS at 1.8×). |
| `docs/execution/APOLLOVEO_2_0_RC_PR1_RESULT_ORIENTED_SUMMARY_EXECUTION_LOG_v1.md` | new | This log. |

---

## 4. Forbidden-Scope Audit (per PR; full audit at Closeout)

| Sub-section | Verdict | Notes |
| --- | --- | --- |
| §4.1 Truth-source / contract preservation | PASS | No new contract. No closed-enum widening. No `source_script_ref` repurposing. No new packet truth. The helper restates `board_bucket` + `head_reason` + the existing eight-stage state; recommended-version reasoning stays in `derive_matrix_script_full_card_summary` / `qc_diagnostics_view`. |
| §4.2 Cross-line preservation | PASS | `git diff --stat` touches only matrix_script-gated branches and one new helper module under `gateway/app/services/matrix_script/`. No `hot_follow*`, no `digital_anchor*`, no `gateway/app/services/asset/`, no `docs/contracts/`, no `schemas/` paths. |
| §4.3 Wave-position preservation | PASS | No Platform Runtime Assembly. No Capability Expansion. No Plan A live-trial reopen. No new operator-eligible discovery surface. |
| §4.4 Scope-boundary preservation | PASS | No new structural surface module (no MS-W9). No OWC-MS re-litigation; the eight already-merged modules stay rendered. No vendor / model / provider / engine identifiers anywhere in the helper or the rendered template. No donor namespace import. No React / Vite rebuild. No durable persistence. |
| §4.5 Closeout-paperwork independence | PASS | This PR does NOT advance OWC-MS MS-A7, OWC-DA DA-A7, or any Plan E A7 / UA7 / RA7 signoff. No coupling to Track A signoff. |

### 4.1 No-fake-`final_video` discipline (RC-A6 forerunner)

The helper renders no media URL, no `https://` / `http://` / `.mp4` substring, and no `final_video_url` synthesis. Where the underlying `publish_readiness` says `final_missing` / `final_stale` / `final_provenance_historical`, the operator-language headline names the gap directly (e.g. "成片缺失，等待生成产出后再进入校对"). Asserted by the dedicated test `test_workbench_no_fake_final_video_when_final_missing`.

### 4.2 No-second-truth-source discipline (RC-A7 forerunner)

The Workbench helper consumes the same `publish_readiness` dict already computed at the wiring layer for `qc_diagnostics_view`; it does not call `compute_publish_readiness` again. The Task Area helper consumes `row["board_bucket"]` and `row["head_reason"]` already set by `task_router_presenters.build_tasks_page_rows`; it does not re-derive them. Asserted by `test_workbench_consumes_publish_readiness_verbatim`.

---

## 5. Tests Run

- New file: `gateway/app/services/tests/test_matrix_script_result_status_view.py` — **45 PASS / 0 FAIL** (gate spec §5.2 ≥25 floor: PASS at 1.8×).
- Adjacent matrix_script regression — **259 PASS / 0 FAIL** across `test_matrix_script_task_area_convergence.py` (eight-stage state preserved); `test_matrix_script_qc_diagnostics_view.py` (MS-W6 unchanged); `test_matrix_script_review_zone_view.py` (MS-W5 unchanged); `test_matrix_script_preview_compare_view.py` (MS-W4 unchanged); `test_matrix_script_workbench_comprehension.py` (PR-U2 unchanged); `test_matrix_script_script_structure_view.py` (MS-W3 unchanged); `test_matrix_script_closure_binding.py` (closure read-only path); `test_publish_readiness_unified_producer.py` (PR-1 producer unchanged); plus the new file.
- Cross-line preservation — **180 PASS / 0 FAIL** across `test_digital_anchor_task_area_convergence.py` (DA Task Area unchanged); `test_matrix_script_delivery_backfill_view.py`, `test_matrix_script_delivery_copy_bundle_view.py`, `test_matrix_script_delivery_comprehension.py`, `test_matrix_script_delivery_zoning.py` (MS-W7/W8 unchanged); `test_publish_readiness_surface_alignment.py` (cross-line publish-readiness alignment).
- Pre-existing Python 3.9 PEP-604 baseline at `gateway/app/config.py:43` — collection errors for `test_task_router_presenters.py` and 18 other env-coupled files are the same baseline recorded in OWC-MS Closeout §8 + OWC-DA Closeout §8 + ENGINEERING_RULES.md §10 (env limitation, not introduced by this PR).

**Aggregate:** 484 PASS / 0 FAIL on the import-light regression set + new file.

---

## 6. Operator-Comprehension Demonstration (RC-A5 — this PR's slice)

The four operator questions from amendment §1 / gate spec §2:

1. **What is usable now** — sample task in stage `publishable`: card row reads `就绪 · 可发布 · 前往交付中心发布 · 在交付中心选择渠道与账号完成发布。`. Operator can act without reading any packet field.
2. **What is blocked** — sample task in stage `pending_config` with `head_reason=null`: card row reads `阻塞 · 待配置 · 缺少变体配置 · 前往工作台完成 Phase B 选型...`. The missing item is named explicitly (`variation_cells_empty`).
3. **What next action is required** — every status carries a concrete `next_action_zh` sentence keyed off the eight-stage state (Task Area) or the `head_reason` closed enum (Workbench). No status is silent.
4. **Whether script / variants / delivery package are present or missing** — RC PR-1 names the *coarse* state (variants present? compose running? final present? publishable?). The fine-grained "show me the readable Hook / Body / CTA + multi-variant candidate listing + delivery bundle" is RC PR-2 / RC PR-4 scope per gate spec §5; this PR sets the operator-comprehension floor without expanding it.
5. **Why Matrix Script is not yet publishable, without reading raw packet structure** — when blocked, the Workbench summary surfaces the `head_reason` label in operator language (e.g. `合成前置项未就绪`); the operator does not have to inspect ready_gate / publish_readiness / packet fields to learn the reason.

---

## 7. Residual Risks

- **RC PR-2 dependency** — the readable Hook / Body / CTA per variation (RC-R1+R2+R3) is the natural follow-on; until RC PR-2 lands, the RC-R6 status row will sometimes name a blocker that the operator cannot resolve from the existing surfaces (e.g. `pending_config` requires Phase B authoring affordances that PR-2 reframes). This is by design — RC PR-1 establishes the result-oriented floor; it does not prematurely deliver RC PR-2 / PR-3 / PR-4 scope.
- **Unknown future `head_reason` values** — the Workbench helper falls back to a generic prompt (`请联系架构师确认状态语义后再决定下一步`) for unknown enum values. Asserted by `test_workbench_unknown_head_reason_degrades_gracefully`. If the closed enum is ever extended (which is forbidden by gate spec §4.1 within this wave), the helper will not break but will surface a generic action.
- **Closure store volatility** — the Task Area helper reads closure read-only via `get_closure_view_for_task`; on a gateway restart the in-process store is empty and the eight-stage state will project as `created` / `pending_config` rather than `backfilled`. This is the same volatility recorded in OWC-MS Closeout §8 (OPS-GAP-2) and the post-OWC ops addendum §6 — not introduced by this PR.
- **Pre-existing Python 3.9 PEP-604 baseline** — `gateway/app/config.py:43` continues to block 19 env-coupled test files from collection on Python 3.9; CI on 3.10+ exercises them. Out-of-scope for the recovery wave per ENGINEERING_RULES §10.

---

## 8. What This PR Does NOT Do

- Does NOT advance any closeout signoff (OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7 stay independently pending).
- Does NOT open RC PR-2 / RC PR-3 / RC PR-4 — those open sequentially per gate spec §5 ordering, each only after its predecessor merges and reviews.
- Does NOT touch Hot Follow, Digital Anchor, Asset Supply, contracts, schemas, packets, samples, or new endpoints.
- Does NOT introduce a second authoritative producer for publishability, recommended version, advisories, or `final_provenance`.
- Does NOT synthesise any media URL or `final_video` placeholder.
- Does NOT couple Track A (Hot-Follow-only Plan A live-trial window) signoff to RC PR-1 — Track A signoff is informational input only per amendment §6.
