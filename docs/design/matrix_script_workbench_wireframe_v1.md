# Matrix Script Workbench — Result-Oriented Wireframe v1

Date: 2026-05-07
Status: **Design package only.** Low-fi wireframe of the Matrix Script Workbench as a result-oriented production workbench, not a packet inspection page. Companion to [matrix_script_result_oriented_ui_plan_v1.md](matrix_script_result_oriented_ui_plan_v1.md).
Authority of creation: same as the result-oriented UI plan §0. This wireframe does not redefine product authority, contract authority, surface authority, or wave authority.

This document does **not** open any implementation gate, mutate any contract / schema / sample / template / test / runtime, or touch Hot Follow / Digital Anchor / Asset Supply files.

---

## 1. Page goal

The Workbench is the **execution shell** for an open Matrix Script task. It must answer the operator's six 10-second questions on first paint, before any drawer opens:

1. What is this task trying to produce? — Block A.
2. Which variants are worth generating or reviewing? — Block C + Block E.
3. What is blocked right now? — Block A header summary + Block D.
4. What should I do next? — Block A "下一步" line + Block D primary action.
5. Which candidate is currently recommended? — Block E recommended marker.
6. Is there a publishable video result yet? — Block F readiness teaser + jump to Delivery.

The operator must **never** be required to interpret packet internals (`cell_id`, `slot_id`, axis-tuple raw label, `content://` handle, validator report) to answer those questions.

---

