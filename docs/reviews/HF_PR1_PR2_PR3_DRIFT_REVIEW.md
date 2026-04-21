# HF PR-1 / PR-2 / PR-3 Drift Review

Date: 2026-04-21

## Scope

Review-only pass across:

- PR-1 `7d1fa1c` task view / workbench contract split
- PR-2 `adc7230` router / service port merge
- PR-3 `0435c15` compose ownership hardening
- follow-up hotfixes:
  - `dfdfa0c` target subtitle save contract
  - `6d3a346` subtitle projection split-brain alignment
  - `a589c99` target translation input binding
  - `11aace7` source subtitle translation lane binding
  - `b4f13e0` helper translation isolation
  - `9d60d73` helper translation UI summary

This document answers where the Hot Follow business line and the state/projection line diverged, without proposing broader architecture work.

## 1. Baseline

### Last known-good baseline

- Tag: `compose-heavy-input-stability-20260419`
- Commit: `1f02f2a`

Why this baseline:

- It is the last tagged mainline baseline before the target-subtitle save / translation-input sequence landed.
- The current live symptom does not exist in the documented baseline business path.

### First known-bad range

- Bad range: `a589c99..11aace7`
- First bad mainline merge: `22f528a`

### Current live broken symptom

Observed business-line symptom:

1. source subtitle exists in the workbench
2. target subtitle main object stays empty
3. subtitle step can surface `done`-like or advanced status while target subtitle truth is still missing
4. `subtitle_ready=false` with `subtitle_missing`
5. dub is skipped with `target_subtitle_empty`

Judgment:

- The live break is not primarily in compose, ready-gate, advisory, or operator summary.
- The primary break is earlier: the normal translate action does not reliably reach the authoritative target subtitle write owner.

## 2. Per-PR Drift Table

### PR-1: `7d1fa1c` task view / workbench contract split

Files touched:

- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `docs/execution/PRE_LINE_STARTUP_PR1_TASK_VIEW_CONTRACT_SPLIT.md`

Intended change:

- Move Hot Follow workbench payload assembly into a presentation-only contract builder.
- Keep public behavior stable and avoid runtime/business ownership changes.

Actual contract effect:

- `task_view.py` became an L4 orchestration surface that delegates payload assembly into `task_view_workbench_contract.py`.
- Subtitle projection became explicitly split between:
  - lane truth from `hf_subtitle_lane_state(...)`
  - projection fields assembled in `_subtitles_section(...)`

Possible drift introduced:

- PR-1 created a second projection surface for subtitle editor hydration.
- In the original PR-1 contract file, `_subtitles_section(...)` still fell back to raw `subtitles_text` / `normalized_source_text` inputs instead of trusting lane-authoritative `primary_editable_text`.
- That did not create the later business-line write failure, but it did create projection drift risk and later enabled split-brain after `dfdfa0c` tightened save semantics.

Exact assessment:

- Business line A-E: not broken by PR-1.
- Projection line G-H: at risk after PR-1 because presentation remained partially independent from lane-authoritative truth.
- This risk was later realized and repaired by `6d3a346`.

### PR-2: `adc7230` router / service port merge

Files touched:

- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_router_actions.py`
- `gateway/app/services/op_auth.py`
- `gateway/app/routers/apollo_avatar.py`
- `gateway/app/services/tests/test_task_router_actions.py`
- `docs/execution/PRE_LINE_STARTUP_PR2_ROUTER_SERVICE_PORT_MERGE.md`

Intended change:

- Remove lazy router imports and introduce explicit action ports.
- Reduce router-to-router coupling without changing Hot Follow runtime semantics.

Actual contract effect:

- Generic task-router action dispatch moved to registered ports.
- No reviewed A-H subtitle truth owner moved in this PR.
- No Hot Follow subtitle save owner, translation owner, or compose gating source changed here.

Possible drift introduced:

- Architectural risk only: the system still kept duplicated router compatibility surfaces elsewhere.
- No evidence that PR-2 changed source subtitle truth, target subtitle write ownership, dub enablement, compose eligibility, ready-gate, or operator summary behavior for the current symptom.

Exact assessment:

- PR-2 did not introduce the current Hot Follow business-line break.
- PR-2 also did not introduce the subtitle projection split-brain.

### PR-3: `0435c15` compose ownership hardening

Files touched:

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `gateway/app/services/tests/test_compose_service_contract.py`
- `docs/execution/PRE_LINE_STARTUP_PR3_COMPOSE_OWNERSHIP_HARDENING.md`

Intended change:

- Move compose startup/finalize lifecycle ownership to `CompositionService.execute_hot_follow_compose_contract(...)`.
- Make compose state writes single-owner.

Actual contract effect:

- Compose lifecycle truth moved behind `CompositionService._write_compose_state(...)`.
- Routers stopped being independent compose state writers.
- Compose reads still occur via workbench/state policy after compose ownership writes land.

Possible drift introduced:

- No direct subtitle-truth drift.
- No direct translation-input drift.
- No change to the authoritative target subtitle save endpoint.
- Compose now more faithfully consumes upstream subtitle/audio truth instead of carrying router-local lifecycle scripts.

Exact assessment:

- PR-3 changed F/G/H ownership boundaries around compose lifecycle.
- PR-3 did not introduce the current symptom where translation fails to produce target subtitle truth.

## 3. Follow-up Hotfix Drift

### `dfdfa0c` enforce target subtitle save semantics

Intended change:

- Reject semantically empty target subtitle saves.
- Stop timing-only SRT from becoming authoritative target truth.

Actual effect:

- Correctly fixed the owner boundary for manual subtitle save.
- Made `patch_hot_follow_subtitles(...)` and `_hf_sync_saved_target_subtitle_artifact(...)` semantic-text aware.

Drift still left behind:

- Projection surfaces still had independent fallback behavior.
- Invalid legacy artifacts could still leak into editor hydration and deliverable projection until `6d3a346`.

### `6d3a346` align subtitle projection truth

Intended change:

- Remove subtitle split-brain across lane, deliverables, and artifact facts.

Actual effect:

- Correctly re-aligned projection surfaces to lane-authoritative truth.
- `task_view_workbench_contract._subtitles_section(...)`, `task_view.hf_deliverables(...)`, and `hot_follow_route_state.build_hot_follow_artifact_facts(...)` now read `subtitle_lane` truth instead of raw physical existence alone.

Drift result:

- This fixed projection split-brain, not the later business-line translation break.

### `a589c99` bind target translation to source subtitle lane

Intended change:

- Separate helper-only translation from normal source-subtitle-lane translation.

Actual effect:

- Frontend main translate action stopped behaving like generic text translation and started declaring `input_source: "source_subtitle_lane"`.
- Backend `translate_hot_follow_subtitles(...)` started routing source-lane requests into `_hf_translate_source_subtitle_lane(...)`, which expected stored source subtitle lanes.

Drift introduced:

- The request contract changed from "translate this visible text" to "translate from authoritative source subtitle lane".
- The frontend/operator-visible source lane and backend-accepted source lane were no longer the same contract.

This is the first commit that introduced the current business-line break.

### `11aace7` bind source subtitle translation lane

Intended change:

- Broaden the frontend’s notion of source-lane visibility.

Actual effect:

- Frontend main translate button became available when `normalized_source_text`, `raw_source_text`, `origin_text`, or `parse_source_text` was visible in the hub.
- Backend source-lane resolver still only trusted storage-backed normalized/origin subtitle text.

Drift introduced:

- The visible source lane widened in the UI.
- The accepted source lane in backend resolution did not widen equivalently.
- This widened the mismatch created by `a589c99`.

### `b4f13e0` and `9d60d73` helper translation isolation

Intended change:

- Keep helper/provider translation failure separate from authoritative target subtitle truth.
- Improve operator messaging.

Actual effect:

- Helper translation state became projection/advisory input.
- Helper failure could influence routing/advisory, but should not write target subtitle truth.

Assessment:

- These commits are not the root cause of the current live break.
- They correctly consume the absence of authoritative target subtitle truth once the translation/write contract has already failed.

## 4. End-to-End Ownership Map

| Stage | Authoritative truth source | Single write owner | Downstream readers | PR-1/2/3 changed it? | Current live behavior vs intended contract |
| --- | --- | --- | --- | --- | --- |
| A. source subtitle truth | `origin_normalized.srt` or `origin_srt_path`, plus projected source-lane text in `hf_subtitle_lane_state(...)` / `_hf_subtitle_lane_state(...)` | parse/subtitle extraction owners, not the workbench | frontend workbench, translate action, route/advisory | PR-1 changed presentation path only; PR-2 no; PR-3 no | Intended contract is only partially matched. UI can show source subtitle truth the backend source-lane translation path does not accept. |
| B. target translation input resolution | `_hf_translate_source_subtitle_lane(...)` for normal lane; helper-only branch in `translate_hot_follow_subtitles(...)` for assisted input | `gateway/app/routers/hot_follow_api.py::translate_hot_follow_subtitles` | target subtitle write path, frontend translate flow | PR-1 no; PR-2 no; PR-3 no. Follow-up `a589c99` and `11aace7` changed it. | Broken on live line. Frontend and backend disagree on what counts as source-lane input. |
| C. target subtitle authoritative write | `_hf_save_authoritative_target_subtitle(...)` and `patch_hot_follow_subtitles(...)` | `gateway/app/routers/hot_follow_api.py` | subtitle lane state, currentness, dub recovery, workbench reload | PR-1/2/3 no. Follow-up `dfdfa0c` hardened it. | Current contract is correct. The issue is often never reaching this owner from the normal translate path. |
| D. target subtitle artifact generation (`vi.srt`) | `_hf_sync_saved_target_subtitle_artifact(...)` / `hf_sync_saved_target_subtitle_artifact(...)` | same authoritative subtitle save owner | deliverables, artifact facts, compose subtitle resolver | PR-1/2/3 no. Follow-up `dfdfa0c` and `6d3a346` aligned it. | Correct if stage C is reached. When C is skipped, `vi.srt` is not produced. |
| E. dub enablement / skip decision | `subtitle_lane.subtitle_ready`, currentness, empty-dub recovery updates, voice state | subtitle save owner clears stale empty skip; dub/runtime owners write dub attempt state | route state, ready gate, operator summary, compose | PR-1 no; PR-2 no; PR-3 no direct change | Current live behavior matches intended contract. Dub is skipped because authoritative target subtitle truth is genuinely missing. |
| F. compose eligibility | ready gate + route state + compose input facts; compose lifecycle owner is `CompositionService.execute_hot_follow_compose_contract(...)` | compose service | workbench compose button, current attempt, final compose route | PR-3 yes; PR-1/2 no direct change | Current behavior matches intended contract. Compose is blocked downstream because subtitle/audio prerequisites are not ready. |
| G. ready_gate projection | `compute_hot_follow_state(...)` and ready-gate evaluation, then projected through `task_view.py` / `task_view_workbench_contract.py` | status/ready-gate computation; task view is projection-only | frontend, skills input, operator summary | PR-1 changed projection split; PR-3 changed compose lifecycle input to it | Current behavior matches intended contract for the live symptom. `subtitle_missing` is downstream-correct once target truth is absent. |
| H. advisory / operator_summary projection | `hot_follow_route_state.py`, `task_view.py`, `skills/hot_follow/input_skill.py`, `skills/hot_follow/routing_skill.py` consuming `artifact_facts`, `current_attempt`, `ready_gate` | projection layer only; no truth writes allowed | operator workbench guidance | PR-1 changed projection shape; PR-2 no; PR-3 changed compose lifecycle inputs | Current behavior is downstream-correct, though it can look misleading because it reports the consequence of the earlier write failure rather than the earlier failure itself. |

## 5. Exact Drift Point

### Primary break location

The current line breaks during source-lane resolution inside the backend translation path, before the authoritative target subtitle write.

Exact sequence:

1. Frontend main translate action sends `input_source: "source_subtitle_lane"` through `translateCurrentSubtitles(...)` and the main translate button handler in `gateway/app/static/js/hot_follow_workbench.js`.
2. Backend receives the request in `translate_hot_follow_subtitles(...)`.
3. Backend delegates to `_hf_translate_source_subtitle_lane(...)`.
4. In the bad mainline range, `_hf_translate_source_subtitle_lane(...)` only trusted storage-backed normalized/origin subtitle inputs and did not reliably use visible request-carried source text.
5. Therefore the normal translate action could stop at `source_subtitle_lane_empty` or equivalent no-write behavior.
6. Because stage C never ran, the target subtitle main object stayed empty.
7. Stages E-H then behaved correctly against empty target truth:
   - `subtitle_ready=false`
   - `subtitle_missing`
   - dub skip `target_subtitle_empty`
   - compose/advisory remain downstream-blocked

### Answered against requested checkpoints

- Before translation request: no. The request is sent.
- During source lane resolution: yes. This is the primary current break.
- During authoritative target subtitle write: no for the live symptom; that was a separate earlier bug fixed by `dfdfa0c`.
- During target artifact generation: no for the live symptom; artifact generation fails only because authoritative write is never reached.
- During status derivation: no for the live symptom; status derivation is consuming empty target truth correctly.

### Important distinction

There are two different drifts in this line:

1. Earlier save/projection drift:
   - fixed by `dfdfa0c` and `6d3a346`
   - problem: timing-only or invalid target subtitle truth could split save, deliverables, and projection

2. Current live business-line drift:
   - introduced by `a589c99`, widened by `11aace7`
   - problem: normal source-subtitle translation does not reliably reach the authoritative target subtitle write owner

The current live symptom belongs to drift (2), not drift (1).

## 6. File-by-File Contract Notes

### `gateway/app/static/js/hot_follow_workbench.js`

Current truth:

- `renderSubtitles()` hydrates from `subtitles.primary_editable_text` and source-lane fields.
- Main translate button reads visible source text from `normalized_source_text || raw_source_text || origin_text || parse_source_text`.
- `patchSubtitles(...)` remains the explicit authoritative target-subtitle save API client.

Drift note:

- After `a589c99` / `11aace7`, the main translate flow asserted a stricter backend source-lane contract than the UI could guarantee.
- The frontend was not wrong to expose visible source subtitle truth. The backend source-lane resolver was too narrow for that UI contract.

### `gateway/app/routers/hot_follow_api.py`

Current truth:

- `patch_hot_follow_subtitles(...)` is the explicit authoritative target subtitle save endpoint.
- `_hf_save_authoritative_target_subtitle(...)` is the single write owner for saved target subtitle truth.
- `_hf_sync_saved_target_subtitle_artifact(...)` owns canonical target subtitle artifact generation.
- `translate_hot_follow_subtitles(...)` chooses whether a translate request is helper-only or source-lane authoritative.

Drift note:

- The business-line break sits in `_hf_translate_source_subtitle_lane(...)`, not in downstream ready-gate or compose code.

### `gateway/app/services/subtitle_helpers.py`

Current truth:

- `hf_subtitle_lane_state(...)` is the read-side authoritative lane summary for projection consumers.
- `hf_dub_input_text(...)` only returns semantic target subtitle text.
- `hf_sync_saved_target_subtitle_artifact(...)` refuses semantically empty target subtitle artifacts.

Drift note:

- This file is currently aligned with intended contract after the save/projection hotfixes.
- It is not the root cause of the live business-line failure.

### `gateway/app/services/task_view.py` and `task_view_workbench_contract.py`

Current truth:

- They build L4 projection.
- `hf_deliverables(...)` now gates subtitle deliverable exposure on lane-authoritative subtitle existence.
- `_subtitles_section(...)` now hydrates target editor fields from `subtitle_lane.primary_editable_text`.

Drift note:

- PR-1 created the projection split.
- `6d3a346` brought this projection back into alignment.
- These files are not the current business-line break.

### `gateway/app/services/hot_follow_route_state.py`, `skills/hot_follow/input_skill.py`, `skills/hot_follow/routing_skill.py`

Current truth:

- They read artifact facts, current attempt, and ready gate.
- They do not own subtitle truth or translation input resolution.

Drift note:

- They can surface misleading operator guidance if upstream failure is hidden, but they are not the primary break.
- For the current symptom, they are correctly reporting the consequence of missing target subtitle truth.

### `gateway/app/services/compose_service.py`

Current truth:

- PR-3 made compose lifecycle single-owner in `execute_hot_follow_compose_contract(...)`.

Drift note:

- Compose ownership hardening is orthogonal to the current regression.

## 7. Minimum Recovery Recommendation

### First file/function to change

Change first:

- `gateway/app/routers/hot_follow_api.py::_hf_translate_source_subtitle_lane(...)`

Reason:

- This is the first point where the normal source-subtitle workflow fails to reach the authoritative target subtitle write owner.
- Fixing downstream projection or compose would only mask the real problem.

The minimum matching frontend change, if mainline still lacks it, is:

- `gateway/app/static/js/hot_follow_workbench.js`
  - ensure the main translate action sends the visible source text along with `input_source: "source_subtitle_lane"`

### What should NOT be touched

Do not touch first:

- `gateway/app/services/compose_service.py`
- ready-gate engine or compose policy logic
- `skills/hot_follow/*` routing/advisory logic
- broad `task_view.py` / presenter cleanup
- PR-4 style four-layer beautification
- router/service platform cleanup unrelated to source-lane translation

Reason:

- These consumers are not the primary write-path break.
- Changing them first would blur the contract review and risk masking the actual regression.

### Regression tests that must be added first

Add or keep focused coverage for:

1. source-lane translation persists full target SRT when normalized source SRT exists
2. source-lane translation persists full target SRT when only origin SRT exists
3. source-lane translation persists authoritative target subtitle when storage-backed source lane is missing but visible plain source text is supplied
4. helper-only translation remains non-authoritative and does not write target subtitle truth
5. authoritative target subtitle save still rejects semantically empty target subtitle input
6. canonical target subtitle synchronization still writes `vi.srt` and re-enables downstream dub recovery when valid target subtitle is produced

## 8. Final Judgment

### Exact drift introduced by PR-1

- PR-1 introduced projection-surface split risk, not the current business-line write failure.
- It created a second subtitle projection contract that later needed `6d3a346` to realign with lane-authoritative truth.

### Exact drift introduced by PR-2

- No direct subtitle business-line drift.
- Router/service boundaries moved, but no A-H truth owner relevant to this symptom changed.

### Exact drift introduced by PR-3

- Compose lifecycle ownership moved into `CompositionService`.
- No direct target subtitle translation/write drift was introduced.

### Exact current break in the business line

- The current live line breaks in backend source-lane resolution inside `_hf_translate_source_subtitle_lane(...)`, before `_hf_save_authoritative_target_subtitle(...)` is reached.
- `a589c99` introduced the broken contract.
- `11aace7` widened it by making the UI source-lane visibility broader than the backend-accepted source-lane truth.

### Minimum next fix

- Fix the source-lane translation contract first.
- Make the backend accept the same visible source-lane text the UI uses when storage-backed normalized/origin SRT is missing.
- Keep authoritative target subtitle save semantics, projection truth fixes, ready-gate, advisory, and compose ownership unchanged.
