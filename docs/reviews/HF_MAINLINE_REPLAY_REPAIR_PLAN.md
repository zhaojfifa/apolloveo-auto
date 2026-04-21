# Hot Follow Mainline Replay Repair Plan

Date: 2026-04-22

## 1. Mainline Repair Rationale

Use current `main` as the repair motherline.

Do not restart from scratch and do not build a new minimal line. Current `main` is closest to the real Hot Follow business shape: it contains the accumulated operator behavior, language/profile compatibility, target subtitle currentness work, no-dub compatibility, compose ownership hardening, and helper-translation isolation. Rebuilding from a minimal baseline risks losing those details.

The repair strategy is commit-by-commit replay and audit after PR-1, followed by a selective revert or narrow fix on a mainline-compatible branch. The goal is to repair mainline behavior without discarding accumulated business behavior.

PR-4 and PR-5 remain paused completely. This plan does not restart PR-4, does not touch PR-5, and does not authorize broad refactor or redesign.

## 2. Positive Samples To Preserve

Use these commits and notes as known-good or restored-once reference points:

- `1f02f2a3a339e193ed4039cf20aad13b30a30536` / tag `compose-heavy-input-stability-20260419`
  - Last tagged business baseline before the PR-1 / PR-2 / PR-3 and post-hotfix drift chain.
- `e970193` / branch `fix/hf-skipped-dub-recovery-after-subtitle-save`
  - Positive sample for clearing stale no-dub state after a valid subtitle save.
- `7a10f9a`
  - Mainline commit that recovered skipped Hot Follow dubbing after subtitle save.
- `dfdfa0c`
  - Positive sample for authoritative target subtitle save semantics: reject semantically-empty target subtitles before writing override/artifact truth.
- `6d3a346`
  - Positive sample for projection truth: lane, deliverables, workbench editor hydration, and artifact facts must not treat a timing-only target SRT as authoritative target subtitle truth.
- `49547e1` / branch `fix/hf-source-lane-target-write-mainline`
  - Restored-once positive sample for source-lane target subtitle write recovery from current `main`.
- `7243312`
  - Follow-up documentation on the same mainline-compatible minimal source-lane fix branch.

Existing fix notes to preserve:

- `docs/execution/ROOT_CAUSE_HF_TARGET_SUBTITLE_SAVE_CONTRACT.md`
- `docs/execution/HF_TARGET_SUBTITLE_FOLLOWUP_SPLIT_BRAIN_FIX.md`
- `docs/execution/HF_TRANSLATION_INPUT_BINDING_FIX.md`
- `docs/execution/HF_SOURCE_SUBTITLE_TRANSLATION_BINDING_FIX.md`
- `docs/execution/HF_MAINLINE_MINIMAL_FIX_OR_ROLLBACK_GATE.md` from `7243312`

## 3. Commit-By-Commit Drift Map After PR-1

### PR-1: `7d1fa1c` task view / workbench contract split

Files:

- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_workbench_contract.py`

Intended scope:

- Split Hot Follow workbench projection out of `task_view.py`.
- Keep runtime/business behavior stable.

Drift:

- Created a second subtitle projection surface.
- Made the target editor SRT-first through workbench projection.
- Exposed an existing backend weakness: timing-only SRT could be saved as target subtitle truth because the backend distinguished parseable SRT structure from neither semantic target text nor valid dub input.

Assessment:

- Not the source-lane missing-write root cause.
- It is the exposure/activation point for the `target_subtitle_empty` shape.

### PR-2: `adc7230` router service port merge

Files:

- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_router_actions.py`
- `gateway/app/services/op_auth.py`
- `gateway/app/routers/apollo_avatar.py`

Assessment:

- No evidence this commit changed source subtitle truth, target subtitle write ownership, subtitle semantic validation, dub recovery, compose readiness, or advisory routing for the two failure shapes.
- Keep it unless a later focused bisect proves otherwise.

### PR-3: `0435c15` compose ownership hardening

