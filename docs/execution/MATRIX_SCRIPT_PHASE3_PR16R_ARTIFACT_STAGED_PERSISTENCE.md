# Matrix Script Phase 3 — PR-16R Artifact Staged Persistence (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr16r-matrix-script-artifact-staged-persistence`
Base: `main` @ `49a9c57a125300be3fcf54bc40c8fe783327fae0`
Status: Second slice of the Real Operator Trial Wave. Promotes the local result pack from `local_workspace` to `artifact_staged` (delivery candidate). NOT publish; `official_publish_ready=false`.

---

## Reading Declaration

Root + docs indexes + governance read. Task-specific: Phase 3 design plan §6 (artifact/manifest model; provider URL never deliverable); PR-4R loop output shape; PR-8R surface; the existing `artifact_storage` abstraction (consumed only via an injected sink — **not modified**). Sufficient; no contract/schema change. No missing authority.

---

## What was added / changed

| File | Change |
| --- | --- |
| `gateway/app/services/matrix_script/minimal_result_artifact_staging.py` | **new** — `ArtifactStagingSink`-shaped `InMemoryArtifactSink`; `MatrixScriptStagedArtifactRef`; `MatrixScriptMinimalResultStagingRecord`; `stage_minimal_result(...)`; dict serializer + leakage guard. |
| `gateway/app/services/matrix_script/minimal_result_delivery_view.py` | **+ additive** `staged_record_to_delivery_block(record)` (artifact_staged delivery candidate view) + staged constants. No existing behavior changed. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_artifact_staging.py` | **new** — 13 tests (in-memory sink; real temp files; no R2). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR16R_ARTIFACT_STAGED_PERSISTENCE.md` | **new** — this note. |

`artifact_storage.py` was **NOT** touched. `minimal_result_record.py` / `minimal_result_projection.py` were **not** modified (not needed; the additive delivery view sufficed).

### Staging
`stage_minimal_result(sink, task_id, final_video_path, manifest_path, subtitles_path, audio_path, scene_clip_paths, stage_scene_clips=True)`:
- Mandatory `final.mp4`; a missing one raises `StagingError`.
- Each file is copied through the injected `sink.put(local_path, artifact_name)` → opaque `artifact://matrix_script/<task_id>/<kind>/<filename>` ref.
- Scene clips staged by default; `stage_scene_clips=False` → `scene_clips_staged=False`, refs empty (explicit local-only).
- Record: `storage_scope=artifact_staged`, `delivery_candidate=True`, `official_publish_ready=False`, `generation_provider=none`.

### Sink discipline
Tests inject `InMemoryArtifactSink` (records puts; no bytes read; no R2). Production wiring (PR-17R) injects a sink that delegates to the existing `artifact_storage` abstraction — this module does not modify it.

---

## Validation

- `pytest test_matrix_script_minimal_result_artifact_staging.py` → **13 passed** (final/manifest/subtitles/audio staged; scene clips default-staged + local-only mode; storage_scope/candidate/publish flags; missing-final fails; sink records exact 7 files; delivery staged-candidate projection; leak-free).
- Regression: `test_matrix_script_minimal_result_route.py` + `test_matrix_script_operator_visibility_wave.py` → **19 passed**.
- `py_compile` OK; `git diff --check` clean; forbidden-path guard (hot_follow/digital_anchor/contracts/schemas/packet/envelope.py) → none; `artifact_storage.py` untouched.

---

## Acceptance mapping (wave criteria 4, 5, 6)

4. final.mp4 written to artifact/R2 staged area: ✅ via injected sink → `artifact://` ref (real R2 deferred to PR-17R wiring; abstraction-only here).
5. Delivery shows staged result candidate: ✅ service-layer `staged_record_to_delivery_block` (template wiring in PR-17R).
6. official_publish_ready=false: ✅ hard-pinned on the record + delivery block.

---

## What was explicitly NOT added (PR-16R forbidden scope)

No `publish_url` / `publish_status` / `official_publish_ready=true`; no `provider_url` / `temporary_url` / Akool task id / model / credit / raw provider response; no provider URL treated as `final_video`; no real R2 write in tests; no `artifact_storage.py` modification; no route/UI/template change; no Hot Follow / Digital Anchor change; no schema/packet/contract change.
