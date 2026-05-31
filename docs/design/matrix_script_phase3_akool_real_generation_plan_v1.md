# Matrix Script Phase 3 — Akool Real Generation Design Plan v1

Date: 2026-05-31
Status: **Design / review document only. No code, no UI, no contract, no schema, no test, no template, no packet change in this artifact.** This is a Phase 3 engineering-planning document (L2-level). It proposes a future production-line shape and an Akool-as-L4 integration; it does **not** open any implementation gate. Real video generation remains gated behind the frozen next engineering sequence (see §8 + §11).
Branch: `phase3/matrix-script-akool-real-generation-design`
Baseline: `origin/main = f1a47b5f02c1fb2965868a1ae563c24b5527c458`

---

## 0. Governance Reading Declaration

### Root governance files read (boot sequence + index-first discipline)

- `CLAUDE.md` (bootloader / no-private-memory rule / native-state-ownership rule)
- `README.md`
- `PROJECT_RULES.md`
- `ENGINEERING_RULES.md` (§1–§13; especially §9 Factory Alignment Gate, §13 Product-Flow Module Presence)
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`

### Docs governance / index files read

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` (current wave, three-line status, frozen next engineering sequence §7, blocked scope §3.2)
- `docs/contracts/engineering_reading_contract_v1.md` (this declaration follows its template)

### Task-specific authority files read (selected through the indexes)

- `docs/execution/VEOMATRIXVOICE05_PHASE2D_INTEGRATION_REPORT_v1.md`
- `docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md`
- `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
- `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`
- `docs/execution/MATRIX_SCRIPT_PHASE2C_OPERATOR_READABILITY_VALIDATION_REPORT_v1.md`
- `docs/product/matrix_script_product_flow_v1.md`
- `docs/product/matrix_script_product_flow_v2_delta.md`
- `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
- `docs/donor/swiftcraft_capability_mapping_v1.md` (P-01/P-02/E-02 Akool absorption rows)
- Code surfaces: `gateway/app/services/capability/adapters/base.py`, `gateway/app/services/packet/envelope.py`, `gateway/app/services/providers/`, `gateway/app/services/workers/adapters/`, `gateway/app/services/voice_tool/`, `gateway/app/routers/voice_tool.py`, `gateway/app/services/compose_service.py`, `gateway/app/services/artifact_storage.py`, `gateway/app/services/worker_gateway.py`, `gateway/app/services/matrix_script/*`, the four named templates.
- External: Akool public API docs (`https://docs.akool.com/`) — authentication, talking photo/avatar, image2video, faceswap, lip sync, VoiceLab TTS, webhook, error-code.

### Why this set was sufficient

The task is a large Phase-3 design / L2-level planning artifact for one line (Matrix Script) plus one resource-layer provider (Akool). The boot sequence + the alignment map fix the wave gate; the Matrix Script design/product/contract-alignment set fixes the current line shape and its honest placeholders; the four-layer + delivery + capability-adapter code fixes the architecture boundaries Akool must respect; the Akool docs fix the provider's real capability/async/URL/webhook model. No broad raw authority set was read "just in case."

### Missing-authority handling

