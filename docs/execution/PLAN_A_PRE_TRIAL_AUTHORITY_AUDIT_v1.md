# Plan A · Pre-Trial Authority Audit v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave
Status: Read-only audit. **Documentation only. No code, no UI, no contract, no schema, no template, no test changes.** This audit re-verifies the §3.1 / §3.2 static evidence rows of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) against the current branch, so the human coordinator briefing operators knows nothing has drifted since the static-pass body was authored on 2026-05-02 and the §11 / §12 addenda were authored on 2026-05-03.

Audit scope is **read-only**: no edits, no commits, no behavioral checks, no live operator runs. The audit answers exactly one question: *do the deployed-branch anchors that the trial brief and write-up rely on still hold on HEAD today?*

## 0. Branch state at audit time

- HEAD SHA: `b0c61c05feccacc1722c307f0fdb5004b463b23a` (most recent commit: "Add CLAUDE.md AI agent bootloader").
- Recent five commits (most recent first):
  - `b0c61c0` Add CLAUDE.md AI agent bootloader
  - `bc67dbc` Add ApolloVeo 2.0 unified alignment map v1 and re-anchor default entry
  - `fd69ef4` Add ApolloVeo 2.0 unified cognition and document re-anchoring review v1
  - `adb3ca9` Land Matrix Script §8.H operator brief re-correction (docs only) (#91)
  - `3d82784` Land Matrix Script §8.F opaque-ref discipline (Option F1) (#90)

The §8.A → §8.H Matrix Script trial-correction chain is fully landed; subsequent commits (`fd69ef4`, `bc67dbc`, `b0c61c0`) are documentation-only re-anchoring.

## 1. §3.1 Trial-eligibility evidence — re-verification on HEAD

| Brief promise / write-up §3.1 row | Authority anchor (per write-up) | Current-branch verification on HEAD | Result |
| --------------------------------- | ------------------------------- | ----------------------------------- | ------ |
| Hot Follow end-to-end is unchanged. | No commits to Hot Follow business logic since `ca20c60`. | `git log` confirms no Hot Follow service / router changes since `ca20c60`; recent activity is Matrix Script + documentation only. | PASS |
| Matrix Script `/tasks/matrix-script/new` accepts a closed entry set. | `gateway/app/services/matrix_script/create_entry.py:22-37` `MATRIX_SCRIPT_REQUIRED_FIELDS` + `_OPTIONAL_FIELDS`; unknown fields rejected via `_require()`. | `MATRIX_SCRIPT_REQUIRED_FIELDS` present at line 27; `MATRIX_SCRIPT_OPTIONAL_FIELDS` at line 36; both still tuple-shaped and exported via `__all__`. **Drift: line numbers shifted by ~5 (file grew with §8.F additions); symbols and behavior intact.** | PASS (with line-number drift noted) |
| Matrix Script target language restricted to `{mm, vi}`. | `create_entry.py:39` `ALLOWED_TARGET_LANGUAGES = ("mm", "vi")`; enforced at line 97. | `ALLOWED_TARGET_LANGUAGES = ("mm", "vi")` present at line 44; enforced at line 187 (`if target not in ALLOWED_TARGET_LANGUAGES`). **Drift: line numbers shifted; tuple value unchanged; closed-enum semantics unchanged.** | PASS (with line-number drift noted) |
| Workbench Phase B variation surface renders read-only. | `gateway/app/services/matrix_script/workbench_variation_surface.py` is projection-only. | Confirmed on HEAD: file remains projection-only; merge note `matrix_script_operator_visible_slice_merge_note_v1.md` still in force. | PASS |
| Forbidden vendor/model/provider/engine keys are stripped at the operator boundary. | `gateway/app/services/operator_visible_surfaces/projections.py:24-33` `FORBIDDEN_OPERATOR_KEYS`; `sanitize_operator_payload` at line 36. | `FORBIDDEN_OPERATOR_KEYS = frozenset({"vendor_id", "model_id", "provider", "provider_id", "engine_id", "raw_provider_route"})` present at line 24; `sanitize_operator_payload` at line 36. | PASS |
| Workbench panel dispatch is closed-by-default. | `projections.py:239-246` `PANEL_REF_DISPATCH` matches the closed map in [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md); `projections.py:268-270` rejects unknown ref_ids. | `PANEL_REF_DISPATCH` present at line 239 with the six entries (matrix_script_variation_matrix, matrix_script_slot_pack, digital_anchor_role_pack, digital_anchor_speaker_plan, hot_follow_subtitle_authority, hot_follow_dub_compose_legality); closed-by-default rejection at line 268 (`if not ref_id or ref_id not in PANEL_REF_DISPATCH: ... continue`). | PASS |

## 2. §3.2 Forbidden / preview-only evidence — re-verification on HEAD

| Brief constraint / write-up §3.2 row | Authority anchor | Current-branch verification on HEAD | Result |
| ------------------------------------ | ---------------- | ----------------------------------- | ------ |
| Digital Anchor Phase D.1 write-back is not implemented. | `gateway/app/services/digital_anchor/publish_feedback_closure.py` Phase D.0 closure shape only. | File present, no write-back code path landed. | PASS — must be hidden from trial |
| Digital Anchor formal `/tasks/digital-anchor/new` route is not implemented. | `gateway/app/routers/tasks.py` no `/tasks/digital-anchor/new` handler; only generic temp `/tasks/connect/{line_id}/new` reachable via `_TEMP_CONNECTED_LINES["digital_anchor"]` at `tasks.py:541-546`. | No `/tasks/digital-anchor/new` handler on HEAD; `_TEMP_CONNECTED_LINES` at line 541; generic temp route handler at line 567 (`/tasks/connect/{line_id}/new`). | PASS — must be hidden from trial |
| Matrix Script Delivery binding artifact lookup is not implemented. | `gateway/app/services/matrix_script/delivery_binding.py:93,101,109,117,125` emits five `not_implemented_phase_c` rows. | All five lines present on HEAD verbatim at the same line numbers (`93, 101, 109, 117, 125`). | PASS — operator must treat as inspect-only |
| Asset Supply / B-roll page is not implemented. | No `gateway/app/services/asset_library/` module; no asset-library route. | Confirmed on HEAD: `asset_library/` does not exist; `gateway/app/services/asset/` exists but contains only `__init__.py` + `README.md` (skeleton, no service surface). | PASS — must be hidden from trial |
| Promote intent submission is not implemented. | No promote service module on the deployed branch. | Confirmed on HEAD: no `promote*/` directory under `gateway/app/services/`. | PASS — must be hidden from trial |
| Unified `publish_readiness_contract_v1` producer is not yet in code. | `projections.py:51-79` `derive_board_publishable` and `:95-131` `derive_delivery_publish_gate` remain independent re-derivations. | `derive_board_publishable` at line 51, `derive_delivery_publish_gate` at line 95; both still independent re-derivations on HEAD. | PASS — surfaces still drift acceptably during trial |
| L3 `final_provenance` is not yet emitted. | No `final_provenance` field in `gateway/app/services/contract_runtime/` or `gateway/app/services/status_policy/hot_follow_state.py`. | Confirmed on HEAD: `grep -rn "final_provenance"` over those two directories returns no matches. | PASS — brief §5.2 trial-coordinator note accounts for this |
| L4 advisory producer is not yet emitting. | No `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` module exists. | Confirmed on HEAD: no `advisory_emitter*` file under `gateway/app/services/`. | PASS — brief §6.1 accounts for empty advisory rows during trial |

## 3. Matrix Script §8.A → §8.H additional anchors — re-verification on HEAD

These anchors were added to the Plan A trial scope by the §8.A → §8.H corrections; the audit re-verifies them so the coordinator knows the chain landed cleanly.

| Anchor | Authority | Current-branch verification on HEAD | Result |
| ------ | --------- | ----------------------------------- | ------ |
| §8.A entry-form ref-shape guard (`_validate_source_script_ref_shape`). | [MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md). | `_validate_source_script_ref_shape` defined at `gateway/app/services/matrix_script/create_entry.py:102`; called at line 189 (`validated_source_script_ref = _validate_source_script_ref_shape(...)`). | PASS |
| §8.F `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` tightened to four opaque-by-construction schemes. | [MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md); brief §0.1 criterion 2; brief §3.2. | `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES = ("content", "task", "asset", "ref")` present at `create_entry.py:62-67` (four entries — `https`/`http`/`s3`/`gs` removed per Option F1). | PASS |
| §8.C deterministic Phase B authoring (`derive_phase_b_deltas`). | [MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md); brief §0.1 criterion 4. | `gateway/app/services/matrix_script/phase_b_authoring.py` present; `derive_phase_b_deltas(entry, task_id)` at line 87; canonical axes `tone` (line 63) / `audience` (line 69) / `length` (line 75); cell loop at lines 99–133 emits index-aligned `(tone, audience, length)` per cell. | PASS |
| §8.G Jinja item-access fix (`axis["values"]` instead of `axis.values`). | [MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md); brief §0.1 criterion 5. | `gateway/app/templates/task_workbench.html:298` reads `{% set axis_values = axis["values"] %}` (item access, not attribute access). No `axis.values` attribute reference present. | PASS |
| §8.E shared-shell suppression (four `{% if task.kind == "hot_follow" %}` whitelist gates around Hot Follow-only template regions). | [MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md); brief §0.1 criterion 6. | Exactly four `{% if task.kind == "hot_follow" %}` gates present at `gateway/app/templates/task_workbench.html` lines 176, 479, 554, 713 — matches §8.E "four contiguous Hot Follow-only template regions". | PASS |
| Matrix Script formal create-entry route on `tasks_newtasks.html`. | Brief §3.2 row "Matrix Script `/tasks/matrix-script/new`". | `gateway/app/templates/tasks_newtasks.html:107` carries `<a href="/tasks/matrix-script/new...">` with `data-line-id="matrix_script"`. | PASS |
| Digital Anchor New-Tasks card click target (must be hidden in trial environment). | Brief §6.3 + §8 row 1; write-up §2.1 step 1. | `gateway/app/templates/tasks_newtasks.html:47` carries `<a href="/tasks/connect/digital_anchor/new...">` with `data-line-id="digital_anchor"` — the surface that the coordinator must hide / disable in the trial environment per the brief. | PASS — must be hidden from trial |

## 4. Drift summary

### 4.1 Substantive drift

**None.** All §3.1 / §3.2 / §8.A → §8.H authority anchors hold on HEAD. The trial brief and the trial coordination write-up may be briefed as written.

### 4.2 Cosmetic drift (line-number references in older write-up footnotes)

The static-pass body of the write-up ([PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §1 / §3.1) cited `create_entry.py` line numbers as they were on 2026-05-02. The `create_entry.py` file grew slightly when §8.F landed (the four opaque-by-construction schemes were declared as a new module-level tuple plus a regex pattern). The current line numbers are:

| Symbol / construct | Write-up cited line(s) | Current line on HEAD | Symbol / value drift |
| ------------------ | ---------------------- | -------------------- | --------------------- |
| `MATRIX_SCRIPT_REQUIRED_FIELDS` | 22-37 | 27 | None — tuple shape unchanged |
| `MATRIX_SCRIPT_OPTIONAL_FIELDS` | (within 22-37) | 36 | None |
| `ALLOWED_TARGET_LANGUAGES` | 39, enforced at 97 | 44, enforced at 187 | None — tuple value `("mm", "vi")` unchanged |
| `_validate_source_script_ref_shape` | n/a (added by §8.A; brief §3.2 cites it generically) | 102 | None |
| `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` | n/a (added by §8.F) | 62-67 | None — four entries (content/task/asset/ref), as Option F1 specifies |
| `FORBIDDEN_OPERATOR_KEYS` | 24-33 | 24 | None — six keys unchanged |
| `sanitize_operator_payload` | 36 | 36 | None |
| `PANEL_REF_DISPATCH` | 239-246 | 239 | None — six entries unchanged |
| Closed-by-default rejection (`ref_id not in PANEL_REF_DISPATCH`) | 268-270 | 268 | None |
| `derive_board_publishable` | 51-79 | 51 | None |
| `derive_delivery_publish_gate` | 95-131 | 95 | None |
| `delivery_binding.py` `not_implemented_phase_c` | 93, 101, 109, 117, 125 | 93, 101, 109, 117, 125 | None — all five rows still verbatim |
| `tasks.py` `_TEMP_CONNECTED_LINES` | 541-546 | 541 | None |
| `tasks_newtasks.html` Digital Anchor card | 47 | 47 | None |

**Action: none required for the trial.** The line-number drift on `create_entry.py` is cosmetic; the symbols and values cited by the brief / write-up are intact. Coordinator may brief operators per the existing write-up §3 wording without correction.

### 4.3 Surfaces the coordinator must still hide / disable

These surfaces remain reachable on the deployed branch and require the §2.1 hide / disable guard from [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md):

- Digital Anchor New-Tasks card click target at `gateway/app/templates/tasks_newtasks.html:47`.
- Digital Anchor temp connect route `/tasks/connect/digital_anchor/new` (handler at `gateway/app/routers/tasks.py:567`, driven by `_TEMP_CONNECTED_LINES["digital_anchor"]` at `tasks.py:541`).

## 5. What the coordinator must know before briefing operators

1. **All §8.A → §8.H Matrix Script trial corrections are landed and present in code on HEAD.** The brief §0.1 / §0.2 / §6.2 / §7.1 / §12 wording matches deployed-branch behavior.
2. **No surface has regressed since the static pass.** The §3.1 (production-eligible) and §3.2 (must-be-hidden / inspect-only) rows still hold.
3. **Two surfaces still require operator-environment hide / disable:** the Digital Anchor New-Tasks card click target and the temp connect route. The coordinator's §2.1 step 1 from the write-up is the binding action.
4. **The trial brief may be briefed verbatim.** No correction is needed before reading §0.1 / §0.2 / §5 / §6 / §7.1 / §8 / §12 to operators.
5. **The live-run is gated on the eight conditions in brief §12.** All eight must hold before Sample 1 starts.

## 6. What the AI agent did NOT do during this audit (binding)

- Did **not** run any operator sample.
- Did **not** generate a `task_id`, observation, or signoff.
- Did **not** modify any file under `gateway/`, `docs/contracts/`, `docs/architecture/`, `docs/product/`, `docs/handoffs/`, or `docs/reviews/`.
- Did **not** modify the trial brief or the trial coordination write-up.
- Did **not** open Plan E preparation; did **not** patch UI; did **not** reopen any §8.A → §8.H correction.
- Did read the boot sequence (CLAUDE.md, alignment map, ENGINEERING_RULES, CURRENT_ENGINEERING_FOCUS, ENGINEERING_STATUS) and the Plan A authorities.
- Did run read-only `grep` / `ls` / `git log` / file reads to re-verify the §3 anchors above.

## 7. Final audit verdict

- **§3.1 trial-eligibility anchors hold on HEAD:** YES — all six rows PASS.
- **§3.2 forbidden / preview-only anchors hold on HEAD:** YES — all eight rows PASS.
- **§8.A → §8.H additional anchors hold on HEAD:** YES — all seven rows PASS.
- **Substantive drift since 2026-05-02 / 2026-05-03 static-pass:** NONE.
- **Cosmetic drift:** line-number shifts in `create_entry.py` only (file grew with §8.F additions); symbols and values intact.
- **Surfaces requiring environment-side hide / disable before trial:** two (Digital Anchor New-Tasks card target + temp connect route), per write-up §2.1 step 1.
- **Audit verdict:** Plan A trial may be briefed and run as written. The brief, the write-up §11 / §12 addenda, and the [PLAN_A_COORDINATOR_HANDOFF_PACKAGE_v1.md](PLAN_A_COORDINATOR_HANDOFF_PACKAGE_v1.md) are all coherent with HEAD.

End of pre-trial authority audit.
