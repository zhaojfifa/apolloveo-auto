# Matrix Script — Guided Operator Workflow Gate Spec (2026-06-07)

Status: **ACCEPTED GATE SPEC — docs-only. Implementation gate for future Matrix
Script Guided Operator Workflow UI PRs. Implements nothing itself.**

Derivation: this gate spec is derived from the merged planning + preview inputs
and freezes them into enforceable engineering rules. It does **not** author a new
Information Architecture and does **not** supersede Bucket A.

- Planning input: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_PLAN_20260607.md` (#216)
- Preview input: `docs/design/previews/matrix_script_guided_operator_workflow_preview.html` +
  `docs/design/screenshots/matrix_script_guided_operator_workflow_preview_20260607.png` (#217)
- Substrate (frozen, consumed, not reopened): #211 / #212 / #213 / #214 / #215.

When this gate spec conflicts with Bucket A authority
(`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A) or root governance
(`ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`), the underlying authority
wins and this spec is corrected in a docs-only follow-up.

---

## 1. Purpose

Freeze the implementation rules that turn the merged #211–#215 capabilities into
**one guided operator procedure** on the Matrix Script Workbench. The procedure the
implementation must teach is a single linear spine:

> 看 V1 → 判断 Shot → 上传素材 → 再次生成 V2 → 对比 V1/V2 → 确认主版本 → 交付

The spec is **gate-spec-first**: no Workbench/runtime PR in this line may open until
this spec is signed (§10). Every implementation slice (§5) is a **pure
presentation / copy / re-order layer** over already-frozen truth — no new
capability, no new producer, no second source of truth.

## 2. Entry Conditions

- E1. #211 / #212 / #213 / #214 / #215 merged to `main` (substrate). ✅ at authoring.
- E2. #216 planning + #217 preview merged to `main` as Planning / Review Inputs. ✅ at authoring.
- E3. This spec's §10 architect + reviewer signoff merged to `main` — **opens the
  implementation gate for PR-1 only**. Subsequent PRs open sequentially per §5.
- E4. The wave gate in `CURRENT_ENGINEERING_FOCUS.md` permits the work; this spec
  does not itself advance any wave, trial, or closeout signoff.

## 3. Allowed Scope — Binding & Exhaustive Zone Rules

The implementation may touch only the Matrix Script Workbench operator surfaces
(`gateway/app/templates/task_workbench.html` and the Matrix-Script-scoped
presentation helper `gateway/app/services/matrix_script/operator_workbench_view.py`)
and the Matrix Script test suites. Re-homing is by **re-ordering / re-labelling
existing sections and moving already-rendered fields** — not new panels, not a
parallel flow, not new `data-role` truth (Design Authority Index Anti-Sprawl rule 4).

The operator surface is five zones in this order, plus collapsed diagnostics:

```
A 区  主视频结果与流程状态      ← 步骤 1（含脚本理解折叠上下文）
B 区  逐镜调整与素材           ← 步骤 2–4
C 区  生成与对比：V1 / V2      ← 步骤 5–6（再次生成 → 对比 → 确认/丢弃 枢纽）
D 区  交付候选                 ← 步骤 7（终点，确认之后）
E 区  进阶 / 诊断折叠          ← 非主路径（视频变体 / 脚本理解 / 过程记录）
J 区  技术诊断                ← 架构视图，默认折叠（不变）
```

### 3.A — A 区 主视频结果与流程状态

A区 MUST show operator-safe state, in the 现状 → 原因 → 下一步 shape:

