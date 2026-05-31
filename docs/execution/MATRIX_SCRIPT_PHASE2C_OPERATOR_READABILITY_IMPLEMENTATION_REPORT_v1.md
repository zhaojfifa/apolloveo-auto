# Matrix Script · Phase 2C Operator Readability Implementation · Report v1

Date: 2026-05-30
Status: **Implementation PR — copy / template-layout / presenter-shaping only.** No backend capability, worker, contract, schema, packet, closed enum, runtime, or route change. No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime touch. No generic factory-readiness touch. No `main` merge. No VeoMatrixVoice05. No Phase 3.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2C Operator Readability Implementer), under **Codex CONDITIONAL GO** with corrections (1)–(6).

---

## 1. Branch and base

| Item | Value |
|---|---|
| Base branch | `design/ms-phase2c-operator-readability-planning-20260530` |
| Base commit | `de38192` (`docs(matrix-script): archive phase2c operator readability plan`) |
| Implementation branch | `fix/ms-script-to-video-phase2c-operator-readability-20260530` |
| Commit message | `fix(matrix-script): improve phase2c operator readability` |
| Purpose | Make the Matrix Script Workbench read as a script-to-video generation workspace rather than a backend / status placeholder surface, via copy / layout / presenter-shaping only. |

### 1.1 Baseline self-containment (Codex correction #1)

The Phase 2C intake document `VEOMATRIXVOICE04_MANUAL_VALIDATION_AND_PHASE2C_INTAKE_v1.md` is **not** present on this implementation branch; it lives on commit **`31c0967`** (above `VeoMatrixVoice04` HEAD). Per Codex correction #1 the commit reference is **pinned here** rather than the file being copied into this PR, so any future reader can resolve the intake authority deterministically. The two companion baseline reports — the VeoMatrixVoice04 joint validation integration report and the New Task entry-cards fidelity-fix report — were read during planning and are reachable from `VeoMatrixVoice04` history.

---

## 2. Files changed

| File | Status | Kind | Allowlist |
|---|---|---|---|
| `gateway/app/templates/task_workbench.html` | MODIFIED | Template copy / layout | ✅ allowed |
| `gateway/app/templates/task_publish_hub.html` | MODIFIED | Template copy | ✅ allowed |
| `gateway/app/templates/matrix_script_new.html` | MODIFIED | Template copy | ✅ allowed |
| `gateway/app/services/tests/test_matrix_script_workbench_phase2c_operator_readability.py` | NEW | Matrix-Script-scoped test | ✅ allowed |

`git diff --stat` against the base: 3 templates changed (+139 / −51), plus 1 new scoped test file. **Zero** entries under `docs/contracts/`, `schemas/`, `samples/`, `gateway/app/routers/`, `gateway/app/main.py`, any worker / generator module, any packet definition, any closed-enum file, or any Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime path.

No presenter / service module under `gateway/app/services/matrix_script/*` required changes: the three new §B labels (目标受众 / 语气 / 时长) read optional helper fields with template-side `or` fallbacks, so no new payload field, no new producer, no packet write.

---

## 3. Section-by-section changes (task_workbench.html)

All changes preserve the back-compat `data-role` anchors and `data-status-code` values that the existing Phase 2B structural tests assert on; only operator-visible copy, layout, and control affordance changed.

