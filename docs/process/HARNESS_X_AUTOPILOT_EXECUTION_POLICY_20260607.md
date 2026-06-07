# Harness X — Autopilot Execution Policy (2026-06-07)

Status: **PROCESS POLICY PROPOSAL — docs-only. Not automation code, not a runtime
authority, not a change to Harness X authority rules.** It defines an *autopilot
path* so low-risk steps run automatically while the Owner is asked only at genuinely
risky transitions.

Builds on `docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md` (the role
state machine §3 and the automation-readiness split §7). It refines *how fast* the
machine may move on its own; it does **not** add roles, change the S0..S9 / BLOCKED_*
states, or relax any red line. Where this policy conflicts with the role engineering
design, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, or Bucket A, the
underlying authority wins.

---

## 1. Why this policy

Harness X is **safe but slow**: every low-risk step (run the checks, detect the
state, write the report) has been adjudicated by the Owner by hand. That manual
adjudication adds no safety on steps that only *read, check, and report* — it only
adds latency. This policy lets automation run those steps continuously and reserves
the Owner's attention for the few transitions where being wrong is expensive.

The principle, unchanged from the role design §7: **automation may detect, check,
validate, report, and recommend — it may never *decide* a risky transition.**

## 2. Hard rules (preserved, non-negotiable)

These constrain autopilot at every layer. They restate the role design red lines:

1. Automation MAY detect, check, validate, report, and recommend.
2. Automation MAY NOT merge to `main` without Owner approval.
3. Automation MAY NOT deploy without Owner approval.
4. Automation MAY NOT expand scope without Owner approval.
5. Automation MAY NOT change authority without Owner approval.
6. Automation MAY NOT move from Gate Spec to runtime implementation (S5→S6) without
   Owner approval.
7. Automation MAY NOT override an Operator Review FAIL or an Operator Trial FAIL.

If any rule would be violated to proceed, autopilot **stops and produces an Owner
Decision Request (§6)** — it does not proceed and does not patch.

## 3. The three layers

Autopilot is layered by how reversible the action is. L1 and L2 run without the
Owner; L3 never does.

### L1 — Auto-Execution (no Owner; read / check / report only)

Side-effect-free or strictly local actions. Autopilot MAY, on its own:

