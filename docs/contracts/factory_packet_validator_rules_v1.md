# Factory Packet Validator Rules v1

Date: 2026-04-25
Status: Frozen for P1 (validator implementation prerequisite)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q6 / Part V item 2 / Part VII (P1 evidence row)

## Purpose

Define the rule set the factory packet validator MUST enforce on any line packet (Hot Follow, Matrix Script, Digital Anchor, future lines) before the line is permitted to enter runtime onboarding.

This document is consumed by:

- `gateway/app/services/packet/validator.py` (the implementation)
- `gateway/app/services/packet/onboarding_gate.py` (consumes validator output)
- Product authors of line packet schemas (Matrix Script, Digital Anchor handoff deliverables)

This document is NOT:

- a wireframe or product spec
- a runtime orchestration spec
- a substitute for line-specific contracts

## Ownership

- Contract owner: factory contract layer
- Runtime consumers: packet validator, onboarding gate, line registration, CI contract tests
- Non-owners: routers, workbench presenters, delivery surfaces, front-end

## Required Inputs

The validator accepts:

- a packet object conforming to `factory_packet_envelope_contract_v1`
- the working `docs/contracts/` directory (for `generic_refs` resolution)
- the registered capability kind set (closed list, see Rule 3)
- the line's reference evidence pointer (Hot Follow baseline by default)

## Allowed Outputs

The validator emits a `PacketValidationReport` with:

- `ok: bool` — true only if zero violations
- `missing: list[FieldRef]` — required fields absent
- `violations: list[Violation]` — rule breaches (each carries rule id, field path, reason)
- `advisories: list[Advisory]` — non-blocking observations (e.g. unused optional generic ref)
- `rule_versions: dict` — rule id → version string for audit replay

The validator MUST NOT:

- mutate the packet
- write any L1 / L2 / L3 / L4 state
- write to delivery contract output
- emit `status` / `ready` / `done` style fields

## Validation Rules

The validator enforces five rules. Each rule has a stable id (`R1`–`R5`); rule ids appear in violations and in CI test names.

### R1 · generic_refs must resolve to existing factory contracts

For every entry in `packet.generic_refs[]`:

- The referenced path MUST start with `docs/contracts/factory_` and end with `_contract_v1.md`
- The file MUST exist at the cited path
- The file's first heading MUST match the contract name declared in the ref entry (path-name-to-heading consistency)
- Versions MUST match: a ref to `factory_scene_plan_contract_v1.md` MUST NOT be re-pointed to a different version without re-versioning the packet

Violation form: `R1.<path-not-found | heading-mismatch | version-skew>`

### R2 · No generic-shape duplication in line-specific objects

A line packet MUST NOT redeclare any field shape already owned by a contract referenced via `generic_refs`. Specifically:

- A line-specific object MAY declare a binding via `extends: <generic_ref_id>` or `binds_to: <generic_ref_id>` and add increments
- A line-specific object MUST NOT redeclare full record shapes for: `factory_input`, `factory_content_structure`, `factory_scene_plan`, `factory_audio_plan`, `factory_language_plan`, `factory_delivery`
- Detection: for each line-specific object that names itself with a generic-shape suffix (e.g. `*_scene_plan`, `*_delivery_pack`), the validator inspects its fields; if a majority overlap with the corresponding generic contract's required fields, it is treated as a duplication violation unless `binds_to` is declared and only delta fields are present

Violation form: `R2.<duplicate-shape | missing-binds_to | non-delta-fields-in-binding>`

### R3 · capability_plan elements are capability kinds, not vendors

For every entry in `packet.capability_plan[]`:

- The `kind` field MUST be one of the closed set:
  `understanding`, `subtitles`, `dub`, `video_gen`, `avatar`, `face_swap`, `post_production`, `pack`, `variation`, `speaker`, `lip_sync`
- The entry MUST NOT contain `vendor_id`, `model_id`, `provider`, `provider_id`, `engine_id`, or any string field whose value matches a known vendor name (Akool, Fal, Kling, WAN, Azure, Gemini, OpenAI, Whisper, etc.)
- The entry MAY contain `mode`, `inputs`, `outputs`, `quality_hint`, `language_hint`, but MUST NOT pin a specific provider

Violation form: `R3.<unknown-kind | vendor-leak | provider-pin>`

The closed kind set is owned by this document; adding a kind requires a document amendment. Vendor selection is performed by `capability_routing_policy_v1` at runtime, not by the packet.

### R4 · Schema must be loadable by JSON Schema Draft 2020-12

The packet schema (`schemas/packets/<line>/packet.schema.json`) MUST:

- Declare `$schema` as `https://json-schema.org/draft/2020-12/schema`
- Be loadable by a Draft-2020-12 validator without parse errors
- Validate cleanly against at least one sample instance shipped alongside the schema (`schemas/packets/<line>/sample/*.json`)
- Use `$id` to declare a stable identifier; `$id` MUST include the line id and the version (e.g. `apolloveo://packets/matrix_script/v1`)

Violation form: `R4.<draft-mismatch | parse-error | sample-fails | missing-id>`

### R5 · No truth-shape state fields in packet

A packet MUST NOT declare any field whose name matches the closed set of state field names:

- `status`, `state`, `phase`, `stage_status`
- `ready`, `is_ready`, `ready_state`, `ready_gate`
- `done`, `completed`, `finished`
- `current_attempt`, `attempt_state`
- `step_status`, `pipeline_status`
- `publishable`, `is_publishable`
- `delivery_ready`, `final_ready`

Truth fields belong to the four-layer state model and are derived at runtime from artifact facts and current attempt. Packet only declares what is needed; the factory derives readiness.

Exception: `packet.evidence.ready_state` (defined by `factory_packet_envelope_contract_v1`) is the single permitted readiness reference; it is structurally distinct from the forbidden field set above and refers to packet-level onboarding readiness, not runtime task readiness.

Violation form: `R5.<forbidden-field-name | masked-state-field>`

## Rule precedence

When multiple rules fire on the same field, the validator reports all of them; precedence does not collapse violations. CI gates fail on any violation regardless of rule.

## Versioning

- Rule set version: `v1`
- Closed sets (capability kinds in R3, forbidden field names in R5) are part of the rule version
- Adding or removing a kind / forbidden name requires bumping to `v2` and amending this document
- Validator MUST stamp the rule version it ran with into `PacketValidationReport.rule_versions`

## Test surface

Each rule MUST have at least one positive and one negative contract test under `tests/contracts/packet_validator/`:

- `test_r1_generic_refs.py`
- `test_r2_no_duplication.py`
- `test_r3_capability_kinds.py`
- `test_r4_schema_loadable.py`
- `test_r5_no_state_fields.py`

These tests are part of the P0 Guardrail Test Suite extension required by Master Plan v1.1 Part VII (P1 evidence).

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Q6, Part V, Part VII
