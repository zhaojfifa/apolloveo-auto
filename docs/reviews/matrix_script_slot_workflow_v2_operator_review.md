# Matrix Script Slot Workflow v2 — Operator Review (2026-06-07)

Status: **OPERATOR REVIEW REPORT — docs-only. Not authority, not implementation.**
Harness X S3→S4 gate artifact (role: Operator Reviewer; reads the static preview +
screenshot only, **does not read code**). The verdict is the gate.

Inputs reviewed:
- Preview: `docs/design/previews/matrix_script_slot_workflow_v2_preview.html`
- Screenshot: `docs/design/screenshots/matrix_script_slot_workflow_v2_preview_20260607.png`
- Plan context (not authority): `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_PRODUCT_PLAN_20260607.md` (#228, merged)

Posture: a front-line operator who must run a real 10-shot Matrix Script task. The
question is not "is the code correct" — it is **"can I run this without an engineer,
and is it better than 10 expanded cards?"**

---

## 1. What I was asked to judge

Whether the v2 queue + single-active-panel model solves the post-Guided-Workflow
operator issue: the all-shot expanded-card B区 does not scale; 5 cards are already
repetitive; 10+ shots need a queue/workflow model; the Shot / Slot / Assignment
object model must become clear; material upload/replacement is active now; and
text/subtitle/voice/BGM must not be falsely presented as editable.

## 2. Scenario as rendered

- **10 shots** (MS-TOMATO-BEACH-001), all visible in one compact queue.
- Statuses present and color-coded: **待处理** (Shot 10), **已上传素材** (04/05/06),
  **已跳过** (08), **已进入 V2** (03), **无需处理** (01/02/07/09).
- **Active shot:** Shot 04 · 吃番茄特写 — the only expanded work panel.
- Slot Editor shows five typed slots with honest classification.
- Batch regenerate bar: "已选择 3 个镜头调整，生成 V2 预览".
- V1 current main; V2 candidate; delivery follows V1 (V2 unconfirmed); diagnostics
  collapsed.

## 3. Step-by-step from the operator seat

1. **Where do I start?** A区 tells me V1 exists and the next step is "处理待处理镜头 →
   批量再次生成". B区 is numbered ①队列 ②活动面板 ③槽位 ④决策. I start at the queue. **Clear.**
2. **Which shots need me?** The queue chips do the triage for me: I ignore the four
   无需处理 rows and the 已跳过 row, and go to 待处理 / 已上传素材. The inline reasons
   ("复用素材，缺真实品尝画面") tell me *why*. **This is the scalability win** — I never
   open 10 cards; I scan 10 rows. **Clear.**
3. **Which shot am I working on?** Shot 04 is highlighted (violet border, "▾ 活动中")
   and is the only panel expanded. Clicking another row would move the panel. **Clear.**
4. **What can I actually change here?** Only the 画面素材槽 (visual_material_slot)
   shows a green "现在可调整" badge with real buttons + upload. **Clear.**
5. **What about copy / subtitle / voice / music?** 文案 and 字幕 are marked
   "仅展示（暂不可编辑）" with read-only values and no controls; 配音 and 背景音乐 are
   marked "后续工作流（尚不可用）". I am not tricked into clicking a dead capability. **Honest.**
6. **What is my decision recording?** The Assignment panel ④ shows the option set, my
   current decision (补充素材), the bound file, lock state (已锁定进入下一次 V2), and
   consumption state (尚未被 V2 消费). I understand this is the only thing I changed. **Clear.**
7. **How do I generate?** One amber batch bar: "已选择 3 个镜头调整，生成 V2 预览",
   with copy that says regeneration happens *after* I finish the selected shots, not
   per card. **Clear and the right model.**
8. **What happens to delivery?** D区 says 交付候选 is V1, will switch to V2 only after
   confirm, 正式交付就绪：否. The C区 guard repeats "V2 确认前不影响交付". **Preserved.**

## 4. Confusing points (honest, operator-seat)

- **C-1 (clarity, non-blocking):** The scenario has *two* notions of V2 on screen at
  once — Shot 03 是「已进入 V2」(already consumed by the current candidate), while
  Shot 04/05/06 是「待下一次再次生成进入 V2」. I could follow it on a careful read, but a
  busy operator might wonder whether pressing "生成 V2 预览" makes a *new* V2 or *updates*
  the existing one, and what happens to Shot 03's state. The copy gets me there, but
  the relationship deserves one tightening sentence (e.g. "再次生成会在现有 V2 基础上，
  把这 3 个镜头一起更新进 V2").
- **C-2 (polish, non-blocking):** The future slots (配音 / 背景音乐) render a
  *disabled button* ("编辑配音（暂不可用）"). It is clearly disabled and not editable, but
  a disabled control still advertises a capability that doesn't exist; a pure status
  line ("配音：后续工作流") would be cleaner and even less misleading.

Neither point blocks me from completing the task. They are copy/visual refinements,
both cheaply addressed and both naturally encodable as binding rules in the future
Gate Spec amendment.

## 5. Recommended changes (carry into a light preview touch and/or the Gate Spec amendment)

1. Tighten the V2 dual-state copy so the relationship between an existing V2 and a
   batch-regenerate that updates it is one unambiguous sentence (addresses C-1).
2. Render future slots (voiceover / bgm) as pure status, dropping the disabled button
   (addresses C-2).

## 6. Operator review checklist

| Item | Verdict |
|------|---------|
| operator knows where to start | **PASS** |
| shot queue is scannable | **PASS** |
| active shot is clear | **PASS** |
| material slot is clearly actionable | **PASS** |
| display-only slots are not misleading | **PASS** |
| future slots are not misleading | **PASS WITH ISSUE** (C-2: disabled button advertises a non-existent capability) |
| assignment model is understandable | **PASS** |
| batch regenerate is understandable | **PASS** |
| V1/V2 relationship is preserved | **PASS WITH ISSUE** (C-1: dual-V2-state copy needs one tightening sentence) |
| delivery remains confirmed-main only | **PASS** |
| diagnostics do not distract | **PASS** |

## 7. Does v2 solve the stated problem?

**Yes.** The queue + single-active-panel decisively replaces the all-shot expanded-card
model: 10 shots are triaged in one scan, exactly one shot is in focus, the
Shot / Slot / Assignment objects are named and visible, the only truly-actionable slot
(visual_material_slot) is the only one with controls, and display/future slots are
honestly non-editable. It scales to 10+ shots in a way the old model does not. Batch
regenerate replaces per-card regeneration. V1/V2 and delivery semantics are unchanged.

## 8. Verdict

**PASS WITH ISSUES.** The v2 model is validated and clearly superior; two specific,
non-blocking copy/clarity refinements (C-1, C-2) remain. Per Harness X §5, PASS WITH
ISSUES does not auto-advance to Gate Spec — it routes back for a light Preview/Plan
touch and re-review, or the Owner may judge the two items minor enough to record
directly as binding copy rules in the Gate Spec amendment scope.

## 9. Boundary

- docs-only; reads preview + screenshot only; no code read; no runtime, template,
  service, test, schema, contract, or Gate Spec change.
- Not authority; does not authorize implementation; does not advance any signoff.

*This is a Harness X Operator Review (S4 gate artifact). The verdict is the gate; the
Owner decides the next transition.*
