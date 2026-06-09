# Matrix Script — Production Job Runtime Gate Spec (2026-06-09)

Status: **ACCEPTED — SIGNED GATE SPEC — docs-only.** §16 signoff filled 2026-06-09 (Architect +
Reviewer + Owner all APPROVED). Implementation gate for the **Matrix Script Production Job Runtime**
wave (move generation execution **off the web dyno** onto a durable job + worker runtime). This
document **implements nothing**. On merge to `main`, the implementation gate **OPENS for PR-1 only**
(Owner S5→S6 granted for PR-1 only); it stays CLOSED for PR-2..PR-5 until each separate Owner approval.

Working title: **Matrix Script Production Job Runtime.**
Harness X state: **S5 (Gate Spec Ready, pending signoff).** Authoring is L1/L2; opening any
runtime slice (S5→S6) is an **Owner-only L3** decision (this spec emits the Owner Decision
Request in §11 (DP-2) / §16 (signoff) and decides nothing).

Derivation: authored under Owner decision 2026-06-09 ("Start redesign for a production-capable
Matrix Script generation runtime … Required first deliverable: author a docs-only Gate Spec, not
runtime code"), immediately after the **1-shot deployed validation FAILED** at `5ecc6c8d` with PR
#256 knobs live (`docs/execution/MATRIX_SCRIPT_DEPLOYED_1SHOT_VALIDATION_FAILURE_REPORT_20260609.md`).

When this gate spec conflicts with Bucket A authority
(`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A), root governance
(`ENGINEERING_RULES.md`, `PROJECT_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`), or the unified
alignment map (`docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`), **the underlying
authority wins** and this spec is corrected in a docs-only follow-up.

---

## 1. Purpose

Freeze the rules that turn Matrix Script generation from a **web-dyno in-process background task**
(which crashes the web worker mid-generation → HTTP 502, no `final.mp4`, no durable trace) into a
**production-capable job runtime**:

- the **web service handles operator workflow only** (author / enqueue / observe);
- **generation runs off the web dyno** on a dedicated worker;
- **every phase writes a durable trace BEFORE heavy work**, so a crash always leaves the failing
  phase identifiable (closes the `TRACE_GAP`);
- **provider clips, compose, upload, and the final result are recoverable** from durable job state;
- the **operator can observe progress and the exact failure reason**;
- **`official_publish_ready` stays `false`** until an explicit, separately-gated delivery confirm.

This spec is **gate-spec-first**. No runtime PR may open until §16 signoff merges; each slice (§10)
is then its own Owner-gated S5→S6 (L3) decision. It is **Matrix-Script-line-scoped** — it is **not**
the platform-wide *Platform Runtime Assembly Wave* (which remains BLOCKED, alignment map §3), **not**
a second production line, and **not** a broad platform abstraction (`PROJECT_RULES.md`).

---

## 2. Source Authority

This gate spec **consumes** (does not supersede) the following, in priority order:

1. **Bucket A / Design Authority Index** — `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`
   (BINDING; A–J Workbench; Anti-Sprawl rules 1–6; execution logs are evidence, not authority).
2. **Root governance** — `ENGINEERING_RULES.md` (§1 file size, §2 function size, §3 router-thin,
   §4 service-owns-runtime, §5 import discipline, §6 contract-first, §8 truth-source, §9 factory
   alignment gate, §13 product-flow module presence), `PROJECT_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`.
3. **Factory alignment gate** — `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
   (binding for any PR touching four-layer state, worker/runtime binding, or new-line onboarding).
4. **Unified alignment map** — `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
   (current wave = OWC; Platform Runtime Assembly Wave is a later BLOCKED wave; this spec does not
   open it).
5. **Async state-machine baseline** — `docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md`
   (the existing operator-facing async lifecycle / polling / stale-guard the new job states must
   project into — not replace).
6. **Storyboard Control + Shot Workbench Gate Spec** —
   `docs/design/MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_20260608.md`
   (the script-directed generation surface this runtime executes; Prompt Builder, material role,
   Option-A route, V1/V2 preservation — all preserved; this wave changes **where/how** generation
   runs, not the operator surface contract).
7. **Provider orchestrator + multi-shot** —
   `docs/execution/MATRIX_SCRIPT_PROVIDER_ORCHESTRATOR_MULTISHOT_PR254_MERGE_REPORT_20260608.md`
   (the `provider_orchestrator.py` + `gemini_prompt_refiner.py` + `ShotTrace` + "AI 生成请求过程"
   panel + `assert_no_provider_trace_leak` the worker reuses as its provider adapter — proven 3/3
   on the LOCAL runtime; the deployed gap is execution location, not provider capability).
8. **Deploy polling auth fix** —
   `docs/execution/MATRIX_SCRIPT_DEPLOY_POLLING_AUTH_FIX_PR255_MERGE_REPORT_20260608.md`
   (the operator poller already sends `op_session` via `credentials: 'same-origin'`; the web→worker
   split must preserve this auth seam and not reintroduce 401).
9. **Provider load knobs + phase logs** —
   `docs/execution/MATRIX_SCRIPT_PROVIDER_LOAD_KNOBS_PR256_MERGE_REPORT_20260609.md`
   (`MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` / `_ATTEMPT_CAP` / `GEMINI_MODEL` knobs + the `ms_phase`
   log vocabulary the durable trace contract §6 persists).
10. **1-shot deployed failure report** —
    `docs/execution/MATRIX_SCRIPT_DEPLOYED_1SHOT_VALIDATION_FAILURE_REPORT_20260609.md`
    (the diagnosis this wave answers — §3).
11. **Product flow** — `docs/product/matrix_script_product_flow_v1.md` (normative spine:
    `final_video` primary; publish = `final_ready + required_deliverables`; no vendor/model in
    operator UI) + `docs/product/matrix_script_product_flow_v2_delta.md` (generation-plan first-class;
    A–J IA; VoiceTrans / Digital Anchor / Asset Supply as **future provider bridges**, consumer-only,
    never vendor-in-UI).

Execution logs are evidence only, not authority (Anti-Sprawl rule 1).

---

## 3. Current Failure Diagnosis (Owner §1)

Established by the 1-shot deployed failure report (read-only verification + code analysis at
`5ecc6c8d`, PR #256 knobs live):

- **1-shot deployed still fails with HTTP 502.** Task `f3fd2cb3380d` finalized
  **首版预览生成失败 / 生成超时**; `initial-preview-status` returned **repeated 502 (Render Bad
  Gateway HTML, not ApolloVeo JSON)**; a manual `POST …/tomato-real-result` **also 502** — the web
  worker itself is down/unresponsive during generation, not an app-level error and not the (fixed)
  PR-255 polling auth.
- **No `final.mp4`** (`preview_url=null`).
- **No AI 生成请求过程 panel** (no result staged → no `capability_status.ai_generation_request_process`).
- **No durable trace** — the provided Render log slice covered startup only; **no `ms_phase` for the
  task**. The phase-timing logs PR #256 added are `logger.info` lines (ephemeral Render logs), not
  durable state, so a worker kill leaves nothing recoverable. Strict root cause is `INCONCLUSIVE`
  precisely because the decisive evidence is non-durable.
- **Root architecture issue:** generation is **tied to the web dyno lifecycle**. It runs in-process
  via FastAPI `BackgroundTasks` (`gateway/app/routers/tasks.py:733` →
  `trigger_matrix_script_initial_preview_generation` → `tomato_real_result_orchestrator`). The heavy,
  long-blocking work (Akool host/create/poll/download/normalize → ffmpeg 1080×1920 compose → upload)
  executes inside the web worker; a worker timeout or OOM kills the in-process job and returns 502.
  Reducing to 1 shot did **not** remove the failure → the dominant cause is **web-dyno unsuitability**
  (long-blocking job on the request worker), with ffmpeg memory a latent secondary risk. Confirmed
  classification: **`WEB_DYNO_UNSUITABLE` / `TRACE_GAP`**.

**What this wave fixes:** (a) generation moves off the web dyno (kills the 502 root); (b) durable
per-phase trace written before heavy work (kills the `TRACE_GAP` and makes failures classifiable
without Render logs); (c) results become recoverable from durable job state.

---

## 4. Target Architecture (Owner §2)

Seven components, each with a single owner and a hard boundary. **The web service and the worker
share state ONLY through the durable Job State Store + Artifact Storage — never through process
memory, never through HTTP-into-the-web-dyno.**

```
        Operator (browser, op_session cookie)
                 │  author / enqueue / observe (poll)
                 ▼
   ┌───────────────────────────┐        enqueue job + read job state/trace
   │  (1) WEB SERVICE          │◄───────────────────────────────────────┐
   │  operator workflow only   │                                         │
   │  - A–J Workbench surface  │     ┌────────────────────────────────┐  │
   │  - auth / session         │     │  (2) JOB STATE STORE (durable) │  │
   │  - enqueue (thin seam)    │────►│  - job record + state (§5)     │◄─┘
   │  - read state + trace     │     │  - durable trace rows (§6)     │
   │  - operator projection(7) │◄────│  - claim/lease for worker      │
   └───────────────────────────┘     └────────────────────────────────┘
                                            ▲   claim job; write state+trace
                                            │
                                ┌───────────────────────────┐
                                │  (3) WORKER RUNTIME        │
                                │  generation execution only │
                                │  - plan → provider → compose → upload
                                │  - writes trace BEFORE heavy work
                                └───────────────────────────┘
                                   │                 │
                  ┌────────────────┘                 └─────────────────┐
                  ▼                                                     ▼
   ┌───────────────────────────┐                       ┌───────────────────────────┐
   │ (5) PROVIDER ADAPTER LAYER│                       │ (4) ARTIFACT STORAGE / R2 │
   │  provider_orchestrator +  │                       │  hosted input (presigned) │
   │  gemini_prompt_refiner +  │                       │  final.mp4 + sidecars     │
   │  akool image_to_video     │                       │  (opaque handles only)    │
   │  (no vendor in operator UI)│                      └───────────────────────────┘
   └───────────────────────────┘
                  │ ShotTrace events → (6) DURABLE TRACE PROJECTION → Job State Store
                  ▼
   (6) DURABLE TRACE PROJECTION: ms_phase rows persisted per §6
   (7) OPERATOR WORKBENCH PROJECTION: AI 生成请求过程 panel + state chips, read from (2), operator-language only
```

| # | Component | Owns | Must NOT own |
|---|---|---|---|
| 1 | **Web service** | operator A–J Workbench; auth/session; a **thin enqueue seam**; reading job state + trace for projection | generation execution; in-process heavy work; provider calls; ffmpeg; vendor UI |
| 2 | **Job state store (durable)** | the job record, its closed state (§5), durable trace rows (§6), worker claim/lease | business logic; rendering |
| 3 | **Worker runtime** | the full generation flow (plan → provider → compose → upload); writing state + trace before heavy work | operator HTML; auth/session; delivery-truth; `official_publish_ready` mutation; vendor selector; schema/contract change (§7) |
| 4 | **Artifact storage / R2** | hosted provider input (presigned, transient), `final.mp4` + sidecars, opaque artifact handles | being a delivery source for raw provider URLs; storing secrets |
| 5 | **Provider adapter layer** | reuse `provider_orchestrator.py` + `gemini_prompt_refiner.py` + `akool_image_to_video_capability.py` behind an internal adapter; emit `ShotTrace` events | exposing any provider/model/vendor/engine name to the operator surface |
| 6 | **Durable trace projection** | persist each `ms_phase` as a durable row (§6) at phase start, update at end | leaking secrets / raw signed URLs / keys / task tokens |
| 7 | **Operator workbench projection** | project job state + trace into operator-language chips + the AI 生成请求过程 panel (reusing `build_provider_request_panel` + `assert_no_provider_trace_leak`) | a second source of truth; raw enums/handles outside §J 技术诊断 |

Boundary rule (binding): components (1) and (3) **never call each other in-process**. The web
enqueues by writing to (2); the worker claims from (2); both observe through (2)+(4). This is what
makes a worker crash unable to take down the web service.

---

## 5. State Model (Owner §3)

A **closed** set of job states with explicit, enforced transitions. The set is exactly:

```
queued · planning · provider_generating · provider_polling · provider_clip_ready
· composing · uploading · result_ready · failed_retryable · failed_terminal · cancelled
```

| State | Kind | Entered when | Allowed next states |
|---|---|---|---|
| `queued` | non-terminal | web enqueues the job (thin seam) | `planning`, `cancelled` |
| `planning` | non-terminal | worker claims the job; builds/confirms the generation plan + reads knobs | `provider_generating`, `failed_retryable`, `failed_terminal`, `cancelled` |
| `provider_generating` | non-terminal (per-shot) | building script-derived prompt + submitting the provider request for the active target shot | `provider_polling`, `provider_clip_ready`, `failed_retryable`, `cancelled` |
| `provider_polling` | non-terminal (per-shot) | provider task created; awaiting async result | `provider_clip_ready`, `provider_generating` (retry/next attempt within cap), `failed_retryable`, `cancelled` |
| `provider_clip_ready` | non-terminal (per-shot) | this shot's clip downloaded + normalized (or honest fallback recorded) | `provider_generating` (next target shot), `composing` (all targets resolved), `failed_retryable`, `cancelled` |
| `composing` | non-terminal | all target shots resolved; ffmpeg compose (clips + Azure voiceover + burned/sidecar subtitles + QC) | `uploading`, `failed_retryable`, `failed_terminal`, `cancelled` |
| `uploading` | non-terminal | final.mp4 composed; upload to R2 + stage artifact | `result_ready`, `failed_retryable`, `cancelled` |
| `result_ready` | **terminal (success)** | artifact staged; `preview_url` set; `official_publish_ready=false` | — |
| `failed_retryable` | semi-terminal | transient/timeout/crash-detected within the retry budget | `queued` (re-enqueue), `failed_terminal` (budget exhausted), `cancelled` |
| `failed_terminal` | **terminal (failure)** | unrecoverable / retry budget exhausted; operator sees the exact reason | — |
| `cancelled` | **terminal** | operator/owner cancels a non-terminal job | — |

Binding state rules:

- **SM-1.** The per-shot loop is `provider_generating → provider_polling → provider_clip_ready`,
  cycling per target shot (bounded by `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` + the ≤5 attempt budget),
  then once all targets resolve → `composing`. An **honest fallback** for a shot (AK-3) is recorded
  in the trace (`fallback_reason_code`) and still allows progression — fallback is **not**
  `failed_terminal`.
- **SM-2.** Terminal states are exactly `result_ready`, `failed_terminal`, `cancelled`. No transition
  leaves a terminal state. `failed_retryable` is the only state that may re-enter `queued`, and only
  while the job-level retry budget remains.
- **SM-3.** **Crash recovery:** a job left in any non-terminal state past a lease/heartbeat deadline
  is reclaimable. The reclaim path projects to the operator exactly as today's stale guard does
  (`operator_workbench_view.RUNNING_STALE_SECONDS`) — but now backed by durable state, so the worker
  death is detected and re-enqueued, not silently lost.
- **SM-4.** These are **worker-internal job states**. The **operator never sees the raw enum** — they
  see the existing operator-language chips (`生成中` / `首版预览生成失败` / etc.) projected from job
  state (component 7). Raw state lives only in §J 技术诊断. The new model **projects into** the
  async-state-machine baseline (`…ASYNC_STATE_MACHINE_CLOSURE_20260604.md`); it does not replace the
  operator-facing vocabulary.
- **SM-5.** State transitions are written to the durable store **transactionally with** the trace row
  (§6) — a phase cannot advance without its trace being persisted first (this is the `TRACE_GAP`
  closure mechanism).

---

## 6. Durable Trace Contract (Owner §4)

Each phase persists a durable trace row to the Job State Store. **Written at phase START (status
`running`, `started_at` set) BEFORE the heavy work begins, then UPDATED at phase END.** A worker
kill therefore always leaves the last `running` row, naming the exact failing phase — without
depending on ephemeral Render logs.

Per-row fields (closed shape):

| Field | Type | Notes |
|---|---|---|
| `task_id` | string | the Matrix Script task |
| `job_id` | string | the generation job (a task may have multiple jobs across retries/regenerations) |
| `shot_id` | string \| null | set for per-shot provider phases; null for job-level phases (planning/compose/upload) |
| `phase` | closed enum | the `ms_phase` vocabulary, now persisted: `generation_start`, `provider_knobs`, `provider_batch_start`, `prompt_build`, `provider_submit`, `provider_poll`, `provider_download`, `provider_normalize`, `shot_done`, `provider_trace_presummary`, `compose_start`, `compose_done`, `upload_start`, `upload_done` |
| `started_at` | timestamp | written before heavy work |
| `ended_at` | timestamp \| null | null while `running` |
| `status` | closed enum | `running` / `succeeded` / `fallback` / `failed` / `skipped` / `cancelled` |
| `elapsed_ms` | int \| null | computed at end |
| `provider_status_class` | closed enum \| null | aligned to the existing taxonomy (`akool_image_to_video_capability` `_KIND_TO_STATUS`): `ok` / `quota` / `rate_limited` / `timeout` / `auth` / `invalid_input` / `server_error` / `unknown` |
| `fallback_reason_code` | closed enum \| null | `provider_quota` / `provider_rate_limited` / `provider_timeout` / `provider_auth` / `provider_invalid_input` / `gemini_unavailable` / `none` |
| `artifact_refs` | string[] | **opaque handles only** (R2 object key / `msmaterial://` handle) |

**Forbidden in any trace row (binding, test-guarded):**

```
API key / token / op key            raw provider task id / credit
raw signed / presigned / temporary_url / download_url      local filesystem path
raw provider/model/vendor/engine name in operator-projected fields      raw prompt / negative_prompt payload
```

- **TR-1.** The contract is **additive and Matrix-Script-line-scoped**. Because durable job/trace
  state is genuinely new, this gate spec is the **explicit, separately-approved contract-first
  authorization** for **this new job/trace contract only** (landed contract-doc + writer in the same
  PR, `ENGINEERING_RULES.md` §6). It does **not** authorize any change to the existing factory generic
  contracts, the `matrix_script` packet schema, or `docs/contracts/**` / `schemas/**` for other
  objects — those stay frozen unless separately approved (§15).
- **TR-2.** The operator AI 生成请求过程 panel is a **pure projection** over these durable rows,
  reusing `provider_orchestrator.build_provider_request_panel` + `assert_no_provider_trace_leak`. No
  new readiness producer; no second source of truth (`ENGINEERING_RULES.md` §8).
- **TR-3.** `artifact_refs` are resolved to operator-safe friendly labels / preview URLs **only** at
  projection time through the existing resolver — the raw handle never reaches operator copy (it lives
  in §J).
- **TR-4.** Trace writing is **fail-safe**: a trace-write failure must not crash the worker; it
  degrades to `status=unknown` for that row and the job continues (the trace is observability, not a
  generation dependency) — except SM-5's pre-phase row, whose write is required to advance.

---

## 7. Worker Boundary (Owner §5)

The worker runtime is a **service-layer** runtime (`ENGINEERING_RULES.md` §3/§4: service owns
business/runtime flow; router stays thin). The worker MUST NOT own:

```
operator HTML rendering              auth / session logic
delivery-truth change                official_publish_ready = true
vendor / model / provider selector UI    schema / contract change (beyond the §6 trace contract, unless separately approved)
new line-specific logic in tasks.py      a second source of truth / new readiness producer
```

- **WK-1.** No operator HTML: the worker emits durable state + trace; the **web** projects it.
- **WK-2.** No auth/session: the worker is not request-scoped; it claims jobs from the durable store.
  Operator auth (PR-255 `op_session` seam) stays entirely on the web side and is preserved.
- **WK-3.** No delivery-truth change and **`official_publish_ready` stays `false`** at every state,
  including `result_ready`. Promotion to delivery is a separate, later, explicitly-gated step.
- **WK-4.** No vendor selector / no provider name in any operator-projected field — the provider
  adapter (component 5) keeps vendor identity backend-only (R3 red line, proven in PR #254).
- **WK-5.** No schema/contract change except the §6 durable trace contract (TR-1). The existing
  generation spine (script → shot-plan → `final.mp4` → artifact_staged → preview_url → acceptance),
  the `matrix_script` packet, `artifact_storage.py`, and all `docs/contracts/**` / `schemas/**`
  stay frozen unless separately approved.
- **WK-6.** The web→worker enqueue is a **thin seam** — no business orchestration, no media flow, no
  state derivation in `tasks.py` (`ENGINEERING_RULES.md` §9; `tasks.py` must not receive new
  line-specific generation logic). Enqueue writes a `queued` job to the durable store and returns.

---

## 8. Provider Adapter Layer + Operator Observability

- **PA-1.** The worker reuses the **already-proven** provider stack as an internal adapter:
  `provider_orchestrator.py` (bounded multi-shot, Gemini-rewrite-then-retry, honest fallback,
  `ShotTrace`), `gemini_prompt_refiner.py` (runtime-transient prompt; fail-closed; key never
  returned/logged), `akool_image_to_video_capability.py` (host/create/poll/download/normalize via the
  additive `on_event` hook). PR #254 proved 3/3 shots on the LOCAL runtime — the deployed gap is the
  **execution location**, not provider capability. This wave does not re-implement the provider stack;
  it relocates it onto the worker and routes its `ShotTrace`/`on_event` stream into the durable trace
  (§6).
- **PA-2.** Provider knobs (`MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` / `_ATTEMPT_CAP` /
  `MATRIX_SCRIPT_PROVIDER_ENABLE_GEMINI_RETRY` / `GEMINI_MODEL` / `MATRIX_SCRIPT_AKOOL_REAL`) are read
  by the worker at `planning` and persisted as the `provider_knobs` trace row (so the active shot
  count is durably recorded — the cross-check the failed run could not produce).
- **OO-1.** The operator sees: a live state chip (operator-language, from §5 via component 7), the
  AI 生成请求过程 panel (per-shot prompt source / status / 进入成片 / 用时 / poll / fallback — from
  §6), and on failure the **exact failure reason** in operator language (mapped from
  `provider_status_class` + `fallback_reason_code`, never a raw vendor error, never a stack trace).
- **OO-2.** Workbench responsiveness: because generation is off-dyno, the web stays responsive during
  generation; the operator page polls `initial-preview-status` (200, never 502) and leaves `生成中`
  on a real terminal state, not a stale-guard-after-crash.

---

## 9. Wave-Gate Alignment & Scope Position (binding)

- **AL-1.** This is the **Matrix Script line's generation-execution runtime**, scoped to Matrix
  Script. It is **not** the platform-wide *Platform Runtime Assembly Wave* (alignment map §3 — a later
  wave gated on Plan A live-trial), **not** a second production line, and **not** a broad platform
  abstraction (`PROJECT_RULES.md`). It introduces no Hot Follow / Digital Anchor / Asset Supply
  coupling.
- **AL-2.** It does **not** itself advance any wave, trial, or closeout signoff. Per the storyboard
  spec's E8 precedent, the root governance files (`CURRENT_ENGINEERING_FOCUS.md`, the alignment map)
  are **stale vs the June Matrix Script work**; a **separate docs-only re-anchor PR** folds this wave
  into root governance — this spec does not edit those files.
- **AL-3.** Because it touches **worker / line-runtime binding + four-layer state**, every
  implementation slice MUST cite the factory alignment review
  (`docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`) and honor its red lines
  (`ENGINEERING_RULES.md` §9; `PROJECT_RULES.md` "Currently Forbidden").
- **AL-4.** **Product-flow module presence** (`ENGINEERING_RULES.md` §13): any slice claiming
  operator-ready scope must surface its module in the operator templates. This wave's operator-visible
  deltas (state chip + AI 生成请求过程 panel) re-home into the existing A–J Workbench (§A 主视频结果 /
  §J 技术诊断) — **no new IA, no parallel flow** (Anti-Sprawl rule 4).

---

## 10. Implementation Slicing (Owner §6)

Small PRs, gate-spec-first, structure-before-polish. Each ships dedicated tests, cites the factory
alignment review, opens **only** after its predecessor merges + reviews, and is its own Owner-gated
S5→S6 (L3) decision. No bundling.

| PR | Scope | Key boundary |
|----|-------|--------------|
| **PR-1** | **Durable Job State + Trace Writer.** Author the §5 state model + §6 trace contract (the one authorized new contract); implement the durable store interface + writer behind a clean seam; web enqueue writes `queued`; trace rows written at phase boundaries. No worker execution yet (writer is exercised by tests + a local harness). | new contract doc + store/writer service; thin enqueue seam in `tasks.py`; **no** provider call; no generation behavior change |
| **PR-2** | **Worker Runtime Skeleton + local CLI execution.** A standalone worker entrypoint that claims a `queued` job and walks the §5 states writing trace, with the generation steps **stubbed** (deterministic, no provider, no network). Runnable as a **local CLI** for hermetic acceptance. | worker process boundary (§7); no operator HTML; no auth; no real provider/ffmpeg yet |
| **PR-3** | **1-shot generation through the worker.** Wire the real provider adapter (§8) + ffmpeg compose + R2 upload into the worker for **`TARGET_SHOTS=1`**; full durable trace; `result_ready` with `final.mp4` + AI 生成请求过程; honest failure → `failed_terminal` with exact reason. | the first real provider spend; bounded to 1 shot; `official_publish_ready=false` |
| **PR-4** | **Multi-shot generation through the worker.** Generalize to `TARGET_SHOTS=N` (per-shot loop, ≤5 attempt budget, honest per-shot fallback); 2-shot then 3-shot; durable trace per shot. | bounded provider cost; no unbounded calls |
| **PR-5** | **Deployed acceptance + operator closeout.** Deploy the chosen worker target (§13); run the §14 deployed acceptance (1-shot → 2-shot); acceptance audit, no-leak audit, forbidden-path audit, signoff. | docs only |

> Reviewer-fail / new-defect corrections are separate narrow follow-up PRs, never folded back into a
> merged slice. **Recommendation: keep the five-slice plan** — PR-1/PR-2 are durable-state +
> stubbed-worker (zero provider cost, hermetic); PR-3 is the single slice that first spends a real
> provider call off-dyno; isolating it bounds the blast radius.

---

## 11. Deployment Options (Owner §7)

| Option | Off web-dyno? | Queue / trigger | Pros | Cons | Verdict |
|---|---|---|---|---|---|
| **A. Render Background Worker** (persistent worker service consuming a durable queue/store) | ✅ true isolation | durable store / Redis / Postgres queue | stays on current Render infra; worker crash cannot touch web; long-running OK; no per-job cold start | adds a worker service + a durable store dependency (new infra cost) | **RECOMMENDED v1 target** (pending Owner approval at signoff) |
| **B. Render one-off job / cron-like worker** | ✅ isolation | scheduled / triggered job per batch | cheap when idle; simple | not truly on-demand per task (latency / scheduling mismatch for interactive generation); harder to stream progress | viable fallback; weaker operator latency |
| **C. Cloud Run Job (GCP)** | ✅ isolation | Pub/Sub or HTTP trigger | strong scale-to-zero + per-job isolation; good ffmpeg headroom | **a GCP migration** — Owner said *no GCP migration before gate approval*; new platform surface | **DEFERRED** — documented future option; requires a **separate** gate approval |
| **D. Keep on web dyno** | ❌ | in-process `BackgroundTasks` (today) | none new | the proven 502 / `TRACE_GAP` root cause | **REJECTED** except as an explicit emergency fallback |

- **DP-1.** **CONFIRMED (Owner 2026-06-09): Option A — Render Background Worker.** It
  achieves true off-dyno isolation on the **current** infra without a GCP migration and without
  treating a **Render Pro upgrade as the architecture fix** (a bigger web dyno does not move
  generation off the request lifecycle). Cloud Run Job (C) is recorded as the future scale option
  behind a separate gate.
- **DP-2.** **RESOLVED (Owner 2026-06-09):** (i) deployment target = **Render Background Worker**
  (Option A); (ii) durable store technology = **Render Postgres**; (iii) **R2 remains artifact
  storage only**; (iv) **Cloud Run Job is deferred** behind a separate future gate; (v) **a Render
  Pro upgrade is NOT the architecture fix**. PR-1 MUST still put the Postgres-backed `job_state_store`
  behind a **swappable interface** so the technology choice stays isolated (binding Architect
  condition).

---

## 12. Acceptance (Owner §8)

The Closeout (PR-5) records PASS/FAIL against every row; each slice contributes the rows it can
satisfy. The interpreter / environment MUST be stated per slice.

| # | Acceptance criterion | Slice |
|---|---|---|
| A-PJ-1 | **1-shot deployed worker completes** with a playable **`final.mp4`** AND a populated **AI 生成请求过程** panel. | PR-3 / PR-5 |
| A-PJ-2 | **2-shot** either completes OR fails with a **complete durable trace** (last `ms_phase` identifiable from durable state, no Render-log dependency). | PR-4 / PR-5 |
| A-PJ-3 | **No web 502 during generation** — `initial-preview-status` returns 200 throughout; the web service stays responsive while the worker runs. | PR-3 / PR-5 |
| A-PJ-4 | **Workbench remains responsive** during generation (operator can navigate; page leaves `生成中` only on a real terminal state). | PR-3 / PR-5 |
| A-PJ-5 | **`official_publish_ready=false`** at every state including `result_ready`. | every PR |
| A-PJ-6 | **Operator sees the exact failure reason** (operator-language, mapped from `provider_status_class` + `fallback_reason_code`) on any failure — never a raw vendor error or stack trace. | PR-3 / PR-4 |
| A-PJ-7 | **No secrets leaked** — durable trace + operator projection carry no key / token / raw signed URL / raw provider task id / local path (test-guarded; `assert_no_provider_trace_leak` extended to the durable rows). | every PR |
| A-PJ-8 | **Durable trace is written BEFORE heavy work** — a forced mid-phase kill in a hermetic test leaves the correct last `running` row (the `TRACE_GAP` closure, A-PJ-2's mechanism). | PR-1 / PR-2 |
| A-PJ-9 | **Crash recovery** — a job left non-terminal past its lease is reclaimed/re-enqueued and projects to the operator as the existing stale state, not silently lost. | PR-2 / PR-4 |
| A-PJ-10 | **Worker boundary clean** (§7): no operator HTML, no auth/session, no delivery-truth change, no vendor in operator copy; web↔worker share state only via the durable store + R2. | every PR |
| A-PJ-11 | **No second source of truth / no new readiness producer**; only the §6 trace contract is new; existing `schemas/**` / `docs/contracts/**` (other than the trace contract) unchanged. | every PR |
| A-PJ-12 | Storyboard Control + Slot-v2 + async-state-machine inherited behavior preserved (state narration, delivery wording, diagnostics fold, honest slot classification, V1/V2 protection). | every PR |

Each slice keeps the Matrix Script suite green; pre-existing PEP-604 env-coupled skips are not
regressions (`ENGINEERING_RULES.md` §10).

---

## 13. Forbidden Scope / What Not To Do (Owner §9 + standard)

The implementation MUST NOT:

```
more web-dyno generation patches         PR-5 (deployed acceptance/closeout) before worker acceptance (PR-3/PR-4)
Render Pro upgrade as the architecture fix     GCP / Cloud Run migration before a separate gate approval
provider / model / vendor / engine selector in operator UI      official_publish_ready = true
delivery-truth change                    second source of truth / new readiness producer
schemas/** or docs/contracts/** change (except the §6 durable trace contract, TR-1)
new line-specific generation logic in tasks.py       Hot Follow / Digital Anchor / Asset Supply file touch
artifact_storage.py change (unless separately approved)    new production line / broad platform abstraction
Platform Runtime Assembly Wave opening   PR-slice bundling      React/Vite rebuild
raw Akool URL / API key / token / task-id leak in trace or operator copy
```

Specifically: a Render Pro upgrade and a GCP migration are **infra decisions, not this wave's fix**;
the fix is the **web/worker split + durable trace**. Any forced additional contract/schema need
(beyond §6) must be raised as a **separate, explicitly-approved, contract-first** scope expansion —
never bundled into a runtime slice.

---

## 14. Forbidden Paths + Allowed Paths

Any appearance in a slice's `git diff --name-only` of the following is an automatic fail:

```
gateway/app/services/hot_follow*         gateway/app/services/digital_anchor/
gateway/app/services/asset/              **/artifact_storage.py (unless separately approved)
schemas/ (except a new line-scoped job/trace schema explicitly approved per TR-1)
docs/contracts/ (except the new durable-trace contract doc, TR-1)
CURRENT_ENGINEERING_FOCUS.md             docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md
```

Allowed implementation paths (indicative; finalized per slice):
```
gateway/app/services/matrix_script/   (new: job_state_store / trace_writer / worker_runtime / provider adapter wiring)
gateway/app/worker/  or  a new worker entrypoint module    (PR-2; off-dyno worker, NOT a router)
gateway/app/routers/tasks.py   (thin enqueue seam ONLY — no orchestration; §7 WK-6)
gateway/app/templates/task_workbench.html   (matrix_script §A/§J projection only)
gateway/app/services/tests/   (Matrix Script tests + a hermetic worker/CLI harness)
docs/contracts/matrix_script/…   (the new durable job/trace contract, TR-1, PR-1 only)
```

---

## 15. Preserved Freezes

Byte-/behavior-stable across every slice, re-audited at Closeout:

- The generation **spine** (script → shot-plan → `final.mp4` → artifact_staged → preview_url →
  acceptance) — this wave changes **where/how** it runs, not the spine.
- The **provider stack** behavior (`provider_orchestrator.py`, `gemini_prompt_refiner.py`,
  `akool_image_to_video_capability.py`) — reused, not re-implemented; bounded ≤5 attempts; honest
  fallback; key never returned/logged.
- The **operator surface contract** (Storyboard Control + Shot Workbench gate spec; Slot-v2 honest
  slot classification; A–J IA; no vendor in operator UI; raw fields only in §J).
- The **PR-255 polling auth seam** (`credentials: 'same-origin'`; backend auth unchanged).
- `artifact_storage.py`, the `matrix_script` packet schema, all other `schemas/**` /
  `docs/contracts/**`, Hot Follow, Digital Anchor, Asset Supply — untouched.
- Azure voiceover + burned/sidecar subtitles + ffmpeg compose/QC/fallback.
- V1-protection + the #212 byte-consumption honesty contract.
- **`official_publish_ready=false`** invariant.
- No second source of truth; the only new state is the §6 durable job/trace contract.

---

## 16. Signoff (gate opens on merge)

This is the gate-opening signoff block. Architect + Reviewer + **Owner** signoff merged to `main`
**opens the implementation gate for PR-1 only** and constitutes the Owner's S5→S6 grant. Opening each
subsequent slice (PR-2..PR-5) is its own Owner-gated S5→S6 (L3) decision — listing it in §10 does not
pre-open it. Coordinator + PM bind the Closeout acceptance audit (§12, PR-5), not gate opening.

| Role | Name | Date | Verdict |
|------|------|------|---------|
| Architect | APPROVED — deployment target = Render Background Worker; durable store = Render Postgres; PR-1 interface must remain swappable | 2026-06-09 | opens S5→S6 for PR-1 only |
| Reviewer | APPROVED — docs-only validation passed; scope/boundary/forbidden paths/acceptance rows are sufficient | 2026-06-09 | READY TO MERGE (gate spec) |
| Owner | APPROVED — Gate Spec approved; S5→S6 granted for PR-1 only | 2026-06-09 | grants S5→S6 for PR-1 only after this Gate Spec merges |
| Operations Coordinator | `<fill at PR-5 closeout>` | `<fill>` | binds Closeout (PR-5) |
| Product Manager | `<fill at PR-5 closeout>` | `<fill>` | binds Closeout (PR-5) |

> **Runtime implementation remains CLOSED** until this gate spec merges and the Owner explicitly
> grants S5→S6 after gate-spec review. This spec authorizes no code; the first allowed action after
> signoff is PR-1 per §10.

---

## 17. Authority Pointers

- Bucket A: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A.
- Root governance: `ENGINEERING_RULES.md`, `PROJECT_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`.
- Factory alignment gate: `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`.
- Unified alignment map: `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`.
- Async state-machine baseline: `docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md`.
- Storyboard Control gate spec: `docs/design/MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_20260608.md`.
- Provider/multishot: `docs/execution/MATRIX_SCRIPT_PROVIDER_ORCHESTRATOR_MULTISHOT_PR254_MERGE_REPORT_20260608.md`.
- Polling auth: `docs/execution/MATRIX_SCRIPT_DEPLOY_POLLING_AUTH_FIX_PR255_MERGE_REPORT_20260608.md`.
- Load knobs + phase logs: `docs/execution/MATRIX_SCRIPT_PROVIDER_LOAD_KNOBS_PR256_MERGE_REPORT_20260609.md`.
- Failure diagnosis: `docs/execution/MATRIX_SCRIPT_DEPLOYED_1SHOT_VALIDATION_FAILURE_REPORT_20260609.md`.
- Product flow: `docs/product/matrix_script_product_flow_v1.md` + `docs/product/matrix_script_product_flow_v2_delta.md`.
- Owner summary: `docs/execution/owner_summaries/matrix_script_production_job_runtime_gate_spec_owner_summary_20260609.md`.

*This is an accepted-pending-signoff gate spec for future runtime implementation. It implements
nothing, opens no wave, and supersedes no authority. Code begins only after §16 signoff merges and
the Owner grants S5→S6, one slice at a time, under the standard discipline.*
