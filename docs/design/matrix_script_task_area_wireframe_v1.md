# Matrix Script Task Area — Result-Oriented Wireframe v1

Date: 2026-05-07
Status: **Design package only.** Low-fi wireframe of the Matrix Script Task Area as production management, not field inspection. Companion to [matrix_script_result_oriented_ui_plan_v1.md](matrix_script_result_oriented_ui_plan_v1.md).
Authority of creation: same as the result-oriented UI plan §0. This wireframe does not redefine product authority, contract authority, surface authority, or wave authority.

This document does **not** open any implementation gate, mutate any contract / schema / sample / template / test / runtime, or touch Hot Follow / Digital Anchor / Asset Supply files.

---

## 1. Page goal

The Task Area is the **production management** view for Matrix Script. The operator's job here is to see which tasks exist on this line, which are blocked, where the next attention should go, and how to enter the Workbench / Delivery Center / Publish Feedback for any individual task.

It is **not** a field inspector. It is **not** a packet debug surface. It is **not** a vendor-selection page.

The Task Area must answer the operator's six 10-second questions at the **task list / card** level (the Workbench answers them at the per-task level):

1. What is this task trying to produce? — card subject + line marker.
2. Which variants are worth generating or reviewing? — variant count + publishable count.
3. What is blocked right now? — current-blocker line.
4. What should I do next? — next-action chip (with explicit jump button).
5. Which candidate is currently recommended? — best-candidate marker.
6. Is there a publishable video result yet? — publishable variant count + result-status pill.

---

## 2. Layout (low-fi, single page)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  TASK AREA — matrix_script line                                                          [ + 新建任务 ]    │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Filter: [ Line: matrix_script ▾ ] [ Stage ▾ ] [ Result: ✓/◐/🚧 ▾ ] [ Search ___________ ]              │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌── Task Card ──────────────────────────────────────────────────────────────────────────────────┐        │
│  │  健身房新会员转化短视频         line: matrix_script                                               │        │
│  │                                                                                                  │        │
│  │  Stage: ● 待校对                  Result: ◐ ready · 待选定推荐版本                                │        │
│  │                                                                                                  │        │
│  │  变体数: 4         可发布版本数: 0/4         当前最佳候选: 候选 1 ⭐ (待选定)                      │        │
│  │  当前阻塞: 暂无                                                                                  │        │
│  │  最近一次生成: 2026-05-07 09:32                                                                  │        │
│  │  下一步: 开始校对 4 个候选版本，选定推荐版本后前往交付                                            │        │
│  │                                                                                                  │        │
│  │  [ 打开工作台 ]   [ 打开交付中心 ]   [ 打开发布反馈 ]                                              │        │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                                              │
│  ┌── Task Card ──────────────────────────────────────────────────────────────────────────────────┐        │
│  │  夏季会员续费提醒短视频          line: matrix_script                                              │        │
│  │  Stage: ● 已发布                  Result: ✓ completed · 已回填指标                                │        │
│  │  变体数: 3         可发布版本数: 3/3         当前最佳候选: 候选 2 ⭐ (已发布)                      │        │
│  │  当前阻塞: 暂无                                                                                  │        │
│  │  最近一次生成: 2026-05-04 18:11                                                                  │        │
│  │  下一步: 查看发布回填指标，决定是否进入下一轮迭代                                                 │        │
│  │                                                                                                  │        │
│  │  [ 打开工作台 ]   [ 打开交付中心 ]   [ 打开发布反馈 ]                                              │        │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                                              │
│  ┌── Task Card ──────────────────────────────────────────────────────────────────────────────────┐        │
│  │  教练 IP 起号 7 天矩阵            line: matrix_script                                             │        │
│  │  Stage: ● 生成中                  Result: 🚧 blocked · 等待视频生成器返回                         │        │
│  │  变体数: 6         可发布版本数: 0/6         当前最佳候选: —                                      │        │
│  │  当前阻塞: 视频生成器输入未就绪 (compose_not_ready)                                              │        │
│  │  最近一次生成: 2026-05-07 11:04                                                                  │        │
│  │  下一步: 等待视频生成器输入就绪 / 或回到工作台 检查脚本结构                                       │        │
│  │                                                                                                  │        │
│  │  [ 打开工作台 ]   [ 打开交付中心 ]   [ 打开发布反馈 ]                                              │        │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Header (page-level)

