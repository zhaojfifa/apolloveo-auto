# Matrix Script Guided Operator Workflow — PR-1: A区 State Narration (2026-06-07)

Engineering execution note. Evidence only — not implementation authority.
Gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` §3.A,
slice PR-1 (§5). Owner authorized the S5→S6 transition for **PR-1 only**.
Builds on the merged #211..#215 substrate; reopens none of it.

## Scope (this PR)

A区 operator-language **state narration** only — 当前主视频 / 当前状态(现状) / 下一步.
Pure presentation + projection over the already-derived `process_state` (#215). No
new generation capability, no storage, no route change, no B/C/D/E re-layout.

## What changed

**View (`operator_workbench_view.py`)** — projection only:
- Two normative maps from Gate Spec §3.A: `_PROCESS_STATE_STATUS_ZH` (现状, the
  short operator vocabulary 稳定 / 已记录调整意图 / 素材已就绪 / 正在生成 V2 /
  V2 待确认 / 生成失败 / 未生成) and `_PROCESS_STATE_NEXT_STEP_ZH` (下一步).
- `_build_process_narration(...)` → `process_narration`:
  `current_main_version` (V1/V2, or None before any preview),
  `current_main_version_label_zh`, `status_zh`, `next_step_zh`.
- Added to the view dict as `process_narration`. The raw `process_state` enum is
  unchanged and stays a **diagnosis-only** `data-process-state` attribute.
- **下一步 is phrased zone-agnostically** (action words, e.g. “返回主视频区，点击
  再次生成预览”) so it is correct in the CURRENT layout — the §3.A table’s “到 C 区”
  wording assumes the future PR-3/PR-4 re-order, which this slice does not ship.

**Template (`task_workbench.html`)** — A区 only:
- Replaced the single `生成流程状态：<label>` line with a structured narration
  block carrying stable markers `data-role="ms-process-current-main"` /
  `ms-process-status` / `ms-process-next-step`, rendering 当前主视频 / 当前状态 /
  下一步. The 主视频 line is omitted when no preview exists. `data-process-state`
  is preserved for Network/DOM diagnosis.

## Behavior preserved

No generation / storage / `artifact_storage.py` / `msmaterial://` resolver /
regeneration / auto-preview lifecycle / schema / contract / route change. The
existing A区 intent_only / material_ready / stable guidance notices are unchanged.
`official_publish_ready` remains **false** in every state. No Hot Follow / Digital
Anchor / Akool / provider touch. No B/C/D/E re-layout.

## Acceptance (Gate Spec §6, A-1 + supporting)

- **A-1** — A区 shows no raw `process_state` enum (or other raw backend field) in
  primary copy; the enum is only a `data-process-state` attribute. Tested with
  attribute-stripped visible copy.
- `official_publish_ready` stays false across states (A-14).

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. New focused suite
`test_matrix_script_pr1_a_state_narration.py` **11 passed** (7 states + leakage +
publish-ready invariant + render markers). Full Matrix Script suite **1862 passed**
(1851 baseline + 11 new; 0 failures). `git diff --check` clean.

## Boundary / not in this PR

PR-2..PR-6 are NOT authorized by this PR. B区 reason/upload-handoff (PR-2),
C区 V1/V2 pivot (PR-3), D区 delivery move (PR-4), E区 fold (PR-5), and Closeout
(PR-6) remain future slices, each opening only after its predecessor merges and the
Owner approves.
