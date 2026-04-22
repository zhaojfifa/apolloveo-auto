# VeoBase01 Unified Glossary

## Purpose

This glossary freezes shared terms used by VeoBase01 preparation docs, schema
examples, and future new-line onboarding packets.

These definitions are authoritative for VeoBase01 documentation unless a higher
priority contract or architecture doc explicitly supersedes them.

## Frozen Terms

| Term | Meaning |
| --- | --- |
| Production Line | A business execution line operating under one explicit line contract. |
| Line Contract | The contract that identifies a line, its refs, and its policy entrypoints. |
| Line Job | A task interpreted through one specific production line contract. |
| Production Agent | Runtime assembly of line contract, SOP profile, skills bundle, worker profile, deliverable profile, and asset sink profile for a line job. |
| SOP Profile | The ordered operating procedure, retry expectations, and operator checkpoints for a line. |
| Skills Bundle | A line-scoped advisory and routing bundle that reads facts and returns strategy output only. |
| Skills Bundle Boundary | The frozen rule that a skills bundle may advise but may not write truth. |
| Worker Profile | Execution-provider and capability policy for the workers used by a line. |
| Deliverable Profile | The declaration of primary, secondary, and optional outputs and their acceptance rules. |
| Asset Sink Profile | The downstream sink policy that operates only on accepted deliverable truth. |
| Line Runtime Refs | Read-only runtime metadata proving which contract refs were resolved for a line. |
| Line Job State Machine | The shared lifecycle model for a task once it is interpreted as a line job. |
| Ready Gate | L4 derived readiness for compose/publish and related blocking reasons. |
| Multi-Role Harness | A future validation harness where multiple roles inspect or act on the same shared line/job contracts without creating duplicate truth writers. |
| Onboarding Packet | The required preparation package for a future line before implementation may start. |
| Onboarding Gate | The explicit decision that a future line remains blocked or may proceed to a later implementation PR. |

## Vocabulary Rules

1. `task` remains the persisted runtime record in the current system.
2. `line job` is the contract interpretation of that task, not a second stored
   record type.
3. `skills bundle` and `worker profile` are not synonyms.
4. `deliverable profile` and `asset sink profile` are not synonyms.
5. `ready gate` is derived readiness, not persisted business truth.
6. `completed` in a line-job state machine must still respect primary
   deliverable acceptance and shared gate semantics.

## Forbidden Synonyms

Do not use the following phrases as replacement authorities in VeoBase01 docs:

- "agent state" when the intended meaning is line job or ready gate
- "worker result truth" when the intended meaning is accepted deliverable truth
- "sink completion" when the intended meaning is primary deliverable completion
- "skills decision" when the intended meaning is ready gate or status policy
