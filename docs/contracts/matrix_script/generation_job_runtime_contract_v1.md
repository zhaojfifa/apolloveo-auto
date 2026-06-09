# Matrix Script — Generation Job Runtime Contract v1 (2026-06-09)

Status: **NORMATIVE (additive, line-scoped).** The single new contract authorized by the signed
Production Job Runtime Gate Spec (`docs/design/MATRIX_SCRIPT_PRODUCTION_JOB_RUNTIME_GATE_SPEC_20260609.md`
§6 TR-1). It defines the durable job-state + per-phase trace truth source for moving Matrix Script
generation **off the web dyno**. It does **not** change the `matrix_script` packet schema, the factory
generic contracts, `artifact_storage.py`, or any other `docs/contracts/**` / `schemas/**` object.

Authority order: when this conflicts with the Gate Spec or root governance, the underlying authority
wins. Execution logs are evidence, not authority.

---

## 1. Scope
- Persistence of **generation jobs** + **per-phase trace rows** in the existing app SQLAlchemy DB
  (Owner 2026-06-09: reuse the app DB; one Render Postgres for tasks + jobs + trace), behind the
  swappable `IJobStateStore` interface.
- Truth source for: job lifecycle state, durable phase trace (the operator AI 生成请求过程 panel
  projects from this), and crash-recovery via lease.
- **Out of scope (this contract):** worker execution, provider calls, ffmpeg, operator HTML, auth,
  delivery truth, `official_publish_ready` (stays `false`).

## 2. Closed job-state model (Gate Spec §5)
States (closed set): `queued`, `planning`, `provider_generating`, `provider_polling`,
`provider_clip_ready`, `composing`, `uploading`, `result_ready`, `failed_retryable`,
`failed_terminal`, `cancelled`.

Terminal (no outgoing transitions): `result_ready`, `failed_terminal`, `cancelled`.

Allowed transitions (closed graph; any other transition is rejected by `assert_transition`):

| From | Allowed → |
|---|---|
| `queued` | `planning`, `cancelled` |
| `planning` | `provider_generating`, `failed_retryable`, `failed_terminal`, `cancelled` |
| `provider_generating` | `provider_polling`, `provider_clip_ready`, `failed_retryable`, `cancelled` |
| `provider_polling` | `provider_clip_ready`, `provider_generating`, `failed_retryable`, `cancelled` |
| `provider_clip_ready` | `provider_generating`, `composing`, `failed_retryable`, `cancelled` |
| `composing` | `uploading`, `failed_retryable`, `failed_terminal`, `cancelled` |
| `uploading` | `result_ready`, `failed_retryable`, `cancelled` |
| `result_ready` | — (terminal) |
| `failed_retryable` | `queued`, `failed_terminal`, `cancelled` |
| `failed_terminal` | — (terminal) |
| `cancelled` | — (terminal) |

Per-shot loop: `provider_generating → provider_polling → provider_clip_ready` cycles per target shot,
then `composing`. Honest fallback for a shot is recorded in trace (`fallback_reason_code`) and still
progresses — it is **not** `failed_terminal`.

## 3. Job record (`generation_jobs` table)
| Field | Type | Notes |
|---|---|---|
| `job_id` | TEXT PK | `job-<uuid4hex>` |
| `task_id` | TEXT (indexed) | the Matrix Script task |
| `state` | TEXT | closed state (§2) |
| `target_shots` | INTEGER | from the `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` knob; `0` = uncapped (worker resolves from the storyboard plan) |
| `knobs_summary` | TEXT (JSON) | operator-safe ints/bools only, **vendor-neutral keys** (`target_shots`/`attempt_cap`/`refine_retry`/`real_provider`) — **no secret, no vendor/model name** |
| `retry_count` | INTEGER | job-level retry budget counter |
| `failure_reason_code` | TEXT | set on failed states |
| `claimed_by` | TEXT | worker id (PR-2 consumes) |
| `lease_expires_at` | TEXT (ISO-8601 UTC) | crash-recovery lease (SM-3) |
| `created_at` / `updated_at` | TEXT (ISO-8601 UTC) | |

## 4. Trace row (`generation_job_trace` table — Gate Spec §6)
**Written at phase START (`status=running`, `started_at`) BEFORE heavy work; updated at phase END.**
A worker kill leaves the last `running` row → the failing phase is identifiable without Render logs.

| Field | Type | Notes |
|---|---|---|
| `trace_id` | TEXT PK | `trc-<uuid4hex>` |
| `job_id` | TEXT (indexed) | |
| `task_id` | TEXT (indexed) | |
| `shot_id` | TEXT \| null | set for per-shot provider phases |
| `phase` | TEXT (closed) | a trace **event**: a generation ms_phase — `generation_start`, `provider_knobs`, `provider_batch_start`, `prompt_build`, `provider_submit`, `provider_poll`, `provider_download`, `provider_normalize`, `shot_done`, `provider_trace_presummary`, `compose_start`, `compose_done`, `upload_start`, `upload_done` — **or** (PR-2) a worker-lifecycle event (see §8) |
| `status` | TEXT (closed) | `running` / `succeeded` / `fallback` / `failed` / `skipped` / `cancelled` |
| `started_at` | TEXT (ISO-8601 UTC) | before heavy work |
| `ended_at` | TEXT \| null | null while running |
| `elapsed_ms` | INTEGER \| null | computed at end (monotonic) |
| `provider_status_class` | TEXT (closed) \| null | `ok`/`quota`/`rate_limited`/`timeout`/`auth`/`invalid_input`/`server_error`/`unknown` |
| `fallback_reason_code` | TEXT (closed) \| null | `provider_quota`/`provider_rate_limited`/`provider_timeout`/`provider_auth`/`provider_invalid_input`/`refiner_unavailable`/`none` (vendor-neutral) |
| `artifact_refs` | TEXT (JSON list) | **opaque handles only** (R2 object key / `msmaterial://`) |
| `seq` | INTEGER | monotonic per job (ordering) |

