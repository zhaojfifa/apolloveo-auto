# Factory Audio Plan Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that describes the intended audio strategy
for a production line before current-attempt execution resolves audio truth.

## Ownership

- contract owner: factory contract layer
- runtime consumers: line route selection, dub/compose planners, worker
  bindings
- non-owners: presenters, publish-only heuristics

## Required Inputs

- normalized factory input object
- content structure object
- language plan object
- source-audio policy
- line audio capability declaration

## Allowed Outputs

- audio plan object
- intended audio route
- required and optional audio artifacts
- no-TTS / preserve-source / BGM legality declaration
- audio validation results

## Validation Rules

- audio plan must declare intended route separately from current audio outcome
- audio plan must distinguish terminal no-TTS routes from retriable TTS failure
  shapes
- source-audio preservation may influence route legality but must not silently
  replace line-specific subtitle/audio requirements

## Relation To Four-Layer State

- L1: dub step reports execution only
- L2: current audio artifact facts remain separate from the audio plan
- L3: audio readiness and route legality derive from L2 facts plus the audio
  plan
- L4: workbench/publish may summarize the active audio route but may not invent
  it

## Relation To Line Runtime

The line runtime binds the generic audio plan to line-specific providers,
voices, preserve-source rules, and composition allowances.

## Relation To Workbench And Delivery Center

- workbench may display route intent, current route, and operator guidance
- delivery center may expose accepted audio artifacts only after L2/L3 truth is
  satisfied

## Factory-Generic Vs Line-Specific

Factory-generic:

- route vocabulary
- required/optional artifact shape
- current-route vs intended-route distinction
- validation categories

Line-specific:

- provider sets
- voice options
- exact no-TTS allowances
- route precedence and blocking rules