- `docs/execution/VEOMATRIXVOICE05_PRODUCTION_DOMAIN_SWITCH_REPORT_v1.md` — **was not found** at the cited path during reading.
- **Fallback authority used** (selected through the indexes; covers the production-domain posture the missing report would have carried):
  - `docs/execution/VEOMATRIXVOICE05_PHASE2D_INTEGRATION_REPORT_v1.md`
  - `docs/product/matrix_script_product_flow_v2_delta.md`
  - `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
- The design below does not depend on the missing file. Flag for the reviewer: confirm whether this report exists under a different name before implementation.

### Scope classification

- Large Phase 3 design / L2-level engineering planning. **No broad implementation in this step.** First and only output is this design/review document plus the structured report it mirrors. Implementation is gated (§8, §11).

---

## 1. Branch / Baseline State

| Item | Value |
| --- | --- |
| Phase 3 branch | `phase3/matrix-script-akool-real-generation-design` |
| origin/main | `f1a47b5f02c1fb2965868a1ae563c24b5527c458` |
| VeoMatrixVoice05 baseline | `517c6f8179a114fdf23e040730529a960402af12` |
| Debt branch (NO-TOUCH) | `debt/post-veomatrixvoice05-test-reconciliation` |

Work for Phase 3 starts only from `phase3/matrix-script-akool-real-generation-design`. Not from `VeoMatrixVoice05`, `main`, or the debt branch.

---

## 2. Current Wave Position (the decisive governance fact)

Per `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` §3 / §7 and `CURRENT_ENGINEERING_FOCUS.md`:

- The active mainline is the **Operator Workflow Convergence Wave (OWC)**; OWC-MS and OWC-DA are CLOSED, and the **Matrix Script Result-Capability Recovery Wave (RC PR-1..PR-4 + Closeout RC-A13)** is CLOSED.
- The **frozen next engineering sequence** is: Matrix Script follow-on trial re-entry review (docs-only) → Plan A live-trial Matrix Script execution → **Platform Runtime Assembly Wave** → **Capability Expansion Gate Wave**.
- **Real generation providers are Capability Expansion Gate Wave scope, specifically W2.3 (Avatar / VideoGen / Storage Provider).** That wave is **explicitly BLOCKED**, gated on Platform Runtime Assembly signoff, which is itself gated on Plan A live-trial closeout.
- The Matrix Script product-flow authorities are internally consistent with this: real main-video generation is repeatedly named as **"Phase 6 — Capability Expansion Wave"** and every operator surface today carries an honest `main_video_pending_capability` placeholder with **no fake `final_video`**.

**Therefore the binding reading of "Matrix Script Phase 3 Akool Real Generation" is:** this is the **design artifact that prepares** the line + the L4 provider absorption so that when the Capability Expansion Gate Wave opens, the implementation is contract-correct and four-layer-clean. **It is not authorization to wire real Akool generation now.** This document opens no gate (§8, §11). The recommendation in §10 is explicit about which sub-steps are docs-only-allowed vs gated.

This tension is surfaced, not hidden, per `ENGINEERING_RULES.md` §6/§8 and `PROJECT_RULES.md` ("不把 future-state 设计描述成已实现").

---

## 3. Current Matrix Script / VoiceTrans State (verified)

### 3.1 Matrix Script production line — what exists vs what is placeholder

```
script input
  → content structure (Hook/Body/CTA)         WIRED   (factory_content_structure; Phase B deterministic authoring)
  → variation plan (V1/V2/V3 versions)         WIRED   (metadata only — no real variant media)
  → scene plan / shot plan (storyboard)        PLACEHOLDER  (factory_scene_plan_contract exists; NO scene_plan_binding in MS packet)
  → visual / B-roll asset decision             PLACEHOLDER  (no Asset Supply bridge)
  → role / voice (presenter, narration)        PLACEHOLDER  (no VoiceTrans bridge into MS; voice-preview demoted to chip)
  → subtitle / music plan                      PLACEHOLDER  (no compose-worker style projection)
  → MAIN VIDEO GENERATION                       NOT WIRED   (main_video_pending_capability)
  → assembly → final.mp4                        HONEST EMPTY-STATE  ("当前尚未生成主视频", no fake media)
  → delivery contract                           PROJECTION ONLY (delivery_binding.py → artifact_lookup_unresolved sentinel)
  → publish / backfill                          GATED (publishable=false; no final_video)
