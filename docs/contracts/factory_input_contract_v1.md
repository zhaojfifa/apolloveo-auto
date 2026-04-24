# Factory Input Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that declares what raw business inputs a
production line may accept before line-specific routing and execution begin.

## Ownership

- contract owner: factory contract layer
- runtime consumers: line registration, task creation, input normalization
- non-owners: routers, workbench presenters, delivery surfaces

## Required Inputs

- line identity
- source entry mode
- source asset references
- source language hints
- operator-supplied business metadata
- ingest-time policy flags

## Allowed Outputs

- normalized input object for line runtime
- input validation result
- input completeness flags
- initial L2 input artifact facts
- references to line-specific adapters

## Validation Rules

- input object must declare one authoritative source entry mode
- input validation must reject shape ambiguity before runtime orchestration
- input normalization may enrich metadata but may not invent downstream truth
- input contract must distinguish factory-generic fields from line-specific
  fields explicitly

## Relation To Four-Layer State

- L1: does not own step execution
- L2: establishes input-side artifact facts and ingest references
- L3: may provide preconditions, but not current-attempt truth
- L4: may be summarized for workbench intake views only after L2 exists

## Relation To Line Runtime

The line runtime consumes the normalized input object and binds it to line
contracts, route rules, and worker/execution policies.

## Relation To Workbench And Delivery Center

- workbench consumes input summary and ingest completeness
- delivery center must not treat raw input acceptance as deliverable truth

## Factory-Generic Vs Line-Specific

Factory-generic:

- source entry mode taxonomy
- source asset reference shape
- language-hint slots
- operator metadata envelope
- validation/error surface shape

Line-specific:

- supported source modes
- source-language restrictions
- line-only ingest policy flags
- line-specific default adapters
