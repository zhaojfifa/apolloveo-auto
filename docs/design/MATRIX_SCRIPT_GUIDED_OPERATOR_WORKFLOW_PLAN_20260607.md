# Matrix Script — Guided Operator Workflow Planning Review (2026-06-07)

Status: **PLANNING PROPOSAL — docs-only. Not implementation authority. Not a new
Matrix Script IA / mock / reset / next-wave design that supersedes Bucket A.**

Author posture: ApolloVeo 2.0 Architect, operator-workflow lens.
Branch baseline: `main` at the merge of #215.

## 0. What this document is — and is not

This is a **运营视角的流程重规划评审 (guided operator workflow planning review)**.
It looks at the Matrix Script Workbench *as a person operating it would*, and asks
whether the capabilities that engineering has shipped are arranged into one
executable operating procedure — or merely exposed.

It does **not**:

- supersede or replace any Bucket A binding authority
  (`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` §A) — it cites them and
  feeds a future gate spec;
- author a new Information Architecture, mock, or parallel Workbench flow
  (Design Authority Index Anti-Sprawl rules 2 & 4) — every regroup proposed here
  re-homes value into an **existing** A–J / A–E section, never a new parallel
  surface;
- open, authorize, or sequence any engineering wave — engineering remains
  gate-spec-first per `ENGINEERING_RULES.md` and the wave gate in
  `CURRENT_ENGINEERING_FOCUS.md`;
- change generation, storage, contracts, schema, samples, templates, or code.

When this document's wording conflicts with Bucket A authority or
`CURRENT_ENGINEERING_FOCUS.md`, the underlying repo authority wins.

## 1. main baseline confirmation

The following are confirmed merged on `main` (verified against `git log`):

