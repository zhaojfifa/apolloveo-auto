# RC PR-4 Execution Log — Matrix Script Result-Capability Recovery (RC-R5 + RC-R7 + RC-R8)

Date: 2026-05-07
Status: Implementation green; PR open. Engineering only — operator-comprehension demonstration (RC-A5) recorded in §6 below.
Wave: ApolloVeo 2.0 Matrix Script Result-Capability Recovery Wave (Track B).
Phase: RC PR-4 — Delivery-ready copy/script package + publish/backfill readiness.
Authority: [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) §3 RC-R5 + §3 RC-R7 + §3 RC-R8 + §5 RC PR-4.

---

## 1. Reading Declaration

Authority files read before authoring this implementation, in `CLAUDE.md` §2 boot order:

1. `CLAUDE.md` — bootloader.
2. `ENGINEERING_RULES.md` — engineering governance, §13 Product-Flow Module Presence.
3. `CURRENT_ENGINEERING_FOCUS.md` — current-stage preamble (post §10 signoff + RC PR-1 / RC PR-2 / RC PR-3 substrate merged on `main`).
4. `ENGINEERING_STATUS.md` — head completion log.
5. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` — bifurcated frozen sequence (§7).
6. `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` (binding scope).
7. `docs/product/matrix_script_product_flow_v1.md` (line-specific product flow §7.1 / §7.3 / §9.5).
8. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`.
9. RC PR-1 + RC PR-2 + RC PR-3 substrate: `result_status_view.py`, `readable_variant_view.py`, `recommended_action_view.py`.
10. OWC-MS PR-3 substrate: `delivery_comprehension.py`, `delivery_copy_bundle_view.py`, `delivery_backfill_view.py`, `publish_hub_pr3_attach.py`.
11. Recovery PR-1 unified `publish_readiness` producer at `gateway/app/services/operator_visible_surfaces/publish_readiness.py`.
12. RC PR-3 execution log for the matrix_script wiring + closure-binding pattern.

Surface mapped via existing OWC-MS PR-3 helpers (`delivery_comprehension` lanes — `required_blocking` / `required_non_blocking` / `optional_non_blocking` with `artifact_status_code ∈ {current_fresh, historical, unresolved, unknown}`), the OWC-MS PR-3 `delivery_copy_bundle_view` per-subfield `status_code ∈ {resolved_from_existing_projection, unresolved_pending_copy_projection_contract}`, the RC PR-2 `readable_variant_view` per-cell payload (axis_summary_zh / differentiator_zh / has_bound_slot / length_hint_zh), the unified PR-1 `publish_readiness` producer's closed `head_reason` enum + `publishable` boolean, and the publish-feedback closure `variation_feedback[].publish_status` closed enum (`pending` / `published` / `failed` / `retracted`). No second producer introduced.

---

## 2. RC-R / RC-A Scope Covered

### 2.1 RC-R items in scope (this PR only)

- **RC-R5 — delivery-ready copy/script package.** Per variation, the Workbench renders one row classifying the package as one of the closed enum values:
  - `ready_package` — bound script slot AND publishable AND all required+blocking artifacts current AND copy_bundle fully resolved (the operator can take the readable bundle to a downstream channel immediately).
  - `partial_package` — readable content exists but some required artifacts / copy fields not in place; operator can begin preparation but cannot finalize.
  - `blocked_package` — publish_readiness blocked; the row names the closed `head_reason` label.
  - `unavailable_tracked_gap` — neither bound slot nor any resolved copy subfield has reached this variation; explicit tracked gap with operator-language next action.
- **RC-R7 — publish / backfill readiness surface.** Per variation, the Publish Hub explains, in operator language, one of the closed readiness states:
  - `publishable_now` — publish_readiness publishable AND no closure record yet → "前往 Delivery Center 选择渠道与账号".
  - `gated_pending_publish_readiness` — publish_readiness blocked, head_reason emitted as a label.
  - `already_published_backfill_pending_metrics` — closure carries `published` or `retracted` for this variation → operator goes to multi-channel backfill panel for metrics.
  - `already_failed_pending_retry` — closure carries `failed`.
  - `tracked_gap_no_artifact` — variation has neither bound script nor a required+blocking lane row; nothing publishable yet.