| Element | Operator label | Source |
|---|---|---|
| Page title | "TASK AREA — matrix_script line" | static |
| New-task action | "+ 新建任务" | route `/tasks/matrix-script/new` (existing) |
| Line filter | "matrix_script" preselected | template gate `kind == "matrix_script"` |
| Stage filter | dropdown over closed eight-stage enum (with operator labels) | `STAGE_*` set from `task_area_convergence.py` |
| Result filter | dropdown ✓ completed / ◐ ready / 🚧 blocked | `STATUS_READY` / `STATUS_BLOCKED` / `STATUS_COMPLETED` |
| Search | substring search over subject | client-side filter |

### 3.1 Forbidden in header

- Any line filter other than `matrix_script` is out of scope for this wireframe; cross-line filters live on the cross-line Board surface, not here.
- "Submit / queue / draft / running / done" pseudo-states (forbidden by surface_task_area_lowfi_v1.md §"State the Task Area must NOT invent").
- Vendor / model / provider / engine filter.

---

## 4. Task card body (binding-and-exhaustive)

These nine fields are **the card** for this wave. Every other field is forbidden.

| # | Card field | Operator label | Source | Closed enum (if any) |
|---|---|---|---|---|
| 1 | Subject / goal | (rendered as card headline) | `task["config"]["entry"].subject` (sanitised) | — |
| 2 | Line marker | "line: matrix_script" | constant | — |
| 3 | Variant count | "变体数: N" | `derive_matrix_script_task_card_summary().variant_count` | — |
| 4 | Publishable variant count | "可发布版本数: M/N" | `derive_matrix_script_task_card_summary().publishable_count` over `variant_count` | — |
| 5 | Current best candidate | "当前最佳候选: 候选 N ⭐ (\<state\>)" or "—" when none | `derive_matrix_script_task_card_summary().best_version` | gated by `RECOMMENDED_BUCKET_PUBLISHABLE` |
| 6 | Current blocker | "当前阻塞" line | `derive_matrix_script_task_card_summary().blocker` (operator-language; mapped from `compute_publish_readiness.head_reason` via `HEAD_REASON_LABELS_ZH`) | sourced from `head_reason` enum |
| 7 | Latest generation time | "最近一次生成: YYYY-MM-DD HH:MM" | `derive_matrix_script_task_card_summary().last_generated_at` | — |
| 8 | Stage badge | "Stage: ●\<stage label\>" | `derive_matrix_script_eight_stage_state` | `STAGE_*` |
| 9 | Result pill | "Result: ✓ / ◐ / 🚧 \<status label\>" | `derive_matrix_script_task_area_result_status` | `STATUS_READY` / `STATUS_BLOCKED` / `STATUS_COMPLETED` |

### 4.1 Next-action chip

Not numbered above because it sits in its own row inside the card body. It is binding for this wave.

| Chip | Operator label | Source |
|---|---|---|
| Next action | "下一步: \<operator-language sentence\>" | `derive_matrix_script_task_area_result_status.next_action_label` |

### 4.2 Three jump buttons

| Button | Operator label | Routes to | Closed precondition |
|---|---|---|---|
| Open Workbench | "打开工作台" | `/tasks/{id}` | task exists |
| Open Delivery | "打开交付中心" | `/tasks/{id}/publish-hub` | `kind == "matrix_script"` |
| Open Publish Feedback | "打开发布反馈" | `/tasks/{id}/publish-hub#publish-feedback` | same |

The three buttons render in a single row, in the order shown. They are always all present, regardless of stage. (A button leading to a zone where nothing is yet meaningful is not hidden — the zone itself owns the empty-state messaging.)

### 4.3 Forbidden in card body

- `cell_id`, `slot_id`, axis-tuple, ref counters, `content://` handle.
- Validator report drawer link.
- Vendor / model / provider / engine label or chip.
- Per-variant inspector (engineering inspector lives behind a separate route, out of scope here).
- Donor / supply / asset reference column.
- Free-text editing of any card field.
- Hidden state — the blocker line must be operator language. If `head_reason` does not yet have a label in `HEAD_REASON_LABELS_ZH`, the card renders a presenter-gap line "等待结果就绪" and the gap is logged as PG-1 (see [result-oriented UI plan §11.2](matrix_script_result_oriented_ui_plan_v1.md)) — never a raw English enum.

### 4.4 Empty / pending state rendering

