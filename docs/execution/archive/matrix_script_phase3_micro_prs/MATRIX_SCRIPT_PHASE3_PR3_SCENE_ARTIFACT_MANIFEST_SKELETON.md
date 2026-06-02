# Matrix Script Phase 3 — PR-3 Scene Artifact / Manifest Skeleton (Execution Note)

Date: 2026-05-31
Branch: `phase3/pr3-matrix-script-scene-artifact-manifest-skeleton`
Base: `main` @ `3cbfcd47653b14476bfb08e4b7b5f5efa7909186`
Status: Implementation note for PR-3. **Pre-runtime, non-generative.** No code path generates media, calls Akool, touches storage, or creates real artifact / deliverable truth.

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §6 (artifact / manifest model; provider URL never deliverable; copy-into-Apollo is a later gated step)
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR2_SHOT_PLAN_SKELETON.md` (PR-2 shot plan)
- `docs/contracts/factory_delivery_contract_v1.md` (`required` / `blocking_publish` zoning; `scene_pack_blocking_allowed: false`)
- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
- `gateway/app/services/matrix_script/shot_plan.py`, `shot_plan_builder.py`, `delivery_binding.py` (required/blocking + clamp vocabulary), `artifact_storage.py` (boundary only — NOT called)

### Why sufficient
PR-3 is a narrow, line-internal planning skeleton connecting the PR-2 shot plan to planned scene-segment slots + a manifest skeleton. The delivery contract fixes the required/blocking + scene-pack-non-blocking vocabulary; the PR-0 design fixes the manifest/artifact-truth boundary. No contract/schema change is needed.

### Missing-authority handling
None.

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/scene_artifacts.py` | `MatrixScriptSceneArtifactSlot` (frozen, planned-only) + `build_scene_artifact_slots(plan)` + closed `SLOT_STATUS_PLANNED` + forbidden-token guard. |
| `gateway/app/services/matrix_script/scene_manifest.py` | `MatrixScriptSceneManifestSkeleton` + `build_scene_manifest_skeleton(plan)` + serialization + manifest token guard. |
| `gateway/app/services/tests/test_matrix_script_scene_artifacts.py` | Unit tests (see Validation). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR3_SCENE_ARTIFACT_MANIFEST_SKELETON.md` | This note. |

### Model
- `MatrixScriptSceneArtifactSlot`: `slot_id, shot_id, order, expected_kind, expected_filename, generation_mode, required_for_final, blocking_publish, status`. Status is the single planning value `"planned"`. `blocking_publish` is structurally forced to `False` (scene segments are intermediate artifacts; the final video is the publish deliverable).
- `MatrixScriptSceneManifestSkeleton`: `manifest_id, plan_id, task_id, aspect_ratio, target_duration_seconds, scene_slots, final_video_required(=True), final_video_expected_filename(="final.mp4"), scene_pack_blocking_allowed(=False)`.

### Behavior
- One planned slot per shot, order-preserving; `expected_filename` = `scene_001.mp4`, `scene_002.mp4`, … (planned names only).
- `manifest_id = manifest-<plan_id>` → deterministic (plan_id is the PR-2 content hash).

---

## Artifact-truth boundary (binding)

The manifest skeleton distinguishes a **planned artifact slot** from **real artifact / deliverable truth**. It never claims an artifact exists. Forbidden fields are absent by construction and enforced by guards: `artifact_key`, `final_video_key`, `download_url`, `provider_url`, `temporary_url`, `exists`, `ready`, `delivered`, `publish_ready`, `provider_task_id`. Future mapping uses `expected_*` / `*_required` naming only.

`final_video_required=True` is an **expectation**, not a created artifact. Real generation/assembly + the provider-output-copy-into-Apollo rule remain gated behind the Capability Expansion Gate Wave (W2.3) per PR-0 §2 / §10.

---

## What was explicitly NOT added (PR-3 forbidden scope)

No Akool call/import; no provider/adapter import; no live API/webhook/polling; no `artifact_storage` call; no file/storage write; no `object_exists`/`object_head`/upload; no scene `.mp4` / `final.mp4` generation; no real artifact truth; no task route/runtime binding; no status-policy mutation; no schema/packet/contract change; `envelope.py` and `artifact_storage.py` untouched; no Workbench/Delivery/template/UI change; no Hot Follow / Digital Anchor change; debt branch untouched.

---

## Validation

- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_scene_artifacts.py` — PASS (see PR body for count)
- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_shot_plan.py` — PASS (PR-2 regression)
- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py` — PASS (no-vendor-name fidelity preserved)
- `python3.11 -m py_compile scene_artifacts.py scene_manifest.py` — OK
- `git diff --check` — clean
- Forbidden-path guard — no forbidden paths touched