## 2. Layout (low-fi, single page)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  WORKBENCH · matrix_script · v1            Stage: ●待校对   Result: ◐ ready · 待选定推荐版本                │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  A. 任务头 / 目标摘要                                                                                       │
│  ──────────────────                                                                                         │
│  主题: 健身房新会员转化短视频                                                                                │
│  受众: B2C 25-40 城市健身用户         目标平台: 抖音                  目标语言: zh-CN                       │
│  当前总状态: ◐ 已生成 4 / 4 变体, 等待校对                                                                  │
│  当前阻塞:    暂无                                                                                          │
│  下一步:      开始校对 4 个候选版本，选定推荐版本后前往交付                                                   │
│  [ 前往交付中心 ]  [ 前往发布反馈 ]                                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  B. 脚本结构                                                                                                │
│  ──────────                                                                                                 │
│  Hook  (前 3 秒): "10 元体验 7 天，老板都怕你坚持不下去 …"                                                    │
│  Body  (中段):    1) 第三方实拍学员 7 天前后对比                                                             │
│                  2) 教练讲明全套训练 / 饮食安排                                                              │
│                  3) 老用户口碑 + 续费率                                                                      │
│  CTA   (结尾):    "评论区留言『体验』，私信领取本周名额"                                                      │
│  关键词: 减脂 · 体验 · 转化 · 教练                                                                          │
│  禁用词: 包瘦 · 7 天暴瘦 · 治愈                                                                              │
│                                                                                                              │
│  (operator-readable view; no axis-tuple raw labels; no slot_id / cell_id)                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  C. 变体策略                                                                                                │
│  ──────────                                                                                                 │
│  当前变体数: 4                                                                                              │
│                                                                                                              │
│  ┌──────────┬──────────────┬───────────────┬───────────────┬───────────────┬─────────────────┐              │
│  │ 变体      │ 语气         │ 受众          │ 节奏 / 时长    │ 视觉角度       │ 字幕 / 配音       │              │
│  ├──────────┼──────────────┼───────────────┼───────────────┼───────────────┼─────────────────┤              │
│  │ 候选 1    │ 真诚         │ 偏新会员       │ 60s 慢节奏     │ 实拍 + 口播     │ zh-CN · 女声温和 │              │
│  │ 候选 2    │ 真诚         │ 偏新会员       │ 30s 快节奏     │ 实拍剪辑        │ zh-CN · 女声温和 │              │
│  │ 候选 3    │ 自信         │ 偏续费用户     │ 45s 中节奏     │ 教练正向推荐   │ zh-CN · 男声坚定 │              │
│  │ 候选 4    │ 玩味         │ 偏新会员       │ 30s 快节奏     │ 二创 / 反差     │ zh-CN · 女声活泼 │              │
│  └──────────┴──────────────┴───────────────┴───────────────┴───────────────┴─────────────────┘              │
│                                                                                                              │
│  (each row reads as why this variant exists, not as which axis-tuple it inherits)                           │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  D. 生成 / 重新生成                                                                                         │
│  ─────────────                                                                                              │
│  主操作: [ 生成 4 个变体 ]    (Stage: 待配置 → 生成中 时启用)                                                 │
│  次操作: [ 重新生成被阻塞的变体 (0) ]                                                                        │
│                                                                                                              │
│  当前前置条件:                                                                                              │
│   · 脚本结构: ✓ 已就绪                                                                                      │
│   · 变体策略: ✓ 已就绪                                                                                      │
│   · 语种支持: ✓ zh-CN                                                                                       │
│  当前阻塞原因: 暂无                                                                                          │
│                                                                                                              │
│  (no provider / model / engine selector — generation mode is system-decided)                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  E. 候选评审                                                                                                │
│  ───────                                                                                                    │
│  ┌── 候选 1 ───────────────────────────────────────────────────────────────────────────────────────┐         │
│  │ 推荐 ⭐  · 状态: ◐ 已成片 待校对                                                                  │         │
│  │ ┌──────────────┐                                                                                 │         │
│  │ │ [预览占位]    │   字幕: ✓ 已就绪    配音: ✓ 已就绪    交付包: ◐ 部分就绪                       │         │
│  │ │  60s          │   QC:  ✓ 时长 ✓ 清晰 ✓ 字幕可读                                                │         │
│  │ │               │   评审区:  [字幕 ✓]  [配音 ✓]  [文案 ◐]  [CTA ✓]                              │         │
│  │ └──────────────┘                                                                                 │         │
│  │ [ 选定为推荐版本 ]   [ 提交分区评审意见 ]   [ 重新生成此变体 ]                                     │         │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘         │
│  ┌── 候选 2 ───────────────────────────────────────────────────────────────────────────────────────┐         │
│  │ 状态: ◐ 已成片 待校对                                                                            │         │
│  │ ...                                                                                              │         │
│  │ [ 选定为推荐版本 ]   [ 提交分区评审意见 ]   [ 重新生成此变体 ]                                     │         │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘         │
│  ...                                                                                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  F. 交付概览                                                                                                │
│  ───────                                                                                                    │
│  发布门禁: ◐ 待选定推荐版本                                                                                  │
│  必需交付: final_video ◐  ·  subtitle ✓  ·  audio ✓  ·  copy_bundle ◐  ·  metadata ✓  ·  manifest ✓        │
│  可选 scene_pack: ◯ 未生成 (非阻塞)                                                                         │
│                                                                                                              │
│  [ 前往交付中心查看完整成片 ]                                                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Block A — 任务头 / 目标摘要 (Task Header / Goal Summary)

### 3.1 Operator question answered

"What is this task trying to produce?" + "What is blocked right now?" + "What should I do next?"

### 3.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Subject | "主题" | `task["config"]["entry"].subject` (sanitised) |
| Audience | "受众" | `task["config"]["entry"].audience` |
| Target platform | "目标平台" | `task["config"]["entry"].target_platform` |
| Target language | "目标语言" | `task["config"]["entry"].target_language` |
| Current overall status | "当前总状态" | `derive_matrix_script_workbench_result_summary().status_label` (RC PR-1) |
| Current blocker | "当前阻塞" | `derive_matrix_script_workbench_result_summary().blocker_label` |
| Next recommended action | "下一步" | `derive_matrix_script_workbench_result_summary().next_action_label` |

### 3.3 Bindings

