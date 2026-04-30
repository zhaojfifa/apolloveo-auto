# Hot Follow VeoBase02 Route Authority Tightening

Date: 2026-04-30
Branch: `VeoBase02`

## Scope

- Unified route ownership for Hot Follow URL and local-upload tasks around one reduced process-state truth.
- Preserved the two business route decisions used by first-line flow: `tts_replace_route` and `preserve_source_route`.
- Added a formal local-upload route-stage action: `switch_local_preserve_to_tts_subtitle_flow`.
- Kept helper translation auxiliary. Helper failure remains telemetry/advisory and is not required for manual continuation into subtitle/dub flow.

## State Discipline

- L1 remains step execution only.
- L2 remains artifact facts only.
- L3 route/currentness is reduced by `hot_follow_process_state`.
- L4 surfaces consume the reduced route truth through `current_attempt`, `ready_gate`, advisory facts, and `operator_summary`.

## Operational Checks

- A local preserve-source testing task can remain on `preserve_source_route`.
- The formal route-stage action switches local tasks to `tts_replace_route` by updating route policy/action state, not subtitle truth.
- Helper failure does not block the formal switch or become the gateway for re-entering subtitle/dub flow.
- `current_attempt`, `hot_follow_process_state`, `ready_gate`, and `operator_summary` report the same selected route after the switch.

## Follow-Up Cleanup

- Existing compatibility fields such as `mm_srt` should continue to be treated as aliases only.
- Broader legacy tests that infer route truth from helper failure or raw source-audio policy should be migrated to consume process-state route truth.