```

- The **result-oriented workbench (Phase 2D)** is live: Section 1 主视频结果 (state pill 未生成/生成中/待审核/可交付 + blocker/next-action banner) → Section 2 生产流程可观测 (compact stepper) → Section 3 可选变体 → Section 4 交付入口 → Section 5 技术诊断 (collapsed). New-task CTA is 「生成视频方案」.
- **No fake `final_video` / `publish_url` / thumbnail** anywhere; a fidelity test asserts zero vendor names (azure/gemini/akool/seedance/openai/anthropic/elevenlabs) in operator-visible copy (`gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py`).
- Matrix Script services present: `create_entry.py`, `phase_b_authoring.py`, `delivery_binding.py` (Plan E B4 `artifact_lookup` → `artifact_lookup_unresolved` sentinel), `result_status_view.py`, `readable_variant_view.py`, `main_video_result_view.py`, `task_card_summary.py`, `source_script_ref_minting.py`, `source_script_body_store.py`.

### 3.2 VoiceTrans / voice_tool — real audio capability exists today

- `gateway/app/routers/voice_tool.py` (`/voice-tool`, `/api/voice-tool`) + `gateway/app/services/voice_tool/service.py`: real flow **text → Gemini translate → Azure Speech TTS → WAV/MP3 artifact** via `VoiceToolService` (`storage`, `translate_client`, `tts_func`). `gateway/app/providers/azure_speech.py::generate_audio_azure_speech()` performs the real synthesis. This is the **audio capability already available** to bridge into Matrix Script — it does NOT require Akool.

### 3.3 Capability adapter + provider layer — the L3/L4 boundary already exists

- `gateway/app/services/capability/adapters/base.py` defines the **closed adapter interface set**: `UnderstandingAdapter`, `SubtitlesAdapter`, `DubAdapter`, `VideoGenAdapter`, `AvatarAdapter`, `FaceSwapAdapter`, `PostProductionAdapter`, `PackAdapter` — each over `AdapterBase`, with `AdapterError` carrying a **closed `AdapterErrorCategory`** (INVALID_INVOCATION, UNAVAILABLE, TIMEOUT, CANCELLED, AUTH, RATE_LIMITED, UPSTREAM, INTERNAL) and `AdapterCredentials` (secret-resolver based, no I/O at `__init__`).
- `gateway/app/services/packet/envelope.py` `CAPABILITY_KINDS` (closed): `understanding, subtitles, dub, video_gen, avatar, face_swap, post_production, pack, variation, speaker, lip_sync`. These are the **L3 capability kinds operators are routed through** — never a vendor.
- Provider host dirs exist: `gateway/app/services/providers/` (only `gemini` absorbed) and worker adapters `gateway/app/services/workers/adapters/` (only `gemini`). The template to follow is `workers/adapters/gemini/understanding.py` → `GeminiUnderstandingAdapter` (resolves secret refs in `invoke()`, maps provider error → `AdapterError`).
- **Akool today = metadata only**: `gateway/data/tools_registry.json` (vendor + `AKOOL_API_KEY` secret ref), `envelope.py` vendor-id list, donor mapping `docs/donor/swiftcraft_capability_mapping_v1.md` P-01 (Akool client consolidation → `gateway/app/services/providers/akool/client.py`), P-02 (dedupe), E-02 (`skills/digital_anchor/akool_prompt.py`). **No Akool client / adapter / worker exists.**

### 3.4 Assembly, storage, async — reusable substrate (from Hot Follow)

- **Assembly:** `gateway/app/services/compose_service.py::CompositionService.compose()` + `execute_hot_follow_compose_contract()` run FFmpeg through the **Worker Gateway** (`worker_gateway.py`: `WorkerExecutionMode` INTERNAL/EXTERNAL/HYBRID, `WorkerRequest`/`WorkerResult`, `WorkerAdapter` protocol; `workers/internal_subprocess_worker.py`). FFmpeg helpers in `gateway/app/services/media/ffmpeg_localization.py`; subtitle burn-in in `compose_subtitle_rendering.py`.
- **Artifact storage:** `gateway/app/services/artifact_storage.py` (`upload_artifact`, `get_download_url` presigned, `object_exists`, `object_head`) over `R2StorageService` (S3) or `LocalStorageService` (`config.get_storage_service()`). final.mp4 download is `task_download_views.py kind == "final_mp4"` keyed on `final_video_key` / `final_video_path` / `deliver_key(task_id, "final.mp4")`.
- **Async model today:** in-process FastAPI `BackgroundTasks` + synchronous compose-through-worker-gateway; task state read from the task dict on each request. **There is no durable job queue and the in-process closure/task store is volatile** (the OWC operations addendum explicitly forbids planned gateway restarts during trial). This is the single biggest structural gap for an async provider like Akool (§9).

---

## 4. Akool API Capability Mapping (provider → Apollo capability kind)

Base URL `https://openapi.akool.com`. Auth: `x-api-key: {key}` header (preferred), or legacy `POST /api/open/v3/getToken` `{clientId, clientSecret}` → Bearer (≈1-year token). Business status is in JSON `code` (`1000` = success); HTTP status is not the signal.

