# Matrix Script Delivery Center — Result-Oriented Wireframe v1

Date: 2026-05-07
Status: **Design package only.** Low-fi wireframe of the Matrix Script Delivery Center built around publishable output. Companion to [matrix_script_result_oriented_ui_plan_v1.md](matrix_script_result_oriented_ui_plan_v1.md).
Authority of creation: same as the result-oriented UI plan §0. This wireframe does not redefine product authority, contract authority, surface authority, or wave authority.

This document does **not** open any implementation gate, mutate any contract / schema / sample / template / test / runtime, or touch Hot Follow / Digital Anchor / Asset Supply files.

---

## 1. Page goal

The Delivery Center is the **publishable-output** surface for a Matrix Script task. It is organised around the primary deliverable `final_video` and the supporting deliverables (subtitle / audio / copy_bundle / metadata / manifest / scene_pack / publish_status). It is read-mostly: the only authoring affordances are publish-event posts to the Phase D.0 closure (and only when publish readiness clears).

It must answer the operator's six 10-second questions, with a strong bias toward "Is there a publishable video result yet?" (question 6) and "Which candidate is currently recommended?" (question 5):

1. What is this task trying to produce? — header subject + line marker.
2. Which variants are worth generating or reviewing? — primary slot variant + the variant tabs (one per per-variation lane row).
3. What is blocked right now? — publish-readiness banner.
4. What should I do next? — readiness banner action label.
5. Which candidate is currently recommended? — primary slot ⭐ marker.
6. Is there a publishable video result yet? — primary slot status pill.

---

## 2. Layout (low-fi, single page)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  DELIVERY CENTER · matrix_script · v1                                Stage: ●可发布   Result: ✓ ready     │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  健身房新会员转化短视频                                                                                      │
│                                                                                                              │
│  发布门禁: ✓ 可发布                                                                                          │
│  下一步:    选择渠道 / 账号，记录发布事件                                                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  主交付 · final_video                                                                                       │
│  ─────────────────                                                                                          │
│  推荐候选: 候选 1 ⭐                                                                                        │
│  当前版本来源: ◉ current   (历史版本: 0)                                                                    │
│                                                                                                              │
│  ┌──────────────────────────────────────────────────┐                                                       │
│  │                                                    │                                                       │
│  │              [ 主成片 final_video ]                │                                                       │
│  │              (server-rendered placeholder           │                                                       │
│  │                + 服务器侧 final 媒介句柄)            │                                                       │
│  │              60s · zh-CN · 真诚 · 60s 慢节奏         │                                                       │
│  │                                                    │                                                       │
│  └──────────────────────────────────────────────────┘                                                       │
│                                                                                                              │
│  变体 tab:    [ 候选 1 ⭐ ]   [ 候选 2 ]   [ 候选 3 ]   [ 候选 4 ]                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  必需交付物                                                                                                  │
│  ──────────                                                                                                  │
│  ┌────────────────┬─────────────────┬──────────────┬─────────────────────────────────────┐                   │
│  │ 交付物          │ 必需 / 可选     │ 状态          │ 说明                                  │                   │
│  ├────────────────┼─────────────────┼──────────────┼─────────────────────────────────────┤                   │
│  │ final_video    │ 必需 · 阻塞发布  │ ✓ 可发布      │ 主成片：候选 1                        │                   │
│  │ subtitle       │ 必需 · 阻塞发布  │ ✓ 可发布      │ zh-CN 字幕已就绪                      │                   │
│  │ audio          │ 必需 · 阻塞发布  │ ✓ 可发布      │ zh-CN 配音已就绪                      │                   │
│  │ copy_bundle    │ 必需 · 不阻塞    │ ✓ 已生成      │ 标题 / hashtags / 评论文案 / CTA      │                   │
│  │ metadata       │ 必需 · 不阻塞    │ ✓ 已生成      │ 标题 / 描述 / 标签                    │                   │
│  │ manifest       │ 必需 · 不阻塞    │ ✓ 已生成      │ 交付清单                              │                   │
│  └────────────────┴─────────────────┴──────────────┴─────────────────────────────────────┘                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  可选交付物 (非阻塞)                                                                                         │
│  ─────────                                                                                                   │
│  scene_pack:   ◯ 未生成 · 不阻塞发布 · 可在工作台请求生成                                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  文案包                                                                                                      │
│  ────                                                                                                        │
│  标题:        "10 元体验，7 天看自己"                                                                        │
│  Hashtags:    #健身  #会员体验  #同城                                                                        │
│  CTA:         "评论区留言『体验』，私信领取本周名额"                                                          │
│  评论关键词:  减脂 · 体验 · 转化                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  发布状态 / 发布反馈                                                                       [ + 记录发布事件 ] │
│  ─────────────────                                                                                          │
│  ┌──────────┬──────────┬────────────────┬──────────────────┬───────────┬──────────────────┐                 │
│  │ 候选      │ 渠道      │ 账号           │ 发布时间          │ 状态      │ 链接 / 指标       │                 │
│  ├──────────┼──────────┼────────────────┼──────────────────┼───────────┼──────────────────┤                 │
│  │ 候选 1    │ 抖音      │ <账号 ID 待填> │ 尚未发布          │ ◐ pending │ —                │                 │
│  │ 候选 2    │ 视频号    │ <账号 ID 待填> │ 尚未发布          │ ◐ pending │ —                │                 │
│  └──────────┴──────────┴────────────────┴──────────────────┴───────────┴──────────────────┘                 │
│                                                                                                              │
│  发布事件日志: (append-only)                                                                                 │
│  · 2026-05-07 09:32  operator_note  候选 1: "选定为推荐版本"                                                 │
│                                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  迭代建议                                                                                                    │
│  ──────                                                                                                      │
│  完成本轮发布后，建议:                                                                                       │
│   · 候选 2 / 候选 4 节奏接近，发布后看七日完播率，决定下一轮是否合并                                          │
│   · 候选 3 男声坚定方向是首次尝试，下一轮可单独跑量观测                                                      │
│                                                                                                              │
│  [ 归档此任务 ]                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Header