- **RC-R8 — no fake `final_video`.** Both helpers reject every media-URL substring (`http(s)://` / `.mp4` / `.mov` / `final_video_url` / `preview_url` / `publish_url` / `content://`). Even when the closure carries a real `publish_url`, the publish-backfill-readiness helper does NOT echo that URL — that field is rendered exclusively by the existing OWC-MS PR-3 `delivery_backfill` view. Each panel-level and per-row payload carries the explicit `no_final_video_url_note_zh` operator-language tracked-gap note.

### 2.2 RC-R items explicitly NOT in scope (per gate spec §5 ordering)

- RC-R6 (blocked / next-action state on Task Area + Workbench summary header) — already shipped by RC PR-1.
- RC-R1 / RC-R2 / RC-R3 (operator-readable script + variant candidate package) — already shipped by RC PR-2.
- RC-R4 (recommended-version + next-action lane) — already shipped by RC PR-3.

### 2.3 RC-A acceptance rows targeted by this PR

- **RC-A4** — RC PR-4 implementation green and merged. Evidence: this execution log + diff + PR # + squash commit (recorded by Closeout when paperwork lands).
- **RC-A5 (this PR's slice)** — operator-comprehension demonstration in §6 below.
- Forbidden-scope audit rows (RC-A6 / RC-A7 / RC-A8 / RC-A9 / RC-A10 / RC-A11 / RC-A12) per-PR audit recorded in §4 below.

---

## 3. Files Changed

| File | Kind | Purpose |
| --- | --- | --- |
| `gateway/app/services/matrix_script/delivery_ready_package_view.py` | new | RC-R5 + RC-R8 helper: `derive_matrix_script_delivery_ready_package(readable_variants, delivery_comprehension, copy_bundle_view, publish_readiness, line_specific_panel)`. Closed package-status enum (`ready_package` / `partial_package` / `blocked_package` / `unavailable_tracked_gap`); reuses RC PR-2 readable variants, OWC-MS PR-3 `delivery_comprehension` lanes, OWC-MS PR-3 `delivery_copy_bundle_view` subfield status, and the PR-1 unified `publish_readiness`. Helper signature has no `compute_publish_readiness` import. Forbidden-token + URL scrub on every echoed string. |
| `gateway/app/services/matrix_script/publish_backfill_readiness_view.py` | new | RC-R7 + RC-R8 helper: `derive_matrix_script_publish_backfill_readiness(readable_variants, delivery_comprehension, publish_readiness, closure)`. Closed readiness enum (`publishable_now` / `gated_pending_publish_readiness` / `already_published_backfill_pending_metrics` / `already_failed_pending_retry` / `tracked_gap_no_artifact`); reads only the closed `publish_status` enum from `variation_feedback[]` — never echoes `publish_url`. Cross-line gated by the closure surface check (`matrix_script_publish_feedback_closure_v1` or `line_id == "matrix_script"`). |
| `gateway/app/services/operator_visible_surfaces/wiring.py` | edit | Inside the existing `panel_kind == "matrix_script"` branch, attaches `bundle["workbench"]["matrix_script_delivery_ready_package"]` after both `matrix_script_recommended_action` and the OWC-MS PR-3 `matrix_script_delivery_comprehension` are computed. Imports `delivery_copy_bundle_view` to derive the workbench-side copy bundle (`base_copy_bundle={}` because the workbench bundle does not carry the publish-hub copy projection — partial-status classification still uses the per-subfield status_code). No new `compute_publish_readiness` call. |
| `gateway/app/services/matrix_script/publish_hub_pr3_attach.py` | edit | Adds a defense-in-depth seam that re-derives the matrix_script readable variants (via `project_workbench_variation_surface` + `derive_matrix_script_readable_variants`) and consumes the already-attached `payload["matrix_script_delivery_comprehension"]` + `payload["operator_surfaces"]["delivery"]["publish_readiness"]` + `payload["matrix_script_publish_feedback_closure"]` to attach `payload["matrix_script_publish_backfill_readiness"]`. Cross-line `_is_matrix_script_task` gate preserved verbatim. |
| `gateway/app/templates/task_workbench.html` | edit | New `data-role="matrix-script-delivery-ready-package-panel"` block inserted between the RC PR-2 readable-variants panel and the OWC-MS PR-2 / MS-W5 review-zone panel, strictly inside the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate. Operator-language status pill, axis summary, length hint, gap explanation, copy-bundle counters, head_reason label, and the explicit no-fake-final-video / no-publish-claim notes. |
| `gateway/app/templates/task_publish_hub.html` | edit | New `data-role="matrix-script-publish-backfill-readiness"` server-rendered card + `renderMatrixScriptPublishBackfillReadiness` JS renderer wired into the existing publish-hub dispatch site. Strictly inside the existing `{% if _ms_kind == "matrix_script" %}` gate. Renderer uses only fields published by the helper — no DOM injection of `publish_url` or media URLs. |
| `gateway/app/services/tests/test_matrix_script_delivery_ready_package_view.py` | new | 38 cases (gate spec §5.2 ≥35 floor: PASS at 1.08×). |
| `gateway/app/services/tests/test_matrix_script_publish_backfill_readiness_view.py` | new | 39 cases. |
| `gateway/app/services/tests/test_matrix_script_publish_hub_pr3_wiring.py` | edit | Updated the byte-isolation `test_attach_does_not_mutate_task_or_inputs_other_than_two_target_keys` assertion to expect the additional RC PR-4 key `matrix_script_publish_backfill_readiness` alongside the OWC-MS PR-3 keys. No semantic change to the seam contract. |
| `docs/execution/APOLLOVEO_2_0_RC_PR4_DELIVERY_PUBLISH_READINESS_EXECUTION_LOG_v1.md` | new | This log. |
| `docs/execution/apolloveo_2_0_evidence_index_v1.md` | edit | New evidence row + RC PR-3 row updated to LANDED. |

`task_router_presenters.py` was NOT touched — RC PR-4 reuses the existing operator_surfaces bundle path.

---

## 4. Forbidden-Scope Audit (per PR; full audit at Closeout)

| Sub-section | Verdict | Notes |
| --- | --- | --- |
| §4.1 Truth-source / contract preservation | PASS | No new contract. No closed-enum widening. The package-status enum and the publish-readiness-explanation enum are presentation-layer view tables, not contract enums. The helpers reuse the closed `RECOMMENDED_BUCKET_*` (RC PR-3 substrate, untouched), `HEAD_REASON_LABELS_ZH` (PR-1 substrate, untouched), `artifact_status_code` (OWC-MS PR-3 substrate, untouched), `publish_status` closed enum from `variation_feedback[]` (closure contract, untouched), and copy_bundle subfield `status_code` (OWC-MS PR-3 substrate, untouched). No `source_script_ref` repurposing. No new packet truth for `final_provenance`, copy_bundle subfields, or `final_video`. |
| §4.2 Cross-line preservation | PASS | `git diff --stat` against `origin/main` touches only matrix_script-gated branches and two new helper modules under `gateway/app/services/matrix_script/`. Zero `hot_follow*`, zero `digital_anchor*`, zero `gateway/app/services/asset/`, zero `docs/contracts/`, zero `schemas/` paths. The publish-hub attach path is gated by the existing `_is_matrix_script_task(task)` short-circuit. |
| §4.3 Wave-position preservation | PASS | No Platform Runtime Assembly. No Capability Expansion. No Plan A live-trial reopen. No new operator-eligible discovery surface. |
| §4.4 Scope-boundary preservation | PASS | No new structural surface module — the new panels reframe the existing OWC-MS PR-3 Delivery Center + RC PR-2 readable-variants projections into operator-language readiness lanes; they do not author MS-W9 or wider. No OWC-MS re-litigation. No vendor / model / provider / engine identifiers (asserted by `test_no_vendor_or_model_strings_in_payload` on each helper). No donor namespace import. No React / Vite rebuild. No durable persistence. |
| §4.5 Closeout-paperwork independence | PASS | No coupling to OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, Track A signoff, RC PR-1 / RC PR-2 / RC PR-3 closeouts. |

### 4.1 No-fake-`final_video` discipline (RC-A6 forerunner)

Both helpers render no media URL, no `http://` / `https://` / `.mp4` / `.mov` / `final_video_url` / `preview_url` / `publish_url` / `content://` substring. Asserted by parametrized `test_no_fake_final_video_or_media_url` across the closed status_kind / readiness_kind matrix on each helper. The publish-backfill-readiness helper additionally has `test_publish_url_from_closure_is_not_echoed_in_payload` — when the closure `variation_feedback` row carries `publish_url=https://example.test/published.mp4`, the helper trusts only the closed `publish_status` field and surfaces nothing of the URL. Both helpers carry the explicit `no_final_video_url_note_zh` operator-language note at panel + per-row level.

### 4.2 No-second-truth-source discipline (RC-A7 forerunner)

The `delivery_ready_package_view` helper signature is `(readable_variants, delivery_comprehension, copy_bundle_view, publish_readiness, line_specific_panel)` — there is no `compute_publish_readiness` call site (asserted by `test_helper_does_not_call_compute_publish_readiness`). Publishability is read verbatim from `publish_readiness["publishable"]`; deliverable lane classification is read verbatim from `delivery_comprehension["lanes"]`; copy_bundle subfield resolution is read verbatim from the per-subfield `status_code`. The `publish_backfill_readiness_view` helper signature is `(readable_variants, delivery_comprehension, publish_readiness, closure)` — same discipline; closure publish_status is read verbatim from the closed enum, never re-derived.

### 4.3 No-raw-handle / no-vendor leakage discipline (RC-A8 forerunner)

Neither helper passes through `script_slot_ref` / `slot_body_ref` / `content://` substrings even when the upstream readable_variants axis_summary or differentiator carries them. The defensive `_scrub` function rejects any forbidden-token or forbidden-URL substring before echoing. Asserted by `test_no_raw_slot_or_body_ref_in_payload` / `test_no_content_handle_leakage` / `test_no_vendor_or_model_strings_in_payload` on each helper.

---

## 5. Tests Run

- New file: `test_matrix_script_delivery_ready_package_view.py` — **38 PASS / 0 FAIL** (gate spec §5.2 ≥35 floor: PASS at 1.08×).
- New file: `test_matrix_script_publish_backfill_readiness_view.py` — **39 PASS / 0 FAIL**.
- Adjacent matrix_script + RC substrate regression: included in **1107 PASS / 29 SKIPPED / 0 FAIL** aggregate across 70 collectable suites under `gateway/app/services/tests/` — `test_matrix_script_delivery_ready_package_view`, `test_matrix_script_publish_backfill_readiness_view`, `test_matrix_script_publish_hub_pr3_wiring` (one assertion updated for the new RC PR-4 key — semantics preserved), `test_matrix_script_recommended_action_view` (RC PR-3 substrate intact), `test_matrix_script_readable_variant_view` (RC PR-2 substrate intact), `test_matrix_script_result_status_view` (RC PR-1 substrate intact), `test_matrix_script_qc_diagnostics_view`, `test_matrix_script_review_zone_view`, `test_matrix_script_preview_compare_view`, `test_matrix_script_workbench_comprehension`, `test_matrix_script_script_structure_view`, `test_matrix_script_closure_binding`, `test_matrix_script_delivery_comprehension`, `test_matrix_script_delivery_backfill_view`, `test_matrix_script_delivery_copy_bundle_view`, `test_matrix_script_delivery_zoning`, `test_publish_readiness_unified_producer`, `test_digital_anchor_publish_hub_pr3_attach` (cross-line preservation), `test_digital_anchor_publish_closure_backfill_view`, `test_publish_readiness_surface_alignment`, etc.
- Pre-existing Python 3.9 PEP-604 baseline at `gateway/app/config.py:43` continues to block the same 19 env-coupled test files from collection (recorded in OWC-MS / OWC-DA / RC PR-1 / RC PR-2 / RC PR-3 evidence). Not introduced by this PR.

---

## 6. Operator-Comprehension Demonstration (RC-A5 — this PR's slice)

The five required outcomes from the user mission:

1. **Surface a delivery-ready copy/script package when existing truth supports it.** Sample task with one variation that has a bound script slot and a publishable `publish_readiness`: the Workbench panel renders one row with `package_status_kind=partial_package` (because the closure-side `comment_keywords` subfield always renders unresolved per OWC-MS PR-3 single-source discipline). Headline reads `脚本/文案包部分就绪 · 仍有可选/非阻塞缺口` with operator-language `next_action_zh = 可参考已就绪字段先行启动文案准备…` and `gap_explanation_zh = copy_bundle 字段就绪 0/4`. When all required+blocking artifacts are current and the bound script slot exists, the row promotes to `ready_package` with operator-language `headline_zh = 可交付的脚本/文案包已就绪`.

2. **Clearly distinguish ready / partial / blocked / unavailable / tracked-gap states.** Five closed cases verified by tests:
   - `ready_package`: bound slot + all artifacts current + copy fully resolved + publishable.
   - `partial_package`: bound slot present but one of the inputs is incomplete (e.g. comment_keywords always unresolved); operator can advance incrementally.
   - `blocked_package`: publish_readiness reports not publishable; the row names the operator-language `head_reason` label (e.g. `合成前置项未就绪`).
   - `unavailable_tracked_gap`: neither bound script slot nor any resolved copy subfield (e.g. Phase B has not yet derived this cell).
   - For the publish-hub side, the parallel readiness lane has five buckets (`publishable_now` / `gated_pending_publish_readiness` / `already_published_backfill_pending_metrics` / `already_failed_pending_retry` / `tracked_gap_no_artifact`).

3. **Explain publish/backfill readiness in operator language.** Sample task where `publish_readiness.publishable=True` and the closure has no `published` row for the variation: the Publish Hub renders `可发布 · 现在即可发布` with `next_input_zh = 在 Delivery Center 选择渠道与账号执行发布；本面板不展示 final_video / 媒体链接，操作后回到本面板查看回填状态。`. When the closure already carries `publish_status=published`, the row promotes to `已发布 · 等待回填指标` with `next_input_zh = 回到 Delivery Center 多渠道回填面板补齐 channel / 时间 / 指标 snapshot；本面板不重复展示 publish_url。`.

4. **Connect the package/readiness explanation to existing Matrix Script facts and `publish_readiness` truth.** Both helpers read `publish_readiness["publishable"]` + `publish_readiness["head_reason"]` verbatim from the unified PR-1 producer. The package row's `head_reason_label_zh` is mapped through the existing closed `HEAD_REASON_LABELS_ZH` map (RC PR-3 substrate, unchanged). The required-artifact gap kinds are the operator-language `kind_label_zh` strings from the existing `delivery_comprehension.lanes.required_blocking.rows` — no second classification.

5. **Do not claim `final_video` or media deliverables if only script/copy package exists.** No row, no helper, no template surfaces a `final_video_url` / `publish_url` / media URL string. The helpers carry `no_final_video_url_note_zh` at panel level and per row. Adversarial test `test_publish_url_from_closure_is_not_echoed_in_payload` confirms the helper never echoes a real `publish_url` from the closure; the multi-channel backfill panel's existing `publish_url` field remains the single rendering site for that string.

---

## 7. Residual Risks

- **Closure store volatility** — same pre-existing OPS-GAP-2 baseline as RC PR-1 / PR-2 / PR-3; in-process closure store is volatile across gateway restart. Not introduced by this PR.
- **Pre-existing Python 3.9 PEP-604 baseline** — same 19 env-coupled test files block as prior RC waves; CI on 3.10+ exercises them.
- **Workbench-side copy_bundle empty** — the workbench wiring derives `delivery_copy_bundle_view` with `base_copy_bundle={}` because the workbench bundle does not own the publish-hub copy projection. The package classifier therefore counts `copy_resolved=0` on the workbench, naturally landing most rows in `partial_package` until the operator reaches the publish-hub-side view. This is acceptable per gate spec §3 RC-R5 (the package presentation is RC-R5 + RC-R8 only; copy projection authority remains the publish-hub `_build_copy_bundle`).
- **Closure publish_url not surfaced in readiness** — by design (gate spec §3 RC-R8 + §4.1). The existing OWC-MS PR-3 `delivery_backfill` panel remains the single rendering site for `publish_url`.

---

## 8. What This PR Does NOT Do

- Does NOT advance any closeout signoff (OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, RC PR-1 / RC PR-2 / RC PR-3 closeouts — all stay independently pending).
- Does NOT touch Hot Follow, Digital Anchor, Asset Supply, contracts, schemas, packets, samples, or new endpoints.
- Does NOT introduce a second authoritative producer for publishability, recommended version, advisories, copy_bundle, or `final_provenance`.
- Does NOT synthesise any media URL or `final_video` placeholder; does not echo `publish_url` from closure or `final_video_url` from compose state.
- Does NOT widen any closed enum (`HEAD_REASON_LABELS_ZH` / `artifact_status_code` / `publish_status` / `RECOMMENDED_BUCKET_*` consumed verbatim).
- Does NOT couple Track A (Hot-Follow-only Plan A live-trial window) signoff to RC PR-4.
- Does NOT advance any new operator-eligible discovery surface; the panels are presentation reframes of the already-rendered OWC-MS / RC substrate.
