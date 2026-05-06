# RC PR-3 Execution Log — Matrix Script Result-Capability Recovery (RC-R4)

Date: 2026-05-06
Status: Implementation green; PR open. Engineering only — operator-comprehension demonstration (RC-A5) recorded in §6 below.
Wave: ApolloVeo 2.0 Matrix Script Result-Capability Recovery Wave (Track B).
Phase: RC PR-3 — Recommended-version + next-action lane.
Authority: [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) §3 RC-R4 + §5 RC PR-3.

---

## 1. Reading Declaration

Authority files read before authoring this implementation, in `CLAUDE.md` §2 boot order:

1. `CLAUDE.md` — bootloader.
2. `ENGINEERING_RULES.md` — engineering governance, §13 Product-Flow Module Presence.
3. `CURRENT_ENGINEERING_FOCUS.md` — current-stage preamble (post §10 signoff + RC PR-1 + RC PR-2 substrate).
4. `ENGINEERING_STATUS.md` — head completion log.
5. `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` (binding scope).
6. `docs/product/matrix_script_product_flow_v1.md`.
7. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`.
8. RC PR-1 + RC PR-2 substrate: `result_status_view.py`, `readable_variant_view.py`.

Surface mapped via existing OWC-MS PR-2 helpers (`preview_compare_view.py` — closed `RECOMMENDED_BUCKET_PUBLISHABLE` / `RECOMMENDED_BUCKET_BLOCKED` / `RECOMMENDED_BUCKET_UNDETERMINED` enum + per-variation `recommended_*` fields decided by the unified `publish_readiness` producer) and the OWC-MS PR-2 `qc_diagnostics_view.HEAD_REASON_LABELS_ZH` map. No second producer introduced.

---

## 2. RC-R / RC-A Scope Covered

### 2.1 RC-R items in scope (this PR only)

- **RC-R4 — recommended-version + next-action lane.** A single Workbench panel renders one of three operator-language statements per task:
  - `推荐 · 可发布候选已锁定` + named variant id + axis summary + concrete next action (`前往 Delivery Center 选择渠道与账号完成发布；发布完成后回到本面板复盘指标。`).
  - `暂不推荐 · 发布门禁阻塞` + operator-language `head_reason` label + concrete next action (`解除 publish_readiness 阻塞前置项后再尝试`).
  - `暂无推荐 · 待 publish_readiness 收敛` + concrete next action (`等待第一次成片产出并完成校对`).

### 2.2 RC-R items explicitly NOT in scope (per gate spec §5 ordering)

- RC-R5, RC-R7, RC-R8 — delivery-ready package + publish/backfill readiness + no-fake-`final_video` Delivery audit (RC PR-4). RC PR-3 already enforces the "no fake `final_video`" discipline locally via test (forerunner of RC-A6).
- RC-R1 / R2 / R3 — already shipped by RC PR-2.
- RC-R6 — already shipped by RC PR-1.

### 2.3 Acceptance rows targeted by this PR

- **RC-A3** — RC PR-3 implementation green and merged. Evidence: this execution log + diff + PR # + squash commit (recorded by Closeout when paperwork lands).
- **RC-A5 (this PR's slice)** — operator-comprehension demonstration in §6 below.
- Forbidden-scope audit rows (RC-A6 / RC-A7 / RC-A8 / RC-A9 / RC-A10 / RC-A11 / RC-A12) per-PR audit recorded in §4 below.

---

## 3. Files Changed

| File | Kind | Purpose |
| --- | --- | --- |
| `gateway/app/services/matrix_script/recommended_action_view.py` | new | RC-R4 helper: `derive_matrix_script_recommended_action(preview_compare, readable_variants, line_specific_panel)`. Reuses the closed `RECOMMENDED_BUCKET_*` enum from MS-W4 verbatim; the only new view-layer constants are the operator-language headlines / next-action sentences (presentation only — not contract enums). Helper signature has no `publish_readiness` parameter; it consumes the pre-decided `recommended_bucket` / `recommended_head_reason` from MS-W4. |
| `gateway/app/services/operator_visible_surfaces/wiring.py` | edit | Inside the existing `panel_kind == "matrix_script"` branch, attaches `bundle["workbench"]["matrix_script_recommended_action"]` after both `matrix_script_preview_compare` and `matrix_script_readable_variants` are computed (so both are available as inputs). No second `compute_publish_readiness` call. |
| `gateway/app/templates/task_workbench.html` | edit | New `data-role="matrix-script-recommended-action-panel"` block inserted between MS-W4 (preview compare) and the RC PR-2 readable-variants panel, strictly inside the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate. |
| `gateway/app/services/tests/test_matrix_script_recommended_action_view.py` | new | 35 dedicated import-light cases (gate spec §5.2 ≥25 floor: PASS at 1.4×). |
| `docs/execution/APOLLOVEO_2_0_RC_PR3_RECOMMENDED_ACTION_LANE_EXECUTION_LOG_v1.md` | new | This log. |
| `docs/execution/apolloveo_2_0_evidence_index_v1.md` | edit | New evidence row + RC PR-2 row updated to LANDED. |

`task_router_presenters.py` was NOT touched — RC PR-3 delivers a Workbench-only surface.

---

## 4. Forbidden-Scope Audit (per PR; full audit at Closeout)

| Sub-section | Verdict | Notes |
| --- | --- | --- |
| §4.1 Truth-source / contract preservation | PASS | No new contract. No closed-enum widening. The lane reuses the existing `RECOMMENDED_BUCKET_PUBLISHABLE` / `RECOMMENDED_BUCKET_BLOCKED` / `RECOMMENDED_BUCKET_UNDETERMINED` enum from MS-W4 verbatim and consumes `recommended_head_reason` from the existing `HEAD_REASON_LABELS_ZH` closed map. The new operator-language constants (`HEADLINE_*_ZH` / `NEXT_ACTION_*_ZH`) are presentation-layer view tables, not contract enums. |
| §4.2 Cross-line preservation | PASS | `git diff --stat` touches only matrix_script-gated branches and one new helper module under `gateway/app/services/matrix_script/`. Zero `hot_follow*`, zero `digital_anchor*`, zero `gateway/app/services/asset/`, zero `docs/contracts/`, zero `schemas/` paths. |
| §4.3 Wave-position preservation | PASS | No Platform Runtime Assembly. No Capability Expansion. No Plan A live-trial reopen. No new operator-eligible discovery surface. |
| §4.4 Scope-boundary preservation | PASS | No new structural surface module — the new panel reframes the existing MS-W4 `recommended_*` projection into an actionable lane; it does not author MS-W9 or wider. No OWC-MS re-litigation. No vendor / model / provider / engine identifiers (asserted by `test_no_vendor_or_model_strings_in_payload`). No donor namespace import. No React / Vite rebuild. No durable persistence. |
| §4.5 Closeout-paperwork independence | PASS | No coupling to OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, Track A signoff, RC PR-1 closeout, or RC PR-2 closeout. |

### 4.1 No-fake-publish / no-fake-`final_video` discipline (RC-A6 forerunner)

The helper renders no media URL, no `https://` / `http://` / `.mp4` / `.mov` / `final_video_url` / `preview_url` / `publish_url` substring. Asserted by parametrized `test_no_fake_final_video_or_media_url` across all three status_kind cases. Adversarial test `test_helper_consumes_recommended_bucket_verbatim` confirms that even when an upstream variation row carries an injected `publishable=True` + `publish_url=https://attacker.example/x.mp4` pair, the helper trusts only the closed `recommended_bucket` field and surfaces nothing of the injected media URL. Every operator-visible status carries the explicit `no_publish_claim_note_zh`: `"本面板不展示 final_video / 媒体链接 / 交付包就绪状态。RC-R5 / RC-R7 / RC-R8 由 RC PR-4 覆盖。"`.

