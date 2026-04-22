# Workbench Hub Response Contract

## Purpose

This contract freezes the typed response boundary for Hot Follow workbench hub responses during VeoBase01 reconstruction.

The workbench hub is a presenter boundary. It may aggregate state, but it must not invent business truth.

Runtime typed model:

- `gateway/app/services/contracts/hot_follow_workbench.py::HotFollowWorkbenchResponse`

Validation rule:

- the current wire payload is validated against the typed model
- the validator returns the original dict unchanged
- compatibility fields remain allowed during reconstruction

## Ownership Rule

Workbench hub response fields must be traceable to one of the four state layers:

- L1 pipeline step status
- L2 artifact facts
- L3 current attempt / runtime resolution
- L4 ready gate / presenter / advisory

Presenter fields can rename or group values for the UI, but cannot override source truth.

## Required Top-Level Sections

| Section | Layer | Meaning |
| --- | --- | --- |
| `line` | contract metadata | production line id, refs, and hook refs consumed by runtime |
| `subtitles` | L1/L2/L3 projection | source subtitle, target subtitle, helper translation, currentness, dub input |
| `audio` | L1/L2/L3 projection | voiceover artifact, audio readiness, provider/voice facts |
| `compose` | L1/L2/L3 projection | compose status, final freshness, compose route facts |
| `artifact_facts` | L2 | physical artifact existence and URLs |
| `current_attempt` | L3 | interpreted current output state and stale/current reasons |
| `ready_gate` | L4 derived | compose/publish readiness and blocking reasons |
| `deliverables` | L2/L4 projection | deliverable rows derived from artifact truth and readiness |
| `operator_summary` | L4 presenter | human-readable guidance based on derived facts |
| `advisory` | L4 skills/presenter | optional advice from skills bundle; read-only |

`advisory` is optional because not every workbench state has active advisory output, but when present it must validate as L4 read-only guidance.

## Invariants

1. `ready_gate` is derived from state facts, never authored by frontend.
2. `deliverables` must not report semantic success when the underlying artifact facts or currentness say otherwise.
3. `subtitles.helper_translation` is auxiliary and must not overwrite `subtitles.primary_editable_text`.
4. `subtitles.primary_editable_text` reflects authoritative target subtitle truth only.
5. `audio.audio_ready` and `current_attempt.dub_current` must derive from voice/audio state, not stale step labels.
6. `compose.final.exists` must be separated from `compose.final.fresh`.
7. `operator_summary` and `advisory` may explain, but must not create readiness.

## Hot Follow Baseline Fields

The current Hot Follow hub may include compatibility fields while VeoBase01 refactors continue. Compatibility fields are allowed only if they mirror the typed sections above.

Forbidden compatibility behavior:

- deriving ready state from display labels
- treating helper text as target subtitle truth
- treating optional pack/scenes output as primary final completion
- treating physical target subtitle existence as semantic target subtitle currentness

## Validation

Every VeoBase01 PR that changes workbench hub assembly must prove:

- artifact facts and deliverables agree
- current attempt and ready gate agree
- helper translation cannot poison subtitle/dub/compose truth
- URL and local-upload Hot Follow paths still validate
- `HotFollowWorkbenchResponse` accepts the runtime payload without changing the wire response shape
