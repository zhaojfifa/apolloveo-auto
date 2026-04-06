# ADR: Task Router Decomposition By Responsibility

- Status: Accepted
- Date: 2026-04-06
- Scope: `tasks.py`, `hot_follow_api.py`, Hot Follow runtime path

## 1. Context

ApolloVeo is a production-factory architecture organized by Production Line, not by model/tool page or one giant transaction script.

Current state:

- `LineRegistry` already exists
- Hot Follow already has a declared line contract and a ready-gate binding path
- compose and status policy have partial service extraction
- but `gateway/app/routers/tasks.py` still behaves like a transaction-script orchestration hub

Current symptoms:

- router files own both transport and business branching
- Hot Follow compatibility logic spills across `tasks.py` and `hot_follow_api.py`
- helper movement risk is often framed as “split the big file” instead of “clarify ownership”
- future Skills Runtime and Worker Gateway have nowhere clean to attach

Measured size is only a symptom, not the architectural problem:

- `gateway/app/routers/tasks.py` is already multi-thousand-line
- `gateway/app/routers/hot_follow_api.py` is also large

The real issue is responsibility mixing.

## 2. Decision

We will decompose `tasks.py` by responsibility, not by file size.

Target layering:

1. contract binding
2. skills runtime boundary
3. worker gateway boundary
4. state / deliverable / asset sink write boundary
5. view assembly / projection

Hot Follow is the first sample line because:

- it is the only line with meaningful contract/runtime/gate material already present
- it already exposes the main failure modes of router-led orchestration
- it is the safest line for proving contract-driven runtime binding without product-scope expansion

## 3. What “By Responsibility” Means

### 3.1 Not This

We are explicitly rejecting a decomposition that only does this:

- take a 3k-line file
- cut it into several smaller files
- keep router, orchestration, truth writes, and presentation mixed together

That kind of split reduces file length but preserves coupling.

### 3.2 Instead, This

We decompose toward stable responsibilities:

- contract binding:
  - resolve line/runtime binding from `task.kind`
- skills runtime:
  - interpretation, routing, quality/compliance, recovery strategy
- worker gateway:
  - execution requests/responses to internal/external/hybrid workers
- state / deliverable / asset sink write path:
  - explicit owners for repo truth, deliverable truth, sink truth
- view assembly:
  - board/workbench/publish projection and response shaping

## 4. Why Hot Follow Is The First Sample Line

Hot Follow already has the minimum ingredients needed for a real line-driven refactor:

- line contract declaration
- line registry binding
- ready gate runtime binding
- status policy
- workbench / publish / compose runtime surfaces

It is therefore the right sample line for proving:

- line contract consumption at runtime
- declarative ready gate consumption
- router/service responsibility reduction

without:

- adding a second production line
- adding a new UI shell
- adding new product scope

## 5. Relation To Jellyfish Review

`docs/reviews/review_jellyfish_importability_for_factory.md` is relevant here for one reason:

- the useful imports are intermediate contracts, service layering, provider/model/settings governance, and candidate-confirmation structures

It is not a reason to import:

- studio shell
- agent product shell
- direct task-status writes from execution layers

This ADR therefore adopts the Jellyfish review in a narrow way:

- absorb responsibility-oriented layering ideas
- reject studio-product truth ownership

## 6. Target Responsibilities After P0

### 6.1 `tasks.py`

Should shrink toward:

- generic task HTTP transport
- generic task orchestration entrypoints
- explicit calls into service/contract/runtime layers

Should stop accumulating:

- Hot Follow-specific workbench state assembly
- Hot Follow-specific view helpers
- lazy import bridges into `hot_follow_api.py`
- direct execution details that belong in services

### 6.2 `hot_follow_api.py`

Should own:

- Hot Follow-specific HTTP endpoints
- workbench / publish hub response assembly
- line-aware route compatibility wrappers where still necessary

Should stop depending on `tasks.py` as a shared helper bag.

### 6.3 Service / Contract Side

Should progressively own:

- compose service execution
- voice/subtitle/artifact helpers
- line binding
- ready gate evaluation
- presenter / view assembly helpers

## 7. Consequences

### 7.1 Immediate

- docs/contracts/ADR/runbook must freeze first
- P0 refactor should move code only when a boundary is clear
- no feature creep
- no new product shell

### 7.2 Positive

- future Worker Gateway can attach cleanly
- future Skills Runtime can attach without becoming truth owner
- line contract can become a real runtime input instead of a ceremonial declaration

### 7.3 Negative / Cost

- transitional wrappers will remain for a while
- some compatibility fields may persist longer than ideal
- P0 will reduce coupling, not fully finish the architecture

## 8. Non-Goals

This ADR does not authorize:

- a full agent platform build
- new business features
- broad UI redesign
- second-line expansion
- renaming the codebase into a new platform shell

## 9. P0 Refactor Direction

The P0 decomposition direction is:

- freeze contracts / SOP / status ownership
- remove router-to-router lazy imports
- extract compose execution into service boundary
- make line contract binding non-ceremonial
- introduce declarative ready-gate hook

This ADR is therefore a responsibility map, not merely a file-shrinking plan.
