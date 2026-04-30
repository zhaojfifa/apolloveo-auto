# gateway/app/services/media/

**Status**: P1.5 host reservation (empty until P2 absorption begins)
**Authority**: Master Plan v1.1 Part IV.1; Donor Boundary §3.1; Capability Mapping rows M-01..M-05

## Purpose

Host directory for media-processing helpers: ffmpeg routines, subtitle building, audio/video merge, serialization, text normalization. Will receive absorbed code from SwiftCraft `backend/app/utils/{ffmpeg_localization,media,subtitle_builder,serialize,zh_normalize}.py`.

## Consumes

- `factory_audio_plan_contract_v1` — audio plan shapes
- `factory_language_plan_contract_v1` — language / subtitle strategy
- `factory_scene_plan_contract_v1` — scene plan shapes (for compose helpers)

## Does not

- Write to L1 / L2 / L3 / L4 state (truth writes belong to callers in `gateway/app/services/...` or skills)
- Auto-promote outputs to Asset Library (only the explicit `promote_flow` does that)
- Import any `swiftcraft.*` package (forbidden)
- Expose helpers directly to the front-end (front-end consumes contracts only)

## Absorption pre-condition

Code lands here only after `swiftcraft_capability_mapping_v1.md` rows M-01..M-05 move to `In progress` via an absorption PR citing the row id.