| Akool capability | Endpoint (create) | Result/poll | Apollo capability kind (L3) | Output field |
| --- | --- | --- | --- | --- |
| Talking Photo | `POST /api/open/v3/content/video/createbytalkingphoto` | `GET /content/video/infobymodelid?video_model_id=` | `avatar` | `video` |
| Talking Avatar | `POST /api/open/v3/talkingavatar/create` | same `infobymodelid` | `avatar` | `video` |
| Image to Video | `POST /api/open/v4/image2Video/createBySourcePrompt` | `POST /api/open/v4/image2Video/resultsByIds` | `video_gen` | `video_url` |
| Face Swap (image/video) | `POST /api/open/v4/faceswap/faceswapPlusByImage` / `v3/.../highquality/specifyvideo` | `GET /api/open/v3/faceswap/result/listbyids?_ids=` | `face_swap` | `url` |
| Lip Sync | `POST /api/open/v3/content/video/lipsync` | same `infobymodelid` | `lip_sync` (fallback `post_production`) | `video` |
| VoiceLab TTS | `POST /api/open/v4/voice/tts` | voice list / status | `dub` (NOT default — VoiceTrans/Azure is the default audio route) | `preview` |

**Async model (uniform status enum):** create → receive `_id` (+ sometimes `job_id`/`task_id`) → poll a family-specific result endpoint **or** receive a webhook. Status: `1=queued, 2=processing, 3=success, 4=failed`. There are **three poll families** (video family `video_status`; faceswap `faceswap_status`; image2video `status`) — the adapter layer must normalize all three to one Apollo attempt state.

**Output URLs are temporary — valid 7 days.** Akool explicitly recommends saving promptly. **Apollo MUST copy provider outputs into Apollo artifact storage on completion and treat the Apollo artifact as the only deliverable truth.** A provider temporary URL is never a deliverable.

**Webhook:** every create accepts optional `webhookUrl` (lowercase `webhookurl` on image2video v4 — verify against `openapi.json`). Akool POSTs an **encrypted** envelope `{signature, dataEncrypt, timestamp, nonce}`: signature = `sha1(sort(clientId, timestamp, nonce, dataEncrypt))`; decrypt AES-CBC/PKCS#7 with **key = clientSecret (24 bytes), IV = clientId (16 bytes)**; decrypted `{_id, status, type, url}`. Endpoint must return HTTP 200 or Akool retries. **Webhooks need the clientId/clientSecret pair even when authenticating by API key.**

**Error / rate / credits:** `1003` param, `1005` too-frequent (rate-limit signal), `1006`/`1104` insufficient credits, `1101`/`1102` token, `1200` blocked. **No numeric rate limit / timeout / poll-interval is published** — design must assume unknown and use conservative client-side backoff + a 3–10 s poll interval. **`deduction_credit` and credit-balance errors MUST be stripped before any operator-visible payload** and mapped to generic internal "capacity/quota" diagnostics.

**Pre-implementation action:** pull `https://docs.akool.com/api-reference/openapi.json` + per-capability YAMLs to lock exact field casing before any client is written.

---

## 5. Proposed Production Line Design (Matrix Script as an independent line)

The intent (per the task) is for Matrix Script to be an independent, real, result-oriented production line comparable to Hot Follow — owning its own L2 orchestration and binding to Apollo-native capabilities, **not** copying Hot Follow's router/service residue (per alignment map §2.6 + runtime assembly rules).

### 5.1 Four-layer placement

- **L1 Operator Surface** — operator sees result-oriented verbs only:
  `生成主视频 · 生成镜头 · 重新生成这一镜头 · 生成角色口播 · 替换背景 · 生成多个版本 · 预览主视频 · 进入交付中心`.
  Operator MUST NOT see: `Akool / provider / vendor / model_id / credits / raw task id / raw provider error / temporary provider URL`. Sanitization is enforced at the operator boundary (alignment map §2.1, validator R3, production-flow-reset §5 forbidden vocabulary).
