# VEOBASE01 Subtitle Authority Review

## 1. Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from indexes:
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/workbench_hub_response.contract.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
   - `docs/contracts/engineering_reading_contract_v1.md`
4. Review-specific reference material:
   - user-provided repair lessons summary from the task prompt:
     - target subtitle must be single-owned
     - helper is side-channel only
     - empty-body SRT must be blocked before success write
     - diagnosis must respect L1/L2/L3/L4
   - requested real-task ids:
     - `6b40d86589da`
     - `944e2e8e6f0d`
     - `91990da2b72f`
     - `796bf811a43b`
5. Missing-authority handling:
   - no indexed authority docs were missing
   - exact real-task payloads for the four ids were not present in the local repo
     or local `shortvideo.db`

## 2. Review question

Why has Hot Follow repeatedly collapsed into:

- `subtitle_missing`
- empty target subtitle truth
- `target_subtitle_empty` / `no_dub` / `no_tts` fallback

even though the underlying business intent is the standard voice-led
target-subtitle path?

Review judgment:

- this is primarily a contract problem, not a single local bug
- the failure class is a combination of:
  - split authoritative target-subtitle write ownership
  - helper side-channel leakage into step-success truth
  - semantic-empty subtitle acceptance on one subtitle write path
  - L4 masking after upstream L1/L2/L3 truth has already become inconsistent

## 3. Evidence set

Direct authority/code evidence used:

- [four_layer_state_contract.md](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/four_layer_state_contract.md)
- [status_ownership_matrix.md](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/status_ownership_matrix.md)
- [workbench_hub_response.contract.md](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/workbench_hub_response.contract.md)
- [hot_follow_projection_rules_v1.md](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/hot_follow_projection_rules_v1.md)
- [hot_follow_state_machine_contract_v1.md](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/hot_follow_state_machine_contract_v1.md)
- [hot_follow_ready_gate.yaml](/Users/tylerzhao/Code/apolloveo-auto/docs/contracts/hot_follow_ready_gate.yaml)
- [hot_follow_line.yaml](/Users/tylerzhao/Code/apolloveo-auto/docs/architecture/line_contracts/hot_follow_line.yaml)
- [hot_follow_api.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/routers/hot_follow_api.py)
- [steps_v1.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/steps_v1.py)
- [steps_text_support.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/steps_text_support.py)
- [hot_follow_subtitle_currentness.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/hot_follow_subtitle_currentness.py)
- [subtitle_helpers.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/subtitle_helpers.py)
- [task_view_presenters.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/task_view_presenters.py)
- [current_attempt_runtime.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/contract_runtime/current_attempt_runtime.py)
- [advisory_runtime.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/contract_runtime/advisory_runtime.py)
- [VEOBASE01_SUBTITLE_AUTHORITY_REPAIR.md](/Users/tylerzhao/Code/apolloveo-auto/docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_REPAIR.md)

Real-task evidence status:

- searched repo/workspace for `6b40d86589da`, `944e2e8e6f0d`, `91990da2b72f`,
  `796bf811a43b`: no local payload artifacts found
- queried local `shortvideo.db` `tasks.id` for those four ids: no rows found
- therefore the review cannot cite local live payload dumps for those exact ids

Formal bad-shape evidence still available from the user request and existing
execution notes:

- subtitle step may show `running` or `done` while effective subtitle reason is
  `subtitle_missing`
- target subtitle text fields can be empty
- `dub_input_text` can be empty
- `helper_translation.failed` can remain false for an upstream helper/provider
  failure shape
- downstream can fall into `no_tts_compose_route` / `no_dub_route_terminal`
  with `compose_no_tts` guidance

## 4. Authoritative target-subtitle truth model

Single authoritative target-subtitle truth should be:

- the canonical target subtitle artifact key/path:
  - persisted target subtitle artifact such as `mm_srt_path` or the target-lang
    variant selected by `hf_task_target_subtitle_key(...)`
- plus semantic subtitle body truth:
  - subtitle body must pass `has_semantic_target_subtitle_text(...)`
- plus currentness truth:
  - `target_subtitle_current`
  - `target_subtitle_current_reason`

