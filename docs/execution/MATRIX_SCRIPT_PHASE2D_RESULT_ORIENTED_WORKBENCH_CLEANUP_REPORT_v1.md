# Matrix Script · Phase 2D Result-Oriented Workbench Cleanup · Report v1

Date: 2026-05-30
Status: **Template-layout / copy / presenter-shaping refinement only.** No
contract / schema / packet / closed-enum / route / runtime / worker / provider
change. No Phase 3. No Asset Supply bridge. No VoiceTrans bridge. No faked media.
No `main` merge. No new VeoMatrixVoice branch.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (ApolloVeo
Matrix Script Phase 2D Result-Oriented Workbench Cleanup Operator).

---

## 1. Branch and base

| Item | Value |
|---|---|
| Base branch | `VeoMatrixVoice05` |
| Fix branch | `fix/ms-script-to-video-phase2d-result-oriented-workbench-20260530` |
| Commit message | `fix(matrix-script): make workbench result-oriented` |

---

## 2. Problem statement

The Matrix Script Workbench presented a **process-first A–I panel stack**
(任务摘要 → 脚本理解 → 视频生成计划 → 画面与素材 → 角色与声音 → 字幕与音乐 →
视频变体 → 校对与微调 → 交付入口). Each backend stage was its own equal-weight
primary section, so the operator's first scan was dominated by internal
production steps and four empty "待主视频生成" review zones — not by the result
("是否已生成主视频 / 当前能否交付 / 下一步要确认什么"). The page read like a
backend pipeline status board rather than a result-oriented operator console.

---

## 3. Before / after information architecture

### Before (process-first primary sections)
```
★ 主视频结果
B 脚本理解            (primary <h2>)
C 视频生成计划 · 故事板 (primary <h2>)
D 画面与素材          (primary <h2>)
E 角色与声音          (primary <h2>)
F 字幕与音乐          (primary <h2>)
G 视频变体            (primary <h2>)
H 校对与微调          (primary <h2>, four empty 待主视频生成 review zones)
4 交付入口
5 技术诊断 (fold)
```

### After (result-oriented primary sections)
```
①  主视频结果         (dominant first surface; capability banner relocated below it)
②  生成方案确认        NEW group header — merges 脚本理解 + 视频生成计划
                       · operator summary: 「系统已根据脚本整理出视频方向和分镜草案…」
                       · storyboard (故事板) is the dominant visible content
                       · 脚本理解 demoted to a collapsed <details> supporting detail (<h3>)
                       · 视频生成计划 · 故事板 demoted to <h3>, scene list stays visible
③  成片要素调整        NEW group header — merges 画面与素材 / 角色与声音 / 字幕与音乐
                       · summary: 「系统已给出默认成片配置，你可以按账号风格微调。」
                       · three example lines (海边/圣女果特写… / 清爽女声… / 大字高亮…)
                       · §D / §E / §F demoted from <h2> to compact <h3> subcards
④  视频版本（可选）    NEW group header — demotes 视频变体
                       · framed as optional, generated AFTER the main video is confirmed
                       · V1 / V2 / V3 cards visible (待生成); 哪里不同 / 为什么测 / 适合哪些账号
                       · legacy <h2>视频变体</h2> heading + all anchors preserved
⑤  交付入口           unchanged copy + CTA (前往交付页面 →)
—   技术诊断 (fold)    default collapsed; all legacy A–F / stepper markers preserved
```

校对与微调 (§H) is **removed from the primary section set**: its container
anchor stays in place between §G and §I, but its content is collapsed into a
default-closed `<details>` ("校对与微调（主视频生成后开放）") and its heading is
demoted out of the primary `<h2>` set. The four `ms-section-review-tuning-zone`
sub-anchors + `review_pending_main_video` status codes are preserved inside the
fold for back-compat.

### How the reorg preserved structural back-compat
The Phase 2B structural suite asserts the document order of the legacy container
anchors (`matrix-script-main-video-result` → … → `matrix-script-section-delivery-entry`).
Rather than physically reorder those containers, Phase 2D:
- **inserts NEW group-header cards** with `ms-section-*` data-roles
  (`ms-section-plan-confirm`, `ms-section-final-elements`,
  `ms-section-video-versions-group`) immediately before the relevant legacy
  containers; and
- **demotes** the legacy section headings (`<h2>` → `<h3>`, or into a
  `<details>`), keeping every legacy container + sub-anchor in place and in order.

This makes the new group headers the operator-facing primary `<h2>` set while
the legacy anchors survive untouched for the Phase 2B / 2C tests.

The capability banner was also relocated from **above** §A to **below** §A so
the result panel is the dominant first surface (this additionally fixed the
pre-existing `test_section1_is_first_op_card_in_branch` failure).

---

## 4. Files changed

| File | Status | Kind |
|---|---|---|
| `gateway/app/templates/task_workbench.html` | MODIFIED | Result-oriented IA: new group headers + heading demotions + §H collapse + banner relocation |
| `gateway/app/services/tests/test_matrix_script_phase2d_result_oriented_workbench.py` | NEW | 13-case scoped Phase 2D regression test |

