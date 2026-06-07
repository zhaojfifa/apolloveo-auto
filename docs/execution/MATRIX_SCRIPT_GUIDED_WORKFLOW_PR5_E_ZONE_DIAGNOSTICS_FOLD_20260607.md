# Matrix Script Guided Operator Workflow — PR-5: E区 进阶/诊断折叠与动作记录 (2026-06-07)

Engineering execution note. Evidence only — not implementation authority.
Gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` §3.E,
slice PR-5 (§5). Owner conditional S5→S6 approval (8 conditions verified). Builds on
#211..#215 + PR-1..PR-4; reopens none of it.

## Scope (this PR)

E区 advanced/diagnostics fold + operator-safe action record — presentation/projection
only:
- **视频变体 / 脚本理解 are already collapsed** (`<details>`, PR-A baseline) — verified
  unchanged.
- **New 过程记录 (动作记录):** a collapsed, operator-safe process/action log
  surfacing operator-language step events from existing facts.

The flagged raw-copy items (`基于素材意图：supplement` in the A区/C区 compare block;
the legacy A-J delivery wording at `task_workbench.html:1894`) are **outside E区** —
per the Owner's condition 8 they were **NOT** touched (touching them would have been
BLOCKED_SCOPE_CREEP). They remain deferred to a future copy follow-up.

## What changed

**View (`operator_workbench_view.py`)** — projection only:
- `_build_process_action_log(shots, regeneration, version_view)` → `process_action_log`:
  operator-language step events — `已记录处理方式：<shot> 补充/替换素材` /
  `上传成功：<shot> <material_name>` / `已请求再次生成预览` / `V2 新预览已生成`. Reuses
  existing shot intents / uploads / regen lifecycle / candidate truth; no new producer.
  Operator-safe by construction — only shot titles + operator-uploaded filenames.

**Template (`task_workbench.html`)** — additive E区 surface:
- New `matrix-script-primary-process-record` card with a collapsed
  `<details data-role="ms-primary-process-record-fold">` rendering
  `process_action_log` items (`ms-primary-process-record-item`), with a note that
  technical detail lives in J · 技术诊断. Renders only when the log is non-empty.

## Behavior preserved

No generation / storage / route / publish-route / `artifact_storage.py` / schema /
contract change. No new truth source; the action log is a projection. Delivery-truth
source, confirmed-main semantics, publish-readiness producer, and
`official_publish_ready` (stays `false`) are unchanged. #212 byte-consumption
unchanged. 视频变体 / 脚本理解 folds unchanged. No Hot Follow / Digital Anchor /
Akool / provider touch.

## Acceptance (Gate Spec §6 / §3.E)

- E区 diagnostics (变体 / 脚本理解 / 过程记录) collapsed by default (A-10).
- Operator-safe process log: operator-language steps only; no `local_path` / manifest
  / provider / publish URL/status / Akool (A-11). Asserted on both the log values and
  the rendered surface.
- Truth preserved: V1 main, `official_publish_ready=false`, #212 consumption (A-12/A-14).

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. New focused suite **6 passed**.
Full Matrix Script suite **1899 passed** (1893 baseline + 6 new; 0 failures) — no test
migration needed (the fold is additive; existing variants/script fold tests stay
green). `git diff --check` clean; forbidden-path scan clean; every changed file in the
authorized set.

## Boundary / not in this PR

PR-6 (Closeout) is NOT authorized. The two flagged raw-copy cleanups remain deferred
(outside E区). No full A/B/C/D/E re-letter (变体/脚本 keep their existing section
markers to avoid out-of-scope test churn).