- **Capability banner (NEW)** — One top-level operator-orientation banner (`matrix-script-capability-banner`) explains the workbench as a script-to-video workspace whose generation / material steps open as capability lands; states that selected preferences feed later generation. Operator language only.
- **§B 脚本理解** — Selling-points line no longer leaks `content_structure` (now "卖点项接入后会在这里逐条展开；当前阶段以脚本主旨为准"). Added operator labels **目标受众 / 语气 / 时长** with safe fallbacks. Subtitle rewritten to operator language.
- **§C 视频生成计划** — Status pill `当前占位 · 后台待接入` → `占位草案`. Subtitle and honest disclaimer rewritten to remove `后端`; honesty preserved ("当前不声明任何镜头已就绪", "占位草案"). All 11 storyboard fields + `plan_pending_upstream` status codes intact.
- **§D 画面与素材** — Three repeated pending slots consolidated into ONE operator-facing **素材意图** intent panel (`ms-section-visual-materials-intent-panel`) as the primary read; the three legacy slot anchors (bg / broll / product) preserved inside a collapsed `<details>` for back-compat. The three disabled-button tooltips are now **differentiated** (背景候选 / B-Roll 候选 / 素材匹配能力). No upload endpoint, no packet write, no fake media (Codex #2).
- **§E 角色与声音** — Removed VoiceTrans / 供应方 / 桥接 from operator-visible copy. Voice-preview placeholder demoted from a dashed panel to a chip (`🔊 试听能力接入后开放`). `ms-section-role-voice-preview-slot` + `voice_preview_pending_voicetrans` status code preserved. No iframe, no raw VoiceTrans UI.
- **§F 字幕与音乐** — Subtitle / BGM controls (font / position / bgm-mood / bgm-volume) are now selectable `<select>` elements carrying operator intent. Each `<select>` has **no `name=`** attribute, submits nothing, writes no packet / route / storage truth (Codex #3). Original anchors + `subtitle_style_pending_compose` / `bgm_pending_upstream` status codes preserved. Added `预览生成后生效` chip.
- **§G 视频变体** — Each version card (V1 / V2 / V3) gains a **适合哪些账号 / 场景** column (`ms-section-video-versions-card-audience`). V1 keeps the single ⭐ recommended marker (count == 1); V2 / V3 gain a 备选 alt-marker (`ms-section-video-versions-card-alt-marker`, distinct data-role). Card status text `当前占位 · 待生成` → `待生成`. The status pill is derived only from the existing static absent-artifact placeholder — no new status truth, no new closed enum, no new `data-status-code` value (Codex #4).
- **§H 校对与微调** — Unchanged; four review zones already read consistent `待主视频生成。` with `待主视频` pill.

## 4. Other surfaces

- **task_publish_hub.html §6** — Metrics placeholder `指标投射尚未上线 · 暂不展示数值。` → future-metrics operator copy describing 完播率 / 点赞 / 评论 / 留资 after publish backfill. No fake numbers, no fake URL; the no-fake-link note is untouched.
- **matrix_script_new.html Card 4** — Role / voice / subtitle options gain operator usage hints (推荐：纯 B-Roll + 字幕 / 讲解型短视频 / 本地化投放 / 生活种草 / 测评说明 / 短视频首屏). VoiceTrans / 供应方 / vendor / model / engine leaks removed from the two visible notes while preserving the `ms-new-voicetrans-future-provider-note` anchor. **No new payload field; no new `name=` control.**

---

## 5. Forbidden-vocabulary discipline (Codex correction #5)

Operator-visible primary copy (Sections B–I, with Jinja comments / statements / expression contents stripped and attribute values blanked) is free of: `content_structure`, `后端`, `backend`, `compose`, `producer`, `桥接`, `provider`, `vendor`, `engine`, `azure`, `akool`, `seedance`, `openai`, `anthropic`, `elevenlabs`, `VoiceTrans`. Remaining occurrences live only inside `{# … #}` comments, `data-status-code` values (closed status codes such as `subtitle_style_pending_compose`, `voice_preview_pending_voicetrans`), and the §J technical-diagnostics fold — all exempt. This is locked by `test_no_forbidden_vocab_in_primary_visible`.

---

## 6. Test evidence

New scoped test file `test_matrix_script_workbench_phase2c_operator_readability.py` adds **20 source-level assertions** covering the capability banner, §B/§C/§D/§E/§F/§G readability shape, the forbidden-vocab gate, the Delivery Center metrics rewrite, and New Task Card 4 hints.

Scoped test run (all green):

```
test_matrix_script_new_task_entry_cards_fidelity.py
test_matrix_script_workbench_phase2b_product_fidelity.py
test_matrix_script_workbench_script_to_video_phase2b.py
test_matrix_script_delivery_center_product_flow_reset_prb.py
test_matrix_script_workbench_phase2c_operator_readability.py   (NEW — 20 assertions)
test_voice_tool_service.py
test_matrix_script_workbench_optional_variants.py
→ 242 passed
```

No previously-passing Matrix Script test regressed.

---

## 7. Boundary statement (what this PR does NOT do)

This PR does NOT: start Phase 3; change contracts, schemas, packets, or closed enums; add workers; change routes or endpoints; touch Hot Follow / Digital Anchor / Asset Supply runtime / VoiceTrans runtime / generic factory readiness; add backend generation; add real B-Roll retrieval; add a VoiceTrans bridge; add an Asset Supply bridge; fake final_video / thumbnails / media URLs / publish_url / generated media / publish success / metrics; expose provider / model / vendor / engine controls; embed a VoiceTrans iframe or raw VoiceTrans UI; create VeoMatrixVoice05; or merge to `main`.

---

## 8. Verdict request

**Phase 2C ready for manual readability validation.**

Recommended manual validation: open a matrix_script task Workbench and confirm the first scan reads as a script-to-video workspace (capability banner → §A main video → §B understanding → §C plan → §D material intent → §E role/voice preferences → §F selectable subtitle/music → §G version cards with audience guidance); confirm no backend / vendor vocabulary is visible in §B–§I; confirm the Delivery Center §6 metrics line describes future publish metrics; confirm New Task Card 4 shows usage hints. Implementation past this point (real generation / material / voice capability) requires a separate裁决.
