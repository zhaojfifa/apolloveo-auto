# Plan E — Matrix Script UI Alignment PR-U2 (Workbench Comprehension) — Execution Log v1

Date: 2026-05-04
Branch: `claude/ui-u2-workbench-comprehension`
Base commit at audit: `9be6ed3` (`Merge pull request #105 from zhaojfifa/claude/ui-u1-task-area-comprehension` — PR-U1 Task Area comprehension merged)
Status: Implementation landed; per gate spec §6 row UA2-A.

Authority of execution:
- [docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md) §3 (allowed scope), §4 (forbidden scope), §5 (PR slicing), §7 (preserved freezes), §10 (gate-opening signoff completed 2026-05-04).
- User-mandated narrowing: gate spec §5 PR-UA1 → PR-UA6 collapsed to PR-U1 (Task Area; merged) → PR-U2 (Workbench, this PR) → PR-U3 (Delivery Center). PR-U2 covers Matrix Script Workbench information hierarchy + variation panel readability + next-step clarity by adding an additive comprehension block ABOVE the existing Matrix Script Variation Panel. The existing Axes / Cells × Slots / Slot detail / Attribution refs / Publish feedback projection sub-blocks are preserved verbatim.

---

## 1. Scope landed

| # | Surface | Operator-visible delta |
| --- | --- | --- |
| 1 | Matrix Script Workbench panel block in `task_workbench.html` | New "Matrix Script · 工作台理解" comprehension block ABOVE the existing Variation Panel: `四区对齐` header binding `content_structure` / `scene_plan` / `audio_plan` / `language_plan` zones to `line_specific_refs[].binds_to`; `任务身份` summary (axes / cells / slots counts + operator-language `ready_state` label); `下一步` block stating `此阶段无需操作 · Phase B 已自动生成` plus the §4.3 explanation; `变体概要` total counts; axis-tuple grouping readability hint that activates only when `cells > cell_grouping_threshold` (default 6). |
| 2 | Existing Matrix Script Variation Panel sub-blocks (Axes / Cells × Slots / Slot detail / Attribution refs / Publish feedback projection) | **Preserved verbatim** — no row removed, no field re-shaped, no §8.G item-access pattern weakened, no §8.E whitelist gate touched. |
| 3 | Hot Follow workbench panel | **Bytewise unchanged** — gated by the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` block boundary. |
| 4 | Digital Anchor workbench surfaces | **Bytewise unchanged** — Digital Anchor `panel_kind` is not `"matrix_script"` so the new block never renders. |
| 5 | Apollo Avatar workbench (`task_workbench_apollo_avatar.html`) | **Untouched** — separate template file. |

## 2. Files added

- [gateway/app/services/matrix_script/workbench_comprehension.py](../../gateway/app/services/matrix_script/workbench_comprehension.py) — pure-projection helper `derive_matrix_script_workbench_comprehension(variation_surface, line_specific_panel, *, cell_grouping_threshold=6)`. Reads `variation_surface.variation_plan.{axes, cells}`, `variation_surface.copy_bundle.slots`, `variation_surface.attribution_refs.line_specific_refs[].binds_to`, `variation_surface.readyState`, `variation_surface.publish_feedback_projection.ready_state`, and `line_specific_panel.{panel_kind, refs[]}`. Emits the comprehension bundle. Returns `{}` for non-Matrix-Script panel kinds.
- [gateway/app/services/tests/test_matrix_script_workbench_comprehension.py](../../gateway/app/services/tests/test_matrix_script_workbench_comprehension.py) — 28 import-light test cases covering: non-Matrix-Script panel returns empty (5 cases incl. `None`); missing inputs safe; four-zone alignment ordering + zone labels; `content_structure` ↔ `matrix_script_variation_matrix` binding; `language_plan` ↔ `matrix_script_slot_pack` binding; unbound zones render the empty sentinel without inventing a binding; zone lookup falls back to panel resolver refs when attribution list empty; task identity counts; `ready_state` translation across the closed enumerated set + unknown fallthrough + missing → `"—"`; `next_step_zone == "system"` and label/explanation cite §4.3; variation summary text matches counts; axis-tuple grouping disabled below threshold / enabled above with stable ordering / sample cap at 3 / handles empty axis_selections / threshold override; validator R3 alignment (no vendor / model / provider / engine identifier anywhere in the bundle, walked recursively); helper does not mutate inputs.

## 3. Files modified (Matrix Script-scoped only)

- [gateway/app/services/operator_visible_surfaces/wiring.py](../../gateway/app/services/operator_visible_surfaces/wiring.py) — added a single `bundle["workbench"]["matrix_script_comprehension"] = derive_matrix_script_workbench_comprehension(variation_surface, workbench_panel)` line inside the existing `if workbench_panel.get("panel_kind") == "matrix_script":` branch in `build_operator_surfaces_for_workbench`. Hot Follow / Digital Anchor / Baseline workbench surfaces never enter this branch. Import is local to the branch (lazy) to keep the cross-line import graph unchanged.
- [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) — inserted an additive `{% if ms_comp.is_matrix_script %} ... {% endif %}` block immediately AFTER the `ms_slot_index` Jinja set statements and BEFORE the existing `<div class="panel" data-role="matrix-script-variation-panel">`. The new block reads `ms_comp = ((ops.workbench or {}).matrix_script_comprehension or {})` and renders the four-zone alignment grid + identity summary + next-step block + variation summary + grouping hint. The existing Variation Panel block is preserved verbatim below.

## 4. Files NOT touched (binding under gate spec §4)

- Any Hot Follow file — gate spec §4.1 preserved.
- Any Digital Anchor file — gate spec §4.2 preserved.
- Any contract file under `docs/contracts/` — gate spec §4.8 preserved.
- Any schema file under `schemas/` — same.
- `gateway/app/services/matrix_script/workbench_variation_surface.py`, `phase_b_authoring.py`, `delivery_binding.py`, `create_entry.py`, `source_script_ref_minting.py`, `publish_feedback_closure.py`, `task_card_summary.py` — Matrix Script truth shapes from PR-1 / PR-2 / PR-3 / PR-U1 unchanged. Gate spec §4.3 (Matrix Script truth / scope creep) preserved.
- `gateway/app/services/operator_visible_surfaces/projections.py` — read-only consumed; no projection mutation. Gate spec §4.7 (no D1 / D2 / D3 / D4 producer) preserved.
- `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (does not exist; this PR does not create it) — gate spec §4.7 preserved.
- The §8.E whitelist gate `{% if task.kind == "hot_follow" %}` around the four Hot Follow-only template regions in `task_workbench.html` — verbatim preserved.
- The §8.G item-access pattern (`axis["values"]`) inside the Axes table — verbatim preserved.
- `gateway/app/templates/matrix_script_new.html` — owned by future entry-surface work; not touched.
- The Matrix Script Delivery Center surface — owned by PR-U3; not touched.
- The first-phase A7 closeout signoff at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §3 — gate spec §4.10 + §7.6 preserved; A7 paperwork remains intentionally pending and is **NOT** advanced by this PR.

