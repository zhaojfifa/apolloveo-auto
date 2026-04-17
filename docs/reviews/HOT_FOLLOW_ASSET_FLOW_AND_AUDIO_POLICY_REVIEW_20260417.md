# Hot Follow Asset Flow And Audio Policy Review

Date: 2026-04-17
Branch: `review/hf-asset-flow-and-audio-policy`
Scope: review-only asset-flow and audio-policy freeze. No runtime behavior changed.

## 1. Review Inputs

Mandatory inputs read:

- `PROJECT_RULES.md`
- `ENGINEERING_RULES.md`
- `ENGINEERING_STATUS.md`
- `docs/README.md`
- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- `docs/baseline/ARCHITECTURE_BASELINE.md`
- `docs/baseline/EXECUTION_BASELINE.md`
- `docs/runbooks/VERIFICATION_BASELINE.md`
- `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
- `docs/execution/logs/VEOSOP05_PROGRESS_LOG.md`
- `docs/reviews/HOT_FOLLOW_STATE_PROBE_AND_FIX_PLAN_20260416.md` from local review stash, because it is not present on current `main`

Implementation paths inspected:

- parse / local ingest: `gateway/app/routers/hot_follow_api.py`, `gateway/app/services/media_helpers.py`, `gateway/app/services/subtitle_helpers.py`
- subtitle storage/currentness: `gateway/app/services/subtitle_helpers.py`, `gateway/app/services/hot_follow_subtitle_currentness.py`
- dub generation / currentness / preview: `gateway/app/routers/tasks.py`, `gateway/app/services/voice_state.py`, `gateway/app/services/voice_service.py`
- source-audio policy: `gateway/app/services/source_audio_policy.py`, `gateway/app/services/media_helpers.py`
- compose input selection / final snapshot: `gateway/app/services/compose_service.py`, `gateway/app/services/task_view_helpers.py`
- workbench / publish diagnostics: `gateway/app/services/task_view.py`, `gateway/app/routers/hot_follow_api.py`, `gateway/app/static/js/hot_follow_workbench.js`
- ready gate: `docs/contracts/hot_follow_ready_gate.yaml`, `gateway/app/services/ready_gate/hot_follow_rules.py`, `gateway/app/services/status_policy/hot_follow_state.py`

## 2. Executive Judgment

Hot Follow now has a mostly protected mainline for subtitle -> TTS voiceover -> compose, but the current architecture still carries compatibility names that can make asset roles easy to misread.

The critical frozen rule is:

> Preserved source audio and uploaded BGM are compose input lanes only. They are not dubbing artifacts and must not drive `audio_ready`, `dub_current`, `compose_ready`, or `publish_ready` as if they were TTS voiceover.

Current runtime enforcement is strongest at `collect_voice_execution_state()` and the workbench audio semantics fields. Current residual risk is not a broad truth break; it is naming and presentation residue around `mm_audio_key`, `/audio_mm`, and generic `audio_url`.

## 3. Asset Flow Matrix

| Asset | Layer | Owner | Created at | Stored as / referenced by | Consumed by | Truth-source eligible? | Notes / risks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `source_video` / raw video | ingest artifact | parse/local ingest | link parse or local upload | `raw_path`; preview URL `/v1/tasks/{id}/raw`; storage name `raw.mp4` | workbench source player, compose video input fallback, parse projection | Yes for parse/source availability only | Raw video may contain an embedded audio stream; that stream is not a separate TTS asset. |
| `source_audio` | embedded lane inside source video | ingest artifact, selected by compose policy | exists implicitly when `raw.mp4` has audio and `pipeline_config.has_audio` is not false | no dedicated storage key; compose reads input `[0:a]` from source video | final compose when `source_audio_policy=preserve` and source audio is available | No for dub/audio truth | It is a source-audio bed, not a voiceover. Absence of audio in raw makes preserve degrade to no source bed. |
| `mute_video` | compatibility video artifact | earlier mute/parse path if present | upstream/legacy media path | `mute_video_key` / `mute_video_path`; workbench still maps preview to raw URL | compose video input before raw fallback | Yes only as video input availability | Current compose prefers `mute_video_key` over `raw_path`; this is compatibility behavior and should not imply source audio was preserved. |
| `origin_subtitle` | source subtitle/helper layer | subtitles step / source extraction | subtitles step | `origin_srt_path`, `origin.srt` | workbench source view, source-copy detection, translation helper | No for target readiness | Source/helper subtitles cannot satisfy target subtitle truth. |
| `target_subtitle` | authoritative target text layer | subtitles step or operator save | subtitles step / save endpoint | `mm_srt_path` compatibility field; actual file name from language profile such as `mm.srt` or `vi.srt`; text hash fields | dub text input, burn subtitle compose input, subtitle readiness | Yes for `subtitle_ready` only when currentness passes | Currentness rejects missing artifact, source mismatch, translation incomplete, empty target, and source-copy. |
| `tts_voiceover` | dubbing artifact | dub route / TTS provider | `run_dub_step_ssot` and upload | `mm_audio_key` / `mm_audio_path`; file normally `audio_mm.mp3`; `audio_sha256`; provider/voice/snapshot fields | voice preview, compose audio input, ready gate audio truth | Yes for `audio_ready` and `dub_current` only when current | Must match provider, resolved voice, subtitle snapshot, speed config, artifact role, and size. |
| `bgm_upload` | optional background audio asset | operator upload | BGM upload endpoint | `config.bgm.bgm_key`, `config.bgm.mix_ratio`, `config.bgm.strategy` | compose optional BGM input and workbench deliverable | No for dubbing truth | Separate from TTS voiceover. May coexist with source audio and TTS. |
| `mixed_audio` | transient compose result lane | compose service | FFmpeg filter graph | not stored as standalone artifact | final video muxing | No | It is an in-process mix of TTS/source/BGM according to policy, not an independent ready artifact. |
| `preview_audio` | presentation URL | voice state / workbench payload | derived at workbench render | `voiceover_url`, `tts_voiceover_url`, `dub_preview_url`; legacy route `/v1/tasks/{id}/audio_mm` | workbench audio player and TTS preview button | No independent truth | Must resolve to current TTS voiceover only. It should never point to preserved source audio/BGM. |
| `final_video` | deliverable artifact | compose service | final compose upload | `final_video_key` / `final_video_path`, `final_source_*` snapshots, `final_asset_version` | workbench final player, publish hub, task board | Yes for `compose_ready` / `publish_ready` only when fresh | Physical existence is not enough; freshness snapshot must match current subtitle/audio/render/source-audio policy. |

## 4. Asset Ownership Details

### Source Video And Source Audio

- Creator: link parse or local upload.
- Storage: `raw_path` points at `raw.mp4`.
- Source audio is not separately stored. Compose treats it as `[0:a]` from the video input only when `source_audio_policy=preserve` and `source_audio_available=true`.
- Allowed truth: raw video can prove parse/source availability. Embedded source audio cannot prove dubbing readiness.

### Target Subtitle

- Creator: subtitles step or operator save endpoint.
- Storage: language-profile file name, referenced through compatibility field `mm_srt_path`.
- Currentness owner: `compute_hot_follow_target_subtitle_currentness()`.
- Allowed truth: only a current target subtitle may drive `subtitle_ready` and unlock downstream TTS/compose truth.

### TTS Voiceover

- Creator: Hot Follow dub route through TTS provider.
- Storage: target-language voiceover artifact under compatibility fields `mm_audio_key` / `mm_audio_path`.
- Currentness owner: `collect_voice_execution_state()`.
- Allowed truth: current TTS voiceover is the only audio artifact that may drive `audio_ready=true` and `dub_current=true`.

### Uploaded BGM

- Creator: BGM upload endpoint.
- Storage: `config.bgm.bgm_key`, usually under a `bgm/` storage prefix.
- Consumption: optional compose input.
- Allowed truth: no mainline status truth. It may appear as a deliverable/input fact only.

### Final Video

- Creator: compose service.
- Storage: `final_video_key` / `final_video_path`.
- Currentness owner: compose freshness checks in `compose_service.py`, `task_view_helpers.py`, and ready-gate projection.
- Allowed truth: only current/fresh final video can drive `compose_ready` and therefore `publish_ready`.

## 5. Compose Input Path

### Common Video Input

Compose resolves video input in this order:

1. `mute_video_key`
2. `mute_video_path`
3. `raw_path`

This is the video carrier used by FFmpeg. When source audio is preserved, compose reads the source audio stream from that selected video input as `[0:a]`.

### Mute Original Audio

Intended semantics:

- source audio is not carried into final output
- if current TTS exists, final audio is TTS only, optionally mixed with uploaded BGM
- if TTS does not exist and this is not a no-dub/subtitle-only branch, compose must not proceed as if dubbing is complete

Runtime path:

- `source_audio_policy_from_task()` returns `mute`
- compose dispatch uses `_compose_voice_only()` or `_compose_voice_bgm()` for voiced paths
- subtitle-only without BGM uses `-an`

### Preserve Original BGM / Source Audio

Intended semantics:

- original source audio bed is preserved in final output
- preserved source audio is not a voiceover
- preserved source audio must not set `dub_current=true`
- if TTS exists, final audio is TTS + source audio bed, optionally plus uploaded BGM
- if TTS does not exist, the task may show source audio preserved but must still show TTS voiceover not ready

Runtime path:

- `source_audio_policy_from_task()` returns `preserve`
- compose uses `_compose_voice_source_audio()` or `_compose_voice_source_audio_bgm()` for voiced paths
- subtitle-only preserve uses `_compose_subtitle_only_source_audio()` or `_compose_subtitle_only_source_audio_bgm()`
- source audio availability is gated by `pipeline_config.has_audio != false`

### Standard TTS Dubbing

Intended semantics:

- authoritative target subtitle -> TTS provider -> current voiceover artifact
- current voiceover drives preview and dub truth
- BGM/source audio remain optional compose inputs only

Runtime path:

- dub route writes `mm_audio_key`, provider/voice metadata, `audio_sha256`, `dub_generated_at`, subtitle snapshot, and speed snapshot
- `collect_voice_execution_state()` validates the artifact and emits `voiceover_url` only when current
- workbench preview uses `dub_preview_url` / `tts_voiceover_url` before any legacy URL

### TTS + Preserved Source Audio

Intended semantics:

- TTS voiceover remains the only dubbing truth
- preserved source audio is mixed underneath as source bed
- final freshness records `final_source_audio_policy` so policy changes make old finals stale

Runtime path:

- compose mixes `[voice][source]` or `[voice][source][bgm]`
- final snapshot records `final_source_audio_policy`
- freshness rejects existing final if the current source-audio policy differs

## 6. Truth-Source Binding

| State | Allowed truth-source assets | Explicitly not allowed |
| --- | --- | --- |
| `subtitle_ready` | current target-language subtitle artifact, resolved through language profile and currentness checks | origin subtitles, normalized source subtitles, helper translation output, OCR/helper text, non-current target artifact |
| `audio_ready` | current TTS voiceover artifact matching provider, voice, target subtitle snapshot, speed snapshot, and storage validity | source video audio, preserved source audio, uploaded BGM, generic audio key whose role is source audio |
| `dub_current` | same current TTS voiceover truth as `audio_ready`, plus artifact existence and expected voice/provider match | source audio, BGM, stale TTS, TTS generated against old subtitle/speed/voice |
| `compose_ready` | current final exists, final is fresh, and ready gate has current audio or valid no-dub branch | physical stale final, historical final, final made with prior source-audio policy, final made with stale subtitle/TTS |
| `publish_ready` | `compose_ready` | raw final key existence, stale final URL, BGM/source audio presence |

Current important guardrails:

- `hf_persisted_audio_state()` marks audio as `source_audio` when `mm_audio_key` points to BGM/raw/mute-source keys.
- `collect_voice_execution_state()` returns `audio_ready_reason=voiceover_artifact_not_tts` for source-audio artifacts.
- `hf_source_audio_semantics()` exposes `source_audio_preserved`, `tts_voiceover_ready`, `tts_voiceover_url`, and `dub_preview_url` so UI surfaces can distinguish source-audio bed from TTS voiceover.
- `compute_final_staleness()` and `_current_final_is_fresh()` include `source_audio_policy` in final freshness.

## 7. Compatibility Naming Residue

| Name | Current role | Classification | Risk |
| --- | --- | --- | --- |
| `mm_audio_key` / `mm_audio_path` | stored reference for target-language TTS voiceover artifact, even for non-Myanmar target profiles | compatibility residue with truth-bearing content | Can mislead readers into thinking the asset is Myanmar-only or generic audio. Do not rename inside narrow truth fixes. |
| `/v1/tasks/{id}/audio_mm` | legacy audio download/preview route for current voiceover | compatibility route | Route name is Myanmar-shaped; payload must keep it gated to current TTS voiceover. |
| `voiceover_url` | presentation URL emitted only when current TTS voiceover is valid | semantic truth surface | Safe when sourced from voice state; should remain the preferred user-facing term. |
| `tts_voiceover_url` | explicit current TTS URL in workbench audio payload | semantic truth surface | Best current field for preview/player binding. |
| `dub_preview_url` | explicit preview URL for standard dub player | semantic truth surface | Should remain TTS-only. |
| `audio_url` | legacy alias currently equal to `voiceover_url` in audio config | compatibility alias | Must not be broadened to BGM/source audio. Future cleanup can remove or rename after consumers migrate. |
| `mm_srt_path` | compatibility reference to target subtitle artifact, including `vi.srt` | compatibility field with target-subtitle truth | Must be interpreted through language profile. Do not infer Myanmar language from field name. |
| `bgm_key` | uploaded BGM storage key under `config.bgm` | semantic compose-input field | Not a dub field and must never satisfy TTS truth. |

## 8. Current Safe Scope For Next PRs

Safe next PRs:

1. Narrow compose input binding review/fix if real-material sampling shows `mute_video_key` precedence conflicts with preserve-source-audio semantics.
2. Narrow source-audio policy persistence fix if a specific create/update path fails to write `source_audio_policy` consistently.
3. Narrow preview/player regression fix if any surface still plays BGM/source audio as dub preview.
4. Narrow status truth fix if a surface bypasses `collect_voice_execution_state()` / ready gate and projects source audio as audio readiness.
5. Focused documentation or small compatibility-label clarification for operator diagnostics.

Explicitly out of scope for the next Hot Follow repair PR:

- broad compose ownership redesign
- publish ownership redesign
- new production line or localization runtime
- translation bridge/platform work
- generalized asset registry/platformization
- `mm_*` naming cleanup mixed with behavior changes
- UI redesign beyond existing diagnostics/player binding
- new external APIs

## 9. Recommended Fix Order

1. Compose input binding sampling.

   Verify with real-material tasks that `preserve` reaches final FFmpeg branches and that the selected video input still exposes a source audio stream when preserve is intended. If a bug is found, fix only that binding.

2. Source-audio policy persistence audit.

   Confirm create, local upload, BGM upload, compose freshness, and workbench payload all preserve the same `mute` / `preserve` meaning.

3. Preview/player binding audit.

   Keep all dub preview/player surfaces on `dub_preview_url` / `tts_voiceover_url` only.

4. Status truth binding audit.

   Ensure task board, workbench, publish hub, and deliverables consume voice state / ready gate instead of raw `mm_audio_key` existence for current dub truth.

5. Naming cleanup.

   Defer until behavior is frozen and covered. Rename or alias `mm_*` fields only in a dedicated compatibility migration PR.

6. Deferred platformization.

   Asset registry, generalized multi-line audio policy, and broad Skills/platform runtime remain postponed.

## 10. Non-Goals

This review PR does not:

- change runtime logic
- change compose branches
- change route/service/status behavior
- rename compatibility fields
- add instrumentation beyond documentation
- implement the next source-audio or compose repair
