# Matrix Script Phase 3 PR-9R Workbench Minimal Result View

## Scope

PR-9R adds a narrow, read-only Workbench view for the PR-8R
`MatrixScriptMinimalResultSurfaceView`.

Changed files:

- `gateway/app/services/matrix_script/minimal_result_workbench_block.py`
- `gateway/app/services/operator_visible_surfaces/wiring.py`
- `gateway/app/templates/task_workbench.html`
- `gateway/app/services/tests/test_matrix_script_minimal_result_workbench_block.py`
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR9R_WORKBENCH_MINIMAL_RESULT_VIEW.md`

## Dependency

PR-9R depends on PR-8R:

- `gateway/app/services/matrix_script/minimal_result_surface.py`
- `MatrixScriptMinimalResultSurfaceView`

PR-9R does not copy or recreate PR-8R ownership.

## Visible Result

The Workbench can render a small local result panel when a pre-computed
`matrix_script_minimal_result` surface dict is present on task config.

Visible fields:

- label: `本地最小成片`
- `result_status`
- `final_video_path`
- `duration_seconds`
- `shot_count`
- `storage_scope`
- `official_publish_ready`
- `operator_note`

If no pre-computed surface dict is present, the block returns
`{"has_result": false}` and the template renders nothing.

## Boundary

This is read-only display wiring only.

No:

- Akool
- provider URL
- artifact storage / R2
- schema / packet / contract change
- Delivery publish logic
- Hot Follow / Digital Anchor change
- Workbench redesign
- player / iframe / download link / publish link

`storage_scope` remains `local_workspace`.

`official_publish_ready` remains `false`.

## Validation

Required validation:

- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_workbench_block.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_surface.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_projection.py --tb=short`
- `git diff --check`
- forbidden-path guard
