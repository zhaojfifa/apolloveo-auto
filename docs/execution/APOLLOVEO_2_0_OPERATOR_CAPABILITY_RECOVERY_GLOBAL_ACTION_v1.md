# ApolloVeo 2.0 Operator Capability Recovery — Global Action v1

Date: 2026-05-04
Status: Direction-correction action file. Documentation only. No code, no UI,
no runtime, no schema, no packet, no test, no template change in this Codex
step.

Active decision authority:
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`

Path note: the mission prompt named
`docs/architecture/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`,
but the decision document present in this checkout is under `docs/execution/`.
This action file cites the concrete file actually read.

## 0. Direction Correction

Current execution focus is now:

**ApolloVeo 2.0 Minimal Operator Capability Recovery Wave**

This supersedes the prior assumption that direct Plan A real operator trial is
the current main action. Plan A is not cancelled; it is demoted to a validation
action after PR-1 through PR-4 restore minimum operator capability and PR-5
explicitly reopens trial.

This action does not:
- open Platform Runtime Assembly;
- open Capability Expansion;
- authorize a real operator trial;
- reopen closed Matrix Script correction chains;
- authorize broad UI patching;
- authorize a third production line;
- make any branch other than `main` an authority baseline.

`main` is the only authority baseline. Every PR in this recovery wave starts
from current `main` after the prior PR has merged, unless Codex issues a later
written correction.

## 1. Claude Operating Rules

Claude executes one PR at a time.

For every PR:
- start from latest `main`;
- create one branch scoped to the PR;
- read this action file and the active decision document before editing;
- implement only the PR's allowed scope;
- add focused tests and execution log / evidence write-back;
- cite this action file, the decision document, and touched contract authority;
- open a PR to `main`;
- stop after the PR is opened or merged, pending Codex review/signoff.

Claude must not:
- self-open the next PR;
- bundle two PRs into one;
- repair unrelated defects opportunistically;
- convert placeholder / discovery-only surfaces into production entrances except
  where the current PR explicitly authorizes it;
- introduce provider / model / vendor / engine controls;
- treat trial as open before PR-5 acceptance.

## 2. Global Red Lines

These red lines apply to PR-1 through PR-5:

- No Platform Runtime Assembly.
- No Capability Expansion.
- No third official production line.
- No full asset platform / admin system.
- No provider / model / vendor / engine console or operator selector.
- No React / Vite full rebuild or new frontend framework.
- No Hot Follow business behavior reopen.
- No rewrite of closed Matrix Script / Digital Anchor truth.
- No reopening Matrix Script correction chain §8.A through §8.H.
- No page-first drift.
- No promotion of discovery-only surfaces as operator-ready without the PR's
  explicit scope and acceptance.
- No branch stacking as authority; merge to `main`, then continue.

## 3. PR Sequence

The execution order is mandatory:

1. PR-1 — Unified Publish Readiness Runtime Recovery.
2. PR-2 — B-roll / Asset Supply Minimum Usable Operator Capability.
3. PR-3 — Matrix Script Operator Workspace Promotion.
4. PR-4 — Digital Anchor Operator Workspace Recovery.
5. PR-5 — Real Operator Trial Re-entry Gate.

PR-2 may not start until PR-1 is merged and reviewed. PR-3 may not start until
PR-2 is merged and reviewed. PR-4 may not start until PR-3 is merged and
reviewed. PR-5 may not start until PR-1 through PR-4 are merged and reviewed.

## 4. PR-1 — Unified Publish Readiness Runtime Recovery

Goal: unify the operator-critical publishability judgment before any workspace
or trial expansion.

### Scope

PR-1 must:
- land one unified `publish_readiness` runtime producer;
- make Board, Workbench, and Delivery consume the same `publish_readiness`
  result;
- land the real `final_provenance` producer / emitter;
- make Delivery Center consume existing `required` / `blocking_publish`
  deliverable zoning;
- remove local per-surface re-computation as the authoritative publishability
  path.

Allowed implementation surface:
- runtime producer module(s) required for unified publish readiness;
- narrow presenter / projection wiring required for Board / Workbench /
  Delivery consumption;
- focused tests proving one-source consumption and final provenance emission;
- one PR-1 execution log under `docs/execution/`;
- root status / evidence-index write-back if needed.

### Red Lines

PR-1 must not:
- do UI beautification;
- build B-roll / Asset Supply pages;
- touch provider / model / vendor controls;
- start Platform Runtime Assembly;
- start Capability Expansion;
- change packet truth;
- reopen Hot Follow business behavior;
- change Matrix Script §8.A–§8.H correction truth;
- implement Digital Anchor formal entry or runtime recovery.

### Acceptance

PR-1 is acceptable only when:
- Board, Workbench, and Delivery expose the same publish readiness result for
  the same task state;
- tests prove no second truth source is used for publishability;
- tests prove `final_provenance` is emitted and consumed from the producer path;
- Delivery uses `required` / `blocking_publish` rather than ad hoc kind mapping;
- Hot Follow baseline remains behaviorally preserved;
- evidence / tests / execution log are complete.

### Stop Conditions

Claude must stop PR-1 and ask for Codex review if:
- unified readiness requires changing packet/schema truth;
- Hot Follow business behavior must be modified to pass tests;
- a surface still needs independent publishability computation;
- PR-1 would require B-roll, Digital Anchor entry, provider controls, Platform
  Runtime Assembly, or Capability Expansion.

After PR-1 is opened or merged, Claude stops. Do not begin PR-2.

## 5. PR-2 — B-roll / Asset Supply Minimum Usable Operator Capability

Goal: provide the minimum operator-visible Asset Supply / B-roll capability
needed for real production continuity, without building a complete asset
platform.

### Scope

PR-2 must:
- add a minimum read-only asset-library service;
- add a minimum promote request path;
- add a minimum promote feedback closure path;
- add a minimum operator-visible asset surface;
- support query / filter / reference / promote intent;
- explicitly preserve scene-pack non-blocking behavior.

Allowed implementation surface:
- minimal asset-library read service and storage shape needed for read-only
  capability;
- minimal promote request / closure handling;
- minimal operator surface required for query, filter, reference, promote intent;
- focused tests and execution log.

### Red Lines

PR-2 must not:
- build a complete asset platform;
- build an admin system;
- build complex CRUD;
- build a platformized asset center;
- change line packet truth;
- break Hot Follow or Matrix Script delivery truth;
- introduce provider/model/vendor controls;
- start Platform Runtime Assembly or Capability Expansion.

### Acceptance

PR-2 is acceptable only when:
- operators can view and filter a minimum asset set;
- operators can reference an asset from the allowed surface;
- operators can initiate promote intent;
- operators can see promote status closure;
- scene-pack remains non-blocking;
- no line truth is broken;
- evidence / tests / execution log are complete.

### Stop Conditions

Claude must stop PR-2 and ask for Codex review if:
- minimum usability requires a full asset database or admin console;
- promote closure requires broad workflow/state redesign;
- any line truth has to be rewritten;
- Digital Anchor or Matrix Script workspace promotion gets pulled into PR-2.

After PR-2 is opened or merged, Claude stops. Do not begin PR-3.

## 6. PR-3 — Matrix Script Operator Workspace Promotion

Goal: promote Matrix Script from inspect-first to real operator-usable workflow.

### Scope

PR-3 must:
- complete usable support for Matrix Script delivery binding / artifact lookup;
- make Matrix Script Delivery Center no longer a placeholder inspect surface;
- ensure Matrix Script variation / workbench / delivery / feedback form an
  operator-usable loop;
- preserve existing Matrix Script packet truth and correction-chain truth.

Allowed implementation surface:
- Matrix Script delivery binding / artifact lookup support;
- Matrix Script workspace / delivery wiring required for real operator
  judgment;
- focused Matrix Script tests;
- execution log and evidence write-back.

### Red Lines

PR-3 must not:
- change Matrix Script packet truth;
- reopen Matrix Script §8.A–§8.H;
- expand to Digital Anchor;
- expand to Asset Supply beyond consuming PR-2's minimum capability if needed;
- change Hot Follow business behavior;
- add provider/model/vendor controls;
- open Platform Runtime Assembly or Capability Expansion.

### Acceptance

PR-3 is acceptable only when:
- Matrix Script can be used as the first real operator trial line;
- Delivery judgment can support operations;
- variation / workbench / delivery / feedback surfaces form a coherent loop;
- no closed Matrix Script truth is rewritten;
- evidence / tests / execution log are complete.

### Stop Conditions

Claude must stop PR-3 and ask for Codex review if:
- real Matrix Script operation requires changing packet truth;
- closed §8.A–§8.H behavior must be reopened;
- Digital Anchor or broad cross-line runtime work becomes necessary;
- Matrix Script cannot reach real operator usability without Platform Runtime
  Assembly.

After PR-3 is opened or merged, Claude stops. Do not begin PR-4.

## 7. PR-4 — Digital Anchor Operator Workspace Recovery

Goal: recover Digital Anchor from inspection-only to real operator workspace.

### Scope

PR-4 must:
- add formal `/tasks/digital-anchor/new`;
- add a create-entry payload builder;
- implement publish feedback D.1 write-back;
- make role / speaker panel production-visible;
- prevent page-first drift.

Allowed implementation surface:
- Digital Anchor formal create-entry route and payload builder;
- Digital Anchor publish feedback write-back implementation;
- Digital Anchor role / speaker panel production path;
- focused Digital Anchor tests;
- execution log and evidence write-back.

### Red Lines

PR-4 must not:
- add provider/model/vendor controls;
- expand into an avatar platform;
- open a third production line;
- modify Hot Follow business behavior;
- modify Matrix Script truth;
- build Platform Runtime Assembly;
- build Capability Expansion.

### Acceptance

PR-4 is acceptable only when:
- Digital Anchor is no longer preview-only;
- operators can enter a real Digital Anchor task;
- operators can reach a real Digital Anchor workbench;
- publish feedback closure is usable within D.1 scope;
- no page-first drift remains;
- evidence / tests / execution log are complete.

### Stop Conditions

Claude must stop PR-4 and ask for Codex review if:
- Digital Anchor requires provider/vendor controls to become usable;
- implementation expands toward avatar-platform infrastructure;
- new runtime assembly abstractions are required beyond this PR's line recovery;
- any discovery-only surface would remain operator-primary after PR-4.

After PR-4 is opened or merged, Claude stops. Do not begin PR-5.

## 8. PR-5 — Real Operator Trial Re-entry Gate

Goal: reopen real operator trial only after PR-1 through PR-4 are complete.

### Scope

PR-5 must:
- rewrite Plan A trial-entry wording for the recovered operator capability
  posture;
- define operator-eligible surfaces after PR-1 through PR-4;
- state clearly that this is no longer only an authority trial;
- organize real operator trial samples and write-up;
- record product manager go/no-go;
- record coordinator / architect / reviewer signoff.

Allowed implementation surface:
- documentation and trial governance only unless Codex explicitly approves a
  narrow non-code validation helper;
- Plan A / write-up / evidence-index updates;
- no runtime implementation by default.

### Red Lines

PR-5 must not:
- enter Platform Runtime Assembly;
- enter Capability Expansion;
- add provider/model/vendor controls;
- add new production lines;
- patch incomplete PR-1 through PR-4 work under trial-governance cover.

### Acceptance

PR-5 is acceptable only when:
- PR-1 through PR-4 are merged and reviewed;
- product manager signs go/no-go;
- coordinator, architect, and reviewer sign off;
- operator-eligible surfaces are explicit;
- non-eligible surfaces remain blocked or labeled;
- real operator trial can begin from a written gate.

### Stop Conditions

Claude must stop PR-5 and ask for Codex review if:
- any PR-1 through PR-4 acceptance is incomplete;
- product manager go/no-go is missing;
- signoff is incomplete;
- real trial would require Platform Runtime Assembly or Capability Expansion.

After PR-5, Claude stops. Real operator trial begins only if PR-5 acceptance is
green.

## 9. Immediate Claude Handoff — Execute PR-1 First

Claude's next task is PR-1 only:

**PR-1 · Unified Publish Readiness Runtime Recovery**

Start conditions:
- checkout latest `main`;
- confirm this action file and the active decision document are present;
- confirm no in-flight branch is used as authority;
- read publish-readiness, delivery, current-attempt, operator-surface, and
  presenter code/contract authority before editing.

Required PR-1 output:
- unified `publish_readiness` producer implementation;
- `final_provenance` producer / emitter implementation;
- Board / Workbench / Delivery consumption of the unified producer;
- tests proving consistency and no second truth source;
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`;
- evidence-index / status write-back.

PR-1 branch suggestion:
- `claude/operator-capability-recovery-pr1-publish-readiness`

PR-1 must stop after its PR is opened or merged. PR-2 requires Codex review and
explicit next instruction.

## 10. Final Gate

- Minimal Operator Capability Recovery re-anchored: YES
- PR-1 through PR-5 sliced: YES
- Platform Runtime Assembly opened: NO
- Capability Expansion opened: NO
- real operator trial authorized now: NO
- `main` remains only authority baseline: YES
