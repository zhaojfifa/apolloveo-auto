# Matrix Script — Operator Process Observability (2026-06-07)

Engineering execution note. Evidence only — not implementation authority. Index
entry: `docs/ENGINEERING_INDEX.md` (Matrix Script Changes). Builds on the merged
P0/P1/P1-2/P1-3 substrate (#202..#214); reopens none of it.

## Why

After #214 operators could see the video and click adjustments, but the
generation *process* was opaque: which inputs were used, which shot used which
material, whether a material was uploaded vs reused vs fallback, what could be
adjusted, whether an adjustment actually entered V2, where V1/V2 differ, and what
requests should appear in the Network tab. This PR opens that process up as a
pure observability layer — no new generation capability, no Akool, no
architecture change.

## What changed (projection + presentation only)

**View (`operator_workbench_view.py`)** — additive projection, no new truth:
- A single derived `process_state` ∈ `not_generated | stable | intent_only |
  material_ready | generation_running | candidate_ready | failed`, with an
  operator-safe `process_state_label_zh`.
- Per-shot trace fields: `visual_source` (+`_label_zh`: 原始生成素材 / 运营上传
  素材 / 运营绑定素材引用 / 复用素材 / 降级占位素材), `entered_current_main`,
  `entered_v2_candidate`, `bytes_consumed_for_shot`, `next_action_zh`,
  `shot_observability_status_zh`, `shot_adjust_outcome_zh`.
- `generation_facts.current_main` (version / source label / shot-match /
  real-visual / missing-material / official_publish_ready=false) and a top-level
  `missing_material_count`.

**Template (`task_workbench.html`)** — A/B/C operator surfaces:
- **A区** carries `data-process-state` + a process-state banner; material
  guidance is now state-aware — `intent_only` says "已记录素材调整意图 / 请先
  上传/绑定素材" and does **not** show "素材已更新，需要再次生成预览";
  `material_ready` shows "素材已就绪，需要再次生成预览"; regeneration running
  shows "正在生成 V2 新预览" with the existing poll + stale guard; V1 hero and V2
  candidate carry `data-preview-version` markers and render separately.
- **B区** each shot card shows "这个镜头现在用了什么？" (visual source), whether
  it entered the V2 candidate, the per-shot observability status (uploaded /
  已上传但未进入新预览 / 已进入 V2 新预览), and "调整后会发生什么？".
- **C区** delivery candidate is version-aware and follows the **confirmed** main
  only ("当前交付候选：主视频 V1/V2"); it never claims V2 before confirm;
  `official_publish_ready=false`.

**Action observability** — stable DOM markers for Network diagnosis:
`data-action="matrix-script-material-intent" | matrix-script-material-upload |
matrix-script-regenerate-preview | matrix-script-regeneration-status"`, plus
`data-process-state` and `data-preview-version="V1|V2"`. The intent POST,
upload POST, regenerate POST, regeneration-status GET poll, and preview
`final.mp4` GET are all visibly identifiable.

## Boundary

No Akool, no provider switching, no new generation capability, no
`artifact_storage.py`, no schema/contract change, no Hot Follow / Digital Anchor
touch, no `official_publish_ready=true`, no broad redesign. No route behaviour
change — the existing `regeneration-status` endpoint already returns
operator-safe state, so `tasks.py` was not modified. No raw manifest / provider /
`local_path` / publish URL / Akool leakage in the primary UI (guarded by the
existing `_assert_clean` scan + a dedicated leakage test).

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. Matrix Script suite
**1851 passed** (14 new observability tests + 2 updated to the state-aware model).
`git diff --check` clean. The 5 pre-existing env-coupled failures
(`test_digital_anchor_new_task_route_shape`, `test_operator_console_ui_rebuild`,
`test_task_router_presenters`) fail identically on clean `main` and are unrelated
to this change.
