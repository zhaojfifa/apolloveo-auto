# Matrix Script UI — Manual Visual Validation (2026-05-28)

## Test environment

- Gateway: `uvicorn gateway.app.main:app --port 8765` (pyenv Python 3.13.5)
- Env: `AUTH_MODE=off`, `WORKSPACE_ROOT=$PWD/.local_workspace`,
  `HF_HUB_OFFLINE=1`, `FASTER_WHISPER_MODEL=/tmp/nonexistent-skip-warmup` (whisper
  warmup intentionally short-circuited; not needed for matrix_script UI).
- Viewport: 1280×800 (initial Screenshot 1 captured at 1366×900 mobile-default).
- Task created for workbench captures: `task_id = 2be4843363da` (entry
  ingested via `/tasks/matrix-script/source-script-refs/ingest` →
  `content://matrix-script/source/mint-605df2921b034d79`).
- Sample script body (paste): three-line Hook / Body / CTA copy mocking a
  short product video pitch.
- Sample task meta: 主题 = "视觉验证样本 V001 (运营可读样本)" / source = zh
  / target = mm / platform = TikTok / 变体数量 = 4 / hints all populated.

## Screenshot index

The actual rendered images for each step are inline in the
conversation transcript (the screenshot harness returns JPEG content
inline and does not write to disk). The HTML responses the gateway
served are saved here under `*.html` so the renders can be reproduced
locally by opening them in a browser pointed at the running gateway.

| # | Capture intent | Source HTML | What is visible |
|---|---|---|---|
| 1 | Matrix Script new task page — full first screen, paste tab default | `01_matrix_script_new_first_screen.html` | Topbar + page heading + mission copy subtitle + Card 1 脚本来源 (paste tab active) + textarea placeholder + Card 2 任务基本信息 header + sidebar Card "提交后会发生什么" |
| 2 | Paste tab with sample script content typed in | `01_matrix_script_new_first_screen.html` (DOM state mutated via fill) | Card 1 脚本来源 paste tab + textarea now carrying Hook/Body/CTA sample text + sidebar 4-step explanation + Card 2 fields populated |
| 3 | Upload tab active | `01_matrix_script_new_first_screen.html` (tab switched via DOM) | Card 1 脚本来源 upload tab active + file picker "选择文件 / 未选择任何文件" + helper "支持 .txt / .md 纯文本；最大 64 KB" |
| 4 | Workbench task summary — Block A 任务摘要 | `04-07_workbench_full_rendered.html` | Block A · 任务摘要 with 矩阵脚本 pill + 主题/受众/目标平台/目标语言 + 当前总状态 + 当前阻塞 (amber) + 下一步建议 (blue) + jump buttons (前往交付中心 / 前往发布反馈) |
| 5 | Script structure + variant plan — Blocks B + C | `04-07_workbench_full_rendered.html` | Block B · 脚本结构 (Hook / Body / CTA cards + 关键词 / 禁用词 chips) + Block C · 变体方案 with variant table (4 rows: 差异点 / 视角概要 / 节奏-时长 / 脚本片段) |
| 6 | Generation progress + candidate review empty state — Blocks D + E | `04-07_workbench_full_rendered.html` | Block D · 生成进度 (status pill "暂不推荐 · 发布门禁阻塞", primary "⚡ 生成 4 个变体", secondary "↻ 重新生成被阻塞的变体 (4)" disabled, blocker banner) + Block E · 候选评审 empty-state banner ("当前暂无可预览成片 / 已完成脚本结构与变体方案；成片生成能力接入后将在这里展示候选视频。") |
| 7 | Delivery summary + collapsed technical diagnostics — Block F | `04-07_workbench_full_rendered.html` | Block F · 交付摘要 with amber "当前不能交付：尚未生成成片。" banner + 已具备 / 待补齐 grid + "前往交付中心查看完整成片 →" CTA + scene_pack non-blocking note + F · 诊断 collapsed fold at bottom |
| 7b (extra) | Technical diagnostics expanded for audit | `04-07_workbench_full_rendered.html` (details.open = true) | Architect view: Matrix Script · 工作台理解 / 四区对齐 / 任务身份 (AXES / CELLS / SLOTS / READY_STATE) / 变体概要 / Workbench A 脚本结构区 with raw SOURCE_SCRIPT_REF / VARIATION_TARGET_COUNT / TARGET_PLATFORM identifiers and `head_reason = final_missing` — confirming quarantine works |

## Reproducing locally

1. Start the gateway as above.
2. `open http://127.0.0.1:8765/tasks/matrix-script/new` — Screenshots 1–3.
3. Submit the form (paste tab; sample body). Note the resulting `task_id`.
4. `open http://127.0.0.1:8765/tasks/<task_id>` — Screenshots 4–7.
5. Expand the "F · 诊断" `<details>` at the bottom for Screenshot 7b.

The full visual validation report is in `VISUAL_VALIDATION_REPORT.md`
alongside this file.