### 4.2 No-second-truth-source discipline (RC-A7 forerunner)

The helper signature is `(preview_compare, readable_variants, line_specific_panel)` — there is no `publish_readiness` parameter. The `recommended_bucket` / `recommended_head_reason` are consumed verbatim from the MS-W4 surface; the helper never re-derives them. Asserted by `test_helper_signature_has_no_publish_readiness_parameter`, `test_helper_does_not_call_compute_publish_readiness`, and `test_helper_signature_only_takes_documented_inputs`. Source-level scan confirms no `compute_publish_readiness(` call site and no `from gateway.app.services.operator_visible_surfaces.publish_readiness` import.

### 4.3 No-raw-handle / no-vendor leakage discipline (RC-A8 forerunner)

The helper does NOT pass through `script_slot_ref` / `slot_body_ref` / `content://` substrings even when the upstream MS-W4 surface carries them — only the operator-visible MS-W2/RC-PR2 fields (`variation_id`, `axis_summary_zh`, `differentiator_zh`, `length_hint_zh`, `has_bound_slot`) flow through. Asserted by `test_no_raw_slot_or_body_ref_in_payload` (adversarial fixture injects `slot_001` + `content://...` and confirms neither leaks). `test_no_vendor_or_model_strings_in_payload` confirms no `vendor` / `model_id` / `provider` / `engine` / `swiftcraft` substrings.

---

## 5. Tests Run

