# SwiftCraft Donor Boundary v1

- Status: Frozen for P1.5 (absorption gate)
- Date: 2026-04-25
- Authority: ADR `ADR-donor-swiftcraft-capability-only.md`, Master Plan v1.1 Part II
- Donor repo: `https://github.com/zhaojfifa/swiftcraft` (local clone `/Users/tylerzhao/Code/swiftcraft`)
- Donor commit pin: TBD at first absorption PR (see §6); pin must be recorded in `swiftcraft_capability_mapping_v1.md` header

## 1. Purpose

This document is the absorption gate. Before any SwiftCraft code lands in ApolloVeo, this document fixes:

1. The list of modules that MAY be absorbed
2. The list of modules / concepts that MUST NOT be absorbed
3. Attribution and ownership rules for absorbed code
4. The rewriting requirements every absorbed module must meet
5. The audit trail requirements for absorption PRs

A SwiftCraft module not listed in §3 is implicitly forbidden. Adding to §3 requires updating this document and citing a Master Plan amendment.

## 2. Donor Identity

- Repo: `https://github.com/zhaojfifa/swiftcraft`
- Author / owner: same author as ApolloVeo (zhaojfifa)
- License declared in donor repo: none present at HEAD (no LICENSE file)
- License treatment: internal-source donor; absorbed code is treated as first-party code authored by the same owner. No external license boilerplate required, but every absorbed file MUST include an attribution header (see §5).
- Donor stability: SwiftCraft remains a separate repo; ApolloVeo does not depend on its runtime, package, or release cadence.

## 3. Permitted Absorption Surface

Each row below identifies a SwiftCraft source path, the absorption strategy, and the Apollo target host directory. Strategy options:

- **Rewrite** — rewrite from scratch in Apollo style, using SwiftCraft as reference only
- **Wrap** — copy code into Apollo path with minimal edits, then wrap behind Apollo capability adapter base
- **Pattern-only** — do not copy code; capture pattern in ADR or contract doc

### 3.1 Media helpers

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/utils/ffmpeg_localization.py` | Wrap | `gateway/app/services/media/ffmpeg_localization.py` | Caller surface re-typed; remove implicit task-truth writes |
| `backend/app/utils/media.py` | Wrap | `gateway/app/services/media/media_helpers.py` | Merge against existing `gateway/app/services/media_helpers.py` |
| `backend/app/utils/subtitle_builder.py` | Wrap | `gateway/app/services/media/subtitle_builder.py` | Must consume `factory_audio_plan` / `factory_language_plan` shapes only |
| `backend/app/utils/serialize.py` | Wrap | `gateway/app/services/media/serialize.py` | Pure function; trivial |
| `backend/app/utils/zh_normalize.py` | Wrap | `gateway/app/services/media/zh_normalize.py` | Pure text utility |

### 3.2 ASR / translate / TTS

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/utils/asr_worker.py` | Rewrite | `gateway/app/services/providers/whisper/worker.py` | Strip task / queue coupling; output Apollo `SubtitlesResult` shape |
| `backend/app/utils/fastwhisper_asr.py` | Wrap | `gateway/app/services/providers/whisper/fastwhisper.py` | Provider client only; no fallback-as-truth |
| `backend/app/utils/translate_gemini.py` | Wrap | `gateway/app/services/providers/gemini/translate.py` | Bind to `UnderstandingAdapter` / `SubtitlesAdapter` interfaces |
| `backend/app/utils/translate_mm.py` | Pattern-only | n/a | Use as reference for fallback design; do not copy |
| `backend/app/utils/dubbing_service.py` | Rewrite | `gateway/app/services/providers/azure/dub.py` | Bind to `DubAdapter`; remove SwiftCraft task references |

### 3.3 Provider clients

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/providers/akool_client.py` | Wrap | `gateway/app/services/providers/akool/client.py` | Single canonical client; collapse with `services/akool_client.py` duplicate |
| `backend/app/services/akool_client.py` | Rewrite | merge into above | Resolve duplication during absorption PR |
| `backend/app/services/r2_client.py` | Wrap | `gateway/app/services/providers/r2/client.py` | Storage provider; not a capability adapter |

### 3.4 Vendor / asset bridge

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/services/vendor_asset_bridge.py` | Rewrite | `gateway/app/services/artifacts/vendor_asset_bridge.py` | Must produce `factory_delivery_contract`-shaped artifact rows; MUST NOT auto-promote to Asset Library |
| `backend/app/services/video_face_extractor.py` | Wrap | `gateway/app/services/artifacts/face_extractor.py` | Pure helper; no truth writes |

