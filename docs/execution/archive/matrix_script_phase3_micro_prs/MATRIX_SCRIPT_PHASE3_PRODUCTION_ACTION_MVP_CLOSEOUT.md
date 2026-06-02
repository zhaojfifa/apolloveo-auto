# Matrix Script Phase 3 — Production Action MVP Closeout

Date: 2026-06-01
Branch: `phase3/mvp-closeout-matrix-script-production-action`
Base: `main` @ `80f340a02d1ca4fe1c3047214c0f817708954483`
Status: **Documentation only. No functional code change in this closeout.** Aggregating audit of the Matrix Script Phase 3 Production Action MVP (PR-0 → PR-13R).

---

## 0. Reading Declaration

Root indexes + governance (`README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`, `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`) read. Task-specific: the PR-0 design plan + the PR-1…PR-13R execution notes + the merged modules under `gateway/app/services/matrix_script/` and `gateway/app/routers/matrix_script_minimal_result.py`. Sufficient because this is an audit of already-merged, individually-reviewed slices. No missing authority.

---

## 1. Scope

Confirm whether Matrix Script reaches the minimum closed loop **operator-triggerable · process-visible · result-visible**, producing a real local `final.mp4`, while keeping real generation (Akool) and official delivery gated.

Out of scope: starting Delivery / Akool / process-trace work (gated on this closeout's review).

---

## 2. Merged PR Lineage (all on `main`)

| PR | Title | PR # | Merge commit |
| --- | --- | --- | --- |
| PR-0 | Phase 3 Akool real-generation design plan (docs) | #165 | `ad7cd103` |
| PR-1 | Akool capability adapter skeleton (mocked) | #166 | `400b710c` |
| PR-2 | Matrix Script shot plan skeleton | #167 | `3cbfcd47` |
| PR-3 | Scene artifact / manifest skeleton | #168 | `d80bdfe5` |
| PR-4R | Minimal result loop producing real `final.mp4` | #169 | `a084bd90` |
| PR-5R | Minimal result service bridge | #170 | `1817c680` |
| PR-6R | Minimal result record | #171 | `726a3a0a` |
| PR-7R | Result projection (operator + delivery) | #172 | `4b2d7573` |
| PR-8R | Minimal result surface view | #173 | `7a1922fa` |
| PR-9R | Workbench read-only result block | #174 | `df3ec12b` |
| PR-10R | Task → result orchestrator | #175 | `7bcac682` |
| PR-11R | Internal minimal result command | #176 | `31fb8e7e` |
| PR-12R | Internal minimal-result route (`POST /api/matrix-script/{task_id}/minimal-result`) | #177 | `d38e3066` |
| PR-13R | Workbench minimal-result trigger action MVP | #178 | `80f340a0` |

---

## 3. Operator Path

```
Workbench (matrix_script task)
  → click 「生成本地最小成片」
  → POST /api/matrix-script/{task_id}/minimal-result
  → orchestrator: derive outline → shot plan → scene slots → FFmpeg color-card
    scene clips → silent narration → subtitles.srt → FFmpeg assembly → final.mp4
    → manifest.json → record → projection → surface view
  → Workbench renders 本地最小成片 (status / local path / duration / shots /
     storage_scope=local_workspace / official_publish_ready=false / note)
```

---

## 4. Result Proof

Aggregate test run across the chain (ffmpeg 8.1.1 present): **188 passed**. Real orchestrator run (`closeout-demo`, 5 shots, target 8.0s) produced:

```
shots/scene_001.mp4 … scene_005.mp4   audio/narration.wav   subtitles/subtitles.srt
final/final.mp4 = 14,683 bytes (ffprobe duration 8.0s)      manifest.json
surface: has_result=True · result_status=generated · storage_scope=local_workspace · official_publish_ready=False
```

- final.mp4: ✅ real, non-empty, ffprobe-readable
- subtitles: ✅ `subtitles.srt`
- audio: ✅ `narration.wav` (silent fallback)
- manifest: ✅ `manifest.json` (`shot_count`, local `final_video_path`, `generation_provider=none`)
- Workbench block: ✅ renders the surface payload; product-flow fidelity suite green (44 passed)

---

## 5. Boundary Proof

- no Akool live: ✅ — PR-1 adapter is a mocked skeleton (no transport → `NOT_WIRED`); no chain module imports it. `generation_provider="none"`.
- no provider URL: ✅ — surface/record/route guards reject provider/temporary/download URLs; outputs are local paths only.
- no artifact_storage/R2: ✅ — no `artifact_storage` import/call anywhere in the chain; output only to a caller/workspace dir.
- no official publish: ✅ — `official_publish_ready` hard-pinned `false`; no `publish_url` / `publish_status`; route returns 503 (not a fake) when ffmpeg absent.
- no schema/contract: ✅ — `packet/envelope.py` and `docs/contracts/**` untouched across all PRs.
- no Hot Follow / Digital Anchor regression: ✅ — forbidden-path guards clean on every PR; the Workbench action is gated to `matrix_script` tasks; HF/DA files never touched.

---

## 6. Answers to the closeout questions

1. Operator can trigger generation from Workbench? **Yes** (PR-13R button → PR-12R route).
2. Real `final.mp4` produced? **Yes** (PR-4R, proven by ffprobe; real artifact above).
3. Workbench shows the local minimal result? **Yes** (PR-9R block + PR-13R action render).
4. local_workspace / non-official-delivery made explicit? **Yes** (`storage_scope=local_workspace`, `official_publish_ready=false`, note "尚未进入正式交付存储").
5. Readable error on failure? **Yes** (action shows `生成失败（<status>）`; route 503 on ffmpeg-absence; 400/404 on bad task).
6. No Akool/provider/vendor/model/credit leakage? **Yes** (guards + leak tests across surface/record/route/action).
7. No artifact_storage/R2/publish_url/publish_status pollution? **Yes** (guards + forbidden-path audits).
8. Hot Follow / Digital Anchor intact? **Yes** (gated; never touched).
9. Manual real-task test still needed? **Yes (recommended)** — one operator run on a real Matrix Script task in a deployed env (these tests run locally with ffmpeg; CI/runner must have ffmpeg). See §9.
10. Next: Delivery read-only result vs Akool scene replacement? **See §7 + §8.**

---

## 7. Known Limitations

- local_workspace only — no official artifact storage / R2.
- silent audio fallback (no real narration / TTS yet; VoiceTrans/Azure bridge not wired into this loop).
- simple FFmpeg color-card scenes (no real visuals / B-roll).
- no Akool scene generation yet (skeleton only; gated behind Capability Expansion W2.3).
- no Delivery official artifact; no publish-ready gate.
- async: synchronous in-request render; no durable job store; environments without ffmpeg return 503 (never a fake).

---

## 8. Next Decision (for reviewer)

- **Option A — Delivery local result read-only view**: surface the same local result in the Delivery Center as an inspect-only, non-publish row (`official_publish_ready=false` preserved). Lowest risk; closes the "result visible in Delivery" gap without publish logic.
- **Option B — Akool replaces one scene clip**: wire the PR-1 adapter (still mocked/dry-run by default) so one shot's `generation_mode=image_to_video`/`avatar` segment can be produced via Akool, copied into Apollo storage. Higher value but crosses into Capability Expansion W2.3 — **requires its own gate-spec + signoff** before any live call.
- **Option C — execution_trace / process observability**: emit a structured, operator-readable trace of the loop steps (shot plan → render → assemble) for the Workbench "process visible" axis.

---

## 9. Recommendation

The minimum closed loop (operator-triggerable · process-visible · result-visible · real local `final.mp4`) is **MET** at MVP scope, with all boundaries held. Recommendation:

1. **Add one manual real-task validation** on a deployed env with ffmpeg installed (CI/runners must provision ffmpeg, or the real-render tests skip) — record it as evidence.
2. Proceed with **Option A (Delivery local read-only result view)** next: it is the smallest, boundary-safe increment that extends "result visible" to the Delivery surface without touching publish logic or crossing the Akool/Capability-Expansion gate.
3. Hold **Option B (Akool)** until a dedicated Capability Expansion W2.3 gate-spec + signoff lands, per the PR-0 design §2/§10 — real generation remains gated.

No functional code is changed by this closeout. Do not start Delivery / Akool / process-trace work until this closeout is reviewed.
