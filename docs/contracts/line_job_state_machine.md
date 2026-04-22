# Line Job State Machine

## Purpose

This document freezes the shared lifecycle for a task interpreted through a
production line contract.

The state machine is preparation infrastructure for future new-line onboarding
and multi-role harness work. It does not add a second production line and does
not replace existing Hot Follow runtime behavior.

## Ownership Rule

The line-job state machine is a documentation and harness model layered on top
of the VeoBase01 four-layer contract.

- L1 still owns operational step status.
- L2 still owns accepted artifact truth.
- L3 still owns currentness and stale/fresh interpretation.
- L4 still owns ready gate, operator summary, advisory, and presentation.

The states below summarize lifecycle milestones. They do not create a new truth
layer and must not be written back as a replacement for L1, L2, L3, or L4.

## Frozen States

| State | Meaning | Entry Condition | Exit Condition |
| --- | --- | --- | --- |
| `submitted` | A task exists but no production line has been bound yet. | task is created and accepted by the system | line binding succeeds or the task is cancelled |
| `line_bound` | The task is bound to one line contract and its runtime refs are known. | line registry and required refs resolve | inputs are accepted for execution, or binding fails |
| `input_ready` | Required inputs are present and accepted for this line. | line-specific input truth is accepted in L2 | execution starts, or inputs are invalidated |
| `execution_active` | One or more line steps are actively running or retrying. | an owning controller/service advances L1 step execution | execution reaches review blocking, terminal failure, or completion conditions |
| `awaiting_review` | Execution produced enough accepted outputs to require operator or policy review before publish. | L2/L3 facts exist but L4 still blocks publish | blocking reasons clear, publish becomes ready, or the task fails/cancels |
| `publish_blocked` | The line has accepted outputs but L4 still denies publish. | ready gate reports publish blockers | blockers clear, or the task fails/cancels |
| `publish_ready` | Shared gates allow publish for the line job. | ready gate reports publish-ready using L2/L3 facts | publish completes, or freshness invalidates readiness |
| `completed` | The line's primary deliverable is accepted and the job reaches its terminal success state. | accepted primary deliverable and terminal completion policy are satisfied | terminal |
| `failed` | The line reaches a terminal failure state. | owning controller/service records terminal failure | terminal |
| `cancelled` | The line is intentionally stopped before terminal success. | owning controller/service records cancellation | terminal |

## Allowed Transitions

```text
submitted -> line_bound
submitted -> cancelled

line_bound -> input_ready
line_bound -> failed
line_bound -> cancelled

input_ready -> execution_active
input_ready -> failed
input_ready -> cancelled

execution_active -> awaiting_review
execution_active -> publish_blocked
execution_active -> publish_ready
execution_active -> completed
execution_active -> failed
execution_active -> cancelled

awaiting_review -> publish_blocked
awaiting_review -> publish_ready
awaiting_review -> failed
awaiting_review -> cancelled

publish_blocked -> execution_active
publish_blocked -> publish_ready
publish_blocked -> failed
publish_blocked -> cancelled

publish_ready -> completed
publish_ready -> publish_blocked
publish_ready -> failed
publish_ready -> cancelled
```

## Transition Constraints

1. `line_bound` requires exactly one active line contract resolution.
2. `input_ready` requires accepted input truth, not only a UI declaration.
3. `publish_ready` must come from L4 ready-gate derivation, never from a
   display label.
4. `completed` requires the line's primary deliverable acceptance policy to be
   satisfied.
5. `awaiting_review` and `publish_blocked` may coexist conceptually in the
   workbench, but the state machine must use the stricter blocker when a single
   harness state is needed.
6. A terminal state must not transition back to a non-terminal state without a
   new task/job identity or a separately documented recovery contract.

## Mapping To Existing VeoBase01 Concepts

| State Machine Concern | Existing VeoBase01 Authority |
| --- | --- |
| line binding | `line.runtime_refs` and line registry binding |
| input acceptance | line-owned L2 input artifacts and refs |
| execution activity | L1 step status and controller/service orchestration |
| review/publish blockers | L4 ready gate and operator summary |
| current output freshness | L3 current attempt / stale-fresh derivation |
| terminal completion | deliverable profile plus line completion policy |

## Harness Preconditions

Any future multi-role harness that uses this state machine must prove:

1. every asserted state is derivable from existing L1-L4 evidence
2. role handoffs do not create duplicate truth writers
3. readiness assertions use L4 gates instead of UI-only summaries
4. completion assertions use primary deliverable acceptance, not optional output
   presence
5. a blocked second line cannot skip directly from `submitted` to
   `execution_active` without a reviewed onboarding packet

## Current Gate

For VeoBase01 PR-5, this state machine is frozen as a preparation reference
only. A second line remains blocked until a later implementation PR explicitly
passes the onboarding gate described in
`docs/contracts/new_line_onboarding_template.md`.