Files:

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`

Assessment:

- Moves compose lifecycle ownership into `CompositionService`.
- Does not directly alter source-lane translation, authoritative target subtitle save, semantic-empty target validation, or helper translation input semantics.
- Not the first break for either subtitle failure shape.

### `dfdfa0c` target subtitle save semantics

Positive fix:

- Adds `has_semantic_target_subtitle_text`.
- Rejects semantically-empty target subtitle saves with `422 target_subtitle_semantically_empty`.
- Prevents `_hf_sync_saved_target_subtitle_artifact` and `hf_sync_saved_target_subtitle_artifact` from uploading semantic-empty target subtitle artifacts.

Assessment:

- This is the repair point for the `target_subtitle_empty` admission problem.
- Do not revert this commit.

### `6d3a346` subtitle projection truth

Positive fix:

- Aligns `subtitle_helpers.py`, router compatibility lane state, `task_view.py`, `task_view_workbench_contract.py`, and artifact facts so timing-only target artifacts do not hydrate as current authoritative target subtitle truth.

Assessment:

- This is the repair point for split-brain projection after `dfdfa0c`.
- Do not revert this commit.

### `a589c99` target translation to source subtitle lane

Break introduced:

- Changes the main translate action from request-carried visible text translation into `input_source: "source_subtitle_lane"`.
- Adds `_hf_translate_source_subtitle_lane(...)` as the normal authoritative translation/write path.
- Backend source-lane resolver initially trusts only stored source subtitle inputs.

Failure shape:

- `subtitle_missing`: source subtitle can be visible to the operator, but target subtitle main object is not written because backend source-lane resolution fails before `_hf_save_authoritative_target_subtitle(...)`.

Assessment:

- This is the first exact re-break commit for authoritative target subtitle write from the normal translate workflow.

### `11aace7` source subtitle translation lane binding

Break widened:

- Frontend enables the main translate action from wider visible source-lane fields: `normalized_source_text`, `raw_source_text`, `origin_text`, or `parse_source_text`.
- Backend still does not accept the same visible request-carried source text when storage-backed normalized/origin SRT is absent.

Failure shape:

- `subtitle_missing`: UI says source lane exists; backend can still return `source_subtitle_lane_empty` or fail to write target subtitle truth.

Assessment:

- This is the second exact re-break commit. It widened the frontend/backend source-lane contract mismatch introduced by `a589c99`.

### `cfc50a0` and `385f2c1` no-TTS/no-dub state projection

Relevant behavior:

- `cfc50a0` adds advisory projection for `no_dub_route_terminal` and `compose_no_tts`.
- `385f2c1` changes route-local state so `no_tts_compose_allowed` / `no_dub_compose_allowed` can project through `current_attempt`, ready gate, and skills routing.

Failure presentation:

- Once upstream target subtitle truth is missing or empty, state/advisory can present the downstream result as a no-TTS/no-dub route rather than clearly leading with "translation did not write authoritative target subtitle."

Assessment:

- These commits do not create the missing target subtitle object.
- They are the exact state/advisory commits that can make the upstream write failure appear as a no-TTS route.
- `b4f13e0` later mitigates helper-translation-specific false no-TTS routing, but it does not repair the normal source-lane missing-write bug.

## 4. Two Failure-Shape Map

### Shape 1: `subtitle_missing`

Observed shape:

1. Source subtitle exists in the workbench.
2. Normal translate action is allowed.
3. Target subtitle main object is not written.
4. Canonical `vi.srt` is absent.
5. Dub remains skipped or blocked because target subtitle truth is missing.
6. Ready gate/advisory may surface `subtitle_missing`, `target_subtitle_empty`, or no-TTS/no-dub route consequences.

Exact re-break commits:

- First break: `a589c99`
- Widened by: `11aace7`
- First bad mainline merge containing both: `22f528a`

Root cause:

- Frontend and backend disagree on what qualifies as the source subtitle lane.
- The frontend can show source subtitle text that the backend source-lane resolver does not accept.
- The backend fails before calling `_hf_save_authoritative_target_subtitle(...)`.

Positive sample:

- `49547e1` accepts request-carried visible source text as fallback while preserving stored normalized/origin SRT preference.

### Shape 2: `target_subtitle_empty`

Observed shape:

1. Target subtitle artifact exists physically.
2. Artifact body is timing-only or semantically empty.
3. Artifact can be treated as authoritative target subtitle truth by some projection or downstream consumer.
4. Dub sees empty target input and routes into `target_subtitle_empty`.

Exact re-break / exposure commit:

- Exposure point: `7d1fa1c`

Why:

- PR-1 made the target editor SRT-first and split workbench projection, which exposed the old backend weakness where parseable timing-only SRT could be accepted as a saved target subtitle.

Exact repair commits already on `main`:

- `dfdfa0c`
- `6d3a346`

Current judgment:

- On inspected current `main`, these repair commits are still present and should prevent the standard save path from admitting semantically-empty target subtitle truth.
- If a current variant can still write semantic-empty `vi.srt`, the likely cause is a bypass of `_hf_save_authoritative_target_subtitle(...)` / `_hf_sync_saved_target_subtitle_artifact(...)` on a non-mainline branch or a replay that dropped the `dfdfa0c` / `6d3a346` guards.
- Do not solve this by weakening currentness or ready-gate logic. Audit all target subtitle artifact writers and require the same semantic guard.

## 5. Exact Re-Break Summary

Authoritative target subtitle write break:

- `a589c99` introduced the source-lane backend write path with too-narrow source input resolution.
- `11aace7` widened UI source-lane eligibility without widening backend accepted source truth.

Semantic-empty target SRT authoritative admission:

- `7d1fa1c` exposed the SRT-first editor/projection path that made timing-only target SRT admission visible and operational.
- `dfdfa0c` and `6d3a346` repair this on `main`; preserve both.

No-TTS/no-dub presentation of these failures:

- `cfc50a0` introduced advisory projection for terminal no-dub/no-TTS route.
- `385f2c1` expanded route-local no-TTS/no-dub terminal state propagation through route state, task view, and skills routing.
- `b4f13e0` is a positive mitigation for helper-translation failures and should be preserved.

## 6. Minimum Selective Revert / Repair Proposal

Preferred action:

1. Start a repair branch from current `main`.
2. Do not revert PR-1, PR-2, PR-3, `dfdfa0c`, or `6d3a346`.
3. Selectively apply the narrow source-lane write fix from `49547e1` onto current `main`.
4. Audit all target subtitle artifact writers for the `dfdfa0c` semantic guard:
   - `gateway/app/routers/hot_follow_api.py::_hf_save_authoritative_target_subtitle`
   - `gateway/app/routers/hot_follow_api.py::_hf_sync_saved_target_subtitle_artifact`
   - `gateway/app/services/subtitle_helpers.py::hf_sync_saved_target_subtitle_artifact`
   - direct upload/update paths that can write `mm.srt` / `vi.srt`
5. Add or preserve focused tests for both shapes.

Minimum code repair shape:

- In `gateway/app/static/js/hot_follow_workbench.js`, ensure the normal translate action sends the visible source text with `input_source: "source_subtitle_lane"`.
- In `gateway/app/routers/hot_follow_api.py::_hf_translate_source_subtitle_lane(...)`, prefer stored normalized source SRT, then stored origin SRT, then request-carried visible source text.
- If fallback text is plain text rather than SRT, translate it and normalize it into valid authoritative target SRT before saving.
- Always write through `_hf_save_authoritative_target_subtitle(...)`.
- Do not change ready gate, advisory, compose ownership, task view contract, or skills routing unless validation proves they still misclassify after the target write is repaired.

Selective revert fallback:

- If the narrow fix cannot be made cleanly, selectively revert only the source-lane contract portion of `a589c99` / `11aace7` while preserving:
  - helper-only translation separation,
  - semantic-empty target rejection from `dfdfa0c`,
  - projection truth alignment from `6d3a346`,
  - PR-1 / PR-2 / PR-3 accumulated architecture,
  - helper failure isolation from `b4f13e0` / `9d60d73`.

## 7. Business Guardrails For Any Repair

Every candidate repair must pass business guardrails, not only unit tests:

1. Source subtitle exists.
2. Translate writes a non-empty target subtitle main object.
3. Canonical `vi.srt` exists for Vietnamese target language.
4. Semantically-empty target SRT is rejected and cannot replace existing truth.
5. Rerun dub works after target subtitle write.
6. Compose works.
7. Final artifact exists.
8. Advisory/state does not present a normal translation write failure as a valid no-TTS route.

Files requiring the guardrail before merge:

- `gateway/app/static/js/hot_follow_workbench.js`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `skills/hot_follow/input_skill.py`
- `skills/hot_follow/routing_skill.py`

## 8. Pause Statement

PR-4 and PR-5 remain paused.

Do not redesign the line, do not start a new minimal implementation, do not do broad refactor, and do not touch PR-4 / PR-5. The immediate work is mainline-compatible repair: identify the exact drift commits, selectively fix or revert only the broken source-lane contract, and preserve accumulated Hot Follow business behavior.
