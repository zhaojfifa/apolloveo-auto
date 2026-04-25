# gateway/app/services/capability/

**Status**: P1 implementation target (registry + adapter base + routing)
**Authority**: Master Plan v1.1 Part IV.1; v1.0 §6 four-segment supply (Tool Registry → Capability Adapter → Routing Policy → Worker Execution Envelope)

## Purpose

Host directory for the capability supply mid-tier:

- `registry.py` — Tool Registry; persists `tool_id / adapter / capabilities[] / config_ref / policy / quota / status / visible_roles / owner`
- `routing.py` — Routing Policy; selects vendor by line packet's `capability_plan` (kinds only); resolves fallback / quota / risk
- `adapters/` — capability adapter **base interfaces** (`AdapterBase`, `UnderstandingAdapter`, `SubtitlesAdapter`, `DubAdapter`, `VideoGenAdapter`, `AvatarAdapter`, `FaceSwapAdapter`, `PostProductionAdapter`, `PackAdapter`)

Vendor implementations of these interfaces live in `gateway/app/services/workers/adapters/<vendor>/`; provider clients live in `gateway/app/services/providers/<vendor>/`. This directory only hosts the contracts and the registry / routing implementations.

## Consumes

- `worker_gateway_contract.md`, `worker_gateway_runtime_contract.md`
- `factory_packet_envelope_contract_v1.md` (`capability_plan[]` is the routing input)
- Closed capability kind set defined by `factory_packet_validator_rules_v1.md` R3

## Does not

- Pin vendors at the packet level (R3 forbids it)
- Expose `vendor_id` to the front-end
- Carry business judgment — routing follows capability plan, not business decisions
- Become a truth source — registry and routing are infrastructure, not state

## Absorption pre-condition

Adapter base interfaces (`adapters/`) land first in P1; vendor implementations and provider clients follow in P2 absorption waves.
