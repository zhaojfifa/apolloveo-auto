# PR-2A · Workbench Main Video Result Block — Implementation Report

Branch: `redesign/ms-workbench-main-result-pr2a-20260528`
Wave: Matrix Script Operator Experience Implementation — **PR-2A of 7**
Date: 2026-05-28
Rollback point: PR-1 commit `dad8f72`

## Reading Declaration

Reads from PR-1 baseline (already in this branch's history):
[design plan §6.2](../README.md) + [Mission §B.1](../../../../CLAUDE.md), the
existing helpers
`derive_matrix_script_recommended_action` / `derive_matrix_script_preview_compare_view` /
`compute_publish_readiness` / `get_closure_view_for_task`, the contract pin
`publish_feedback_closure_contract_v1.md` (closure schema preserved; no
new event_kind, no widening).

## Files changed

| File | Change | Net |
|---|---|---|
| `gateway/app/services/matrix_script/main_video_result_view.py` | NEW presenter helper. Closed 4-value state enum (未生成 / 生成中 / 待审核 / 可交付), closed 4-action enum (生成主视频 / 重新生成 / 确认为主版本 / 前往交付页面), confirm-main intent detection via the structured `[main-version-confirmed]` operator_note prefix, honest empty-state message verbatim from Mission §B.1, head_reason → operator-language label mapping (engineering enum NEVER leaks). | +397 |
| `gateway/app/services/operator_visible_surfaces/wiring.py` | Wire `derive_matrix_script_main_video_result` into the `panel_kind == "matrix_script"` branch. Read-only closure peek via `get_closure_view_for_task`; defensive try/except so a transient closure failure cannot brick the workbench render. | +37 |
| `gateway/app/templates/task_workbench.html` | New op-card block at TOP of the matrix_script branch (above existing Block A 任务摘要) carrying state pill, preview hero (real bound preview OR honest empty state), 4-action bar (state-dependent enablement; closure endpoint + note prefix wired as data-attrs for client-side write-back), and operator-language blocker + next-action banner. Mission §B.1 wording preserved verbatim. | +99 |
| `gateway/app/services/tests/test_matrix_script_main_video_result_view.py` | NEW · 22 helper unit tests covering state derivation, action enablement, confirm-main detection, no-fake-URL audit, no-vendor-leak audit. | +355 |
| `gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py` | NEW · 9 template-source tests covering block-above-Block-A ordering, data-role marker presence, no engineering identifier in card source. | +94 |
| `docs/design/screenshots/.../pr2a/` | Snapshot + report. | new |

## Scope boundary

**Inside PR-2A**: helper `main_video_result_view.py`, wiring branch for the new helper, template block at the top of the matrix_script workbench branch, tests, PR-2A snapshot + report.

**Outside PR-2A** (sequenced into PR-2B / 2C / 2D / 3 / 4):
- Observable production flow stepper (PR-2B).
- Optional variants redesign (PR-2C).
- Workbench delivery summary + diagnostics quarantine (PR-2D).
- Delivery Center reframing (PR-3).
- Unified visual validation report (PR-4).

The existing Block A 任务摘要 + Blocks B/C/D/E/F + collapsed F · 诊断 fold remain **untouched** in this PR; they sit below the new main video block. They will be re-shaped in PR-2B..2D.

**Bytewise unchanged**: all Hot Follow / Digital Anchor / Asset Supply files, all contracts, all closed enums (`EVENT_KINDS` / `REVIEW_ZONE_VALUES` / `RECORD_KINDS`), all schemas, the POST handlers, the mint/ingest/peek endpoints.

## Screenshots

Real browser captures via Claude Preview MCP on the running gateway (pyenv Python 3.13.5, `AUTH_MODE=off`, `WORKSPACE_ROOT=.local_workspace`, viewport 1280×900). Inline image above in this transcript. HTML snapshot saved here:

| # | Capture | Viewport | URL | HTML | Runtime DOM probe |
|---|---|---|---|---|---|
| 1 | Workbench top — new 主视频结果 block on a real `not_generated` task | 1280×900 | `/tasks/2be4843363da` | [`01_workbench_main_video_result_1280x900.html`](01_workbench_main_video_result_1280x900.html) | state=`not_generated`, pill="未生成", title="主视频结果", 4 actions (generate/regenerate/confirm-main all `enabled=false` + go-to-delivery `enabled=true`), blocker="当前阻塞：主成片缺失。", next="下一步：完善脚本结构与变体方案后等待生成能力接入。" ✓ |

Visual confirmation from the screenshot:
- New block renders at TOP of matrix_script workbench, above the existing Block A 任务摘要.
- Hero preview area: dashed-border 200px+ empty card with the operator-language message verbatim from Mission §B.1 ("当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。").
- 4-action bar laid out left-to-right; the 3 disabled actions are visibly muted; "前往交付页面 →" is the only emerald-primary CTA.
- Amber blocker banner below the actions with the operator-language blocker + next-action one-liners.
- NO engineering identifier visible (`head_reason`, `publish_readiness`, `final_video`, `RC-R8`, `artifact_lookup`, `slot_pack` all absent from the rendered card source).

## Tests

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_main_video_result_view.py \
                    gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py -v
============================== 31 passed in 0.07s ==============================
```

Broader regression: existing matrix_script suite still **1005 pass / 1 fail pre-existing / 17 skipped** (identical to PR-1 baseline; the single failure `test_block_d_resolved_subfield_has_status_resolved_when_caption_present` is pre-existing on main).

## Explicit no-change statement

This PR does **NOT**:
- Touch any contract under `docs/contracts/`.
- Touch any packet shape, closed enum, or `kind_label_zh` value.
- Add a new endpoint (the confirm-main write-back uses the existing
  `POST /api/matrix-script/closures/{task_id}/events` with `event_kind=operator_note`).
- Widen `EVENT_KINDS`, `REVIEW_ZONE_VALUES`, or `RECORD_KINDS`.
- Touch any Hot Follow file.
- Touch any Digital Anchor file.
- Touch any Asset Supply file.
- Add, expose, or hide any provider / model / vendor / engine selector.
- **Fake any `final_video`, `publish_url`, or media reference.** When
  no current_fresh media exists the preview hero renders the
  mission-mandated empty-state message; when current_fresh media exists
  the helper still does NOT echo any URL — only the opaque
  `variation_id` is passed to the template, which displays a
  "candidate N is bound · 完整成片在交付页面" hint with NO embedded URL.
- Add any backend generation capability. "生成主视频" / "重新生成" are
  rendered but **disabled-with-operator-tooltip** until the generation
  worker lands (out of this wave's scope; gated to Capability
  Expansion Wave).

## Remaining backend limitations (unchanged)

- No variant generation backend. Phase B authoring is still a
  deterministic seed at task creation. `生成主视频` button is shown but
  disabled with the tooltip "成片生成能力接入后启用 · 当前阶段仅做结构与
  方案准备。"
- No `final_video` worker. The preview hero renders the honest empty
  state; even when a hypothetical `current_fresh` artifact existed,
  the helper would not synthesize a URL.
- The confirm-main path writes to the volatile in-process closure
  store (lost on gateway restart) per the Recovery Decision §4.3
  known limit.
- The architect `?technical=1` query path from PR-1 remains
  unchanged.

## Matrix Script is not production-operable

This PR moves the **operator UI** one step closer to result-first
visual verifiability. It does NOT add production capability. The wave
target after PR-1..PR-4 remains *"UI visually verifiable; backend
final-video generation remains pending."*

## Rollback

`git reset --hard dad8f72` (PR-1 commit) — removes the PR-2A helper +
wiring + template block + tests + snapshot/report.