Classification by field family:

- source subtitle truth:
  - `origin_srt_path`
  - normalized source subtitle text loaded from `subs/origin_normalized.srt`
- target subtitle truth:
  - persisted target subtitle artifact key/path
  - semantic body loaded from the authoritative artifact/override
  - `target_subtitle_current`
  - `target_subtitle_current_reason`
- helper translation side-channel fields:
  - `subtitle_helper_status`
  - `subtitle_helper_error_reason`
  - `subtitle_helper_error_message`
  - `subtitle_helper_provider`
  - `subtitle_helper_input_text`
  - `subtitle_helper_translated_text`
  - `subtitle_helper_target_lang`
- editable/persisted subtitle fields:
  - override file under `subtitles/subtitles_override.srt`
  - `subtitles_content_hash`
  - `subtitles_override_updated_at`
  - `subtitles_override_mode`
- canonical subtitle artifact fields:
  - `mm_srt_path`
  - target-lang selected subtitle filename
- dub-input binding fields:
  - `dub_input_text`
  - `dub_input_source`
  - `subtitle_ready`

Which fields are source of truth:

- authoritative target subtitle:
  - canonical target subtitle artifact key/path
  - semantic target subtitle body
  - `target_subtitle_current` and `target_subtitle_current_reason`

Which fields are projections only:

- `subtitle_ready`
- `subtitle_artifact_exists`
- `edited_text`
- `srt_text`
- `primary_editable_text`
- `dub_input_text`
- `ready_gate.*`
- `current_attempt.*`
- advisory and workbench presentation fields

Which fields must never overwrite authoritative target subtitle:

- any `subtitle_helper_*` field
- `parse_source_text`
- `origin_srt_path`
- `normalized_source_text`
- `dub_input_text`
- any L4 explanation or no-dub/no-TTS route summary

Conclusion:

- the design contract is single-owned
- the implementation is not single-owned in practice

## 5. Ownership map

Step-by-step ownership map:

1. Truth first created:
   - subtitle generation path in [steps_v1.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/steps_v1.py)
   - manual save / source-subtitle translation path in [hot_follow_api.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/routers/hot_follow_api.py)
2. Truth persisted:
   - `run_subtitles_step()` writes `origin_srt_path`, maybe `mm_srt_path`,
     `subtitles_status`, `target_subtitle_current`,
     `target_subtitle_current_reason`
   - `_hf_save_authoritative_target_subtitle()` writes override text, uploads the
     target subtitle artifact, updates `mm_srt_path`,
     `target_subtitle_current`, `target_subtitle_current_reason`
3. Truth projected:
   - `hf_subtitle_lane_state(...)` in [subtitle_helpers.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/services/subtitle_helpers.py)
   - duplicated `_hf_subtitle_lane_state(...)` in
     [hot_follow_api.py](/Users/tylerzhao/Code/apolloveo-auto/gateway/app/routers/hot_follow_api.py)
   - `build_hot_follow_current_attempt_summary(...)`
   - ready gate / advisory / workbench surface builders

Current leaks and duplications:

- leak 1:
  - `run_subtitles_step()` can persist `subtitles_status="ready"` even when
    `target_subtitle_authoritative` is false and no canonical target subtitle
    artifact is written
  - that is a direct L1 success write without L2 authoritative target subtitle
    truth
- leak 2:
  - `run_subtitles_step()` uses `subtitle_result_contract(...)` which accepts
    `mm_text` from step output but does not enforce semantic non-empty target
    subtitle before writing `subtitles_status="ready"`
  - empty or non-authoritative target subtitle can coexist with subtitle-step
    success
- leak 3:
  - authoritative subtitle save logic exists in router-local
    `_hf_save_authoritative_target_subtitle(...)`, while step orchestration has
    its own separate write path
  - that is split write ownership for the same business truth
- leak 4:
  - subtitle lane projection exists twice:
    - service-level `hf_subtitle_lane_state(...)`
    - router-local `_hf_subtitle_lane_state(...)`
  - duplicated projection increases drift risk at the L2/L3 boundary
