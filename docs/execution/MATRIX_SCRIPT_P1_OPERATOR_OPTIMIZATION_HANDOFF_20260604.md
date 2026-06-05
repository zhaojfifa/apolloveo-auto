# Matrix Script P1 Operator Optimization — Harness Handoff (2026-06-04)

Lightweight engineering coordination file for Harness-scheduled remote Claude
runs on Matrix Script P1. Read **only this file plus the minimal set in §7**.
Do not re-read full history. Do not produce broad summaries.

---

## 1. Current P0 baseline (closed)

```
Matrix Script P0 is CLOSED.
#202 = artifact truth + failed-generation finalization
#203 = async lifecycle (queued/running/succeeded/failed) + polling + stale guard
       + operator-visible terminal state
Validated on Render at SHA bf4af50b (= merged #203 tree on main a2c6d1f0).
Closure baseline: docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md
```

Fixed main flow (must be preserved by every future PR):

```
A 主视频预览 / 生成视频
B 背景、素材、配乐调整
C 交付入口
D 视频变体        (folded)
E 脚本理解 / 故事理解 (folded)
F 技术诊断        (collapsed)
```

Lifecycle states (L1): `queued / running / succeeded / failed / retry_required`
(`retry_required` is projection-only, derived from a stale queued/running attempt
older than `RUNNING_STALE_SECONDS = 300`).

Poll endpoint: `GET /api/matrix-script/{task_id}/initial-preview-status`
→ `{status, poll, operator_usable, preview_url, blocked_reason, official_publish_ready:false}`.

---

## 2. Next phase — P1 goal

P1 is **not** a rewrite, **not** Akool, **not** multi-line expansion. P1 closes
exactly one operator loop:

```
运营素材替换 → 再生成预览 → 确认主版本 → 更新交付候选
material replacement → regenerate preview → confirm main version → update delivery candidate
```

The async lifecycle from #203 is reused as-is; P1 adds the *intent + versioning*
on top of it.

---

## 3. Forbidden (hard boundary)

```
- No code in this handoff PR (docs-only).
- Do not touch: Hot Follow, Digital Anchor, artifact_storage.py, schemas/contracts.
- No Akool live / provider / model / vendor / engine controls.
- No new production line, no platform runtime assembly, no capability expansion.
- No new parallel Matrix Script flow; no second Workbench surface.
- Primary UI must NOT expose: artifact refs, raw manifest, provider URLs,
  publish URLs, Akool task/model/credit, technical step internals.
- official_publish_ready MUST remain false.
- Do not reorder the A/B/C/D/E/F flow; do not unfold D/E or expand F into primary.
- No new broad design doc (this file is the only P1 coordination doc).
```

---

## 4. Recommended plan — max 2 PRs

### PR-1: Shot Material Replacement Intent
- B区: each Shot can record a replacement / supplement-material **intent**
  (operator-language only; no provider/artifact internals in primary UI).
- Workbench shows "素材已更新，需要再次生成预览" when an intent is recorded.
- A区 surfaces "再次生成预览".
- Recording an intent must **not** auto-overwrite the current main video and must
  **not** flip the existing delivery candidate.
- Files (expected): `gateway/app/templates/task_workbench.html`,
  `gateway/app/services/matrix_script/operator_workbench_view.py`,
  the Matrix Script-scoped router/service for intent persistence,
  `gateway/app/services/tests/test_matrix_script_*`.
- Tests: intent recorded → "material changed" projection true; current main
  video unchanged; delivery candidate unchanged; no forbidden-token leakage;
  official_publish_ready=false.

