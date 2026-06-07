# Matrix Script P1-3 — Shot Material Operator Copy Clarity (2026-06-07)

Short engineering execution note. Evidence only — not implementation authority.
Index entry: `docs/ENGINEERING_INDEX.md` (Matrix Script Changes). P1-3 closure:
`docs/execution/MATRIX_SCRIPT_P1_3_MATERIAL_BYTES_CLOSURE_20260606.md`.

## Why

P1-3 PR-C (#211) and PR-D (#212) landed the shot-material upload / storage handle
and byte-consuming regeneration, and both are merged on `main`. The capability is
correct, but the Workbench B区 per-shot controls used engineering-flavored labels
(`标记替换素材` / `标记补素材` / `保持当前素材`) that did not tell the operator
*when* to choose each option, whether clicking regenerates, or how the choice
relates to uploading material.

The original instruction targeted "PR #211" as if open; on rebuild from `main`,
#211 / #212 (PR-D) / #213 (docs closure) were all already merged. This is
therefore a **fresh copy-only follow-up PR off `main`**, not an update to the
merged #211.

## What changed (copy / layout only)

- Each Shot card now opens a decision area titled **这个镜头怎么处理？** with
  operator-language buttons in choose-order: **使用当前素材 / 补充这个镜头素材 /
  替换这个镜头素材**, plus per-choice helper text explaining when to pick each.
- Upload section relabelled **上传这个镜头的新素材** with helper text stating that
  uploading does **not** immediately overwrite the main video and that the
  operator must return to the main-video area and click **再次生成预览**.
- State label copy aligned: supplement intent → `已标记补充素材`; unattached
  dirty shot → `待上传素材` (was `待补素材`); uploaded → `已上传，等待再次生成
  预览` (unchanged); keep → `使用当前素材` (unchanged); replace →
  `已标记替换素材` (unchanged).

Files: `gateway/app/templates/task_workbench.html`,
`gateway/app/services/matrix_script/operator_workbench_view.py`, and the
`test_matrix_script_*` suites (new
`test_matrix_script_shot_material_operator_copy.py` + label updates in the
primary-flow / replacement-intent / attachment-handle suites).

## Behavior preserved

No route / storage / `msmaterial://` resolver / regeneration / auto-preview
lifecycle / config / schema / contract change. Intent still persists; upload
handle still persists; `bytes_resolvable` stays true for uploaded material; V1
preserved; V2 untouched; delivery follows the confirmed main; primary UI leaks no
provider URL / raw manifest / publish URL / Akool task-model-credit / `local_path`.
`official_publish_ready` remains **false**. No Hot Follow / Digital Anchor /
`artifact_storage.py` touch.