- leak 5:
  - helper side-channel status is not part of the step-status ownership matrix
    and is persisted only on selected paths
  - before the recent repair, source-subtitle-lane helper failure did not write
    authoritative subtitle failure state
  - the remaining structural issue is that subtitles step success can still be
    recorded when target subtitle is explicitly non-authoritative

Ownership conclusion:

- truth is first created in more than one place
- truth is persisted through more than one path
- truth is projected through more than one loader
- that is the core ownership leak

## 6. Helper side-channel boundary

Exact contract boundary:

- helper may do:
  - provide translation assistance
  - provide sanitized helper failure truth
  - provide advisory context
  - provide operator-facing helper input/output history
- helper must never do:
  - become the authoritative target subtitle by itself
  - allow subtitle-step success to be persisted when authoritative target
    subtitle is absent
  - silently fail while downstream sees only `subtitle_missing`
  - overwrite a valid current target subtitle

Current-state assessment:

- helper output does not directly overwrite authoritative target subtitle on the
  main save path
- helper boundary is still violated indirectly because non-authoritative/helper
  subtitle outcomes can still coexist with `subtitles_status="ready"` in
  `run_subtitles_step()`
- that means helper/non-authoritative side-channel truth can contaminate mainline
  step-success truth even if it does not directly overwrite `mm_srt_path`

Answer to the review questions:

- can helper output overwrite authoritative target subtitle?
  - not directly on the reviewed main save path
  - indirectly, it can still distort the subtitle-success contract by allowing a
    non-authoritative target subtitle outcome to be treated as subtitle success
- can helper failure fail to propagate while still causing downstream
  `subtitle_missing`?
  - yes; that was already proven on the source-subtitle translation lane and
    structurally remains a risk anywhere helper-side facts are not written into
    authoritative subtitle failure state
- can helper success/failure leave target subtitle empty while L1/L2 look
  superficially successful?
  - yes; `subtitles_status="ready"` can still be written even when
    `target_subtitle_authoritative=false` or semantic target text is not proven

## 7. Empty-body subtitle failure model

The required contract rule is:

- empty-body SRT must be rejected before authoritative success write
- file existence alone is never sufficient for subtitle success truth

Current implementation state:

- correct on manual/router authoritative save path:
  - `_hf_save_authoritative_target_subtitle(...)` rejects semantic-empty target
    subtitle with `422`
- not correct on subtitles step path:
  - `run_subtitles_step()` writes `subtitles_status="ready"` after
    `subtitle_result_contract(...)` and currentness computation
  - currentness may correctly say:
    - `subtitle_missing`
    - `target_subtitle_empty`
    - `target_subtitle_source_copy`
    - `target_subtitle_translation_incomplete`
  - but L1 can still say subtitle step `ready`

Required distinctions:

1. source subtitle exists but target subtitle object is empty:
   - must be subtitle failure or non-authoritative incomplete state
   - must not be subtitle success
2. target subtitle file exists but body text is empty:
   - must be `target_subtitle_empty`
   - must not be authoritative target subtitle success
3. target subtitle artifact is absent:
   - must be `subtitle_missing`
   - must not be subtitle success if target subtitle was required
4. target subtitle artifact exists but is not current/usable:
   - may be non-ready currentness
   - must not be collapsed to clean success

Conclusion:

- empty-body subtitle acceptance is part of the failure class
- the blocking bug is not only downstream interpretation
- one subtitle write path still permits L1 success without semantic L2 target
  subtitle truth

## 8. Four-layer violation analysis

Expected four-layer behavior:

- L1 says whether subtitle execution ran and what status it ended in
- L2 says whether a real authoritative target subtitle exists
- L3 says whether the current attempt can dub/compose from that subtitle truth
- L4 explains the current attempt without inventing new truth

Current violations:

- L1/L2 violation:
  - subtitle step can be marked `ready` while authoritative target subtitle is
    missing, non-authoritative, empty, or not current
- L2/L3 violation:
  - subtitle lane currentness is derived from artifact/text semantics, but
    upstream writes can leave contradictory `subtitles_status` and
    `target_subtitle_current` combinations
