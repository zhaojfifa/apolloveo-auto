# Skills Bundle Boundary

## Purpose

This document freezes the minimum boundary for a line-scoped skills bundle used
by VeoBase01 runtime preparation.

It complements `docs/contracts/skills_runtime_contract.md` by defining the
minimum bundle surface that future new-line onboarding and multi-role harness
work may rely on.

## Frozen Boundary

A skills bundle is the combination of:

- one line-scoped bundle path
- one ordered set of skill stages
- one read-only input surface
- one strategy-only output surface
- one deterministic fallback policy

The bundle is advisory and routing infrastructure only. It does not become a
truth layer.

## Minimum Bundle Shape

```text
skills/<line_id>/
  input_skill.py
  routing_skill.py
  quality_skill.py
  recovery_skill.py
  config/
    defaults.yaml
```

Additional modules are allowed later, but this minimum shape is the shared
bundle boundary for onboarding preparation.

## Read-Only Inputs

Each stage may read:

- line binding metadata
- line runtime refs
- task snapshot
- accepted artifact facts
- derived currentness inputs
- operator request context

Each stage may not write:

- repository truth
- deliverable truth
- ready-gate truth
- asset sink truth
- presenter-only truth shortcuts

## Allowed Outputs

Skills bundle outputs must stay inside these classes:

- normalized interpretation
- routing recommendation
- provider preference
- quality note
- compliance note
- recovery recommendation
- operator advisory
- execution intent proposal

The output may explain, rank, propose, or warn. It may not persist canonical
truth or finalize business state.

## Bundle Boundary Checklist

A line-scoped skills bundle is inside the frozen boundary only if:

1. the bundle path is line-scoped and explicit
2. the stage order is explicit
3. all inputs are read-only
4. all outputs are strategy-only
5. fallback behavior is deterministic when the bundle is missing or fails
6. accepted deliverable and ready-gate truth stay outside the bundle

## Multi-Role Harness Preconditions

Any future harness using multiple roles around a skills bundle must prove:

1. bundle readers and bundle executors use the same glossary terms
2. a role can inspect bundle output without becoming a truth writer
3. a role handoff cannot reinterpret bundle output as accepted artifact truth
4. fallback behavior is asserted when skills are unavailable
5. line-specific roles still consume the same shared line-job state machine

## Second-Line Gate

This boundary doc does not authorize a second line.

A future line may reference this boundary only after:

1. a concrete onboarding packet is completed with
   `docs/contracts/new_line_onboarding_template.md`
2. worker, deliverable, and asset sink profile docs are present
3. the shared line-job state machine is adopted
4. Hot Follow remains the stable baseline line
