# Matrix Script §8.A Ref-Shape Guard — Execution Log v1

Date: 2026-05-02
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, item §8.A)
Status: implementation green; ready for signoff
Authority:
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) §8.A
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md)
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with addendum landed in this change)
- [docs/contracts/matrix_script/slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is no top-level `CLAUDE.md` in this repository. The equivalent
authority chain followed for this work:

- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md)
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)
- [ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md)
- [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md)
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md)
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md)
- Matrix Script entry / slot-pack contracts under `docs/contracts/matrix_script/`.
- Read-only inspection of `gateway/app/services/matrix_script/create_entry.py`,
  `gateway/app/templates/matrix_script_new.html`,
  `gateway/app/routers/tasks.py:611-650`,
  `gateway/app/services/tests/test_new_tasks_surface.py`.

## 2. Scope (binding)

This change implements **only** §8.A from the Matrix Script trial blocker
review: a server-side ref-shape guard for `source_script_ref` and the
operator-facing input semantics that mirror it. Items §8.B (panel-dispatch
trace), §8.C (Phase B authoring or fixture-LS-delta policy), and §8.D
(operator brief correction) are out of scope and remain blocked per the
review's gate recommendation.

What this change adds:

- A line-scoped guard in
  [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py)
  that rejects any `source_script_ref` value carrying script body text or
  any other non-reference payload, before
  `build_matrix_script_task_payload` ever runs.
- A matching client-side input shape on the formal create-entry surface
  [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html)
  (text input with `pattern` and `maxlength`, plus operator-facing helper
  text that explicitly forbids pasting body text).
- A contract addendum
  ([docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md)
  §"Source script ref shape (addendum, 2026-05-02)") that pins the closed
  scheme set used by the guard.
- A focused test suite
  [gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py)
  proving the guard at the service boundary, the HTTP boundary, and the
  template-shape boundary.

What this change does NOT add (out of §8.A):

- no Phase B authoring capability; no LS1 / LS2 delta producer (§8.C).
- no panel-dispatch route trace or assertion (§8.B).
- no operator brief correction
  ([docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md))
  (§8.D).
- no relaxation, widening, or reshaping of the `source_script_ref`
  semantics in the contract — the closed scheme set is exhaustive at v1.
- no change to packet truth, schema, sample, the workbench projector, or
  the delivery projector.
- no Digital Anchor change. The Digital Anchor entry contract carries the
  same `source_script_ref` field but the formal create-entry route and
  payload-builder for Digital Anchor are still contract-frozen / not
  implemented per Plan B B1 / B2; widening this guard to Digital Anchor is
  the responsibility of that wave.
- no Hot Follow change.
- no Board / Delivery / Workbench shape change.
- no provider / model / vendor / engine controls.

## 3. Closed Accepted Shape

The contract addendum at
[docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md)
§"Source script ref shape (addendum, 2026-05-02)" pins the accepted shapes:

1. URI with one of the closed schemes: `content`, `task`, `asset`, `ref`,
   `s3`, `gs`, `https`, `http`. Format `<scheme>://<non-whitespace>`.
2. Bare token id matching `^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$`. No
   embedded `://` separator (so an unrecognised URI scheme can never
   silently pass as a token).

Both shapes are additionally constrained by the same envelope rules:

- single line (no `\n` or `\r`);
- no whitespace anywhere in the value;
- length ≤ 512 characters.

On any rejection the entry surface raises the existing entry-validation
error type (`fastapi.HTTPException(status_code=400, detail=...)`) with a
field-named, constraint-named message. This matches the pre-existing
pattern used by the closed required-set check, the language enum check,
and the `variation_target_count` range check in the same builder.