| UI element | Backend | File |
|---|---|---|
| Stage badge in header | `derive_matrix_script_eight_stage_state` | gateway/app/services/matrix_script/task_area_convergence.py |
| Result pill (`STATUS_*`) | `derive_matrix_script_workbench_result_summary` | gateway/app/services/matrix_script/result_status_view.py |
| Comprehension header (任务身份 / 四区对齐 / 下一步 anchor) | `derive_matrix_script_workbench_comprehension` | gateway/app/services/matrix_script/workbench_comprehension.py |
| Jump button "前往交付中心" | route `/tasks/{id}/publish-hub` (existing) | gateway/app/routers/tasks.py |
| Jump button "前往发布反馈" | publish-hub anchor `#publish-feedback` | template anchor |

### 3.4 Forbidden in Block A

- `cell_id`, `slot_id`, `content://` handle, `binds_cell_id`, `script_slot_ref`.
- Validator report drawer (kept off the result-oriented surface; engineering inspector available behind a separate route, out of scope).
- Vendor / model / provider / engine label.
- Raw English `head_reason` enum value (must be operator language).

---

## 4. Block B — 脚本结构 (Script Structure)

### 4.1 Operator question answered

"What is this task trying to produce?" (content level).

### 4.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Hook | "Hook (前 3 秒)" | `derive_matrix_script_script_structure_view().hook` |
| Body points | "Body (中段)" | `derive_matrix_script_script_structure_view().body_points` (list) |
| CTA | "CTA (结尾)" | `derive_matrix_script_script_structure_view().cta` |
| Keywords | "关键词" | `derive_matrix_script_script_structure_view().keywords` |
| Forbidden terms | "禁用词" | `derive_matrix_script_script_structure_view().forbidden_terms` |

### 4.3 Bindings

| UI element | Backend | File |
|---|---|---|
| All five fields | `derive_matrix_script_script_structure_view` | gateway/app/services/matrix_script/script_structure_view.py |
| Underlying truth | Phase A entry + `slot_pack` body refs (dereferenced server-side) | matrix_script/task_entry_contract_v1.md + slot_pack_contract_v1.md |

### 4.4 Discipline

- This block is **read-only** in this wave. Operator-driven Phase B authoring is forbidden by Plan E gate spec §4.3.
- Operator never sees `slot_id`, `binds_cell_id`, or `content://` handles. The presenter dereferences them server-side.
- If a body field is missing, the block renders an explicit tracked-gap operator-language line (e.g. "Body 内容尚未结构化") — never an opaque ref token.

### 4.5 Forbidden in Block B

- Raw `slot_pack.delta.slots[]` rendering. (That rendering remains in [panel_matrix_script_variation_lowfi_v1.md](panel_matrix_script_variation_lowfi_v1.md), which targets the engineer-facing inspector pane, not the result-oriented workbench.)
- Free-text editing of Hook / Body / CTA in this wave (interaction gap IG-A, future Plan E phase).

---

## 5. Block C — 变体策略 (Variant Strategy)

### 5.1 Operator question answered

"Which variants are worth generating or reviewing?"

### 5.2 Per-variant row fields

| Column | Operator label | Source |
|---|---|---|
| Variant index | "候选 N" | derived from `variation_matrix.delta.cells[]` ordering, displayed as "候选 1 / 2 / …" |
| Tone | "语气" | axis-tuple → operator label via `derive_matrix_script_readable_variants` axis-tuple dictionary |
| Audience | "受众" | same |
| Pacing / length | "节奏 / 时长" | same; length grouped into `30s 快节奏` / `45s 中节奏` / `60s 慢节奏` operator buckets |
| Visual angle | "视觉角度" | same |
| Subtitle / dub differentiator | "字幕 / 配音" | same; expanded to operator-language "zh-CN · 女声温和" / "zh-CN · 男声坚定" |
| Why this variant | (tooltip on row hover) | `derive_matrix_script_readable_variants[].why_label` |

### 5.3 Bindings

| UI element | Backend | File |
|---|---|---|
| Variant rows | `derive_matrix_script_readable_variants` | gateway/app/services/matrix_script/readable_variant_view.py |
| Variant count badge | `derive_matrix_script_workbench_comprehension.variant_summary.count` | gateway/app/services/matrix_script/workbench_comprehension.py |
| Why-this-variant tooltip | `derive_matrix_script_readable_variants[].why_label` | gateway/app/services/matrix_script/readable_variant_view.py |