- **L2 Production Line Orchestration (Matrix Script owns):** script understanding → outline/hook/body/CTA → variation plan → shot plan → shot-level asset decision → voice/subtitle plan → assembly plan → delivery readiness → publish-feedback binding.
- **L3 Capability Execution (Apollo-native kinds):** `script_understanding` (`understanding`), `shot_plan_generation` (`understanding`/`variation`), `image_to_video_segment` (`video_gen`), `talking_avatar_segment` (`avatar`), `background_replace` (`face_swap`/`post_production`), `face_swap_or_character_enhance` (`face_swap`), `audio_generation` (`dub` — VoiceTrans/Azure default), `subtitle_generation` (`subtitles`), `video_assembly` (`post_production`/`pack` via compose worker), `delivery_packaging` (`pack`).
- **L4 Provider / Resource Layer (Akool lives here):** provider request/response, provider task id, provider status, provider temporary URL, retry/timeout details, failure reason. **L4 must not define L1 state.** Akool is one provider behind `video_gen` / `avatar` / `face_swap` / `lip_sync`; the line never names it.

### 5.2 First real controlled route (the only route this design proposes wiring)

```
script input
  → script_understanding            (existing understanding capability)
  → outline / hook / body / CTA      (existing content-structure / Phase B)
  → shot_plan_generation             (NEW: scene_plan_binding storyboard, 4–8 shots)
  → shot-level asset decision         (per-shot: still image / reference asset → capability choice)
  → scene-segment generation          (L3 video_gen|avatar via L4 Akool OR a mock/dry-run fallback)
  → audio_generation                 (VoiceTrans / Azure — existing real route; Akool TTS optional fallback only)
  → subtitle_generation / alignment   (existing subtitles capability)
  → FFmpeg assembly                  (existing compose worker → final.mp4)
  → final.mp4                         (real Apollo artifact in storage; provider URL copied in, never echoed)
  → delivery contract                (factory_delivery_contract; required/blocking_publish zoning)
  → publish feedback / archive        (existing closure path)
```

- **End-to-end "script→video in one Akool call" is NOT the default.** It may be documented only as an **experimental comparison lane** (separate, clearly labeled, never operator-default), per the task constraint.
- **Minimum first experiment scope:** line `matrix_script_line`; 9:16 short video; 20–60s; 1 script; 1–3 variants; 4–8 shots; primary result `final.mp4`; required deliverables `final_video, subtitles, audio, copy_bundle, metadata, manifest`; optional `scene_pack, source scene clips, provider diagnostics`.

---

## 6. Proposed Artifact and State Model

### 6.1 Additive line-packet bindings (Phase 3, additive only — existing instances must still validate)

Per `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` §3, all additive to the existing six factory-generic refs:

- `aspect_ratio_intent` — operator intent only.
- `operator_intent_map` — role/voice/subtitle/B-roll preference + variant strategy.
- `scene_plan_binding` — the storyboard object (the core Phase 3 object; absent today).
- `visual_materials_binding` — B-roll/background/product candidates (links `factory_input.reference_assets`).
- `audio_plan_binding` — per-scene voiceover + BGM + voice route (declares VoiceTrans as the runtime audio route).
- `language_plan_binding` — per-scene subtitle + language plan.
- `video_versions_binding` — per-version headline/differentiator/why_test/is_recommended.

These are **line-packet additive** — they do not change the six generic contracts and do not widen any closed enum. Authoring them is itself **gated** (no new contracts/closed-enum widening is allowed until the relevant wave opens — see §8/§11).

### 6.2 Manifest / final.mp4 truth model

- **Provider job record (L4, internal):** `{capability_kind, provider=akool, provider_task_id, provider_status, provider_temp_url, attempts[], last_error_category, requested_at}`. Stored outside operator payloads; never projected to L1.
- **Apollo artifact (L2 truth):** on provider `status==3`, **download → upload via `artifact_storage.upload_artifact`** → record `ArtifactHandle {key, content_length, etag, content_type, captured_at, source_capability}`. The Apollo key (e.g. `deliver_key(task_id, "scene/<n>.mp4")`, `deliver_key(task_id, "final.mp4")`) is the only deliverable truth.
- **Manifest:** per-shot artifact list + final.mp4 handle + audio + subtitles + copy_bundle + metadata, with per-deliverable `required` / `blocking_publish` per `factory_delivery_contract_v1` (scene_pack stays `required=false, blocking_publish=false`; `scene_pack_blocking_allowed:false`).
- **No fake `final_video`.** Until the real artifact exists, the operator surface shows the existing honest `main_video_pending_capability` / `not_generated` state.

### 6.3 Four-layer state mapping

