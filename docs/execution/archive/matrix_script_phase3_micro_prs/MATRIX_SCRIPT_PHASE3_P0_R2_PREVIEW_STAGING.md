# Matrix Script Phase 3 — P0 R2 / Artifact Preview Staging

Date: 2026-06-01
Branch: `phase3/p0-matrix-script-r2-preview-staging`
Base: `main` @ `c17d684c615a0b1b6f497430dae2486b0c4ad036`
Status: P0 — make the staged Matrix Script `final.mp4` operator-accessible via a browser-openable preview link. Still staged, not publish (`official_publish_ready=false`).

---

## 1. Root Cause

- `final.mp4` exists on the server (e.g. `/var/data/.../matrix_script_minimal/<id>/final/final.mp4`).
- Operators could not access it because the result was only exposed as a **local filesystem path** (`final_video_path`) — not a browser-openable URL. The result was generated but not operator-accessible.
- (Validation also confirmed the earlier `/files/<key>` route is not a reliable preview path: its `WORKSPACE_ROOT` comes from `VIDEO_WORKSPACE` and gates on `ALLOWED_TOP_DIRS`, which don't align with the storage key prefix `default/…` → 404.)

## 2. Fix

- **Production staging sink** (`ArtifactStorageStagingSink` in `gateway/app/routers/matrix_script_real_trial.py`) now uses the existing abstraction only — `upload_artifact` to stage + `get_download_url` for a URL — and exposes `preview_url_for`. **`artifact_storage.py` not modified.**
- **Staging record** (`minimal_result_artifact_staging.py`) gains `final_video_preview_url`; `InMemoryArtifactSink` (tests) returns a `/files/<name>` fake; `stage_minimal_result` populates it from the sink.
- **Delivery view** (`minimal_result_delivery_view.py`) staged block now carries `preview_url`.
- **Dedicated preview endpoint** (the reliable operator link): `GET /api/matrix-script/{task_id}/real-trial/preview/final.mp4` streams the local staged `final.mp4` (`FileResponse`, `video/mp4`), falling back to a storage URL redirect, else 404. The real-trial `POST` payload sets `preview_url` to this endpoint — browser-openable regardless of storage backend / static config.
- **Workbench** (`task_workbench.html`): new "暂存并预览" action POSTs `/real-trial` and renders a clickable **打开视频** link from `preview_url`.
- **Delivery** (`task_publish_hub.html`): staged-candidate block renders a **打开视频（暂存预览）** link when `preview_url` is present.

Field naming: `preview_url` (internal staged preview). NOT `download_url` / `publish_url` / `provider_url` / `temporary_url`.

## 3. Validation

- Tests (focused + regression): **199+ passing** across staging / real-trial orchestrator / real-trial route / operator-visibility / akool gate / minimal-result route / phase2b fidelity / delivery-center suites.
- New P0 tests: staging carries `final_video_preview_url`; staged delivery block includes `preview_url`; real-trial payload `preview_url` == dedicated endpoint; **GET preview streams the staged final.mp4 (200, `video/mp4`, non-empty)**; preview 404/302 when not generated; Workbench "暂存并预览" action + 打开视频 link present; Delivery staged preview link present.
- **Live human validation (gate off, local storage backend):** `POST /api/matrix-script/<id>/real-trial` → 200; `preview_url=/api/matrix-script/<id>/real-trial/preview/final.mp4`; `GET preview_url` → **HTTP 200, Content-Type video/mp4, Content-Length 33145, valid MP4 (ISO Media), ffprobe duration 20.0s (video+audio) → browser-playable**.
- ffprobe of the real final.mp4: duration 20.0s, video + audio streams.
- R2/artifact staging: exercised via the existing abstraction (`upload_artifact`/`get_download_url`); real R2 only when env-configured; tests use a fake in-memory sink.

## 4. Boundary Confirmation

- storage_scope: `artifact_staged` ✅ · delivery_candidate: `true` ✅ · official_publish_ready: `false` ✅
- no publish_url/publish_status ✅ · no provider_url/temporary_url ✅ · no download_url field ✅ · no Akool task id/model/credit ✅
- no schema/contract change ✅ · no Hot Follow / Digital Anchor change ✅ · `artifact_storage.py` untouched ✅ · `main.py` not touched in this P0 (route already registered by PR-17R).

## 5. Known follow-up

- The Delivery **server-rendered** staged block reads `task.config.matrix_script_staged_candidate`, but the publish handler passes a projected `detail` as the template `task`, so it does not surface from raw task config (separate follow-up already filed). The **Workbench "暂存并预览" action is the reliable operator-accessible preview path today** (renders the route response client-side, including the 打开视频 link).