- **当前主视频：** `V1` 或 `V2`（确认后）。
- **当前状态（operator wording）:** 稳定 / 已记录调整意图 / 素材已就绪 / 正在生成 V2 /
  V2 待确认 / 生成失败 — one operator-language sentence, mapped from the existing
  derived `process_state` (#215). The mapping table is normative:

  | derived state (#215) | A区 现状 (operator copy) | 下一步 |
  |----------------------|--------------------------|--------|
  | `not_generated` | 还没有生成主视频 | 确认素材与配乐后生成主视频预览 |
  | `stable` | 已有可用的主视频（V1），暂无改动 | 检查镜头，或进入交付 |
  | `intent_only` | 已记录素材调整意图，但还没有上传素材 | 到 B 区上传这个镜头的素材 |
  | `material_ready` | 素材已就绪，但还没有体现到新预览里 | 到 C 区点击「再次生成预览」 |
  | `generation_running` | 正在生成新版本预览（V2 候选） | 稍候，本页自动更新；不影响当前主视频 |
  | `candidate_ready` | 新预览（V2 候选）已生成，等待确认 | 到 C 区对比 V1/V2，确认或丢弃 |
  | `failed` | 这次生成没有成功 | 当前主视频未受影响，可重试 |

- **下一步:** one of 检查镜头 / 上传素材 / 再次生成 / 对比 V1/V2 / 确认主版本 / 重试.

A区 MUST NOT show as primary operator copy any of the following raw tokens (these
are diagnostics-only, §3.E / J 区):

```
process_state                    preview_generation_succeeded
material_bytes_consumed          official_publish_ready=false
raw manifest                     provider URL
local_path                       publish URL
Akool task / model / credit      any version-slot internal / created_at / source=*
```

No operator-facing note may NAME an internal enum (e.g. "不显示原始 process_state
枚举值" is an engineer note, not operator copy — forbidden in the primary surface).

### 3.B — B 区 逐镜调整与素材

Each shot card MUST answer, in operator language:

1. **这个镜头现在用了什么？** — visual source label only (原始生成素材 / 运营上传素材 /
   运营绑定素材引用 / 复用素材 / 降级占位素材), from #215 `visual_source_label_zh`.
2. **为什么建议处理？** — **R-SHOT-REASON (binding):** every shot card suggested for
   supplement/replace MUST explain *why* it is being handled, in operator language,
   drawing only on existing observable signals (visual source / shot-match /
   missing-material from #215). It introduces no new field or producer. Example copy:
   - `建议处理原因：当前为复用素材，缺少真实品尝画面，建议补充一个吃番茄/品尝特写。`
   - `建议处理原因：当前为复用素材，缺少递向镜头，建议替换为递向/展示动作素材。`
3. **这个镜头怎么处理？** — three primary decisions (choose-order), #214 copy:
   `使用当前素材` / `补充这个镜头素材` / `替换这个镜头素材`, each with a one-line helper.
4. **上传这个镜头的新素材** — the **primary** material path (see §3.B.1).
5. **调整后会发生什么？** — operator-language outcome ("再次生成时使用补充/替换素材生成
   V2 候选；确认前不影响 V1 与交付").

#### 3.B.1 — Upload primary; advanced binding folded

- Upload is the primary path for normal operators.
- Existing reference-binding capability MAY remain, but only behind a folded,
  visually secondary disclosure:
  - `高级：绑定已有素材引用`
  - `仅当你已有系统素材引用时使用。普通运营请上传素材。`
- `asset://` / `msmaterial://` MUST NOT be exposed as a *required primary input* for
  normal operators. (They remain valid backend handles; they are not operator copy.)

#### 3.B.2 — Upload → Regenerate handoff (R-UPLOAD-HANDOFF, binding)

After a shot material upload, the next step MUST be visible near the upload area;
the operator MUST NOT have to search another section to learn the next action:

- `下一步：素材已上传。请点击「再次生成预览」生成 V2。`
- Provide a local nudge or a jump to C 区 (e.g. an in-page anchor to the C-zone
  regenerate control). If a regenerate CTA is mirrored beside the upload, the copy
  MUST state it is the **same** action as the C 区 trigger — not a second
  regenerate path.

### 3.C — C 区 生成与对比：V1 / V2

C 区 is the named pivot of the workflow and MUST own:

```
再次生成预览                    （触发 V2 候选生成；不覆盖 V1）
当前主版本 V1                   （视觉上与 V2 明显区分）
新预览候选 V2                   （永远标注「候选」，确认前）
V2 使用了哪些上传素材           （operator-safe consumed-material list, #212）
哪些镜头发生了变化              （changed-shot list vs V1）
确认 V2 为主版本 / 丢弃 V2 / 继续调整
```

Required truth, shown explicitly: **`V2 未确认前不会影响交付。`**

V1 and V2 MUST be visually distinct (separate `data-preview-version="V1|V2"`
markers already exist from #215; reuse, do not invent new truth).

### 3.D — D 区 交付候选

D 区 shows delivery truth only:

- `当前交付候选：V1`（未确认 V2 时）or `当前交付候选：V2`（确认后）.

Rules:

- Delivery follows the **confirmed** main only.
- An unconfirmed V2 MUST NEVER be shown as the delivery candidate.
- `official_publish_ready` remains `false`.
- **R-DELIVERY-WORDING (binding):** the primary D 区 MUST NOT show the raw backend
  field `official_publish_ready=false`. Use operator wording only: `正式交付就绪：否`.
  The raw field (and any raw enum/flag) may appear only in collapsed diagnostics
  (§3.E / J 区).

### 3.E — E 区 进阶 / 诊断折叠

Collapsed by default:

```
视频变体
脚本理解 / 故事理解
过程记录 / 技术诊断
```

The operator-safe process log MAY show operator-language step events only:

```
已记录处理方式：Shot 04 补充素材
上传成功：Shot 04 eat_tomato.png
已请求再次生成预览
V2 新预览已生成
```

The process log MUST NOT contain `local_path`, raw manifest, provider URL, publish
URL/status, or Akool task/model/credit. Raw engineering fields belong only in J 区.

---

## 4. Forbidden Scope

The implementation MUST NOT:

```
No generation pipeline change          No publish automation
No storage change                      No official_publish_ready=true
No artifact_storage.py change          No new production line
No schema / contract change            No second source of truth
No Akool live / Akool surface          No new endpoint / route behaviour change
No provider switching / promotion      No new closed-enum / enum widening
No Hot Follow file touch               No Digital Anchor file touch
No durable persistence                 No React/Vite rebuild
No donor-namespace import              No PR-slice bundling
```

Specifically: no helper may call a new producer or recompute truth; all zones read
existing #211–#215 projection truth + the #215 derived `process_state`. No
`compute_*` truth producer is introduced. The #212 byte-consumption behavior is
consumed read-only and not modified.

Forbidden paths (any appearance in a slice's `git diff --name-only` is an automatic
fail): `gateway/app/services/asset/`, `gateway/app/services/hot_follow*`,
`gateway/app/services/digital_anchor/`, `**/artifact_storage.py`, `schemas/`,
`docs/contracts/`, `CURRENT_ENGINEERING_FOCUS.md`.

---

## 5. Implementation Slices

Small PRs, gate-spec-first, copy-first before structure. Each slice preserves
behavior, ships with dedicated tests, and opens only after its predecessor merges
and reviews. No bundling.

| PR | Scope | Touches | Risk |
|----|-------|---------|------|
| **PR-1** | A区 状态叙述与下一步引导 — map `process_state`→现状/原因/下一步 (§3.A); strip any raw-enum primary copy. | view + template copy | Lowest |
| **PR-2** | B区 逐镜卡片主流程收敛 — 5 questions incl. R-SHOT-REASON (§3.B); upload primary; fold advanced binding; R-UPLOAD-HANDOFF nudge (§3.B.2). | view + template | Medium |
| **PR-3** | C区 V1/V2 对比与确认区 — promote regenerate→compare→confirm pivot (§3.C); visual V1/V2 distinction; "V2 未确认前不影响交付". | template re-order + view | Medium |
| **PR-4** | D区 交付候选后移与确认保护 — move 交付 after confirm; R-DELIVERY-WORDING (§3.D). | template re-order | Medium |
| **PR-5** | E区 高级/诊断折叠与动作记录 — collapse 变体/脚本理解/过程记录; operator-safe log (§3.E). | template + view | Low–Medium |
| **PR-6** | Closeout docs + operator trial checklist — acceptance audit (§6), no-leak audit, signoff. | docs only | Docs-only |

> Reviewer-fail / new-defect corrections are authored as separate narrow follow-up
> PRs, never folded back into a merged slice.

---

## 6. Acceptance Tests

The future Closeout (PR-6) records PASS/FAIL against every row. Each implementation
slice contributes the rows it can satisfy; the audit is exhaustive at Closeout.

| # | Acceptance criterion | Slice |
|---|----------------------|-------|
| A-1 | A区 never shows a raw `process_state` enum (or any §3.A raw token) in primary UI. | PR-1 |
| A-2 | B区 guided shot cards show *why* the shot needs supplement/replace (R-SHOT-REASON). | PR-2 |
| A-3 | Advanced reference-binding is folded and visually secondary; not a required primary input. | PR-2 |
| A-4 | Upload is the primary material path. | PR-2 |
| A-5 | Upload → regenerate handoff is visible near the upload area (R-UPLOAD-HANDOFF). | PR-2 |
| A-6 | C区 shows V1 and V2 separately and visually distinct. | PR-3 |
| A-7 | An unconfirmed V2 candidate does not affect the delivery candidate. | PR-3 / PR-4 |
| A-8 | Confirming V2 switches the delivery candidate to V2. | PR-3 / PR-4 |
| A-9 | D区 does not show `official_publish_ready=false`; only `正式交付就绪：否` (R-DELIVERY-WORDING). | PR-4 |
| A-10 | E区 diagnostics (变体 / 脚本理解 / 过程记录) are collapsed by default. | PR-5 |
| A-11 | No leakage anywhere in the primary surface: `local_path`, raw manifest, provider URL, publish URL/status, Akool task/model/credit. (Guarded by the existing `_assert_clean` scan + a dedicated leakage test.) | every PR |
| A-12 | #212 byte-consumption behavior is unchanged (`material_bytes_consumed` true only when bytes actually consumed; honest copy otherwise). | every PR |
| A-13 | V1 is preserved until an explicit confirm; failed/discarded regeneration never overwrites V1. | PR-3 |
| A-14 | `official_publish_ready` remains `false` at every checkpoint. | every PR |
| A-15 | No Hot Follow / Digital Anchor / `artifact_storage.py` / schema-contract change (forbidden-path scan clean per §4). | every PR |

Each slice MUST keep the Matrix Script suite green (the established #215 baseline
was 1851 passed; new tests add to it). Pre-existing env-coupled (PEP-604) skips are
not regressions per `ENGINEERING_RULES.md` §10.

---

## 7. Preserved Freezes

These are byte-stable across every slice and are re-audited at Closeout:

- Generation chain (script → shot-plan → `final.mp4` → artifact_staged →
  preview_url → acceptance) — UI re-order does not re-wire it.
- Matrix-Script storage (`shot_material_storage.py`, `local_workspace` scope) and
  the `msmaterial://` resolver — untouched.
- `artifact_storage.py`, `schemas/**`, `docs/contracts/**` — untouched.
- Hot Follow, Digital Anchor — zero file touch; the DA five operations findings
  remain in force.
- V1-protection and the #212 consumption honesty contract.
- `official_publish_ready=false` invariant.
- No second source of truth — all zones read existing projection truth + #215
  `process_state`; no new producer, no `compute_*` truth call.

---

## 8. Authority Boundary

- This gate spec is **derived from #216 planning and #217 preview**.
- It **does not supersede Bucket A** architecture/design authority.
- It governs **only future Matrix Script Guided Operator Workflow UI
  implementation** (the five operator zones + Matrix Script tests).
- It **does not authorize** any backend generation / storage / provider / Akool /
  schema / contract change.
- #216 and #217 remain **Planning / Review Inputs (NOT authority)** — they are not
  moved into Bucket A by this spec.
- Execution logs remain evidence only (Design Authority Index Anti-Sprawl rule 1).

---

## 9. Open Questions (resolved at PR authoring, not blocking the gate)

1. Is the C-zone pivot a standalone section or an always-expanded sub-block of A?
   Recommendation: standalone C 区 per §3.C; the PR-3 author confirms test-marker
   placement.
2. Failure-path as a guided station (A-13) — show "生成失败怎么办" inline; deferrable
   to PR-3 polish, not a gate blocker.
3. In the live build, the R-UPLOAD-HANDOFF nudge should clear once a shot has
   already entered V2 (avoid showing nudge + "已进入 V2" together) — PR-2 detail.

## 10. Signoff (gate opens on merge)

| Role | Name | Date | Verdict |
|------|------|------|---------|
| Architect | `<fill>` | `<fill>` | `<fill>` |
| Reviewer | `<fill>` | `<fill>` | `<fill>` |
| Operations Coordinator | `<fill>` | `<fill>` | binds Closeout (PR-6) |
| Product Manager | `<fill>` | `<fill>` | binds Closeout (PR-6) |

Architect + Reviewer signoff merged to `main` **opens the implementation gate for
PR-1 only**. Coordinator + PM bind the Closeout acceptance audit (§6, PR-6), not
gate opening. This spec authorizes no code; the first allowed action after signoff
is PR-1 per §5.

---

## 11. Authority Pointers

- Bucket A: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A.
- Planning input: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_PLAN_20260607.md`.
- Preview input: `docs/design/previews/matrix_script_guided_operator_workflow_preview.html`.
- Substrate evidence: `docs/execution/MATRIX_SCRIPT_P1_3_MATERIAL_BYTES_CLOSURE_20260606.md`,
  `…_OPERATOR_COPY_CLARITY_20260607.md`, `…_OPERATOR_PROCESS_OBSERVABILITY_20260607.md`.
- Wave gate: `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_RULES.md`.

*This is an accepted gate spec for future UI implementation. It implements nothing,
opens no wave, and supersedes no authority. Code begins only after §10 signoff, one
slice at a time, under the standard discipline.*
