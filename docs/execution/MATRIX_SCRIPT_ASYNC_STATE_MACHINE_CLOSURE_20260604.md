# Matrix Script Async State Machine — P0 Closure (2026-06-04)

Status: **CLOSED — Matrix Script P0 production line established.**
Deployed + validated SHA: `bf4af50b36b8e87a9611830e059d94562b936553`
(merged to `main` as `a2c6d1f05fcbaca71d54cc5fd5af7349d9d69657`; the merge tree
is byte-identical to the branch tree `41c09b59…`).

Health evidence (Render configured environment):

```
{"status":"ok","version":"bf4af50b36b8e87a9611830e059d94562b936553",
 "storage":"R2StorageService","storage_ok":true,"ffmpeg":true}
```

Fresh-task validation evidence (not reusing the #202 task):

```
task_id: 3eded8a36aaa  (created=matrix_script)
POST /tasks/matrix-script/new: not 502
Workbench A区: 主视频预览 — inline <video> visible and playable
status: 运营可用 ; current version: V1 主视频预览
visual_semantic_match: partial_pass ; shot_match_count: 3/5 ; real_visual_count: 3
missing material count: 2
delivery_candidate: true ; official_publish_ready: false
no endless generating
```

## Matrix Script P0 baseline

```
New Task submit
→ task created
→ initial preview lifecycle queued / running / succeeded / failed
→ Workbench A区 shows inline video on success
→ Workbench A区 shows failure + retry on failed
→ no endless generating
→ B区 supports material / music / voice status and future replacement loop
→ C区 exposes delivery candidate
→ D / E are folded
→ official_publish_ready remains false
```

## Closure composition

```
#202: artifact truth + failure finalization
#203: async lifecycle + polling / stale guard + operator-visible terminal state
```

Together #202 and #203 form the current P0 closure: Matrix Script can produce an
operator-visible main video result from a script-driven task and expose it as a
delivery candidate without claiming official publish readiness.

## Operator-facing UI rule

Primary UI must show only operator states:

```
1. generating
2. video ready
3. generation failed / retry
```

Primary UI must NOT expose:

```
artifact refs
raw manifest
provider URLs
publish URLs
Akool task / model / credit
technical step internals
```

## Four-layer boundary

```
L1 process: queued / running / succeeded / failed / retry_required
L2 artifact facts: valid final.mp4, manifest, preview route, subtitles / audio if present
L3 readiness: operator_usable, delivery_candidate, official_publish_ready=false
L4 operator projection: inline video / failure retry / material loop / delivery candidate
```

## Stale guard

A queued/running attempt older than `RUNNING_STALE_SECONDS` (300s) projects to
`retry_required` in the operator projection — a dead worker never reads as
endless generating.

## Implementation references

- `gateway/app/routers/tasks.py` — New Task POST enqueues `queued`, dispatches
  generation via `BackgroundTasks`, redirects immediately; poll endpoint
  `GET /api/matrix-script/{task_id}/initial-preview-status`.
- `gateway/app/services/matrix_script/auto_preview_generation.py` — lifecycle
  states + artifact validation (from #202).
- `gateway/app/services/matrix_script/operator_workbench_view.py` — stale guard,
  queued/retry_required projection, `poll` flag.
- `gateway/app/templates/task_workbench.html` — A区 render branches + poller.
- Tests: `gateway/app/services/tests/test_matrix_script_async_preview_state_machine.py`,
  `..._new_task_auto_preview_generation.py`.
- Prior execution note: `docs/execution/MATRIX_SCRIPT_INITIAL_PREVIEW_ASYNC_STATE_MACHINE.md`.

## Boundary held

No Hot Follow / Digital Anchor / `artifact_storage.py` / schema-contract / Akool
live / provider-logic changes. `official_publish_ready` remains false.