### 5.4 Forbidden in Block C

- Raw axis-tuple labels (`tone=formal · audience=b2b · 60`) — they belong only in the engineering inspector panel, not on the result-oriented workbench.
- `cell_id` / `script_slot_ref` columns.
- Vendor / model / provider / engine column (e.g. "voice provider" / "gen engine").
- Donor / supply column.

### 5.5 Presenter gap

- PG-2 (per the result-oriented UI plan §11.2): some axis kinds may render developer-language tooltips. Closure path: extend `derive_matrix_script_readable_variants` axis-tuple → operator-label dictionary in a follow-on presenter-only PR.

---

## 6. Block D — 生成 / 重新生成 (Generate / Regenerate Action)

### 6.1 Operator question answered

"What should I do next?" + "What is blocked right now?"

### 6.2 Action layout

| Slot | Operator label | Action | Closed precondition |
|---|---|---|---|
| Primary | "生成 N 个变体" (N = variant count from Block C) | trigger generation for all variants currently in the variation matrix | `STAGE_PENDING_CONFIG` + `evidence.ready_state ∈ {ready}` |
| Secondary | "重新生成被阻塞的变体 (M)" (M = blocked variant count) | trigger regeneration for variants with `RECOMMENDED_BUCKET_BLOCKED` | M > 0 |

### 6.3 Precondition / blocker rendering

| Field | Operator label | Source |
|---|---|---|
| Precondition list | "当前前置条件" | `derive_matrix_script_recommended_action.preconditions[]` (operator-language) |
| Blocker reason | "当前阻塞原因" | `derive_matrix_script_recommended_action.blocked_reason_label` (mapped via `HEAD_REASON_LABELS_ZH` from `compute_publish_readiness.head_reason`) |

### 6.4 Bindings

| UI element | Backend | File |
|---|---|---|
| Recommended action lane | `derive_matrix_script_recommended_action` | gateway/app/services/matrix_script/recommended_action_view.py |
| Blocked-reason label dictionary | `HEAD_REASON_LABELS_ZH` (consumes `compute_publish_readiness.head_reason`) | publish_readiness producer (Recovery PR-1) |
| Primary action wiring | existing variation execution path; gated by `evidence.ready_state` | gateway/app/services/operator_visible_surfaces/wiring.py (matrix_script branch) |
| Secondary action wiring | same path scoped per `cell_id` | same; interaction gap IG-2 in result-oriented UI plan §11.3 |

### 6.5 Forbidden in Block D

- Vendor / model / provider / engine selector ("which model to use?", "which voice engine?").
- Free-text override of generation parameters (deferred to Plan E or later).
- Hidden state — every blocker reason must be visible in operator language; no "internal error" placeholder.
- Auto-trigger on page load — generation is always operator-initiated.

### 6.6 Interaction gap

- IG-2 "Regenerate blocked variant" per-variant action — design supports a single-button affordance per variant; current wiring scopes execution per `cell_id` but the Workbench's existing paths only expose the bulk regeneration. Closure path: future implementation PR scopes execution per `cell_id` as a thin presenter-side dispatch (no contract change).

---

## 7. Block E — 候选评审 (Result Review)

### 7.1 Operator question answered

"Which candidate is currently recommended?" + "What is blocked right now?" (per-variant) + "Is there a publishable video result yet?" (per-variant teaser).

### 7.2 Per-variant card layout

