# Hot Follow Current-Branch Final Acceptance Freeze

## 1. Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/workbench_hub_response.contract.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
   - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
   - `docs/execution/VEOBASE01_EXECUTION_LOG.md`
4. Why these files were sufficient:
   - this pass is an acceptance/freeze judgment for Hot Follow four-layer state,
     contract-driven status, business-flow stability, and boundary stability
   - the selected contracts and execution notes cover the exact state, route,
     ready-gate, workbench, helper-side-channel, and preserve-source concerns
5. Missing-authority handling:
   - no indexed authority files were missing
   - the representative live task ids `791a826f4e11`, `c0dac743a540`, and
     `e7c248b90ef4` were not available in local repo artifacts or local
     `shortvideo.db`, so live replay evidence was not available in this
     workspace

## 2. Scope of this freeze pass

This pass did only:

- acceptance verification on the current branch
- baseline-freeze judgment against the four required dimensions
- one narrow same-branch correction forced by acceptance evidence

This pass did not:

- switch branches
- restart from `main` or `VeoBase01`
- widen into new-line work, scenario onboarding, or unrelated cleanup

## 3. Four-layer architecture acceptance

Judgment: accepted.

The current branch is materially operating with distinct layers:

- L1 step layer is represented by pipeline execution fields such as
  `parse_status`, `subtitles_status`, `dub_status`, `compose_status`,
  `publish_status`, and `last_step`
- L2 fact/truth layer is represented by subtitle/audio/final/helper/current
  artifact facts, including authoritative target subtitle existence/currentness,
  current audio existence/currentness, final existence/freshness,
  source-audio-preserved truth, helper failure state, and selected compose
  route evidence
- L3 gate/decision layer is represented by `current_attempt`,
  `selected_compose_route`, `compose_allowed`, `compose_execute_allowed`,
  `compose_blocked`, `publish_ready`, and ready-gate blocking reasons
- L4 presentation/projection layer is represented by workbench/publish payloads,
  `operator_summary`, `advisory`, and compatibility aliases shaped after
  authoritative projection and ready-gate evaluation

Acceptance evidence:

- `gateway/app/services/task_view_projection.py`,
  `gateway/app/services/status_policy/hot_follow_state.py`, and
  `gateway/app/services/task_view_presenters.py` preserve the L2/L3 to L4
  direction instead of letting workbench/publish recompute competing truth
- `gateway/app/services/contract_runtime/current_attempt_runtime.py` and
  `gateway/app/services/contract_runtime/ready_gate_runtime.py` keep route and
  gate decisions in runtime rule layers