## 4. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| Add `_validate_source_script_ref_shape`, accepted-scheme constants, regex compilation; wire guard before payload-builder. | [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py) | EDIT |
| Replace free-form `<textarea>` with constrained `<input type="text">` (`pattern` mirrors the server guard, `maxlength=512`); rewrite placeholder + helper text to forbid body paste. | [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) | EDIT |
| Add §"Source script ref shape (addendum, 2026-05-02)" pinning the closed scheme set, the bounded-length / single-line / no-whitespace envelope rules, and the rejection-error type. | [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) | EDIT |
| New focused suite for the guard. Covers prose rejection (multi-line, single-line with whitespace, overlong, unrecognised scheme, short token), accepted-scheme parametrised pass list (covers every documented scheme + bare token ids), payload-builder still constructs the formal Matrix Script payload, and the HTTP boundary (POST 400 on prose body, POST 303 on contract-shaped ref). | [gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py) | NEW |
| This execution log. | [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md) | EDIT |

No file in this change widens scope beyond §8.A. No router / service caps
were exceeded; the only Python file edited adds 60 lines net (well under
the §1 service file thresholds). No new line-specific logic enters
`tasks.py`.

## 5. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5).
Worktree path:
`/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/zen-chandrasekhar-caa7c9`.
Branch: `claude/zen-chandrasekhar-caa7c9`. Baseline commit: `b3ca888`.

### 5.1 New §8.A guard suite

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py -v
```

Result: **23 passed, 0 failed.** Cases:

- Rejection branches (6):
  `test_multi_line_prose_body_is_rejected`,
  `test_prose_body_with_whitespace_is_rejected_even_when_single_line`,
  `test_overlong_ref_is_rejected`,
  `test_unrecognised_scheme_is_rejected`,
  `test_empty_string_is_still_rejected_as_required`,
  `test_short_token_below_minimum_length_is_rejected`.
- Accepted branches (12 parametrised + 1 sweep):
  `test_contract_shaped_refs_are_accepted[...]` for every documented
  shape (`content://`, `task://`, `asset://`, `ref://`, `https://`,
  `http://`, `s3://`, `gs://`, plus three bare-token examples), plus
  `test_accepted_scheme_set_is_complete` walking
  `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` directly.
- Payload-builder remains correct (1):
  `test_payload_builder_still_constructs_formal_packet_for_valid_ref`
  asserts `kind/category_key/platform=matrix_script`,
  `source_url=content://...`, `config.entry.source_script_ref=content://...`,
  and the `{matrix_script_variation_matrix, matrix_script_slot_pack}`
  line-specific ref pair on both `packet.line_specific_refs[]` and the
  legacy mirror.
- HTTP boundary (2):
  `test_post_handler_rejects_prose_body_with_400` confirms `repo.create`
  is never invoked when prose is posted; `test_post_handler_accepts_contract_shaped_ref_and_redirects`
  confirms the 303 redirect to `/tasks/{task_id}?created=matrix_script` is
  unchanged for a contract-shaped ref.
- Template wiring (2): textarea is replaced; `pattern` / `maxlength`
  attributes are present; helper text contains 不要 / 脚本正文 (do not
  paste body).

### 5.2 Surrounding suites — no regression

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py \
  gateway/app/services/tests/test_new_tasks_surface.py \
  tests/contracts/matrix_script/ \
  tests/contracts/operator_visible_surfaces/ \
  tests/guardrails/ -v
```

Result: **122 passed, 0 failed.** Includes the pre-existing
`test_matrix_script_form_post_creates_task_and_redirects_to_workbench`
which already used a contract-shaped ref (`content://matrix-script/source/001`)
— it still passes, confirming the guard is additive rather than
behavior-changing for legal inputs.

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest tests/guardrails/ tests/contracts/ -q
```

Result: **178 passed, 0 failed.**

### 5.3 Pre-existing environment limitation

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest gateway/app/services/tests/ -q
```

