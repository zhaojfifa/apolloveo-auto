# Factory Content Structure Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that describes how source content is
understood structurally before scene planning, subtitle planning, audio
planning, and delivery assembly.

## Ownership

- contract owner: factory contract layer
- runtime consumers: parse layer, line structure adapters, scene/audio planners
- non-owners: workbench labels, publish-only helpers

## Required Inputs

- normalized factory input object
- source media structural probes
- speech / silence / text-density evidence
- content mode hints
- line capability declaration

## Allowed Outputs

- content structure summary
- structural segment references
- speech/text/media mode classification
- structure-level risk flags
- planner input bundle for scene/audio/language contracts

## Validation Rules

- structure object must separate probe evidence from interpretation
- helper/provider-side evidence may support structure but may not replace
  authoritative line truth by itself
- structure contract must be stable across URL and local ingest classes
- ambiguous structure cases must remain diagnosable, not silently collapsed

## Relation To Four-Layer State

- L1: may consume parse-step completion, but does not define parse success alone
- L2: records factual source-content structure evidence
- L3: may inform route feasibility and planner readiness
- L4: may be summarized for operator review and advisory only

## Relation To Line Runtime

Each line maps the factory content structure object into line-specific state and
route policies without redefining the generic structure vocabulary.

## Relation To Workbench And Delivery Center

- workbench may show structure summaries and risk flags
- delivery center must never use structure summaries as publish readiness

## Factory-Generic Vs Line-Specific

Factory-generic:

- structure vocabulary
- speech/text/silence evidence shape
- segment reference conventions
- risk-flag categories

Line-specific:

- how structure affects route choice
- whether subtitle-led or voice-led modes are legal
- which structural gaps are blocking vs advisory
