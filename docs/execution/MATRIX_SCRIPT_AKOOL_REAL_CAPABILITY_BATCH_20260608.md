# Matrix Script Akool Real Capability Batch Report

Status: **Heavy Fast Lane S5→S8 executed; merge-ready PR opened; STOPPED BEFORE MERGE** per
the Owner stop condition "Akool call fails with real provider error" (the live Akool job
returned FAILED on the test image). Headline: **real Azure voiceover SUCCEEDED** end-to-end;
the **Akool capability is wired + live-create-validated** (real API returned a QUEUED task id);
the full local Akool clip was blocked by (a) a real provider processing failure on an arbitrary
test image and (b) the pre-existing Python 3.9.6 `artifact_storage` import limit for hosting the
real still. `final.mp4` is playable with real voiceover + honest Akool fallback.

## 1. PR / Branch / Tag
- rollback tag: `matrix-script-before-akool-real-capability-20260608` → `5d6c4402` (pushed)
- PR: opened, **NOT merged** (stop-before-merge)
- branch: `feat/matrix-script-akool-real-capability-20260608`
- commit: Akool real capability commit on the branch

## 2. Owner Goal
- why the previous baseline failed operator acceptance: silent video, provider generation
  treated as missing.
- what real capability this batch adds: a real **Akool `image_to_video`** backend capability
  provider (capability kind, not a UI vendor selector) wired into the operator path with a live
  HTTP transport + bounded poll + download + normalize, plus honest per-shot status; AND real
  **Azure voiceover** now actually runs (credentials present) — the final.mp4 carries real
  narration.
- why this is not another ffmpeg micro-PR: it integrates a real external generative provider
  (Akool) by capability kind, with credential handling, async job polling, and an honest
  per-shot status taxonomy — proven against the live Akool API.

## 3. Credential Handling
- credential source: `~/.apolloveo/apolloveo-auto.env`, loaded with `set -a; source …; set +a`
  into the process environment only.
