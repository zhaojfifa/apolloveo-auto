# Matrix Script UI · Visual Validation Report

Date: 2026-05-28
Scope: Visual validation of the Matrix Script Operator UI Redesign wave
landed earlier today (UI / presenter / copy layer only). No backend
generation, no contract / packet / runtime change implied by this report.

## Test setup

- Gateway: `uvicorn gateway.app.main:app --port 8765` running on
  pyenv Python 3.13.5 with `AUTH_MODE=off`, `WORKSPACE_ROOT=.local_workspace`,
  `HF_HUB_OFFLINE=1`, `FASTER_WHISPER_MODEL=/tmp/nonexistent-skip-warmup`.
- Viewport: 1280×800 (Screenshot 1 also captured at the default ~800px
  width to document the responsive degradation).
- Browser harness: Claude Preview MCP (`preview_screenshot`).
- Task captured: `task_id = 2be4843363da`, created end-to-end through
  the redesigned ingest flow (`POST /tasks/matrix-script/source-script-refs/ingest`
  → minted handle `content://matrix-script/source/mint-605df2921b034d79`
  → form POST to `/tasks/matrix-script/new` redirected to the workbench).
- Sample script: 3-line Hook / Body / CTA, ~150 characters of Chinese
  product-video copy mocking a TikTok pitch.

## Screenshot paths

The rendered images live inline in the conversation transcript (the
preview-screenshot harness returns JPEG content inline, not to disk).
The HTML responses the gateway served — i.e. the source-of-truth of
what each rendered image shows — are saved here:

| # | Capture intent | HTML on disk | Inline image |
|---|---|---|---|
| 1 | Matrix Script new task page · full first screen | `visual/01_matrix_script_new_first_screen.html` | inline (1280×800, scroll=0) |
| 2 | Paste-script input state (sample script content typed in) | same file, DOM after `fill` | inline (1280×800, scrolled to Card 1) |
| 3 | Upload-script input state (upload tab active, file picker visible) | same file, DOM after tab switch | inline (1280×800, scrolled to Card 1) |
| 4 | Workbench Block A · 任务摘要 | `visual/04-07_workbench_full_rendered.html` | inline (1280×800, scrolled to Block A) |
| 5 | Workbench Blocks B + C · 脚本结构 + 变体方案 | same file | inline (1280×800, scrolled to Block B) |
| 6 | Workbench Blocks D + E · 生成进度 + 候选评审 empty state | same file | inline (1280×800, scrolled to Block D) |
| 7 | Workbench Block F + collapsed F · 诊断 | same file | inline (1280×800, scrolled to Block F) |
| 7b (extra) | Diagnostics fold expanded for quarantine audit | same file with `details.open = true` | inline (1280×800, scrolled to fold) |

A `visual/README.md` next to this report walks through how to reproduce
each capture locally.

## Visual score — 26 / 35

Scored per the seven user-required captures (5 points each); deductions
recorded with explicit anchors so a follow-up iteration knows what to
fix.

