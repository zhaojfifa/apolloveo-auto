# Harness X — Role Engineering Design (2026-06-07)

Status: **DESIGN — docs-only. A coordination protocol spec, not automation code and
not a runtime authority.** It promotes Harness X v2.1 from a *workflow suggestion*
into an *executable multi-role coordination protocol*: a state machine in which each
role consumes a defined artifact, produces a defined artifact, declares a verdict,
and never self-authorizes the next phase except where the protocol explicitly allows
auto-advance. The **Owner** is the only final phase-transition authority for risky
steps.

Source inputs:
- `Harness-X_WORKFLOW_v2.1.md` (v2.1 candidate baseline) — roles, phases, red lines,
  Matrix Script retrospective, report templates.
- v2.0 `WORKFLOW.md` — the engineering spine (Architect → Developer → Reviewer →
  Owner) and the L0/L1/L2 grading + red lines this design preserves.

This design does not supersede repo authority. Where it conflicts with
`ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, or any Bucket A authority,
the repo authority wins and this spec is corrected in a docs-only follow-up. In
particular, Harness X roles are a *coordination* protocol; they never override the
wave gate, the contract-first rule, or the no-private-memory rule (CLAUDE.md §3).

---

## 1. Purpose (§2.1)

Harness X roles are **not multiple agents acting freely**. They are positions in a
**state machine**. The protocol exists to make the cost of being wrong cheap: catch
operability and scope problems in a planning doc or a static preview — before any
runtime code is written — rather than in production.

Every role obeys four invariants:

- **Consume** exactly one defined prior artifact (its input).
- **Produce** exactly one defined artifact (its output), in the standard shape (§4).
- **Declare** a verdict: `PASS` / `PASS WITH ISSUES` / `FAIL` / `BLOCKED`.
- **Never self-authorize** the next phase unless the transition table (§3) marks it
  auto-advance. Risky transitions require Owner approval.

The Owner remains the only final phase-transition authority for risky steps
(merge to main, deployment, scope expansion, authority change, overriding an
Operator Review FAIL, and crossing Gate Spec → runtime implementation).

This is the engineering generalization of the lesson from the Matrix Script case
(§8): *capability correct ≠ operationally usable; tests green ≠ operator knows how
to use it; observable state ≠ clear product path.*

---

## 2. Role Definitions (§2.2)

Each role is specified as a contract. "Required reads" always implicitly includes
the boot sequence in `CLAUDE.md` §2 and the index-first discipline; only
task-specific reads are listed per role.

### 2.1 Architect

- **Purpose:** Qualify the problem and decide whether it enters the engineering
  spine (§3.1 of v2.1) or the operator-product flow (§3.2). Set architectural
  boundaries.
- **Inputs:** Problem Raised (Owner's description / a failing trial / a bug).
- **Required reads:** `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_RULES.md`, the
  relevant Bucket A / authority index.
- **Output artifact:** Problem Decision Memo (§4).
- **Allowed actions:** classify the problem (capability / flow / state / operator-
  comprehension / environment); name the authority that governs; declare the task
  type and complexity (L0/L1/L2/P-flow).
- **Forbidden actions:** write runtime code; author the implementation; bypass the
  wave gate.
- **PASS criteria:** problem is named with one diagnosis sentence; task type +
  complexity assigned; governing authority cited.
- **BLOCK conditions:** required authority file absent; the request conflicts with
  active wave focus → `BLOCKED_AUTHORITY_CONFLICT`.
- **Next consumer:** Product Planner (P-flow) or Developer (engineering/bug).

### 2.2 Product Planner

- **Purpose:** Translate already-shipped capability into an operator-executable flow
  — primary path, advanced fold, diagnostics, state vocabulary, page zones.
- **Inputs:** Problem Decision Memo (P-flow verdict).
- **Required reads:** Bucket A authority set; relevant execution evidence; substrate
  PRs.
- **Output artifact:** Workflow Plan (`docs/design/<feature>_WORKFLOW_PLAN_<date>.md`).
- **Allowed actions:** define mainline / advanced / diagnostic split; state language;
  A/B/C/D/E zoning; per-button expectations; a gate-spec-first PR slicing proposal.
- **Forbidden actions:** write code; authorize implementation; supersede Bucket A;
  author a new IA / parallel flow.
- **PASS criteria:** answers the ten planning questions (v2.1 §5 Phase B); names what
  must not change; explicitly marks itself non-authority.
- **BLOCK conditions:** Bucket A authority missing or contradictory →
  `BLOCKED_AUTHORITY_CONFLICT`.
- **Next consumer:** Preview Builder.

### 2.3 Preview Builder

- **Purpose:** Build a static preview + screenshot so a human can judge whether the
  flow is comprehensible — cheaply, before runtime.
- **Inputs:** Workflow Plan.
- **Required reads:** the Workflow Plan; the relevant preview Bucket A reference.
- **Output artifact:** Static Preview (`docs/design/previews/<feature>_preview.html`)
  + Preview Screenshot (`docs/design/screenshots/<feature>_preview_<date>.png`).
- **Allowed actions:** static HTML/CSS only; a local-only collapse toggle; one
  realistic business scenario; reuse of a throwaway static server purely to render a
  screenshot (removed afterward).
- **Forbidden actions:** connect a backend; use real data; modify `gateway/**`, the
  real Workbench, routes, or any runtime.
- **PASS criteria:** all required zones rendered; realistic scenario (not a blank
  skeleton); no runtime wiring; `git diff --check` clean; docs-only.
- **BLOCK conditions:** cannot render without backend / real data → re-scope with
  Product Planner; `BLOCKED_SCOPE_CREEP` if the preview starts requiring runtime.
- **Next consumer:** Operator Reviewer.

### 2.4 Operator Reviewer

- **Purpose:** Judge, strictly from a front-line operator's seat, whether the flow is
  independently operable. The pre-implementation usability gate.
- **Inputs:** Static Preview + Screenshot (Workflow Plan as context only).
- **Required reads:** the preview HTML + screenshot. **Does not read code.**
- **Output artifact:** Operator Review Report (§4).
- **Allowed actions:** answer the operator questions (v2.1 §5 Phase D); flag confusing
  copy / layout / density; mark must-fix vs defer.
- **Forbidden actions:** read or evaluate code; assess architecture; let an
  engineering "tests pass" argument override an operability finding.
- **PASS criteria:** can complete the flow without engineer help; no operator-blocking
  confusion remains.
- **BLOCK conditions:** preview missing required zones / not renderable →
  `BLOCKED_OPERATOR_FAIL` back to Preview Builder.
- **Next consumer:** Owner (decision), then Gate Spec Author (on PASS).

### 2.5 Gate Spec Author

- **Purpose:** Freeze the validated plan + preview into enforceable engineering rules
  — the single input to runtime implementation.
- **Inputs:** Workflow Plan + passed Operator Review + Owner go.
- **Required reads:** Bucket A; the Workflow Plan; both Operator Review rounds.
- **Output artifact:** Gate Spec (`docs/design/<feature>_GATE_SPEC_<date>.md`).
- **Allowed actions:** binding zone rules; state-source / four-layer mapping; button
  behavior; data-projection + forbidden-leakage rules; acceptance tests; PR slicing;
  forbidden list; a `<fill>` signoff block.
- **Forbidden actions:** implement anything; open a wave; supersede Bucket A; authorize
  backend/storage/provider/schema/contract change.
- **PASS (READY) criteria:** every required section present; forbidden scope explicit
  and path-scannable; acceptance rows concrete; slices small + ordered; authority
  boundary stated; signoff block present.
- **BLOCK conditions:** Operator Review not PASS → cannot author (hard predecessor);
  scope exceeds plan → `BLOCKED_SCOPE_CREEP`.
- **Next consumer:** Owner (signoff), then Developer (on signoff merge).

### 2.6 Developer

- **Purpose:** Implement strictly to the Gate Spec, one PR slice at a time, with
  tests.
- **Inputs:** signed Gate Spec; the specific slice (e.g. PR-1).
- **Required reads:** the Gate Spec; `ENGINEERING_RULES.md`; the substrate it consumes.
- **Output artifact:** Implementation PR Report (§4) + the code/test diff.
- **Allowed actions:** the slice's allowed scope only; presentation/copy/re-order over
  existing truth (for a UI gate); dedicated tests; behavior preservation.
- **Forbidden actions:** self-review as the gating review; expand scope; bundle slices;
  treat green tests as operator acceptance; touch any forbidden path.
- **PASS criteria:** diff inside the slice's allowed scope; tests cover the user path;
  forbidden-path scan clean; behavior preserved; report complete.
- **BLOCK conditions:** the Gate Spec is ambiguous → back to Gate Spec Author;
  required change falls in forbidden scope → `BLOCKED_SCOPE_CREEP`; tests fail →
  `BLOCKED_TEST_FAIL`.
- **Next consumer:** Code Reviewer.

### 2.7 Code Reviewer

- **Purpose:** Independent diff / boundary / test / leakage audit. Non-asymmetric
  review (the implementer never gates their own code).
- **Inputs:** Implementation PR Report + diff.
- **Required reads:** the Gate Spec; the diff; the forbidden-path list.
- **Output artifact:** Code Review Report (§4).
- **Allowed actions:** verify diff ⊆ Gate Spec; forbidden-path scan; test-coverage
  check; backend-field / secret leakage scan; state-drift check.
- **Forbidden actions:** produce the product design; substitute for the Owner's
  approval; substitute for the Operator Trial.
- **PASS criteria:** no Gate Spec deviation; no forbidden-path touch; tests cover the
  user path; no leakage; no state drift.
- **BLOCK conditions:** forbidden-path touched / leakage / scope deviation →
  `BLOCKED_SCOPE_CREEP`; tests insufficient → `BLOCKED_TEST_FAIL`.
- **Next consumer:** Operator Trial Reviewer.

### 2.8 Operator Trial Reviewer

- **Purpose:** Run the real operator path against the implemented build (not just
  pytest). Confirms the shipped flow is what the preview promised.
- **Inputs:** merged/stageable implementation (per slice or at integration).
- **Required reads:** the Gate Spec acceptance rows; the original Operator Review.
- **Output artifact:** Operator Trial Report (§4).
- **Allowed actions:** exercise the live operator path (新建 → 生成 V1 → 检查 Shot →
  上传 → 再生成 V2 → 对比 → 确认 → 交付); confirm acceptance rows; confirm no leakage
  live.
- **Forbidden actions:** approve deployment; substitute for Owner approval; rewrite the
  Gate Spec.
- **PASS criteria:** the operator path completes as specified; acceptance rows hold
  live; no leakage observed.
- **BLOCK conditions:** operator path breaks / acceptance fails → `BLOCKED_OPERATOR_FAIL`
  back to Developer (or, if it's a flow problem, back to Product Planner).
- **Next consumer:** Owner (merge/deploy approval).

### 2.9 Scribe

- **Purpose:** Record execution, closure, and lessons; keep the trail on-index. Does
  not decide anything.
- **Inputs:** any phase's artifacts at closeout.
- **Required reads:** the artifacts being recorded; `docs/README.md` placement.
- **Output artifact:** Closure Report (§4) + Lessons Entry (`tasks/lessons.md` per
  v2.1 §13).
- **Allowed actions:** docs-only summarization; index pointers; lessons capture.
- **Forbidden actions:** author authority; change verdicts; alter state.
- **PASS criteria:** closure records every acceptance row's final state; lessons entry
  in the standard format; pointers added.
- **BLOCK conditions:** none typically; if evidence is missing, requests it (no
  invention).
- **Next consumer:** Owner / future readers.

### 2.10 Owner

- **Purpose:** The only final phase-transition authority for risky steps. Adjudicates;
  does not get auto-overridden by any tool.
- **Inputs:** the relevant phase report(s).
- **Required reads:** the verdicts; the divergence reports if any.
- **Output artifact:** Owner Decision (recorded as an approval / direction; for risky
  transitions, an Owner Decision Request is answered).
- **Allowed actions:** approve a transition; send back; stop a direction; merge;
  authorize deploy; authorize scope/authority change.
- **Forbidden actions:** (by design, none restricted) — but Owner approval is required,
  not optional, at every risky transition.
- **PASS criteria:** decision recorded against the specific transition.
- **Next consumer:** whichever role the decision unblocks.

> Auxiliary roles from v2.1 (Librarian for L2 history scans, Worker for future
> pipeline automation) are recognized but out of scope for this protocol version;
> Worker stays disabled until §7 automation maturity is reached.

---

## 3. State Machine (§2.3)

### 3.1 States

```
S0  Problem Raised
S1  Architect Decision Ready
S2  Product Plan Ready
S3  Preview Ready
S4  Operator Review Passed
S5  Gate Spec Ready                (READY = §10 signoff merged → gate open)
S6  Implementation PR Ready
S7  Code Review Passed
S8  Operator Trial Passed
S9  Merge / Deploy Approved        (terminal for the slice/feature)
```

Blocked (terminal-until-resolved) states:

```
BLOCKED_STATE_DIVERGENCE     repo state ≠ premise (see §6)
BLOCKED_SCOPE_CREEP          work exceeds the authorized scope / forbidden path
BLOCKED_OPERATOR_FAIL        operator cannot complete the flow
BLOCKED_TEST_FAIL            tests fail / coverage insufficient
BLOCKED_AUTHORITY_CONFLICT   spec/plan conflicts with Bucket A or wave gate
```

### 3.2 Transition Table

Legend: **AA** = auto-advance allowed (role may proceed without Owner);
**OA** = Owner approval required.

| From | To | Allowed role | Required artifact | AA | OA | Rollback / retry target |
|------|----|--------------|-------------------|----|----|--------------------------|
| S0 | S1 | Architect | Problem Decision Memo | No | OA (task-type + entry) | stay S0; ask Owner |
| S1 | S2 | Product Planner | Workflow Plan | AA (author) | OA to *merge* plan | back to S1 if misclassified |
| S2 | S3 | Preview Builder | Static Preview + Screenshot | AA | OA to merge preview | back to S2 if plan gap |
| S3 | S4 | Operator Reviewer | Operator Review Report = PASS | No | — (verdict is the gate) | PASS WITH ISSUES → S2/S3; FAIL → S2 |
| S4 | S5 | Gate Spec Author | Gate Spec (authored) | AA (author) | **OA — §10 signoff opens gate** | back to S4 if not PASS |
| S5 | S6 | Developer | Implementation PR Report (slice) | No | **OA — gate open + slice order** | BLOCKED_* per §3.1 |
| S6 | S7 | Code Reviewer | Code Review Report = PASS | AA (run review) | — (verdict is the gate) | FAIL → S6 (Developer) |
| S7 | S8 | Operator Trial Reviewer | Operator Trial Report = PASS | No | — (verdict is the gate) | FAIL → S6 or S2 |
| S8 | S9 | Owner | Owner Decision = approve | No | **OA — merge / deploy** | hold at S8 |
| any | BLOCKED_* | any role | Divergence / Block Report | — | **OA to clear** | resume at the named retry target |

Hard rules encoded in the table:

- **S3 → S4 only on Operator Review `PASS`.** `PASS WITH ISSUES` does **not**
  auto-authorize the next phase — it routes back to fix the plan/preview, then
  re-review (Matrix Script ran two rounds for exactly this reason).
- **S4 → S5 is a hard predecessor:** no Gate Spec may be authored before Operator
  Review PASS.
- **S5 → S6 requires the Gate Spec's §10 signoff merged** (Architect + Reviewer) —
  authoring the Gate Spec does *not* open the gate; the Owner-approved signoff does,
  and only for the first slice.
- **S7 → S8 and S8 → S9 are distinct:** Code Review PASS never replaces the Operator
  Trial, and Operator Trial PASS never replaces Owner merge/deploy approval.

---

## 4. Artifact Contracts (§2.4)

Every artifact shares a header: title, date, status line (DESIGN / PLANNING /
GATE / REPORT), source inputs, and an explicit authority line. Standard types:

| Artifact | Path convention | Required sections | Minimum evidence | Signs off | Consumed by |
|----------|-----------------|-------------------|------------------|-----------|-------------|
| **Problem Decision Memo** | `docs/process/decisions/<feature>_<date>.md` (or inline) | diagnosis sentence; task type; complexity; governing authority; entry verdict | cited authority file | Architect | Product Planner / Developer |
| **Workflow Plan** | `docs/design/<feature>_WORKFLOW_PLAN_<date>.md` | capabilities; mainline; advanced fold; diagnostics; A/B/C/D/E; state language; button expectations; PR slicing; must-not-change | substrate PR list; authority citation | Product Planner | Preview Builder / Gate Spec |
| **Static Preview** | `docs/design/previews/<feature>_preview.html` | the required zones; one realistic scenario | renders standalone; no network | Preview Builder | Operator Reviewer |
| **Preview Screenshot** | `docs/design/screenshots/<feature>_preview_<date>.png` | full-page capture | matches the HTML | Preview Builder | Operator Reviewer / Owner |
| **Operator Review Report** | `docs/reviews/<feature>_operator_review[_rN].md` | overall; step-by-step; confusing points; recommended changes; verdict | per-question answers | Operator Reviewer | Owner / Gate Spec |
| **Gate Spec** | `docs/design/<feature>_GATE_SPEC_<date>.md` | zone rules; state mapping; button behavior; leakage list; acceptance tests; PR slices; forbidden list; signoff block | acceptance rows A-n; forbidden-path list | Architect + Reviewer (§10) | Developer |
| **Implementation PR Report** | in PR body + `docs/execution/<feature>_<slice>_*.md` | scope; files; tests; boundary; validation | test counts; diff scope; forbidden-scan | Developer | Code Reviewer |
| **Code Review Report** | `docs/reviews/<feature>_code_review[_slice].md` | diff vs spec; forbidden-path; tests; leakage; verdict | scan outputs | Code Reviewer | Operator Trial Reviewer |
| **Operator Trial Report** | `docs/execution/<feature>_operator_trial_<date>.md` | path walkthrough; acceptance-row results; leakage check; verdict | live-path evidence | Operator Trial Reviewer | Owner |
| **Closure Report** | `docs/execution/<feature>_closure_<date>.md` | what landed; acceptance final state; freezes re-audited; signoff | per-row PASS/FAIL | Scribe + signoffs | Owner / future |
| **Lessons Entry** | `tasks/lessons.md` (append) | 做了什么 / 哪里不顺 / 根因 / 下次怎么改 / 是否更新 WORKFLOW | one entry | Scribe | future readers |

Authority class of each artifact (from v2.1 §6.1) is fixed: Bucket A = authority;
Gate Spec = authority (this wave only); Workflow Plan / Preview / Operator Review /
Execution Report = **not** authority.

---

## 5. Acceptance Gates (§2.5)

For each gated phase, `PASS` / `PASS WITH ISSUES` / `FAIL` mean:

| Gate | PASS | PASS WITH ISSUES | FAIL |
|------|------|------------------|------|
| **Product Planner Review** | flow solves the operational problem; non-authority stated | solves it but with gaps that are preview-testable → proceed to preview, carry issues | does not solve it / introduces new IA → redo plan |
| **Preview Builder** | all zones + realistic scenario; docs-only; clean | renders but a zone is thin → note, still usable | not renderable / requires runtime → BLOCKED_SCOPE_CREEP |
| **Operator Review** | operable without engineer help | operable but specific must-fixes remain → **back to plan/preview, re-review** (no auto-advance) | cannot operate → redo plan |
| **Gate Spec Review** | READY: enforceable, scoped, authority-clean | minor clarity gaps that don't block merge → land + follow-up | not enforceable / scope leak → rewrite |
| **Implementation Review** | diff ⊆ spec; tests cover user path; clean | trivial nits → land + nit follow-up | spec deviation / forbidden-path / leakage → BLOCKED |
| **Code Review** | no deviation / leakage / drift | cosmetic only | any boundary breach → BLOCKED |
| **Operator Trial** | live operator path completes per spec | completes with minor cosmetic gaps → log, defer | path breaks / acceptance fails → BLOCKED_OPERATOR_FAIL |
| **Closure** | every acceptance row PASS + signoffs | rows PASS with documented deferrals | unresolved acceptance row → not closed |

**Binding gate rules (non-negotiable):**

1. `PASS WITH ISSUES` does **not** automatically authorize implementation.
2. Operator Review `FAIL` returns to Product Planner or Preview Builder — never
   forward.
3. Gate Spec `READY` (signoff merged) is required before the Developer writes runtime
   code.
4. Implementation PR `PASS` does **not** replace the Operator Trial.
5. Code Review `PASS` does **not** replace Owner approval.

---

## 6. Divergence Protocol (§2.6)

A role MUST run a state check at phase entry. If the observed repo/PR state conflicts
with the premise it was handed, it enters `BLOCKED_STATE_DIVERGENCE` and stops.

Trigger examples (all observed in or near the Matrix Script case):

```
instruction says a PR is OPEN but git says it is MERGED
a planning doc is assumed on main but is absent (PR still open)
a handoff references a file that does not exist
current main already contains a LATER PR than the instruction assumes
a required authority file is absent
```

Required response — **stop-and-report, never patch over**:

```
1. STOP at the current phase. Do not advance.
2. Report the divergence precisely: expected vs observed, with the git/PR evidence.
3. Do NOT patch the discrepancy. Do NOT open a PR on a wrong premise.
4. Do NOT build on an unmerged/absent artifact unless the Owner explicitly authorizes
   it (and then only as clearly-labelled branch-based validation, not as authority).
5. Ask the Owner for corrected direction; resume only from the Owner-named retry
   target.
```

Precedent: the preview task correctly stopped when #216 was unmerged, and resumed
only on explicit Owner authorization to validate against the #216 branch — without
treating it as main authority. That is the canonical divergence response.

---

## 7. Automation Readiness (§2.7)

**Safe to automate later** (read-only detection + templating; no state change):

```
state detection from git / gh PR status (which S-state a feature is in)
required-file presence check (does the expected artifact exist at its path)
forbidden-path scan (git diff --name-only against the forbidden list)
artifact completeness check (required sections present in a report)
report-template generation (pre-fill the standard headers/sections)
transition recommendation (suggest the next allowed transition + who acts)
```

**Must NOT be automated without explicit Owner action** (every risky transition):

```
merge to main
deployment
scope expansion
changing authority (what is Bucket A / what a Gate Spec governs)
overriding an Operator Review FAIL
moving from Gate Spec to runtime implementation (S5 → S6)
```

Design rule: automation may *detect, check, and recommend*; it may never *decide* a
risky transition. The Owner's approval is a required input the automation waits on,
not a default it assumes. (This mirrors the v2.1 red line "不得把 AI 自我授权"; the
Worker role stays disabled until these read-only checks are proven.)

---

## 8. Matrix Script Case Mapping (§2.8)

The Matrix Script Guided Operator Workflow case is the worked example. State mapping:

| Artifact / event | Harness X state | Verdict |
|------------------|-----------------|---------|
| Operational complaint: "capability exposed, not productized" | S0 Problem Raised | — |
| (Architect framing: flow problem, not capability problem) | S1 Architect Decision Ready | flow problem |
| **#216** Guided Operator Workflow Planning | S2 Product Plan Ready | PASS |
| **#217** Static Preview + Screenshot | S3 Preview Ready | built |
| **Operator Review Round 1** | S3→ (gate) | **PASS WITH ISSUES** (3 must-fixes) |
| Preview Revision (shot reason / upload→regenerate / drop raw field) | S3 (re-enter) | fixed |
| **Operator Review Round 2** | S4 Operator Review Passed | **PASS** |
| **#218** Guided Operator Workflow Gate Spec | S5 Gate Spec Ready (authored) | READY TO MERGE |
| Gate Spec §10 signoff (pending) | S5 → gate-open precondition | `<fill>` |
| **Future PR-1..PR-6** implementation slices | S6 → S7 → S8 per slice | not started |
| Closeout (PR-6) + Operator Trial | S8 → S9 | not started |

Key protocol facts the case demonstrates:

- `PASS WITH ISSUES` at Round 1 did **not** advance to Gate Spec — it routed back to
  the preview, exactly per §5 rule 1/2.
- The Gate Spec (#218) was authored **only after** Operator Review Round 2 PASS — the
  S4 → S5 hard predecessor.
- #216/#217 remain **Planning / Review Inputs (NOT authority)**; #218 is an accepted
  implementation gate that does **not** supersede Bucket A — the §4 authority classes
  held throughout.
- The gate to runtime (S5 → S6) is still **closed**: #218's §10 signoff carries
  `<fill>` placeholders, so no Developer work is authorized yet.

---

## 9. Templates (§2.9)

Concise, copy-ready. (The full per-phase report templates already live in
`Harness-X_WORKFLOW_v2.1.md` §14; these five fill the protocol-level gaps.)

### 9.1 Role Handoff Packet

```markdown
# Handoff: <from-role> → <to-role> · <feature> · <date>
- from-state → to-state:
- input artifact (path):
- output artifact expected (path):
- verdict carried: PASS / PASS WITH ISSUES (issues listed) / —
- premise the next role must verify: <git/PR facts to check>
- forbidden scope reminder: <paths/behaviors>
```

### 9.2 Divergence Report

```markdown
# Divergence Report · <feature> · <date>
- phase / role:
- expected premise:
- observed state (evidence):  <git log / gh pr view output>
- conflict type: STATE_DIVERGENCE / SCOPE_CREEP / OPERATOR_FAIL / TEST_FAIL / AUTHORITY_CONFLICT
- action taken: STOPPED — did not patch, did not open PR
- Owner question: <what direction is needed>
- proposed retry target (for Owner to confirm):
```

### 9.3 Owner Decision Request

```markdown
# Owner Decision Request · <feature> · <date>
- transition requested: S<x> → S<y>
- why this is a risky (Owner-gated) transition:
- evidence the predecessor verdict is satisfied:
- options: [A approve] [B send back to S<z>] [C stop direction]
- recommendation:
```

### 9.4 Transition Report

```markdown
# Transition Report · <feature> · <date>
- from-state → to-state:
- role acted:
- artifact produced (path):
- auto-advance or Owner-approved:
- acceptance rows touched:
- next allowed transition + role:
```

### 9.5 Closure Report

```markdown
# Closure Report · <feature> · <date>
- slices landed (PRs):
- acceptance rows: <A-1..A-n each PASS/FAIL>
- preserved freezes re-audited:
- operator trial result:
- signoffs: Architect / Reviewer / Operator / Owner
- lessons entry appended: yes/no
- verdict: CLOSED / NOT CLOSED
```

---

## 10. Boundary & Authority Note

- **Docs-only.** This design adds no automation code and changes no runtime.
- It does **not** modify Matrix Script runtime, `gateway/**`, `schemas/**`,
  `docs/contracts/**`, `artifact_storage.py`, Hot Follow, Digital Anchor, or
  Akool/provider logic, and does **not** change `CURRENT_ENGINEERING_FOCUS.md`.
- Harness X is a **coordination protocol**, not a source of project authority. It
  sequences who-acts-when; it never overrides `ENGINEERING_RULES.md`, the wave gate,
  contract-first discipline, or the no-private-memory rule (CLAUDE.md §3). Where it
  conflicts with repo authority, the repo authority wins.
- This document is itself a Harness X artifact at design level; promoting it (or a
  `harness-x/WORKFLOW.md`) to a binding process authority is an Owner decision, not a
  side effect of merging this doc.

*The point of the protocol is not more roles — it is that each role speaks only in
the phase it is good at, and no role authorizes its own next step where the cost of
being wrong is high.*
