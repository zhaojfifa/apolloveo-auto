# Matrix Script Product / Design Realignment

Date: 2026-06-02
Status: Engineering execution alignment note only.

This document is not a new Matrix Script design authority. It records the
product/design baseline that must be cited before the next narrow Workbench /
New Task correction. It does not change runtime, templates, presenters,
contracts, schemas, packets, workers, generation paths, Hot Follow, Digital
Anchor, Asset Supply, Akool, or `artifact_storage.py`.

## 1. Rules read

### Root files

- `CLAUDE.md`
- `README.md`
- `PROJECT_RULES.md`
- `ENGINEERING_RULES.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `ENGINEERING_STATUS.md`
- `CURRENT_ENGINEERING_FOCUS.md`

### Docs index

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

### Product authority

- `docs/product/matrix_script_product_flow_v1.md`
- `docs/product/matrix_script_product_flow_v2_delta.md`

### Design authority

- `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`
- `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
- `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
- `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`
- `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html`

### Architecture / state authority

- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
- `docs/contracts/status_ownership_matrix.md`

### Missing files

- None from the requested list.

## 2. Product baseline

### Product v1 conclusion

`matrix_script_product_flow_v1` defines Matrix Script as a formal result
production line, not a generic task-status page. The line turns a topic or
script into multiple publishable short-video versions, supports matrix-account
testing, and ends in delivery / publish feedback / iteration. Its primary
result is `final_video`; subtitle, audio, copy bundle, metadata, manifest,
variation config, publish status, and optional `scene_pack` are supporting
deliverables.

The business spine remains:

```text
主题/目标 -> 脚本结构化 -> 变体配置 -> 生成任务 -> 校对与筛选
-> 成片交付 -> 发布回填 -> 复盘沉淀
```

### Product v2 delta conclusion

`matrix_script_product_flow_v2_delta` shifts the operator-facing product from a
task/status/result surface to a script-to-video production surface. The first
operator product object is the generation plan / storyboard. The operator
journey is:

```text
入口 · 生成视频方案
-> 工作台 · 审阅方案 + 配置 + 生成
-> 交付中心 · 主视频 + 发布
```

Variants should read as video versions, not axis rows. VoiceTrans and Digital
Anchor are future runtime/provider inputs through contracts and navigation;
they must not be raw-embedded in the Matrix Script UI. No provider, model,
vendor, or engine choice belongs in the primary operator surface.

### Matrix Script production line definition

Matrix Script is the script-driven TK-style short-video production line for:

- turning script / topic / product intent into a video generation plan;
- checking and replacing per-shot visual material before generation;
- generating a primary video preview and video versions;
- routing the accepted primary video into Delivery;
- preserving publish feedback and iteration as the loop closure.

### Operator task flow

The entry flow should collect only what the operator can naturally provide:

- script text or script source;
- product / material description and references;
- target platform, aspect ratio, target language, audience;
- role, voice, subtitle, B-Roll, BGM, and variant preferences as intent.

The New Task page should not read as a long contract form. It should make clear
that product / material detail can be refined per shot in the Workbench after
the video plan is created.

### Workbench goal

The Workbench must help the operator finish the production decision loop:

1. See whether a primary video preview exists.
2. If no preview exists, prepare material / music / subtitle intent and
   generate the preview.
3. If a preview exists, inspect the video, current version, and operator
   acceptance.
4. Replace or supplement material by shot, especially partially matched shots.
5. Regenerate when inputs changed.
6. Send a delivery candidate to Delivery while keeping
   `official_publish_ready=false` until the delivery gate authorizes otherwise.

### Delivery goal

Delivery consumes the accepted primary result and publish-facing package. It
should not contain generation controls. It should expose the main video,
required deliverables, optional deliverables, publish settings, publish
feedback, and diagnostics, with `scene_pack` optional and non-blocking.

## 3. Design baseline

### Authority index conclusion

`MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX` is binding. Future Matrix Script UI and
result-line work must read it first. Bucket A is the only binding design /
product / result authority set:

1. `docs/product/matrix_script_product_flow_v2_delta.md`
2. `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
3. `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html`
4. `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
5. `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`
6. `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
7. `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md`