- read indexes and authority pointers (boot sequence, ENGINEERING_INDEX, Bucket A);
- **detect the current S-state** from git / `gh` PR status + artifact presence;
- verify the required artifacts for the phase exist at their expected paths;
- run the **forbidden-path scan** (`git diff --name-only` vs the slice's forbidden list);
- run tests (focused suite + the relevant full suite);
- run `git diff --check`;
- run **leakage checks** (raw-enum / backend-field / secret scans on the rendered or
  projected output);
- run **route/render trials** where the Gate Spec explicitly allows a lightweight
  render trial (e.g. PR-1 A区 narration);
- generate all standard reports (Developer / Code Review / Operator Trial / Transition).

L1 produces evidence and reports. It changes no shared state: no merge, no push to a
protected branch, no deploy, no scope change. (Opening a PR branch and pushing a
*feature* branch for review is L1; merging it is L3.)

### L2 — Auto-Recommendation (no Owner; propose, do not act)

From L1 evidence, autopilot MAY:

- produce a structured **Owner Decision Request** (§6);
- recommend **APPROVE / HOLD / BLOCK**;
- name the **exact next allowed transition** (e.g. "S8→S9 merge PR #220");
- name the **retry target** if blocked (e.g. "FAIL → back to S6 Developer").

L2 is advice. The recommendation is an input the Owner reads; it is never a
self-granted approval. A recommendation of APPROVE does not authorize the action.

### L3 — Owner-Required Decisions (autopilot stops and asks)

Autopilot MUST obtain explicit Owner approval, and MUST NOT proceed without it, for:

- **S5→S6** — starting runtime implementation from a Gate Spec;
- **S8→S9** — merge / deploy;
- **scope expansion** (anything beyond the authorized slice's allowed scope);
- **authority change** (what is Bucket A, what a Gate Spec governs);
- **clearing any BLOCKED_\*** state;
- **opening a new implementation slice** (e.g. PR-2 after PR-1) — each slice's S5→S6
  is its own L3 decision, even when the Gate Spec already lists it in §5.

L3 maps exactly to hard rules 2–7. Autopilot reaching an L3 point is the *normal*
end of an autopilot run: it stops, emits the Owner Decision Request, and waits.

## 4. The autopilot run loop

A single autopilot run, given a feature/PR:

```
1. L1  detect S-state · verify artifacts · run checks/tests/scans/trials · build reports
2.     if any check FAILs        → classify BLOCKED_*  → go to 4 (recommend BLOCK)
3.     if the next transition is L1/L2-internal and safe → advance, loop to 1
       else (next transition is L3)                       → go to 4
4. L2  emit Owner Decision Request: state, evidence, risk, recommendation, retry target
5. L3  STOP. Wait for the Owner reply (APPROVE / HOLD / BLOCK). Do not proceed.
```

Autopilot advances *through* L1/L2-internal transitions automatically (e.g. running
Code Review after Developer Report, then Operator Trial after Code Review) and
*stops at* every L3 boundary. It never chains across an L3 boundary on its own.

## 5. Risk classification (how a transition is graded)

| Risk | Meaning | Layer | Owner |
|------|---------|-------|-------|
| **low** | read / check / report; reversible; no shared-state change | L1/L2 | no |
| **medium** | produces a recommendation or a reviewable PR branch; still no merge/deploy | L2 | no |
| **high** | merge, deploy, scope/authority change, runtime-start, unblocking, new slice | L3 | **yes** |

Grading rule (from the role design): *if undoing the step is cheap and it changed no
shared state, it is low/medium; if it merges, deploys, expands scope, changes
authority, or starts runtime, it is high.* When unsure, grade **up**.

## 6. Owner Decision Request — standard template

Autopilot emits this at every L3 boundary (and whenever it must BLOCK):

```md
# Owner Decision Request

## 1. Current State
- feature:
- PR:
- current Harness X state:
- requested transition:

## 2. Evidence
- required reports:
- tests:
- forbidden-path scan:
- leakage scan:
- divergence check:

## 3. Risk Classification
- low / medium / high:
- why:

## 4. Automation Recommendation
- APPROVE / HOLD / BLOCK:
- reason:

## 5. Required Owner Reply
One of:
- APPROVE <transition>
- HOLD <reason>
- BLOCK <blocked_state>
```

The Owner's reply is the only thing that advances an L3 transition. `APPROVE` is
scoped to the named transition only — it does not pre-authorize the next slice or
any later transition.

## 7. Matrix Script worked example

How the policy maps onto the slice that just ran:

| Step | Layer | Owner? | Outcome |
|------|-------|--------|---------|
| Detect PR-1 S-state, verify artifacts, forbidden-path scan, run 1862-test suite, leakage scan, A区 render trial, write Developer Report | L1 | no | PASS, evidence built |
| Code Review (S6→S7) — diff ⊆ Gate Spec, boundary, tests, leakage | L1 | no | READY TO MERGE |
| Operator Trial (S7→S8) — route/render trial of all 7 A区 states | L1 | no | PASS |
| Emit Owner Decision Request: "APPROVE S8→S9 merge PR #220", risk=high | L2 | no | recommendation only |
| **S8→S9 merge PR #220** | **L3** | **yes** | Owner APPROVED → merged; PR-1 reached **S9** |
| #221 docs-only §10 signoff reconciliation | L1 (docs) | merge is L3 | paperwork; merge still Owner-gated |
| **Open PR-2 (a new S5→S6)** | **L3** | **yes** | **CLOSED — not authorized; awaits a separate Owner APPROVE** |

Binding facts of record:

- **#220 PR-1 reached S9** after Developer Report PASS, Code Review PASS, Operator
  Trial PASS, and **Owner merge approval** — the single L3 decision in the run.
- **#221 is docs-only** §10 signoff reconciliation; its own merge is still an L3
  (Owner-gated) action.
- **PR-2 remains CLOSED** until the Owner separately authorizes a new S5→S6
  transition. Under this policy autopilot may *prepare and recommend* PR-2 work
  (L1/L2) but may **not** open or start the slice (L3).

## 8. What autopilot still may NOT do (summary)

- merge to `main` · deploy · expand scope · change authority · start runtime from a
  Gate Spec · clear a BLOCKED_* state · open a new slice (e.g. PR-2) ·
  override an Operator Review FAIL or Operator Trial FAIL.

Each of these is an L3 / hard-rule boundary. Autopilot's correct behavior at every
one of them is identical: **stop, emit an Owner Decision Request, wait.**

## 9. Boundary & authority note

- **Docs-only process proposal.** Adds no automation code and changes no runtime.
- Does **not** modify Matrix Script implementation, `gateway/**`, tests,
  `schemas/**`, `docs/contracts/**`, `artifact_storage.py`, providers, Akool, Hot
  Follow, or Digital Anchor; does **not** start or authorize PR-2.
- Does **not** change Harness X authority rules — it refines *execution cadence*
  within the existing role state machine and red lines.
- Adopting this policy as binding (and wiring any L1 automation later) is an Owner
  decision, not a side effect of merging this doc. Any future automation that
  implements L1/L2 must itself pass through Harness X as its own task.

*Autopilot is not "let the AI decide faster." It is "let the AI do the reading and
checking continuously, and bring the Owner a clean decision exactly when the decision
is the Owner's to make."*
