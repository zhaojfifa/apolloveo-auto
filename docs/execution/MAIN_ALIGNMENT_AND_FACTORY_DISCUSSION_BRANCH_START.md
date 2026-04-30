# Main Alignment And Factory Discussion Branch Start

Date: 2026-04-24
Status: Completed

## Purpose

Record the alignment of `main` to the accepted `VeoBase01` baseline and the
creation of the fresh discussion branch for factory-level contract discussion.

## Baseline Preservation

- accepted freeze tag: `HotFollow-ContractDriven-Baseline-Freeze01`
- tag status: unchanged
- tag target remains:
  `2bfef16053c5f97b85b044de3a28a367eca26fbc`

## Main Alignment

- source integration branch: `VeoBase01`
- alignment method: fast-forward only
- `main` now includes the accepted `VeoBase01` baseline

## Active Discussion Branch

- branch name: `factory-contract-objects-discussion-v1`
- base branch: updated `main`
- scope: factory-level contract discussion only

## Current Allowed Scope

Allowed:

- discussion and refinement around:
  - `docs/contracts/factory_input_contract_v1.md`
  - `docs/contracts/factory_content_structure_contract_v1.md`
  - `docs/contracts/factory_scene_plan_contract_v1.md`
  - `docs/contracts/factory_audio_plan_contract_v1.md`
  - `docs/contracts/factory_language_plan_contract_v1.md`
  - `docs/contracts/factory_delivery_contract_v1.md`
  - `docs/architecture/factory_line_template_design_v1.md`

Blocked:

- Hot Follow internal runtime reopening without a new acceptance regression
- new line runtime onboarding
- scenario runtime implementation

## Discussion Objective

The next line must provide a full contract-object packet before runtime
onboarding is allowed. Discussion on this branch should stay at that contract
packet and line-template level.
