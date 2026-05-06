# RC PR-2 Execution Log — Matrix Script Result-Capability Recovery (RC-R1 + R2 + R3)

Date: 2026-05-06
Status: Implementation green; PR open. Engineering only — operator-comprehension demonstration (RC-A5) recorded in §6 below.
Wave: ApolloVeo 2.0 Matrix Script Result-Capability Recovery Wave (Track B).
Phase: RC PR-2 — Operator-readable script / variant candidate package.
Authority: [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) §3 RC-R1..R3 + §5 RC PR-2.

---

## 1. Reading Declaration

Authority files read before authoring this implementation, in `CLAUDE.md` §2 boot order:

1. `CLAUDE.md` — bootloader.
2. `ENGINEERING_RULES.md` — engineering governance, §13 Product-Flow Module Presence.
3. `CURRENT_ENGINEERING_FOCUS.md` — current-stage preamble.
4. `ENGINEERING_STATUS.md` — head completion log.
5. `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` (binding scope).
6. `docs/product/matrix_script_product_flow_v1.md`.
7. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`.
8. RC PR-1 substrate: `result_status_view.py` execution log + helper signature.

Surface mapped via existing OWC-MS PR-2 helpers (`script_structure_view.py` for section derivation logic; `preview_compare_view.py` for `diff_hints`; `phase_b_authoring.py` for closed `TONES` / `AUDIENCES` / `LENGTH_PICKS` axis enums) and the MS-W7 forbidden-token scrub in `delivery_copy_bundle_view.py`. No second producer introduced.

---

## 2. RC-R / RC-A Scope Covered

### 2.1 RC-R items in scope (this PR only)

- **RC-R1 — operator-readable script output.** Per-variation Hook / Body / CTA text rendered as readable strings derived from already-resolved `task["config"]["entry"]` content + the deterministic Phase B cells / slots. When a section's underlying source has no signal, it renders the closed `unresolved_pending_outline_contract` sentinel — never a synthesised placeholder.
- **RC-R2 — Hook / Body / CTA structure preserved.** Each per-variation card always carries three section rows in the canonical order (`hook` → `body` → `cta`); empty sections render the closed sentinel from MS-W3; structure is never collapsed. Asserted by `test_each_variant_has_three_readable_sections_in_order`.
- **RC-R3 — multi-variant candidate one-line summary.** Per-variation `axis_summary_zh` exposes the localized axis selections + length hint. Per-variation `differentiator_zh` names only the axes that differ from the invariant set (consumed verbatim from the existing MS-W4 `diff_hints` — single source).

### 2.2 RC-R items explicitly NOT in scope (per gate spec §5 ordering)

- RC-R4 — recommended-version actionable lane (RC PR-3).
- RC-R5, RC-R7, RC-R8 — delivery-ready package + publish/backfill readiness + no-fake-`final_video` Delivery audit (RC PR-4). RC PR-2 already enforces the "no fake `final_video`" discipline locally via test (forerunner of RC-A6).
- RC-R6 — already shipped by RC PR-1 (substrate).

### 2.3 Acceptance rows targeted by this PR

- **RC-A2** — RC PR-2 implementation green and merged. Evidence: this execution log + diff + PR # + squash commit (recorded by Closeout when paperwork lands).
- **RC-A5 (this PR's slice)** — operator-comprehension demonstration in §6 below.
- Forbidden-scope audit rows (RC-A6 / RC-A7 / RC-A8 / RC-A9 / RC-A10 / RC-A11 / RC-A12) per-PR audit recorded in §4 below.

---

## 3. Files Changed

| File | Kind | Purpose |
| --- | --- | --- |
| `gateway/app/services/matrix_script/readable_variant_view.py` | new | RC-R1+R2+R3 helper: `derive_matrix_script_readable_variants(task, variation_surface, line_specific_panel, *, preview_compare)`. Closed `TONE_LABELS_ZH` + `AUDIENCE_LABELS_ZH` localization tables (cover every `phase_b_authoring` enum value verbatim). Per-variation Hook / Body / CTA derivation reuses MS-W3's section status closed enum (`STATUS_RESOLVED` / `STATUS_UNRESOLVED`); per-variation summary + differentiator built from cell axis_selections + slot_pack truth. Forbidden-token scrub mirrors MS-W7 verbatim. |
| `gateway/app/services/operator_visible_surfaces/wiring.py` | edit | Inside the existing `panel_kind == "matrix_script"` branch, adds `bundle["workbench"]["matrix_script_readable_variants"]` after `matrix_script_preview_compare` so `preview_compare.diff_hints` are available as input. No second producer call. |
| `gateway/app/templates/task_workbench.html` | edit | New `data-role="matrix-script-readable-variants-panel"` block inserted between MS-W4 (preview compare) and MS-W5 (review zone), strictly inside the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate. |
| `gateway/app/services/tests/test_matrix_script_readable_variant_view.py` | new | 46 dedicated import-light cases (gate spec §5.2 ≥35 floor: PASS at 1.3×). |
| `docs/execution/APOLLOVEO_2_0_RC_PR2_READABLE_SCRIPT_AND_VARIANTS_EXECUTION_LOG_v1.md` | new | This log. |
| `docs/execution/apolloveo_2_0_evidence_index_v1.md` | edit | New evidence row. |

`task_router_presenters.py` was NOT touched — RC PR-2 delivers a Workbench-only surface; the Task Area card stays at the RC PR-1 result-oriented summary level.

---

## 4. Forbidden-Scope Audit (per PR; full audit at Closeout)

| Sub-section | Verdict | Notes |
| --- | --- | --- |
| §4.1 Truth-source / contract preservation | PASS | No new contract. No closed-enum widening. The new helper consumes existing variation surface + entry truth + the existing MS-W4 `diff_hints` verbatim. Section status uses the closed `STATUS_RESOLVED` / `STATUS_UNRESOLVED` codes already authored by MS-W3. No new packet truth. |
| §4.2 Cross-line preservation | PASS | `git diff --stat` touches only matrix_script-gated branches and one new helper module under `gateway/app/services/matrix_script/`. Zero `hot_follow*`, zero `digital_anchor*`, zero `gateway/app/services/asset/`, zero `docs/contracts/`, zero `schemas/` paths. |
| §4.3 Wave-position preservation | PASS | No Platform Runtime Assembly. No Capability Expansion. No Plan A live-trial reopen. No new operator-eligible discovery surface. |
| §4.4 Scope-boundary preservation | PASS | No new structural surface module — the new panel reframes existing Phase B truth into a readable view; it does not author MS-W9 or wider. No OWC-MS re-litigation; the eight already-merged modules stay rendered. No vendor / model / provider / engine identifiers (asserted by parametrized scrub tests). No donor namespace import. No React / Vite rebuild. No durable persistence. |
| §4.5 Closeout-paperwork independence | PASS | No coupling to OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, Track A signoff, or RC PR-1 Closeout. |

### 4.1 No-fake-`final_video` discipline (RC-A6 forerunner)

The helper renders no media URL, no `https://` / `http://` / `.mp4` / `.mov` / `final_video_url` / `preview_url` / `publish_url` substring. Asserted by `test_no_fake_final_video_in_payload`. Per-variation `slot_body_ref` is the upstream-stored opaque `content://` handle — never dereferenced; the panel emits an explicit operator-language note (`脚本来源是 opaque 句柄；当前阶段不解引用句柄正文`).

