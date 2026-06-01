# Matrix Script · Design Authority Consolidation v1

Date: 2026-06-01
Branch: `docs/ms-design-authority-consolidation-20260601`
Status: **Consolidation index only.** This is NOT a new UI/IA design spec and does NOT redefine product/contract/mock authority — it *selects* the single acceptable baseline from the existing files and defines the minimal authority set for the next wave. No UI, no runtime, no schema/contract, no Hot Follow / Digital Anchor / `artifact_storage.py`, no Akool. **No files are deleted or moved by this PR** — Bucket D lists *proposed* archive candidates only, pending sign-off.

## 0. Why this exists

Census of Matrix Script documentation today: **3 product · 13 design · 2 architecture · 58 execution · 6 reviews ≈ 82 docs.** The problem is not a missing design — it is **design-authority sprawl + patch-driven implementation**: multiple overlapping mocks/IAs (wireframe A–F, result-oriented UI plan, low-fi surfaces, reset 5-section, v2 10-section) and ~50 per-PR execution logs, with no single declared baseline. The PR-B FAIL (duplicate parallel flow) was a direct symptom: an engineer could not tell which mock was binding.

This index fixes that by naming **one** baseline and a **small** authority set; everything else becomes reference or historical.

## 1. Selected single mock / IA baseline (BINDING)

The next UI/engineering cleanup wave MUST use exactly this baseline:

| Role | File | Why |
|---|---|---|
| **Product target** | `docs/product/matrix_script_product_flow_v1.md` (normative spine) **+** `docs/product/matrix_script_product_flow_v2_delta.md` (accepted amendment) | v1 is the normative product spec; v2 delta adds the script→video framing, the `generation_plan` first-class object, and video-version variants without overwriting v1. Treat the pair as the product authority (v2 amends v1). |
| **Mock (rendered)** | `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` | The approved Phase 1 clickable mock — the visual source of truth for the three pages. |
| **IA / presenter map** | `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md` | Maps the mock's 10-section Workbench IA (A 主视频结果 / B 脚本理解 / C 视频生成计划 / D 画面与素材 / E 角色与声音 / F 字幕与音乐 / G 视频变体 / H 校对与微调 / I 交付入口 / J 技术诊断) to presenters. **This is the IA target.** |
| **Anti-additive / reset discipline** | `docs/design/matrix_script_workbench_product_flow_reset_v1.md` | Subtractive-not-additive rule; retire legacy blocks into the collapsed 技术诊断 fold; lightweight delivery entry. The implemented template's ①–⑤ grouping (with collapsed diagnostics) is the current realization of the A–J IA — see §1.1. |
| **Copy / readability constraints** | `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md` | Operator-language copy + per-section density rules; the forbidden-primary-vocabulary list. |
| **Contract layer** | `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` | The additive line-packet bindings (`scene_plan_binding` etc.) the A–J sections consume; defines the closed `data-status-code` honesty register. |
| **Result acceptance baseline** | `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md` | Binds operator-result acceptance (`operator_usable` / `visual_semantic_match` / `shot_match_count` / `real_visual_count` / `delivery_candidate` / `official_publish_ready=false`) — the PR-A overlay feeds these into the IA. |

### 1.1 The one reconciliation the next wave owns

There are **two section counts** in the authority set and they must be read as one, not two:

- The **v2 / presenter-alignment IA is A–J (10 sections)** — the *design target*.
- The **implemented template is ①–⑤ + collapsed 技术诊断** (the reset realization), which **groups** A–J (e.g. ③ 要素 merges D 画面与素材 + E 角色与声音 + F 字幕与音乐). The PR-A acceptance is overlaid into ① / ② / ⑤.

**Decision:** the implemented ①–⑤ grouping IS the accepted realization of the A–J IA. The next wave reconciles labels/grouping in place (subtractive) — it does **not** introduce an 11th section or a parallel flow. No new mock file is authored to express this; this index is the reconciliation record.

## 2. Minimal authority set for the next wave

Read **only** these (Bucket A). Anything not on this list is reference or historical and MUST NOT be cited as implementation authority:

