# Factory Language Plan Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that describes source language, target
language, subtitle authority expectations, and language-route obligations for a
production line.

## Ownership

- contract owner: factory contract layer
- runtime consumers: subtitle planners, audio planners, line runtime adapters
- non-owners: helper translation side channels, L4 summaries

## Required Inputs

- normalized factory input object
- content structure object
- requested source/target language scope
- line language capability declaration
- subtitle authority policy

## Allowed Outputs

- language plan object
- authoritative subtitle expectations
- target-language route requirements
- helper-side-channel allowances
- language validation results

## Validation Rules

- authoritative target subtitle ownership must remain single-owned
- helper translation must remain side-channel unless a line contract explicitly
  promotes a result through the authoritative save path
- translation-incomplete and source-copy states must stay visible as contract
  reasons, not collapse into generic missing-state labels

## Relation To Four-Layer State

- L1: subtitle step status is execution-only
- L2: authoritative subtitle artifacts and language evidence are factual truth
- L3: subtitle currentness, route obligations, and dubbing expectations derive
  from the language plan plus L2 facts
- L4: workbench/publish may explain language state but may not replace it

## Relation To Line Runtime

The line runtime binds the generic language plan to line-specific language
profiles, subtitle filenames, provider policies, and authority-save paths.

## Relation To Workbench And Delivery Center

- workbench may surface authoritative subtitle readiness and helper diagnostics
- delivery center may expose subtitle/audio deliverables only from accepted
  authoritative truth

## Factory-Generic Vs Line-Specific

Factory-generic:

- language-plan object shape
- authority-side-channel distinction
- translation state vocabulary
- source/target language slots

Line-specific:

- target-language profiles
- exact authoritative subtitle filenames
- provider-specific language constraints
- route rules driven by language state
