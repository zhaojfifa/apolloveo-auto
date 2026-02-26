# Hot Follow Delivery SOP

## 1. Input
- Provide Douyin source URL.
- Create/select Hot Follow task.

## 2. Automatic Pipeline
- `parse` -> fetch raw video and basic metadata
- `subtitles(mm)` -> generate target subtitle artifacts
- `dub(mm)` -> generate target voiceover audio
- `pack` -> generate editable package
- `compose` -> merge video + voice + optional BGM
- `publish` -> operator confirms and backfills publish record

## 3. Operator Actions
- Choose/adjust voice if needed.
- Upload BGM (optional) and set mix ratio.
- Click `Compose Final` and wait for completion.
- Download deliverables for publishing and archival.

## 4. Pre-Delivery Checklist
- Compose status is ready.
- Final video preview is playable.
- Deliverables list is complete and downloadable.
- Publish page status shows ready for release.

## 5. Deliverables
- Final: `final.mp4`
- Pack: `pack.zip` / `edit_bundle.zip`
- Subtitles: `origin.srt`, `mm.srt`, `mm.txt`
- Audio: `mm_audio` (voiceover), `bgm` (if uploaded)
- Scene pack: optional, does not block final delivery

## 6. Common Issues
- `compose_in_progress` (409):
  - Wait and refresh.
  - Avoid repeated clicks; UI is debounced.
- `scene pack pending`:
  - Optional; final delivery can proceed.
- Missing final:
  - Return to workbench and rerun compose.

## 7. Download and Handoff
- Download `final.mp4` for direct publish.
- Download pack/subtitles/audio as needed by editing or archive workflows.
- Complete publish backfill (`publish_url` / notes) after external posting.

## 8. Hard Subtitle Handling (v1.9)
- Hard subtitles in source videos are not removable in v1.9.
- Prefer **A-tier overlay** in compose:
  - Keep `overlay_subtitles` enabled.
  - Cover original subtitle area with black box / heavy stroke style.
  - Keep target subtitle text concise and readable.
- Use **B-tier simple crop** in CapCut/剪映 only when overlay cannot satisfy visual QA.
- If dubbing is too long, edit translated subtitles text and rerun dubbing (preferred over aggressive speed-up).
