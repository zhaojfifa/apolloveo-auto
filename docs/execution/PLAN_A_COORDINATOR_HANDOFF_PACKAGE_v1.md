# Plan A · Coordinator Handoff Package v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave
Status: Handoff package. **Documentation only. No code, no UI, no runtime change.** This document is a single-page coordinator-runnable consolidation that points at the existing Plan A authorities verbatim. It is **not** a replacement authority and does **not** introduce new semantics. Every load-bearing instruction is cited to the underlying authority by section; the underlying authority remains the truth.

## 0. What this document IS / IS NOT

- **IS:** a single sheet the human trial coordinator can carry into the trial environment. It consolidates pointers (with section anchors) so the coordinator does not have to navigate three documents in parallel during a live operator session.
- **IS NOT:** a re-author of the brief or the write-up; it does not paraphrase load-bearing wording (§0.1 sample-validity criteria, §0.2 product-meaning, §5 explanation 口径) — those are quoted verbatim with section citations or pointed at by anchor.
- **IS NOT:** an authorisation to run the trial. The five conditions in [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §12 (extended to eight by §8.H) must hold before any operator session.
- **IS NOT:** a record of execution. Live-run evidence is captured in [docs/execution/PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) (empty placeholder for ops team) and ultimately appended to [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 by the human operations team.

If anything in this handoff appears to conflict with the underlying authority, the underlying authority wins.

## 1. Authority pointers (read in this order before briefing operators)

1. [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) — the frozen operator trial brief.
2. [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) — the trial coordination & static verification write-up (read both §1–§10 body and §11 §8.D addendum and §12 §8.E/§8.F/§8.G/§8.H addendum).
3. [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §3 + §7.1 — current-wave gate + frozen next sequence.
4. [docs/execution/PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md](PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md) — the pre-trial read-only re-verification of §3 static evidence rows on the current branch.

## 2. Pre-trial guards (must hold before any operator submits anything)

Source: [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §2.1, copied verbatim:

1. **Hide Digital Anchor entry surfaces.** New-Tasks card click target for Digital Anchor and the temp route `/tasks/connect/digital_anchor/new` MUST be hidden or disabled in the trial environment (per brief §6.3 + §8 row 1). If the trial environment cannot hide them, post a top-of-page operator notice that Digital Anchor is preview-only; do not rely on operator memory to enforce this.
2. **Hide Asset Supply / B-roll page.** Per brief §4.1 + §8 row 5. The page is contract-frozen, not implemented; any operator interaction is unsafe.
3. **Brief the §5 explanation 口径.** Coordinator reads the Task Area / Workbench / Delivery Center explanations verbatim to operators, including the "current vs historical" rule and the "scene-pack never blocks publish" rule.
4. **Restrict trial sample set to brief §7.1.** Brief §7.2 samples are explicitly excluded; coordinator stops the trial if any §7.2 pattern is observed.
5. **Confirm coordinator has the abort criteria.** If any §8 risk activates (operator submits Digital Anchor; vendor selector appears; third-line URL resolves; Matrix Script Delivery row treated as confirmed), pause trial and file a regression note before continuing.

### 2.1 Concrete deployed-branch surface to hide / disable (audit-confirmed on HEAD)

| Surface | Path | Action | Authority |
| --- | --- | --- | --- |
| Digital Anchor New-Tasks card click target | [gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html) — `<a href="/tasks/connect/digital_anchor/new...">` | Hide / disable in trial env | Brief §4.1, write-up §3.3 |
| Digital Anchor temp connect route | `/tasks/connect/digital_anchor/new` (handler at [gateway/app/routers/tasks.py:567](../../gateway/app/routers/tasks.py)) — driven by `_TEMP_CONNECTED_LINES` at [tasks.py:541](../../gateway/app/routers/tasks.py) | Block via env-side guard or operator-facing top-of-page notice | Brief §4.1, write-up §3.3 |
| Asset Supply / B-roll page | No deployed module (`gateway/app/services/asset_library/` does not exist) | No nav entry should reach an asset page; if one does, file regression | Brief §4.1, write-up §3.2 |
| Promote intent submit | No deployed module | No submit affordance should be reachable; if one is, file regression | Brief §4.1, write-up §3.2 |

## 3. Operator briefing 口径 (verbatim — coordinator MUST read these to operators)

Source: [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §5.1 / §5.2 / §5.3, with the §8.E / §8.F / §8.G / §8.H additions.

### 3.1 Task Area (`/tasks`, `/tasks/<line>/new`) — brief §5.1

> **What you see:** three lines listed — Hot Follow, Matrix Script, Digital Anchor.
> **What you may do:** submit Hot Follow tasks; submit Matrix Script tasks via the line's create-entry form.
> **What you may not do:** submit Digital Anchor tasks. The Digital Anchor card is preview only; its create form has not yet landed.
> **What's hidden:** vendor, model, provider, engine, route — these are runtime concerns and never appear here.

### 3.2 Workbench (`/tasks/{task_id}`) — brief §5.2

Read brief §5.2 verbatim to operators. Key load-bearing notes from §8.E / §8.G corrections (already inside the brief §5.2 — read them in place):

- **Current vs historical** is UI-inferred from `final_fresh` + timestamps until D2 lands. Do not race resubmits.
- **Empty Phase B fallback** ("No axes resolved on this packet" etc.) → pre-§8.A invalid sample. Discard, create fresh.
- **Bound-method repr** (`<built-in method values of dict object at 0x…>`) on Axes table → pre-§8.G render. Refresh page (template-only fix).
- **Hot Follow stage cards on a Matrix Script workbench** → pre-§8.E render. Refresh page (template-only fix).
- **HTTP 400 "scheme is not recognised" on `source_script_ref`** → §8.F guard working, not a defect.

### 3.3 Delivery Center (`/tasks/{task_id}/publish`) — brief §5.3

> **What you see:** the deliverables for this task — final video, required deliverables, and optional items.
> **What is required vs optional:** required deliverables block publish; optional items (e.g., scene pack) **never block publish**. If you see an optional item missing, that is expected and not an error.
> **What you may do:** for Hot Follow, publish end-to-end. For Matrix Script, inspect — Delivery Center is not yet truth for this line; operate via Workbench publish-feedback closure instead.
> **What you may not do:** rely on a deliverable row labeled "unresolved" for Matrix Script. That label means the artifact lookup has not yet been wired through to L2 truth.

## 4. Matrix Script sample-validity rule (binding) — brief §0.1 verbatim references

A Matrix Script sample qualifies as trial evidence iff **all seven** criteria in [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 hold. The coordinator MUST read §0.1 verbatim to operators before any sample-creation session. Summary anchors (do not paraphrase — read §0.1):

1. Formal `/tasks/matrix-script/new` POST (never `/tasks/connect/...`).
2. §8.A + §8.F opaque-ref shape: scheme ∈ `{content, task, asset, ref}` or bare token; single line; no whitespace; ≤512 chars.
3. §8.F operator transitional convention `content://matrix-script/source/<token>` (recommended).
4. §8.C populated Phase B truth (3 canonical axes `tone`/`audience`/`length`; `variation_target_count` cells; one slot per cell).
5. §8.B + §8.G mounted readable Phase B panel (human-readable Axes table — no bound-method repr).
6. §8.E shared-shell suppression intact (no Hot Follow stage controls in visible HTML).
7. §8.D + §8.H operator brief in force (this handoff package + the brief §0.1 / §0.2 / §6.2 / §7.1 sessions completed).

Pre-§8.A samples (pasted-body) and pre-§8.F samples (`https://` / `http://` / `s3://` / `gs://`, including the live-trigger sample `task_id=415ea379ebc6`) are **invalid evidence** and MUST NOT be reused.

## 5. Product-meaning of `source_script_ref` (binding) — brief §0.2 verbatim references

The coordinator MUST read [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.2 verbatim before any sample-creation session. Anchors (do not paraphrase — read §0.2):

- **IS:** a source-script asset identity handle.
- **IS NOT:** a body-input field (§8.A rejects body text).
- **IS NOT:** a publisher-URL ingestion field (§8.F rejects `https`/`http`/`s3`/`gs`).
- **IS NOT:** a currently dereferenced content address (Plan B B4 contract-only / Plan E gated).

## 6. Per-line runbook — brief §2.3 + §6 verbatim references

Source: [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §2.3, copied verbatim:

| Line           | Allowed actions                                                                                          | Forbidden actions                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Hot Follow     | Submit short-clip golden-path; submit preserve-source variant; publish.                                  | Rapid resubmit / race tests against current-vs-historical (D2 not yet in code).                                |
| Matrix Script  | Submit via `/tasks/matrix-script/new` (target `mm` or `vi` only); inspect Workbench Phase B variation surface; exercise publish-feedback closure per variation row. | Treating Matrix Script Delivery Center row as confirmed delivery; submitting target language outside `{mm, vi}`. |
| Digital Anchor | **Inspect-only.** Open New-Tasks landing; confirm card is labeled preview.                                | Any submission via any route (formal `/tasks/digital-anchor/new` is contract-frozen, not implemented; temp `/tasks/connect/digital_anchor/new` is discovery-only). |

For per-line operator misuse to avoid, read brief §6.1 (Hot Follow), §6.2 (Matrix Script), §6.3 (Digital Anchor) verbatim.

## 7. Approved sample-wave order — brief §7.1 verbatim references

Source: [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §7.1 — coordinator MUST run samples in this order. Each entry's full goal text is in §7.1; do not paraphrase.

1. **Hot Follow — short clip golden path.** §7.1.1.
2. **Hot Follow — preserve-source route.** §7.1.2.
3. **Matrix Script — fresh contract-clean small variation plan.** §7.1.3 (`variation_target_count=4`, `target_language=mm`, `source_script_ref=content://matrix-script/source/<token>`).
4. **Matrix Script — multi-language target.** §7.1.4 (same plan with `target_language=vi`).
5. **Matrix Script — variation count boundary check.** §7.1.5 (one with `variation_target_count=1`, one with `variation_target_count=12`).
6. **Cross-line `/tasks` Board inspection.** §7.1.6.

Sample success/abort criteria for each are in [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §4 (Sample 1 through Sample 5 dry-run).

## 8. Abort triggers — brief §8 + write-up §5 verbatim references

Source: [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §5 (the live-monitoring trigger table), copied verbatim — do not paraphrase:

| Trigger                                                                              | Action                                                                                       |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Operator clicks Digital Anchor card and reaches a create form (any).                 | **Pause trial.** File regression note. The hide/disable guard from §2.1 step 1 failed.       |
| `not_implemented_phase_c` rendered on Matrix Script Delivery row appears as a system error to operator. | Coordinator restates brief §6.2 explanation; this is by-design until Plan E.                 |
| Optional row (scene-pack, archive, pack_zip) presented as a publish blocker.         | **Pause trial.** Validate against Plan C `scene_pack_blocking_allowed: false`; file regression. |
| Vendor / model / provider / engine selector appears anywhere.                        | **Pause trial immediately.** R3 regression; do not resume until root cause identified.       |
| Asset Supply / B-roll page reached by URL.                                           | Hide via deployed-environment guard or coordinator-enforced URL block; warn operator off.    |
| Advisory row shows an unknown code outside the Hot Follow taxonomy.                  | **Pause trial.** Producer drift; D4 contract pins the closed taxonomy.                       |
| Workbench panel mount fails for a known ref_id.                                      | **Pause trial.** Verify `PANEL_REF_DISPATCH` matches the contract object (D3).               |
| Board / Workbench / Delivery disagree on `publishable` for the same task.            | Note the divergence; expected variability until D1 lands. Do not abort unless divergence is operator-confusing. |

The full risk list is in [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §8 (24 rows including §8.E / §8.F / §8.G / §8.H additions); coordinator carries §8 verbatim into the live session.

## 9. Conditions for the trial to proceed — brief §12 verbatim

Source: [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §12 (eight conditions post-§8.H), copied verbatim:

1. Trial coordinator briefs operators on §5 explanation 口径 verbatim.
2. Digital Anchor New-Tasks card and `/tasks/connect/digital_anchor/new` are hidden or disabled for the trial duration.
3. Asset Supply / B-roll page is hidden from operator navigation for the trial duration.
4. Trial scope is restricted to §7.1 samples; samples in §7.2 are not attempted.
5. Coordinator monitors for the §8 risk list and pauses the trial if any forbidden surface activates.
6. Matrix Script trial samples MUST be fresh contract-clean samples per §0.1 (post-§8.A / §8.B / §8.C / §8.D / §8.E / §8.F / §8.G, formal `/tasks/matrix-script/new` POST only). Pre-§8.A samples (pasted-body) and pre-§8.F samples (`https://` / `http://` / `s3://` / `gs://`, including the live-trigger sample `task_id=415ea379ebc6`) MUST NOT be reused as trial evidence.
7. Coordinator briefs operators on §0.2 (product-meaning of `source_script_ref`) verbatim before any sample-creation session — `source_script_ref` is a source-script asset identity handle, not a body-input field, not a publisher-URL ingestion field, and not a currently dereferenced content address.
8. Coordinator confirms the recommended operator transitional convention `content://matrix-script/source/<token>` is in use for new Matrix Script samples (other `task://` / `asset://` / `ref://` opaque shapes are also accepted; `<token>` is operator-chosen and treated as fully opaque by the product).

## 10. Required signoff roles after live-run

Source: [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7.1 deliverable.

After the operations team appends live-run results to §8 of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), the following human signoffs are required (per [docs/execution/apolloveo_2_0_role_matrix_v1.md](apolloveo_2_0_role_matrix_v1.md)):

- **Operations team coordinator** — confirms §8 entries are coherent, abort triggers fired and resolved are recorded, regressions filed are linked.
- **Architect** — confirms no scope drift (no Plan E preparation, no Platform Runtime Assembly entry, no Capability Expansion, no frontend patching).
- **Reviewer** — confirms Plan E pre-condition #1 satisfied per [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §9.

The signoff is then pre-condition #1 of Plan E gate spec authoring per the unified alignment map §7.1 → §7.2.

## 11. What the AI agent did not do (binding)

The AI agent that prepared this handoff package:

- Did **not** execute any sample.
- Did **not** invent any `task_id`, date, surface note, or signoff.
- Did **not** modify the brief, the write-up, the alignment map, or any contract / runtime / template.
- Did **not** open Plan E preparation; did **not** patch UI or code; did **not** reopen any §8.A → §8.H correction.
- Did read the boot sequence ([CLAUDE.md](../../CLAUDE.md), [unified alignment map](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md)) and the Plan A authorities ([OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md)) before producing this consolidation.
- Did run a read-only authority audit; the audit note is at [PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md](PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md).
- Did create an empty live-run capture template at [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md), explicitly marked as "to be filled by the human ops team during real execution; not AI-generated evidence."
- Did record the preparation step at [PLAN_A_HANDOFF_PREPARATION_EXECUTION_LOG_v1.md](PLAN_A_HANDOFF_PREPARATION_EXECUTION_LOG_v1.md).

End of Plan A coordinator handoff package.
