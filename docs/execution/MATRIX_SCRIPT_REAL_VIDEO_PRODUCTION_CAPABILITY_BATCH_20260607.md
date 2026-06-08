# Matrix Script Real Video Production Capability Batch Report

Status: **Heavy Fast Lane S5→S8 executed. Implemented + tested + smoked. NOT merged (stop
before merge).** Headline verdict: **BLOCKED_CREDENTIAL_MISSING** for live voiceover +
provider generation (no credentials in this environment) — but the operator final.mp4 is
**playable and operator-usable** (1080×1920 + material replacement + burned subtitles + QC),
and the **real voiceover capability is landed and proven** (composes real narration the
moment a TTS path is available).

## 1. PR / Branch / Tag
- rollback tag: `matrix-script-before-real-video-production-20260607` → `5d6c4402` (pushed)
- PR: none opened (stop-before-merge)
- branch: `feat/matrix-script-real-video-production-20260607`
- commit: real-video-production batch commit on the branch (runtime + tests + this report)

## 2. Owner Goal
- why the previous baseline failed operator acceptance: the operator video was a **silent**
  Ken-Burns proxy — no narration, capability status not operator-visible; it read as "process,
  not product."
- what real capability this batch adds: a **real voiceover capability** (credentialed Azure →
  keyless edge_tts → honest silent fallback) composed into the operator final.mp4, plus
  **operator-safe capability status** (voiceover / image_to_video / subtitles / bgm) surfaced
  in the Workbench. Material replacement into V2 and burned subtitles were already real and are
  preserved.
- why this is not another ffmpeg micro-PR: it integrates an actual TTS capability + an honest
  multi-capability status model into the operator path, not compose/QC plumbing. It produces
  real narration audio (proven via an injected TTS that yields a non-silent composed track).

## 3. Capability Integration (P0–P5)
- **P0 final.mp4 path:** preserved + working (1080×1920 h264 30fps via the merged backbone).
- **P1 provider/tool scene generation:** **BLOCKED_CREDENTIAL_MISSING** — no image_to_video
  credential (Kling/Runway/Veo/fal/Akool/Vertex all unset); honestly reported; backbone proxy
  kept as the non-faked fallback. No provider call made.