| Field | Operator label | Source |
|---|---|---|
| Page title | "DELIVERY CENTER · matrix_script · v1" | static + `packet_version` |
| Stage badge | "Stage: ●\<stage label\>" | `derive_matrix_script_eight_stage_state` |
| Result pill | "Result: ✓ / ◐ / 🚧 \<status label\>" | `derive_matrix_script_task_area_result_status` (or workbench result summary; both render the same closed values) |
| Subject | (rendered as page subtitle) | `task["config"]["entry"].subject` |
| Publish-readiness banner | "发布门禁: \<label\>" + "下一步: \<action\>" | `compute_publish_readiness` (head_reason → operator label via `HEAD_REASON_LABELS_ZH`); next-action via banner-specific operator-language helper consuming the same producer |

### 3.1 Forbidden in header

- Validator report drawer link.
- Vendor / model / provider / engine label.
- Re-derived `publishable` bool — Block must consume `compute_publish_readiness` directly (RC-A7).

---

## 4. Block A — 主交付 final_video (Primary deliverable slot)

### 4.1 Operator question answered

"Is there a publishable video result yet?" (question 6) and "Which candidate is currently recommended?" (question 5).

### 4.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Recommended candidate | "推荐候选: 候选 N ⭐" | `derive_matrix_script_delivery_comprehension.final_video_primary.recommended_candidate_label` |
| Provenance pill | "当前版本来源: ◉ current / 历史" | L3 `final_provenance` (Recovery PR-1 emitter) |
| Historical version count | "历史版本: M" | per-task historical-version count from delivery_comprehension |
| Primary media slot | server-rendered placeholder + final media handle (when present); explicit tracked-gap operator-language line when absent (RC-R8: never fabricated URL) | `derive_matrix_script_delivery_comprehension.final_video_primary.media_handle` |
| Per-variant tabs | one tab per variant; `⭐` on the recommended one | one row per `derive_matrix_script_preview_compare_view[]` (re-projected for tab usage) |

### 4.3 Bindings

