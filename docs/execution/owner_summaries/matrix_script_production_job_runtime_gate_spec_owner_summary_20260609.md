# Owner Summary — Matrix Script Production Job Runtime Gate Spec

Date: 2026-06-09
Type: **Docs-only gate spec authoring (Harness X S5).** No code / template / router / schema / contract / test / runtime change. No implementation opened.
Gate Spec: `docs/design/MATRIX_SCRIPT_PRODUCTION_JOB_RUNTIME_GATE_SPEC_20260609.md`
Authority: Owner decision 2026-06-09 — "Start redesign for a production-capable Matrix Script generation runtime … Required first deliverable: author a docs-only Gate Spec, not runtime code."
Status update (2026-06-09): §16 **SIGNED** (Architect + Reviewer + Owner APPROVED); §11 DP-2 **RESOLVED** (Render Background Worker + Render Postgres; R2 artifact-only; Cloud Run deferred; no Pro-upgrade-as-fix). This Gate Spec is merged docs-only per Owner instruction; the Gate Spec merge report follows. On merge, the implementation gate **OPENS for PR-1 only**.

---

## What was authored
A binding-pending-signoff gate spec that freezes the redesign of Matrix Script generation from a **web-dyno in-process background task** (the proven 502 / no-`final.mp4` / no-durable-trace failure) into a **production-capable off-dyno job runtime**: web handles operator workflow only; generation runs on a worker; every phase writes a **durable trace before heavy work**; results are recoverable; the operator sees progress + the exact failure reason; `official_publish_ready` stays `false`. It is **Matrix-Script-line-scoped** — explicitly **not** the platform-wide Platform Runtime Assembly Wave (still BLOCKED), not a second production line, not a broad platform abstraction.

## Coverage of the 9 required content points
1. **Current failure diagnosis** — §3 (1-shot deployed still 502; no final.mp4; no AI 生成请求过程; no durable trace; root cause = generation tied to the web-dyno lifecycle via `BackgroundTasks` at `tasks.py:733`; classification `WEB_DYNO_UNSUITABLE` / `TRACE_GAP`).
2. **Target architecture** — §4 (7 components with single owners + hard boundaries: Web service / Job state store / Worker runtime / Artifact storage R2 / Provider adapter layer / Durable trace projection / Operator workbench projection; web and worker share state **only** via the durable store + R2, never in-process — so a worker crash cannot take down the web).
3. **State model** — §5 (closed set: `queued · planning · provider_generating · provider_polling · provider_clip_ready · composing · uploading · result_ready · failed_retryable · failed_terminal · cancelled`, with an explicit transition table, terminal classification, per-shot loop, honest fallback ≠ terminal, crash-recovery via lease, and projection into the existing operator-facing async vocabulary).
4. **Durable trace contract** — §6 (per-phase row: task_id / job_id / shot_id / phase / started_at / ended_at / status / elapsed_ms / provider_status_class / fallback_reason_code / artifact_refs; **written at phase START before heavy work** then updated at end — the `TRACE_GAP` closure; **no secrets / no raw signed URLs / opaque handles only**; panel is a pure projection reusing `assert_no_provider_trace_leak`).
5. **Worker boundary** — §7 (no operator HTML; no auth/session; no delivery-truth change; no `official_publish_ready=true`; no vendor selector UI; no schema/contract change except the §6 trace contract; thin enqueue seam in `tasks.py`, no orchestration).
6. **Implementation slicing** — §10 (PR-1 Durable Job State + Trace Writer → PR-2 Worker Runtime Skeleton + local CLI → PR-3 1-shot through worker → PR-4 multi-shot through worker → PR-5 deployed acceptance + closeout). Recommendation: keep five slices; PR-3 is the first real off-dyno provider spend, isolated.
7. **Deployment options** — §11 (compared: **A. Render Background Worker = RECOMMENDED v1** true off-dyno on current infra; B. Render one-off/cron = viable fallback, weaker latency; **C. Cloud Run Job = DEFERRED** — a GCP migration, needs separate gate approval; **D. keep on web dyno = REJECTED** except emergency).
8. **Acceptance** — §12 (A-PJ-1..A-PJ-12: 1-shot deployed completes with final.mp4 + AI 生成请求过程; 2-shot completes or fails with **durable** trace; no web 502 during generation; workbench responsive; `official_publish_ready=false`; operator sees exact failure reason; no secrets leaked; trace-before-heavy-work proven by a forced-kill test; crash recovery; clean worker boundary; no second source of truth; inherited behavior preserved).
9. **What not to do** — §13 + forbidden paths §14 (no more web-dyno generation patches; no PR-5 before worker acceptance; **no Render Pro upgrade as the architecture fix**; **no GCP migration before gate approval**; no provider selector UI; no `official_publish_ready=true`; no delivery-truth/second-truth; no Hot Follow / Digital Anchor / Asset Supply touch; no `schemas/`·`docs/contracts/` change except the §6 trace contract).

