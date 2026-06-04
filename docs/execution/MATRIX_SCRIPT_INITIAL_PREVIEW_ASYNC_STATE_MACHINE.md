# Matrix Script Initial Preview — Async State Machine

Status: implemented (PR — `fix/matrix-script-auto-preview-async-state-machine`).
Date: 2026-06-04.

## Why

Up to PR #202 the Matrix Script first-preview generation ran **synchronously
inside** `POST /tasks/matrix-script/new`. The full ffmpeg path (5-shot tomato
assembly) executed on the request thread, so a render that outlived the
gateway/worker timeout produced a 502 and the externally-killed worker could
leave the task stuck — PR #202 mitigated the stuck-`running` symptom by removing
the persisted `running` write and validating artifacts, but it did **not**
remove the synchronous 502 root cause, and there was no in-progress lifecycle
the Workbench could recover from.

This change moves generation off the request thread and gives the first preview
a real lifecycle with a stale guard, modeled on the stable Hot Follow pattern
(background dispatch + durable status + polling).

## Lifecycle

```
POST /tasks/matrix-script/new
  → create matrix_script task
  → persist initial_preview.status = queued (queued_at)        [synchronous, fast]
  → dispatch generation via BackgroundTasks
  → 303 redirect to Workbench                                  [immediate, no 502]

background job (trigger_matrix_script_initial_preview_generation):
  → running (started_at)
  → validate final.mp4 + manifest (PR #202 gate)
  → succeeded (completed_at) + matrix_script_staged_candidate.preview_url
  OR failed (failed_at) + operator-safe error_summary

projection (operator_workbench_view, owns the stale guard):
  → queued / running  → poll = true   (Workbench polls)
  → succeeded         → inline video
  → failed            → failure reason + retry
  → running/queued older than RUNNING_STALE_SECONDS (300s)
                      → retry_required (poll = false), never endless generating
```

## Four-layer mapping

- **L1 process**: `queued → running → succeeded / failed`; projected
  `retry_required` for a stale attempt. `running` carries `started_at`; terminal
  states carry `completed_at` / `failed_at`.
- **L2 artifact facts**: unchanged from PR #202 — `validate_tomato_result_artifacts`
  (exists + size + ffprobe duration + video stream + manifest) gates success.
- **L3 readiness**: computed only from a validated staged candidate.
- **L4 operator projection**: `poll` flag + status drive the Workbench A区
  generating / inline-video / retry states; stale guard prevents endless
  generating. `official_publish_ready` stays false; the overlay asserts no
  provider/model/publish leakage.

## Surfaces

- `gateway/app/routers/tasks.py` — New Task POST enqueues `queued` + dispatches
  background generation (resilient: a marker-write failure never blocks the
  redirect); new operator-safe poll endpoint
  `GET /api/matrix-script/{task_id}/initial-preview-status`.
- `gateway/app/services/matrix_script/auto_preview_generation.py` — `queued`
  enqueue, `running`/`completed_at` on the background trigger, lifecycle
  constants.
- `gateway/app/services/matrix_script/operator_workbench_view.py` — stale guard,
  queued/retry_required projection, `poll` flag.
- `gateway/app/templates/task_workbench.html` — queued/retry_required render
  branches + background poller that reloads on a terminal state.

## Tests

`gateway/app/services/tests/test_matrix_script_async_preview_state_machine.py`:
fast non-blocking New Task redirect, queued persistence, queued/running →
succeeded/failed transitions, corrupt-final → failed, queued/running poll
projection, success inline, failure retry, stale running/queued → retry_required,
no provider/publish leakage, `official_publish_ready=false`, poll endpoint
(queued / success / non-MS 400 / missing 404).

## Boundary

No Hot Follow, Digital Anchor, `artifact_storage.py`, schema/contract, or Akool
live changes. No provider logic. `official_publish_ready` remains false. No new
UI redesign — only lifecycle render branches + a poller on the existing A区.