| PR | Subject | Merge |
|----|---------|-------|
| [#211](https://github.com/zhaojfifa/apolloveo-auto/pull/211) | P1-3 PR-C — Shot Material Upload / Storage Handle | `323199a4` |
| [#212](https://github.com/zhaojfifa/apolloveo-auto/pull/212) | P1-3 PR-D — Regenerate Consumes Uploaded Material Bytes | `9ede2985` |
| [#213](https://github.com/zhaojfifa/apolloveo-auto/pull/213) | P1-3 Material Bytes Closure (docs) | `7d797f58` |
| [#214](https://github.com/zhaojfifa/apolloveo-auto/pull/214) | P1-3 Operator Copy Clarity (shot material decision) | `5ba22c52` |
| [#215](https://github.com/zhaojfifa/apolloveo-auto/pull/215) | Operator Process Observability for Workbench | `d113f002` |

Substrate cited: `docs/execution/MATRIX_SCRIPT_P1_3_MATERIAL_BYTES_CLOSURE_20260606.md`,
`docs/execution/MATRIX_SCRIPT_P1_3_OPERATOR_COPY_CLARITY_20260607.md`,
`docs/execution/MATRIX_SCRIPT_OPERATOR_PROCESS_OBSERVABILITY_20260607.md`.

**The finding that motivates this review:** with #211–#215 the line can now (a)
generate a V1 main video, (b) let an operator decide per shot to keep / supplement
/ replace material, (c) upload real material bytes, (d) regenerate a V2 candidate
that actually consumes those bytes, (e) confirm or discard V2, and (f) expose the
whole process state. **Each capability is real and individually correct. But they
are presented as a flat field of controls and badges, not as one guided
procedure.** The operator can see everything and is told nothing about the order in
which to do it. That is the productization gap this plan addresses.

---

## 2. Q1 — What capabilities exist today?

Grouped by what the operator can actually *do* or *see* on `main`.

**Generation & version lifecycle**
- C1. Generate a first main video preview (V1) from script + bound material.
- C2. Regenerate a V2 *candidate* off the request thread; V1 is never overwritten
  (L1 lifecycle: queued/running/succeeded/failed/retry, with stale guard + poll).
- C3. Confirm V2 → V2 becomes current main, delivery follows V2, intents cleared;
  or discard V2 → V1 stays current main.
- C4. Failure path: failed regeneration writes no V2 and keeps V1, with a retry
  affordance.

**Per-shot material decision loop**
- C5. Per shot: 使用当前素材 / 补充这个镜头素材 / 替换这个镜头素材 (decision
  intent, #214 copy).
- C6. Upload real material bytes for a shot (`msmaterial://` handle,
  `bytes_resolvable=true`, local-workspace scope; #211).
- C7. V2 regeneration consumes uploaded bytes honestly — image used directly,
  video used only when first-frame extraction succeeds; otherwise honest
  reference-label copy and `material_bytes_consumed=false` (#212).
- C8. Per-shot trace: 这个镜头现在用了什么 (visual source: 原始生成 / 运营上传 /
  运营绑定引用 / 复用 / 降级占位), 是否进入 V2, observability status,
  调整后会发生什么 (#215).

**Process observability**
- C9. A single derived `process_state` ∈ not_generated / stable / intent_only /
  material_ready / generation_running / candidate_ready / failed, with an
  operator-safe `process_state_label_zh` and an A-区 banner (#215).
- C10. State-aware material guidance (intent_only vs material_ready vs running),
  V1/V2 preview-version markers, version-aware delivery candidate.
- C11. Stable DOM `data-action` / `data-process-state` / `data-preview-version`
  markers making the intent / upload / regenerate / status-poll / preview-GET
  requests identifiable in the Network tab.

**Delivery & diagnostics**
- C12. Delivery candidate follows the *confirmed* main only; never claims V2 before
  confirm; `official_publish_ready=false` everywhere.
- C13. Script understanding / story view (E 区).
- C14. Video variants view (D 区).
- C15. J · 技术诊断 — raw/engineering fields, collapsed by default.

---

## 3. Q2 — Which of these are the operational mainline?

The **mainline** is the smallest path that takes an operator from "task opened" to
"a main video I am willing to confirm." Everything else is in service of, or
adjacent to, that path.

**Mainline (the spine — must be linear, numbered, and unmissable):**

1. **看首版** — review the V1 main video (C1, the A-区 result).
2. **逐镜判断** — walk shots; for each, decide keep / supplement / replace (C5, C8).
3. **补素材** — for shots that need it, upload material (C6).
4. **再次生成** — regenerate V2 candidate from the changed material (C2, C7).
5. **对比 V1/V2** — compare current main vs candidate (C10).
6. **确认或丢弃** — confirm V2 as main, or discard and keep V1 (C3).
7. **进入交付候选** — delivery follows the confirmed main (C12).

Capabilities C9/C10/C11 (process state, version markers, action markers) are not
*steps* — they are the **status spine** that should annotate each step ("you are
here / this is what just happened / this is what to do next"). Today they exist as
fields; in the mainline they should read as a guided narration.

**This is the single executable procedure the Workbench should teach.** The review's
core recommendation is that steps 1–7 become a visible, ordered guided flow rather
than five co-equal lettered sections the operator must self-assemble.

---

## 4. Q3 — Which should be folded into advanced capability?

Capabilities that are real and worth keeping, but that a first-time operator does
not need in the primary linear path. Fold these behind a labelled "高级 / 进阶"
disclosure that is **collapsed by default but one click away** — not removed, not
buried in diagnostics.

- **D 区 视频变体 (C14)** — variants are a power feature; the mainline is "one main
  video, confirm it." Variants belong in an advanced lane reachable after a main is
  confirmed, not as a co-equal step between delivery and script.
- **E 区 脚本理解 / 故事理解 (C13)** — valuable *context*, but it is read-only
  understanding, not an action the operator performs to move the task forward. Fold
  it to a collapsible "为什么是这样生成的 / 脚本理解" context panel anchored near
  step 1, expanded on demand.
- **Per-shot deep trace detail (the full C8 field set)** — the headline "这个镜头
  用了什么 + 是否进入 V2 + 下一步" stays inline on the mainline; the exhaustive
  field list (bytes_consumed flags, source enumerations, observability sub-status)
  folds into a per-shot "详情" expander.
- **Reuse / fallback material sourcing** (复用素材 / 降级占位素材 visual sources) —
  surfaced as a status label inline, but the operator's *choice* set stays the three
  clean options (keep / supplement / replace); the fallback mechanics are advanced
  context.

Folding criterion: **if removing it from the primary path does not break the
"open → confirm a main video" procedure, it folds.**

---

## 5. Q4 — Which belong to diagnostics only?

Strictly J · 技术诊断, collapsed by default (Design Authority Index Anti-Sprawl
rule 5). These are *engineer/architect* surfaces, never operator-actionable:

- Raw artifact references, `msmaterial://` / `asset://` handles as raw strings,
  raw manifest, raw JSON, `local_path` (already never projected — keep it that way).
- `process_state` raw enum value (the operator sees only `process_state_label_zh`;
  the raw token is diagnostic).
- L1 lifecycle internals beyond the operator-safe "生成中 / 失败 / 可重试" framing.
- `material_bytes_consumed` boolean, `consumed_materials[]` internal list, version
  slot `source=material_regeneration` and `created_at` timestamps.
- The `data-action` / `data-process-state` / `data-preview-version` DOM markers —
  these are *diagnosis affordances* (see Q8), present in the DOM and Network view but
  not rendered as operator-facing copy.
- Provider / model / vendor / engine / Akool anything — **forbidden from operator
  payloads entirely**, not merely collapsed (this is a red line, see Q10, not a
  diagnostics item to be exposed even in J).

Rule of thumb: **diagnostics answer "why did the system do that"; the mainline
answers "what do I do next." If a field cannot change what the operator does next,
it is diagnostics.**

---

## 6. Q5 — How should Workbench A/B/C/D/E be re-ordered?

**Current order (as rendered on `main`):**

| Now | Zone | Problem from the operator's seat |
|-----|------|----------------------------------|
| A | 主视频预览 / 生成视频 | Correct as step 1. |
| B | 背景、素材、配乐调整 | Correct as the editing body. |
| C | 交付入口 | **Delivery appears before the operator has even compared/confirmed a version.** |
| D | 视频变体 | Advanced feature sitting on the mainline. |
| E | 脚本理解 / 故事理解 | Context is *last*, after delivery — read in the wrong order. |

The lettering implies five co-equal stops. The actual procedure is a loop
(review → adjust → regenerate → compare → confirm) feeding a terminal (deliver),
with two side-panels (script-context, variants) that are not stops at all.

**Proposed re-arrangement** (re-homing within the existing sections — not a new IA):

| New | Zone | Role | Source |
|-----|------|------|--------|
| **A** | 主视频结果 + 流程状态 | **Step 1.** The current main video + the process-state narration banner ("你在这一步 / 刚才发生了什么 / 下一步"). Script-understanding context folds here as a collapsed "为什么这样生成". | C1, C9, C10 + folded C13 |
| **B** | 逐镜调整与素材 | **Steps 2–4.** The shot-by-shot keep/supplement/replace + upload loop, with the per-shot headline trace inline and deep trace folded. | C5–C8 |
| **C** | 生成与对比 (再次生成 → V1/V2 对比 → 确认/丢弃) | **Steps 5–6.** Promote the regenerate→compare→confirm decision into its **own** explicit zone. Today this is split between A's acceptance block and scattered version markers; it deserves to be the named pivot of the workflow. | C2, C3, C4, C10 |
| **D** | 交付候选 | **Step 7, terminal.** Delivery follows the confirmed main; moved *after* the confirm decision, not before it. `official_publish_ready=false` stays visible. | C12 |
| **进阶** | 视频变体 + 深度诊断入口 | Collapsed advanced lane. Variants live here, reachable after a main is confirmed. | C14 |
| **J** | 技术诊断 | Unchanged — collapsed, architect-only. | C15 |

The single most important move: **delivery (old C) must come after the
confirm decision, and the regenerate→compare→confirm pivot deserves to be a named
zone of its own** rather than being implied by badges in the result block. Variants
and script-understanding leave the mainline.

> Implementation note for the future gate spec: this re-homing must be done by
> re-ordering / re-labelling existing sections and moving already-rendered fields,
> **not** by creating new panels or a parallel flow (Anti-Sprawl rule 4). No new
> `data-role` semantics, no new truth.

---

## 7. Q6 — How should each state read in operator language?

The derived `process_state` (C9) is the right backbone. The recommendation is to
make every state read as a **sentence the operator can act on**, in three parts:
*现状 → 原因 → 下一步*. Current labels are close; this tightens them to the guided
narration.

| `process_state` | 现状 (operator copy) | 下一步 it should imply |
|-----------------|----------------------|------------------------|
| `not_generated` | 还没有生成主视频 | 确认素材与配乐后，点击「生成主视频预览」 |
| `stable` | 已有可用的主视频（V1），暂无改动 | 可逐镜检查素材，或进入交付候选 |
| `intent_only` | 已记录素材调整意图，但还没有上传/绑定素材 | 先到 B 区上传或绑定这个镜头的素材 |
| `material_ready` | 素材已就绪，但还没有体现到新预览里 | 回到生成区点击「再次生成预览」 |
| `generation_running` | 正在生成新版本预览（V2 候选） | 稍候，本页会自动更新；这一步不会动到当前主视频 |
| `candidate_ready` | 新预览（V2 候选）已生成，等待你对比确认 | 对比 V1 与 V2，确认设为主版本或丢弃 |
| `failed` | 这次生成没有成功 | 当前主视频未受影响，可查看原因后「再次生成预览」 |

Companion vocabulary (already landed in #214, keep aligned):

- 镜头决策：使用当前素材 / 补充这个镜头素材 / 替换这个镜头素材
- 镜头状态：待上传素材 / 已标记补充素材 / 已标记替换素材 / 已上传，等待再次生成预览
- 版本：当前主视频 V1 ｜ 新预览候选 V2（确认前永远是「候选」）

**Forbidden in any state copy:** version-slot internals, provider/model/engine names,
`material_bytes_consumed` as a raw boolean, any "正式发布就绪/true" claim, any URL.

---

## 8. Q7 — After each button click, what should the operator expect?

Each action should produce an **immediate visible acknowledgement** + a **next-step
nudge**. Today the mechanics are correct (#215 observability); the gap is that the
expected outcome is not always *stated* to the operator before/after the click.

| Button | Operator should expect | Visible after | Does NOT happen |
|--------|------------------------|----------------|------------------|
| 生成主视频预览 | 进入「生成中」状态，页面自动轮询更新 | A 区状态→`generation_running`；完成后 V1 出现 | 不会立即可发布 |
| 使用当前素材 (per shot) | 该镜头标记为「使用当前素材」，不触发生成 | 镜头状态更新；无新预览 | 不上传、不生成 |
| 补充这个镜头素材 | 进入补素材意图；提示去上传 | 镜头→`待上传素材`；A 区→`intent_only` | 不立即改主视频 |
| 替换这个镜头素材 | 标记替换意图；提示去上传 | 镜头→`已标记替换素材` | 不立即改主视频 |
| 上传这个镜头的新素材 | 素材被校验并保存，可预览 | 镜头→`已上传，等待再次生成预览`；A 区→`material_ready` | **不会自动覆盖主视频** |
| 再次生成预览 | 生成 V2 *候选*，当前主视频不动 | 状态→`generation_running`→`candidate_ready` | V1 不被覆盖 |
| 设为主版本（确认 V2） | V2 成为当前主视频，交付跟随 V2 | 当前版本→V2；意图清空；交付候选更新 | 不发布到正式渠道 |
| 丢弃新预览 | 候选移除，V1 仍为当前主视频 | 候选消失；当前版本仍 V1 | 不影响已上传素材记录 |

The general rule the gate spec should encode: **every action that does not
immediately change the main video must say so before the operator wonders why
nothing happened** (the #214 copy did this for upload; extend it to all material
decisions). And **every action that changes state must echo the new state in
operator language within the same view**.

---

## 9. Q8 — Diagnosable Network / action log without leaking technical detail

The #215 observability layer already established the right principle: stable DOM
`data-action` markers make each request identifiable, while the *operator-facing
copy* stays clean. The plan keeps and systematizes this two-channel split:

**Channel 1 — operator copy (visible, clean):** state sentences (Q6), step
narration, never a URL / provider / handle / raw enum.

**Channel 2 — diagnosis affordances (present, identifiable, non-leaking):**
- Stable `data-action="matrix-script-…"`, `data-process-state`,
  `data-preview-version="V1|V2"` attributes so a support engineer reading the DOM or
  the Network tab can map a request to a step.
- Requests are *identifiable by name/shape* (intent POST, upload POST, regenerate
  POST, status GET poll, preview `final.mp4` GET) but their **payloads/responses
  carry only operator-safe fields** — guarded by the existing `_assert_clean` scan +
  leakage test. No `local_path`, raw manifest, provider, publish URL, or Akool
  task/model/credit in any primary-UI-reachable response.
- A future "运营操作记录 / action log" (if proposed) should log **operator-language
  step events** ("上传 Shot 04 素材 → 已就绪", "确认 V2 为主版本"), not raw request
  bodies. The diagnostic correlation (which DOM action, which state) stays in the
  data-attributes / Network view, not in the operator-readable log.

Design rule for the gate spec: **diagnosability lives in attributes and request
shape; it must never require putting a technical string into operator-readable
copy.** If a diagnosis need can only be met by leaking a handle/URL/provider into the
operator UI, it is reclassified to J 技术诊断 instead.

---

## 10. Q9 — How many engineering PRs should this split into?

Gate-spec-first. **Nothing below is authorized to start** — it is a slicing
*proposal* for a future gate spec authored under `ENGINEERING_RULES.md` and the
wave gate. Each PR is a pure presentation / copy / re-order layer over the
already-frozen #211–#215 substrate; none touches generation, storage, contracts, or
schema. Sliced so each PR is independently shippable and reviewable, smallest
operator-value-bearing increment first.

| PR | Scope | Operator value | Risk |
|----|-------|----------------|------|
| **PR-1 — State narration** | Tighten `process_state` copy to the 现状→原因→下一步 sentences (Q6); no layout change. | Operator can read where they are. | Lowest (copy only). |
| **PR-2 — Action outcome echo** | Per-action acknowledgement + next-step nudge for every material/generate/confirm button (Q7); extend the #214 "upload doesn't auto-overwrite" pattern to all decisions. | Operator knows what each click did. | Low (copy + existing markers). |
| **PR-3 — Zone re-order** | Re-home A/B/C/D/E per Q5: split out the regenerate→compare→confirm pivot as its own named zone; move 交付 after confirm. Re-label/re-order existing sections only — no new panel. | The Workbench reads as one procedure. | Medium (template re-order; needs careful test-marker preservation). |
| **PR-4 — Advanced fold** | Fold 视频变体 + 脚本理解 + per-shot deep trace into collapsed 进阶 / context disclosures; keep headline inline. | Mainline is uncluttered; power features one click away. | Medium (visibility logic; must not hide mainline). |
| **PR-5 — Diagnosis hygiene + action-log framing** | Systematize the two-channel split (Q8); optional operator-language step-event log; leakage-test extension. | Supportable without leaking. | Low–medium. |
| **PR-6 — Closeout** | Docs-only: operator-comprehension walkthrough, no-leak audit, no-second-truth audit, freeze audit, four-party signoff. | Governance closure. | Docs-only. |

Recommended ordering: **PR-1 → PR-2 → PR-3 → PR-4 → PR-5 → Closeout**, each opening
only after its predecessor merges + reviews. PR-1/PR-2 deliver operator value with
near-zero structural risk and can validate the narration model before the PR-3
re-order touches layout. If a tighter scope is wanted, PR-1+PR-2 (copy) and
PR-3+PR-4 (structure) are the two natural halves.

A production browser validation pass (the "next recommended engineering" from the
bytes-closure doc) should gate entry to this slicing: prove the end-to-end loop live
before re-arranging it.

---

## 11. Q10 — What must absolutely not change

These are inherited red lines from Bucket A, the Result-Capability Recovery gate
spec, the OWC freezes, and the P1-3 closure boundaries. **None of the workflow
re-planning above is permitted to touch any of them.**

- **生成链路 (generation chain)** — script→shot-plan→`final.mp4`→artifact_staged
  →preview_url→acceptance. Re-ordering the UI must not re-wire generation.
- **storage / `artifact_storage.py`** — untouched. Matrix-Script material stays in
  the `local_workspace`-scoped `shot_material_storage.py`; no provider/publish
  surface.
- **schema / contracts** — no closed-enum widening, no new contract, no schema
  change (`docs/contracts/**`, `schemas/**` frozen).
- **Akool** — no Akool surface / task / model / credit, live or projected.
- **Hot Follow** — zero file touch; benchmark line stays byte-stable.
- **Digital Anchor** — zero file touch; the five operations not-trial-capable
  findings remain in force; no DA scope widening.
- **`official_publish_ready=false`** — stays false at every checkpoint; delivery is
  a *candidate*, never a published deliverable.
- **No provider / model / vendor / engine** promoted into any operator payload.
- **V1 protection** — regeneration never overwrites the current main; confirm is the
  only path that promotes V2.
- **No second source of truth** — no new producer; projections read existing packet
  truth / `publish_readiness` / `final_provenance` / advisory output only.
- **No private memory / off-index cognition file** (CLAUDE.md §3) — this review is a
  native `docs/design/` file, not a parallel ledger.

---

## 12. Open questions for the next gate-spec author

1. Should the regenerate→compare→confirm pivot (proposed new C 区) be a genuinely
   separate section, or an always-expanded sub-block inside A? (Affects PR-3 test
   markers.)
2. Is an operator-language **action log** in scope now, or deferred? (Q8 / PR-5.)
3. Does the production browser validation pass (bytes-closure doc §"Next") need to
   land and sign before PR-1 opens, or in parallel?
4. Confirm with operations which of D 视频变体 / E 脚本理解 they actually consult
   during a run — if neither is used operationally, the fold (Q3) can be more
   aggressive.

---

## 13. Authority pointers (read these, not this, for truth)

- `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` — Bucket A binding authority.
- `docs/product/matrix_script_product_flow_v1.md` + `…_v2_delta.md` — product flow.
- `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` — RC scope
  + forbidden scope this plan inherits.
- `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md` — wave gate + allowed work.
- `docs/execution/MATRIX_SCRIPT_P1_3_MATERIAL_BYTES_CLOSURE_20260606.md`,
  `…_OPERATOR_COPY_CLARITY_20260607.md`,
  `…_OPERATOR_PROCESS_OBSERVABILITY_20260607.md` — #211–#215 substrate evidence.

*This planning review is evidence + proposal only. It authorizes no code, opens no
wave, and supersedes no authority. Implementation requires a separate gate spec
under the standard discipline.*
