# Worker Gateway Runtime Contract

## 1. Purpose

This document freezes the Phase-2 runtime-facing contract for Worker Gateway.

It complements, but does not replace, the broader ownership baseline in:

- `docs/contracts/worker_gateway_contract.md`

This file focuses on runtime slots, request/response shape, and execution boundary used by PR-7.

## 2. Runtime Role

Worker Gateway is the execution adapter between line-aware orchestration and concrete internal/external/hybrid workers.

Its runtime responsibility is to:

- accept normalized worker requests
- invoke a registered worker route
- surface structured execution results
- return artifact candidates and attempt facts

It is not allowed to:

- write repo truth directly
- finalize deliverable truth directly
- finalize status or ready-gate truth directly
- publish or sink accepted artifacts directly

## 3. Execution Modes

Supported execution modes:

- `internal`
- `external`
- `hybrid`

Meaning:

- `internal`: local service / local binary / local subprocess execution
- `external`: remote provider / remote API / remote control surface
- `hybrid`: external work combined with local validation, normalization, or media assembly

## 4. Runtime Registration Model

Runtime registration is keyed by:

- `line_id`
- `step_id`
- optional `worker_capability`
- optional `execution_mode`

Minimal registry intent:

```json
{
  "line_id": "hot_follow_line",
  "step_id": "dub",
  "worker_capability": "tts",
  "execution_mode": "external"
}
```

This is a registration boundary, not a direct truth grant.

## 5. Request Shape

Minimal normalized worker request:

```json
{
  "request_id": "uuid-or-stable-run-id",
  "line_id": "hot_follow_line",
  "task_id": "task-id",
  "step_id": "parse|subtitles|dub|compose|pack|publish",
  "worker_capability": "parse|asr|translation|tts|compose|pack|publish_sink",
  "execution_mode": "internal|external|hybrid",
  "worker_profile_ref": "docs/contracts/worker_gateway_runtime_contract.md",
  "input_refs": {
    "task_ref": "task-id",
    "artifact_refs": ["raw_path", "target_srt_key", "voiceover_key"]
  },
  "strategy_hints": {
    "provider_hint": "azure_speech",
    "quality_mode": "default"
  },
  "runtime_config": {
    "timeout_seconds": 120,
    "retry_budget": 2
  }
}
```

Required semantics:

- request must be line-aware
- request must be step-aware
- request must declare timeout
- request must use refs or staged inputs, not direct truth ownership

## 6. Response Shape

Minimal normalized worker response:

```json
{
  "request_id": "same-as-request",
  "task_id": "task-id",
  "step_id": "dub",
  "result": "success|failed|timeout|retryable",
  "attempt_facts": {
    "started_at": "2026-04-07T12:00:00Z",
    "finished_at": "2026-04-07T12:00:05Z",
    "worker_mode": "external",
    "provider": "azure_speech"
  },
  "artifact_candidates": [
    {
      "kind": "audio",
      "storage_key": "tasks/<id>/audio_mm.mp3",
      "sha256": "..."
    }
  ],
  "output_facts": {
    "duration_ms": 12345,
    "content_hash": "..."
  },
  "error": {
    "reason": "timeout",
    "message": "provider timed out after 120 seconds"
  },
  "retry_hint": {
    "retryable": true,
    "after_seconds": 30
  }
}
```

Allowed outputs:

- attempt facts
- artifact candidates
- output facts
- structured error surface
- retry hint

Disallowed outputs:

- direct repo mutation
- accepted deliverable promotion
- final publish reference write
- final ready-gate write

## 7. Runtime Boundary With Skills

Skills Runtime may influence:

- `worker_capability`
- `provider_hint`
- `quality_mode`
- retry recommendation

Worker Gateway must remain deterministic once a request is issued.

It must not:

- call back into skills to rewrite truth
- collapse strategy and execution into one opaque side effect

## 8. Runtime Boundary With Status Policy

Worker Gateway is upstream of Status Policy.

Required sequence:

1. orchestration prepares worker request
2. worker gateway executes
3. worker gateway returns structured output
4. orchestration validates and accepts allowed truth writes
5. status policy derives ready/current state from accepted truth

This prevents worker execution from becoming the status owner.

## 9. Timeout / Retry / Error Surface

Every execution path must support:

- declared timeout
- structured timeout result
- explicit retryability
- explicit error reason

Minimum error classes:

- `validation_error`
- `timeout`
- `provider_error`
- `transport_error`
- `worker_internal_error`
- `artifact_write_error`

## 10. Hot Follow MVP Scope

The Phase-2 Worker Gateway MVP is intentionally narrow.

It should first absorb execution boundaries already present in Hot Follow:

- provider-backed parsing / ASR / TTS calls
- compose subprocess execution boundary
- hybrid local + remote steps

Current live MVP path:

- Hot Follow compose FFmpeg execution now goes through the Worker Gateway `internal` adapter path

It should not, in PR-7:

- implement every provider
- redesign business truth ownership
- broaden into OpenClaw platform work
- invent a second line product scope