### 4.2 No-second-truth-source discipline (RC-A7 forerunner)

The helper signature is `(task, variation_surface, line_specific_panel, *, preview_compare)` — there is no `publish_readiness` parameter. The differing-axes set is consumed verbatim from MS-W4 `diff_hints`; the helper does not re-derive it. Asserted by `test_helper_does_not_call_publish_readiness`, `test_helper_does_not_call_compute_publish_readiness`, and `test_helper_signature_only_takes_documented_inputs`.

### 4.3 No-vendor / model leakage discipline (RC-A8 forerunner)

The helper's `_scrub_forbidden` mirrors `delivery_copy_bundle_view._scrub_forbidden` and applies to every entry-derived string before it reaches the operator-visible payload (topic, target_platform). When a forbidden token is present, the section falls back to the unresolved sentinel rather than emitting a sanitised partial value. Asserted by parametrized `test_forbidden_token_scrub_drops_vendor_strings_in_topic` + `test_forbidden_token_scrub_drops_vendor_strings_in_target_platform` + `test_no_vendor_or_model_strings_in_payload`.

---

## 5. Tests Run

- New file: `test_matrix_script_readable_variant_view.py` — **46 PASS / 0 FAIL** (gate spec §5.2 ≥35 floor: PASS at 1.3×).
- Adjacent matrix_script regression: **485 PASS / 0 FAIL** across `test_matrix_script_readable_variant_view.py`, `test_matrix_script_result_status_view.py` (RC PR-1 substrate intact), `test_matrix_script_task_area_convergence.py`, `test_matrix_script_qc_diagnostics_view.py`, `test_matrix_script_review_zone_view.py`, `test_matrix_script_preview_compare_view.py`, `test_matrix_script_workbench_comprehension.py`, `test_matrix_script_script_structure_view.py`, `test_matrix_script_closure_binding.py`, `test_publish_readiness_unified_producer.py`.
- Cross-line preservation: included in the 485 above — `test_digital_anchor_task_area_convergence.py`, `test_matrix_script_delivery_backfill_view.py`, `test_matrix_script_delivery_copy_bundle_view.py`, `test_matrix_script_delivery_comprehension.py`, `test_matrix_script_delivery_zoning.py`, `test_publish_readiness_surface_alignment.py`.
- Pre-existing Python 3.9 PEP-604 baseline at `gateway/app/config.py:43` continues to block the same 19 env-coupled test files from collection (recorded in OWC-MS / OWC-DA Closeout §8 + RC PR-1 execution log §5 + ENGINEERING_RULES §10). Not introduced by this PR.