Execution logs are evidence only, not UI authority, unless the authority index
explicitly lists them for a narrow factual purpose.

### Accepted mock / IA

The accepted mock establishes three surfaces:

- New Task: five cards, primary CTA `生成视频方案`.
- Workbench: script-to-video sections centered on main video result,
  script understanding, video generation plan / storyboard, visual material,
  role and sound, subtitles and music, versions, review, delivery, and collapsed
  diagnostics.
- Delivery Center: final-video-oriented delivery and publish feedback.

The current correction may use the later operator-first ordering requested by
product review, but it must be interpreted as a projection of the accepted
script-to-video mock: preview first, material loop second, delivery third, then
variants / script understanding / diagnostics folded or de-emphasized.

### Reset discipline

The reset design says the old backend-like A/B/C/D/E/F blocks must not survive
as visible parallel primary flow. Legacy data-role anchors may exist only in a
collapsed architect diagnostic fold, and must not keep duplicate primary action
groups that can leak back into visible UI.

### Readability discipline

The Phase 2C readability plan says Workbench copy and layout must use operator
language. Primary UI must not say `content_structure`, `后端`, `compose`,
`producer`, `provider`, `vendor`, `engine`, `model`, or expose vendor names as
operator controls. Unsupported capability must be described as an honest future
appearance, not as backend vocabulary or fake readiness.

## 4. Four-layer state boundary

### L1

Pipeline step / process status. It records what ran and how the step ended. It
does not prove business correctness by itself.

### L2

Artifact facts. It records what artifacts exist, their factual metadata,
freshness inputs, and local / staged / delivery artifact facts. L2 must not be
backfilled from UI text.

### L3

Current attempt / readiness / operator acceptance. It interprets whether the
current artifact set is actionable, current, stale, blocked, candidate, or
accepted. Matrix Script's current PR-A result chain may surface operator
acceptance and `delivery_candidate=true` as L3-derived facts, while
`official_publish_ready` remains false.

### L4

Operator summary / UI projection. It presents L2/L3 safely to the operator,
including Workbench and Delivery views. L4 may consume L2/L3; it must not
create artifact truth, publish truth, provider truth, or readiness truth.

### What UI may show

- L4 operator summaries: primary video status, material readiness summary,
  shot acceptance labels, recommended next action, delivery candidate copy.
- Necessary L3 acceptance facts: `operator_usable`, `delivery_candidate`,
  `official_publish_ready=false`, shot match count, real visual count, semantic
  match summary.
- Local preview path / `preview_url` only as a local or staged preview truth
  when produced by the existing result chain, not as official delivery truth.

### What UI must not show

- Raw L2 artifact refs, raw manifest JSON, trace JSON, provider URLs, temporary
  URLs, R2 keys, artifact keys, raw local paths as primary operator text.
- Provider / model / vendor / engine / credit / external task IDs.
- `official_publish_ready=true` without an approved delivery contract gate.
- Fake `final_video`, fake thumbnail, fake media URL, fake `publish_url`.
- L1 process labels as if they were operator outcome truth.

## 5. Current implementation gap

### Main video preview

PR #196 moves the visible page toward preview-first ordering, but the product
expression is still not a complete operator video card. The card needs to read
as a working video production object: current version, preview, acceptance
summary, material-change state, and the correct next action. "Generated" and
"ungenerated" states must not share action groups.

### Material replacement

The material section is now earlier in the page, but the loop is still not
clear enough: which shot needs replacement, what material is currently used,
what operator action changes it, and whether that change requires regeneration.
Shot 04 / 05 partial reuse must become an obvious material-supplement task,
not a technical acceptance row.

### Regenerate linkage

The page must explain the production loop:

```text
replace / supplement shot material or music
-> mark preview inputs changed
-> generate again / regenerate preview
-> inspect primary video
-> deliver candidate
```

Without that linkage, "生成视频预览" and "再次生成" look like isolated buttons.

