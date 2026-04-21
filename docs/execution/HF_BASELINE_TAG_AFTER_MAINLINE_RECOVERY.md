# Hot Follow Baseline Tag After Mainline Recovery

Date: 2026-04-22

## Why This Tag Was Created

The current Hot Follow main business line has been recovered and live-validated on a real task. This tag freezes the recovered baseline before starting any separate helper-translation repair work.

The baseline confirms the main subtitle -> dub -> compose path is working again:

- target subtitle main object write works
- canonical Vietnamese subtitle artifact exists
- dub works
- final compose works
- publish readiness is restored

This is a baseline-freeze action only. No runtime code is changed by this step.

## Tag

- Tag name: `hot-follow-business-baseline-20260421`
- Tagged commit: `22f528a412ce3b14ea44b533848ddfc6235f251a`
- Commit subject: `Merge branch 'hotfix/hf-target-subtitle-save-contract'`

## Validation Evidence

Recovered real task:

- Task: `b1bf7348a7f3`

Observed validation evidence:

- `subtitles.status=done`
- `dub.status=done`
- `compose.status=done`
- `vi.srt` done
- `audio_vi.mp3` done
- final video done
- `ready_gate.subtitle_ready=true`
- `ready_gate.audio_ready=true`
- `ready_gate.compose_ready=true`
- `ready_gate.publish_ready=true`
- target subtitle main object is valid
- `subtitle_ready=true`
- `audio_ready=true`
- `dub_current=true`
- `compose_ready=true`
- `publish_ready=true`

## Scope Exclusions

Helper-only translation is not included as fixed in this baseline.

Known excluded issue:

- helper translate can still return `helper_translate_provider_exhausted` / Gemini `429`

This helper-only translation issue is isolated from the recovered main business path and must be handled in a separate narrow branch.

PR-4 and PR-5 remain paused. This baseline tag does not restart PR-4, does not restart PR-5, and does not authorize architecture work.

## Next Step

Create a narrow helper-translation-only branch after tagging.

That branch should only address helper translation/provider exhaustion handling and must not change the recovered main subtitle -> dub -> compose business line.