| UI element | Backend | File |
|---|---|---|
| Primary slot recommended marker | `derive_matrix_script_delivery_comprehension.final_video_primary` | gateway/app/services/matrix_script/delivery_comprehension.py |
| Provenance pill | L3 `final_provenance` Recovery PR-1 emitter; **today rendered as inferred label** (BG-2 gap) | gateway/app/services/matrix_script/* (Recovery PR-1 substrate) |
| Media handle | `result_packet_binding.artifact_lookup` for `final_video` row (E.MS.1 / Plan E PR-1 has closed this lookup for `final_video`) | gateway/app/services/matrix_script/delivery_comprehension.py + result_packet_binding_artifact_lookup_contract_v1.md |
| Variant tabs | `derive_matrix_script_preview_compare_view` per-variant rows | gateway/app/services/matrix_script/preview_compare_view.py |

### 4.4 Forbidden in Block A

- Fake `final_video` URL or fabricated `publish_url` echo (RC-R8 audit).
- Inline editor or re-trim affordance — re-runs go through Workbench Block D regenerate, not from here.
- Vendor / model / provider / engine name (e.g. "rendered by gemini").
- Comparison split-view of two variants — split-view lives in Workbench Block E preview compare; here the surface stays focused on the recommended primary.

### 4.5 Empty-state rendering

When no `RECOMMENDED_BUCKET_PUBLISHABLE` candidate exists yet:

- Header pill renders 🚧 blocked (consistent with Task Area result pill).
- Block A renders a single tracked-gap operator-language line: "暂无推荐主成片 · 请回到工作台完成校对".
- No fabricated thumbnail.

---

## 5. Block B — 必需交付物 (Required Deliverables)

### 5.1 Operator question answered

"Is there a publishable video result yet?" (decomposed: which required pieces are present and which block publishing).

### 5.2 Row layout (binding-and-exhaustive for this wave)

The Matrix Script line policy currently required by the Plan E delivery zoning landing is:

| Deliverable | required | blocking_publish | Source of zoning policy |
|---|---|---|---|
| variation_manifest | true | true | matrix_script/delivery_binding.py |
| slot_bundle | true | true | same |
| subtitle_bundle | true | true (when subtitles capability enabled) | same |
| audio_preview | true | true (when dub capability enabled) | same |
| copy_bundle | true | false | same |
| metadata | true | false | same |
| manifest | true | false | same |
| scene_pack | false | false (`SCENE_PACK_BLOCKING_ALLOWED = False`) | same; rendered in Block C below |

### 5.3 Per-row fields

| Column | Operator label | Source | Closed enum |
|---|---|---|---|
| Deliverable | "交付物" | `derive_matrix_script_delivery_comprehension` row id mapped to operator label | — |
| Required / blocking | "必需 · 阻塞发布" / "必需 · 不阻塞" / "可选 · 不阻塞" | `factory_delivery_contract_v1` `required` + `blocking_publish` (Plan C amendment) | three closed combinations |
| Status | `✓ 可发布` / `◐ 部分就绪` / `🚧 缺失` / `◯ 已生成` | `derive_matrix_script_delivery_ready_package` row state | `READINESS_PUBLISHABLE_NOW` / `READINESS_GATED` / `READINESS_TRACKED_GAP` / `READINESS_ALREADY_PUBLISHED` / `READINESS_ALREADY_FAILED` |
| Description | operator-language line | per-row narrator helper inside `delivery_comprehension.py` | — |

### 5.4 Bindings

| UI element | Backend | File |
|---|---|---|
| Required / blocking column | `factory_delivery_contract_v1` Plan C fields | [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) |
| Per-row status | `derive_matrix_script_delivery_ready_package` | gateway/app/services/matrix_script/delivery_ready_package_view.py |
| Per-row narration | `derive_matrix_script_delivery_comprehension` | gateway/app/services/matrix_script/delivery_comprehension.py |
| Cross-row publish-blocking aggregation | `compute_publish_readiness` | publish_readiness producer (Recovery PR-1) |

### 5.5 Forbidden in Block B

- Per-row vendor / model / provider / engine column.
- Per-row "rerun" action button (rerun lives in Workbench Block D / E).
- Re-derived publish-blocking flag outside `compute_publish_readiness`.

---

## 6. Block C — 可选交付物 scene_pack (Optional Scene Pack — non-blocking)

### 6.1 Discipline

- **Always non-blocking.** `SCENE_PACK_BLOCKING_ALLOWED = False` is the binding constant; `factory_delivery_contract_v1` Plan C amendment carries the same invariant.
- Operator may always advance other capabilities when scene_pack is incomplete.
- Header gate badge does not change because scene_pack is incomplete.

### 6.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Header line | "scene_pack: \<status\> · 不阻塞发布 · 可在工作台请求生成" | `derive_matrix_script_delivery_comprehension.optional_non_blocking.scene_pack` |
| Status | `◯ 未生成` / `◐ 部分就绪` / `✓ 已生成` | `derive_matrix_script_delivery_ready_package` for scene_pack row |
| Jump to workbench | inline link "在工作台请求生成" → `/tasks/{id}#scene-pack` | template anchor |

### 6.3 Forbidden in Block C

- Any "block publish" semantics — even if upstream payload claims `pack.required = True`, the Matrix Script Delivery Center renders scene_pack as non-blocking per the line policy hard-coding.
- Vendor / model / provider / engine label.

---

## 7. Block D — 文案包 (Copy Bundle)

### 7.1 Operator question answered

Side-supports question 1 (what is being produced) and operator readiness for publish.

### 7.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Title | "标题" | `derive_matrix_script_delivery_copy_bundle().title` |
| Hashtags | "Hashtags" | `derive_matrix_script_delivery_copy_bundle().hashtags` |
| CTA | "CTA" | `derive_matrix_script_delivery_copy_bundle().cta` |
| Comment keywords | "评论关键词" | `derive_matrix_script_delivery_copy_bundle().comment_keywords` |

### 7.3 Bindings

| UI element | Backend | File |
|---|---|---|
| All four fields | `derive_matrix_script_delivery_copy_bundle` | gateway/app/services/matrix_script/delivery_copy_bundle_view.py |

### 7.4 Forbidden in Block D

- Free-text editing in this wave (deferred).
- Vendor / model / provider / engine label.

---

## 8. Block E — 发布状态 / 发布反馈 (Publish Status / Publish Feedback)

This block is the **Publish Feedback sub-zone** — the operator-visible portion of the Phase D.0 closure. It renders the current row table, the append-only event log, and the "+ 记录发布事件" affordance.

### 8.1 Operator question answered

Post-publish observation. Also satisfies the iteration loop into Block F.

### 8.2 Row table fields (per-variant)

| Column | Operator label | Source | Closed enum |
|---|---|---|---|
| Variant | "候选 N" | `variation_feedback[].variation_id` mapped to operator label "候选 N" | — |
| Channel | "渠道" | `variation_feedback[].channel` | — |
| Account | "账号" | `variation_feedback[].account` (rendered as tracked-gap "<账号 ID 待填>" when absent) | — |
| Publish time | "发布时间" | `variation_feedback[].publish_time` (or fallback ordering: D.1 publish-state-mutating record → row.last_event_recorded_at → metrics captured_at → "尚未发布") | — |
| Publish status | "状态" | `variation_feedback[].publish_status` mapped to ◐ pending / ✓ published / 🚧 failed / ⊘ retracted | `D1_PUBLISH_STATUS_VALUES` |
| Link / metrics | "链接 / 指标" | `variation_feedback[].publish_url` (rendered only when present — RC-R8) + `channel_metrics` snapshot summary | — |

### 8.3 Event log

Append-only per `feedback_closure_records[]`:

| Column | Operator label | Source |
|---|---|---|
| Timestamp | "发布事件日志" | `feedback_closure_records[].recorded_at` |
| Event kind | (operator-language) | `feedback_closure_records[].event_kind` mapped to operator label |
| Subject | per-event description | event-specific helper |

### 8.4 Bindings

| UI element | Backend | File |
|---|---|---|
| Row table | Phase D.0 closure `variation_feedback[]` | gateway/app/services/matrix_script/publish_feedback_closure.py |
| Event log | `feedback_closure_records[]` | same |
| Closure read | `get_closure_view_for_task` (read-only on this surface) | gateway/app/services/matrix_script/closure_binding.py |
| Event post | `POST /api/matrix-script/closures/{task_id}/events` with closed `D1_EVENT_KINDS` | gateway/app/routers/matrix_script_closure.py |
| Closed enums | `D1_EVENT_KINDS`, `D1_PUBLISH_STATUS_VALUES`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES`, `CHANNEL_METRICS_KEYS`, `ACTOR_KINDS` | gateway/app/services/matrix_script/publish_feedback_closure.py |

### 8.5 Allowed actions

| Action | Operator label | Wired to | Closed precondition |
|---|---|---|---|
| Record publish | "+ 记录发布事件" → form: channel / account / publish_url / publish_status / metrics_snapshot | `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_publish"` | `compute_publish_readiness.publishable == True` |
| Record retract | (event row "撤回此变体") | same with `event_kind == "operator_retract"` | row's `publish_status == "published"` |
| Record metrics snapshot | (event row "记录指标快照") | same with `event_kind == "metrics_snapshot"` | row's `publish_status == "published"` |
| Record operator note | (event row "记录备注") | same with `event_kind == "operator_note"` (optional `review_zone ∈ REVIEW_ZONE_VALUES`) | always allowed |

### 8.6 Forbidden in Block E

- Mutation / deletion of any closure event (the log is append-only — `feedback_closure_records[]` semantics).
- Re-derived publish state outside `D1_PUBLISH_STATUS_VALUES` enum.
- Fake `publish_url` echo (RC-R8); `publish_url` column renders blank when source field is absent.
- Vendor / model / provider / engine column.
- Cross-line publish view (this surface is matrix_script-only).

---

## 9. Block F — 迭代建议 (Iteration Recommendation) + Archive

### 9.1 Operator question answered

"What should I do next?" after publish — the loop back into the next iteration.

### 9.2 Fields rendered

| Field | Operator label | Source |
|---|---|---|
| Iteration recommendation lines | "完成本轮发布后，建议:" + bulleted operator-language lines | `derive_matrix_script_publish_backfill_readiness.next_iteration_text` (gap taxonomy → operator-language sentence) |
| Archive button | "归档此任务" | posts an `event_kind == "operator_publish"` (or system-decided) followed by a `record_kind == "archive_action"` event per existing closure semantics |

### 9.3 Bindings

| UI element | Backend | File |
|---|---|---|
| Iteration text | `derive_matrix_script_publish_backfill_readiness` | gateway/app/services/matrix_script/publish_backfill_readiness_view.py |
| Archive event | `feedback_closure_records[]` with `record_kind == "archive_action"` | gateway/app/services/matrix_script/publish_feedback_closure.py |

### 9.4 Forbidden in Block F

- Cross-task aggregation (recommendations are per-task in this wave).
- Auto-archive on metrics threshold (operator-initiated only).

### 9.5 Backend gap

- BG-5 (per result-oriented UI plan §11.1): iteration recommendation grounded in actual metrics history is gated to a future post-Plan-E analytics wave. This wave renders `next_iteration_text` from gap taxonomy heuristics, not from metric-grounded analysis.

---

## 10. Cross-block discipline

| Discipline | Rule | Authority |
|---|---|---|
| Single source of truth for `publishable` | every block consuming "publishable" reads `compute_publish_readiness` directly | recovery gate spec RC-A7 |
| No fake `final_video` / fabricated `publish_url` | tracked-gap rows render operator-language text; never synthesised URLs | recovery gate spec RC-R8 |
| No vendor / model / provider / engine | structurally absent from every block on this surface | factory_packet_envelope_contract_v1 E5 + validator R3 |
| Operator language only | every label originates from `HEAD_REASON_LABELS_ZH` or per-helper operator-language helper | result-oriented UI plan §5 |
| Append-only closure | Block E is read-only on existing rows; new events post to closure D.1 only | publish_feedback_closure_contract_v1 §"append-only" |
| Scene pack non-blocking | `SCENE_PACK_BLOCKING_ALLOWED = False` is binding; no block treats scene_pack as a publish blocker | matrix_script/delivery_binding.py + factory_delivery_contract_v1 Plan C |
| No Digital Anchor / Hot Follow / Asset Supply file touch | this surface neither references nor reads those lines | recovery amendment §7 + post-OWC addendum §2.3 |

---

## 11. Six-question test (delivery-center-only re-statement)

When the operator opens the Delivery Center cold:

1. "What is this task trying to produce?" → header subject + line marker.
2. "Which variants are worth generating or reviewing?" → variant tabs row.
3. "What is blocked right now?" → header readiness banner.
4. "What should I do next?" → header banner action label + iteration recommendation block.
5. "Which candidate is currently recommended?" → primary slot ⭐ marker.
6. "Is there a publishable video result yet?" → primary slot status pill + Block B required-deliverable row aggregation.

All six are above the fold (Blocks A → F render in document order on a single scrollable surface).

---

## 12. Backend mapping table (delivery-center-scoped)

| Block / region | UI element | Backend feed | Service file | Closed enum |
|---|---|---|---|---|
| Header | stage badge | `derive_matrix_script_eight_stage_state` | task_area_convergence.py | `STAGE_*` |
| Header | result pill | `derive_matrix_script_task_area_result_status` | result_status_view.py | `STATUS_*` |
| Header | readiness banner + next-action | `compute_publish_readiness` + operator-language label | publish_readiness producer | `head_reason` enum → operator label |
| A | recommended candidate marker | `derive_matrix_script_delivery_comprehension.final_video_primary` | delivery_comprehension.py | gated by `RECOMMENDED_BUCKET_PUBLISHABLE` |
| A | provenance pill | L3 `final_provenance` (Recovery PR-1 emitter; BG-2 gap as first-class field) | matrix_script Recovery PR-1 substrate | `current` / `historical` |
| A | media handle | `result_packet_binding.artifact_lookup` for `final_video` row | E.MS.1 / Plan E PR-1 substrate + delivery_comprehension.py | — |
| A | variant tabs | per-variant rows of `derive_matrix_script_preview_compare_view` | preview_compare_view.py | `RECOMMENDED_BUCKET_*` |
| B | required / blocking column | `factory_delivery_contract_v1` Plan C amendment | docs/contracts/factory_delivery_contract_v1.md | three closed combinations |
| B | per-row status | `derive_matrix_script_delivery_ready_package` | delivery_ready_package_view.py | `READINESS_*` |
| B | per-row narration | `derive_matrix_script_delivery_comprehension` | delivery_comprehension.py | — |
| B | cross-row publish blocker | `compute_publish_readiness` | publish_readiness producer | `head_reason` |
| C | scene_pack non-blocking | `SCENE_PACK_BLOCKING_ALLOWED = False` | matrix_script/delivery_binding.py | constant |
| D | copy bundle fields | `derive_matrix_script_delivery_copy_bundle` | delivery_copy_bundle_view.py | — |
| E | row table | Phase D.0 closure `variation_feedback[]` | publish_feedback_closure.py | `D1_PUBLISH_STATUS_VALUES` |
| E | event log | `feedback_closure_records[]` | publish_feedback_closure.py | `D1_EVENT_KINDS`, `RECORD_KINDS` |
| E | event post | `POST /api/matrix-script/closures/{task_id}/events` | matrix_script_closure router | same |
| F | iteration recommendation | `derive_matrix_script_publish_backfill_readiness` | publish_backfill_readiness_view.py | `READINESS_*` |
| F | archive | `record_kind == "archive_action"` event | publish_feedback_closure.py | `RECORD_KINDS` |

---

## 13. Gaps surfaced by this wireframe (cross-reference to result-oriented UI plan §11)

| Gap | Type | Symptom in Delivery Center |
|---|---|---|
| BG-1 | backend gap | Header readiness banner cannot consume L4 advisory `recommended_next_action` text until L4 advisory producer ships; today it falls back to operator-language label derived from `head_reason` |
| BG-2 | backend gap | Block A provenance pill renders inferred label from Recovery PR-1 substrate; first-class L3 emission of `final_provenance` is gated to a future Plan E phase |
| BG-3 | backend gap | Variant tabs in Block A may render tracked-gap thumbnails for non-`final_video` rows until artifact_lookup expansion lands |
| BG-4 | backend gap | Block E "raw payload" link from `metrics_snapshot` cannot be opened until a resolver service ships |
| BG-5 | backend gap | Block F iteration recommendation is not yet metric-grounded |
| PG-1 | presenter gap | Header banner falls back to "未就绪" for less-common `head_reason` values |
| PG-3 | presenter gap | Block E status column may render raw `retracted` for closure D.1 retracted state |
| PG-4 | presenter gap | Archive action lacks an iteration-hint trailer |
| PG-5 | presenter gap | Header lacks a `hot_follow ✓` reference badge |
| IG-1 | interaction gap | "Open publish feedback" jump from Task Area lands here on `#publish-feedback` anchor; Delivery Center already exposes Block E inline so this is fully satisfied at the surface — gap remains only in Task Area card button row |
| IG-3 | interaction gap | Block F lacks a one-click "duplicate as new task" affordance |
| IG-5 | interaction gap | Block A primary slot has no inline `final_video` player; operators jump to R2/CDN URL |

None of the above gaps are solved in this design step.

---

## 14. Reading declaration

This wireframe consumes the same reading set as [matrix_script_result_oriented_ui_plan_v1.md §14](matrix_script_result_oriented_ui_plan_v1.md). Additional surface authority specifically consulted: [docs/design/surface_delivery_center_lowfi_v1.md](surface_delivery_center_lowfi_v1.md). Additional contract authority specifically consulted: [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md), [docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md](../contracts/matrix_script/publish_feedback_closure_contract_v1.md), [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md), [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md), [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md).

Documentation only — no code, no UI implementation, no contract authoring, no schema mutation, no template change, no test change, no runtime change.
