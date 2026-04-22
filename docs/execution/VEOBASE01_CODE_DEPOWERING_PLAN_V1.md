# VeoBase01 Code De-Powering Plan v1

Date: 2026-04-23
Status: Planning baseline only

## Purpose

This plan defines how oversized files lose rule power.

It does not perform the refactor in this pass. It freezes ownership-removal
direction so future slices do not re-litigate the architecture every time.

## Prioritized Sequence

1. freeze no-growth and rule-removal direction
2. extract cohesive ownership into rule-appropriate modules
3. move contract loading and rule lookup upward into declared loaders
4. leave explicit transitional shells only where import stability requires them

## 1. `gateway/app/routers/tasks.py`

Current problem:

- still concentrates broad orchestration and compatibility pressure
- still has high blast radius because generic task routing and legacy surfaces
  meet in one file

Rule power it still owns:

- residual route-adjacent orchestration decisions
- compatibility path selection
- some task-surface dispatch decisions that can still drift toward business
  rules if new work is added

What power must be removed:

- any new state precedence logic
- any new projection truth assembly
- any new line-specific business branching

What it may still keep:

- HTTP auth/dependency handling
- route registration
- dispatch into explicit services
- thin compatibility wrappers while transitional

Target owner for removed logic:

- line/service modules
- task router presenter services
- explicit contract-loading services

Next change type:

- extraction
- explicit no-growth rule

## 2. `gateway/app/routers/hot_follow_api.py`

Current problem:

- still too close to a line runtime shell with risk of reabsorbing fact or
  presentation rule power

Rule power it still owns:

- route-level collaborator wiring that can turn back into line policy
- residual line-shaped helper flow pressure

What power must be removed:

- fact ownership
- presentation fallback ownership
- any line-rule branching beyond transport concerns

What it may still keep:

- auth
- request parsing
- route-to-service dispatch
- explicit response return points

Target owner for removed logic:

- line-aware service entry layer
- projection/state services
- runtime assembly loaders

Next change type:

- contract loading
- extraction

## 3. `gateway/app/services/task_view_helpers.py`

Current problem:

- gray-zone helper module risk: useful helpers can quietly become shared rule
  owners if left unchecked

Rule power it still owns:

- some compatibility-era helper behavior and legacy convenience assembly paths

What power must be removed:

- any new authoritative publish/workbench truth path
- any new ready-gate or precedence decisions
- any new business fallback logic that belongs in projection/presenter/rule
  contracts

What it may still keep:

- low-level neutral helper functions
- URL / download helpers
- format conversion helpers
- import-stable transitional wrappers where clearly marked

Target owner for removed logic:

- `task_view_projection.py`
- `task_view_presenters.py`
- contract/rule documents and their loaders

Next change type:

- freeze as transitional layer
- explicit no-growth rule

## 4. `gateway/app/services/steps_v1.py`

Current problem:

- large legacy execution file with ongoing temptation to absorb more
  compatibility and line-specific step logic

Rule power it still owns:

- step orchestration residue
- compatibility-era helper reach

What power must be removed:

- any new line-specific onboarding logic
- any new scenario-specific rule handling
- any new cross-line state semantics

What it may still keep:

- existing transitional/legacy compatibility execution paths
- clearly bounded legacy step wrappers until replaced slice by slice

Target owner for removed logic:

- specialized service modules
- future explicit line/runtime assembly and rule loaders

Next change type:

- freeze as transitional layer
- explicit no-growth rule

## File-Level Direction Summary

| File | Direction | Key intent |
| --- | --- | --- |
| `tasks.py` | extraction + no-growth | lose rule power, not just lines |
| `hot_follow_api.py` | extraction + contract loading | become a line adapter shell |
| `task_view_helpers.py` | transitional freeze | do not let helpers become rule owners |
| `steps_v1.py` | transitional freeze | legacy compatibility only, no new line logic |

## Acceptance Signal For Future Refactor Slices

Future slices should be judged by:

- did the file lose rule power
- did ownership move to a clearer layer
- did routers/services stop deciding line rules ad hoc

They should not be judged only by line count reduction.
