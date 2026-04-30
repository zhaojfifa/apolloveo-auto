# Hot Follow Phase 3 Surface Validation

Date: 2026-04-30
Branch: `rebuild/hf-business-flow-and-state-machine`

## Samples Tested

| Sample ID | Lane | Scenario |
| --- | --- | --- |
| `hf-phase3-url-origin-only` | URL | `origin.srt` exists, stale legacy `mm_srt_path` exists, target subtitle truth is not materialized/current. |
| `hf-phase3-local-helper-telemetry` | Local upload | Helper translation reports provider exhaustion telemetry, with no target subtitle materialization. |
| `hf-phase3-manual-save-vi-materialized` | Manual target subtitle save | Authoritative/current `vi.srt` is materialized, previous dub/compose snapshots are stale or absent. |

## Surfaces Validated

- `build_hot_follow_workbench_hub`
- `build_hot_follow_publish_hub`
- `hf_deliverables`
- Ready-gate projection embedded in the workbench and publish payloads

## Findings

- No tested sample showed subtitle-missing and subtitle-available truth conflicts.
- URL origin-only state did not promote target subtitle closure, even with a stale legacy `mm_srt_path`.
- Helper pending/failed telemetry stayed under helper telemetry and did not count as subtitle business truth.
- Manual save projected authoritative/current `vi.srt`; audio stayed blocked because no current `audio_vi.mp3` existed.
- Compose stayed blocked unless authoritative/current target subtitle truth and current audio were both present.
- Publish derived `mm.txt` is now gated by authoritative/current target subtitle truth, so a legacy `mm_srt_path` cannot surface derived subtitle/script availability by itself.

## Surface Gap Closed

- Workbench subtitles payload was not carrying `subtitle_artifact_exists`, so the strict ready gate could disagree with the subtitle section on a valid manual-save sample. The surface now carries `subtitle_artifact_exists` and `actual_burn_subtitle_source` from subtitle authority truth.
- Publish deliverable labels now preserve the authoritative deliverable label, so Vietnamese target subtitle materialization surfaces as `vi.srt`. A language-specific `vi_srt` deliverable alias is emitted from the same authoritative item.

## Remaining Compatibility Gaps

- Legacy tests and fixtures outside the focused Phase 1-3 set may still encode old assumptions that audio can be current without explicit target subtitle truth.
- This validation uses controlled Hot Follow task-shaped samples and injected storage/download loaders; it does not execute external providers or real media processing.
- Older `mm_srt` compatibility naming remains as an alias for the same authoritative subtitle deliverable, but it no longer creates truth independently.

## Recommendation

Merge is recommended for the Hot Follow first-line v1 business-flow/state-machine rebuild if the focused regression suite remains green. Remaining legacy fixture cleanup should be handled separately without relaxing subtitle, audio, or compose strictness.
