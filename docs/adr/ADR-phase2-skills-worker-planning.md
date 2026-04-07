# ADR: Phase-2 Skills / Worker / Planning Baseline

- Status: Accepted
- Date: 2026-04-07
- Scope: Phase-2 foundation after `VeoMVP01-HF-Phase1`

## 1. Context

`VeoMVP01-HF-Phase1` established:

- docs-first Hot Follow contract freeze
- router import cleanup
- compose service extraction
- live line binding
- YAML-backed ready gate

That phase intentionally stopped before:

- real skills bundle runtime
- worker gateway runtime boundary
- planning-first upstream contracts for future lines

The codebase now has the correct Phase-1 foundation, but still lacks the next explicit boundary layer for:

- strategy
- execution routing
- planning drafts
- planning asset views

## 2. Decision

Phase-2 will proceed in controlled, docs-first PRs with this sequence:

1. PR-5: contracts / ADR / runbooks freeze
2. PR-6: Skills Runtime MVP for Hot Follow
3. PR-7: Worker Gateway MVP
4. PR-8: Script Video planning contract and draft path
5. PR-9: Action Replica planning asset view

These PRs are intentionally ordered so that:

- contracts land before runtime
- strategy is separated from execution
- planning stays separate from truth
- new line planning does not smuggle in a studio shell

## 3. Why Skills Runtime Exists

We need a boundary for:

- input interpretation
- routing judgment
- quality/compliance advisory
- recovery guidance

without turning that logic into:

- status policy
- repo truth ownership
- deliverable ownership

The Phase-1 advisory hook proved that line-scoped read-only advisory can exist safely. Phase-2 extends this into a real line-scoped skills bundle path, but still keeps truth writes outside.

## 4. Why Worker Gateway Exists

Current execution paths still show the classic risk:

- provider branching scattered in services
- local subprocess execution and remote provider execution using different implicit surfaces
- no common request/response envelope for future execution slots

Worker Gateway is needed so future execution targets share one boundary:

- internal
- external
- hybrid

This enables clean future slots for:

- existing provider-backed parse/TTS style paths
- OpenClaw-like control surfaces later
- other future worker-backed lines

without letting execution become the truth owner.

## 5. Why Planning Contracts Exist Now

The Jellyfish importability review showed a useful split:

- the most valuable import is planning/intermediate structure
- the least suitable import is studio product shell and task-status ownership

Therefore Phase-2 freezes planning contracts before UI or generator work:

- `script_video_line` gets planning-first script/shot/candidate/link structure
- `action_replica_line` gets planning asset identity/wardrobe/prop/role/shot structure

This preserves:

- candidate vs linked dual-state
- file-usage indexing hooks
- prompt template registry references

while rejecting:

- project/chapter/studio shell
- workflow editor scope
- direct business truth writes from planning models

## 6. Layering Decision

Target layering remains:

1. line contract binding
2. skills runtime
3. worker gateway
4. state / deliverable / asset sink truth
5. view assembly / presentation
6. planning drafts and planning asset views as upstream non-truth structures

Important rule:

- planning is not a replacement for execution truth
- skills are not a replacement for status policy
- worker gateway is not a replacement for deliverable ownership

## 7. Why Not A Studio Shell

This ADR explicitly rejects Phase-2 scope creep into:

- top-level project/chapter/studio UI
- agent management shell
- workflow editor
- video editor shell

Reason:

- product-shell import would blur truth boundaries again
- it would also outrun the existing factory line-contract architecture

The planning contracts absorb structure, not product shell.

## 8. Consequences

### 8.1 Positive

- Hot Follow can become the first real line with skills and worker slots
- future lines get planning-first upstream structures without immediate UI explosion
- execution and truth boundaries become clearer

### 8.2 Negative / Cost

- more contracts must be maintained before code lands
- some fields will remain hook-only until later PRs
- there will be intentional temporary asymmetry between Hot Follow runtime maturity and new planning-line maturity

## 9. Non-Goals

This ADR does not authorize:

- full agent platform implementation
- broad OpenClaw expansion
- second-line product launch in the same PR
- giant workbench UI
- direct truth writes from skills/workers/planning

## 10. Merge Discipline

For every Phase-2 PR:

- docs/contracts/ADR/runbook/log updates land in the same PR
- repo-grounded verification is required
- no live upstream success claim is allowed without real execution evidence
- Hot Follow business behavior must remain stable unless the PR is explicitly about Hot Follow behavior
