# SCENE_SOP_HOT_FOLLOW (v1.9)

## Scenario Definition
Hot Follow (Hot Trend Remix) is a 3-page flow that creates a task from a source URL, runs the pipeline, and delivers downloadable artifacts for publishing.

## 3-Page Model
- P1 New Task: `/tasks/hot/new` (wizard entry + probe + create & run)
- P2 Workbench: `/tasks/{task_id}` (step control + events)
- P3 Delivery Center: `/tasks/{task_id}/publish` (deliverables + publish backfill)

## Operator SOP
1) Open P1, paste source URL, wait for Probe card to show title/cover.
2) (Optional) Upload BGM and set mix ratio.
3) Click **Create & Run**. System runs parse ¡ú subtitles ¡ú dub ¡ú pack ¡ú scenes.
4) Open P2 to monitor progress and re-run steps if needed.
5) Open P3 to download deliverables (pack/scenes/subtitles/audio).
6) After external publish, backfill published URL in P3.

## Error Handling Playbook
- Probe failed: verify URL, platform, provider health; retry.
- Parse failed: re-run parse; if repeated, check provider or input URL.
- Subtitles failed: re-run subtitles; check ASR backend availability.
- Dub failed: re-run dub; verify voice provider.
- Pack failed: re-run pack; check storage availability.

## SSOT Rule
UI readiness and download availability MUST be gated by deliverables keys, not status alone.

## P0 Acceptance Criteria
- 3 pages render with locale switching.
- Probe endpoint returns metadata without task creation or raw download.
- BGM upload attaches config via policy_upsert.
- Deliverables list is gated by deliverables keys.
- Publish backfill persists `published_url` via policy_upsert.