- New file: `test_matrix_script_recommended_action_view.py` — **35 PASS / 0 FAIL** (gate spec §5.2 ≥25 floor: PASS at 1.4×).
- Adjacent matrix_script + RC substrate regression: included in **530 PASS / 0 FAIL** aggregate across 17 import-light suites — `test_matrix_script_recommended_action_view`, `test_matrix_script_readable_variant_view` (RC PR-2 substrate intact), `test_matrix_script_result_status_view` (RC PR-1 substrate intact), `test_matrix_script_task_area_convergence`, `test_matrix_script_qc_diagnostics_view`, `test_matrix_script_review_zone_view`, `test_matrix_script_preview_compare_view`, `test_matrix_script_workbench_comprehension`, `test_matrix_script_script_structure_view`, `test_matrix_script_closure_binding`, `test_publish_readiness_unified_producer`, `test_digital_anchor_task_area_convergence` (cross-line preservation), `test_matrix_script_delivery_*` (×4), `test_publish_readiness_surface_alignment`.
- Pre-existing Python 3.9 PEP-604 baseline at `gateway/app/config.py:43` continues to block the same 19 env-coupled test files from collection (recorded in OWC-MS / OWC-DA / RC PR-1 / RC PR-2 evidence). Not introduced by this PR.

---

## 6. Operator-Comprehension Demonstration (RC-A5 — this PR's slice)

The five required outcomes from the user mission:

1. **Clearly identify the currently recommended variant in operator language** — sample task with two cells in `publishable_candidate` bucket: panel reads `推荐 · 可发布候选已锁定 · 推荐变体：cell_001 · 语气=轻松（casual） · 受众=面向消费者（b2c） · 时长=60s`. The variant id and operator-language axis summary are named explicitly.

2. **Explain why it is recommended** — reason row reads `推荐依据：publish_readiness=publishable 且未在 closure 中标记为已发布 → 列入推荐候选。`. Wording is sourced from the existing MS-W4 `recommended_explanation_zh` verbatim — no new authority.

3. **Tell the operator what next action to take** — concrete next-action sentence: `前往 Delivery Center 选择渠道与账号完成发布；发布完成后回到本面板复盘指标。`. When blocked: `解除 publish_readiness 阻塞前置项后再尝试；具体阻塞原因见 head_reason。`. When undetermined: `等待第一次成片产出并完成校对；publish_readiness 收敛后系统会自动推进推荐。`.

4. **Without claiming publish-readiness or delivery-readiness beyond existing truth** — when `recommended_bucket == "blocked_pending_publish_readiness"`, the panel reports `暂不推荐 · 发布门禁阻塞` and surfaces the operator-language `head_reason` label (e.g. `合成前置项未就绪`); `recommended_variant` is `null`; no media URL or delivery artifact is shown. The explicit `no_publish_claim_note_zh` row tells the operator that delivery readiness is RC PR-4 scope.

5. **Preserve existing truth ownership and avoid second-truth creation** — helper signature `(preview_compare, readable_variants, line_specific_panel)` cannot reach `publish_readiness`; `recommended_bucket` / `recommended_head_reason` flow through verbatim. Adversarial test confirms an injected `publishable=True` + `publish_url=https://...` pair on an MS-W4 row whose `recommended_bucket == "blocked"` is rejected — the lane stays blocked.

---

## 7. Residual Risks

- **RC PR-4 dependency** — the lane points the operator at "Delivery Center" for the publish action, but the Delivery Center's result-oriented readiness explanation (per-variation delivery bundle row + publish-hub backfill readiness) is RC PR-4 scope. Until RC PR-4 lands, the operator follows existing MS-W7/W8 surfaces and the existing PR-1 unified `publish_readiness` for the actual publish step. Acceptable per gate spec §5 ordering.
- **First-publishable selection semantic** — when multiple variants are in the `publishable_candidate` bucket, the lane picks the first one (the same ordering as MS-W4). An operator-driven "best version" selector is explicitly out of all RC scope per OWC-MS Closeout §8.
- **Closure store volatility** — same pre-existing OPS-GAP-2 baseline as RC PR-1 / RC PR-2; in-process closure store is volatile across gateway restart. Not introduced by this PR.
- **Pre-existing Python 3.9 PEP-604 baseline** — same 19 env-coupled test files block as RC PR-1 / RC PR-2; CI on 3.10+ exercises them.

---

## 8. What This PR Does NOT Do

- Does NOT advance any closeout signoff (OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, RC PR-1 / RC PR-2 closeouts — all stay independently pending).
- Does NOT open RC PR-4 — opens only after this PR merges + reviews per gate spec §5.
- Does NOT touch Hot Follow, Digital Anchor, Asset Supply, contracts, schemas, packets, samples, or new endpoints.
- Does NOT introduce a second authoritative producer for publishability, recommended version, advisories, or `final_provenance`.
- Does NOT synthesise any media URL or `final_video` placeholder; does not surface `publish_url` from the closure.
- Does NOT widen any closed enum (`RECOMMENDED_BUCKET_*` / `HEAD_REASON_LABELS_ZH` consumed verbatim).
- Does NOT couple Track A (Hot-Follow-only Plan A live-trial window) signoff to RC PR-3.
- Does NOT touch the Task Area surface — RC PR-3 is Workbench-only.