| # | Dimension | Score | Why |
|---|---|---|---|
| 1 | New task page first screen | **4** / 5 | Clean op-card layout; mission subtitle "创建后，系统会解析脚本结构、生成变体方案，并进入工作台评审。" rendered correctly; emerald matrix-script pill present. Small alignment: at the default narrow viewport the topbar nav wraps and the matrix-script pill floats slightly above the heading text. At 1280px the layout is clean. −1 for the responsive-degradation. |
| 2 | Paste-script input state | **5** / 5 | Active-tab pill switches to "粘贴脚本"; textarea accepts the Hook / Body / CTA sample verbatim; helper text reiterates volatility + no-vendor-leakage commitment; Card 2 (任务基本信息) populates with provided meta. No operator-facing leakage. |
| 3 | Upload-script input state | **5** / 5 | Tab switch (via real DOM click) updates active styling + ARIA + panel visibility; file picker reads `选择文件 / 未选择任何文件`; helper text names `.txt` / `.md` + 64 KB cap. (Note: the MCP `preview_click` tool failed to dispatch a click that reached the JS handler — verified to be a harness quirk, not a UI defect — `element.click()` from `preview_eval` does switch tabs correctly.) |
| 4 | Workbench task summary (Block A) | **4** / 5 | Block A reads cleanly: 主题 / 受众 / 目标平台 / 目标语言 fields are present and operator-readable; 当前阻塞 amber banner + 下一步建议 blue banner; "前往交付中心" + "前往发布反馈" jump buttons render at the top-right. −1: the 当前总状态 row carries both a status badge ("阻塞") AND an inline headline ("阻塞 · 成片缺失") — they restate each other and add visual noise without adding information. |
| 5 | Script structure + variant plan (Blocks B + C) | **3** / 5 | Block B Hook/Body/CTA cards + keyword / forbidden chips render. Block C variant table renders 4 candidate rows with 差异点 / 视角概要 / 节奏-时长 / 脚本片段 columns. −2: **raw axis vocabulary leaks into operator panels** — the Body card shows `audience=[b2b, b2c] · length=[30, 45, 60, 75] · tone=[casual, formal, playful]` and the variant-table 差异点 column shows `tone=正式 (formal) · audience=面向企业 (b2b) · length=30s`. `b2b`/`b2c`/`formal`/`casual`/`playful` are Phase-B internal axis values; the variant-table already proves operator-language is possible in the 视角概要 column ("语气=正式 · 受众=面向企业 · 时长=30s"). The 差异点 column and the Body card should drop the bracketed raw English. |
| 6 | Generation progress + candidate review empty state | **2** / 5 | Block E empty-state is exactly mission-mandated: "当前暂无可预览成片 / 已完成脚本结构与变体方案；成片生成能力接入后将在这里展示候选视频。" Block D primary / secondary buttons + status pill render. **−3: significant English-ID leakage into operator-visible copy** — Block D banner subtext reads "下一步 · 解除 `publish_readiness` 阻塞项后再尝试；具体阻塞原因见 `head_reason`." and the 说明 cell reads "当前发布门禁阻塞；`head_reason`=成片缺失。请按 Workbench E 的阻塞建议先解除前置项." Both `publish_readiness` and `head_reason` are internal IDs that the redesign explicitly relocated to F · 诊断 (Mission §5). Block E and Block F tech-note disclaimers also leak `final_video` / `publish_readiness` / `RC-R8` outside the quarantined fold. |
| 7 | Delivery summary + collapsed technical diagnostics (Block F + F · 诊断) | **3** / 5 | Block F headline "当前不能交付：尚未生成成片。" exactly matches Mission §4; "已具备：脚本结构、变体方案。" matches; scene-pack non-blocking note present; CTA to Delivery Center present. The collapsed `F · 诊断` fold sits at the bottom with the operator-language summary and stays collapsed by default. **−2: "待补齐" deviates from the mission baseline** — actual render shows derived contract row labels "变体清单、脚本 slot 包。" instead of Mission §4's literal "成片、字幕、音频、manifest、交付包。" On a real task the Jinja prefers the derived missing-items list (contract `kind_label_zh` values) over the canonical operator baseline. Also a third small tech-note leak ("本面板不展示 final_video / 发布 URL · final_video 主体在交付中心渲染 (RC-R8)") visible inside the operator card. |

**Total: 26 / 35.**

The expanded F · 诊断 audit (7b, not part of the 35) confirms quarantine
works as designed: `SOURCE_SCRIPT_REF`, `VARIATION_TARGET_COUNT`,
`TARGET_PLATFORM`, `AXES`, `CELLS`, `SLOTS`, `READY_STATE`,
`matrix_script_variation_matrix@v1`, `head_reason = final_missing`, and
the opaque `content://matrix-script/source/mint-...` handle all live
inside the collapsed details. Daily operators do not see them unless
they explicitly expand the fold.

## Pass / Partial / Fail verdict

