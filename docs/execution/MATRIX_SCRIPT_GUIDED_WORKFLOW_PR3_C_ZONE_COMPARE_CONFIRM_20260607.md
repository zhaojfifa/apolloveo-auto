# Matrix Script Guided Operator Workflow — PR-3: C区 V1/V2 对比与确认区 (2026-06-07)

Engineering execution note. Evidence only — not implementation authority.
Gate: `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` §3.C,
slice PR-3 (§5). Owner authorized S5→S6 for **PR-3 only**. Builds on the merged
#211..#215 substrate + PR-1 (#220) + PR-2 (#223); reopens none of it.

## Scope (this PR)

C区 generate → compare → confirm pivot — presentation/projection only over the
already-existing regen lifecycle (#207 versioning / #212 consumed materials / #215
markers). No new producer, no endpoint/semantics change, no D/E re-layout.

## What changed

**View (`operator_workbench_view.py`)** — projection only:
- `candidate_changed_shots` — the shots that entered the V2 candidate (changed vs
  V1), derived from the existing per-shot `entered_v2_candidate` truth; only
  populated when a candidate exists. No new producer.

**Template (`task_workbench.html`)** — the existing `ms-regen-versioning` block only
(additive; every existing `data-role` preserved):
- A **named pivot title** `生成与对比：V1 / V2` (`ms-compare-confirm-pivot-title`).
- A **V1 reference paired with the V2 candidate** so the two are visually distinct:
  `ms-compare-current-main` (`data-preview-version="V1"`) +
  `ms-compare-candidate-label` (`data-preview-version="V2"`, always `候选`).
- A **changed-shots list** `哪些镜头发生了变化：` (`ms-compare-changed-shots`).
- The **explicit delivery-truth guard** `V2 未确认前不会影响交付。`
  (`ms-compare-delivery-guard`).
- The existing confirm / discard / continue actions (`ms-regen-confirm` /
  `ms-regen-discard` / `ms-regen-keep-tuning`) and the #212 consumed-material list
  are unchanged and preserved in place.

## Behavior preserved

No generation / storage / route / `artifact_storage.py` / schema / contract change.
The confirm/discard/regenerate endpoints and confirmed-main + delivery semantics are
unchanged — PR-3 only *surfaces* them. `delivery.delivery_candidate` still tracks
the confirmed main (V1) while a V2 candidate is pending. V1 is preserved until an
explicit confirm; a failed regeneration keeps V1 with no candidate. #212
byte-consumption projection unchanged. `official_publish_ready` stays **false**.
D区 / E区 untouched. No Hot Follow / Digital Anchor / Akool / provider touch.

## Acceptance (Gate Spec §6)

A-6 (V1/V2 separate + distinct, named pivot), A-7 (unconfirmed V2 doesn't affect
delivery), A-8 (confirm uses existing behavior — affordances preserved), A-13 (V1
preserved until confirm; failed regen keeps V1) — covered by
`test_matrix_script_pr3_c_zone_compare_confirm.py`. A-11 (no leakage), A-12 (#212
unchanged), A-14 (`official_publish_ready=false`) also asserted. A-15
(forbidden-path scan clean) verified by the change-set scan.

## Validation

`python3.11 -m py_compile gateway/app/main.py` OK. New focused suite **14 passed**.
Full Matrix Script suite **1887 passed** (1873 baseline + 14 new; 0 failures) — the
existing versioning tests stayed green (all `ms-regen-*` markers preserved).
`git diff --check` clean; forbidden-path scan clean.

## Boundary / not in this PR

PR-4..PR-6 are NOT authorized by this PR. D区 delivery move (PR-4), E区 fold (PR-5),
and Closeout (PR-6) remain future slices, each opening only after its predecessor
merges and the Owner approves. The pivot is *named and completed in place*; the full
A/B/C/D/E re-letter (moving 交付 after the pivot) is PR-4's job.