- **L1 step status** — per-shot and per-final generation step (`not_generated / generating / ready_for_review / deliverable`), written only by step execution; surfaced as operator verbs/pills.
- **L2 artifact facts** — existence + freshness of each Apollo artifact (shot clips, final.mp4, audio, subtitles), derived from storage `object_head`. Provider temp URLs are **not** L2 facts.
- **L3 current attempt / route** — the normalized current generation attempt (collapsing Akool's three poll families + status enum into one attempt state); current-vs-historical via `final_provenance`.
- **L4 ready gate / projection / advisory** — consumes L2/L3; produces `publish_readiness`; renders the result-oriented workbench + delivery center. L4 never creates truth and never names a provider.

---

## 7. Delivery Center Phase 3 Requirements

- Delivery Center stays **final-video-oriented and result-only** (production-flow-reset §6): six sections (交付结果介绍 / 主视频 / 必需交付物 / 可选交付物 / 发布设置 / 发布回填); **no generation controls, no production-flow panels**.
- Replace the current `artifact_lookup_unresolved` sentinel rows with **real `ArtifactHandle` resolution** once L2 artifacts exist — through the existing `delivery_binding.py` B4 `artifact_lookup` path, **without B4 code change** (it already resolves real handles when `final_provenance`/`final_fresh` are present).
- Per-deliverable `required` / `blocking_publish` zoning rendered from contract fields; scene_pack non-blocking; publish gated on real `final_video` presence.
- Gap today: nothing produces real artifacts, so every row is a tracked-gap. Phase 3's delivery requirement is purely "make the projection resolve when truth lands" — no new Delivery Center truth ownership.

---

## 8. PR Breakdown (proposed; opens nothing by itself)

PRs are proposed **only after design review** and **only when the governing wave opens** (§11). Each is small, single-boundary, file-fenced, with mocked/dry-run tests first.

- **PR-0 — Phase 3 design document only (THIS artifact).** Docs-only. Opens no gate.
- **PR-1 — Apollo-native Akool capability adapter interface, mocked.** New `gateway/app/services/providers/akool/client.py` (P-01 absorption) + `gateway/app/services/workers/adapters/akool/{avatar,video_gen,face_swap}.py` subclassing the existing adapter bases; secret ref `AKOOL_API_KEY`; **all tests mocked, no live calls**; error mapping to `AdapterErrorCategory`; credit fields stripped. *(Gated: Capability Expansion W2.3.)*
- **PR-2 — Matrix Script shot plan + artifact contract.** Additive `scene_plan_binding` (+ intent map) line-packet object; manifest/ArtifactHandle model; tests prove existing instances still validate. *(Gated: requires the wave that authorizes new line-packet objects.)*
- **PR-3 — Akool scene-segment generation worker (mocked / dry-run).** Worker-gateway request shape for a scene segment; provider-output → Apollo-artifact copy path; **dry-run mode default**; no live provider call in CI.
- **PR-4 — VoiceTrans / Azure audio + subtitle bridge for Matrix Script.** Reuse `VoiceToolService`/Azure; no Akool dependency.
- **PR-5 — FFmpeg assembly worker for final.mp4.** Matrix Script assembly through the existing compose/worker-gateway substrate; produces a real Apollo `final.mp4` artifact from shot clips + audio + subtitles.
- **PR-6 — Delivery Center result-oriented projection.** Resolve real `ArtifactHandle` rows; render required/blocking zoning. No new truth.
- **PR-7 — Minimal E2E smoke for Matrix Script real generation.** Narrow first-experiment scope (§5.2); dry-run/mocked provider; assert no fake media, no vendor leak, artifact-truth delivery.

Do not combine these. Do not start any of PR-1..PR-7 in this branch — this branch produces PR-0 only.

---

## 9. Risks / Blockers

1. **WAVE GATE (highest).** Real Akool generation is Capability Expansion Gate Wave W2.3, **BLOCKED** on Platform Runtime Assembly signoff, which is BLOCKED on Plan A live-trial closeout. PR-1..PR-7 cannot land until that sequence opens. This design opens nothing.
2. **No durable job store.** Async Akool (create→poll/webhook over minutes) collides with the current in-process volatile task/closure store + FastAPI `BackgroundTasks`. A durable job/attempt store is a Platform-Runtime-Assembly-class prerequisite; without it, provider tasks are lost on restart.
3. **Provider-URL-as-truth trap.** Akool URLs expire in 7 days. Must copy to Apollo storage on completion; never store/echo provider temp URLs as deliverables.
4. **Second-task-system trap.** Akool returns its own task ids/status. These are L4 only; they must be normalized into one Apollo attempt and never become a parallel operator task system.
5. **Operator-boundary leakage.** Vendor name, model id, credits, raw provider error, raw task id must be stripped (validator R3 + fidelity test). Webhook payloads carry provider ids — sanitize before any projection.
6. **Webhook crypto + reachability.** AES-CBC with clientSecret/clientId, signature verification, 200-or-retry. Needs a public callback endpoint; in a trial/headless env webhooks may be unreachable → polling fallback required.
7. **No published rate/timeout/poll guidance.** Implement conservative backoff (`1005`) + 3–10 s poll + per-attempt timeout; verify empirically.
8. **Field-casing drift** in Akool `.md` docs (`webhookUrl` vs `webhookurl`). Lock against `openapi.json` before coding.
9. **God-file pressure.** Do not add Akool/orchestration to `tasks.py` / routers (`ENGINEERING_RULES.md` §3/§9, constraints index). All provider flow goes through capability-adapter + worker-gateway boundaries.
10. **Missing report file** `VEOMATRIXVOICE05_PRODUCTION_DOMAIN_SWITCH_REPORT_v1.md` (§0) — confirm before implementation.

---

## 10. Final Recommendation

### 10.0 Explicit gate statement (binding)

**This document does NOT open Capability Expansion W2.3.** Real Akool generation remains **BLOCKED** until **Platform Runtime Assembly Wave** signoff **and** **Capability Expansion Gate Wave** signoff land per the frozen next engineering sequence. Approving PR-0 (this design artifact) opens no implementation gate.

**PR-1 statement (binding):** The **mocked Akool adapter (PR-1) is NOT authorized by this review.** PR-1 requires **separate approval** under its own gate spec + signoff. Nothing in this document authorizes adding an Akool client, adapter code, schema/packet changes, or template changes.

### 10.1 Recommendation

- **Implementation allowed after design review: NO (for real generation).** Real Akool generation (PR-1..PR-7) is gated behind Platform Runtime Assembly + Capability Expansion Gate Wave W2.3 and must not start in this branch or before those waves open.
- **What IS allowable now (docs-only, this branch):** this Phase 3 design document (PR-0). Optionally, after review and explicit hand-off, the **mocked/dry-run capability-adapter interface (PR-1)** could be considered as donor-absorption preparation **only if** a reviewer confirms it fits "always-allowed maintenance / donor preparation" without crossing the Capability Expansion gate — recommend treating it as gated unless explicitly authorized.
- **Recommended immediate next step:** review this document; if accepted, record it in the evidence index and hold PR-1..PR-7 until the Capability Expansion Gate Wave is opened by its own gate spec + signoff, per the frozen next engineering sequence.

---

## 11. Explicit No-Touch Statement

- **`debt/post-veomatrixvoice05-test-reconciliation` — NOT TOUCHED.** Known debt (status policy / Hot Follow currentness; operator-visible surfaces; Matrix Script legacy copy/source-ref drift; Digital Anchor shared workbench rendering; local env PEP-604 dependency issue) is **documented here as known debt and not fixed in this branch.**
- **Hot Follow runtime — NOT REGRESSED / NOT TOUCHED.** This design reuses Hot Follow's compose/worker-gateway/storage substrate by reference only; it proposes no change to `hot_follow_*`, `tasks.py` Hot Follow paths, or `compose_service.py` behavior.
- **Digital Anchor — NOT TOUCHED / NOT WIDENED.** The five operations findings remain in force.
- **Non-negotiable guardrails (all observed):** no provider/model/vendor/credits in operator UI; Akool is not a second task system; no provider temp URL as final truth; Workbench/Delivery Center invent no state; Hot Follow not regressed; Scene Pack not a publish blocker; artifact/deliverable truth not bypassed; no secrets logged; no large router/service rewrite as a first step; Phase 3 not mixed with post-merge debt; **first and only output is this design/review document.**
