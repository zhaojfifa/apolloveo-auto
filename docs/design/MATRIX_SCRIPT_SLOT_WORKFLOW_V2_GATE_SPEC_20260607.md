# Matrix Script — Slot Workflow v2 Gate Spec (2026-06-07)

Status: **ACCEPTED-PENDING-SIGNOFF GATE SPEC — docs-only. Implementation gate for
future Matrix Script Slot Workflow v2 UI PRs. Implements nothing itself. The
implementation gate is CLOSED until §13 §10-style signoff merges to `main`.**

Derivation: this gate spec is derived from the merged Product Plan and the validated
static preview + operator review, and freezes them into enforceable engineering
rules. It does **not** author a new Information Architecture and does **not** supersede
Bucket A. It is the **v2 successor** to the Guided Operator Workflow Gate Spec for the
B区 model only; A区 / C区 / D区 / E区 inherit the Guided Workflow Gate Spec rules
except where amended here.

- Product Plan input: `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_PRODUCT_PLAN_20260607.md` (#228, MERGED)
- Preview input: `docs/design/previews/matrix_script_slot_workflow_v2_preview.html`
- Operator Review input: `docs/reviews/matrix_script_slot_workflow_v2_operator_review.md` (Round 2 = PASS)
- Predecessor gate (inherited, amended for B区): `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md`
- Substrate (frozen, consumed, not reopened): #211 / #212 / #213 / #214 / #215 and the
  Guided Operator Workflow slices #220 / #223 / #224 / #225 / #226 / #227.

When this gate spec conflicts with Bucket A authority
(`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A) or root governance
(`ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`), the underlying authority
wins and this spec is corrected in a docs-only follow-up.

---

## 1. Purpose

Freeze the implementation rules that replace the Guided Operator Workflow **all-shot
expanded-card B区** with a **scalable queue + single-active-panel model** that works at
10+ shots, while preserving every merged behavior (upload, V2 byte-consumption, V1
protection, delivery-follows-confirmed-main, `official_publish_ready=false`).

The model the implementation must teach (unchanged spine, scalable body):

> 看 V1 → **扫描镜头队列** → **打开当前镜头** → 在槽位上做处理决策（上传/替换/补充/跳过）
> → **批量再次生成 / 更新 V2** → 对比 V1/V2 → 确认主版本 → 交付

The spec is **gate-spec-first**: no Workbench/runtime PR in this v2 line may open until
this spec's signoff (§13) merges. Every implementation slice (§11) is a **pure
presentation / re-order / projection layer** over already-frozen truth — no new
capability, no new producer, no second source of truth, no new contract or schema.

## 2. Entry Conditions

- E1. #211 / #212 / #213 / #214 / #215 merged to `main` (capability substrate). ✅
- E2. Guided Operator Workflow slices #220 / #223 / #224 / #225 / #226 / #227 merged
  (the v1 B区 this v2 replaces). ✅
- E3. Slot Workflow v2 Product Plan #228 merged to `main`. ✅
- E4. The static preview + operator review (Round 2 = PASS) authored. ✅ (preview +
  review land via their own docs branch; this spec cites them by path).
- E5. This spec's §13 signoff (Architect + Reviewer) merged to `main` — **opens the
  implementation gate for PR-1 only**. Subsequent PRs open sequentially per §11, each
  its own Owner-gated S5→S6 (L3) decision per the Autopilot Execution Policy §3.
- E6. The wave gate in `CURRENT_ENGINEERING_FOCUS.md` permits the work; this spec does
  not itself advance any wave, trial, or closeout signoff.

## 3. Allowed Scope — Binding & Exhaustive Zone Rules

The implementation may touch only the Matrix Script Workbench operator surfaces
(`gateway/app/templates/task_workbench.html` and the Matrix-Script-scoped presentation
helper `gateway/app/services/matrix_script/operator_workbench_view.py`) and the Matrix
Script test suites. Re-homing is by **re-ordering / re-labelling existing sections,
restructuring B区 presentation, and moving already-rendered fields** — not new panels
outside the existing A–E zones, not a parallel flow, not new `data-role` truth (Design
Authority Index Anti-Sprawl rule 4).

The operator surface remains five zones; only **B区** changes model. Zones A / C / D /
E inherit the Guided Operator Workflow Gate Spec §3.A / §3.C / §3.D / §3.E rules
verbatim except as amended in §3.C below.

```
A 区  主视频结果与流程状态      ← 步骤 1（不变；Guided Gate Spec §3.A 继承）
B 区  逐镜调整与素材           ← 步骤 2–4（v2 模型：队列 + 单一活动面板，本 §3.B 重写）
C 区  生成与对比：V1 / V2      ← 步骤 5–6（继承 §3.C，新增批量再次生成入口 §3.C.1）
D 区  交付候选                 ← 步骤 7（不变；Guided Gate Spec §3.D 继承）
E 区  进阶 / 诊断折叠          ← 非主路径（不变；Guided Gate Spec §3.E 继承）
J 区  技术诊断                ← 架构视图，默认折叠（不变）
```

### 3.B — B 区 逐镜调整与素材 (v2 — rewritten)

B区 is restructured into a **compact Shot Queue** plus **one active Current Shot Work
Panel** plus an in-panel **Slot Editor** carrying the **Assignment** object. The
binding rules:

#### 3.B.1 — Compact Shot Queue (binding)

- ALL shots of the task MUST be rendered as a single compact, scannable list — **one
  short row per shot**, not a full expanded card per shot. The queue MUST stay readable
  at **10+ shots** without expanding more than one shot.
- Each queue row MUST show, in operator language: shot index/label, a **status chip**,
  and the per-shot **R-SHOT-REASON** one-liner **only when the shot is flagged** for
  supplement/replace (reason drawn only from existing #215 observable signals — visual
  source / shot-match / missing-material; no new field, no new producer).
- The status chip vocabulary is a **closed operator-language set** mapped from existing
  per-shot projection truth (#214 decision + #215 trace + upload/consumption state).
  The normative set:

  | chip (operator copy) | meaning (from existing truth) |
  |----------------------|-------------------------------|
  | `待处理` | flagged / not yet decided |
  | `已上传素材` | material uploaded, locked for next V2, not yet consumed |
  | `已跳过` | operator marked skip / 无需处理 by choice |
  | `已进入 V2` | this shot's material is already consumed by the current V2 candidate |
  | `无需处理` | system-fine shot, no action suggested |

- Exactly **one** shot is the active (expanded) shot at a time. Selecting another row
  MUST move the active panel — it MUST NOT open a second expanded card.

#### 3.B.2 — Current Shot Work Panel (binding)

The single active shot expands into one work panel that MUST show, in operator
language:

1. **shot title** (index + label).
2. **为什么需要处理** — R-SHOT-REASON, when flagged (same source as §3.B.1).
3. **当前素材状态** — operator-safe visual-source / uploaded-file label (#215
   `visual_source_label_zh`; friendly file label, never the raw `msmaterial://` /
   `asset://` handle).
4. **当前处理决策（Assignment）** — the current Assignment (§3.B.4).
5. **下一步** — operator-language next action (e.g. 到 C 区批量再次生成 V2).

#### 3.B.3 — Slot Editor (binding) + honest capability classification

Inside the active panel, the shot's slots are presented as a **typed set**. A slot is
rendered with a **real, operator-actionable control ONLY if it is `active now`**.
Display-only and future slots MUST be rendered as status, never as an editable or
disabled-but-advertised control. The classification is **normative and closed**:

| slot type | classification | rendering rule |
|-----------|----------------|----------------|
| `visual_material_slot` | **active now** | full Assignment control set: 使用当前素材 / 补充素材 / 替换素材 / 跳过此镜头 + 上传（primary）+ folded `高级：绑定已有素材引用`. The **only** actionable slot. |
| `text_copy_slot` | **display-only now** | read-only status / current-copy summary; **no edit control**; helper states no operator copy-edit action exists on this line. |
| `subtitle_slot` | **display-only now** | read-only subtitle status; **no edit control**; future editability only under a separate gate spec. |
| `voiceover_slot` | **future workflow** | **pure status line only** ("后续工作流 · 暂不可编辑"); **MUST NOT render any button** (not even a disabled one). |
| `bgm_slot` | **future workflow** | **pure status line only**; **MUST NOT render any button**. |

Honesty rule (binding, from the operator review C-2 fix): **a future slot MUST NOT
advertise an unavailable capability — no disabled button, no clickable affordance; a
status line only.** A display-only slot MUST NOT present an editable field.

#### 3.B.4 — Assignment model (binding)

The Assignment is the **only operator-mutable object**. Shots and Slots are read-only
structure. The Assignment panel MUST show:

- **decision option set** (closed, #214 copy): `使用当前素材` / `补充素材` / `替换素材` /
  `跳过此镜头`.
- **current decision**; **bound material** (friendly label, never a raw handle);
  **lock state** (`已锁定进入下一次 V2`); **consumption state** (`尚未被 V2 消费` /
  `已被 V2 消费`).
- Upload is the **primary** material path. Existing reference-binding MAY remain only
  behind a folded, visually secondary `高级：绑定已有素材引用` disclosure (Guided Gate
  Spec §3.B.1 inherited). `asset://` / `msmaterial://` MUST NOT be a required primary
  input or appear as operator copy.

An Assignment records intent + uploaded bytes; it MUST NOT compute new truth, call a
new producer, or overwrite V1. Only an explicit confirm (C区) promotes V2.

### 3.C — C 区 生成与对比 (inherited + §3.C.1 batch entry)

C区 inherits the Guided Operator Workflow Gate Spec §3.C rules (named pivot; V1/V2
visually distinct via existing `data-preview-version="V1|V2"`; "V2 未确认前不会影响交付";
confirm / discard / continue). Added:

#### 3.C.1 — Batch Regenerate Entry (binding)

- C区 MUST own a **single, central batch-regenerate entry** ("生成 / 更新 V2 预览"),
  triggered **after** the operator finishes the selected shot Assignments — **not a
  per-card / per-shot regenerate**.
- The entry MUST state the **selected-shot set** that will enter/update V2.
- **V1/V2 dual-state copy (binding, from operator review C-1 fix):** when a V2 candidate
  already exists, the copy MUST make clear that (a) a V2 candidate already exists; (b)
  batch regenerate **updates the same V2 candidate** with the selected shots (not a new
  parallel version); (c) the current main is **始终是 V1 until an explicit confirm**, and
  V1 + delivery are unchanged before confirm.
- Batch regenerate MUST reuse the existing regeneration path (#212 byte-consumption,
  read-only); it MUST NOT introduce a second regenerate path or a new producer.

### 3.D / 3.E — inherited

D区 (交付候选; `正式交付就绪：否` only, never raw `official_publish_ready=false`;
delivery follows confirmed main only; unconfirmed V2 never the delivery candidate) and
E区 (变体 / 脚本理解 / 过程记录 collapsed by default; operator-safe step log only)
inherit the Guided Operator Workflow Gate Spec §3.D / §3.E rules **verbatim and
unchanged**.

## 4. V1/V2 Semantics Preservation (binding)

- V1 is the current main video. V2 is **always a candidate** until an explicit confirm.
- Batch regenerate / failed regenerate / discard MUST NEVER overwrite V1.
- Confirming V2 promotes it to current main and switches the delivery candidate to V2;
  discard keeps V1 and removes the candidate.
- These are existing behaviors consumed read-only; the v2 UI re-order MUST NOT re-wire
  them.

## 5. Delivery Truth Preservation (binding)

- Delivery candidate follows the **confirmed** main only. An unconfirmed V2 MUST NEVER
  be shown as the delivery candidate.
- `official_publish_ready` remains `false`; the primary D区 shows `正式交付就绪：否`
  only (R-DELIVERY-WORDING inherited). The raw field may appear only in collapsed
  diagnostics.

## 6. Honest Slot Capability Classification (binding — restated for emphasis)

```
visual_material_slot = active now        → real controls (only actionable slot)
text_copy_slot       = display-only now  → read-only status, no edit control
subtitle_slot        = display-only now  → read-only status, no edit control
voiceover_slot       = future workflow   → status line only, NO button
bgm_slot             = future workflow   → status line only, NO button
```

This classification is closed for this gate. Promoting any display-only/future slot to
actionable requires a **separate** gate spec backed by a real, contract-defined backend
action — it is forbidden in this v2 scope (§9 / §12).

## 7. Forbidden Leakage / Raw Backend Wording Rules (binding)

The primary operator surface MUST NOT show, as operator copy, any of:

```
process_state (raw enum)         official_publish_ready=false (raw flag)
material_bytes_consumed (raw)    msmaterial:// / asset:// (raw handles)
local_path                       raw manifest / raw JSON
provider URL / publish URL       Akool task / model / credit
version-slot internal / created_at / source=*
```

No operator-facing note may NAME an internal enum (e.g. "不显示原始 process_state 枚举值"
is an engineer note, forbidden in the primary surface). Raw fields belong only in J区.
Guarded by the existing `_assert_clean` scan + a dedicated leakage test (§8 A-V2-8).

## 8. Acceptance Tests

The future Closeout records PASS/FAIL against every row. Each slice contributes the
rows it can satisfy; the audit is exhaustive at Closeout.

| # | Acceptance criterion | Slice |
|---|----------------------|-------|
| A-V2-1 | B区 renders all shots as a compact queue (one row each), scannable at 10+ shots; not one full card per shot. | PR-1 |
| A-V2-2 | Exactly one shot is active/expanded at a time; selecting another row moves the active panel (no second expanded card). | PR-1 |
| A-V2-3 | Queue status chips use only the closed operator set (待处理 / 已上传素材 / 已跳过 / 已进入 V2 / 无需处理), each mapped from existing truth. | PR-1 |
| A-V2-4 | Current Shot Work Panel shows title / why (R-SHOT-REASON when flagged) / current material status / current Assignment / next step. | PR-1 |
| A-V2-5 | `visual_material_slot` is the only actionable slot (decision set + upload primary + folded advanced binding). | PR-2 |
| A-V2-6 | `text_copy_slot` and `subtitle_slot` render as read-only status with **no edit control**. | PR-2 |
| A-V2-7 | `voiceover_slot` and `bgm_slot` render as **status line only, with no button** (not even disabled). | PR-2 |
| A-V2-8 | No leakage in the primary surface: raw enum / `official_publish_ready=false` / raw handle / `local_path` / manifest / provider URL / publish URL/status / Akool. (`_assert_clean` + dedicated leakage test.) | every PR |
| A-V2-9 | Assignment is the only operator-mutated object: decision set + bound material (friendly label) + lock state + consumption state; no raw handle as operator copy. | PR-2 |
| A-V2-10 | C区 batch-regenerate entry is single/central and runs after selected changes (not per-card); states the selected-shot set. | PR-3 |
| A-V2-11 | V1/V2 dual-state copy is explicit: existing V2 candidate; batch updates the same candidate; V1 stays main until explicit confirm (C-1). | PR-3 |
| A-V2-12 | V1 preserved until explicit confirm; batch/failed/discarded regen never overwrites V1. | PR-3 |
| A-V2-13 | Unconfirmed V2 does not affect the delivery candidate; delivery follows confirmed main; `正式交付就绪：否` only. | PR-3 |
| A-V2-14 | #212 byte-consumption behavior unchanged (`material_bytes_consumed` true only when bytes actually consumed; honest copy otherwise). | every PR |
| A-V2-15 | `official_publish_ready` remains `false` at every checkpoint. | every PR |
| A-V2-16 | No new producer / second source of truth; all zones read existing #211–#215 projection truth + #215 `process_state`; no `compute_*` truth call introduced. | every PR |
| A-V2-17 | No Hot Follow / Digital Anchor / `artifact_storage.py` / schema-contract change (forbidden-path scan clean per §12). | every PR |
| A-V2-18 | A区 / D区 / E区 inherited Guided Gate Spec behavior preserved (no regression to state narration, delivery wording, diagnostics fold). | every PR |

Each slice MUST keep the Matrix Script suite green (the Guided Workflow closeout
baseline was 1899 passed at PR-5; new tests add to it). Pre-existing env-coupled
(PEP-604) skips are not regressions per `ENGINEERING_RULES.md` §10.

## 9. Forbidden Scope

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
No operator-driven Phase B authoring (roles[] / segments[] / shot creation/reorder)
No promotion of any display-only / future slot to actionable in this scope
```

Specifically: no helper may call a new producer or recompute truth; all zones read
existing #211–#215 projection truth + the #215 derived `process_state`. The Shot Queue
and Slot Editor are **presentation over existing per-shot projection** — they introduce
no new per-shot data, no new status producer, and no new Assignment store. The
Assignment surfaces the existing material-intent + upload + #212 consumption path only.

## 10. Preserved Freezes

Byte-stable across every slice, re-audited at Closeout:

- Generation chain (script → shot-plan → `final.mp4` → artifact_staged → preview_url →
  acceptance) — UI re-order does not re-wire it.
- Matrix-Script storage (`shot_material_storage.py`, `local_workspace` scope) and the
  `msmaterial://` resolver — untouched.
- `artifact_storage.py`, `schemas/**`, `docs/contracts/**` — untouched.
- Hot Follow, Digital Anchor — zero file touch; the DA five operations findings remain
  in force.
- V1-protection and the #212 consumption honesty contract.
- `official_publish_ready=false` invariant.
- A区 / C区 (pivot) / D区 / E区 Guided Operator Workflow Gate Spec behavior.
- No second source of truth — all zones read existing projection truth + #215
  `process_state`; no new producer, no `compute_*` truth call.

## 11. Implementation Slices

Small PRs, gate-spec-first, structure-before-polish. Each slice preserves behavior,
ships with dedicated tests, and opens only after its predecessor merges and reviews. No
bundling. Each slice's S5→S6 is its own Owner-gated (L3) decision per the Autopilot
Execution Policy §3.

| PR | Scope | Touches | Risk |
|----|-------|---------|------|
| **PR-1** | B区 队列 + 单一活动面板骨架 — compact Shot Queue (closed status chips, R-SHOT-REASON when flagged), single active Current Shot Work Panel (§3.B.1 / §3.B.2). Replaces the all-shot expanded-card layout. | view + template re-order | Medium |
| **PR-2** | B区 Slot Editor + Assignment — typed slots with honest classification (§3.B.3), Assignment as the only mutable object (§3.B.4), upload primary, advanced binding folded, future slots status-only. | view + template | Medium |
| **PR-3** | C区 批量再次生成入口 + V1/V2 双态文案 — single batch entry (§3.C.1), V1/V2 dual-state copy (C-1), delivery/confirm preservation. | template re-order + view | Medium |
| **PR-4** | Closeout docs + operator trial checklist — acceptance audit (§8), no-leak audit, forbidden-path audit, four-party signoff. | docs only | Docs-only |

> Reviewer-fail / new-defect corrections are authored as separate narrow follow-up
> PRs, never folded back into a merged slice.

Recommended ordering: **PR-1 → PR-2 → PR-3 → Closeout (PR-4)**. PR-1 establishes the
scalable skeleton; PR-2 makes the slots honest and the Assignment clear; PR-3 lands the
batch/compare semantics; PR-4 closes out.

## 12. Forbidden Paths

Any appearance in a slice's `git diff --name-only` is an automatic fail:

```
gateway/app/services/asset/          gateway/app/services/hot_follow*
gateway/app/services/digital_anchor/ **/artifact_storage.py
schemas/                             docs/contracts/
CURRENT_ENGINEERING_FOCUS.md         routers/ (no route behavior change)
```

Allowed implementation paths only: `gateway/app/templates/task_workbench.html`,
`gateway/app/services/matrix_script/operator_workbench_view.py`, and Matrix Script test
suites under `gateway/app/services/tests/`.

## 13. Signoff (gate opens on merge)

| Role | Name | Date | Verdict |
|------|------|------|---------|
| Architect | `<fill>` | `<fill>` | opens S5→S6 for PR-1 only |
| Reviewer | `<fill>` | `<fill>` | READY TO MERGE (gate spec) |
| Operations Coordinator | `<fill>` | `<fill>` | binds Closeout (PR-4) |
| Product Manager | `<fill>` | `<fill>` | binds Closeout (PR-4) |

Architect + Reviewer signoff merged to `main` **opens the implementation gate for PR-1
only**. Coordinator + PM bind the Closeout acceptance audit (§8, PR-4), not gate
opening. This spec authorizes no code; the first allowed action after signoff is PR-1
per §11. Opening each subsequent slice (PR-2, PR-3) is its own Owner-gated S5→S6 (L3)
decision per the Autopilot Execution Policy §3 — listing it in §11 does not pre-open it.

## 14. Authority Boundary

- This gate spec is **derived from #228 Product Plan + the validated v2 preview +
  operator review (Round 2 PASS)**.
- It **does not supersede Bucket A** architecture/design authority.
- It is the **v2 successor to the Guided Operator Workflow Gate Spec for the B区 model
  only**; A/C/D/E inherit the Guided Gate Spec except where §3.C.1 amends C区.
- It governs **only future Matrix Script Slot Workflow v2 UI implementation** (B区 model
  + C区 batch entry + Matrix Script tests).
- It **does not authorize** any backend generation / storage / provider / Akool /
  schema / contract change.
- The Product Plan, preview, and operator review remain **inputs (NOT Bucket A
  authority)** — this spec does not move them into Bucket A.
- Execution logs remain evidence only (Design Authority Index Anti-Sprawl rule 1).

## 15. Authority Pointers

- Bucket A: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A.
- Product Plan: `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_PRODUCT_PLAN_20260607.md`.
- Preview: `docs/design/previews/matrix_script_slot_workflow_v2_preview.html`.
- Operator Review: `docs/reviews/matrix_script_slot_workflow_v2_operator_review.md`.
- Predecessor gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md`.
- Guided Workflow closeout: `docs/execution/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_CLOSEOUT_20260607.md`.
- Wave gate: `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_RULES.md`.
- Process: `docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md`, `…AUTOPILOT_EXECUTION_POLICY_20260607.md`.

*This is an accepted-pending-signoff gate spec for future UI implementation. It
implements nothing, opens no wave, and supersedes no authority. Code begins only after
§13 signoff merges, one slice at a time, under the standard discipline.*
