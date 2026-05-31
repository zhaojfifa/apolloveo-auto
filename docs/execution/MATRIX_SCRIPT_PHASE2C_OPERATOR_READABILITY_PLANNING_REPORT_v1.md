# Matrix Script · Phase 2C Operator Readability Planning · Report v1

Date: 2026-05-30
Status: **Docs-only PR. No code, no template, no presenter, no contract, no schema, no packet, no closed-enum, no runtime, no worker, no router, no endpoint, no sample, no test change.** No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans touch. No `main` merge.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2C Planning Archivist).

---

## 1. Branch and base

| Item | Value |
|---|---|
| Base branch | `VeoMatrixVoice04` |
| Base commit | `63bc709` (`docs(VeoMatrixVoice04): joint validation integration report`) |
| Planning branch | `design/ms-phase2c-operator-readability-planning-20260530` |
| Purpose | Archive the accepted Phase 2C operator-readability planning direction as a reviewable docs-only artifact. |

---

## 2. Files changed

| File | Status | Kind |
|---|---|---|
| `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md` | NEW | Planning document |
| `docs/execution/MATRIX_SCRIPT_PHASE2C_OPERATOR_READABILITY_PLANNING_REPORT_v1.md` | NEW | This report |

`git diff --stat` against `VeoMatrixVoice04` shows only the two files above. No changes under `gateway/`, `docs/contracts/`, `schemas/`, `samples/`, or any runtime / template / presenter path.

---

## 3. Summary of planning contents

The planning document `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md` defines:

1. **Scope and hard boundaries (§1)** — Phase 2C is operator-readability only; only copy / layout / presenter projection may be touched by a later implementation PR; no backend capability, worker, contract, schema, packet, closed enum, runtime, or route change; honest placeholder discipline remains; IA preserved (Workbench 10 sections A–J; Delivery 6 sections + §7 fold; New Task 5 cards).
2. **Section-by-section readability plan (§2)** for §B / §C / §D / §E / §F / §G:
   - §B 脚本理解 — remove `content_structure` / backend vocabulary; operator-language echo.
   - §C 视频生成计划 — keep storyboard; rewrite "后端方案生成能力" disclaimer as product-facing draft / replacement language.
   - §D 画面与素材 — consolidate three repeated pending slots into one upload / material panel; differentiate disabled tooltips.
   - §E 角色与声音 — promote four preference selectors to section top; demote voice-preview placeholder to a chip.
   - §F 字幕与音乐 — make subtitle / BGM controls selectable so they carry operator intent.
   - §G 视频变体 — add `适合哪些账号 / 场景` column; split recommendation / state pills.
3. **Backend-pending language reduction strategy (§3)** — top-level capability banner; forbidden vocabulary list (`content_structure`, `后端`, `compose`, `producer`, `bridge`, `provider`, `vendor`, `engine`, `model`, vendor names); narrative empty-state wording.
4. **D / E / F operator choice-panel mental model (§4)** — D / E / F are for expressing operator intent, not waiting on backend results; intents become future generation inputs without UI rework.
5. **Video-version enhancement (§5)** — stable three-question model: 哪里不同 / 为什么测这一版 / 适合哪些账号 · 场景; plus dual-pill state model.
6. **Implementation scope candidate list (§6)** — candidate files for a later implementation PR: `gateway/app/templates/task_workbench.html`, `gateway/app/templates/task_publish_hub.html`, `gateway/app/templates/matrix_script_new.html`, `gateway/app/services/matrix_script/*`, Matrix-Script-scoped tests. **This planning PR does not touch these files.**
7. **Deferred Phase 3+ list (§7)** — `scene_plan_binding` / single-scene edit; real B-Roll retrieval / Asset Supply bridge; VoiceTrans bridge; subtitle / BGM compose worker; backend video generation worker; publish-metrics-based recommendation projection; real review-zone activation; packet persistence of new preferences.
8. **Acceptance gates for future Phase 2C implementation (§8)** — forbidden-vocabulary grep; §D single upload area; §E selector DOM order; §F selectable controls; §G V1 / V2 / V3 field + pill structure; capability banner density; New Task Card 4 usage hints; Delivery §6 future-metrics wording; zero contract / schema / packet / runtime / worker changes; scoped test pass; no `main` merge; no surface regression.
9. **Final boundary statement (§9)** — implementation requires a separate裁决; no template / presenter / test / backend / `main`-merge action authorized by this document.

---

## 4. Explicit docs-only / no-code / no-runtime / no-contract statement

This PR is **documentation only**. It does NOT:

- Edit any template (`gateway/app/templates/**`).
- Edit any presenter or service module (`gateway/app/services/**`).
- Edit any router or endpoint (`gateway/app/routers/**`, `gateway/app/main.py`).
- Edit any contract, schema, packet, sample, or closed enum (`docs/contracts/**`, `schemas/**`, `samples/**`).
- Add, remove, or modify any test.
- Add, remove, or modify any runtime worker, generator, or capability.
- Touch any Hot Follow, Digital Anchor, Asset Supply, VoiceTrans, or generic factory-readiness file.
- Open any Phase 2C implementation branch.
- Open or contribute to any Phase 3 wave.
- Merge to `main`.

The planning document explicitly enumerates these prohibitions in §1 and §9 so that any future reader operating from this artifact alone cannot drift into implementation under its authority.

---

## 5. Recommended next step

1. Review the planning document `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`.
2. If the planning direction is accepted, issue a separate裁决 to open the Phase 2C implementation branch (`fix/ms-script-to-video-phase2c-operator-readability-…`) targeting the candidate files in §6 of the plan, gated to the acceptance criteria in §8.
3. If the planning direction needs revision, open a follow-on docs-only planning revision branch from this branch; do not edit templates or presenters until the planning revision is signed off.
4. Do not start Phase 2C implementation, do not start Phase 3, and do not merge this planning PR to `main` without explicit, separate裁决.

---

## 6. Validation log

The author of this PR ran the following local validation before push:

- `git diff --stat VeoMatrixVoice04..HEAD` — confirmed only `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md` and `docs/execution/MATRIX_SCRIPT_PHASE2C_OPERATOR_READABILITY_PLANNING_REPORT_v1.md` appear in the change set.
- Path audit — confirmed zero entries under `gateway/`, `docs/contracts/`, `schemas/`, or `samples/`.
- Content audit — confirmed the planning document carries the binding hard-boundary clauses in §1 and the final boundary statement in §9.