- When `variant_count == 0`: "变体数: 0" + "可发布版本数: 0/0" + "当前最佳候选: —" + next-action chip "前往工作台开始变体配置".
- When `last_generated_at` is null: "最近一次生成: 尚未生成".
- When `RECOMMENDED_BUCKET_PUBLISHABLE` has no winner: "当前最佳候选: —" (never a fabricated marker).
- When `compute_publish_readiness.publishable == False` and `head_reason ∈ {publish_not_ready, compose_not_ready}`: blocker line renders the operator-language label and result pill is `🚧 blocked`.

---

## 5. Three-tier projection (script / variant / publish lanes)

The Task Area's underlying read consumes `derive_matrix_script_three_tier_lanes`. The three lanes drive the card's *primary highlighting*:

| Lane | Operator label | Drives |
|---|---|---|
| Script lane | "脚本结构" | renders gold border + structure-blocker label when this lane is the active blocker |
| Variant lane | "变体生成 / 评审" | renders the active per-variant blocker label |
| Publish lane | "发布交付" | renders the publish-readiness blocker label |

The card always renders one (and only one) lane as the **active** lane — defined as the leftmost lane that is not yet `STAGE_PUBLISHABLE` or beyond. The active lane's status is what the result pill summarises.

### 5.1 Lane bindings

| UI element | Backend | File |
|---|---|---|
| Three-tier lane projection | `derive_matrix_script_three_tier_lanes` | gateway/app/services/matrix_script/task_area_convergence.py |
| Active-lane selection rule | leftmost-not-completed semantics inside `derive_matrix_script_three_tier_lanes` | same |
| Lane-level operator labels | per-lane label dictionary inside the helper | same |

### 5.2 Forbidden lane behaviour

- A card never highlights two lanes simultaneously. Conflicts collapse to leftmost-active.
- The three lanes are not separate cards; they are three *aspects* of the same card.
- The lanes do not introduce a new state vocabulary — they read the same `STAGE_*` enum + `STATUS_*` enum and re-project them by lane.

---

## 6. Card sort + filter behaviour

### 6.1 Default sort

- Primary: by active-lane priority (script-blocked first, variant-blocked second, publish-blocked third, completed last).
- Secondary: by `last_generated_at` descending.

### 6.2 Filters

| Filter | Closed values | Source |
|---|---|---|
| Line | `matrix_script` (preselected; no other value rendered on this surface) | template gate |
| Stage | eight closed values from `STAGE_*` rendered as operator labels | `task_area_convergence.py` |
| Result | three closed values `✓ completed` / `◐ ready` / `🚧 blocked` | `STATUS_READY` / `STATUS_BLOCKED` / `STATUS_COMPLETED` |

### 6.3 Discipline

- Filters never invent buckets. Each value is a literal closed-enum member from an existing helper.
- Multi-select within a filter is allowed; cross-filter is AND.

---

## 7. New-task action

- Operator label: "+ 新建任务".
- Route: `/tasks/matrix-script/new` (existing).
- Reading: this wireframe does **not** redesign the new-task intake page; that page is owned by [docs/design/surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md) §"New Tasks" and the Phase A entry contract. The Task Area only presents the entry button.

### 7.1 Forbidden in the new-task entry from this surface

- Vendor / model / provider / engine selector at intake (forbidden by surface authority).
- Donor / supply selector.
- "Submit / queue" pseudo-states on the resulting card after intake — the new card lands as `STAGE_CREATED` with result pill `◐ ready · 配置变体` and next-action chip "前往工作台配置变体".

---

## 8. Cross-card discipline

| Discipline | Rule | Authority |
|---|---|---|
| Single source of truth per card field | every card field maps to exactly one helper output; no card field re-derives state | result-oriented UI plan §12 + recovery gate spec RC-A7 |
| No fake `final_video` | no card may show a fabricated `publish_url` or final video URL | recovery gate spec RC-R8 |
| No vendor / model / provider / engine | structurally absent from card body and filters | factory_packet_envelope_contract_v1 E5 + validator R3 |
| Operator language for every label | every label originates from a closed enum + `HEAD_REASON_LABELS_ZH` / per-helper operator-language dictionary; no raw English enum strings | result-oriented UI plan §5 |
| Append-only history | the card does not mutate any closure event from this surface; archive entry comes from `record_kind == "archive_action"` event in publish_feedback_closure | publish_feedback_closure_contract_v1 §"append-only" |
| No Digital Anchor cross-mention | this surface never references Digital Anchor tasks even as a filter value (cross-line view lives on the cross-line Board) | post-OWC addendum §2.3 |
| Hot Follow benchmark only, no file touch | Hot Follow card patterns are referenced as UX template; no Hot Follow file is changed | recovery amendment §7 |

