# Factory Scene Plan Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that turns accepted content structure into a
scene-level execution or composition plan without directly implementing scene
runtime.

## Ownership

- contract owner: factory contract layer
- runtime consumers: line planners, compose preparation, optional scene-pack
  generators
- non-owners: router-local composition fallbacks

## Required Inputs

- normalized factory input object
- content structure object
- line composition capability declaration
- operator overrides that are contract-legal

## Allowed Outputs

- ordered scene-plan object
- scene-level timing and grouping references
- scene execution prerequisites
- optional scene-pack expectations
- scene-plan validation results

## Validation Rules

- scene plan must distinguish required execution scenes from optional scene-pack
  derivatives
- scene-plan absence must not by itself demote a line whose final delivery path
  does not require scene packs
- scene-level references must remain traceable to structure/input evidence

## Relation To Four-Layer State

- L1: scene-related steps may report execution state only
- L2: scene-plan object and scene-pack artifact evidence are factual outputs
- L3: scene-plan readiness may affect compose planning where relevant
- L4: scene-pack pending remains advisory when final-ready truth is already met

## Relation To Line Runtime

The line runtime chooses whether scene planning is mandatory, optional, or
unsupported, but must consume one stable scene-plan object family.

## Relation To Workbench And Delivery Center

- workbench may expose plan summary and scene-pack advisory
- delivery center may expose scene derivatives, but they must remain secondary
  to final delivery truth

## Factory-Generic Vs Line-Specific

Factory-generic:

- scene-plan object shape
- scene grouping/timing vocabulary
- optional-vs-required derivative distinction

Line-specific:

- whether scene packs exist
- how scene planning affects composition
- line-specific scene validation thresholds
