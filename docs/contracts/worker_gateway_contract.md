# Worker Gateway Contract

## 1. Purpose

This document freezes the boundary between line-aware orchestration and worker execution.

It exists to prevent `tasks.py`, router wrappers, Skills logic, or future control meshes from treating workers as direct business-truth writers.

## 2. Role In The Factory

Worker Gateway is the execution boundary that accepts a normalized line-aware request and returns execution facts plus artifact candidates.

It is not:

- the line contract
- the source of repo truth
- the source of deliverable truth
- the source of asset sink truth
- the final status policy owner

OpenClaw or any future control mesh belongs on the execution/control side of this boundary, not on the business-truth side.

## 3. Request Shape

Minimal normalized request shape:

```json
{
  "request_id": "uuid-or-stable-run-id",
  "line_id": "hot_follow_line",
  "task_id": "task-id",
  "step_id": "parse|subtitles|dub|compose|pack|publish",
  "execution_mode": "internal|external|hybrid",
  "input_refs": {
    "task_ref": "repo task id",
    "artifact_refs": ["raw_path", "target_srt_key", "voiceover_key"]
  },
  "runtime_config": {
    "provider": "azure_speech",
    "timeout_seconds": 120,
    "retry_budget": 2
  },
  "operator_context": {
    "confirmed": false,
    "requested_by": "user-or-system"
  }
}
```

Required semantics:

- `line_id`, `task_id`, `step_id` are mandatory routing keys
- worker input references must be artifact or task references, not direct ownership grants
- line/service/controller is responsible for deciding whether a request should be issued

## 4. Response Shape

Minimal normalized response shape:

```json
{
  "request_id": "same-as-request",
  "task_id": "task-id",
  "step_id": "dub",
  "result": "success|failed|timeout|retryable",
  "attempt_facts": {
    "started_at": "2026-04-06T12:00:00Z",
    "finished_at": "2026-04-06T12:00:05Z",
    "provider": "azure_speech",
    "worker_mode": "hybrid"
  },
  "artifact_candidates": [
    {
      "kind": "audio",
      "path": "/tmp/voice.wav",
      "storage_key": "tasks/<id>/audio_mm.mp3",
      "sha256": "..."
    }
  ],
  "output_facts": {
    "media_duration_ms": 12345,
    "content_hash": "..."
  },
  "error": {
    "reason": "provider_timeout",
    "message": "provider timed out after 120s"
  },
  "retry_hint": {
    "retryable": true,
    "after_seconds": 30
  }
}
```

Allowed worker outputs:

- attempt facts
- artifact candidates
- checksums / media facts / telemetry
- retry hints
- machine-readable error surface

## 5. Execution Modes

### 5.1 Internal

Execution occurs fully inside ApolloVeo-controlled process/runtime.

Examples:

- local FFmpeg
- local file preparation
- local artifact normalization

### 5.2 External

Execution occurs fully via remote provider/service.

Examples:

- remote parsing
- remote ASR
- remote TTS

### 5.3 Hybrid

Execution spans both internal and external stages.

Examples:

- remote TTS + local audio normalization
- remote parsing + local artifact persistence
- local compose using externally generated dub/subtitle assets

## 6. Prohibited Direct Writes

Workers are not allowed to directly write:

- `task.status`
- `task.last_step`
- `error_reason` / `error_message`
- final `ready_gate.*`
- final derived currentness fields
- canonical deliverable keys on the repo task record
- final asset sink truth / publish truth

Workers may only return candidate outputs. Controllers/services remain responsible for:

- repo write decisions
- deliverable write-path decisions
- status-policy derivation
- ready-gate evaluation
- publish / sink confirmation

## 7. Retry / Timeout / Error Surface

Required policy:

- every worker request must declare an execution timeout
- timeout must surface as structured worker error, not swallowed text
- retryability must be explicit
- gateway callers may retry only when line/service policy allows it

Error surface classes:

- `validation_error`
- `provider_error`
- `timeout`
- `transport_error`
- `worker_internal_error`
- `artifact_write_error`

## 8. Relation To Status Policy And Deliverable Writes

Worker Gateway sits upstream of both:

- Status Policy
- Deliverable / Asset Sink write path

Required sequencing:

1. controller/service sends worker request
2. worker returns attempt facts + artifact candidates
3. controller/service validates outputs and persists allowed truth
4. status policy derives currentness / ready gate / projection state
5. deliverable and asset sink writes happen through approved write paths

This means:

- worker gateway may inform status policy
- worker gateway must not replace status policy
- worker gateway may supply artifact candidates
- worker gateway must not replace deliverable ownership

## 9. Why This Contract Exists

The current codebase already shows the failure mode this contract is meant to prevent:

- routers behaving like orchestration hubs
- helper layers writing both attempt truth and display truth
- execution details leaking into business status

This contract freezes the opposite direction:

- execution is composable
- truth ownership is explicit
- line contract and status policy remain the business authority