---

## 6. Operator-Comprehension Demonstration (RC-A5 — this PR's slice)

The five required outcomes from the user mission:

1. **Operator-readable script output (RC-R1)** — sample task with `topic = "春季新品上线"`, `target_platform = "tiktok"`, two Phase B cells (`tone=casual` / `tone=playful`, both `audience=b2c`, `length=60`): the per-variation Hook reads `主题：春季新品上线 · 语气：轻松（casual） · 目标受众：面向消费者（b2c）`. Real readable text, not sentinel placeholders.

2. **Readable Hook / Body / CTA structure (RC-R2)** — every per-variation card has exactly three section rows in canonical order. Sentinel rendered when source absent (e.g. empty `topic` → `unresolved_pending_outline_contract` for Hook, with operator-language gating reason).

3. **Multiple variant candidates in operator language (RC-R3)** — variant card 1 reads `cell_001 · 语气=轻松（casual） · 受众=面向消费者（b2c） · 时长=60s`; variant card 2 reads `cell_002 · 语气=俏皮（playful） · 受众=面向消费者（b2c） · 时长=60s`. Operator can compare without opening either variant.

4. **Differences between variants understandable (RC-R3)** — variant card 1 differentiator reads `差异轴 · tone=轻松（casual）`; variant card 2 reads `差异轴 · tone=俏皮（playful）`. The shared invariant axes (`audience`, `length`) are not repeated in the differentiator — operator sees only what changed.

5. **No fake `final_video` and no fake delivery claims** — the panel emits an explicit operator-language note (`本面板不展示 final_video / 媒体链接 / 交付包就绪状态。RC-R5 / RC-R7 / RC-R8 ... 由 RC PR-4 覆盖。`), `slot_body_ref` is rendered as the opaque `content://` handle with the "不解引用句柄正文" note, and no publish status / publish url is surfaced. Asserted by tests.

---

## 7. Residual Risks