```
┌── 候选 N ──────────────────────────────────────────────────────────────────────┐
│ [推荐 ⭐]  · 状态: <stage 标签>                                                 │
│ ┌──────────────┐                                                                │
│ │ [预览占位]    │   字幕: <✓ / ◐ / ◯ / 🚧>    配音: <…>    交付包: <…>        │
│ │  <duration>  │   QC:   <时长 / 清晰 / 字幕可读 三项 ✓ / ◐ / 🚧>             │
│ │               │   评审区:  [字幕 ✓]  [配音 ✓]  [文案 ◐]  [CTA ✓]            │
│ └──────────────┘                                                                │
│ [ 选定为推荐版本 ]   [ 提交分区评审意见 ]   [ 重新生成此变体 ]                   │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Per-card field bindings

| Field | Operator label | Source |
|---|---|---|
| Recommended marker | ⭐ when `RECOMMENDED_BUCKET_PUBLISHABLE` and ranking position == 1 | `derive_matrix_script_preview_compare_view().recommended_variant_id` |
| Card status | one of: 草稿 / 生成中 / 已成片待校对 / 已选定 / 已发布 / 已阻塞 | `derive_matrix_script_preview_compare_view[].variant_state_label` (mapped from per-variant readiness + closure status) |
| Preview placeholder | tracked-gap thumbnail when no live preview is available; per-variation final media slot when artifact_lookup resolves | `derive_matrix_script_delivery_ready_package[]` per-row final media handle (BG-3 gap for non-`final_video` previews) |
| Duration | "60s" / "45s" / "30s" | per-variant length axis selection (operator-bucketed) |
| Subtitle status | ✓ ready · ◐ generating · ◯ pending · 🚧 tracked-gap | per-variant subtitle row of `derive_matrix_script_qc_diagnostics_view` |
| Audio status | same scale | per-variant dub row of `derive_matrix_script_qc_diagnostics_view` |
| Package readiness | `READINESS_PUBLISHABLE_NOW` / `READINESS_GATED` / `READINESS_TRACKED_GAP` rendered as `✓ / ◐ / 🚧` | `derive_matrix_script_delivery_ready_package` |
| QC checks | duration / clarity / subtitle readability — closed three-item set in Operator language | `derive_matrix_script_qc_diagnostics_view` |
| Review zone chips | one chip per `REVIEW_ZONE_VALUES` member with status (✓ approved / ◐ noted / 🚧 unreviewed) | `derive_matrix_script_review_zone_view` per-zone status |

### 7.4 Card actions

| Action | Operator label | Wired to | Closed precondition |
|---|---|---|---|
| Select recommended | "选定为推荐版本" | closure `event_kind == "operator_note"` with operator-language note "selected as recommended"; future closure D.1 enrichment may add an explicit `record_kind` (interaction gap IG-4) | `STAGE_AWAITING_REVIEW` + `RECOMMENDED_BUCKET_PUBLISHABLE` for that variant |
| Submit zone-scoped review | "提交分区评审意见" | `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_note"` + `review_zone ∈ REVIEW_ZONE_VALUES` | per-zone form (existing) |
| Regenerate this variant | "重新生成此变体" | execution path scoped by `cell_id` | `RECOMMENDED_BUCKET_BLOCKED` or operator override on `RECOMMENDED_BUCKET_UNDETERMINED` |

### 7.5 Bindings (consolidated)

| UI element | Backend | File |
|---|---|---|
| Per-variant card | `derive_matrix_script_preview_compare_view` | gateway/app/services/matrix_script/preview_compare_view.py |
| Recommended marker | `RECOMMENDED_BUCKET_PUBLISHABLE` | gateway/app/services/matrix_script/preview_compare_view.py + recommended_action_view.py |
| Subtitle / audio / package status | `derive_matrix_script_qc_diagnostics_view` + `derive_matrix_script_delivery_ready_package` | gateway/app/services/matrix_script/qc_diagnostics_view.py + delivery_ready_package_view.py |
| Review-zone chips | `derive_matrix_script_review_zone_view` | gateway/app/services/matrix_script/review_zone_view.py |
| Submit-review form action | matrix_script_closure router | gateway/app/routers/matrix_script_closure.py |
| Closure event closed enums | `D1_EVENT_KINDS`, `REVIEW_ZONE_VALUES` | gateway/app/services/matrix_script/publish_feedback_closure.py |

### 7.6 Forbidden in Block E

