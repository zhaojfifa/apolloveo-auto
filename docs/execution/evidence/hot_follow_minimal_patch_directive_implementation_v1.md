# Hot Follow Minimal Patch Directive Implementation v1

Date: 2026-04-30
Branch: `VeoBase02`
Directive: `docs/execution/VEOBASE02_HOT_FOLLOW_MINIMAL_PATCH_DIRECTIVE.md`

## Implemented Actions

### Phase A: target subtitle materialization

Implemented formal action:

```text
materialize_target_subtitle_from_origin
```

The action consumes source subtitle text, translates it to the target language, and delegates the authoritative `vi.srt` write to the existing Subtitle Stage owner path. It records typed materialization status and errors without using helper telemetry as subtitle truth.

Typed failures:

- `no_translated_target_produced`
- `invalid_target`
- `provider_error`
- `stale_source`

### Phase B: stale-pending detector

Implemented read-only diagnostic:

```text
translation_waiting_diagnostic
```

It distinguishes:

- `active_translation_running`
- `stale_pending_without_progress`
- `not_waiting_for_translation`

This diagnostic does not write subtitle truth, dub truth, compose truth, or route truth.

### Phase C: local preserve to subtitle/dub flow

Implemented formal operator action:

```text
local_preserve_to_subtitle_dub_flow
```

The action records operator intent to leave local preserve-source testing and queues `materialize_target_subtitle_from_origin`. It does not materialize subtitle truth.

### Phase D: helper remains auxiliary

Helper output can feed the materialization action as input. Helper telemetry remains telemetry and does not own route switching, subtitle closure, dub readiness, compose readiness, or subtitle truth writes.

## Validation

- `gateway/app/services/tests/test_hot_follow_minimal_patch_directive.py`
- Existing subtitle ownership and binding regressions

No broad state-policy rewrite, provider strategy change, compose optimization, or route-system rewrite was introduced.
