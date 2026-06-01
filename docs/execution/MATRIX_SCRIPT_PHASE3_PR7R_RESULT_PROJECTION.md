# Matrix Script Phase 3 PR-7R Result Projection

## Scope

PR-7R adds a pure service-layer projection over the PR-6R
`MatrixScriptMinimalResultRecord`.

Added files:

- `gateway/app/services/matrix_script/minimal_result_projection.py`
- `gateway/app/services/tests/test_matrix_script_minimal_result_projection.py`
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR7R_RESULT_PROJECTION.md`

## Projection Shape

Two frozen read models were added:

- `MatrixScriptOperatorResultProjection`
- `MatrixScriptDeliveryResultProjection`

Both expose local-workspace result facts:

- `task_id`
- `line_id`
- `result_status`
- `has_final_video`
- `final_video_path`
- `has_manifest`
- `manifest_path`
- `has_subtitles`
- `subtitles_path`
- `has_audio`
- `audio_path`
- `duration_seconds`
- `shot_count`
- `publish_ready_candidate`
- `storage_scope`
- `official_publish_ready`

Operator projection adds `operator_summary`.
Delivery projection adds `delivery_summary`.

## Readiness Boundary

`storage_scope` is fixed to `local_workspace`.

`official_publish_ready` is always `false`.

`publish_ready_candidate` may mirror the internal PR-6R candidate hint, but it
is still only a candidate and not the official publish gate.

## Forbidden Fields

Projection serialization rejects:

- `provider_url`
- `temporary_url`
- `download_url`
- `artifact_key`
- `r2_key`
- `publish_url`
- `publish_status`
- `akool`
- `vendor`
- `model_id`
- `credit`
- `provider_task_id`

## Boundary Confirmation

PR-7R does not change:

- UI/templates
- routers/endpoints
- Delivery Center runtime
- artifact storage / R2
- official publish gates
- Akool live API
- webhook/polling
- schemas/packets/contracts
- Hot Follow
- Digital Anchor
- publish logic

## Validation

Required validation:

- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_projection.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_record.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_service.py --tb=short`
- `python3.11 -m py_compile gateway/app/services/matrix_script/minimal_result_projection.py`
- `git diff --check`
