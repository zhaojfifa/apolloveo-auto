# Owner Summary — Matrix Script Akool Provider Mode Production Smoke (2026-06-08)

Docs companion. Not authority; the smoke report governs.

Report: `docs/execution/MATRIX_SCRIPT_AKOOL_PROVIDER_MODE_PRODUCTION_SMOKE_20260608.md`

## Headline

**PASS — Akool provider mode proven end-to-end.** A real Akool image2Video clip was generated
from the tomato-beach still and consumed into an operator-visible `final.mp4`:
- **shot02 = real Akool clip** (`render_mode=provider_image_to_video`, status `provider_success`,
  「AI 视频生成已生成此镜头」) — not an ffmpeg proxy.
- shot01/03/04/05 = honest backbone-proxy fallback.
- **real Azure voiceover** (`azure_tts`, −20.8 dB, 旁白已生成) + burned subtitles.
- 1080×1920 h264 30fps 20s, ffprobe QC passed, playable, `official_publish_ready=false`, no leakage.

## How the local blocker was cleared

- Ran the live smoke on **python3.11** (default 3.9.6 can't import `artifact_storage` →
  config.py:43 PEP-604).
- Hosted the real still via the **existing ApolloVeo artifact path** (composition root
  `create_storage_service()` in R2/s3 mode → presigned URL Akool fetches). No new uploader; no
  local path sent to the provider.
- One narrow contract fix (allowed "existing Akool provider capability file"):
  `providers/akool/client.py` `_OUTPUT_FIELDS[IMAGE_TO_VIDEO]` **`video_url`→`video`** — the real
  image2Video result returns the clip URL in `data.video` on `video_status==3`. This was the only
  reason the earlier attempt said `success_no_output`.

## Cost

Akool image2Video = **100 credits/job** (`deduction_credit`). The smoke ran a bounded handful of
jobs (diagnostic + one-shot + full orchestrator) on the Owner's Akool Max Pro plan; USD 30 cap
respected.

## Validation

Akool capability + akool_real_gate + voiceover + backbone = **68 passed** (injected transport;
no network in tests); tomato/operator suite re-run; py_compile OK; diff-check / forbidden-path /
no-secret clean. Changed files: `providers/akool/client.py` (1-line contract fix) + 2 test
updates (`video_url`→`video`) + this report/summary. No routes/schemas/contracts modified.

## Boundary

provider calls: **Yes** (bounded) · credentials: env-only, never committed/printed · secrets
committed: **No** · schemas/contracts/routes: **No** · vendor UI: **No** · delivery truth:
**unchanged** · official_publish_ready: **false** · Slot v2: **not started**.

## 给 Claude 的指令

- **current Owner decision:** Akool provider mode = primary; produce one operator-visible
  final.mp4 with ≥1 Akool shot — **achieved**.
- **allowed next actions:** on Owner go → merge the contract-fix PR + run the queued Deploy/CI
  smoke (Python 3.10+) to reproduce in the deployed runtime; optionally a 2nd Akool shot.
- **forbidden actions:** no local-only ffmpeg micro-PR; no provider selector in UI; no secrets in
  repo/logs/docs; no schema/contracts/routes unless separately approved; no
  `official_publish_ready=true`; no Slot v2 runtime; no unrelated cleanup; no merge without go.
- **required outputs (delivered):** real Akool clip + operator final.mp4; contract fix + tests;
  report; this summary.
- **validation checks:** tests + py_compile + diff-check + forbidden-path + no-secret + live smoke
  + ffprobe QC — all run.
- **stop point:** stopped after this report; PR merge-ready, not merged.
- **Owner Decision Needed:** below.

## Owner Decision Needed

Akool provider mode is proven (final.mp4 has a real Akool shot + real voiceover). Choose:
- **Accept as the Matrix Script operator pilot baseline + merge** the one-line contract fix so
  provider mode works for all runs, then run the Deploy/CI smoke; or
- **Run the Deploy/CI smoke first** (deployed Python 3.10+ runtime) before accepting; or
- **Revise / hold.**

Stop after report.