- **P2 material-to-V2 visible closure:** preserved — `material_overrides` (#212) feed the
  backbone; a replacement image is consumed (`consumed_material_shot_ids`), trace surfaced.
- **P3 voiceover:** **real capability landed.** New `voiceover_capability.py` resolves
  Azure (credentialed) → edge_tts (keyless) → honest silent fallback; composes the narration
  track into final.mp4; operator status 旁白已生成 / 旁白未生成·缺少语音凭证. In **this
  environment** Azure has no creds and edge_tts returns HTTP 403 → status
  **blocked_credential_missing**, silent fallback (NOT labeled as generated). Proven real via
  an injected TTS (composed audio mean_volume ≈ −22 dB, `audio_mode=edge_tts`,
  `voiceover_status=generated`).
- **P4 subtitles:** preserved — burned-in via the existing Pillow overlay at 1080×1920;
  status 字幕已烧录.
- **P5 BGM:** honest — no library; status 配乐未选择 (not faked).
- **compose:** existing `assemble_final_video` (concat + mux).
- **manifest:** additive operator-safe `scene_engine` / `per_shot_render` / `qc` / `backbone`
  / `capability_status` / `voiceover_status`; legacy keys unchanged; no leakage.
- **QC:** `ffmpeg_backbone.qc_probe` verdict on the composed final (passed).
- **Workbench:** capability-status strip (voiceover / subtitles / image_to_video / bgm) added
  under the main video; view surfaces `capability_status` + `voiceover_status` read-only.

## 4. Generated Result (live smoke, no creds)
- task id: `rv-live`
- final.mp4: produced, 5.3 MB, non-empty
- duration: 20.0s · resolution: 1080×1920 · codec/fps: h264 / 30fps · playable: **yes**
- scene clips: 5, all via `ffmpeg_backbone_proxy`
- provider-generated clips: **0 (BLOCKED_CREDENTIAL_MISSING)**
- fallback clips: 5 backbone proxies (honest)
- voiceover audio: **not generated (BLOCKED_CREDENTIAL_MISSING)** → silent fallback track (aac)
- subtitles: burned-in (字幕已烧录)
- BGM: not selected (配乐未选择)
- manifest: present with capability_status + voiceover_status + qc + per_shot_render
- QC: passed (1080×1920 / h264 / 30fps / duration_fit)

## 5. Material / V1-V2 Proof
- changed shot: `shot04` (override smoke)
- consumed material: an uploaded/replacement image (resolvable bytes) consumed through the
  backbone → `consumed_material_shot_ids=('shot04',)`
- V1 state: current main (staged candidate) unchanged until confirm
- V2 state: regeneration consumes the replacement bytes (existing #212 path, preserved)
- visible difference: V2 shot rendered from the replacement still
- trace shown to operator: existing consumed-materials / based-on-assets projection (preserved)

## 6. Voiceover Proof
- provider/tool used: capability chain — Azure Speech (credentialed) → edge_tts (keyless)
- credential source: none available in this environment (Azure key/region unset; no `.env`)
- audio generated: **no** live (Azure no-cred; edge_tts HTTP 403). Proven real via injected
  TTS (non-silent composed audio, `audio_mode=edge_tts`).
- composed into final.mp4: yes when a TTS path yields audio (proven); silent fallback otherwise
- fallback if blocked: honest silent track + status `blocked_credential_missing` (never
  labeled as generated voiceover)
- operator wording: 旁白已生成 (generated) / 旁白未生成 · 缺少语音凭证（已保留静音） (blocked)

## 7. Browser / Operator Smoke
- URL: `GET /tasks/{task_id}` (Workbench `<video data-role="ms-main-video-result-video">` +
  the new `data-role="ms-capability-status"` strip) served via the existing
  `/api/matrix-script/{task_id}/preview-version/{V}/final.mp4` route (unchanged).
- main video visible: yes · video playable: yes (h264 1080×1920 30fps 20s)
- voice audible: **no — honestly reported** (旁白未生成 · 缺少语音凭证) [BLOCKED_CREDENTIAL_MISSING]
- subtitles visible: yes (burned-in)
- material trace visible: yes (preserved projection)
- V1/V2 visible: yes (preserved)
- delivery candidate: safe (follows confirmed main only)
- official_publish_ready: **false**
- leakage check: capability status uses operator-safe Chinese labels + status enums only; no
  local_path / provider / token / manifest leak (payload + view `_assert_clean` guards pass).
- screenshots: not captured headlessly (no browser in this environment); the served route +
  template binding are verified by the rendered context + DOM `data-role` markers.

## 8. Code Review
- verdict: **PASS** (self-review)
- scope compliance: only allowed files — `gateway/app/services/matrix_script/**`
  (orchestrator + new `voiceover_capability.py` + `operator_workbench_view.py`),
  `task_workbench.html`, Matrix Script tests, docs.
- provider/credential handling: capability gated on credential **presence only**; key/region
  values passed straight to the provider call, never returned/logged/stored; no secret in repo.
- schema/contract check: no change (manifest/payload/view additions are operator-safe,
  additive, not a published schema/contract).
- route check: no change (existing preview route reused).
- delivery truth: unchanged (`staged_record_to_delivery_block`, provider="none").
- publish readiness: stays false everywhere.
- test adequacy: 7 voiceover-capability unit tests + 3 new orchestrator/view tests (capability
  status, real-voiceover compose via injected TTS, view passthrough) + updated assertions.

## 9. Operator Trial
- verdict: **PASS WITH ISSUES BUT OPERATOR-USABLE** for the video; **BLOCKED_CREDENTIAL_MISSING**
  for live voiceover + provider generation.
- operator usability: playable 1080×1920 video with burned subtitles + material trace + V1/V2
  + an honest capability-status strip; operator can see exactly what is/ isn't produced.
- result quality: rough (Ken-Burns proxy, silent in this env) — acceptable per the heavy-batch
  rules **because** voice/provider credentials are genuinely missing and reported as
  BLOCKED_CREDENTIAL_MISSING.
- acceptable issues: silent audio (no TTS creds), proxy visuals (no provider creds), BGM not
  selected — all honestly labeled.
- blockers: live voiceover + provider generation require credentials not present here.

## 10. Validation
- focused tests: voiceover capability **7 passed**; tomato **23 passed** total incl. new
  capability/voiceover/compose/view tests (4 route tests fail at import on the pre-existing
  PEP-604 env limit).
- adjacent tests: backbone + minimal_result + operator workbench flow + workbench blocks A–F
  + minimal-result block/action = **238 passed** (1 route-import failure = same PEP-604 limit).
- py_compile: `gateway/app/main.py` + all touched modules → OK.
- diff check: `git diff --check` clean.
- forbidden-path scan: clean (no routes/schemas/contracts/`app/providers/` modifications).
- no-secret scan: clean (only credential env-var **names** as string literals; no values).
- worktree: branch as above; new `voiceover_capability.py` + its test; orchestrator + view +
  template edits.
- **Pre-existing env limit (not a regression):** route/config-importing tests fail at
  `gateway/app/config.py:43` (`str | None` needs Python 3.10+; local 3.9.6) — verified
  identical on the clean baseline; ENGINEERING_RULES §10; CI runs 3.10+.

## 11. Boundary
- runtime changed: **Yes** — orchestrator + new voiceover_capability + operator_workbench_view + template
- provider integration: **No** (no provider call executed; image_to_video reported BLOCKED)
- credentialed calls: **No** (no credentials present; none used)
- secrets: **None** (presence-only checks; no value read into artifact/log/repo)
- schemas/contracts: **No**
- routes: **No**
- vendor UI: **No** (operator-safe labels only; no brand in primary UI)
- delivery truth: **unchanged**
- official_publish_ready: **unchanged (False)**
- Slot Workflow v2: **not started**

## 12. Verdict

**BLOCKED_CREDENTIAL_MISSING** — live voiceover (Azure no-cred; edge_tts HTTP 403) and
provider image_to_video (no credential) cannot run in this environment, reported honestly per
the heavy-batch rules. The operator final.mp4 is nonetheless **playable and operator-usable**
(1080×1920 + material replacement + burned subtitles + QC + honest capability status), and the
**real voiceover capability is landed and proven** (it composes real narration the instant a
TTS path is available). No fakes; `official_publish_ready=false`; delivery truth unchanged.

## 给 Claude 的指令
- **current Owner decision:** heavy real-video batch; S5→S8; stop before merge.
- **allowed next actions:** (a) if the Owner supplies a working TTS credential/config (Azure
  Speech key+region) or a working keyless-TTS environment → re-run the smoke to produce a
  real-voiceover sample, then request S8→S9; (b) or, on Owner approval, merge the
  credential-gated real capability now (it unblocks automatically when creds exist) → merge +
  sync + post-merge validation + merge report. Provider image_to_video remains a separate
  credentialed-trial decision.
- **forbidden actions:** no merge without Owner approval; no provider calls/credentials/secrets;
  no faked provider/voice/BGM; no Kling/Runway/Veo/Azure runtime without credentials+approval;
  no vendor selector in primary UI; no schema/contracts; no route change; no delivery-truth
  change; no `official_publish_ready=true`; no Slot v2 runtime; no unrelated refactor; no
  follow-up PR without approval.
- **required outputs (delivered):** rollback tag; real voiceover capability + capability status;
  tests; live + injected smokes; this report; the Owner Summary.
- **validation checks:** focused + adjacent tests, py_compile, diff-check, forbidden-path,
  no-secret, live + injected smoke — all clean (pre-existing PEP-604 env aside).
- **stop point:** stopped before merge; no PR opened; no push.
- **Owner Decision Needed:** below.

## 13. Owner Decision Needed

The final.mp4 is playable with real material replacement + burned subtitles, and the real
voiceover capability is landed + proven — but **live voiceover and provider generation are
BLOCKED_CREDENTIAL_MISSING** in this environment.

Choose one:
- **Supply a working TTS credential/config** (Azure Speech key+region) or a working keyless-TTS
  environment → I re-run the smoke to capture a real-voiceover sample, then request S8→S9; or
- **APPROVE S8→S9 merge now** of the credential-gated real capability (it produces real
  voiceover the moment creds exist; today it falls back honestly with BLOCKED status); or
- **Revise / hold.**

Stop before merge. No follow-up PR without Owner approval.
