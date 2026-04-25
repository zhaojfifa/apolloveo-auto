# SwiftCraft → ApolloVeo Capability Mapping v1

- Status: Frozen for P1.5 (absorption-PR prerequisite)
- Date: 2026-04-25
- Authority: ADR `ADR-donor-swiftcraft-capability-only.md`, `docs/donor/swiftcraft_donor_boundary_v1.md`, Master Plan v1.1 Part I Q9 / Part III P1.5
- Donor commit pin (P2 absorption wave 1): TBD — set at the first absorption PR; one pin per absorption wave; recorded below

## 0. Donor commit pins

| Wave | Donor commit (short SHA) | Recorded by | Date |
|---|---|---|---|
| W1 (helpers + storage) | TBD | TBD | TBD |
| W2 (ASR / translate / TTS) | TBD | TBD | TBD |
| W3 (provider clients) | TBD | TBD | TBD |
| W4 (vendor / asset bridge) | TBD | TBD | TBD |
| W5 (engine prompt fragments) | TBD | TBD | TBD |

A wave is closed when all of its rows reach `Absorbed` or `Skipped`. A new wave SHA pin is required if donor HEAD has moved between waves.

## 1. How to use this document

- Every absorption PR MUST cite a row id from this document in its description (e.g. `Absorbs M-03`)
- A row may be cited by at most one merged PR; subsequent edits to the same Apollo file follow normal PR rules without citing this mapping
- A row in `Not started` status MAY NOT be absorbed — it must first move through `In progress` (PR open)
- A row in `Skipped` status records a deliberate decision not to absorb; it can be re-opened only by amending this doc

Row id schema: `<category>-<##>` where category is `M / A / P / V / E / R / O` matching `swiftcraft_donor_boundary_v1.md` §3 sub-sections (§3.1 → M, §3.2 → A, §3.3 → P, §3.4 → V, §3.5 → E, §3.6 → R, §3.7 → O).

## 2. Mapping rows

### 2.1 M — Media helpers (boundary §3.1)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| M-01 | `backend/app/utils/ffmpeg_localization.py` | `gateway/app/services/media/ffmpeg_localization.py` | `factory_audio_plan` + `factory_language_plan` consumer; called by `DubAdapter` and `PackAdapter` impls | Wrap | All entry points return Apollo `MediaResult` shape; no SwiftCraft `task_*` references; attribution header present | Not started |
| M-02 | `backend/app/utils/media.py` | `gateway/app/services/media/media_helpers.py` | `factory_scene_plan` + `factory_audio_plan` consumer | Wrap | Merge against existing `gateway/app/services/media_helpers.py`; deduplicate; preserve existing Apollo callers | Not started |
| M-03 | `backend/app/utils/subtitle_builder.py` | `gateway/app/services/media/subtitle_builder.py` | `factory_language_plan` consumer; called by `SubtitlesAdapter` impls | Wrap | Plain-text SRT path preserved (matches Hot Follow frozen rule); no language-plan invention | Not started |
| M-04 | `backend/app/utils/serialize.py` | `gateway/app/services/media/serialize.py` | n/a (pure utility) | Wrap | Pure functions only; unit tested | Not started |
| M-05 | `backend/app/utils/zh_normalize.py` | `gateway/app/services/media/zh_normalize.py` | n/a (text utility) | Wrap | Pure functions only; preserves Apollo's existing dub text guard semantics | Not started |