Result: **324 passed, 1 failed** —
`gateway/app/services/tests/test_task_repository_file.py::test_op_download_proxy_uses_attachment_redirect_for_final_video`
fails with HTTP 500 vs expected 302. This failure reproduces on the
worktree baseline (`b3ca888`, the §8.A starting commit) without any of
this change's edits applied (verified by `git stash` round-trip). It is
unrelated to the Matrix Script entry surface and is recorded here as an
environment limitation per `ENGINEERING_RULES.md` §10 ("distinguish code
regressions from environment limitations").

### 5.4 Manual proof of the four required validations

The §8.A "Validation" requirements from the review brief, mapped to
evidence above:

| Required validation | Evidence |
| ------------------- | -------- |
| Prose body input is rejected. | `test_multi_line_prose_body_is_rejected`, `test_prose_body_with_whitespace_is_rejected_even_when_single_line`, `test_overlong_ref_is_rejected`, `test_post_handler_rejects_prose_body_with_400`. |
| Valid ref-shaped input is accepted. | `test_contract_shaped_refs_are_accepted[...]` (all 11 cases), `test_accepted_scheme_set_is_complete`, `test_post_handler_accepts_contract_shaped_ref_and_redirects`. |
| Create-entry path still builds the formal Matrix Script payload. | `test_payload_builder_still_constructs_formal_packet_for_valid_ref`, plus the unmodified `test_matrix_script_form_post_creates_task_and_redirects_to_workbench` (line-specific refs, redirect target, `kind=matrix_script` all preserved). |
| Smallest relevant tests added/updated. | New file `test_matrix_script_source_script_ref_shape.py` (23 cases). The pre-existing Phase A artefact tests at `tests/contracts/matrix_script/test_task_entry_phase_a.py` remain green; the addendum did not change the closed entry-field set, the line-truth classification, the mapping note, the forbidden-token list, or the out-of-wave scope rules, so those assertions still hold. |

## 6. Contract Alignment Check

- `task_entry_contract_v1` semantic on `source_script_ref`: now
  enforced. The opaque-ref requirement is no longer aspirational; the
  guard rejects body text at the entry surface before the payload-builder
  runs. This closes the §6 "Bypassed / violated contracts" item from the
  blocker review.
- `slot_pack_contract_v1:44` ("`body_ref` MUST be opaque … pack does not
  embed body text"): the upstream prerequisite is now hard. Any future
  Phase B authoring step on a sample created through the formal entry
  surface will see only opaque values for `source_script_ref` and
  therefore cannot transitively carry body text into `body_ref`. The
  staged violation flagged in the blocker review §6 is removed.
- `task_entry_contract_v1` closed entry-field set: unchanged. The
  addendum constrains the *shape* of an existing field; it does not add
  or rename any field. `tests/contracts/matrix_script/test_task_entry_phase_a.py`
  remains green.
- No new vendor / model / provider / engine identifier was introduced.
  Validator R3 / R5 forbidden-token sets are unchanged in the contract
  text.
- No second source of task or state truth was introduced. The guard runs
  inside the existing single payload-builder boundary.
- `tasks.py` did not receive new line-specific logic. The router still
  delegates to `build_matrix_script_entry`; the new guard lives entirely
  in the line service.

## 7. Final Gate

- **§8.A:** **PASS.** Server-side ref-shape guard, client-side input
  shape, contract addendum, and validation tests are all landed and
  green.
- **Current sample reusable:** **NO.** §8.A does not retrofit existing
  task rows. The blocker review §9 ruling stands: the sample with body
  text in `source_script_ref` is still invalid trial evidence; create a
  fresh sample after §8.A + §8.B + §8.C land.
- **Ready for §8.B:** **YES.** §8.B (panel-dispatch trace) does not
  depend on §8.A, but it does depend on a clean trial sample to inspect
  end-to-end. Now that the entry surface enforces opaque-ref semantics,
  a fresh sample created via `/tasks/matrix-script/new` will not carry
  body text into the packet, so a §8.B route trace can use it without
  the prior contamination. §8.C remains the binding precondition for
  Plan A trial evidence: without populated LS1 / LS2 deltas the
  workbench panel still has nothing to render.

## 8. Hard Red Lines (re-stated, observed)

This change observes every red line restated by the blocker review §9:

- Hot Follow scope: not reopened.
- Platform Runtime Assembly: not entered.
- Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake populated axes / cells / slots.
- `source_script_ref` contract: not weakened — the addendum *narrows*
  the accepted shape, never widens it.
- Delivery Center for Matrix Script: still inspect-only; no row was
  promoted, mutated, or written back.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.

End of v1.