### 3.5 Engine prompt fragments (capability hints, not engine truth)

Engine files in `backend/app/engines/` are **not** absorbed wholesale. Only their prompt-shaping segments and provider call patterns may be lifted into Apollo skills.

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/engines/action_replica_prompt.py` | Wrap | `skills/digital_anchor/action_replica_prompt.py` | Prompt shaping only; remove engine task wiring |
| `backend/app/engines/akool_engine.py` (prompt segment only) | Pattern-only + selective Wrap | `skills/digital_anchor/akool_prompt.py` | Extract prompt builders; engine orchestration logic stays in donor |
| `backend/app/engines/akool_swap_face_engine.py` (prompt + segmentation hints) | Pattern-only | `skills/swap_face/` (future line) | Reference for swap_face line packet, not absorbed in P2 |
| `backend/app/engines/fal_kling_motioncontrol_v3_pro_engine.py` (prompt + provider params) | Selective Wrap | `skills/digital_anchor/fal_kling_prompt.py` | Identity anchor / motion preserve / camera preserve patterns; no engine task code |
| `backend/app/engines/fal_kling_reference_v2v_engine.py` | Selective Wrap | `skills/digital_anchor/fal_kling_v2v_prompt.py` | Same |
| `backend/app/engines/fal_wan26_flash_engine.py` | Selective Wrap | `skills/digital_anchor/fal_wan26_flash_prompt.py` | Same |
| `backend/app/engines/fal_wan26_r2v_engine.py` | Selective Wrap | `skills/digital_anchor/fal_wan26_r2v_prompt.py` | Same |
| `backend/app/engines/localization_engine.py` (prompt + helper segments) | Pattern-only | `skills/hot_follow/localization_prompt.py` | Hot Follow already frozen; only reference patterns |

### 3.6 Policies / ports / preset patterns

| SwiftCraft path | Strategy | Apollo target | Notes |
|---|---|---|---|
| `backend/app/policies/video_recraft_policy.py` | Pattern-only | n/a | Capture as ADR if needed; do not import |
| `backend/app/ports/recraft_video_provider.py` | Pattern-only | n/a | Use as reference for Apollo capability adapter base |
| `backend/app/services/preset_resolver.py`, `presets.py` | Pattern-only | n/a | Apollo presets live in `presets/` and `gateway/app/services/planning/prompt_registry.py` |
| `backend/app/services/swap_quality.py`, `swap_segmenter.py` | Pattern-only | `skills/swap_face/` (future) | Reference for swap_face line packet |

### 3.7 Env / runtime / storage organization

| SwiftCraft surface | Strategy | Apollo target | Notes |
|---|---|---|---|
| `.env.example` shape | Pattern-only | `ops/env/env_matrix_v1.md` | Capture provider env matrix; do not copy |
| R2 / S3 split, storage assumptions | Pattern-only | `ops/env/storage_layout_v1.md` | Reference patterns |
| `scripts/render_preflight.sh` | Wrap | `ops/runbooks/render_preflight.sh` | If deploy preflight is needed |

## 4. Forbidden Absorption Surface

The following SwiftCraft modules and concepts MUST NOT be absorbed by direct copy, import, or semantic re-implementation:

### 4.1 Task / state truth

- `backend/app/services/task_contract.py`
- `backend/app/services/task_manager.py`
- `backend/app/services/task_service.py`
- `backend/app/services/task_store.py`

Reason: ApolloVeo holds task / state truth via line contract + four-layer state model. Importing SwiftCraft's task model would create a parallel truth source.

### 4.2 Engine truth

- `backend/app/engines/registry.py` (engine-as-truth registry)
- `backend/app/engines/base.py` (engine task base coupled to scenario truth)
- `backend/app/engines/mock_engine.py` (test scaffolding, not production capability)
- `backend/app/engines/follow_video_placeholder_engine.py` (placeholder; not capability)
- Wholesale copy of any engine file in `backend/app/engines/` (only prompt fragments per §3.5 are permitted)

Reason: ApolloVeo runtime is line-contract-driven, not engine-shaped. Engine truth conflicts with packet / capability adapter / worker gateway model.

### 4.3 Payload shapes

- `run_config_snapshot` payload shape
- Any provider-shaped task config snapshot embedded in SwiftCraft's task model
- Scenario-shaped delivery objects (`action_replica` / `localization` / `swap_face` / `swap_scene` / `follow_video` scenario truth)

Reason: ApolloVeo delivery is `factory_delivery_contract_v1`-shaped, line-bound. Scenario-shaped payloads cannot be re-projected without losing line contract guarantees.

### 4.4 Decision logic

- Internal delivery / ready-gate decisions written against scenario truth
- Fallback ASR / TTS paths that promote fallback output to primary truth
- Any code that writes to L1 / L2 / L3 / L4 of a state model that is not ApolloVeo's

Reason: ApolloVeo's ready gate consumes L2 artifact facts and L3 current attempt. Donor decisions written against scenario truth would invert this discipline.

## 5. Re-homing and Attribution Rules

### 5.1 Path rule
Every absorbed file MUST live under one of the §3 target host directories. No `swiftcraft.*` package path may survive absorption.

### 5.2 Attribution header rule
Every absorbed file MUST include a header comment block:

```python
# Origin: SwiftCraft <relative path in donor repo>
# Donor commit: <short SHA pinned at absorption time>
# Absorbed into ApolloVeo on: <YYYY-MM-DD>
# Strategy: <Rewrite | Wrap | Pattern-only-derived>
# Capability mapping row: <link to swiftcraft_capability_mapping_v1.md row id>
```

This header is the audit trail. Removing it requires an ADR.

### 5.3 Import rule
- No `from swiftcraft.*` import in ApolloVeo source, ever
- No transitive import of a non-absorbed sibling SwiftCraft module
- Static-import scanner in P0 Guardrail Test Suite enforces both

### 5.4 Truth-write rule
Absorbed modules MUST NOT write to L1 / L2 / L3 / L4 state, delivery contract output, or asset library entries. They return values; Apollo callers write truth.

### 5.5 Adapter binding rule
Provider clients (Akool, Fal, Azure, Gemini, Whisper, R2) MUST be bound behind the corresponding capability adapter base interface (`UnderstandingAdapter` / `SubtitlesAdapter` / `DubAdapter` / `VideoGenAdapter` / `AvatarAdapter` / `PackAdapter`) before they are usable from line packets.

## 6. Audit Trail Requirements for Absorption PRs

Every absorption PR MUST:

1. Cite the corresponding row of `docs/donor/swiftcraft_capability_mapping_v1.md` in the PR description
2. Pin the donor commit SHA in the PR description (one repo-wide pin per absorption wave; recorded in mapping doc header)
3. Include the §5.2 attribution header in every absorbed file
4. Pass the P0 Guardrail Test Suite (no `swiftcraft.*` imports; no donor task / engine truth re-introduction)
5. Reference this boundary doc and the ADR in the PR description
6. NOT bundle multiple capability categories in one PR (one wave per §3 sub-section)

## 7. Front-end Isolation

No ApolloVeo front-end module imports any donor-derived helper, provider client, or worker adapter. Front-end consumes only contract objects and derived gates exposed by ApolloVeo gateway routers. Verified by:

- P0 contract test: scan front-end source for any reference to `gateway/app/services/providers/*`, `gateway/app/services/workers/adapters/*`, `gateway/app/services/media/*`
- P0 contract test: scan front-end source for any string literal matching `swiftcraft`

## 8. Boundary Drift Controls

If during absorption a permitted §3 module is found to carry hidden truth-write or task-coupled code:

1. Stop the absorption PR
2. Move the module to §4 forbidden list with a one-line justification
3. Update Master Plan v1.1 evidence table for P1.5

If a §4 module is later judged absorbable:

1. Open a Master Plan amendment
2. Add an ADR explaining the re-classification
3. Move the module to §3 with explicit absorption strategy

Both paths require architect approval. Drift without these steps is a contract violation.

## 9. References

- `docs/adr/ADR-donor-swiftcraft-capability-only.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q1 / Q7 / Q11 / Q12, Part II, Part III P1.5, Part VII
- `docs/donor/swiftcraft_capability_mapping_v1.md` (companion mapping doc)
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/hot_follow_line_contract.md` (frozen baseline; absorption MUST NOT regress)
