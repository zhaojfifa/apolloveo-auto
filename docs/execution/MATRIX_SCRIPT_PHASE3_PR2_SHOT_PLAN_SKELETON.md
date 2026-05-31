# Matrix Script Phase 3 — PR-2 Shot Plan Skeleton (Execution Note)

Date: 2026-05-31
Branch: `phase3/pr2-matrix-script-shot-plan-skeleton`
Base: `main` @ `ad7cd103a95943ce875ec37b3b9ccc8142a55087`
Status: Implementation note for PR-2. Pre-runtime Phase 3 preparation. **No code path generates video, calls Akool, or writes artifact truth.**

---

## Reading Declaration

### Root indexes read first
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`

### Docs indexes read second
- `docs/README.md`, `docs/ENGINEERING_INDEX.md`

### Root governance (boot sequence)
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` (PR-0; PR-2 row + §5 L2 orchestration + §6 artifact/state model)
- `docs/product/matrix_script_product_flow_v1.md` §6.1A (Hook / Body / CTA)
- `docs/product/matrix_script_product_flow_v2_delta.md` (storyboard / shot plan as first product object)
- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` (`scene_plan_binding` storyboard intent)
- `docs/contracts/factory_scene_plan_contract_v1.md`, `docs/contracts/factory_content_structure_contract_v1.md` (conceptual relation only — no schema changed)
- `gateway/app/services/matrix_script/` (existing services, esp. `script_structure_view.py`, `phase_b_authoring.py`, `main_video_result_view.py`, `delivery_binding.py`)

### Why sufficient
PR-2 is a narrow, line-internal L2 domain skeleton for one line. The PR-0 design fixes the shot-plan's place in the production line; the product-flow + contract-alignment docs fix the Hook/Body/CTA storyboard shape; the factory contracts are conceptual (no field schema) so no contract change is needed.

### Missing-authority handling
None. The two factory contracts define no concrete field schema, confirming the shot plan must be a **line-internal** object (not a generic-contract or packet change).

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/shot_plan.py` | Frozen domain model: `MatrixScriptShotSpec`, `MatrixScriptShotPlan`, closed `GENERATION_MODES`, `ShotPlanError`, pure serialization (`shot_plan_to_dict`), and validation guards (`validate_shot_plan`, `assert_no_forbidden_tokens`). |
| `gateway/app/services/matrix_script/shot_plan_builder.py` | Deterministic `build_shot_plan(outline, ...)` → 4–8 shots from a Hook/Body/CTA outline. Content-hash `plan_id` (no clock/uuid/randomness). |
| `gateway/app/services/tests/test_matrix_script_shot_plan.py` | Unit tests (see Validation). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR2_SHOT_PLAN_SKELETON.md` | This note. |

### Object shape
- `MatrixScriptShotSpec`: `shot_id, order, duration_seconds, role, visual_intent, action, scene_context, asset_need, audio_text, subtitle_text, generation_mode, blocking`.
- `MatrixScriptShotPlan`: `plan_id, task_id, aspect_ratio, target_duration_seconds, shots, source_outline_ref`.
- `generation_mode` closed set (Apollo-native business intent, **not** provider/model): `static_asset, image_to_video, avatar_segment, broll, title_card, cta_card`.

### Builder behavior
- 1 hook shot (avatar when a `role` is supplied, else image_to_video) + 2–6 body shots (deterministic mode rotation `static_asset → image_to_video → broll`) + 1 cta_card shot, clamped to `[4, 8]`.
- Even duration distribution summing to the requested target (within ≤0.5s tolerance).
- `plan_id = shotplan-<sha1(canonical outline + task_id + aspect_ratio + target)[:12]>` → deterministic.

---

## What was explicitly NOT added (PR-2 forbidden scope)

- No Akool call / import; no provider / adapter / capability-enum dependency.
- No live API, webhook, or polling.
- No `final.mp4` generation, no artifact-storage write, no artifact truth.
- No task route / runtime binding; no task-status write; no file/storage write.
- No schema / packet / contract change; `gateway/app/services/packet/envelope.py` untouched.
- No Workbench / Delivery Center / template / UI change.
- No Hot Follow / Digital Anchor change; debt branch untouched.

The shot plan is a **pre-generation L2 object**, never deliverable truth. Real generation remains gated behind the Capability Expansion Gate Wave (W2.3) per PR-0 §2 / §10.

---

## Validation

- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_shot_plan.py` — PASS (see PR body for count)
- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py` — PASS (no-vendor-name fidelity preserved)
- `python3.11 -m py_compile shot_plan.py shot_plan_builder.py` — OK
- `git diff --check` — clean
- Forbidden-path guard — no forbidden paths touched
