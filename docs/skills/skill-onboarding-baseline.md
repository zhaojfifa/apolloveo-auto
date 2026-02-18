# Skill Onboarding Baseline (Command-like Providers)

## 1) Skill ID and Versioning
- `skill_id`: stable identifier (e.g. `compose.burnin.ffmpeg`)
- `version`: semantic version (`MAJOR.MINOR.PATCH`)
- `changelog`: required for contract or behavior changes

## 2) Inputs (Artifacts) Contract
- Define required artifact keys/paths explicitly.
- Example inputs:
  - `raw_video_key` (mp4, required)
  - `voiceover_audio_key` (mp3/aac, required)
  - `bgm_audio_key` (optional)
  - `subtitle_srt_key` (required when burn-in enabled)

## 3) Params Schema and Defaults
- Validate all params before execution.
- Required defaults must be documented.
- Example:
  - `overlay_subtitles: true`
  - `target_lang: "mm"`
  - `bgm_mix: 0.3` (range `0..1`)
  - `force: false`

## 4) Outputs (Artifacts) Contract
- Declare output key, mime, and readiness checks.
- Example:
  - `final_video_key = deliver/tasks/{task_id}/final.mp4`
  - `content_type = video/mp4`
  - `size_bytes > MIN_VIDEO_BYTES`
  - `duration_ms > 0`

## 5) Gating and Preconditions (Fail Fast)
- Validate tool/runtime availability (`ffmpeg`, fonts, provider env vars).
- Validate required inputs exist and are non-empty.
- Return typed reason codes on failure.

## 6) Idempotency and Lock Semantics
- Concurrent start on same task must return `409`.
- `409` body must be machine-readable:
```json
{
  "error": "compose_in_progress",
  "status": "running",
  "retry_after_ms": 1500,
  "task_id": "..."
}
```
- State must remain monotonic (`running -> done/failed`).

## 7) Error Code Dictionary (Operator-readable)
- `missing_raw`
- `missing_voiceover`
- `subtitles_missing`
- `font_missing`
- `compose_in_progress`
- `compose_failed`
- `final_missing`

Each error must include short `message` for operators.

## 8) Event and Log Requirements
- Log start/end timestamps and elapsed time.
- Record command and critical stderr tail:
  - `compose_last_ffmpeg_cmd`
  - `compose_last_error` (tail)
- Include task id and selected provider in logs.

## 9) Provider Contract (Timeouts, Retries, Env Deps)
- Document per-provider timeout and retry policy.
- Document hard dependencies:
  - CLI binaries (`ffmpeg`, `ffprobe`)
  - font packages (`Noto Sans Myanmar` for mm burn-in)
  - model/API env vars when applicable

## Appendix: Worked Example (Compose Burn-in)
- Input:
  - `overlay_subtitles=true`
  - `target_lang=mm`
- Behavior:
  - Resolve `mm.srt`, burn into video (`libx264`)
  - Mix voiceover (+ optional bgm)
  - Produce deliverable `final.mp4`
- Guarantee:
  - `final.exists=true`
  - `composed_ready=true`
  - operator can publish without external editing tools
