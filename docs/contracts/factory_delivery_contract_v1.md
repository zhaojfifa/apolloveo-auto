# Factory Delivery Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that describes accepted delivery outputs,
their readiness semantics, and the relationship between primary delivery truth
and optional derivative outputs.

## Ownership

- contract owner: factory contract layer
- runtime consumers: line deliverable profiles, ready-gate evaluation, delivery
  center
- non-owners: workers, presenters, optional derivative generators

## Required Inputs

- line contract reference
- accepted deliverable profile
- current artifact facts
- current-attempt state
- ready-gate output

## Allowed Outputs

- delivery object with primary and secondary deliverables
- current vs historical delivery distinction
- publishability declaration
- optional derivative visibility policy
- delivery validation results

## Validation Rules

- primary delivery truth must dominate optional derivative state
- historical output may be visible but must not satisfy current-ready truth
- optional pack / scene-pack / archive outputs may remain non-blocking when the
  current final delivery is fresh and publishable
- delivery center must consume shared authoritative truth instead of inventing a
  second readiness path

## Relation To Four-Layer State

- L1: publish/pack/scenes steps report execution only
- L2: delivery artifacts are factual existence and freshness truth
- L3: publish-ready and delivery-currentness derive from L2 plus route state
- L4: workbench/delivery center surface delivery truth after ready-gate
  evaluation

## Relation To Line Runtime

Each line binds the generic delivery contract to a line-specific deliverable
profile and readiness policy, but must preserve the primary-vs-optional
distinction.

## Relation To Workbench And Delivery Center

- workbench shows operator-safe delivery state
- delivery center exposes accepted deliverables and historical outputs
- both must consume the same authoritative projection path

## Factory-Generic Vs Line-Specific

Factory-generic:

- delivery object shape
- current vs historical distinction
- primary vs optional derivative precedence
- delivery validation vocabulary

Line-specific:

- exact deliverable kinds
- required vs optional outputs per route
- publish confirmation hooks
- sink/export profiles
