# gateway/app/services/providers/

**Status**: P1.5 host reservation (empty until P2 absorption begins)
**Authority**: Master Plan v1.1 Part IV.1 (Provider Supply); Donor Boundary §3.2 / §3.3; Capability Mapping rows A-01..A-05, P-01..P-03

## Purpose

Host directory for provider clients (Akool, Fal, Azure, Gemini, faster-whisper, R2). Each vendor lives in its own subdirectory; clients are bound behind the corresponding capability adapter base interface before they are usable from line packets.

Vendor subdirectories are created at absorption time:

- `akool/` — provider client for Akool (rows P-01, P-02)
- `fal/` — provider client for Fal (created at row E-04..E-07 absorption if Fal client surface is needed)
- `azure/` — Azure Speech / TTS (row A-05)
- `gemini/` — Gemini translation (row A-03)
- `whisper/` — faster-whisper ASR (rows A-01, A-02)
- `r2/` — R2 storage (row P-03)

## Consumes

- `worker_gateway_contract.md`
- `worker_gateway_runtime_contract.md`
- Capability adapter base interfaces (defined under `gateway/app/services/capability/`)

## Does not

- Expose vendors to the front-end (front-end never sees `vendor_id`)
- Implement business decisions (provider clients are pure capability surface)
- Write truth fields (returns values; callers persist truth)
- Import any `swiftcraft.*` package

## Absorption pre-condition

Each vendor subdirectory is created when its capability mapping row moves to `In progress`. Capability adapter base interfaces (under `gateway/app/services/capability/`) MUST land first.