- **RC PR-3 dependency** — the recommended-version actionable lane is RC PR-3 scope; until that lands, the operator can read variants and compare them, but the "which one to pick" decision is still framed by the existing MS-W4 recommended marker. Acceptable per gate spec §5 ordering.
- **Phase B determinism** — `tone` / `audience` / `length` axis selections are deterministic per the §8.C addendum; the readable variants depend on this determinism. If a future variation matrix authoring path changes the axis emission shape (forbidden by gate spec §4.1 within this wave), the localization layer falls through verbatim (asserted by `test_unknown_axis_value_renders_raw_string_via_summary`).
- **Opaque `slot_body_ref`** — the "readable" Body section is structural (target time + tone + slot id + canonical Hook→Body→CTA structure) rather than the actual slot body text, because slot bodies remain opaque `content://` handles per §8.F (gate-locked). Operator readability of the actual body text is gated to a future Outline Contract authoring step (out of all RC scope). The panel surfaces this constraint explicitly via the `slot_body_ref_note_zh` line.
- **Forbidden-token scrub is substring-based** — same baseline as MS-W7; legitimate captions containing English nouns like "vendor" can be stripped. Acknowledged out-of-scope per OWC-MS Closeout §8.
- **Pre-existing Python 3.9 PEP-604 baseline** — same 19 env-coupled test files block as RC PR-1; CI on 3.10+ exercises them.

---

## 7.1 Conditional-Pass Corrections (2026-05-06)

The first PR-150 review returned **CONDITIONAL PASS** with two blockers; both are now closed in this PR (no scope widening, RC PR-2 boundary preserved):

### Blocker 1 — Raw internal handles removed from operator-visible surface

- The helper output dict no longer carries `script_slot_ref`, `slot_body_ref`, or `slot_body_ref_note_zh` keys. Variant identity is the `variation_id` only.
- Two new operator-language fields replace the raw handles: `has_bound_slot: bool` (machine-readable presence flag) + `bound_slot_label_zh` (operator-visible string `"已绑定脚本片段（正文为 opaque 句柄，本面板不展开正文）"` or `"尚未绑定脚本片段"`). The opacity rationale is exposed via `slot_body_opacity_note_zh` which itself names neither slot ids nor `content://`.
- The Workbench template no longer renders `variant.script_slot_ref` / `variant.slot_body_ref` / the literal labels `script_slot_ref：` / `body_ref：`. The replacement anchor is `data-role="ms-readable-variant-slot-bound"` rendering only the operator-language label + opacity note.
- Variant differences remain operator-understandable: the per-variant card carries the variant id (`变体 cell_001`), the localized one-line axis summary (`语气=轻松（casual） · 受众=面向消费者（b2c） · 时长=60s`), the differentiator (`差异轴 · tone=轻松（casual）`), and the structural Body. None of these expose internal handles.

### Blocker 2 — Body section reframed honestly with three-state distinction

- New view-layer status code `STATUS_STRUCTURAL_ONLY = "structural_summary_only"` introduced **inside this helper module** (presentation-only; not a contract enum, not a closed-enum widening of any packet / contract surface — gate spec §4.1 preserved).
- The per-variation Body section now returns `STATUS_STRUCTURAL_ONLY` whenever at least one structural signal is present (length / tone / bound slot); the closed `STATUS_UNRESOLVED` sentinel applies when no signal is present. The shared Body is also re-coded `STATUS_STRUCTURAL_ONLY` (the prior `STATUS_RESOLVED` claim was misleading because the shared Body always describes the canonical structure, not real resolved body text).
- Honest operator-language label `STATUS_STRUCTURAL_ONLY_LABEL_ZH` reads: `"结构性占位（slot 正文为 opaque 句柄；本字段展示目标时长 + 语气 + slot 结构摘要，非可读正文；待 Outline Contract / 句柄解引用上线后补齐）"`. Operator can read the label and learn (a) this is a placeholder, (b) why (opaque handle), (c) what would unblock real readability (Outline Contract / handle dereference).
- The raw slot id is also removed from the structural Body text itself: previously `"slot=slot_001"`, now `"已绑定脚本片段（正文为 opaque 句柄，本面板不展开）"`. Asserted by `test_per_variation_body_is_structural_only_with_length_and_tone` (`assert "slot_001" not in body["body_text"]`).
- Three-state operator distinction in templates:
  - `data-status-code="resolved_from_source_content"` → renders inside `data-role="ms-readable-variant-section-readable"` / `ms-readable-shared-section-readable` (real readable text).
  - `data-status-code="structural_summary_only"` → renders inside `data-role="ms-readable-variant-section-structural"` / `ms-readable-shared-section-structural` (structural placeholder + honest label).
  - else → renders inside `data-role="ms-readable-variant-section-unresolved"` / `ms-readable-shared-section-unresolved` (closed tracked-gap sentinel).
