# VeoBase01 PR-4 Line Runtime And Skills Boundary

## Purpose

PR-4 freezes the next VeoBase01 runtime slice for Hot Follow: line registry references, skills bundle references, worker profile references, deliverable profile references, and asset sink profile references are now consumed by runtime instead of remaining ceremonial metadata.

This PR does not change translation, subtitle save, helper translation, dub, compose, or ready gate business semantics.

## Branch

- Branch: `VeoBase01-pr4-line-runtime-consumption-and-skills-boundary`
- Base: `VeoBase01`

## Mandatory Entry Files

The PR was started only after reading:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- relevant contracts under `docs/contracts/`
- line contract files under `docs/architecture/line_contracts/`

## Runtime References Consumed

| Reference | Runtime Consumer | Result |
| --- | --- | --- |
| `gateway.app.lines.base.LineRegistry` | `get_line_runtime_binding(...)` | resolves the active Hot Follow production line |
| `skills/hot_follow` | `load_line_skills_bundle(line)` | loads bundle id, line id, hook kind, and stage order |
| `docs/contracts/worker_gateway_runtime_contract.md` | line runtime reference resolver | confirms active worker profile contract reference |
| `docs/architecture/line_contracts/hot_follow_line.yaml` | line runtime reference resolver | reads primary and secondary deliverable kinds |
| `docs/contracts/status_ownership_matrix.md` | line runtime reference resolver | confirms asset sink profile reference and sink policy flag |

The runtime payload exposes these under `line.runtime_refs`.

## Skills Boundary

The Hot Follow skills bundle is now explicitly loaded through the skills runtime loader boundary.

Skills remain read-only strategy/advisory modules:

- they may advise, route, classify, warn, or recommend
- they may not write task truth
- they may not write subtitle, dub, compose, deliverable, ready gate, or asset sink truth
- they may not become a hidden state owner

## Business Preservation

The current business baseline remains the invariant:

- URL sample `c084b276e819`: parse done, subtitles done, dub done, compose done, final exists, `compose_ready=true`, `publish_ready=true`
- local sample `8501fc94c1c8`: parse done, subtitles done, dub done, `tts_voiceover_plus_source_audio` path valid

PR-4 does not touch:

- translation input/source logic
- target subtitle save contract
- helper translation behavior
- dub execution
- compose execution
- ready gate semantics
- second-line implementation

## Validation

Validation run:

- `python3.11 -m py_compile gateway/app/services/line_binding_service.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/tests/test_veobase01_contract_conformance.py gateway/app/services/tests/test_hot_follow_skills_advisory.py`
  - result: passed
- `git diff --check`
  - result: passed
- `python3.11 -m pytest gateway/app/services/tests/test_line_binding_service.py gateway/app/services/tests/test_veobase01_contract_conformance.py gateway/app/services/tests/test_skills_runtime.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_workbench_contract.py -q`
  - result: `43 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_source_audio_policy_persistence.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q -k 'not compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not subtitle_render_signature_tracks_minimal_retune_defaults'`
  - result: `145 passed, 2 deselected`

Representative business coverage:

- URL workbench path remains covered by `/api/hot_follow/tasks/{task_id}/workbench_hub` tests that assert `compose_ready=true`, `publish_ready=true`, final URL availability, and typed workbench validation.
- Local source-audio-preserved plus TTS path remains covered by current dub state tests that assert `audio_flow_mode == "tts_voiceover_plus_source_audio"`.
- Helper translation failure remains covered by subtitle binding tests that preserve `mm_srt_path`, `mm_audio_key`, `final_video_key`, `dub_current`, `compose_ready`, and `publish_ready`.

## Acceptance

PR-4 is acceptable only if:

- line runtime references are explicitly consumed
- skills boundary is explicit and read-only
- wire behavior remains compatible
- Hot Follow business behavior remains unchanged
- VeoBase01 is stable for PR-5 preparation after validation
