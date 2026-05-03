# Matrix Script §8.F Opaque Ref Discipline — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, follow-up blocker review v1, item §8.F — Option F1)
Status: implementation green; ready for signoff
Authority:
- [docs/reviews/matrix_script_followup_blocker_review_v1.md](../reviews/matrix_script_followup_blocker_review_v1.md) §6 (§8.F — Opaque Ref Discipline vs Operator Usability), §8 (Recommended Ordering — §8.F lands third after §8.G and §8.E), §9 (Gate Recommendation — §8.F BLOCKED on authority decision; Option F1 recommended)
- Authority decision: Option F1 accepted (tighten the scheme set; defer minting to Plan E; brief operators on the transitional `<token>` convention). Options F2 (in-product minting flow) and F3 (accept the slippage / document it) explicitly REJECTED in this wave.
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)" + §"Opaque-by-construction discipline (§8.F tightening, 2026-05-03)" + §"Operator transitional convention (Plan A trial wave only)" + §"Why this is contract-tightening AND a usability adjustment" + §"Out of scope for §8.F" landed in this change)
- [docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md) (§8.E — landed; ops trial retry pipeline now has a clean shell against which §8.F's tightened scheme set can be exercised)
- [docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md) (§8.G — landed)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed; the guard whose accepted-scheme set this change tightens)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) (§8.D — landed; operator brief unchanged here; §8.H is the natural successor that re-aligns the brief)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation, §11 Scope Control
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the standing
execution discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
[PROJECT_RULES.md](../../PROJECT_RULES.md), and
[docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this work is:

- engineering rules / current focus / status / constraints index;
- docs index;
- the follow-up blocker review v1 §6 (§8.F authority gate, the reviewed
  Options F1 / F2 / F3 menu, the contract-intent reasoning, and the
  recommended decision);
- the prior trial blocker review and the §8.A / §8.B / §8.C / §8.D /
  §8.E / §8.G execution logs (so §8.F builds on the contract-clean
  fresh-sample pipeline that §8.A / §8.B / §8.C / §8.D / §8.E / §8.G
  established);
- the matrix_script frozen contracts
  (`task_entry_contract_v1` with §8.A and §8.C addenda — the contract
  being tightened by this change; `slot_pack_contract_v1` §"Forbidden"
  no-body-embedding rule that pins the contract intent for opaque
  refs; `packet_v1` for the `body_ref` template invariant);
- the `result_packet_binding_artifact_lookup_contract_v1` (the Plan B
  B4 artifact-lookup boundary that Option F2 / F3 would have to bridge
  but which §8.F leaves to Plan E);
- read-only inspection of
  [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py)
  (the §8.A guard at `_validate_source_script_ref_shape` — the only
  Python file edited by this change),
  [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html)
  (the operator-facing input — the only template edited by this
  change),
  [gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py)
  (the §8.A regression suite that this change extends).

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

This change implements **only** §8.F from the Matrix Script follow-up
blocker review v1, applying the explicit Chief-Architect decision that
Option F1 is the in-wave correction. The change tightens the
`source_script_ref` accepted-scheme set on the §8.A entry-form guard
from `{content, task, asset, ref, s3, gs, https, http}` to
`{content, task, asset, ref}`, mirrors the tightening on the
operator-facing HTML input pattern, additively amends the
`task_entry_contract_v1` source-script-ref-shape addendum to reflect
the tightening and pin the operator transitional
`content://matrix-script/source/<token>` convention, and extends the
§8.A regression suite with new cases that prove the dropped schemes
are now rejected and that the transitional convention passes.

Items §8.A (initial guard), §8.B (panel-dispatch confirmation), §8.C
(Phase B deterministic authoring), §8.D (operator brief), §8.E
(workbench shell suppression), and §8.G (Phase B panel render
correctness) are out of scope and remain as already accepted. Item §8.H
(operator brief re-correction) is the natural successor and is OUT of
scope for this PR — §8.H follows once §8.E / §8.F / §8.G are all
landed.

### 2.1 Path decision

The follow-up blocker review §6 offered three options:

- **Option F1** — Tighten the scheme set, accept the operator pain. Drop
  `https` / `http` (and possibly `s3` / `gs`) from the accepted set;
  brief operators on the transitional convention.
- **Option F2** — Keep the scheme set, add an in-product minting flow.
- **Option F3** — Accept the slippage; document it.

This change lands **Option F1**, with the broadest interpretation: drop
`https`, `http`, `s3`, and `gs` (all four). Rationale, with citations:

1. The contract intent is "opaque ref handle" — i.e. dereferenceable
   inside the product. Per follow-up review §6 ("Contract intent"):
   `content` / `task` / `asset` / `ref` are **opaque-by-construction**
   inside the product; `s3` / `gs` are "opaque by convention" but the
   entry surface has no enforceable mechanism to distinguish a
   product-owned bucket from a public / arbitrary one; `https` / `http`
   are not opaque in the contract sense.
2. The §8.C `body_ref` template only emits `content://...` URIs. No
   downstream consumer of `source_script_ref` distinguishes `s3://` or
   `gs://` from `https://` today, so dropping all four keeps the
   accepted set aligned with the only schemes the product actually
   mints under Plan A. Plan E (Option F2) is the proper resolution
   path for any operator-facing minting service.
3. F2 is explicitly out of scope for this wave — review §6 names it as
   "squarely in Plan C C1 scope, which is gated to Plan E. Implementing
   it during the Plan A trial correction wave would expand wave scope
   beyond the blocker-review charter and arguably violate the 'do not
   enter Capability Expansion' red line."
4. F3 ("Accept the slippage; document it") is rejected by the review
   itself: "Best for: nobody — this is the do-nothing option that lets
   the observed defect become permanent."
5. The contract addendum's narrowing-permitted clause from §8.A
   ("Narrowing it is permitted only if no live trial sample relies on
   the removed scheme") is satisfied: per the follow-up review §1 / §9
   the old pre-§8.A invalid sample is not reusable, and no live
   post-§8.A sample has been authorized to use `https` / `http` / `s3`
   / `gs` (the pre-correction publisher-URL sample
   `task_id=415ea379ebc6` is invalid evidence per follow-up review §9
   anyway).

### 2.2 What this change adds

- **Server-side guard tightening** at
  [gateway/app/services/matrix_script/create_entry.py:57-66](../../gateway/app/services/matrix_script/create_entry.py:57)
  — the `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` tuple is now exactly
  `("content", "task", "asset", "ref")`. The
  `_SOURCE_SCRIPT_REF_URI_PATTERN` regex is regenerated automatically
  from the tightened tuple. The module docstring on the constant is
  updated to explain the §8.F tightening reasoning. No other code
  branches change — the existing whitespace / single-line / max-length
  / scheme-not-recognised / bare-token rejection branches all stand
  verbatim.
- **Operator-facing input tightening** at
  [gateway/app/templates/matrix_script_new.html:160-174](../../gateway/app/templates/matrix_script_new.html:160)
  — the `pattern` regex is updated from
  `^(?:(?:content|task|asset|ref|s3|gs|https?)://\S+|...)$` to
  `^(?:(?:content|task|asset|ref)://\S+|...)$` so the browser-side
  hint mirrors the server-side guard. The placeholder is updated to
  `content://matrix-script/source/<your-token>` to point operators at
  the transitional convention. The helper text is rewritten to:
  - name the four accepted schemes explicitly;
  - explicitly call out external web URLs (`https://` / `http://`)
    and bucket schemes (`s3://` / `gs://`) as **not accepted** ("不接受")
    with the reason "they are not product-internal opaque refs";
  - retain the "do not paste body text" rule from §8.A;
  - add a second hint paragraph documenting the transitional convention
    `content://matrix-script/source/<token>` with the explicit
    statement that `<token>` is operator-chosen and that the product
    does not dereference or read back `<token>`.
- **Contract addendum extension** at
  [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md)
  §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F
  on 2026-05-03)" — the heading is renamed to acknowledge the §8.F
  tightening; the closed scheme set in the addendum body is updated
  to the four opaque-by-construction schemes; four new sub-sections
  are appended:
  - §"Opaque-by-construction discipline (§8.F tightening, 2026-05-03)"
    — declares the original pre-§8.F scheme set, names the four
    dropped schemes, names the live trigger case (`https://news.qq.com/...`),
    explains the contract-intent reasoning for dropping each scheme
    family, and pins the four retained schemes as opaque-by-construction;
  - §"Operator transitional convention (Plan A trial wave only)" —
    pins the canonical operator-facing form
    `content://matrix-script/source/<token>`, declares it operator-
    discipline-only (not a product feature), states that the product
    treats `<token>` as fully opaque (never dereferences, never
    validates uniqueness, never reads back content), and pins the
    forward-compatibility / removal path for Plan E (Option F2);
  - §"Why this is contract-tightening AND a usability adjustment" —
    documents the pre-§8.F slippage and the contract-intent restoration;
  - §"Out of scope for §8.F" — explicitly enumerates what the
    addendum does NOT do (no minting endpoint, no asset-library
    expansion, no §8.D operator brief refresh, no Plan B B4
    URL-shaped-ref behavior, no `body_ref` template change, etc.).
- **Regression-suite extension** at
  [gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py):
  - new parametrized rejection case
    `test_section_f_dropped_schemes_are_now_rejected` covering 5 refs
    (the live-trigger publisher URL, an internal-doc HTTPS URL, a
    legacy HTTP URL, an `s3://` bucket, a `gs://` bucket) — each must
    raise `HTTPException(400)` with the same `"scheme is not recognised"`
    message branch the original §8.A guard used for foreign schemes;
  - new positive case
    `test_section_f_accepted_scheme_set_is_exactly_four_opaque_schemes`
    asserting the constant tuple is exactly the four-scheme set and
    that none of `https` / `http` / `s3` / `gs` appear in it;
  - new positive case
    `test_section_f_transitional_convention_passes_guard` asserting
    the canonical operator-facing form passes the guard with no new
    code branch (it is one instance of the existing `content` opaque-
    scheme path);
  - existing `test_contract_shaped_refs_are_accepted` parametrize
    list pruned to drop the four dropped-scheme entries (`https://...`,
    `http://...`, `s3://...`, `gs://...`); the seven retained refs all
    still pass;
  - existing `test_accepted_scheme_set_is_complete` updated docstring
    only — the assertion mechanism (round-trip every scheme in the
    constant) is unchanged and now covers four schemes instead of
    eight;
  - new template-wiring case
    `test_template_pattern_is_tightened_to_section_f_scheme_set`
    asserting the operator-facing HTML pattern's URI alternation is
    exactly `(?:content|task|asset|ref)://` and that the dropped
    schemes (`s3`, `gs`, `https?`, `http?`) do not appear in the
    pattern;
  - new template-wiring case
    `test_template_helper_text_documents_transitional_convention`
    asserting the helper text names the four accepted scheme prefixes,
    explicitly calls out the rejected scheme families, and embeds the
    transitional `content://matrix-script/source/<token>` form;
  - existing module docstring expanded to explain the §8.F authority
    chain alongside §8.A.
- This execution log.
- Standing repo guidance writeback to `ENGINEERING_STATUS.md`,
  `CURRENT_ENGINEERING_FOCUS.md`, the Matrix Script
  first-production-line log, and the ApolloVeo 2.0 evidence index.

### 2.3 What this change does NOT add (out of §8.F)

- **No in-product minting / lookup service.** Option F2 would have
  added `POST /assets/mint?kind=script_source` (or equivalent); §8.F
  rejects F2 in this wave per the explicit decision. No new endpoint,
  no new operator-facing service, no new schema, no new packet field.
  Plan E is the resolution path.
- **No asset-library service expansion.** Plan C C1 (asset library) is
  contract-frozen and gated to Plan E. §8.F does not touch it.
- **No §8.D operator brief refresh.** The Plan A trial brief at
  `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` still cites the
  pre-§8.F scheme set in §3.2 / §6.2; refreshing those rows is §8.H's
  scope. §8.F intentionally leaves the brief unchanged so §8.H can
  re-align it in one pass alongside the §8.E / §8.G updates.
- **No `body_ref` template change.** The §8.C planner's body-ref
  template `content://matrix-script/{task_id}/slot/{slot_id}` is
  unchanged and remains opaque-by-construction (it uses the `content`
  scheme that §8.F retains).
- **No Plan B B4 (`result_packet_binding`) change.** The
  artifact-lookup contract has no defined behavior for URL-shaped
  refs; under §8.F's tightened scheme set the contract no longer needs
  to define one (URL-shaped refs cannot enter the system). Plan E
  retains the freedom to define artifact-lookup behavior for
  `content://` / `task://` / `asset://` / `ref://` schemes.
- **No `g_lang` token alphabet pinning.**
- **No widening of the closed scheme set.** A future widening (e.g. a
  Plan E `content-bundle://`) would require a contract re-version, not
  an addendum.
- **No second production line onboarding.**
- **No router edit.** `tasks.py` is not touched.
- **No Phase B / Phase C / Phase D code change.**
- **No projector change.**
- **No schema / sample / packet re-version.**
- **No provider / model / vendor / engine controls.**
- **No §8.E shell-suppression change.** §8.E is independent and
  already landed; the §8.F change touches only the entry-form guard
  and operator-facing input, not the workbench shell.
- **No §8.G axes-table change.** §8.G is independent and already
  landed; the §8.F change is upstream of the workbench panel.
- **No CSS-only operator hint.** The transitional convention is
  documented in the helper text body, not via CSS — the test surface
  asserts text presence.
- **No backwards-compatibility shim.** Tasks created under the
  pre-§8.F scheme set (if any) are not migrated; the §8.F authority
  is binding for new POSTs only. The follow-up review §9 / §1
  reaffirms the old pre-§8.A sample is invalid evidence anyway.

## 3. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| Tighten `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` from 8 to 4 entries (`content`, `task`, `asset`, `ref`); update inline docstring comments to explain the §8.F tightening. The `_SOURCE_SCRIPT_REF_URI_PATTERN` regex is regenerated automatically from the tuple. No new code branches; existing whitespace / single-line / max-length / scheme-not-recognised / bare-token branches all stand verbatim. | [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py) | EDIT |
| Tighten the operator-facing HTML `pattern` regex to `^(?:(?:content|task|asset|ref)://\S+|[A-Za-z0-9][A-Za-z0-9._\-:/]{3,})$`; update the placeholder to `content://matrix-script/source/<your-token>`; rewrite the helper text to name the four accepted schemes, explicitly reject external web schemes and bucket schemes ("不接受"), retain the no-body-paste rule, and add a second hint paragraph pinning the transitional `content://matrix-script/source/<token>` operator-discipline convention. | [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) | EDIT |
| Rename §"Source script ref shape (addendum, 2026-05-02)" to §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)"; update the closed scheme set in the body to four entries; append four new sub-sections — §"Opaque-by-construction discipline (§8.F tightening, 2026-05-03)", §"Operator transitional convention (Plan A trial wave only)", §"Why this is contract-tightening AND a usability adjustment", §"Out of scope for §8.F". The §"Phase B deterministic authoring (addendum, 2026-05-03)" sub-tree is unchanged. | [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) | EDIT |
| Update module docstring to cite both §8.A and §8.F authority. Add 5 new test cases: `test_section_f_dropped_schemes_are_now_rejected[5 params]`, `test_section_f_accepted_scheme_set_is_exactly_four_opaque_schemes`, `test_section_f_transitional_convention_passes_guard`, `test_template_pattern_is_tightened_to_section_f_scheme_set`, `test_template_helper_text_documents_transitional_convention`. Prune existing `test_contract_shaped_refs_are_accepted` parametrize list to drop the four dropped-scheme entries; the seven retained entries are unchanged. Update `test_accepted_scheme_set_is_complete` docstring only. Update `test_template_replaces_textarea_with_pattern_constrained_input` placeholder assertion to be prefix-only (the placeholder now ends in `<your-token>` not `001`). | [gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py) | EDIT |
| This execution log. | [docs/execution/MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

**File-size budget.** `create_entry.py` shrinks by 4 entries inside an
existing tuple (no line-count delta of significance). The HTML template
gains a few lines in the helper-text. The contract document grows by
~50 lines of additive sub-sections. The test module gains 5 new
cases (~80 lines) and prunes 4 lines from the parametrize list. No
router or service file gains business logic; no god-file growth; no
new line-specific logic in `tasks.py`, `task_view.py`, or
`hot_follow_api.py`.

## 4. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5),
matching the §8.A / §8.B / §8.C / §8.E / §8.G execution logs.
Worktree path:
`/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/unruffled-merkle-d9f22e`.
Branch: `claude/matrix-script-8f-opaque-ref-tightening`. Baseline commit:
`5be78f5` (post-§8.E, the immediately prior accepted state on `main`
after §8.E PR #89 merge). The old pre-§8.A invalid sample is **not**
used in any of the assertions below; the pre-§8.F live-trigger sample
`task_id=415ea379ebc6` (which submitted `https://news.qq.com/...`) is
referenced only as a prior-state observation and is invalid evidence
per the follow-up review §9.

### 4.1 Targeted suite — §8.A + §8.F shape guard

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py -v
```

Result: **28 passed, 0 failed.** The original 23 §8.A cases stay green
(adjusted: the §8.A `test_contract_shaped_refs_are_accepted`
parametrize list is now 7 entries instead of 11; the §8.A
`test_accepted_scheme_set_is_complete` now iterates 4 schemes instead
of 8). 5 new §8.F cases pass:

- `test_section_f_dropped_schemes_are_now_rejected[https://news.qq.com/...]`
- `test_section_f_dropped_schemes_are_now_rejected[https://docs.internal...]`
- `test_section_f_dropped_schemes_are_now_rejected[http://legacy.internal/...]`
- `test_section_f_dropped_schemes_are_now_rejected[s3://bucket/...]`
- `test_section_f_dropped_schemes_are_now_rejected[gs://bucket/...]`
- `test_section_f_accepted_scheme_set_is_exactly_four_opaque_schemes`
- `test_section_f_transitional_convention_passes_guard`
- `test_template_pattern_is_tightened_to_section_f_scheme_set`
- `test_template_helper_text_documents_transitional_convention`

### 4.2 Surrounding suites — no regression

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py \
  gateway/app/services/tests/test_matrix_script_workbench_dispatch.py \
  gateway/app/services/tests/test_new_tasks_surface.py \
  gateway/app/services/tests/test_task_router_presenters.py \
  tests/contracts/matrix_script/ \
  tests/contracts/operator_visible_surfaces/ \
  tests/guardrails/ -q
```

Result: **200 passed, 0 failed.** Up from §8.E's 195 baseline because
§8.F adds 5 new cases to the §8.A suite (28 - 23 = 5). §8.B's 4 cases,
§8.C's planner-unit 27 + end-to-end (now 13 = 11 prior + §8.G + §8.E),
`test_workbench_variation_phase_b`, the operator-visible-surface
contracts, and guardrails all stay green.

### 4.3 Live HTTP-boundary evidence (captured)

A direct end-to-end run against the live FastAPI app (in-memory repo)
exercises the three load-bearing branches:

```
=== §8.F live HTTP boundary check ===

--- Reject: publisher article URL (the live trigger case) ---
  POST /tasks/matrix-script/new with
    source_script_ref=https://news.qq.com/rain/a/20260502A05LYM00
  → POST status: 400  (expected 400)
  → body contains 'scheme is not recognised': True

--- Reject: s3:// bucket ---
  POST /tasks/matrix-script/new with
    source_script_ref=s3://bucket/source/001.json
  → POST status: 400  (expected 400)

--- Accept: transitional convention content://matrix-script/source/<token> ---
  POST /tasks/matrix-script/new with
    source_script_ref=content://matrix-script/source/op-token-001
  → POST status: 303  (expected 303)
  → persisted source_url: content://matrix-script/source/op-token-001
  → persisted entry.source_script_ref: content://matrix-script/source/op-token-001
```

This is the load-bearing operator-visible evidence: the live trigger
case from the follow-up review §3 (`https://news.qq.com/rain/a/...`)
is now rejected at the entry-form HTTP boundary; an `s3://` bucket
scheme is also rejected (Option F1's broader interpretation); the
transitional convention `content://matrix-script/source/<token>`
passes the guard and persists with the operator-supplied opaque
handle intact (no rewriting, no `<token>` interpretation).

### 4.4 Manual proof of the §8.F validation requirements

Mapping the §8.F authority decision and the review §6 acceptance items
to evidence above:

| Required validation | Evidence |
| ------------------- | -------- |
| Tighten `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` to enforce opaque-ref discipline. | §3 — tuple shrunk from 8 to 4 entries; §4.1 `test_section_f_accepted_scheme_set_is_exactly_four_opaque_schemes`; §4.3 live publisher-URL rejection. |
| Update §8.A addendum accordingly. | §3 — header rename + body update + four new sub-sections at `task_entry_contract_v1.md`. |
| Prepare operator-facing transitional convention `content://matrix-script/source/<token>`. | §3 — addendum §"Operator transitional convention (Plan A trial wave only)" pins the form; helper-text update at `matrix_script_new.html` documents it for operators; §4.1 `test_template_helper_text_documents_transitional_convention`; §4.3 live `content://matrix-script/source/op-token-001` accepted. |
| Option F1 only — no F2 minting service, no F3 slippage acceptance. | §3 — no new endpoint added, no asset-library expansion; addendum §"Out of scope for §8.F" enumerates F2 / F3 explicitly as out of wave. §2.1 records the path decision with citation to review §6. |
| Reject the live trigger case (`https://news.qq.com/...`). | §4.1 `test_section_f_dropped_schemes_are_now_rejected[https://news.qq.com/...]`; §4.3 live POST returns 400 with the expected error branch. |
| §8.A initial guard not regressed (body-text paste, whitespace, max-length, foreign scheme, bare-token min length, required-field). | §4.1 — the original 23 §8.A cases all stay green; the only adjustment is the parametrize-list pruning of the four dropped-scheme entries from `test_contract_shaped_refs_are_accepted`. |
| §8.B / §8.C / §8.D / §8.E / §8.G not retracted. | §4.2 — 200/200 cases pass across the surrounding suites; no §8.B dispatch / §8.C planner / §8.E shell-suppression / §8.G axes-table assertion is affected. |
| Old invalid pre-§8.A sample remains invalid evidence. | Re-asserted by the §8.A guard and the addendum's narrowing-permitted clause; no §8.F assertion uses the old sample. The pre-§8.F live-trigger sample `task_id=415ea379ebc6` is referenced only as prior-state observation. |

## 5. Contract Alignment Check

- `task_entry_contract_v1`: respected, **additively amended**. The
  source-script-ref-shape addendum's narrowing-permitted clause
  ("Narrowing it is permitted only if no live trial sample relies on
  the removed scheme") is satisfied — see §2.1 Point 5. Four new
  sub-sections are appended; the §"Phase B deterministic authoring
  (addendum, 2026-05-03)" sub-tree is unchanged. The closed entry-field
  set, the line-truth/operator-hint rule, the deferral table, and the
  forbidden-field list are unchanged.
- `slot_pack_contract_v1` §"Forbidden": respected, **unchanged**. The
  no-body-embedding rule that pinned the contract intent for opaque
  refs is what §8.F restores by removing the URL allowance. The §8.C
  `body_ref` template is unchanged.
- `variation_matrix_contract_v1`: respected, **unchanged**. No axes /
  cells / kind-set change.
- `packet_v1`: respected, **unchanged**. No `status` / `ready` /
  `done` / `phase` / `current_attempt` / `delivery_ready` /
  `final_ready` / `publishable` field added at any scope. Validator
  R3 / R5 token sets unchanged.
- `workbench_panel_dispatch_contract_v1`: respected, **unchanged**.
  The §8.E shared-shell-neutrality addendum stands verbatim. §8.F is
  upstream of the workbench mount.
- `workbench_variation_surface_contract_v1`: respected, **unchanged**.
- `result_packet_binding_artifact_lookup_contract_v1`: respected,
  **unchanged**. With `https` / `http` / `s3` / `gs` removed from the
  accepted set, the artifact-lookup contract has no need to define
  URL-shaped-ref behavior — Plan E retains full freedom.
- `tasks.py` did not receive new line-specific logic. The router still
  dispatches via the registry + the projection bundle. No router edit.
- No new vendor / model / provider / engine identifier was introduced.
- No second source of task or state truth was introduced. The guard is
  unchanged in mechanism; only the accepted-set tuple shrinks.
- No backwards-compatibility shim — tasks created under the pre-§8.F
  scheme set (none authorized as live evidence) are not migrated.

## 6. Final Gate

- **§8.F: PASS.** The accepted-scheme set is tightened from 8 to 4
  entries (`content`, `task`, `asset`, `ref`); the §8.A contract
  addendum carries the §8.F tightening sub-section, the operator
  transitional convention, the contract-intent reasoning, and the
  out-of-scope enumeration; the operator-facing input pattern and
  helper text mirror the tightened set; 5 new regression cases prove
  the dropped schemes are now rejected, the constant tuple is exactly
  the four-scheme set, the transitional convention passes, the HTML
  pattern matches the server-side guard, and the helper text documents
  the convention; live HTTP boundary confirms the publisher URL
  rejection (§3 live trigger case) and the transitional convention
  acceptance.
- **Option F1 only: YES.** No F2 minting endpoint added; no F3
  slippage acceptance documented; no asset-library expansion; no
  Plan E gated work entered.
- **Live publisher URL rejected: YES.** `https://news.qq.com/rain/a/20260502A05LYM00`
  → HTTP 400 with `"scheme is not recognised"` per §4.3.
- **Transitional convention accepted: YES.** `content://matrix-script/source/op-token-001`
  → HTTP 303, persisted with the operator-supplied handle intact per
  §4.3.
- **§8.A / §8.B / §8.C / §8.D / §8.E / §8.G: not retracted.** §8.F is
  additive only; the §8.A guard mechanism stands verbatim; the §8.A
  contract addendum is extended (header renamed; body updated; four
  new sub-sections appended); all prior gates stay PASS.
- **Old invalid pre-§8.A sample reusable: NO.**
- **Pre-§8.F live-trigger sample (`task_id=415ea379ebc6`) reusable:
  NO** — it submitted a publisher URL that the §8.F-tightened guard
  now rejects; per follow-up review §9 it remains invalid evidence.
- **Ready for §8.H: YES.** §8.E + §8.G + §8.F now all PASS; the
  natural successor §8.H (operator brief re-correction at
  `OPERATIONS_TRIAL_READINESS_PLAN_v1.md` §0.1 / §3.2 / §6.2 / §7.1
  to reflect the §8.E shell suppression, the §8.F tightened scheme
  set, and the transitional convention) is unblocked.
- **Matrix Script live-run: still BLOCKED.** Per the user instruction:
  "Matrix Script live-run remains BLOCKED until §8.H completes." §8.F
  alone does not unblock live-run; only §8.H finishes the chain.
- **Plan E pre-conditions still gated: YES.** Option F2 (minting
  service) remains a Plan E item with the contract addendum's
  forward-compatibility statement intact.

## 7. Hard Red Lines (re-stated, observed)

This work observes every red line restated by the follow-up blocker
review §9 and the prior wave authority:

- F2 minting service: not implemented in this wave. Plan E retains
  the resolution.
- F3 slippage acceptance: explicitly rejected — the contract intent
  is restored, not preserved-as-observed.
- Asset Library / promote (Plan C C1–C3): not entered.
- §8.A / §8.B / §8.C / §8.D / §8.E / §8.G: not reopened. §8.A's guard
  mechanism is unchanged; only the accepted-set tuple shrinks.
- §8.D operator brief: not edited (§8.H is the successor; §8.F leaves
  the brief at its post-§8.D state so §8.H can re-align it in one
  pass).
- `body_ref` template: not changed (§8.C's `content://matrix-script/{task_id}/slot/{slot_id}`
  is unchanged and remains opaque-by-construction).
- Hot Follow scope: not reopened. Hot Follow's
  `hot_follow_workbench.html` and entry routes are unaffected.
- Platform Runtime Assembly / Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench redesign: no.
- Per-line workbench template files for matrix_script / digital_anchor:
  not added.
- CSS-only operator hint: not used. The transitional convention is
  documented in the helper text body, asserted by the regression
  test.
- Backwards-compatibility shim for tasks created under the pre-§8.F
  scheme set: not added (no live evidence relies on the removed
  schemes; the narrowing-permitted clause from the §8.A addendum is
  satisfied).
- `g_lang` token alphabet: not pinned in this PR.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.
- `tasks.py` / `task_view.py` / `hot_follow_api.py`: untouched.
- Old invalid sample: not used as evidence.
- Plan E gated items (B4 `result_packet_binding`, D1 `publish_readiness`,
  D2 `final_provenance`, D3 panel-dispatch-as-contract-object,
  D4 advisory producer): not implemented.
- Promote Delivery Center beyond inspect-only for Matrix Script in
  this wave: not done.
- §8.H operator brief re-correction: not done in this PR (the natural
  successor; takes §8.E + §8.F + §8.G in one pass).
- Matrix Script live-run unblock: not done. Per the user instruction
  the live-run remains BLOCKED until §8.H completes.

End of v1.
