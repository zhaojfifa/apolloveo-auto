# Factory Line Template Design v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-level production-line template that future lines must fit
before runtime onboarding is allowed.

This document is above the frozen Hot Follow sample. It does not implement a
new runtime line.

## What A Production Line Template Is

A production line template is the factory-generic assembly model that defines:

- which contract objects a line must provide
- which four-layer state boundaries the line must obey
- which runtime references are required before execution is allowed
- which surfaces must consume shared authoritative truth

It is the template for line design, not a router/runtime implementation.

## Fixed Across Lines

The following parts stay fixed across lines:

- Layer 0 to Layer 3 architecture order
- four-layer state discipline
- single-owner truth discipline
- ready-gate and delivery truth precedence rules
- shared workbench/delivery-center truth path requirements
- factory contract-object families:
  - input
  - content structure
  - scene plan
  - audio plan
  - language plan
  - delivery

## What Varies By Line

The following parts are line-specific:

- supported source entry modes
- target result type
- language profiles
- audio route policies
- scene-pack relevance
- deliverable profile
- worker profile
- skills bundle
- line-specific ready-gate rules
- line-specific advisory mappings

## Template Layers

### Template Layer A — Factory Contract Objects

Every line must provide or bind:

- `factory_input_contract_v1`
- `factory_content_structure_contract_v1`
- `factory_scene_plan_contract_v1`
- `factory_audio_plan_contract_v1`
- `factory_language_plan_contract_v1`
- `factory_delivery_contract_v1`

### Template Layer B — Line Contract Binding

Every line must provide:

- line identity
- task kind
- target result type
- input contract binding
- deliverable profile binding
- worker/skills/sink bindings
- ready-gate reference
- status policy reference

### Template Layer C — State And Projection Binding

Every line must prove:

- L1/L2/L3/L4 separation
- current-vs-historical output discipline
- ready-gate derivation from authoritative truth
- workbench and delivery-center truth-path alignment

## How Hot Follow Maps Into The Template

Hot Follow already supplies the first accepted sample for:

- a concrete line contract
- four-layer state separation
- current-vs-historical final distinction
- route-aware audio/language logic
- shared workbench/publish truth discipline
- optional scene-pack non-blocking delivery semantics

What Hot Follow still does not authorize:

- copying its runtime directly into a second line
- using its router/service residue as the line-template standard

## What The Next Line Must Provide Before Runtime Onboarding Is Allowed

Before any next line may enter runtime onboarding, it must provide:

- a bound factory input contract
- a bound content structure contract
- a bound scene plan contract
- a bound audio plan contract
- a bound language plan contract
- a bound delivery contract
- a line contract showing task kind, target result, worker/skills/delivery
  bindings
- explicit line-specific route and ready-gate rules
- proof that workbench/delivery surfaces will consume the same authoritative
  projection path
- a completed onboarding packet required by the engineering gate

## Design Rule

The next engineering layer after frozen Hot Follow is contract-object design,
not scenario runtime implementation.

That means:

- create/edit contract objects first
- bind them into line templates second
- permit runtime onboarding only after the gate is explicitly lifted

## Non-Scope

- no new runtime line
- no scenario execution logic
- no multi-role harness
- no reopening Hot Follow internals without a new acceptance regression