- name-only probe (no values): **SET** — `AKOOL_API_KEY`, `AKOOL_API_BASE_URL`,
  `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `GEMINI_API_KEY`. (Akool uses key-auth; no
  CLIENT_ID/SECRET — matches the existing `AKOOL_LOGICAL_TO_ENV` mapping, so **no env-name
  resolver was needed**.)
- env-name resolver: not required — the existing canonical mapping already maps
  `akool.api_key→AKOOL_API_KEY`, `akool.base_url→AKOOL_API_BASE_URL`.
- secret redaction: the api key lives only on the outgoing `x-api-key` header (built by the
  existing `AkoolClient`); never returned/logged/stored. Diagnostics carry a redacted CLASS only
  (e.g. `provider:invalid_request`, `provider_status_failed`, `err:TypeError`).
- no-secret scan: clean (only fake test literal `"k"`).

## 4. Capability Integration
- script / shot plan: unchanged fixed tomato plan (5 shots).
- material replacement: preserved (#212 `material_overrides` → backbone).
- image_to_video (Akool): **new** `akool_image_to_video_capability.py` — host still as a public
  URL (Apollo artifact storage) → `AkoolClient.create_task(IMAGE_TO_VIDEO,{image_url,prompt})` →
  bounded poll `read_task_result` → download temp output → normalize to 1080×1920/30fps. Gated
  behind `MATRIX_SCRIPT_AKOOL_REAL` + key presence; one designated shot (`shot02`) per run to
  bound cost.
- voiceover: real Azure TTS via the prior `voiceover_capability` (creds now present) → **生成成功**.
- subtitles: burned-in (preserved).
- BGM: honest 配乐未选择.
- compose / manifest / QC: ffmpeg compose + additive manifest evidence + ffprobe QC (passed).
- Workbench: capability-status strip (image_to_video / voiceover / subtitles / bgm) surfaced
  (from the prior batch; image_to_video now reflects the real Akool per-shot status).

## 4b. Live Akool validation (real API)
- **`create_task(IMAGE_TO_VIDEO, {image_url, prompt})` → real provider task id, status QUEUED.**
  Credential valid, endpoint contract correct (`/api/open/v4/image2Video/createBySourcePrompt`),
  transport + auth header work against the live API. (Redacted: no key/url/task-id surfaced.)
- Full one-shot on an arbitrary public test image → job processed and returned **FAILED**
  (`provider_status_failed`) — a real provider-side processing failure on a non-product test
  image, not a credential/endpoint/wiring defect.
- The orchestrator's real still could not be hosted locally: `artifact_storage` import raises on
  **Python 3.9.6** (`config.py:43` `str | None`, PEP-604) — the same env limit affecting the
  route tests all along; on Python 3.10+ (deploy/CI) hosting works and the real still feeds Akool.

## 5. Generated Result (live smoke)
- task id: `ms-real-001`
- final.mp4: produced, ~5.46 MB, non-empty · duration 20.0s · resolution 1080×1920 · h264/30fps
  · **playable**
- scene clips: 5 (shot02 attempted Akool → real provider FAILED → honest backbone-proxy fallback;
  all 5 `provider_image_to_video`-attempted-or-backbone proxies)
- provider-generated clips: 0 locally (real provider processing failure + 3.9.6 hosting limit)
- fallback clips: 5 backbone proxies (honest)
- voiceover audio: **real Azure TTS** (`audio_mode=azure_tts`, mean_volume −20.8 dB = real
  narration, `voiceover_status=generated`, 旁白已生成)
- subtitles: burned-in · BGM: not selected (honest)
- manifest: scene_engine + per_shot_render + qc + capability_status + voiceover_status
- QC: passed (1080×1920 / h264 / 30fps / duration_fit)

## 6. Provider Video Result
- provider attempted: Akool image_to_video (one shot, `shot02`)
- shots attempted: 1 · successful clips: 0 (local) · failed clips: 1
- create call: **succeeded (QUEUED)** — live API validated
- processing: **FAILED** on the test image (`provider_status_failed`); real still not hostable on
  3.9.6
- latency: create ~sub-second; poll bounded ≤ 240s
- estimated cost: ~1 image_to_video job (well under any USD 30 cap)
- failure modes (redacted): `provider_status_failed` (job processing) + `err:TypeError` (local
  `artifact_storage` import on Python 3.9.6). No credential/auth/quota error.

## 7. Browser / Operator Smoke
- URL: `GET /tasks/{task_id}` (Workbench `<video>` + `data-role="ms-capability-status"` strip),
  served by the existing preview route.
- main video visible / playable: yes / yes (1080×1920 h264 30fps 20s)
- voice status: 旁白已生成 (real Azure narration audible; mean_volume −20.8 dB)
- provider generation status: AI 视频生成未成功 · 已回退本地兜底 (honest)
- material trace / V1·V2: preserved · delivery candidate: safe · official_publish_ready: **false**
- leakage check: capability/status surfaces carry operator-safe Chinese labels + closed status
  enums only; no local_path / token / secret / raw manifest / vendor brand (render mode token is
  the vendor-agnostic `provider_image_to_video`).
- screenshots: not captured — the app cannot start locally on Python 3.9.6 (`config.py:43`); the
  surface is verified via rendered context + DOM markers + the served route.

## 8. Code Review
- verdict: **PASS** (self-review)
- scope compliance: only allowed paths — new `gateway/app/services/matrix_script/akool_image_to_video_capability.py`
  + orchestrator wiring + Matrix Script tests. Existing `providers/akool`, `capability/adapters`,
  `workers/*` are **imported, not modified**.
- provider/credential handling: gated, presence-only checks, key only on the outgoing header;
  redacted diagnostics; no secret in repo/log/manifest/operator payload.
- schema/contract check: none. route check: none (existing preview route reused).
- delivery truth: unchanged. publish readiness: stays false.
- test adequacy: 7 Akool capability tests (gate, success, failed, timeout, policy_blocked,
  no-leak) with injected transport/host/download; orchestrator capability_status reflects the
  real Akool result; voiceover + tomato suites green.

## 9. Operator Trial
- verdict: **PASS WITH ISSUES** — operator-usable; provider clip issue remains.
- operator usability: playable 1080×1920 video with **real voiceover** + burned subtitles +
  material trace + V1/V2 + honest capability status.
- result quality: rough proxies for visuals (Akool clip not produced locally); real narration.
- acceptable issues: Akool clip absent locally (real provider processing failure on test image +
  3.9.6 hosting limit) — honestly reported, backbone fallback.
- blockers (per stop conditions): a real Akool provider error occurred → stop before merge.

## 10. Validation
- focused tests: Akool capability 7 + voiceover 7 + akool_real_gate — pass.
- adjacent tests: tomato + backbone + operator workbench flow = **104 passed** (4 = pre-existing
  PEP-604 route limit).
- py_compile: `gateway/app/main.py` + touched modules → OK.
- diff check / forbidden-path scan / no-secret scan: clean.
- worktree: branch as above; live artifacts in `/tmp` scratch (not committed).

## 11. Boundary
- provider calls: **Yes** (Akool create validated live; one bounded job)
- credentials: used from env only (never committed/printed)
- secrets committed: **No**
- schemas/contracts: **No** · routes: **No** · vendor UI: **No**
- delivery truth: **unchanged** · official_publish_ready: **false** · Slot Workflow v2: **not started**

## 12. Verdict

**PASS WITH ISSUES BUT OPERATOR-USABLE.** The final.mp4 is playable with **real Azure voiceover**
+ burned subtitles + honest capability status; the **Akool image_to_video capability is wired and
validated against the live API** (real create → QUEUED). The full Akool clip was not produced
locally due to a real provider processing failure on an arbitrary test image plus the Python
3.9.6 `artifact_storage` hosting limit — both environmental/test artifacts, expected to resolve on
the Python 3.10+ deploy/CI runtime with the real hosted still. Per the Owner stop condition
("Akool call fails with real provider error"), **stopped before merge.**

## 给 Claude 的指令
- **current Owner decision:** S5→S9 Akool real capability; one continuous run; stop only on a
  hard boundary — a real Akool provider error occurred, so stopped before merge.
- **allowed next actions:** (a) on Owner go → merge the capability (sound + live-create-validated;
  runs on 3.10+ deploy) and run a deploy/CI smoke that hosts the real still; or (b) run the smoke
  in a Python 3.10+ environment first to capture a real Akool clip, then merge.
- **forbidden actions:** no secrets in repo/logs/docs/manifest; no faked provider/voice/BGM; no
  vendor selector in primary UI; no schema/contracts; no route change; no delivery-truth change;
  no `official_publish_ready=true`; no Slot v2 runtime; no unrelated refactor; no merge without
  Owner go (stop condition triggered).
- **required outputs (delivered):** rollback tag; Akool capability + orchestrator wiring; tests;
  live smoke (real voiceover success + Akool create validated + honest failure); this report; the
  Owner Summary.
- **validation checks:** focused + adjacent tests, py_compile, diff-check, forbidden-path,
  no-secret, live credentialed smoke — all run.
- **stop point:** stopped before merge (PR opened, merge-ready).
- **Owner Decision Needed:** below.

## 13. Owner Decision Needed

`final.mp4` is playable with real voiceover; the Akool capability is wired and **validated
against the live API** (create → QUEUED), but the full local clip hit a real provider processing
failure (arbitrary test image) + the Python 3.9.6 hosting limit. Choose:
- **APPROVE merge** of the Akool capability (sound + live-validated; will host the real still and
  run the Akool job on the Python 3.10+ deploy/CI runtime), then run a deploy smoke to capture a
  real Akool clip; or
- **Run the smoke on a Python 3.10+ runtime first** (so the real tomato still is hosted and the
  Akool job uses the correct product image) before merging; or
- **Revise / hold.**

Stop before merge. No unrelated follow-up PR.
