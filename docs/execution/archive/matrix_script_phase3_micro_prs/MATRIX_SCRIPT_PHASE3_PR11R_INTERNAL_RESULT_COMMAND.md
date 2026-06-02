# Matrix Script Phase 3 PR-11R Internal Result Command

## Scope

PR-11R adds a controlled internal service command:

`task / output_dir -> run_matrix_script_task_minimal_result() -> MatrixScriptMinimalResultSurfaceView`

Added files:

- `gateway/app/services/matrix_script/minimal_result_command.py`
- `gateway/app/services/tests/test_matrix_script_minimal_result_command.py`
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR11R_INTERNAL_RESULT_COMMAND.md`

## Behavior

The command:

- validates that the input task is Matrix Script scoped;
- requires an explicit caller-provided `output_dir`;
- delegates to PR-10R `run_matrix_script_task_minimal_result()`;
- returns `MatrixScriptMinimalResultSurfaceView`;
- lets invalid command inputs fail with `MinimalResultCommandError`;
- does not swallow FFmpeg/render errors.

## Boundary

PR-11R does not add:

- public router endpoint;
- button/action wiring;
- UI/template changes;
- Delivery Center runtime changes;
- artifact storage / R2 writes;
- official publish gate;
- Akool live API or Akool adapter usage;
- webhook/polling;
- schema/packet/contract changes;
- Hot Follow / Digital Anchor changes;
- publish logic;
- task repository mutation.

## Validation

Required validation:

- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_command.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_orchestrator.py --tb=short`
- `python3.11 -m pytest -q gateway/app/services/tests/test_matrix_script_minimal_result_workbench_block.py --tb=short`
- `python3.11 -m py_compile gateway/app/services/matrix_script/minimal_result_command.py`
- `git diff --check`
- forbidden-path guard