1. `docs/product/matrix_script_product_flow_v1.md` (+ `_v2_delta.md`)
2. `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
3. `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html`
4. `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
5. `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`
6. `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
7. `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md`
8. `docs/reviews/MATRIX_SCRIPT_PR_B_MOCK_ALIGNMENT_REVIEW.md` (the anti-additive lesson — read once, do not repeat the mistake)

## 3. Classification table (four buckets)

### Bucket A — Binding Authority (next engineering work MAY use as authority)
| File | Role |
|---|---|
| `product/matrix_script_product_flow_v1.md` | product spine |
| `product/matrix_script_product_flow_v2_delta.md` | product target (amendment) |
| `design/matrix_script_script_to_video_presenter_alignment_v1.md` | IA / presenter map (mock target) |
| `design/previews/matrix_script_script_to_video_workbench_v1/index.html` | rendered mock |
| `design/matrix_script_workbench_product_flow_reset_v1.md` | anti-additive / reset discipline |
| `design/matrix_script_phase2c_operator_readability_plan_v1.md` | copy / readability constraints |
| `architecture/matrix_script_script_to_video_contract_alignment_v1.md` | contract-layer bindings + status-code register |
| `execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md` | result acceptance baseline |

### Bucket B — Supporting Reference (context, NOT implementation authority)
| File | Why reference-only |
|---|---|
| `design/matrix_script_kapwing_benchmark_product_advice_v1.md` | benchmark advice that fed v2; not an IA spec |
| `design/matrix_script_phase3_akool_real_generation_plan_v1.md` | future real-generation plan (Akool); gated, not current UI authority |
| `reviews/MATRIX_SCRIPT_PR_B_MOCK_ALIGNMENT_REVIEW.md` | the lesson record (why no second flow) |
| `execution/MATRIX_SCRIPT_PHASE3_PR_A_TOMATO_REAL_RESULT.md`, `..._PR_A_REVIEW_ADDENDUM.md`, `..._PR_B_OPERATOR_WORKBENCH_FLOW_ALIGNMENT.md` | recent PR-A/PR-B result + overlay reports |
| `execution/MATRIX_SCRIPT_PHASE3_P0_R2_PREVIEW_STAGING.md`, `..._PR17R_REAL_OPERATOR_TRIAL.md` | artifact-staging / preview-path facts the overlay relies on |
| `execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md`, `..._PRESENTER_ALIGNMENT_REPORT_v1.md` | companions to the Bucket-A mock/IA docs |
| `design/matrix_script_delivery_center_wireframe_v1.md` | delivery wireframe context (superseded by v2 §3 + PR-B delivery reset, kept for lineage) |

### Bucket C — Historical / Superseded (retained as evidence; DO NOT cite as authority)
These caused or recorded the additive/patch era. They remain in-repo as engineering evidence (per the repo's append-only execution-log discipline) but are **not** authority.
- Pre-v2 mocks/plans superseded by the Bucket-A baseline: `design/matrix_script_workbench_wireframe_v1.md` (A–F), `design/matrix_script_result_oriented_ui_plan_v1.md`, `design/matrix_script_result_oriented_ui_implementation_slicing_v1.md`, `design/matrix_script_task_area_wireframe_v1.md`, `design/surface_workbench_lowfi_v1.md`, `design/surface_delivery_center_lowfi_v1.md`, `design/panel_matrix_script_variation_lowfi_v1.md`.
- Per-PR execution logs of the minimal_result / real_trial build (`execution/MATRIX_SCRIPT_PHASE3_PR2..PR17R*`, `PR4R..PR9R`, `PR10R..PR13R`, `PRODUCTION_ACTION_MVP_CLOSEOUT`) — step records; the durable learning is captured in the Bucket-A result baseline.
- Phase 2B/2C/2D + reset PR implementation/validation reports (`PHASE2B_*`, `PHASE2C_*`, `PHASE2D_*`, `WORKBENCH_PRODUCT_FLOW_RESET_PRA/PRB/PRC*`, `DELIVERY_CENTER_PRODUCT_FLOW_RESET_PRB*`).
- `PLAN_E_MATRIX_SCRIPT_*` execution logs and the `MATRIX_SCRIPT_{A..H}_*` correction logs (closed-out trial-correction history).

### Bucket D — Archive / Delete Candidate (PROPOSED — no action in this PR)
| Candidate | Reason | Recommended action |
|---|---|---|
| `design/MATRIX_SCRIPT_OPERATOR_WORKBENCH_UI_RESET_v1.md` | **Does not exist** (good — was never created). | none |
| Pre-v2 low-fi mocks if they are ever cited as authority: `surface_workbench_lowfi_v1.md`, `surface_delivery_center_lowfi_v1.md`, `matrix_script_workbench_wireframe_v1.md` | They contradict the selected A–J/reset baseline if used as authority and are the most likely source of future confusion. | **Archive** under a `docs/design/_superseded/` index with a one-line "superseded by §1 baseline" banner — NOT hard-delete (preserve lineage). Requires sign-off. |
| `execution/MATRIX_SCRIPT_NEXT_WAVE_START_NOTE_v1.md` | Temporary pointer note; superseded by this consolidation index. | Archive / mark superseded. |

No file is touched by this PR beyond adding this index. Bucket D is a proposal for a follow-up cleanup PR after sign-off.

## 4. Anti-sprawl rules going forward (binding)

1. **No new Matrix Script UI mock / IA / reset design file.** The baseline is §1. Changes to the IA are edits to the §1 files, not new files.
2. **No "add a new section" PRs.** The IA is A–J (realized as ①–⑤ + collapsed). New operator value is *overlaid into* an existing section (the PR-B revised overlay is the pattern), never a parallel flow.
3. **Execution logs are evidence, not authority.** A new per-PR log is fine; it must not be cited as design authority and must not restate the IA.
4. **One product authority pair (v1 + v2 delta).** If v2 is promoted to normative, overwrite v1 — do not spawn a v3 doc alongside.
5. **Cite Bucket A only.** Any PR citing a Bucket C/D file as implementation authority is returned.

## 5. Verdict

Single mock/IA baseline selected (§1), minimal authority set defined (§2), full doc set classified (§3), anti-sprawl rules set (§4). The next wave is a **Matrix Script UI/Engineering Cleanup Wave** that reconciles the ①–⑤ ↔ A–J labels in place and retires legacy blocks per the reset discipline — opened only after this consolidation is signed off. No UI/runtime/contract change in this PR.
