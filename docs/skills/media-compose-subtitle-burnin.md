# Media Compose: Subtitle Burn-in Skill Baseline

## Hard Rule
If `compose_plan.overlay_subtitles=true`, compose must burn target subtitles into video.

## Prerequisites
- Target subtitle asset must exist.
- Language normalization must map `my -> mm`.
- Subtitle resolution source of truth:
  - Burmese: `mm_srt_path` or `deliver/tasks/{task_id}/mm.srt`
  - Other languages: `{target_lang}_srt_path` (optional fallback by deliver convention)

## Font Contract
- Use bundled repo font only:
  - `gateway/app/assets/fonts/NotoSansMyanmar-Regular.ttf`
- No dependency on system fonts (`/usr/share/fonts`, `fc-list`).
- Missing bundled font must fail with `font_missing`.

## FFmpeg Contract
- `overlay_subtitles=true`:
  - command must include `subtitles=...` filter
  - video must be re-encoded (`libx264`)
- `overlay_subtitles=false`:
  - existing fast path may keep `-c:v copy`

## Error Contract
- `subtitles_missing`
- `font_missing`
- `compose_failed`
- `compose_in_progress`

All failures must include short operator-readable `message`.
