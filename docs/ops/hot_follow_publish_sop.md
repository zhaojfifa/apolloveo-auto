# Hot Follow Publish SOP

## 1. Scope
This SOP covers `/tasks/{task_id}/publish` for Hot Follow tasks:
- readiness check
- final preview check
- deliverables download
- scene pack optional generation

## 2. Publish Flow
1. Open publish page for target `task_id`.
2. Confirm `Composed: Ready` status.
3. Play final preview and check audio/video.
4. Download required deliverables.
5. (Optional) Generate Scene Pack for downstream editing.
6. Fill publish URL/notes and submit backfill.

## 3. Deliverables Meaning
- `final.mp4`: final composed output for publication.
- `pack.zip` / `edit_bundle.zip`: editing package.
- `origin.srt` / `mm.srt` / `mm.txt`: subtitle/script artifacts.
- `mm_audio`: generated voiceover.
- `scenes.zip`: optional scene pack, not required to publish final video.

## 4. Pre-publish Checklist
- `composed_ready == true`.
- Final preview is playable on page.
- Duration and content are correct.
- No blocking compose error in publish/workbench hub.
- Required files are downloadable.

## 5. Download and Delivery
- Use grouped deliverables list.
- Download only needed artifacts for current workflow.
- Keep `final.mp4` as primary publish artifact.
- Treat Scene Pack as optional helper asset.

## 6. Scene Pack (Optional)
- Click `Generate Scene Pack` on publish page.
- If response is in-progress, wait for status update.
- Scene Pack pending does not block `可发布`.

## 7. Common Issues
- `Not Ready`: compose not finished or failed; return to workbench and rerun compose.
- Preview blank: refresh publish hub, check final URL and stream status.
- Scene Pack unavailable: generate from publish/workbench and retry later.
- Download link unavailable: wait for artifact writeback and reload.