## 5. Validation

- `python3 -m pytest gateway/app/services/tests/test_matrix_script_workbench_comprehension.py gateway/app/services/tests/test_matrix_script_task_card_summary.py -v` → **58/58 PASS** (28 new PR-U2 + 30 cross-PR sanity PR-U1) on local Python 3.9.6.
- Jinja parse check on `task_workbench.html` → **OK** (no template syntax error).
- Helper module direct import → **OK**.
- Broader chain that would import `gateway/app/config.py` blocks at collection on local Python 3.9 due to the pre-existing PEP-604 `str | None` syntax (documented across PR-1 / PR-2 / PR-3 / PR-U1 execution logs) — NOT caused by PR-U2; CI on Python 3.10+ runs the full chain.
- Hot Follow file isolation: `git diff --name-only` shows zero Hot Follow files touched.
- Digital Anchor file isolation: `git diff --name-only` shows zero Digital Anchor files touched.

## 6. Hot Follow + Digital Anchor preservation

- The new comprehension block sits inside `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` — Hot Follow workbenches (whose `panel_kind` is `"hot_follow"` or `None`) never reach the new block. Hot Follow's `Hot Follow panel` block at lines 449+ stays as-is; Hot Follow's deliverables / scenes / publish hub / debug logs blocks stay gated by the §8.E `{% if task.kind == "hot_follow" %}` whitelist.
- Digital Anchor `panel_kind` resolves to `"digital_anchor"` (or remains `None` on inspect-only flows); the new block never renders. The Plan A §2.1 hide guards on the Digital Anchor New-Tasks card click target + temp `/tasks/connect/digital_anchor/new` route remain in force.
- The cross-line `applyFilters()` JS on the Task Area page (PR-U1) is unaffected.

