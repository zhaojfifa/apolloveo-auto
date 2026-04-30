# schemas/packets/

**Status**: P1 packet onboarding entry. No schemas live here yet for Matrix Script
or Digital Anchor — placeholders only.

**Authority**:
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`

## Layout

```
schemas/packets/
  README.md                         (this file)
  hot_follow/
    sample/
      reference_packet_v1.json      reference green sample (Hot Follow)
  matrix_script/
    sample/                         (empty — awaiting product handoff)
  digital_anchor/
    sample/                         (empty — awaiting product handoff)
```

Each line directory will eventually contain:

- `packet.schema.json` — JSON Schema Draft 2020-12, `$id` of the form
  `apolloveo://packets/<line_id>/<packet_version>` (R4)
- `sample/*.json` — at least one passing instance the validator runs against (R4)

## Validation Entry Points

The validator can be reached via:

- `gateway.app.services.packet.validator.validate_packet(envelope, ...)`
  for callers that already hold a `PacketEnvelope`
- `gateway.app.services.packet.entry.validate_packet_dict(payload, ...)`
  for callers holding a parsed JSON dict
- `gateway.app.services.packet.entry.validate_packet_path(instance_path, ...)`
  for callers holding a JSON file on disk

All three return a `PacketValidationReport` with rule-level violations / advisories.

## What does NOT live here

- L1 / L2 / L3 / L4 truth fields (forbidden by R5)
- Vendor / model / provider names (forbidden by R3)
- Donor (SwiftCraft) module references (forbidden by envelope contract)
- Runtime task readiness state (owned by the four-layer state model)

## Onboarding flow (read-only)

1. Product author drops `packet.schema.json` + `sample/<name>.json` into the line
   directory.
2. `validate_packet_path("schemas/packets/<line>/sample/<name>.json", schema_path=...)`
   produces a `PacketValidationReport`.
3. `gateway.app.services.packet.onboarding_gate.evaluate_onboarding(envelope, report)`
   produces an `OnboardingGateResult` (passed / blocked / pending).
4. Only `passed` packets at `evidence.ready_state = ready` are eligible for P3
   runtime onboarding (current phase forbids that promotion).
