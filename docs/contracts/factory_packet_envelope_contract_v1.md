# Factory Packet Envelope Contract v1

Date: 2026-04-25
Status: Frozen for P1 (validator and onboarding gate prerequisite)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P1, Master Plan v1.0 §3 (carried forward)

## Purpose

Define the factory-generic envelope that wraps a line packet for validation and onboarding. The envelope is the binding object: it declares which line a packet belongs to, which factory-generic contracts it references, which line-specific objects it adds, which reference evidence backs its readiness, and a single packet-level ready state.

The envelope is the only object the factory packet validator and the onboarding gate read at the top level. Line-specific contracts are reachable through the envelope's `line_specific_refs`; factory-generic contracts are reachable through `generic_refs`.

## Ownership

- Contract owner: factory contract layer
- Runtime consumers: packet validator, onboarding gate, line registration, line conformance checks
- Non-owners: routers, workbench presenters, delivery surfaces, front-end, donor (SwiftCraft) modules

## Distinction from the six factory-generic objects

The envelope is **not** a seventh generic object. The six generic objects (`factory_input`, `factory_content_structure`, `factory_scene_plan`, `factory_audio_plan`, `factory_language_plan`, `factory_delivery`) are content contracts. The envelope is a packaging contract: it does not declare content, only the structure that binds content references together for a specific line.

## Required Inputs

The envelope object declares:

- `line_id` — stable identifier of the production line (e.g. `hot_follow`, `matrix_script`, `digital_anchor`)
- `packet_version` — semantic version of this packet (e.g. `v1`, `v1.1`); independent from the rule set version
- `generic_refs[]` — list of references to factory-generic contracts; each entry declares:
  - `ref_id` — local id used by line-specific objects to point at this ref
  - `path` — repo-relative path to the contract file (`docs/contracts/factory_*_contract_v1.md`)
  - `version` — declared version of the referenced contract
- `line_specific_refs[]` — list of references to line-specific contracts; each entry declares:
  - `ref_id`
  - `path` (typically `docs/contracts/<line>/*_contract_v1.md`)
  - `version`
  - `binds_to[]` — list of `generic_ref` ids this line-specific object extends or binds to (may be empty)
- `binding` — line-binding object declaring:
  - `worker_profile_ref` — id of the worker profile bound to this line (resolved by worker gateway)
  - `deliverable_profile_ref` — id of the deliverable profile bound to this line
  - `asset_sink_profile_ref` — id of the asset sink profile bound to this line
  - `capability_plan[]` — per-capability declarations (kinds only; vendors forbidden by `factory_packet_validator_rules_v1` R3)
- `evidence` — onboarding evidence object declaring:
  - `reference_line` — the reference line whose truth discipline backs this packet (default: `hot_follow`)
  - `reference_evidence_path` — repo-relative path to the reference evidence document or test artifact
  - `validator_report_path` — repo-relative path to the most recent `PacketValidationReport`
  - `ready_state` — packet-level onboarding readiness, one of: `draft`, `validating`, `ready`, `gated`, `frozen`
- `metadata` — non-truth descriptive fields (`created_at`, `created_by`, `notes`); MUST NOT carry runtime status

## Allowed Outputs

The envelope, when consumed by the validator and onboarding gate, yields:

- `PacketValidationReport` (defined by `factory_packet_validator_rules_v1`)
- `OnboardingGateResult` carrying `gate_status ∈ {pending, passed, blocked}`, `blocked_reasons[]`, `evidence_links[]`
- The envelope itself is unchanged by these operations; both report and gate result live outside the envelope

## Validation Rules

The envelope is validated by `factory_packet_validator_rules_v1` rules R1–R5; this contract adds five envelope-specific structural requirements:

### E1 · line_id is stable and unique

`line_id` MUST be a registered line identifier in the production line registry. Two packets MAY NOT share `line_id` unless they differ in `packet_version`.

### E2 · generic_refs paths are factory-generic only

Every `generic_refs[].path` MUST start with `docs/contracts/factory_` and end with `_contract_v1.md`. Paths to line-specific contracts in `generic_refs` are a structural error.

### E3 · line_specific_refs binds_to references resolve

Every entry in `line_specific_refs[].binds_to[]` MUST reference an existing `ref_id` declared in `generic_refs`. Dangling `binds_to` ids are a structural error.

### E4 · ready_state is the only permitted readiness field

`evidence.ready_state` is the single readiness field allowed in a packet. It refers to packet-level onboarding readiness only; it MUST NOT be conflated with runtime task readiness, which is derived by the factory's four-layer state model from artifact facts. `factory_packet_validator_rules_v1` R5 enforces this exception.

Permitted transitions:

```
draft  →  validating  →  ready  →  frozen
                    ↘
                      gated  (validator failures or onboarding gate blocked)
```

`gated` returns to `validating` after fixes; `frozen` is terminal for the packet version (a new version restarts at `draft`).

### E5 · capability_plan kind closure

`binding.capability_plan[].kind` MUST be drawn from the closed kind set defined in `factory_packet_validator_rules_v1` R3. Vendor pins are forbidden at envelope level and at every nested level.

## Forbidden in the envelope

- Any field shaped as L1 / L2 / L3 / L4 truth (`status`, `phase`, `done`, `current_attempt`, etc.) — see `factory_packet_validator_rules_v1` R5
- Any field naming a vendor, model, provider, or engine — see `factory_packet_validator_rules_v1` R3
- Any direct embed of a generic contract's full record shape inside `line_specific_refs` — `binds_to` is the only legal way to extend a generic contract
- Any reference to a donor (SwiftCraft) module path — donor code is reached through capability adapters, never through the envelope

## Schema

The envelope JSON Schema lives at `schemas/packet/envelope.schema.json` (Draft 2020-12). It MUST validate every line packet's envelope object before the validator runs the R1–R5 content rules. Sample instances live under `schemas/packet/sample/`.

## Lifecycle

1. Product author drafts a line packet conforming to this envelope (see product handoff for Matrix Script and Digital Anchor)
2. Validator runs envelope structural checks (E1–E5) and content rules (R1–R5)
3. Onboarding gate consumes the validator report and reference evidence
4. Gate emits `passed`, `blocked`, or `pending`
5. Only `passed` packets at `evidence.ready_state = ready` are eligible for runtime onboarding (P3)
6. Runtime onboarding promotes the packet to `frozen`; subsequent edits require a new `packet_version`

## References

- `docs/contracts/factory_packet_validator_rules_v1.md` (companion rule set)
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Q6, Part III, Part V, Part VII
