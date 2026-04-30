# gateway/app/services/packet/

**Status**: P1 implementation target (envelope + validator + onboarding gate)
**Authority**: Master Plan v1.1 Part IV.1; `factory_packet_envelope_contract_v1.md`; `factory_packet_validator_rules_v1.md`

## Purpose

Host directory for the factory packet runtime: envelope dataclass, validator, and onboarding gate.

Modules:

- `envelope.py` — packet envelope dataclass; mirrors `factory_packet_envelope_contract_v1.md` (in tree)
- `validator.py` — runs R1..R5 + E1..E5 rules; emits `PacketValidationReport` (in tree)
- `onboarding_gate.py` — consumes validator report + reference evidence; emits `OnboardingGateResult` (in tree)
- `entry.py` — dict / JSON-file validation entry helpers (`envelope_from_dict`, `validate_packet_dict`, `validate_packet_path`) (in tree)

## Consumes

- `factory_packet_envelope_contract_v1.md` (E1..E5 structural rules)
- `factory_packet_validator_rules_v1.md` (R1..R5 content rules)
- The six factory-generic contracts (for ref resolution)
- Hot Follow reference evidence (default reference line)

## Does not

- Mutate packets (validator is read-only)
- Write L1 / L2 / L3 / L4 state
- Make runtime orchestration decisions (those belong to capability routing and worker gateway)
- Expose direct entry points to the front-end (consumed by gateway routers, not by UI)

## Schemas

Per-line packet schemas live at `schemas/packets/<line>/packet.schema.json` (Draft 2020-12). Sample instances live at `schemas/packets/<line>/sample/`. See `schemas/packets/README.md` for the layout and onboarding flow.

Hot Follow reference instance: `schemas/packets/hot_follow/sample/reference_packet_v1.json` — used as the green baseline. See `docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`.

## Test surface

Contract tests live at `tests/contracts/packet_validator/` — one positive + one negative per rule, plus the onboarding gate matrix and the Hot Follow reference baseline regression.
