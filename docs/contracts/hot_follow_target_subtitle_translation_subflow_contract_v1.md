# Hot Follow Target Subtitle Translation Subflow Contract v1

Date: 2026-04-29
Status: Active Hot Follow subflow contract

## Purpose

This contract makes target subtitle translation a first-class Hot Follow
subflow instead of a loose helper-pending result.

The subflow exists inside the first production line and is consumed by the
canonical Hot Follow process reducer. It does not add provider behavior and it
does not replace target subtitle authority/currentness. It explains why the
voice-led target subtitle is or is not authoritative/current.

## Layer 1 Fact Model

Layer 1 facts are pure inputs. They do not carry readiness, legality, terminal,
or retry meaning.

Allowed facts:

- `origin_subtitle_exists`
- `origin_subtitle_key`
- `origin_subtitle_text_present`
- `helper_translation_requested`
- `helper_translation_status`
- `helper_raw_output_received`
- `helper_output_state`
- `helper_provider_health`
- `helper_error_reason`
- `helper_error_message`
- `helper_input_text`
- `helper_translated_text`
- `helper_target_lang`
- `helper_requested_at`
- `helper_responded_at`
- `helper_failed_at`
- `retry_count`
- `target_subtitle_artifact_exists`
- `target_subtitle_materialized`
- `target_subtitle_current`
- `target_subtitle_authoritative_source`
- `target_subtitle_current_reason`
- `manual_override_present`
- `manual_override_updated_at`

Rule:

- These facts answer what exists or what happened. They do not decide whether
  the subflow is waiting, retryable, terminal, or authoritative.

## Layer 2 Contract State

The canonical state owner is:

- `gateway/app/services/hot_follow_translation_subflow.py`

Allowed states:

- `translation_not_required_for_route`
- `translation_not_started`
- `translation_requested`
- `translation_inflight`
- `translation_output_pending_retryable`
- `translation_output_received_unmaterialized`
- `translation_materialization_failed_retryable`
- `translation_materialization_failed_terminal`
- `target_subtitle_authoritative_current`
- `target_subtitle_stale_after_edit`
- `manual_target_subtitle_override_current`

Derived contract fields:

- `waiting`
- `retryable`
- `terminal`
- `authoritative_current`
- `materialized`
- `blocking_reason`
- `operator_action`

Rules:

- `target_subtitle_authoritative_current` requires both target subtitle
  currentness and authoritative source truth.
- `manual_target_subtitle_override_current` is a current authoritative target
  subtitle with manual override evidence.
- Helper output received without a materialized authoritative target subtitle is
  not provider pending. It is `translation_output_received_unmaterialized` or a
  materialization failure state.
- Provider pending or retryable provider failure without materialized target
  subtitle is retryable waiting, not terminal line failure.
- Terminal state requires explicit terminal helper/provider evidence or a
  terminal materialization reason.
- Route-not-required state is legal only when the canonical process reducer
  selects a non-target-dub route.

## Layer 3 Runtime / Reducer Consumption

`reduce_hot_follow_process_state()` consumes the subflow object and derives:

- `subtitle_process_state`
- `subtitle_translation_waiting_retryable`
- `dub_waiting_for_target_subtitle`
- `audio_ready`
- `compose_allowed`
- `compose_reason`
- `subtitle_terminal_state`

Rule:

- The main reducer may map subflow states into existing compatibility process
  states, but it must not independently re-derive helper-pending semantics.

## Layer 4 Projection / Advisory

Workbench, current attempt, ready gate, operator summary, and advisory consume
the reducer-owned subflow object.

Allowed projection meanings:

- waiting on provider work
- translation returned but target SRT materialization is not complete
- materialization failed and retry is allowed
- terminal translation/materialization failure
- manual target subtitle override is current
- authoritative target subtitle is current

Rule:

- Presentation layers may expose compatibility aliases, but they may not create
  new translation truth or replace the subflow state with local pending
  heuristics.

## Compatibility Fields

These legacy fields may remain as projections only:

- `helper_translate_status`
- `helper_translate_output_state`
- `helper_translate_provider_health`
- `helper_translate_error_reason`
- `helper_translate_retryable`
- `helper_translate_terminal`
- `subtitle_translation_waiting_retryable`
- `subtitle_ready_reason`
- `target_subtitle_current_reason`

They are not alternate semantic owners.