### New Task material input

`matrix_script_new.html` already has a product/material card, but it still uses
upload-placeholder language and backend-worker wording. The entry page should
say: first fill product and material description; later, in Workbench, replace
or supplement material per shot; when upload support lands, each shot can accept
real material.

### Delivery entry

Delivery should be a consequence of a generated delivery candidate. In
ungenerated state it should only say "generate primary video before delivery".
When `delivery_candidate=true`, it should show the candidate and route to
Delivery without contradicting the main result.

### Script/story understanding

Script and story understanding remain important, but product review says they
are not the first operator action. They must be folded or placed after preview,
material/music, delivery, and variants. Their role is explanation and
traceability, not the primary production action.

## 6. Correction plan

### Workbench

Next code work should be the Matrix Script Preview-Material Loop:

- Main preview card:
  - Ungenerated: material preparation summary + one primary action
    `生成视频预览`.
  - Generated: inline video + current version + operator acceptance.
  - Material changed after preview: explicit "需要再次生成" prompt.
- Material / background / music card:
  - Show shot-level material rows.
  - Bind replacement actions to specific shots.
  - Mark Shot 04 / 05 as needing real tasting / handoff material.
  - Concentrate BGM, voice, subtitle state in the same loop.
- Delivery entry:
  - `delivery_candidate=true` gates the delivery CTA.
  - Keep `official_publish_ready=false`.
- Folded sections:
  - Variants de-emphasized until main preview is accepted.
  - Script / story understanding folded and after variants.
  - Technical diagnostics collapsed and the only place for raw fields.

### New Task

Change only operator copy / presentation:

- product / material section states that current entry captures descriptions
  and references first;
- Workbench is where material is replaced per shot;
- future upload support can supplement each shot after the generation plan
  exists;
- avoid backend-worker wording in primary copy.

### Delivery

No Delivery runtime change should be part of the next narrow fix. Delivery may
need only consistency copy if the Workbench delivery entry references it.

### Docs / index updates

The docs index should route Matrix Script work through the authority index and
Bucket A first, and should state execution logs are evidence only, not design
authority.

## 7. Files to modify next

### Templates

- `gateway/app/templates/task_workbench.html`
- `gateway/app/templates/matrix_script_new.html`
- `gateway/app/templates/task_publish_hub.html` only if delivery copy
  consistency requires it.

### Tests

- Add or update Matrix Script Workbench focused tests for:
  - preview/material/delivery/variant/script/diagnostic order;
  - generated vs ungenerated actions;
  - material replacement row semantics;
  - "needs regeneration after material changed" copy;
  - no primary UI raw engineering terms.
- Add or update Matrix Script New Task tests for:
  - product/material copy;
  - Workbench per-shot replacement explanation;
  - no backend-worker wording in primary copy.

### Docs index

- `docs/ENGINEERING_INDEX.md`

## 8. Deprecated authority / evidence-only documents

The following document classes may be read only as implementation evidence or
historical diagnostics. They must not be treated as the next UI authority:

- PR14-PR17 execution logs.
- `minimal_result` reports.
- staged preview reports.
- operator preview reports.
- PR-A / PR-B temporary reports.
- Any `docs/execution/*` file unless listed by
  `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`.

Execution evidence can prove that a capability or regression exists; it cannot
define a new IA, new product object, new readiness truth, or new UI hierarchy.

## 9. Boundary confirmation

- Hot Follow untouched.
- Digital Anchor untouched.
- Asset Supply untouched.
- VoiceTrans runtime untouched.
- `artifact_storage.py` untouched.
- No schema / contract / packet / closed enum change.
- No generation path change.
- No Akool live/API work.
- No provider URL / temporary URL / publish URL surfacing.
- `official_publish_ready` remains false until a delivery contract gate says
  otherwise.

## 10. Verdict

READY FOR CODE FIX.

The next code correction should be a narrow Matrix Script Preview-Material Loop
PR based on this realignment. It should cite Bucket A, this execution note, and
the four-layer state boundary above before touching templates or tests.
