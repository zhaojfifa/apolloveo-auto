# Matrix Script Guided Operator Workflow — PR-4: D区 交付候选与确认保护 (2026-06-07)

Engineering execution note. Evidence only — not implementation authority.
Gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` §3.D,
slice PR-4 (§5). Owner authorized S5→S6 for **PR-4 only**, plus a narrow
test-baseline migration (below). Builds on #211..#215 + PR-1/PR-2/PR-3; reopens none.

## Scope (this PR)

Primary D区 delivery surface — presentation/copy only:
- **R-DELIVERY-WORDING (§3.D / A-9):** the primary D区 shows `正式交付就绪：否` only;
  the raw `official_publish_ready=false` field is no longer surfaced there.
- **确认保护 (A-7) preserved/verified:** delivery follows the confirmed main only;
  an unconfirmed V2 is never the candidate (existing copy + behavior).
- **A-8 (existing behavior) verified:** when the confirmed main is V2, the delivery
  candidate reads `主视频 V2` — driven by the existing `current_main_version`, no
  endpoint change.

The delivery section already sits after the A区 confirm pivot (PR-3) positionally,
so no DOM move is needed; the title/section-letter is left unchanged to stay inside
the authorized R-DELIVERY-WORDING migration (renaming would touch other pinned
tests). The full A/B/C/D/E re-letter (folding 变体/脚本 into E区) is PR-5.

## What changed

**Template (`task_workbench.html`)** — one line in the primary delivery section
(`matrix-script-primary-delivery-entry`):
- `ms-primary-delivery-publish-ready`:
  `official_publish_ready=false；正式交付就绪：false。` → **`正式交付就绪：否。`**

**No view change** — reuses `delivery` + `current_main_version` (no new producer).

**Authorized test-baseline migration** (R-DELIVERY-WORDING only; the two assertions
that actually broke on the primary surface):
- `test_matrix_script_operator_process_observability.py` — primary `_c_zone` now
  asserts `正式交付就绪：否` + no raw field, plus the underlying truth
  `view["delivery"]["official_publish_ready"] is False`.
- `test_matrix_script_workbench_primary_operator_flow.py` — full-render assertion
  migrated to `正式交付就绪：否`.

The other two authorized files (`…flow_alignment`, `…phase2d`) were **not** edited:
their `official_publish_ready=false` / `正式交付就绪：false` assertions key on
*other* surfaces (the legacy A-J section at `:1891` / the A区 acceptance block),
which PR-4 does not touch — they still pass.

## Behavior preserved

No generation / storage / route / publish-route / `artifact_storage.py` / schema /
contract change. Delivery-candidate source, confirmed-main semantics, and the
publish-readiness producer are unchanged — `official_publish_ready` stays **false**
(only its primary-UI wording changed). #212 byte-consumption unchanged. E区
(变体/脚本) untouched. No Hot Follow / Digital Anchor / Akool / provider touch. The
legacy A-J `:1891` raw wording is intentionally left as-is (out of PR-4 scope).

## Acceptance (Gate Spec §6)

A-9 (R-DELIVERY-WORDING), A-7 (unconfirmed V2 not the candidate), A-8 (confirm →
delivery V2, existing behavior) — covered by `test_matrix_script_pr4_d_zone_delivery_wording.py`.
A-11 (no leakage), A-13 (V1 preserved), A-14 (`official_publish_ready=false`) also
asserted. A-15 (forbidden-path scan clean) verified by the change-set scan.

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. New focused suite **6 passed**.
Full Matrix Script suite **1893 passed** (1887 baseline + 6 new; 0 failures); the 2
migrated assertions are green. `git diff --check` clean; forbidden-path scan clean;
every changed file is inside the authorized set.

## Boundary / not in this PR

PR-5..PR-6 are NOT authorized. E区 fold (PR-5) and Closeout (PR-6) remain future
slices. The legacy A-J `:1891` cleanup is explicitly out of scope.