### 2.2 A — ASR / translate / TTS (boundary §3.2)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| A-01 | `backend/app/utils/asr_worker.py` | `gateway/app/services/providers/whisper/worker.py` | `SubtitlesAdapter` (ASR mode) | Rewrite | No SwiftCraft task / queue coupling; outputs Apollo `SubtitlesResult`; fallback paths emit advisories, never primary truth | Not started |
| A-02 | `backend/app/utils/fastwhisper_asr.py` | `gateway/app/services/providers/whisper/fastwhisper.py` | `SubtitlesAdapter` (ASR provider) | Wrap | Provider client only; cache / preflight retained; no fallback-as-truth | Not started |
| A-03 | `backend/app/utils/translate_gemini.py` | `gateway/app/services/providers/gemini/translate.py` | `UnderstandingAdapter` + `SubtitlesAdapter` | Wrap | Bound to adapter base; no direct front-end exposure | Not started |
| A-04 | `backend/app/utils/translate_mm.py` | n/a | n/a | Pattern-only | Capture as ADR or contract note if MM fallback design is needed; do not copy code | Not started |
| A-05 | `backend/app/utils/dubbing_service.py` | `gateway/app/services/providers/azure/dub.py` | `DubAdapter` | Rewrite | Bound to `DubAdapter`; no SwiftCraft task references; honors `dub_text_guard` semantics already in Apollo | Not started |

### 2.3 P — Provider clients (boundary §3.3)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| P-01 | `backend/app/providers/akool_client.py` | `gateway/app/services/providers/akool/client.py` | `AvatarAdapter` + `VideoGenAdapter` (depending on Akool endpoint) | Wrap | Single canonical client (collapse with P-02 duplicate); env-key injection via Apollo config; no SwiftCraft task wiring | Not started |
| P-02 | `backend/app/services/akool_client.py` | merged into P-01 target | same as P-01 | Rewrite (merge) | Resolve duplication; record reconciliation notes in absorption PR | Not started |
| P-03 | `backend/app/services/r2_client.py` | `gateway/app/services/providers/r2/client.py` | storage provider (not a capability adapter) | Wrap | Bound under Apollo storage abstraction; honors Apollo Artifact Store / Asset Library boundary; no auto-promote | Not started |

### 2.4 V — Vendor / asset bridge (boundary §3.4)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| V-01 | `backend/app/services/vendor_asset_bridge.py` | `gateway/app/services/artifacts/vendor_asset_bridge.py` | `factory_delivery_contract` artifact rows | Rewrite | Produces artifact rows shaped to `factory_delivery_contract_v1`; MUST NOT auto-promote to Asset Library; promote requires explicit Apollo `promote_flow` call | Not started |
| V-02 | `backend/app/services/video_face_extractor.py` | `gateway/app/services/artifacts/face_extractor.py` | helper for `AvatarAdapter` / `VideoGenAdapter` | Wrap | Pure helper; no truth writes; output consumed by skill or worker, not by router | Not started |

### 2.5 E — Engine prompt fragments (boundary §3.5)

> Engine files are NEVER absorbed wholesale. Only prompt-shaping segments and provider call patterns are lifted. Engine task / orchestration logic stays in donor.

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| E-01 | `backend/app/engines/action_replica_prompt.py` | `skills/digital_anchor/action_replica_prompt.py` | skill-level prompt; consumed by `AvatarAdapter` route hint | Wrap | Prompt builders only; no engine task wiring; no scenario truth | Not started |
| E-02 | prompt segment of `backend/app/engines/akool_engine.py` | `skills/digital_anchor/akool_prompt.py` | `AvatarAdapter` route hint | Selective Wrap | Extract prompt builders only; engine orchestration stays in donor | Not started |
| E-03 | `backend/app/engines/akool_swap_face_engine.py` (prompt + segmentation hints) | `skills/swap_face/` (future line) | future swap_face packet | Pattern-only | Reference only; no copy in P2; revisit when swap_face line packet opens | Not started |
| E-04 | prompt segment of `backend/app/engines/fal_kling_motioncontrol_v3_pro_engine.py` | `skills/digital_anchor/fal_kling_prompt.py` | `VideoGenAdapter` / `AvatarAdapter` route hint | Selective Wrap | Identity anchor / motion preserve / camera preserve patterns; no engine task code | Not started |
| E-05 | prompt segment of `backend/app/engines/fal_kling_reference_v2v_engine.py` | `skills/digital_anchor/fal_kling_v2v_prompt.py` | `VideoGenAdapter` route hint | Selective Wrap | Same as E-04 | Not started |
| E-06 | prompt segment of `backend/app/engines/fal_wan26_flash_engine.py` | `skills/digital_anchor/fal_wan26_flash_prompt.py` | `VideoGenAdapter` route hint | Selective Wrap | Same as E-04 | Not started |
| E-07 | prompt segment of `backend/app/engines/fal_wan26_r2v_engine.py` | `skills/digital_anchor/fal_wan26_r2v_prompt.py` | `VideoGenAdapter` route hint | Selective Wrap | Same as E-04 | Not started |
| E-08 | prompt + helper segments of `backend/app/engines/localization_engine.py` | `skills/hot_follow/localization_prompt.py` | Hot Follow reference (already frozen) | Pattern-only | Hot Follow internals are frozen; only reference patterns; no live edits to Hot Follow line | Not started |
| E-09 | `backend/app/engines/registry.py`, `base.py`, `mock_engine.py`, `follow_video_placeholder_engine.py` | n/a | n/a | **Skipped (forbidden)** | Forbidden by boundary §4.2; row exists for audit completeness only | Skipped |