- L3/L4 violation:
  - once `dub_input_text` is empty and `no_dub` heuristics trigger, current
    attempt and advisory can pivot toward `no_tts_compose_route` /
    `no_dub_route_terminal`
  - that can mask the primary upstream subtitle-authority failure

Rule for when `no_dub`/`no_tts` terminal is valid:

- only when explicit no-dub/no-TTS route facts exist
- only when the line contract allows the non-TTS route
- only when the task is genuinely silent/subtitle-led or otherwise explicitly
  no-dub eligible
- not when the intended path is standard voice-led target-subtitle + TTS and the
  real problem is missing/invalid target subtitle truth

Rule for when subtitle formation failure must remain primary truth:

- when target subtitle is missing because creation failed
- when target subtitle exists physically but semantic body is empty
- when target subtitle is non-authoritative or not current on a voice-led
  target-subtitle-expected path
- when helper/provider failure prevented authoritative subtitle formation

Rule for what advisory should say:

- if authoritative target subtitle is missing due upstream formation failure:
  - advisory should stay on subtitle formation/failure truth
  - not `compose_no_tts`
- if authoritative target subtitle is current and TTS lane later fails:
  - advisory may say retry/inspect dub
- if explicit no-dub/no-TTS terminal path truly applies:
  - advisory may say compose without TTS

Conclusion:

- L4 masking is part of the failure class
- but it is secondary
- the first failure is upstream contract inconsistency between subtitle-step
  success and authoritative target subtitle truth

## 9. Contract corrections required before repair

1. Authoritative target subtitle contract correction
   - make authoritative target subtitle write single-owned
   - subtitles step must not persist `subtitles_status="ready"` unless an
     authoritative target subtitle has been validated and persisted
   - non-authoritative helper-only subtitle outcomes must not share the same
     success state as authoritative target subtitle creation
2. Helper side-channel contract correction
   - freeze `subtitle_helper_*` as side-channel-only fields
   - helper failures must either:
     - surface as authoritative subtitle failure when no current target subtitle
       exists, or
     - remain advisory-only when a valid current target subtitle already exists
   - helper/non-authoritative results must never imply subtitle-step success by
     themselves
3. Empty-body subtitle acceptance contract correction
   - apply semantic-empty rejection to every authoritative subtitle write path,
     not only manual/router save
   - physical file presence and raw `mm_srt` payload are insufficient
4. Subtitle -> dub_input binding correction
   - `dub_input_text` must bind only from validated authoritative current target
     subtitle
   - any missing/empty/non-current target subtitle on a voice-led path must
     remain a subtitle-authority block, not a no-dub explanation
5. Four-layer projection/advisory correction
   - L4 must not resolve `compose_no_tts` while upstream primary truth is
     subtitle-authority failure
   - no-dub/no-TTS terminal interpretation must require explicit contract-backed
     no-dub eligibility

## 10. Repair order recommendation

Recommended next pass name:

- `VeoBase01-subtitle-authority-contract-correction`

Recommended order:

1. unify authoritative target subtitle write ownership
2. freeze helper side-channel boundary against subtitle-step success truth
3. enforce semantic-empty rejection on every authoritative subtitle write path
4. re-derive `dub_input_text` only from authoritative current target subtitle
5. only then revisit L4 no-dub/no-TTS/advisory shaping

Clear judgment:

- the current problem is primarily a contract problem
- `VeoBase01` should next do a subtitle-authority contract correction pass
- downstream `no_dub`/`no_tts` logic should remain effectively untouched until
  subtitle truth is corrected at the authoritative layer
- current contract tightening should stay paused until subtitle-authority
  contract repair is complete

## 11. What must NOT be patched downstream

- do not patch advisory text alone
- do not patch `no_dub_reason` or `compose_no_tts` selection alone
- do not patch workbench/publish labels alone
- do not patch `dub_input_text` with fallback text from helper/source subtitle
  when authoritative target subtitle is missing
- do not let presentation code invent subtitle truth
- do not continue broader contract tightening until subtitle-authority truth is
  single-owned and semantically validated
