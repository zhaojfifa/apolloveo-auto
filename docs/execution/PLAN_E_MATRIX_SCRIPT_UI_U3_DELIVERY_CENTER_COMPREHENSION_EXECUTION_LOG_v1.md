# Plan E — Matrix Script UI Alignment PR-U3 (Delivery Center Comprehension) — Execution Log v1

Date: 2026-05-04
Branch: `claude/ui-u3-delivery-center-comprehension`
Base commit at audit: `9be6ed3` (`Merge pull request #105 from zhaojfifa/claude/ui-u1-task-area-comprehension` — PR-U1 merged; PR-U2 #106 opened but not yet merged at PR-U3 open time, so PR-U3 branches off latest `origin/main` for clean independent merge)
Status: Implementation landed; per gate spec §6 row UA4-A / UA5-A spirit (Delivery Center comprehension).

Authority of execution:
- [docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md) §3 (allowed scope), §4 (forbidden scope), §5 (PR slicing), §7 (preserved freezes), §10 (gate-opening signoff completed 2026-05-04).
- User-mandated narrowing: gate spec §5 PR-UA1 → PR-UA6 collapsed to PR-U1 (Task Area; merged) → PR-U2 (Workbench; opened) → PR-U3 (Delivery Center, this PR — final slice). PR-U3 covers the Matrix Script Delivery Center surface only — `final_video` primacy, `required` vs `scene_pack` zoning, publish-blocking explanation, historical-vs-current artifact separation. Hot Follow / Digital Anchor / Baseline publish hubs stay bytewise unchanged.

---

## 1. Scope landed

| # | Surface | Operator-visible delta |
| --- | --- | --- |
| 1 | Matrix Script publish hub at `task_publish_hub.html` (Matrix Script tasks only) | New "Matrix Script · 交付中心理解" comprehension card inside the deliverables tab, gated server-side by `task.kind == "matrix_script"`. Renders: `final_video` primacy block (visually highlighted, separated from structural rows); three operator-language lanes (`必交付 · 阻塞发布` / `必交付 · 不阻塞发布` / `可选 · 不阻塞发布`) with row counts and per-row `kind_label_zh` + `zoning_label_zh` + `artifact_status_label_zh`; publish-blocking explanation in operator language with the failing rows enumerated; explicit historical-vs-current explanation pinning the no-collapse invariant. |
| 2 | Hot Follow `task_publish_hub.html` and `hot_follow_publish.html` | **Bytewise unchanged**. The new block is gated `{% if _ms_kind == "matrix_script" %}` server-side; Hot Follow tasks render `hot_follow_publish.html` (separate template) and never reach the Matrix Script path. |
| 3 | Digital Anchor publish surfaces | **Bytewise unchanged**. Digital Anchor tasks fall through `task_publish_hub.html` but the Matrix Script-only block is gated by `kind == "matrix_script"` so the comprehension card never renders. |
| 4 | `publish_hub_payload(task)` for non-Matrix-Script kinds | **Bytewise unchanged** — additive `matrix_script_delivery_comprehension` key is attached only when `kind == "matrix_script"`. |

## 2. Files added

- [gateway/app/services/matrix_script/delivery_comprehension.py](../../gateway/app/services/matrix_script/delivery_comprehension.py) — pure-projection helper `derive_matrix_script_delivery_comprehension(delivery_binding)` reading the existing `matrix_script_delivery_binding_v1` projection emitted by `project_delivery_binding(packet)`. Emits the comprehension bundle with `final_video_primary` block, three classified lanes, publish-blocking explanation, history-vs-current explanation, and operator-language labels for every kind / zoning / artifact-status combination. Returns `{}` for non-Matrix-Script bindings or empty input.
- [gateway/app/services/tests/test_matrix_script_delivery_comprehension.py](../../gateway/app/services/tests/test_matrix_script_delivery_comprehension.py) — 20 import-light test cases covering: non-Matrix-Script surfaces / empty input return empty; surface-or-line_id recognition; `final_video` primary block presence; lane classification for variation_manifest / slot_bundle / scene_pack; subtitle / audio capability-flag-driven lane assignment; row counts; operator-language zoning labels; Chinese kind labels; `artifact_lookup` translation across `unresolved` / `current_fresh` / `historical` / `provenance.attempt_id`-only paths; publish-blocking under unresolved required rows; publish-unblocked when all required rows current_fresh; **historical required rows still block publish** (no fast path); validator R3 alignment via recursive walk; helper does not mutate input; section labels.

## 3. Files modified (Matrix Script-scoped only)

- [gateway/app/services/task_view_helpers.py](../../gateway/app/services/task_view_helpers.py) — converted the trailing `return { ... }` of `publish_hub_payload(task)` into a `payload = { ... }` dict + final `return payload`. Added a Matrix Script-only branch `if kind_value == "matrix_script":` that lazy-imports `project_delivery_binding` + `derive_matrix_script_delivery_comprehension` and attaches `payload["matrix_script_delivery_comprehension"]`. Hot Follow / Digital Anchor / Baseline publish hubs receive payload bytewise identical to pre-PR (the new key is absent on those payloads). Defense-in-depth `try/except` around the Matrix Script branch ensures comprehension errors never break the publish hub.
- [gateway/app/templates/task_publish_hub.html](../../gateway/app/templates/task_publish_hub.html) — inserted an additive `<div class="card" id="matrix-script-delivery-comprehension-block" data-role="matrix-script-delivery-comprehension" style="display:none;">` block at the top of `<div class="tab-panel" id="tab-deliverables">`, gated server-side by `{% if _ms_kind == "matrix_script" %}`. Added the JS function `renderMatrixScriptDeliveryComprehension(comp)` directly after `renderDeliverables` that populates the gated container from `data.matrix_script_delivery_comprehension`. Added one call to `renderMatrixScriptDeliveryComprehension(data.matrix_script_delivery_comprehension || null)` inside the existing `fetchPublishHub()` success path immediately after `renderDeliverables(data.deliverables || {})`. The renderer short-circuits when the gated container does not exist (Hot Follow / Digital Anchor / Baseline tasks) or when the payload key is absent.

## 4. Files NOT touched (binding under gate spec §4)

- Any Hot Follow file under `gateway/app/services/hot_follow_*`, `gateway/app/templates/hot_follow_*`, `gateway/app/routers/hot_follow_*`, `tasks.py` Hot Follow paths, `hot_follow_publish.html`, `hot_follow_workbench.html` — gate spec §4.1 + §7.1 preserved.
- Any Digital Anchor file under `gateway/app/services/digital_anchor/*`, `gateway/app/templates/digital_anchor*`, the formal `/tasks/digital-anchor/new` route, the temp `/tasks/connect/digital_anchor/new` route — gate spec §4.2 + §7.2 preserved.
- Any contract file under `docs/contracts/` — gate spec §4.8 preserved.
- Any schema file under `schemas/` — same.
- `gateway/app/services/matrix_script/delivery_binding.py` — Matrix Script truth shape from PR-3 unchanged. `_clamp_blocking_publish`, `SCENE_PACK_BLOCKING_ALLOWED`, the closed five-row deliverable set, the `artifact_lookup` discipline are all preserved verbatim.
- `gateway/app/services/matrix_script/{create_entry,phase_b_authoring,workbench_variation_surface,publish_feedback_closure,source_script_ref_minting}.py` — Matrix Script truth shapes from PR-1 / PR-2 / PR-3 unchanged. Gate spec §4.3 preserved.
- `gateway/app/services/operator_visible_surfaces/projections.py` — read-only consumed; no projection mutation. Gate spec §4.7 (no D1 / D2 / D3 / D4 producer) preserved.
- `gateway/app/services/operator_visible_surfaces/wiring.py` — untouched (not on the Delivery Center path).
- `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (does not exist; this PR does not create it).
- `gateway/app/templates/{tasks.html,task_workbench.html,matrix_script_new.html}` — Task Area + Workbench + entry surfaces are owned by PR-U1 / PR-U2 / future entry-form work; not touched by PR-U3.
- The first-phase A7 closeout signoff at [PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §3 — gate spec §4.10 + §7.6 preserved; A7 paperwork remains intentionally pending and is **NOT** advanced by this PR.

## 5. Validation

- `python3 -m pytest gateway/app/services/tests/test_matrix_script_delivery_comprehension.py -v` → **20/20 PASS** on local Python 3.9.6.
- Jinja parse check on `task_publish_hub.html` → **OK** (no template syntax error).
- Helper module direct import → **OK**.
- Broader chain that would import `gateway/app/config.py` blocks at collection on local Python 3.9 due to the pre-existing PEP-604 `str | None` syntax (documented across PR-1 / PR-2 / PR-3 / PR-U1 / PR-U2 execution logs) — NOT caused by PR-U3; CI on Python 3.10+ runs the full chain.
- Hot Follow file isolation: `git diff --name-only` shows zero Hot Follow files touched.
- Digital Anchor file isolation: `git diff --name-only` shows zero Digital Anchor files touched.

## 6. Hot Follow + Digital Anchor preservation

- Hot Follow tasks render `hot_follow_publish.html` (separate template; line 1565 in `tasks.py`); the Matrix Script comprehension block is in `task_publish_hub.html` only and is server-gated by `{% if _ms_kind == "matrix_script" %}`. Hot Follow publish hub renders bytewise as before.
- Digital Anchor tasks fall through `task_publish_hub.html` but the Matrix Script-only block is gated by the same `kind == "matrix_script"` check; the new block never renders for Digital Anchor and the `renderMatrixScriptDeliveryComprehension` JS function short-circuits at the container check (`if (!block) return;`).
- The `publish_hub_payload(task)` change is gated by `kind_value == "matrix_script"` so Hot Follow / Digital Anchor / Baseline payloads carry no `matrix_script_delivery_comprehension` key — bytewise unchanged.
- Plan A §2.1 hide guards on the Digital Anchor New-Tasks card click target + temp `/tasks/connect/digital_anchor/new` route remain in force.

## 7. Acceptance evidence (gate spec §6 row UA4-A / UA5-A spirit, narrowed to Delivery Center comprehension)

| # | Acceptance row | Status | Evidence |
| --- | --- | --- | --- |
| UA4-A (final_video primacy) | `final_video` rendered with visual primacy on the Matrix Script Delivery Center | PASS (static) | `test_final_video_primary_block_present_and_marked_primary` |
| UA4-A (required vs scene_pack zoning) | `必交付 · 阻塞发布` vs `必交付 · 不阻塞发布` vs `可选 · 不阻塞发布` zones rendered correctly | PASS (static) | `test_variation_manifest_and_slot_bundle_in_required_blocking_lane`, `test_scene_pack_always_in_optional_non_blocking_lane`, `test_subtitle_and_audio_required_status_follows_capability_flags`, `test_zoning_labels_for_each_combination`, `test_lane_row_counts_match` |
| UA4-A (operator-language labels) | Per-row Chinese labels translate from contract kind set | PASS (static) | `test_kind_labels_translate_to_chinese` |
| UA5-A (publish-blocking explanation) | When required+blocking row not current_fresh → operator-language `is_blocked=True` + naming the failing rows; otherwise `is_blocked=False` + 可启用 message | PASS (static) | `test_publish_blocked_when_required_blocking_row_unresolved`, `test_publish_unblocked_when_all_required_rows_current_fresh`, `test_historical_required_row_still_blocks_publish` |
| UA4-A (history vs current separation) | Historical and current artifacts kept in separate `artifact_status_code` lanes; explanation explicit about no-collapse invariant | PASS (static) | `test_historical_freshness_kept_separate_from_current`, `test_provenance_attempt_id_alone_classifies_historical`, `test_top_level_bundle_carries_all_section_labels` |
| HF-PRES (PR-U3) | Hot Follow publish hub unchanged | PASS (file isolation + template gate) | `git diff --name-only` shows no Hot Follow files touched; Hot Follow uses `hot_follow_publish.html`; new block is `{% if _ms_kind == "matrix_script" %}`-gated |
| DA-PRES (PR-U3) | Digital Anchor freeze preserved | PASS (file isolation + template gate) | `git diff --name-only` shows no Digital Anchor files touched; new block never renders for Digital Anchor (kind gate); Plan A §2.1 hide guards still in force |
| FORBID (PR-U3) | No gate spec §4 forbidden item landed | PASS | No contract mutation; no projection mutation (`project_delivery_binding` consumed read-only); no D1 unified `publish_readiness` producer; no D2 / D3 / D4; no Asset Library; no promote service; no operator-driven Phase B authoring; no `deliverable_id` enumeration widening; no `required` / `blocking_publish` field re-shape; no provider/model/vendor/engine identifier in bundle (covered by `test_bundle_carries_no_vendor_model_provider_engine_keys` walking recursively); no donor namespace import; no React/Vite footprint; no first-phase A7 signoff touched |

## 8. Final gate (PR-U3)

| # | Question | Verdict |
| --- | --- | --- |
| 1 | PR-U3 stayed inside delivery-center-only scope | **YES** — only `task_publish_hub.html` (Matrix Script-only block + JS), the Matrix Script-only branch in `publish_hub_payload`, the new helper, and its test |
| 2 | Hot Follow baseline preserved | **YES** — file isolation; Hot Follow uses separate `hot_follow_publish.html`; Matrix Script block server-gated |
| 3 | Digital Anchor freeze preserved | **YES** — no Digital Anchor file touched; new block never renders for Digital Anchor; Plan A §2.1 hide guards in force |
| 4 | No vendor/model/provider controls introduced | **YES** — covered by recursive `test_bundle_carries_no_vendor_model_provider_engine_keys` |
| 5 | No contract-truth mutation | **YES** — no `docs/contracts/` or `schemas/` touched; `delivery_binding.py` consumed read-only; no `deliverable_id` enumeration / row count change |
| 6 | Ready for UI-alignment phase closeout | **YES** — three narrow slices (PR-U1 / PR-U2 / PR-U3) cover Task Area / Workbench / Delivery Center comprehension; comprehension-phase closeout document `PLAN_E_MATRIX_SCRIPT_UI_ALIGNMENT_PHASE_CLOSEOUT_v1.md` may be authored after PR-U3 lands and PR-U2 merges. First-phase A7 closeout signoff remains independently pending. |

This is the **last** of the three narrow UI-alignment implementation slices per the user-mandated narrowing of gate spec §5 PR-UA1 → PR-UA6 to PR-U1 / PR-U2 / PR-U3. No fourth implementation PR is authorized under this gate spec; subsequent Plan E phases for Digital Anchor / Asset Library / promote services / L4 advisory producer / L3 `final_provenance` emitter / unified `publish_readiness` producer / workbench panel dispatch contract object / operator-driven Phase B authoring require their own future gate-spec authoring step.

---

End of Plan E Matrix Script UI Alignment PR-U3 (Delivery Center Comprehension) — Execution Log v1.