- Per-variant vendor / model / provider / engine label ("rendered by gemini-1.5-pro").
- Raw `cell_id` / `slot_id` / axis-tuple in the card.
- Fake `final_video` / fabricated `publish_url` for tracked-gap rows (RC-R8 audit).
- "Reset closure" / "delete event" affordances. The closure log is append-only.

### 7.7 Gaps surfaced

- BG-1 (advisory strip empty until L4 advisory producer ships).
- BG-3 (per-variant non-`final_video` preview is tracked-gap until artifact_lookup expansion lands).
- IG-4 (recommended-candidate confirmation event currently posts `operator_note`; future closure D.1 enrichment may transition state).

---

## 8. Block F — 交付概览 (Delivery Overview Teaser)

### 8.1 Operator question answered

"Is there a publishable video result yet?" — at workbench-level glance before the operator jumps to the Delivery Center.

### 8.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Publish gate | "发布门禁" | `compute_publish_readiness.publishable` mapped to `✓ 可发布` / `◐ 待 …` / `🚧 阻塞`; trailing operator-language reason from `head_reason` |
| Required deliverables | "必需交付" | each row of `derive_matrix_script_delivery_comprehension.required_blocking + required_non_blocking` rendered as `<name> <status>` (`✓ / ◐ / 🚧`) |
| Optional scene_pack | "可选 scene_pack" | `derive_matrix_script_delivery_comprehension.optional_non_blocking` (always non-blocking) |

### 8.3 Bindings

| UI element | Backend | File |
|---|---|---|
| Publish gate | `compute_publish_readiness` | publish_readiness producer (Recovery PR-1) |
| Required deliverable rows | `derive_matrix_script_delivery_comprehension` | gateway/app/services/matrix_script/delivery_comprehension.py |
| Scene_pack non-blocking | `SCENE_PACK_BLOCKING_ALLOWED = False` | gateway/app/services/matrix_script/delivery_binding.py |
| Jump button "前往交付中心" | route `/tasks/{id}/publish-hub` | existing |

### 8.4 Forbidden in Block F

- Inline `final_video` player. The full primary slot lives in the Delivery Center, not in the workbench teaser.
- Publish action button. Publishing happens in the Delivery Center / Publish Feedback zone only.
- Re-derived `publishable` bool (must consume `compute_publish_readiness` directly — RC-A7).

---

## 9. Cross-block discipline

| Discipline | Rule | Authority |
|---|---|---|
| Single truth source for publishable | every block claiming `publishable` consumes `compute_publish_readiness` directly | recovery gate spec RC-A7 |
| No fake `final_video` | tracked-gap rows render `🚧` operator-language text, not synthesised URLs | recovery gate spec RC-R8 |
| No vendor / model / provider / engine UI | structurally absent from every block in this wireframe | factory_packet_envelope_contract_v1 E5 + validator R3 |
| Operator language only | every label originates from `HEAD_REASON_LABELS_ZH` or per-service operator-language helper; no raw enum strings | result-oriented UI plan §5 |
| No second truth source | Block F's required-deliverable status comes from `derive_matrix_script_delivery_comprehension`; no block re-implements lane derivation | recovery gate spec RC-A7 |
| Append-only closure | Block E review actions and Block F publish action only post events; no event mutation / deletion | publish_feedback_closure_contract_v1 §"append-only" |
| Hot Follow benchmark only, no file touch | Hot Follow files are referenced for UX patterns; no Hot Follow file is changed by anything that follows from this design | recovery amendment §7 |
| Digital Anchor untouched | this design does not surface or reference Digital Anchor on Matrix Script flows | post-OWC addendum §2.3 |

---

## 10. Six-question test (workbench-only re-statement)

When the operator opens this Workbench cold, with no prior conversation context:

1. "What is this task trying to produce?" → Block A subject + audience + target language.
2. "Which variants are worth generating or reviewing?" → Block C variant table + Block E recommended marker.
3. "What is blocked right now?" → Block A "当前阻塞" line + Block D blocker reason.
4. "What should I do next?" → Block A "下一步" line + Block D primary action.
5. "Which candidate is currently recommended?" → Block E ⭐ marker on the recommended card.
6. "Is there a publishable video result yet?" → Block F publish gate banner.