`git diff --stat`: 1 file changed (+127 / −37) + 1 new test file. **Zero**
entries under `docs/contracts/`, `schemas/`, `samples/`, any packet / closed-enum
file, any router / worker / generator / runtime module, or any Hot Follow /
Digital Anchor / Asset Supply / VoiceTrans path. No route, endpoint, or
presenter-shape (Python) change — the edit is template + test only.

---

## 5. Tests run

### New scoped file `test_matrix_script_phase2d_result_oriented_workbench.py` — 13 cases, all green
1. Primary section order is result-oriented (主视频结果 → 生成方案确认 → 成片要素调整 → 视频版本（可选）→ 交付入口 → 技术诊断 fold).
2. New group headers render the operator titles as primary `<h2>`.
3. 校对与微调 is not a primary `<h2>` section (collapsed into `<details>`; 4 zones preserved in fold).
4. 脚本理解 / 视频生成计划 are no longer separate primary `<h2>` headings (demoted to `<h3>`).
5. Storyboard scene list is visible inside 生成方案确认 (after the header, before 成片要素调整).
6. Hook / Body / CTA + 关键词 / 禁用词 + audience/tone/duration anchors preserved as supporting detail.
7. 画面与素材 / 角色与声音 / 字幕与音乐 are `<h3>` subcards inside 成片要素调整.
8. V1 / V2 / V3 visible under 视频版本（可选）; legacy `<h2>视频变体</h2>` preserved; all three still 待生成.
9. No fake final_video / thumbnail / media URL / `<video>` / publish_url in primary view.
10. No provider / model / vendor / engine vocab in primary view.
11. No VoiceTrans `<iframe>` embed; no-iframe note preserved.
12. Delivery entry copy + CTA preserved; publish hub template not touched by Phase 2D.
13. Hot Follow + Digital Anchor templates carry no Phase 2D marker / Matrix-Script-only anchors.

### Focused regression (Python 3.13 venv, `PYTHONPATH=.`)
```
pytest gateway/app/services/tests/ -k matrix_script -q
→ 8 failed, 1503 passed, 711 deselected
```
- The Phase 2B / 2C structural + readability suites stay green (all legacy
  container + sub-anchors preserved).
- The 13 new Phase 2D cases pass.
- `test_section1_is_first_op_card_in_branch` (previously failing on the base
  tree) now **passes** thanks to the capability-banner relocation.

### 5.1 Pre-existing unrelated failures (NOT caused by this PR)
The 8 remaining failures are the documented pre-existing baseline (9 on the
clean `VeoMatrixVoice05` tree, now 8 after this PR fixed one):
- `test_matrix_script_new_page_redesign_2026_05_28` — 2 funcs (target
  `matrix_script_new.html`, untouched here).
- `test_matrix_script_phase_b_authoring` — 2 funcs (legacy Phase B authoring
  expectations superseded by the redesign).
- `test_matrix_script_source_script_ref_shape` — 2 funcs (stale "forbid pasting
  body" assertions superseded by the Phase 2C paste tab; already flagged for a
  separate follow-up).
- `test_matrix_script_workbench_dispatch::test_get_workbench_renders_matrix_script_phase_b_variation_panel` — 1 func.
- `test_operator_console_ui_rebuild::test_matrix_script_workbench_uses_operator_language_block_titles` — 1 func (asserts legacy `matrix-script-block-*` titles).

These pre-date and are independent of this Phase 2D layout cleanup. **Net effect
of this PR on the matrix_script suite: −1 failure, +13 new passing tests, zero
new regressions.**

---

## 6. Known limitations

- The reorganization is **layout / copy only**. The merged "sections" are
  presentational group headers wrapping legacy cards; there is no new
  presenter/view object and no contract behind them.
- Storyboard rows, V1/V2/V3 cards, 画面/角色/字幕 contents remain deterministic
  placeholders carrying honest `*_pending_*` status codes — nothing is generated
  and no media is faked.
- 校对与微调 and the variant actions remain disabled-with-tooltip until the
  generation worker lands (out of this wave's scope).
- The 8 pre-existing unrelated test failures remain (out of scope for this PR).

---

## 7. No-change statement (what this PR does NOT do)

This PR does NOT: start Phase 3; change any contract, schema, packet, or closed
enum; change any route / endpoint / runtime / worker / provider logic; add a
backend video worker; add an Asset Supply bridge; add a VoiceTrans bridge; fake
`final_video` / thumbnails / media URLs / `publish_url` / metrics / generated
media; expose provider / model / vendor / engine controls; embed VoiceTrans;
touch Hot Follow / Digital Anchor / Asset Supply runtime / VoiceTrans runtime;
redesign the New Task page; modify the Delivery Center (publish hub) template;
create a new VeoMatrixVoice branch; or merge to `main`.

---

## 8. Verdict

**Ready for manual result-oriented Workbench validation.** The Matrix Script
Workbench now leads with the result (主视频结果) and presents four
operator-language primary sections (生成方案确认 → 成片要素调整 → 视频版本（可选）
→ 交付入口) plus the default-collapsed 技术诊断 fold; 校对与微调 is demoted out of
the primary scan; all legacy contracts / anchors / status codes are intact; and
the 13-case Phase 2D suite plus the Phase 2B / 2C suites are green (the only
remaining failures are pre-existing, unrelated, and reduced by one).
