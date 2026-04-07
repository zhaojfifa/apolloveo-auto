# Phase-2 Execution Plan

## 1. Purpose

This runbook freezes the execution sequence for Phase-2 on top of `VeoMVP01-HF-Phase1`.

Phase-2 goal:

- build the next-stage factory foundation
- keep product scope stable
- preserve truth ownership boundaries

## 2. Phase-2 PR Sequence

### PR-5

Docs / contracts / ADR / runbooks freeze.

Required outputs:

- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/script_video_planning_contract.md`
- `docs/contracts/action_replica_planning_assets_contract.md`
- `docs/adr/ADR-phase2-skills-worker-planning.md`
- `docs/runbooks/phase2_execution_plan.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`

### PR-6

Skills Runtime MVP for Hot Follow.

Required outcomes:

- line-scoped bundle loader path
- hot_follow bundle skeleton
- strategy-only logic moved into bundle modules
- no truth ownership regression

### PR-7

Worker Gateway MVP.

Required outcomes:

- normalized worker request/response contract
- internal / external / hybrid execution slot
- existing execution paths begin adapting toward gateway shape
- worker does not write truth directly

### PR-8

Script Video planning layer.

Required outcomes:

- planning draft contract
- candidate vs linked asset dual-state
- file-usage indexing hook
- prompt template registry skeleton

### PR-9

Action Replica planning asset view.

Required outcomes:

- planning asset model for identity / wardrobe / prop / role / shot binding
- mapping hooks to future line execution
- no giant UI shell

## 3. Guardrails

Phase-2 must not become:

- studio product import
- new global UI shell
- broad platform rewrite
- truth-layer rewrite
- hidden second-line launch

Required rules:

- line contract stays primary
- skills are strategy only
- worker gateway is execution only
- status / deliverable / asset sink remain the truth layer

## 4. Verification Discipline

Every PR must include:

- docs update in the same PR
- focused repo-grounded tests
- explicit scope boundary
- explicit remaining debt

If a PR makes a business-critical claim, it must provide:

- live execution evidence
or
- a clear statement that evidence is repo-grounded only

## 5. Hot Follow Safety Rule

Hot Follow is the sample line for Phase-2 runtimeization.

This means:

- Hot Follow may gain runtime hooks first
- Hot Follow behavior must remain stable
- no Phase-2 PR should silently rewrite Hot Follow business semantics

## 6. Planning-Line Safety Rule

`script_video_line` and `action_replica_line` are planning-first targets in Phase-2.

This means:

- contract and draft structure may land first
- no heavy product shell should land in the same phase by drift
- planning outputs must not be treated as final execution truth

## 7. Recommended Validation Set

### PR-5

- docs presence / discoverability checks

### PR-6

- import smoke
- Hot Follow bundle loader tests
- no truth write regression tests

### PR-7

- worker request/response contract tests
- timeout / retry surface tests
- Hot Follow execution adapter regression tests

### PR-8

- planning schema tests
- candidate vs linked state tests
- file-usage index tests

### PR-9

- planning asset schema tests
- role / shot binding tests
- line mapping tests

## 8. Interpreter Baseline

Use the current repository recommendation from:

- `docs/runbooks/VERIFICATION_BASELINE.md`

If `./venv/bin/python` is available, it remains the preferred interpreter for import/runtime tests.

## 9. Current Phase-2 Limits

Phase-2 currently does not authorize:

- live provider success claims without real execution
- UI shell expansion
- second-line business rollout
- OpenClaw platform build-out
