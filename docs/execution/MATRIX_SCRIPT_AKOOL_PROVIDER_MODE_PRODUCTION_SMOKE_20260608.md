# Matrix Script Akool Provider Mode Production Smoke Report

Status: **PASS — a real Akool provider clip was generated and consumed into an operator-visible
final.mp4.** Akool is now exercised in provider mode as the primary Matrix Script real video
provider. A merge-ready PR carries one narrow contract fix; **stopped before merge** pending
Owner go.

## 1. Environment
- runtime: local macOS, **python3.11** (3.11.15) for the live smoke (the default python3.9.6
  cannot import `artifact_storage` → `config.py:43` PEP-604; 3.11 imports it cleanly).
- main HEAD: `134b551f` (#247 Akool capability merged).
- env presence (names only, no values): **SET** — `AKOOL_API_KEY`, `AKOOL_API_BASE_URL`,
  `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `STORAGE_BACKEND=s3`, `R2_BUCKET`, `GEMINI_API_KEY`.
- input hosting method: the **existing ApolloVeo artifact path** — composition root
  `create_storage_service()` (R2/s3 mode) + `set_storage_service()`, then
  `artifact_storage.upload_artifact` + `get_download_url` → a presigned R2 URL Akool can fetch.
  No new uploader; no local path sent to the provider.
- cost cap: USD 30 smoke cap respected. Akool image2Video bills **100 credits/job**
  (`deduction_credit: 100`); this smoke ran a bounded handful of jobs (diagnostic + 1 one-shot +
  1 full orchestrator) on the Owner's Akool Max Pro plan.

## 2. Akool Provider Run
- shot id: `shot02` (product close-up — tomato bowl).
- input asset: `assets/matrix_script_assets/MS-TOMATO-BEACH-001/02_tomato_bowl.png`, hosted via
  the artifact path as a presigned R2 URL (not a local path).
- prompt: "product close-up of fresh cherry tomatoes in a bowl, gentle camera push-in, natural
  sunlight, vertical 9:16".
- task created: **yes** (real provider task id; status lifecycle 1→2→3).
- final provider status: **SUCCESS** (`video_status==3`).
- output clip downloaded: **yes** — the result URL is returned in the `video` field; downloaded +
  normalized to 1080×1920/30fps h264. Standalone clip: `h264,1080,1920,30/1, 5.07s, 2.96 MB`.
- latency: create sub-second; total to SUCCESS ≈ 40–60s (one poll interval).
- cost estimate: ~100 credits for the consumed shot (per `deduction_credit`).
- failure class if any: none for the consumed shot.

### Contract fix applied (allowed: existing Akool provider capability file)
`gateway/app/services/providers/akool/client.py` — `_OUTPUT_FIELDS[IMAGE_TO_VIDEO]` corrected
from `"video_url"` to **`"video"`** (verified against the live API: on `video_status==3` the
generated clip URL is in `data.video`, not `data.video_url`). This is the only reason the prior
local attempt reported `success_no_output`. No other client change; no schema/route/contract
change. The v3 `infobymodelid` read endpoint is correct for image2Video and was unchanged.

## 3. Final Video
- final.mp4: `/tmp/ms_akool_final.mp4` (operator path artifact), **5.96 MB**.
- Akool clips included: **1** (`shot02` → `render_mode=provider_image_to_video`).
- fallback clips: 4 (`shot01/03/04/05` → `ffmpeg_backbone_proxy`, honest per-shot).
- Azure voiceover: **real** (`audio_mode=azure_tts`, mean_volume −20.8 dB = real narration,
  `voiceover_status=generated`, 旁白已生成).
- subtitles: burned-in (caption_mode burned_in).
- duration: 20.0s · resolution: 1080×1920 · codec/fps: h264/30fps.
- QC: **passed** (ffprobe — resolution/codec/fps/duration_fit).
- playable: **yes**.

## 4. Operator Evidence
- Workbench URL: `GET /tasks/{task_id}` (`<video data-role="ms-main-video-result-video">` +
  `data-role="ms-capability-status"` strip), served by the existing preview route.
- video visible / playable: yes / yes.
- capability status: image_to_video **provider_success** (「AI 视频生成已生成此镜头」); voiceover
  **generated** (旁白已生成); subtitles 字幕已烧录; bgm 配乐未选择.
- per-shot trace: `shot02 = provider_image_to_video`; others `ffmpeg_backbone_proxy`.
- material trace / V1·V2: preserved · delivery candidate: true · official_publish_ready: **false**.
- screenshots/evidence: not captured headlessly (app start blocked on py3.9.6 locally); evidence
  is the produced final.mp4 + ffprobe + manifest `per_shot_render` + capability_status.
- leakage check: operator surfaces carry operator-safe Chinese labels + closed status enums +
  the vendor-agnostic `provider_image_to_video` token only — no API key / token / local_path /
  raw Akool URL / vendor brand / raw manifest. (Akool URL/key live only on the wire + in the
  client header; redacted everywhere else.)

## 5. Boundary
- provider calls: **Yes** (Akool image2Video, provider mode, bounded).
- credentials: from `~/.apolloveo/apolloveo-auto.env` into the process only; never committed/printed.
- secrets committed: **No**.
- schemas/contracts: **No** · routes: **No** · vendor UI: **No** (no provider selector).
- delivery truth: **unchanged** · publish readiness: **false**.

## 6. Verdict

**PASS — Akool provider clip E2E proven.** A real Akool image2Video clip (`shot02`) was generated
from the tomato-beach still (hosted via the existing artifact path), downloaded, normalized, and
consumed into an operator-visible 1080×1920 final.mp4 alongside real Azure voiceover + burned
subtitles + honest per-shot fallback for the other shots. QC passed; publish-ready false; no
leakage; one narrow allowed contract fix (`video_url`→`video`).

## 给 Claude 的指令
- **current Owner decision:** Akool provider mode = primary; produce one operator-visible
  final.mp4 with ≥1 Akool-generated shot — achieved.
- **allowed next actions:** on Owner go → merge the contract fix PR (so Akool provider mode works
  for everyone) and proceed to the previously-queued Deploy/CI smoke (Python 3.10+) to capture
  the same result in the deployed runtime. Optionally extend Akool to a 2nd shot (lifestyle) if
  cost/latency acceptable.
- **forbidden actions:** no new local-only ffmpeg micro-PR; no provider selector in UI; no
  secrets in repo/logs/docs; no schema/contracts/routes unless separately approved; no
  `official_publish_ready=true`; no Slot v2 runtime; no unrelated cleanup; no merge without Owner go.
- **required outputs (delivered):** real Akool provider clip + operator final.mp4; contract fix +
  tests; this report; the Owner Summary.
- **validation checks:** Akool capability + akool_real_gate + voiceover + backbone tests (68
  passed); tomato/operator suite; py_compile; diff-check; forbidden-path; no-secret; live smoke +
  ffprobe QC — all run.
- **stop point:** stopped after this report; PR merge-ready, not merged.
- **Owner Decision Needed:** below.

## 7. Owner Decision Needed

Akool provider mode is **proven end-to-end**: `final.mp4` contains a real Akool-generated shot +
real voiceover, playable, publish-ready false, no leakage. Choose:
- **Accept this as the Matrix Script operator pilot baseline** + **merge** the one-line contract
  fix (`video_url`→`video`) so provider mode works for all runs, then run the Deploy/CI smoke; or
- **Run the Deploy/CI smoke first** (Python 3.10+ deployed runtime) before accepting; or
- **Revise / hold.**

(No blocker remains. The only fix needed — the output-field contract correction — is applied and
tested.)

Stop after report. No unrelated PR.
