# VeoBase01 Contract Runtime Expansion Pass 3

Date: 2026-04-23
Branch: `VeoBase01`
Base SHA: `3e6dc57a7c780886359035a90e99c0cc9130fc81`

## Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Reading contract read:
   - `docs/contracts/engineering_reading_contract_v1.md`
4. Minimum task-specific authority files selected from the indexes:
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/production_line_runtime_assembly_rules_v1.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
   - `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`
5. Sufficiency note:
   - This pass only targets Hot Follow current-attempt route-summary,
     retriable-vs-terminal route classification, and advisory selection for
     the selected subset. It does not require broader scenario docs, new-line
     onboarding docs, UI/editor docs, or multi-role harness docs.
6. Missing-authority handling:
   - none; every expected authority file was present through the indexes.

## Bug Class Addressed

The bug was not "first dub failed." The bug was that current-attempt,
route-summary, ready-gate, and advisory interpretation collapsed a retriable
TTS-lane failure into terminal no-TTS/no-dub route truth.

The fixed shape is:

- subtitle/current target is ready
- TTS lane is expected
- no underlying lane/fact explicitly says no-dub terminal
- current audio is not ready because the dub/TTS/provider/audio generation
  attempt failed

That shape now remains `tts_replace_route`, sets
`retriable_dub_failure=true`, and does not set
`no_dub_route_terminal=true` or recommend `compose_no_tts`.

## Runtime Subset Expanded

Pass 3 expands contract runtime ownership into:

- intended route vs fallback route precedence for TTS-expected tasks
- route-summary selection for subtitle-ready/no-audio Hot Follow attempts
- retriable TTS/provider/audio generation failure classification
- true no-dub/no-TTS terminal route criteria
- `current_attempt.compose_allowed_reason` for the selected subset
- `current_attempt.subtitle_terminal_state` for the selected subset
- advisory selection for final-ready, retriable dub failure, and true no-TTS
  terminal paths

## Contract Sources Used

- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Modules Changed

- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/contract_runtime/advisory_runtime.py`
- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/contract_runtime/__init__.py`
- `gateway/app/services/hot_follow_route_state.py`
- `gateway/app/services/hot_follow_skills_advisory.py`
- `gateway/app/services/ready_gate/hot_follow_rules.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/tests/test_hot_follow_artifact_facts.py`
- `gateway/app/services/tests/test_hot_follow_skills_advisory.py`

## Ownership Removed

- `hot_follow_route_state.py` lost selected current-attempt route ownership:
  route map, selected-route precedence, route allowance,
  terminal-dub-lane normalization, and current-attempt summary rules now live
  in `contract_runtime/current_attempt_runtime.py`.
- `hot_follow_skills_advisory.py` no longer owns advisory selection for the
  selected final-ready / retriable-dub-failure / terminal-no-TTS subset. It
  consults `contract_runtime/advisory_runtime.py` before falling back to the
  existing skills bundle path for other advisory cases.
- `ready_gate/hot_follow_rules.py` and `ready_gate_runtime.py` consume the
  contract-runtime selected-route resolver rather than importing the route
  state compatibility shell as rule owner.
- `task_view_workbench_contract.py`, `task_view_presenters.py`, and
  `task_view_helpers.py` were reviewed for this subset; no new rule power was
  added there and no router changes were required.

## Validations

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/contract_runtime/advisory_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/hot_follow_route_state.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/services/ready_gate/hot_follow_rules.py gateway/app/services/status_policy/hot_follow_state.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_contract_runtime_projection_rules.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`
- `git diff --check`

## Regression Classes Covered

1. Voice-led / subtitle-ready / first TTS failure:
   - stays `tts_replace_route`
   - sets `retriable_dub_failure=true`
   - does not set no-TTS/no-dub terminal route truth
   - advisory recommends `retry_or_inspect_dub`, not `compose_no_tts`
2. Voice-led retry succeeds:
   - stays `tts_replace_route`
   - `audio_ready=true`
   - `compose_status=done`
   - final-ready advisory remains `continue_qa`
3. True no-dub/no-TTS terminal case:
   - remains allowed to resolve to terminal no-TTS when explicit route facts
     and no-dub/no-TTS allowance apply
4. Final-ready with scene-pack pending:
   - retained through existing publish/workbench ready-gate coverage as
     non-blocking and publishable

Live replay of task `a71bb3fd679e` was not run in this workspace. Regression
evidence is fixture/in-process coverage only.

## Risks

- This pass intentionally changes the old fallback where subtitle-ready +
  missing voiceover could become a legal no-TTS route without explicit no-dub
  facts. That fallback is the bug class fixed here.
- Advisory selection now has a contract-runtime pre-pass for the selected
  subset. Non-selected advisory cases still fall back to the existing skills
  runtime path.

## Rollback Path

Revert this pass by removing:

- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/contract_runtime/advisory_runtime.py`
- the projection/state-machine contract extensions
- the imports from `ready_gate_runtime.py`, `ready_gate/hot_follow_rules.py`,
  `status_policy/hot_follow_state.py`, and `hot_follow_skills_advisory.py`
- the route-state wrapper changes

Then restore `hot_follow_route_state.py` as the selected route/current-attempt
owner from the prior revision.

## Acceptance Judgment

Accepted for pass scope:

- first-dub-failure misclassification is fixed in contract-runtime coverage
- current-attempt route-summary for the selected subset is contract-runtime
  owned
- advisory resolution for the selected subset is contract-runtime owned
- helper/presenter/route-state files lost real rule ownership for the selected
  subset
- no scenario onboarding, new-line runtime, UI/editor work, or multi-role
  harness work was introduced