**PARTIAL.** New-task page (Screenshots 1–3) is operator-verifiable as-is.
Workbench primary panels (Screenshots 4 + 7) are largely operator-readable.
The quarantine pattern itself works (7b confirms it). But Block D and the
Block E / Block F tech-note disclaimers actively leak English IDs into
operator-visible copy, and Block F "待补齐" deviates from the mission's
canonical operator wording. These are presentation-layer fixes — no
contract / packet / runtime change — but they ARE the kind of leakage
the redesign was meant to eliminate.

## Top 5 operator-facing issues

1. **Block D leaks `publish_readiness` and `head_reason` in operator copy** (Screenshot 6).
   Banner subtext: "解除 `publish_readiness` 阻塞项后再尝试；具体阻塞原因见 `head_reason`."
   说明: "head_reason=成片缺失。请按 Workbench E 的阻塞建议先解除前置项。"
   Fix: replace `publish_readiness` with "发布门禁", drop `head_reason` (the operator-language label already says the same thing two lines up), drop the positional "Workbench E" reference in favour of "候选评审区" by name. Move the residual technical phrasing into the F · 诊断 fold.

2. **Block E and Block F tech-note disclaimers leak `final_video` / `publish_readiness` / `RC-R8` outside the quarantined fold** (Screenshots 6 + 7).
   Sample: "本面板不展示 final_video / 媒体链接 / 发布 URL — 上述项由统一 publish_readiness 与 Delivery Center 收敛 (RC-R8)."
   Fix: rephrase as operator-language: "本面板不展示完整成片或外部链接；完整成片在交付中心。" Move the engineering reference (RC-R8 / publish_readiness / final_video) into the F · 诊断 fold for architects only.

3. **Block F "待补齐" diverges from the mission canonical list** (Screenshot 7).
   Actual: "变体清单、脚本 slot 包。" (contract row labels)
   Mission: "成片、字幕、音频、manifest、交付包。"
   Fix: change the Jinja so the mission baseline always renders, with operator-language overlays appended/struck-through based on resolved deliverables. Stop surfacing raw contract `kind_label_zh` ("脚本 slot 包") on the operator surface.

4. **Block B Body card + Block C 差异点 column expose raw Phase-B axis values** (Screenshot 5).
   Body card: "audience=[b2b, b2c] · length=[30, 45, 60, 75] · tone=[casual, formal, playful]."
   差异点 column: "tone=正式 (formal) · audience=面向企业 (b2b) · length=30s."
   Fix: map axis-id + raw-value tuples to operator-language phrasing (the 视角概要 column already proves this is possible). The raw `(b2b)` / `(formal)` / `(playful)` parentheticals should be dropped from operator-visible columns and only retained inside F · 诊断.

5. **Responsive degradation: at narrow viewport (≤880px) the topbar wraps and the matrix-script pill misaligns** (Screenshot 1 mobile-default capture).
   The page is desktop-first by design but degrades poorly on tablet widths — "矩阵脚本" wraps onto two lines and the line pill floats above the heading. Lowest priority of the five; not a blocker for desktop ops.

## Is the UI ready for functional validation?

**No.** The verdict is **"UI needs another visual iteration before functional validation."**

Issues 1, 2, and 3 are explicit Mission §4 / §5 commitments the
redesign promised to deliver (Chinese-first operator language; English
technical identifiers only in collapsed diagnostics; mission-mandated
delivery summary wording). They are visible in the rendered Workbench
on a contract-clean sample task, not on a synthetic fixture. Letting
operators see `publish_readiness` / `head_reason` / `final_video` /
`RC-R8` on primary panels would re-introduce exactly the
contract-projection-heavy feel the redesign was meant to eliminate.

Issues 4 and 5 are lower priority but should be picked up in the same
follow-up iteration — they are pure copy / Jinja fixes.

After those fixes land, the Matrix Script UI is expected to be
visually verifiable, at which point a functional validation pass
(operator actually walks the loop end-to-end with the existing
no-backend constraints) is appropriate.

## Out-of-scope reminders

- This wave still does NOT produce a real `final_video`. The
  redesign + this visual validation only fix what operators see; the
  generation backend remains absent and is Capability Expansion scope.
- The in-process body / closure stores are still volatile.
- This report is observation-only — no contract / packet / runtime
  change is recommended or implied by anything above.