### PR-2: Regenerate Preview Versioning (only if PR-1 lands clean)
- Regenerate produces a **new** preview version (reuses the #203 async lifecycle).
- V1 = current main video; V2 = new preview (no auto-promotion).
- Operator can: 设为主版本 / 丢弃 / 继续调整 (confirm-main / discard / keep-tuning).
- Delivery candidate follows the **confirmed main version** only.
- Files (expected): same surface set as PR-1, no new line/contract.
- Tests: V2 generated as async lifecycle terminal; V1 stays main until explicit
  confirm; confirm-main moves delivery candidate to the confirmed version;
  discard keeps V1; official_publish_ready=false throughout.

Stop after at most these two PRs. Re-gate before anything larger.

---

## 5. Minimal Harness → Claude input template

Paste this (fill the slots); do not paste history:

```
Mode: Matrix Script P1 remote engineering.
Read ONLY: docs/execution/MATRIX_SCRIPT_P1_OPERATOR_OPTIMIZATION_HANDOFF_20260604.md
plus the files named in §7 relevant to <PR-1|PR-2>.
Task: implement <PR-1 Shot Material Replacement Intent | PR-2 Regenerate Preview Versioning> per §4.
Constraints: §3 forbidden list is binding. Keep A/B/C/D/E/F flow. official_publish_ready=false.
Deliverable: one PR on branch fix/matrix-script-p1-<slug>; tests; the §6 report.
Do NOT re-read full repo history. Do NOT touch Hot Follow / Digital Anchor / artifact_storage.py / schemas / contracts.
```

---

## 6. Claude → Harness report template

```
Matrix Script P1 PR Report
1. Branch / Commit / PR
2. Files Read (handoff + minimal set actually opened)
3. Scope (what it does / does NOT do / follow-up)
4. Lifecycle (reused #203 states; new intent/version states if any)
5. Tests (focused list; full MS suite count; py_compile; diff --check)
6. Operator Projection (A/B/C states; no forbidden tokens; official_publish_ready=false)
7. Boundary (no Hot Follow / Digital Anchor / artifact_storage.py / schemas / Akool)
8. Verdict PASS/FAIL + single next action
```

---

## 7. Token-saving / no-redundant-read rule

```
Per P1 run, read at most:
1. THIS handoff (always).
2. The files named in §4 for the targeted PR (only those actually edited).
3. One closure baseline reference IF a lifecycle detail is unclear:
   docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md
Do NOT re-read: CLAUDE.md boot chain, ENGINEERING_STATUS history, unrelated
execution logs, or the full docs index, unless a constraint is genuinely
ambiguous. Trust this handoff as the P1 source of truth; if it conflicts with
repo authority, the repo authority wins and this file must be corrected in a
docs-only PR.
Prefer grep/targeted reads over whole-file reads. Reuse the #203 lifecycle and
poll endpoint instead of re-deriving them.
```

---

## 8. Four-layer consistency rule

```
L1 process: queued / running / succeeded / failed / retry_required
            (P1 may add a per-version lifecycle reusing these SAME states; do
             not invent parallel status vocab).
L2 artifact facts: valid final.mp4, manifest, preview route, subtitles/audio if
            present. Material-replacement intent is NOT an artifact fact until a
            regenerate produces a validated final.mp4.
L3 readiness: operator_usable, delivery_candidate, official_publish_ready=false.
            Delivery candidate follows the confirmed main version only; a recorded
            intent or an unconfirmed V2 must not change L3 truth.
L4 operator projection: inline video / failure retry / material loop / delivery
            candidate. L4 consumes L2/L3; it invents no truth and must not show a
            new preview as delivery candidate before validation + confirmation.
```

---

## 9. Operator-perspective consistency rule

```
Primary UI shows only operator states: generating / video ready / failed-retry,
plus the P1 material-loop affordances (替换素材 / 再次生成预览 / 设为主版本 /
丢弃 / 继续调整) in operator language.
Never surface engineering internals (artifact refs, raw manifest, provider URLs,
publish URLs, Akool task/model/credit, step internals) in primary UI.
Keep result-first ordering: A main video first, B material/music, C delivery,
D/E folded, F diagnostics collapsed.
Material replacement is an INTENT until regenerate; regenerate is async (reuse
#203); a new preview is never auto-promoted and never auto-delivery-candidate.
```

---

## 10. Boundary held by this handoff

Docs-only. No code, schema, contract, Hot Follow, Digital Anchor,
`artifact_storage.py`, or Akool changes. `official_publish_ready` remains false.
This file does not authorize implementation by itself — it scopes the P1 work
that subsequent fenced PRs will carry.
