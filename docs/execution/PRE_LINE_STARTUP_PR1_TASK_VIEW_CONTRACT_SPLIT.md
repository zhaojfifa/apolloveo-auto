# Pre-Line Startup PR-1: Task View / Workbench Contract Split

Date: 2026-04-20

## Gate Citation

This PR is governed by:

- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md`
- `docs/reviews/appendix_code_inventory.md`
- `docs/reviews/appendix_router_service_state_dependency_map.md`
- `docs/reviews/appendix_four_layer_state_map.md`

## Fix

- Split Hot Follow workbench payload construction and projection repair out of `gateway/app/services/task_view.py`.
- Added `gateway/app/services/task_view_workbench_contract.py` as the presentation-only contract builder surface for:
  - compose plan normalization
  - compose last-attempt projection
  - pipeline and legacy pipeline row construction
  - workbench payload section assembly
  - final URL and final deliverable projection sync
  - ready-gate compose projection sync
- Preserved the existing `build_hot_follow_workbench_hub()` public import path and payload behavior.

## Not Fix

- No second/new production line work.
- No OpenClaw work.
- No router/service port merge.
- No compose ownership changes.
- No broad Skills runtime platform.
- No UI redesign or new workbench payload semantics.

## Follow-Up

- PR-2 should continue with router/service port merge and lazy router bridge removal.
- PR-4 should further tighten four-layer state ownership after this projection split.
- A future contract PR should add versioned workbench response schemas once the builder surface is stable.

## Validation

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/task_view.py gateway/app/services/task_view_workbench_contract.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`

Result: 27 passed.