## 7. Acceptance evidence (gate spec §6 row UA2-A spirit, narrowed to Workbench comprehension)

| # | Acceptance row | Status | Evidence |
| --- | --- | --- | --- |
| UA2-A (four-zone alignment) | `content_structure / scene_plan / audio_plan / language_plan` zones render with operator-language labels and bind to `line_specific_refs[].binds_to` | PASS (static) | `test_four_zone_alignment_emits_all_four_zones_in_order`, `test_content_structure_zone_binds_variation_matrix`, `test_language_plan_zone_binds_slot_pack`, `test_unbound_zones_render_empty_label_without_inventing_binding`, `test_zone_lookup_falls_back_to_panel_refs_when_attribution_empty` |
| UA2-A (task identity) | Operator-language summary of axes / cells / slots counts + `ready_state` translation | PASS (static) | `test_task_identity_summary_counts_match_inputs` + 8 ready_state cases |
| UA2-A (next-step clarity) | "此阶段无需操作 · Phase B 已自动生成" + `next_step_zone == "system"` + §4.3 explanation | PASS (static) | `test_next_step_zone_is_system_and_label_says_no_action_required` |
| UA2-A (variation panel readability) | Variation summary text + axis-tuple grouping readability hint above threshold | PASS (static) | `test_variation_summary_text_matches_counts` + 4 grouping cases |
| HF-PRES (PR-U2) | Hot Follow workbench unchanged | PASS (file isolation + panel-kind gate) | `git diff --name-only` shows no Hot Follow files touched; new block sits inside `panel_kind == "matrix_script"` branch only |
| DA-PRES (PR-U2) | Digital Anchor freeze preserved | PASS (file isolation + panel-kind gate) | `git diff --name-only` shows no Digital Anchor files touched; Plan A §2.1 hide guards still in force |
| FORBID (PR-U2) | No gate spec §4 forbidden item landed | PASS | No contract mutation; no projection mutation; no D1 / D2 / D3 / D4 producer; no Asset Library; no promote service; no operator-driven Phase B authoring affordance (`next_step_zone == "system"` only); no `panel_kind` enum widening; no `ref_id` enumeration widening; no provider/model/vendor/engine identifier (covered by `test_bundle_carries_no_vendor_model_provider_engine_keys` walking the bundle recursively); no donor namespace import; no React/Vite footprint; no first-phase A7 signoff touched |

## 8. Final gate (PR-U2)

| # | Question | Verdict |
| --- | --- | --- |
| 1 | PR-U2 stayed inside workbench-only scope | **YES** — only `task_workbench.html` Matrix Script panel block, the Matrix Script-only branch in `wiring.py`, the new helper, and the new test were touched |
| 2 | Hot Follow baseline preserved | **YES** — file isolation; new block sits inside `panel_kind == "matrix_script"` gate; §8.E whitelist + §8.G item-access pattern preserved verbatim |
| 3 | Digital Anchor freeze preserved | **YES** — no Digital Anchor file touched; Plan A §2.1 hide guards in force |
| 4 | No vendor/model/provider controls introduced | **YES** — covered by recursive `test_bundle_carries_no_vendor_model_provider_engine_keys` |
| 5 | No contract-truth mutation | **YES** — no `docs/contracts/` or `schemas/` touched; no `panel_kind` enum widening; no `ref_id` enumeration widening; no `axis["values"]` weakening |
| 6 | Ready for PR-U3 next | **YES** — only Delivery Center comprehension remains; PR-U3 will open after PR-U2 merges |

PR-U3 (Delivery Center comprehension) remains pending and will be opened only **after** PR-U2 lands per the user-mandated sequence.

---

End of Plan E Matrix Script UI Alignment PR-U2 (Workbench Comprehension) — Execution Log v1.