- Asserted by new tests `test_three_state_distinction_in_per_variation_sections`, `test_three_state_distinction_when_topic_and_platform_missing`, `test_body_unresolved_when_no_structural_signals`, `test_template_renders_three_section_states_distinctly`.

### Updated test coverage

- 10 new tests added on top of the original 46 (total **56 PASS / 0 FAIL**, gate spec §5.2 ≥35 floor: PASS at 1.6×):
  - `test_variant_dict_does_not_expose_raw_slot_identifiers`
  - `test_variant_dict_does_not_carry_content_scheme_strings`
  - `test_each_variant_has_bound_slot_boolean_and_label`
  - `test_unbound_slot_renders_unbound_label`
  - `test_each_variant_carries_opacity_note` (rewritten — formerly checked the now-removed raw-ref note)
  - `test_three_state_distinction_in_per_variation_sections`
  - `test_three_state_distinction_when_topic_and_platform_missing`
  - `test_body_unresolved_when_no_structural_signals`
  - `test_structural_only_status_label_is_honest_about_opaque_handle`
  - `test_no_raw_slot_or_body_ref_anywhere_in_payload`
  - `test_template_does_not_render_raw_handles`
  - `test_template_renders_three_section_states_distinctly`
- Two existing tests rewritten to assert the new honest framing: `test_shared_body_is_structural_only_with_canonical_structure` (was `test_shared_body_resolves_unconditionally_with_canonical_structure`) and `test_per_variation_body_is_structural_only_with_length_and_tone` (was `test_per_variation_body_includes_length_and_tone_when_present`).
- Adjacent + cross-line preservation regression: **495 PASS / 0 FAIL** across 16 import-light suites.

### Scope preservation (corrections only, no widening)

- Still RC-R1 / RC-R2 / RC-R3 only.
- No RC PR-3 recommended-version actionable lane.
- No RC PR-4 delivery-ready package / publish-backfill expansion.
- No fake `final_video` (already enforced; corrections preserve it).
- No second truth source (helper signature unchanged; still no `publish_readiness` parameter).
- No contract / schema mutation. The new `STATUS_STRUCTURAL_ONLY` is a presentation-layer view code local to this helper; it is NOT added to MS-W3's closed `STATUS_RESOLVED`/`STATUS_UNRESOLVED` enum (which remains untouched at `script_structure_view.py`).
- No Hot Follow / Digital Anchor / Asset Supply / runtime / provider/model UI touched.

---

## 8. What This PR Does NOT Do

- Does NOT advance any closeout signoff (OWC-MS MS-A7, OWC-DA DA-A7, Plan E A7 / UA7 / RA7, RC PR-1 closeout — all stay independently pending).
- Does NOT open RC PR-3 / RC PR-4 — those open sequentially per gate spec §5 ordering, each only after its predecessor merges and reviews.
- Does NOT touch Hot Follow, Digital Anchor, Asset Supply, contracts, schemas, packets, samples, or new endpoints.
- Does NOT introduce a second authoritative producer for publishability, recommended version, advisories, or `final_provenance`.
- Does NOT synthesise any media URL or `final_video` placeholder; does not dereference the opaque `content://` slot handle.
- Does NOT couple Track A (Hot-Follow-only Plan A live-trial window) signoff to RC PR-2.
- Does NOT touch the Task Area surface — Task Area stays at the RC PR-1 result-oriented summary level; readable variants are a Workbench-only addition.
