# Matrix Script Guided Operator Workflow — PR-2: B区 逐镜卡片主流程收敛 (2026-06-07)

Engineering execution note. Evidence only — not implementation authority.
Gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` §3.B,
slice PR-2 (§5). Owner authorized S5→S6 for **PR-2 only**. Builds on the merged
#211..#215 substrate + PR-1 (#220); reopens neither.

## Scope (this PR)

B区 shot-card main-flow convergence — presentation/projection only:
- **R-SHOT-REASON (§3.B.2 / A-2):** each reuse-source shot explains *why* it is
  suggested for handling, framed `建议处理原因：…`.
- **Upload primary (§3.B.1 / A-4):** the upload control is always-visible and listed
  first.
- **Advanced binding folded (§3.B.1 / A-3):** reference-binding stays a collapsed
  `<details>` relabelled `高级：绑定已有素材引用` with the helper
  `仅当你已有系统素材引用时使用。普通运营请上传素材。`; `asset://` is no longer a
  required primary input.
- **R-UPLOAD-HANDOFF (§3.B.2 / A-5):** after a shot's material is attached and before
  a V2 candidate exists, a `下一步：素材已上传。请点击“再次生成预览”生成 V2。` nudge
  renders right by the upload area.

## What changed

**View (`operator_workbench_view.py`)** — projection only:
- Per-shot `suggested_for_handling` + `suggestion_reason_zh` (set in `_build_shots`
  from the existing `source == fallback_semantic_reuse` signal; per-shot phrase
  reproduces the established copy, prefixed `建议处理原因：`).
- Per-shot `upload_handoff_zh` (set in `_enrich_shot_observability` when material is
  attached and no candidate exists yet).

**Template (`task_workbench.html`)** — B区 shot card only:
- Suggestion rendered from `suggestion_reason_zh` (inline fallback retained for
  legacy hand-built overlays so the established copy still renders).
- Upload block promoted to a primary, always-visible `<div>` listed before the
  advanced binding `<details>`; handoff nudge added inside the upload block.
- Binding relabelled to `高级：绑定已有素材引用` + helper; `asset://` example dropped
  from the primary surface.

## Behavior preserved

No generation / storage / route / `artifact_storage.py` / schema / contract change.
The per-shot decision actions (使用/补充/替换), upload + binding endpoints, visual
source trace, and #212 byte-consumption projection are all unchanged. C/D/E
untouched. `official_publish_ready` stays **false**. No Hot Follow / Digital Anchor
/ Akool / provider touch.

## Acceptance (Gate Spec §6)

A-2 (shot reason), A-3 (advanced binding folded), A-4 (upload primary), A-5
(upload→regenerate handoff) — all covered by `test_matrix_script_pr2_b_zone_convergence.py`.
A-11 (no leakage), A-12 (#212 byte-consumption unchanged), A-14
(`official_publish_ready=false`) also asserted. A-15 (forbidden-path scan clean)
verified by the change-set scan.

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. New focused suite **11 passed**.
Full Matrix Script suite **1873 passed** (1862 baseline + 11 new; 0 failures) — two
existing B区 tests stayed green via the template's backward-compat suggestion
fallback + the preserved upload-helper phrase. `git diff --check` clean;
forbidden-path scan clean.

## Boundary / not in this PR

PR-3..PR-6 are NOT authorized by this PR. C区 V1/V2 pivot (PR-3), D区 delivery move
(PR-4), E区 fold (PR-5), and Closeout (PR-6) remain future slices, each opening only
after its predecessor merges and the Owner approves.
