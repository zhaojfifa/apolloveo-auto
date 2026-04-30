# Hot Follow VeoBase02 Operational Validation

Date: 2026-04-30
Target branch: `VeoBase02`
Merged branch: `rebuild/hf-business-flow-and-state-machine`
Merge commit: `0314af0`

## Samples Validated

| Sample ID | Lane | Validation intent |
| --- | --- | --- |
| `hf-phase3-url-origin-only` | URL | `origin.srt` plus stale legacy `mm_srt_path` must not promote target subtitle closure or publish subtitle/script availability. |
| `hf-phase3-local-helper-telemetry` | Local upload | Helper provider exhaustion must stay helper telemetry only and must not satisfy subtitle truth, audio readiness, or compose readiness. |
| `hf-phase3-manual-save-vi-materialized` | Manual target subtitle save | Manual materialization must surface authoritative/current `vi.srt`, keep stale dub/compose snapshots invalid, and block compose until current audio exists. |

## Surface Checks

- Workbench, presenter, publish, and deliverable surfaces consumed the same authoritative/current subtitle truth.
- No sample showed both subtitle-missing and subtitle-available business truth.
- Audio stayed blocked unless target subtitle was authoritative/current.
- Compose stayed blocked unless authoritative/current target subtitle truth and current audio were both present.
- Legacy compatibility fields did not reintroduce subtitle split-brain in the tested surface layer.

## Follow-Up Cleanup Items

- Continue replacing legacy fixtures that assume audio can be current without explicit authoritative/current target subtitle truth.
- Keep `mm_srt` compatibility naming as an alias only; do not allow it to generate subtitle truth independently.
- Broader external-provider/media execution validation remains separate from this narrow operational surface validation.

## Validation Commands

- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_phase3_surface_validation.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_subtitle_stage_owner.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_phase3_surface_validation.py -q`

Result: both passed on `VeoBase02`.