---

## 9. Six-question test (task-area-only re-statement)

When the operator opens the Task Area cold:

1. "What is this task trying to produce?" → card subject (top of each card).
2. "Which variants are worth generating or reviewing?" → "变体数" + "可发布版本数" line.
3. "What is blocked right now?" → "当前阻塞" line + result pill 🚧 colour.
4. "What should I do next?" → "下一步" chip + jump buttons.
5. "Which candidate is currently recommended?" → "当前最佳候选" line.
6. "Is there a publishable video result yet?" → "可发布版本数" + result pill ✓ colour + "当前最佳候选" with state suffix.

All six are above the fold within a single card.

---

## 10. Backend mapping table (task-area-scoped)

| Card field / region | Backend feed | Service file | Closed enum |
|---|---|---|---|
| Subject | `task["config"]["entry"].subject` | task_card_summary.py | — |
| Line marker | template constant | tasks.html (matrix_script branch) | — |
| Stage badge | `derive_matrix_script_eight_stage_state` | task_area_convergence.py | `STAGE_*` |
| Three-tier lanes | `derive_matrix_script_three_tier_lanes` | task_area_convergence.py | per-lane closed sentinels |
| Result pill | `derive_matrix_script_task_area_result_status` | result_status_view.py | `STATUS_READY` / `STATUS_BLOCKED` / `STATUS_COMPLETED` |
| Next action chip | `derive_matrix_script_task_area_result_status.next_action_label` | result_status_view.py | (operator-language sentence) |
| Variant count | `derive_matrix_script_task_card_summary().variant_count` | task_card_summary.py | — |
| Publishable count | `derive_matrix_script_task_card_summary().publishable_count` | task_card_summary.py | — |
| Best candidate | `derive_matrix_script_task_card_summary().best_version` | task_card_summary.py | gated by `RECOMMENDED_BUCKET_PUBLISHABLE` |
| Blocker | `derive_matrix_script_task_card_summary().blocker` | task_card_summary.py | mapped from `compute_publish_readiness.head_reason` |
| Last generated | `derive_matrix_script_task_card_summary().last_generated_at` | task_card_summary.py | — |
| Open Workbench | route `/tasks/{id}` | gateway/app/routers/tasks.py | — |
| Open Delivery | route `/tasks/{id}/publish-hub` | gateway/app/routers/tasks.py | — |
| Open Publish Feedback | publish-hub anchor `#publish-feedback` | template anchor | — |
| Stage filter values | `STAGE_*` mapped to operator labels | task_area_convergence.py | — |
| Result filter values | `STATUS_*` mapped to operator labels | result_status_view.py | — |

---

## 11. Gaps surfaced by this wireframe (cross-reference to result-oriented UI plan §11)

| Gap | Type | Symptom in Task Area |
|---|---|---|
| BG-2 | backend gap | The card cannot show a `current` vs `historical` provenance label on the best-candidate line; today the marker only renders ⭐ |
| PG-1 | presenter gap | Blocker line may render "等待结果就绪" placeholder when `head_reason` is uncovered by `HEAD_REASON_LABELS_ZH` |
| PG-3 | presenter gap | Blocker line renders raw English `retracted` for closure D.1 retracted state; closure path: add operator label in result_status_view.py |
| PG-4 | presenter gap | Archive badge has no iteration-hint trailer; closure path: derive trailer from `derive_matrix_script_publish_backfill_readiness.next_iteration_text` |
| PG-5 | presenter gap | Reference badge (`hot_follow ✓`) is not rendered on Matrix Script result-oriented blocks; trivial template addition |
| IG-1 | interaction gap | "Open publish feedback" jump button currently exists only as a template anchor; design here promotes it to a first-class card button (anchor wiring already present, only the button row needs to be added) |
| IG-3 | interaction gap | Archived card has no one-click "duplicate as new task" affordance |

None of the above gaps are solved in this design step.

---

## 12. Reading declaration

This wireframe consumes the same reading set as [matrix_script_result_oriented_ui_plan_v1.md §14](matrix_script_result_oriented_ui_plan_v1.md). Additional surface authority specifically consulted: [docs/design/surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md).

Documentation only — no code, no UI implementation, no contract authoring, no schema mutation, no template change, no test change, no runtime change.
