# gateway/app/services/workers/adapters/

**Status**: P1.5 host reservation (empty until P2 absorption begins)
**Authority**: Master Plan v1.1 Part IV.1 (Worker Adapter Supply); Donor Boundary §3.3 / §3.5

## Purpose

Host directory for worker-side adapters that bind provider clients to capability adapter base interfaces (`UnderstandingAdapter`, `SubtitlesAdapter`, `DubAdapter`, `VideoGenAdapter`, `AvatarAdapter`, `PackAdapter`, etc.).

Worker adapters are the bridge between provider clients (`gateway/app/services/providers/<vendor>/`) and the worker execution envelope.

## Consumes

- `worker_gateway_contract.md`
- `worker_gateway_runtime_contract.md`
- Capability adapter base interfaces (`gateway/app/services/capability/`)
- Provider clients (`gateway/app/services/providers/<vendor>/`)

## Does not

- Carry product judgment — adapters execute the selected tool chain only
- Write truth fields directly — returns adapter results; callers persist truth
- Import any `swiftcraft.*` package
- Bypass capability registry / routing (vendors are selected by routing policy, not by adapter call sites)

## Absorption pre-condition

Each vendor adapter lands only after the capability adapter base interface for its capability kind has been merged. Capability mapping row id is cited in every absorption PR.
