# Hot Follow State Table v1

Date: 2026-04-25
Status: Frozen docs-only authority packet

## Purpose

This table freezes the explicit Hot Follow state set and the reviewable
transition rules for each state.

State ids are contract ids. They are not instructions to rename runtime fields
in this pass.

## State Table

| State Id | Layer | Entry Conditions | Exit Conditions | Blocking Conditions | Allowed Transitions | Terminal | Retryable | Manual Action Allowed | Projection Expectations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_created` | L1/L4 | task row exists; downstream pipeline not yet materially started | raw artifact materialized | missing raw/source materialization | `raw_ready`, `parse_waiting` | no | no | yes | show created/pending only; do not imply parse success |
| `raw_ready` | L2/L4 | raw/source artifact exists | parse begins or parse outputs become ready | none beyond parse dependency | `parse_waiting`, `parse_ready` | no | no | yes | raw available; parse pending or runnable |
| `parse_waiting` | L1/L4 | `parse_status` is `pending` or `running` | parse succeeds, requires manual action, or fails terminally | raw missing, parse runtime blocked, provider/runtime failure | `parse_ready`, `parse_manual_intervention_required`, `parse_terminal_failed` | no | no | yes | parse waiting; no subtitle-ready implication |
| `parse_ready` | L1/L2/L4 | `parse_status=done`; parse outputs exist | subtitle lane begins | none at parse boundary | `subtitle_waiting` | no | no | yes | parse complete; subtitle lane unlocked |
| `subtitle_waiting` | L1/L2/L3/L4 | subtitle lane started but authoritative target subtitle is not current | subtitle becomes authoritative/current, retryable wait is recognized, manual action is required, or terminal failure occurs | authoritative target subtitle absent; subtitle currentness false; live subtitle formation blocked | `helper_sidechannel_waiting`, `translation_waiting_retryable`, `target_subtitle_ready`, `subtitle_manual_intervention_required`, `subtitle_terminal_failed` | no | no | yes | subtitle waiting or blocked; must not project no-dub terminal by default |
| `helper_sidechannel_waiting` | L2/L3/L4 | helper lane is still pending or unresolved while mainline subtitle truth is incomplete | helper resolves, warning-only retryable state is recognized, or manual action becomes required | helper output missing when helper is the live blocker; helper provider still unresolved | `target_subtitle_ready`, `helper_retryable_failure_warning_only`, `helper_resolved_with_retryable_provider_warning`, `subtitle_manual_intervention_required` | no | yes | yes | explicit helper waiting/warning state; never null/unknown helper shape |
| `translation_waiting_retryable` | L3/L4 | translation incomplete or equivalent currentness failure is active on the intended subtitle/dub path | subtitle authority is restored, retry is attempted, or manual/terminal subtitle state is declared | target subtitle not authoritative/current; route still expects subtitle completion | `subtitle_waiting`, `helper_sidechannel_waiting`, `target_subtitle_ready`, `subtitle_manual_intervention_required` | no | yes | yes | warning/retryable state; route stays mainline; forbidden from no-dub terminal projection |
| `helper_retryable_failure_warning_only` | L3/L4 | helper provider/output failed in a retryable way while mainline success is still possible | helper resolves, target subtitle becomes ready, or operator retries | helper failure evidence present but not authoritative mainline failure | `helper_sidechannel_waiting`, `helper_resolved_with_retryable_provider_warning`, `target_subtitle_ready`, `subtitle_manual_intervention_required` | no | yes | yes | expose helper warning only; must not downgrade authoritative subtitle/audio/final truth |
| `helper_resolved_with_retryable_provider_warning` | L3/L4 | mainline subtitle truth has recovered but helper warning residue remains relevant diagnostically | warning clears or downstream flow advances | none for mainline progression | `target_subtitle_ready`, `dub_waiting` | no | yes | yes | subtitle ready plus helper warning/advisory only |
| `target_subtitle_ready` | L2/L3/L4 | authoritative target subtitle exists; `target_subtitle_current=true`; authority source is current | dub lane begins or no-dub/no-TTS route is explicitly and legally selected | missing authority, stale subtitle, or surface still reports missing authority | `dub_waiting` | no | no | yes | subtitle ready must be consistent across workbench/publish/task detail |
| `dub_waiting` | L1/L2/L3/L4 | TTS/dub lane is active and current audio is not yet ready | audio becomes current, retryable wait is recognized, manual action is required, or terminal failure occurs | route expects TTS audio; `audio_ready=false`; provider/audio generation not yet successful | `dub_ready`, `translation_waiting_retryable`, `dub_manual_intervention_required`, `dub_terminal_failed` | no | no | yes | dub waiting on intended route; must not collapse into terminal no-TTS without explicit contract allowance |
| `dub_ready` | L1/L2/L3/L4 | `dub_status=done`; current audio artifact exists; `audio_ready=true`; `dub_current=true` | compose begins | none at dub-ready boundary | `compose_waiting` | no | no | yes | audio ready and current; top-level audio error must already be clear |
| `compose_waiting` | L1/L2/L3/L4 | compose path is active but current final is absent or stale | compose currentness becomes ready, manual intervention is required, or compose fails terminally | compose input blocked, derive failed, final absent, final stale, audio/subtitle dependency not ready | `compose_ready`, `compose_manual_intervention_required`, `compose_terminal_failed` | no | no | yes | compose waiting with explicit blocking reasons from ready gate only |
| `compose_ready` | L2/L3/L4 | current final exists and compose currentness is satisfied for the current route | final is recognized ready for publish path | final still stale against current attempt | `final_ready` | no | no | yes | compose ready; selected route must be unified across artifact facts/current attempt/ready gate |
| `final_ready` | L2/L3/L4 | current fresh final exists and current attempt is ready | publish gate is satisfied, publish manual action is invoked, or publish terminal failure occurs | final freshness lost or publish confirmation not yet granted | `publish_ready`, `publish_manual_intervention_required`, `publish_terminal_failed` | no | no | yes | final-ready truth dominates historical output and scene-pack residue |
| `publish_ready` | L4 | ready gate says publish-ready; final is current and fresh | none within current attempt | none | none | yes | no | yes | publish/workbench/task detail align on publishable current truth |
| `parse_manual_intervention_required` | L3/L4 | parse cannot continue automatically and operator action is required | operator restarts parse or re-enters intake path | parse runtime blocked or invalid input condition | `parse_waiting`, `raw_ready` | no | yes | yes | explicit manual parse stop; not terminal unless controller closes attempt |
| `subtitle_manual_intervention_required` | L3/L4 | subtitle line cannot progress automatically and requires operator action | subtitle retry/restart or authoritative subtitle is supplied | missing/contradictory subtitle authority; unresolved helper/manual review need | `subtitle_waiting`, `helper_sidechannel_waiting`, `target_subtitle_ready` | no | yes | yes | explicit manual subtitle state; never implicit no-dub fallback |
| `dub_manual_intervention_required` | L3/L4 | dub line cannot progress automatically and requires operator action | dub retry/restart or explicit route change under contract authority | provider exhausted, invalid voice config, or unresolved audio operator decision | `dub_waiting`, `dub_ready` | no | yes | yes | explicit manual dub state; keep intended route visible |
| `compose_manual_intervention_required` | L3/L4 | compose path requires operator intervention before progressing | compose retry/restart after blocking condition is resolved | compose input derive failed, compose blocked, or manual review required | `compose_waiting`, `compose_ready` | no | yes | yes | explicit manual compose state; blocking reasons remain authoritative |
| `publish_manual_intervention_required` | L4 | final is ready but publish confirmation or operator action is still required | publish confirmation is completed or publish fails terminally | confirmation policy pending or downstream publish sink issue | `publish_ready`, `publish_terminal_failed` | no | yes | yes | publish hold/confirmation only; do not downgrade final-ready truth |
| `parse_terminal_failed` | L1/L3/L4 | parse failure is terminal for the current attempt | new attempt only | terminal parse failure reason persists | none | yes | no | yes | terminal parse failure |
| `subtitle_terminal_failed` | L1/L3/L4 | subtitle failure is terminal for the current attempt | new attempt only | terminal subtitle failure reason persists | none | yes | no | yes | terminal subtitle failure; distinct from retryable translation waiting |
| `dub_terminal_failed` | L1/L3/L4 | dub failure is terminal for the current attempt | new attempt only | terminal dub failure reason persists | none | yes | no | yes | terminal dub failure; distinct from TTS retryable waiting |
| `compose_terminal_failed` | L1/L3/L4 | compose failure is terminal for the current attempt | new attempt only | terminal compose failure reason persists | none | yes | no | yes | terminal compose failure |
| `publish_terminal_failed` | L1/L4 | publish/distribution attempt failed terminally for the current attempt | new attempt only | terminal publish failure reason persists | none | yes | no | yes | publish failed after final-ready path |

## State Notes

### Explicit Retryable Set

The minimum retryable, non-terminal states are:

- `translation_waiting_retryable`
- `helper_retryable_failure_warning_only`
- `helper_resolved_with_retryable_provider_warning`

### Explicit No-Dub / No-TTS Boundary

The table above assumes:

- `subtitle_waiting`
- `translation_waiting_retryable`
- `dub_waiting`

do not become no-dub/no-TTS terminal states unless explicit route allowance and
route-consistent L2/L3 facts already exist.

### Projection Discipline

For every state:

- L4 may summarize but may not contradict L2/L3
- helper side-channel states remain separate from mainline readiness
- historical success does not satisfy current-ready truth