## Key engineering decisions made in the spec
- **Off-dyno via durable store, never in-process.** Web↔worker share state only through the Job State Store (§5) + R2 (§4). This is the structural fix for both the 502 (worker crash can't reach the web) and the `TRACE_GAP`.
- **Trace-before-heavy-work (SM-5 / TR-1).** A phase cannot advance without its `running` trace row persisted first → a crash always leaves the failing phase identifiable **without** Render logs.
- **Reuse, don't re-implement, the provider stack.** `provider_orchestrator` + `gemini_prompt_refiner` + `akool_image_to_video_capability` (proven 3/3 locally in PR #254) are relocated onto the worker behind an internal adapter; the deployed gap was execution **location**, not provider capability.
- **One authorized new contract only.** The §6 durable job/trace contract is the single contract-first addition this wave authorizes (line-scoped, additive); all other `schemas/**` / `docs/contracts/**` stay frozen.
- **Five slices, not one.** PR-1/PR-2 are durable-state + stubbed worker (zero provider cost, hermetic); PR-3 isolates the first real off-dyno provider spend.

## Open decisions for the Owner (L3 — resolve at/before signoff, §11 DP-2)
- **(i) Deployment target:** Option A (Render Background Worker, recommended) vs B (one-off/cron); C (Cloud Run / GCP) deferred behind a separate gate.
- **(ii) Durable store technology** for the Job State Store + trace: e.g. Render Redis vs Render Postgres vs R2-backed state + queue. PR-1 puts the store behind a swappable interface so this choice is isolated; the spec recommends but does not unilaterally pick it.

## Validation
- Change set: **docs-only** — 2 new files (`docs/design/…GATE_SPEC_20260609.md`, this owner summary) + the renamed failure report; no `gateway/`, `schemas/`, `docs/contracts/`, `.py`, tests, routes touched.
- Gate spec: **0** conflict markers, **0** trailing-whitespace lines.
- No-secret scan: **PASS** (only env-var **names**, public host, and endpoint **paths** as identifiers; no key / token / signed-URL values).
- Note: the prior 1-shot failure report was **renamed** to the Owner-referenced canonical name `docs/execution/MATRIX_SCRIPT_DEPLOYED_1SHOT_VALIDATION_FAILURE_REPORT_20260609.md` so the gate spec's required-reading list resolves.

## Owner decision (RESOLVED 2026-06-09)
The Owner reviewed the gate spec, resolved §11 DP-2 (Render Background Worker + Render Postgres; R2 artifact-only; Cloud Run deferred; no Pro-upgrade-as-fix), and signed §16 (Architect + Reviewer + Owner APPROVED). The Gate Spec is merged docs-only per Owner instruction (see the Gate Spec merge report). The implementation gate is now **OPEN for PR-1 only**; PR-2..PR-5 remain CLOSED until each separate Owner approval.

Stop point honored: Gate Spec + Owner Summary + docs-only merge + merge report only. No runtime implemented. No web-dyno patch. No infra change. No PR-5.
