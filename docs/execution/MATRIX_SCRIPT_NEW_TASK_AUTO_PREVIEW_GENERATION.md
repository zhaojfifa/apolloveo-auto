# Matrix Script New Task Auto Preview Generation

## Scope

This change closes the Matrix Script New Task -> Workbench production-start
link. Submitting the Matrix Script New Task form now starts the first preview
generation synchronously and persists the staged candidate on the task config.

## Route

- New Task route: `POST /tasks/matrix-script/new`
- Reused generation path: controlled tomato real-result orchestrator behind
  `/api/matrix-script/{task_id}/tomato-real-result`

## Persistence

The first preview result is stored under:

- `config.matrix_script_staged_candidate`
- `config.matrix_script_initial_preview_generation`

The Workbench reads those existing Matrix Script projections and can render:

- generated inline preview when the preview succeeds;
- retry/error state when generation fails.

## Test Proof

The PR includes route-level render tests for both outcomes:

- Successful injected auto-preview:
  `POST /tasks/matrix-script/new` persists
  `config.matrix_script_staged_candidate.preview_url`, redirects to the
  Workbench, and the A section renders
  `<video controls preload="metadata">` with the preview URL. The first
  generation does not require a second operator click.
- Failed auto-preview:
  task creation still returns the Workbench redirect, persists
  `config.matrix_script_initial_preview_generation.status =
  preview_generation_failed`, and the A section renders `首版预览生成失败`
  plus `重新生成预览` instead of a dead `未生成` state.

The local machine does not have the configured storage service for the existing
tomato staging sink, so an unstubbed local smoke records the failure path. The
successful path is proven through injected route tests that write the same
Workbench-facing staged candidate shape.

## Boundary

- No Hot Follow changes.
- No Digital Anchor changes.
- No `artifact_storage.py` changes.
- No schema or contract changes.
- No Akool live/API changes.
- `official_publish_ready` remains false.
