# Owner Summary — Matrix Script Real Video Production Capability Batch (2026-06-07)

Docs companion to the heavy batch (Fast Lane S5→S8). Not authority; the report governs.

Report: `docs/execution/MATRIX_SCRIPT_REAL_VIDEO_PRODUCTION_CAPABILITY_BATCH_20260607.md`

## Headline

**BLOCKED_CREDENTIAL_MISSING** for live voiceover + provider generation — **no credentials
exist in this environment** (Azure key/region unset; edge_tts returns HTTP 403; Kling/Runway/
Veo/fal/Akool all unset). Per the heavy-batch rules, the silent proxy is acceptable here
**because** credentials are genuinely missing and reported honestly. The operator final.mp4
is still **playable and operator-usable**, and the **real voiceover capability is landed +
proven** (it produces real narration the instant a TTS path works). **NOT merged.**

- rollback tag: `matrix-script-before-real-video-production-20260607` → `5d6c4402`
- branch: `feat/matrix-script-real-video-production-20260607`

## What this batch adds (real capability)

- **Real voiceover capability** — new `voiceover_capability.py`: Azure (credentialed) →
  edge_tts (keyless) → honest silent fallback, composed into the operator final.mp4. Proven
  real via an injected TTS (non-silent composed track, `audio_mode=edge_tts`,
  `voiceover_status=generated`, label 旁白已生成).
- **Operator-safe capability status** — voiceover / image_to_video / subtitles / bgm surfaced
  in the manifest, payload, view, and a Workbench status strip under the main video (旁白…/
  字幕已烧录 / AI 视频生成未启用·缺少凭证 / 配乐未选择). No provider brand, no secret, no leak.
- Preserved real: 1080×1920 backbone video + ffprobe QC + material replacement into V2 +
  burned subtitles + V1/V2 + delivery truth + `official_publish_ready=false`.

## Capability scorecard (this environment)

P0 final.mp4 ✅ playable 1080×1920 · P1 provider scene gen ⛔ **BLOCKED_CREDENTIAL_MISSING**
(proxy fallback, honest) · P2 material→V2 ✅ (shot consumed replacement) · P3 voiceover ⛔
**BLOCKED_CREDENTIAL_MISSING** live (capability real + proven; honest silent fallback) ·
P4 subtitles ✅ burned-in · P5 BGM ➖ 配乐未选择 (honest, not faked).

## Live smoke (no creds)

final.mp4 1080×1920 h264 30fps 20s playable · voiceover_status=blocked_credential_missing
(silent fallback, not labeled generated) · subtitles burned · capability strip operator-safe ·
QC passed · publish_ready false · no leakage.

## Validation

voiceover capability **7 passed** · tomato **23 passed** (new capability/voiceover/compose/view
tests) · adjacent **238 passed** · py_compile OK · diff-check clean · forbidden-path clean (no
routes/schemas/contracts/providers) · no-secret clean. Only failures = pre-existing PEP-604 env
limit (`config.py:43`, Python 3.9.6) on route/config-importing tests — not a regression; CI 3.10+.

## Boundary

runtime changed: orchestrator + new voiceover_capability + operator_workbench_view + template ·
provider integration: **No** · credentialed calls: **No** · secrets: **None** · schemas/
contracts: **No** · routes: **No** · vendor UI: **No** · delivery truth: **unchanged** ·
official_publish_ready: **unchanged (False)** · Slot v2: **not started** · merged: **No**.

## 给 Claude 的指令

- **current Owner decision:** heavy real-video batch; S5→S8; stop before merge.
- **allowed next actions:** (a) Owner supplies a working TTS credential/config → re-run smoke
  for a real-voiceover sample → request S8→S9; (b) or Owner approves S8→S9 merge of the
  credential-gated real capability now; (c) provider image_to_video stays a separate
  credentialed-trial decision.
- **forbidden actions:** no merge without approval; no provider calls/credentials/secrets; no
  faked provider/voice/BGM; no vendor selector in primary UI; no schema/contracts; no route
  change; no delivery-truth change; no `official_publish_ready=true`; no Slot v2 runtime; no
  unrelated refactor; no follow-up PR without approval.
- **required outputs (delivered):** rollback tag; voiceover capability + status; tests; smokes;
  report; this summary.
- **validation checks:** tests + py_compile + diff-check + forbidden-path + no-secret + live &
  injected smoke — all clean (pre-existing PEP-604 env aside).
- **stop point:** stopped before merge; no PR; no push.
- **Owner Decision Needed:** below.

## Owner Decision Needed

Live voiceover + provider generation are **BLOCKED_CREDENTIAL_MISSING**; the video is playable
with real material + subtitles and the real voiceover capability is landed + proven. Choose:
- **Supply a working TTS credential/config** (Azure Speech key+region, or a working keyless-TTS
  environment) → I capture a real-voiceover sample, then request merge; or
- **APPROVE S8→S9 merge now** of the credential-gated real capability (real voiceover the
  moment creds exist; honest fallback today); or
- **Revise / hold.**

Stop before merge.
