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

The synchronous MVP route must finish with either:

- `preview_generation_succeeded` plus `matrix_script_staged_candidate.preview_url`;
- `preview_generation_failed` plus an operator-safe `error_summary`.

It must not leave `preview_generation_running` after the request completes.
The initial-preview service validates the generated `final.mp4` and manifest
before persisting a staged candidate.
Validation requires:

- `final.mp4` exists and is larger than the minimal guard threshold;
- `ffprobe` can read duration and the duration is greater than zero;
- a video stream exists;
- `manifest.json` exists.

Generation, validation, staging, and persistence failures are all finalized as
`preview_generation_failed` with an operator-safe summary. A staged candidate is
not written unless the final video and manifest pass validation.

## Test Proof

The PR includes route-level render tests for both outcomes:

- Real local success path with injected in-memory staging:
  `trigger_matrix_script_initial_preview_generation()` runs the existing tomato
  preview path, creates a readable `final.mp4`, writes `manifest.json`, validates
  the artifacts with `ffprobe`, persists
  `config.matrix_script_staged_candidate.preview_url`, and finishes with
  `preview_generation_succeeded`.
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
Workbench-facing staged candidate shape plus the real local success test above.

Failure tests cover invalid final video, missing manifest, staging failure, and
persistence failure. Each case records `preview_generation_failed` and avoids a
long-lived `preview_generation_running` state.

## Read-Only Production Diagnostic

Run from a production shell to inspect one task without writing data:

```bash
python - <<'PY'
import json, os, glob, subprocess
from gateway.app.deps import get_task_repository

task_id = os.environ.get("TASK_ID", "baeeaa59625a")
task = get_task_repository().get(task_id)
print("task_id", task_id)
print("task_kind", (task or {}).get("kind"))
cfg = (task or {}).get("config") or {}
for key in (
    "matrix_script_initial_preview_generation",
    "matrix_script_staged_candidate",
    "matrix_script_tomato_real_result",
    "matrix_script_minimal_result",
):
    print(key, json.dumps(cfg.get(key), ensure_ascii=False, indent=2))

roots = [
    os.environ.get("WORKSPACE_ROOT"),
    "/var/data/video_workspace",
    "/opt/render/project/src/.local_workspace",
    ".local_workspace",
]
for root in [r for r in roots if r]:
    print("ROOT", root)
    for path in glob.glob(f"{root}/**/*{task_id}*", recursive=True):
        print(path)

for path in glob.glob(f"/var/data/video_workspace/**/*{task_id}*/**/final.mp4", recursive=True):
    print("ffprobe", path)
    subprocess.run(["ffprobe", "-hide_banner", path], check=False)
PY
```

## Boundary

- No Hot Follow changes.
- No Digital Anchor changes.
- No `artifact_storage.py` changes.
- No schema or contract changes.
- No Akool live/API changes.
- `official_publish_ready` remains false.