All six are above the fold (Blocks A → F render in document order on a single scrollable surface).

---

## 11. Backend mapping table (workbench-scoped)

| Block | UI element | Backend feed | Service file |
|---|---|---|---|
| A | header / 任务身份 / 下一步 | `derive_matrix_script_workbench_comprehension` + `derive_matrix_script_workbench_result_summary` | workbench_comprehension.py + result_status_view.py |
| A | stage badge | `derive_matrix_script_eight_stage_state` | task_area_convergence.py |
| A | jump buttons | router routes (existing) | gateway/app/routers/tasks.py |
| B | hook / body / cta / keywords / forbidden | `derive_matrix_script_script_structure_view` | script_structure_view.py |
| C | variant table | `derive_matrix_script_readable_variants` | readable_variant_view.py |
| C | variant count | `derive_matrix_script_workbench_comprehension.variant_summary` | workbench_comprehension.py |
| D | preconditions / blocker | `derive_matrix_script_recommended_action` + `compute_publish_readiness.head_reason` | recommended_action_view.py + publish_readiness producer |
| D | primary / secondary actions | `wiring.build_operator_surfaces_for_workbench` (matrix_script branch) | gateway/app/services/operator_visible_surfaces/wiring.py |
| E | per-variant cards | `derive_matrix_script_preview_compare_view` | preview_compare_view.py |
| E | qc / status | `derive_matrix_script_qc_diagnostics_view` | qc_diagnostics_view.py |
| E | review zones | `derive_matrix_script_review_zone_view` | review_zone_view.py |
| E | per-variant package readiness | `derive_matrix_script_delivery_ready_package` | delivery_ready_package_view.py |
| E | submit-review form | matrix_script_closure router + `D1_EVENT_KINDS` + `REVIEW_ZONE_VALUES` | gateway/app/routers/matrix_script_closure.py + publish_feedback_closure.py |
| F | publish gate teaser | `compute_publish_readiness` | publish_readiness producer |
| F | required / optional lane | `derive_matrix_script_delivery_comprehension` + `SCENE_PACK_BLOCKING_ALLOWED` | delivery_comprehension.py + delivery_binding.py |

---

## 12. Gaps surfaced by this wireframe (cross-reference to result-oriented UI plan §11)

| Gap | Type | Symptom in this wireframe |
|---|---|---|
| BG-1 | backend gap | Block E has no advisory strip until L4 advisory producer ships |
| BG-2 | backend gap | Block A header cannot show definitive `current` vs `historical` provenance label |
| BG-3 | backend gap | Block E per-variant non-`final_video` preview thumbnails render as tracked-gap |
| PG-1 | presenter gap | Block A blocker label may fall back to "未就绪" for less-common `head_reason` values |
| PG-2 | presenter gap | Block C tooltips may render developer-language for unusual axis kinds |
| PG-3 | presenter gap | Block A blocker label may render `retracted` raw English for closure D.1 retracted state |
| IG-2 | interaction gap | Block D / Block E "重新生成此变体" needs per-`cell_id` execution path |
| IG-4 | interaction gap | Block E "选定为推荐版本" currently posts `operator_note`; closed-state transition for `STAGE_AWAITING_REVIEW → STAGE_FINAL_READY` is future closure enrichment |

None of the above gaps are solved in this design step.

---

## 13. Reading declaration

This wireframe consumes the same reading set as [matrix_script_result_oriented_ui_plan_v1.md §14](matrix_script_result_oriented_ui_plan_v1.md). Additional surface authority specifically consulted: [docs/design/surface_workbench_lowfi_v1.md](surface_workbench_lowfi_v1.md), [docs/design/panel_matrix_script_variation_lowfi_v1.md](panel_matrix_script_variation_lowfi_v1.md).

Documentation only — no code, no UI implementation, no contract authoring, no schema mutation, no template change, no test change, no runtime change.