### 2.6 R — Policies / ports / preset patterns (boundary §3.6)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| R-01 | `backend/app/policies/video_recraft_policy.py` | n/a (pattern only) | n/a | Pattern-only | Capture pattern as ADR if needed; do not import | Not started |
| R-02 | `backend/app/ports/recraft_video_provider.py` | n/a (pattern only) | reference for `AdapterBase` | Pattern-only | Use as reference for capability adapter base; do not copy | Not started |
| R-03 | `backend/app/services/preset_resolver.py`, `presets.py` | n/a (pattern only) | reference for Apollo `presets/` and `gateway/app/services/planning/prompt_registry.py` | Pattern-only | Apollo presets already exist; only borrow organization patterns | Not started |
| R-04 | `backend/app/services/swap_quality.py`, `swap_segmenter.py` | `skills/swap_face/` (future line) | future swap_face packet | Pattern-only | Reference for swap_face line packet; revisit when that line opens | Not started |

### 2.7 O — Env / runtime / storage organization (boundary §3.7)

| ID | Donor path | Apollo target | Capability / contract binding | Strategy | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| O-01 | `.env.example` shape | `ops/env/env_matrix_v1.md` | env matrix | Pattern-only | Capture provider env matrix; record key naming normalization in doc; do not copy file | Not started |
| O-02 | R2 / S3 split, storage assumptions | `ops/env/storage_layout_v1.md` | storage layout | Pattern-only | Record patterns; do not copy code | Not started |
| O-03 | `scripts/render_preflight.sh` | `ops/runbooks/render_preflight.sh` | deploy preflight | Wrap | Optional; only absorb if Apollo deploy pipeline needs it | Not started |

## 3. Row lifecycle

```
Not started  →  In progress  →  Absorbed
                              ↘  Skipped
```

- `Not started`: row defined in this doc; no PR opened
- `In progress`: an absorption PR has been opened citing this row id; status updated by PR author
- `Absorbed`: PR merged; attribution header in target file points back to this row
- `Skipped`: deliberate decision not to absorb; rationale recorded in row notes

Status edits in this doc require a same-PR or follow-up PR; status drift between doc and reality is treated as a contract violation.

## 4. Forbidden cross-references

A row in this document MUST NOT cite or import any module listed in `swiftcraft_donor_boundary_v1.md` §4 (forbidden list). If during absorption a permitted row is found to transitively pull in a forbidden module, the absorption PR is rejected and the row is moved to Skipped with a justification note, per boundary doc §8.

## 5. Audit trail summary

For any future reviewer, this document answers:

- Which donor modules entered ApolloVeo (rows in `Absorbed`)
- Where they live in Apollo (`Apollo target` column)
- Why they were chosen (`Capability / contract binding` column)
- Which donor modules were considered and rejected (rows in `Skipped`)
- Which donor commit each absorption wave was pinned to (§0)

## 6. References

- `docs/adr/ADR-donor-swiftcraft-capability-only.md`
- `docs/donor/swiftcraft_donor_boundary_v1.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q9, Part III P1.5, Part VII
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