## 5. No-secret rule (binding, test-guarded)
A trace row (and any operator projection of it) MUST NOT contain: API key / token / op key /
`Authorization` / bearer; raw provider task id / credit; raw signed / presigned / `temporary_url` /
`download_url`; local filesystem path; raw provider/model/vendor/engine name in operator-projected
fields; raw prompt / negative_prompt payload. `artifact_refs` are rejected if they look like raw URLs
or carry signing parameters (`http(s)://`, `X-Amz`, `Signature=`). Guarded by
`assert_no_job_trace_leak` (writer) + an opacity check in the store.

## 6. Interface (swappable; Owner binding condition)
`IJobStateStore`: `create_job`, `get_job`, `get_jobs_for_task`, `transition_state`, `append_trace`,
`update_trace`, `get_traces`, `claim_next_queued_job`. Two impls: `InMemoryJobStateStore` (tests +
local harness) and `SqlAlchemyJobStateStore` (durable; Render Postgres in prod, SQLite locally). The
technology stays isolated behind this interface so the future Service Topology Split can re-decide.

## 7. Boundary
- Additive: two new tables; no change to `tasks` or any existing model/contract/schema.
- PR-1 delivers state + trace + a thin enqueue seam only — **no worker execution, no provider call,
  no ffmpeg, no UI, no auth change**. `official_publish_ready` remains `false`.
- The operator AI 生成请求过程 panel projects from these durable rows (no second source of truth).

## 8. Worker runtime + worker-lifecycle events (PR-2; additive)
PR-2 adds an off-dyno worker (`worker.py` + `cli.py`) that consumes the store via `IJobStateStore`
and is **dry-run only** (no provider/ffmpeg/upload). It extends the durable trace vocabulary with a
closed **worker-lifecycle event** set, carried in the trace `phase` column (§4):

```
worker_started · job_claimed · heartbeat · dry_run_started · dry_run_completed
· job_completed · job_failed_retryable · job_failed_terminal
```

- **Lease / heartbeat:** `claim_next_queued_job` sets `lease_expires_at = now + lease_seconds`
  (queued → planning). `heartbeat(job_id, worker_id, lease_seconds)` extends the lease (only the
  current claimant). `reclaim_expired_leases(max_retries)` resets non-terminal jobs whose lease
  expired back to `queued` (graph-legal via `failed_retryable`), incrementing `retry_count` and
  setting `failure_reason_code="lease_expired"`; once `retry_count >= max_retries` the job goes
  `failed_terminal` instead. **Terminal jobs are never reclaimed.**
- **Crash-safety:** the dry-run opens a `dry_run_started` (`running`) row BEFORE the stubbed work;
  a crash/exception leaves that open row + a durable `failed_retryable`/`failed_terminal` state.
- **Boundary:** worker is independent of the FastAPI request lifecycle; no operator HTML, no auth, no
  delivery-truth change, `official_publish_ready` stays `false`.

## 9. Worker 1-shot generation (PR-3; additive)
PR-3 makes the worker execute EXACTLY ONE real provider shot by REUSING the existing tomato stack
(`run_tomato_real_result`) off the FastAPI request lifecycle — no rewrite of Akool/Gemini/Azure/ffmpeg.

- **Trace = state walk.** A trace row's `phase` may also be a closed JOB STATE name: the worker writes
  a per-state OPEN `running` row BEFORE each phase's heavy work and closes it on advance. Driven by an
  additive `on_phase(name)` hook on `run_tomato_real_result` (guarded; default `None` = no behavior
  change) firing at `generation_start` / `provider_batch_start` / `compose_start` / `upload_start`.
  A crash leaves the in-flight state's OPEN row as durable evidence.
- **Bounded load.** The worker forces `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS=1` +
  `MATRIX_SCRIPT_PROVIDER_ATTEMPT_CAP=1` (merged over the full env so the akool gate + creds + knobs
  resolve together). It uses `use_gemini=True` to match the web in-process path (equivalent operator
  deliverable — no silent quality drop; Gemini fail-closes to deterministic without creds). Outcomes:
  (1) `result_ready` + provider final.mp4; (2) `result_ready` + fallback final.mp4 (provider failed,
  ffmpeg fallback); (3) `failed_retryable` / `failed_terminal` + durable trace.
- **H1 — atomic claim.** `claim_next_queued_job` (SQLAlchemy) uses a conditional single-row UPDATE
  (`WHERE state='queued'`) — race-safe + portable (SQLite/Postgres); the interface stays swappable.
- **H2 — seq hardening.** `append_trace` (SQLAlchemy) locks the parent job row (FOR UPDATE on Postgres;
  no-op on SQLite, where writes serialize) then `MAX(seq)+1` — deterministic per-job seq, no
  `count()+1` race.
- **Web gate.** `MATRIX_SCRIPT_WORKER_OWNS_GENERATION` (default OFF): when ON, the web new-task handler
  skips the in-process heavy generation — the durable `queued` job is the worker's hand-off; OFF
  preserves current behavior. Scope: the **initial-preview** path only. Regenerate-preview (V2) stays
  in-process and is intentionally deferred (the worker does not yet produce V2) — a later PR.
- **Boundary.** No multi-shot; no UI; no route business logic (thin gate only); no delivery-truth
  change; `official_publish_ready` stays `false`; no new table/column (state names reuse the trace
  `phase` column).