- `gateway/app/services/tests/test_hot_follow_artifact_facts.py`,
  `gateway/app/services/tests/test_hot_follow_skills_advisory.py`,
  `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`,
  and `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
  now pass on this branch

Conclusion:

- each layer is materially distinguishable
- lower-layer truths are no longer casually replaced by upper-layer
  presentation logic
- the four-layer model is good enough to freeze as the Hot Follow baseline

## 4. Contract-driven status acceptance

Judgment: accepted.

Required checks:

- subtitle authority is now single-owned through
  `gateway/app/services/hot_follow_subtitle_authority.py`
- helper remains side-channel only once current subtitle/audio/final truth
  exists
- empty-body / non-authoritative subtitle success is blocked
- URL voice-led standard dubbing remains rule-stable on `tts_replace_route`
  for translation-incomplete/currentness-driven failure shapes
- local preserve-source route is explicitly separated by
  `preserve_source_route_no_target_subtitle_required`
- historical skip/failure history no longer overrides current truth when
  current subtitle/audio/final evidence exists
- publish/workbench/ready_gate/current_attempt are explained from the same
  truth set rather than separate router-local heuristics

Narrow correction applied during this pass:

- Myanmar manual subtitle save recovery still failed with `422` when legacy
  `my.srt` alias evidence was returned during helper-failure recovery
- `gateway/app/services/hot_follow_subtitle_currentness.py` now treats
  Myanmar `my.srt` as an accepted alias for canonical `mm.srt`
- focused coverage added in
  `gateway/app/services/tests/test_hot_follow_subtitle_currentness.py`
- this restored helper-failure recovery without weakening the general
  authoritative subtitle contract

Conclusion:

- status interpretation is now rule-driven enough to stop treating Hot Follow
  as an ad hoc exception line

## 5. Business-flow acceptance

Judgment: accepted.

The branch now behaves coherently across the current enterprise flow:

- task creation and parameter configuration feed explicit route/runtime inputs
- generation-in-progress remains operational L1 status, not final business
  truth
- subtitle/audio verification is evaluated by authoritative currentness and
  ready-gate rules
- regenerate/reconfirm paths preserve current-vs-historical separation
- finished video and publish semantics are tied to fresh final truth plus
  ready-gate output
- publish backfill / Scene Pack remain downstream and non-blocking once current
  final truth is ready
- archive/history remains visible without outranking current truth

Scene Pack judgment:

- correctly non-blocking relative to final/publish readiness

Conclusion:

- the operational flow is coherent enough to treat this branch as the first
  production-line baseline
- deliverables and publish semantics are stable enough for freeze

## 6. Boundary stability acceptance

Judgment: accepted.

Boundary checks:

- URL same-class tasks:
  successful URL and translation-incomplete URL cases are now separated by
  explicit rule/fact reasons rather than drifting between TTS and no-TTS
  interpretations
- Local preserve-source tasks:
  preserve-source route is explicitly explainable and no longer drifts into
  standard dubbing or fake target-subtitle-authority failure without named
  route facts
- Helper coexistence:
  helper failure/recovery no longer pollutes recovered current truth after
  authoritative subtitle/audio/final recovery, including manual save recovery
  after the narrow `my.srt` alias fix in this pass
- Historical event isolation:
  stale `target_subtitle_empty` / `dub_input_empty` history remains diagnostic
  only and does not override current truth

Conclusion:

- boundary behavior is stable enough to freeze

## 7. Evidence set

Representative evidence used in this pass:

- authoritative contracts:
  `docs/contracts/four_layer_state_contract.md`,
  `docs/contracts/status_ownership_matrix.md`,
  `docs/contracts/workbench_hub_response.contract.md`,
  `docs/contracts/hot_follow_ready_gate.yaml`,
  `docs/contracts/hot_follow_projection_rules_v1.md`,
  `docs/contracts/hot_follow_state_machine_contract_v1.md`
- current-branch execution evidence:
  `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
  and `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- runtime modules:
  `gateway/app/services/task_view_projection.py`,
  `gateway/app/services/status_policy/hot_follow_state.py`,
  `gateway/app/services/contract_runtime/current_attempt_runtime.py`,
  `gateway/app/services/contract_runtime/ready_gate_runtime.py`,
  `gateway/app/services/hot_follow_subtitle_authority.py`,
  `gateway/app/services/hot_follow_subtitle_currentness.py`
- targeted current-branch validation:
  `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q`
  - result: `61 passed`
  `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
  - result: `7 passed`
  `python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_currentness.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py`
  - result: passed
  `git diff --check`
  - result: passed

Live representative task evidence status:

- exact live replay for `791a826f4e11`, `c0dac743a540`, and `e7c248b90ef4`
  was not available locally
- local `shortvideo.db` did not contain those rows
- freeze acceptance is therefore based on contract/runtime inspection and
  focused in-process validation rather than live replay

## 8. Minimal corrections applied, if any

One narrow same-branch correction was applied because current acceptance
verification exposed a live failure:

- problem:
  manual subtitle save after helper failure still returned `422` and therefore
  did not fully satisfy helper coexistence / recovered-current-truth stability
- exact correction:
  accept legacy Myanmar `my.srt` as an authoritative alias of canonical
  `mm.srt` for currentness matching only
- files changed:
  - `gateway/app/services/hot_follow_subtitle_currentness.py`
  - `gateway/app/services/tests/test_hot_follow_subtitle_currentness.py`
- non-scope preserved:
  - no new route design
  - no refactor
  - no new-line work

## 9. Final freeze judgment

Final judgment: A. Freeze accepted

Meaning:

- the current branch is good enough to freeze as the Hot Follow
  contract-driven baseline
- the first production-line sample is now stable enough to stop churning Hot
  Follow internals for this boundary set

Exact judgment by acceptance dimension:

- four-layer architecture acceptance: accepted
- contract-driven status acceptance: accepted
- business-flow acceptance: accepted
- boundary stability acceptance: accepted

## 10. Next action after freeze

Next action:

- move upward into factory-level contract objects and line-template design
  using this branch as the frozen Hot Follow baseline
- do not reopen Hot Follow internals unless a new acceptance regression is
  identified against this baseline
