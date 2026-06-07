# Owner Summary — Matrix Script Slot Workflow v2 Gate Spec (2026-06-07)

Docs-only. One-page summary for the Owner. Not authority; the Gate Spec itself governs.

## What this is

The S4→S5 artifact: a docs-only **Gate Spec** that freezes the validated Slot Workflow
v2 product model into enforceable engineering rules. It implements nothing and opens no
runtime — the implementation gate stays **CLOSED until the §13 signoff merges**.

- Gate Spec: `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_GATE_SPEC_20260607.md`
- Index pointer added: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`

## Where it came from (Harness X trail)

- S0/S1 problem (B区 all-shot cards don't scale) → S2 Product Plan **#228 merged** →
  S3 static preview → S4 Operator Review **Round 1 = PASS WITH ISSUES (C-1, C-2)** →
  Preview-only revision → S4 **Round 2 = PASS** → **S5 (this Gate Spec)**.

## What it freezes

- **B区 v2 model** (rewritten): compact **Shot Queue** (one row/shot, scannable at 10+),
  one active **Current Shot Work Panel**, **Slot Editor**, **Assignment** as the only
  operator-mutable object, and a single **C区 batch-regenerate** entry (not per-card).
- **Honest slot classification:** `visual_material_slot` active now; `text_copy_slot` /
  `subtitle_slot` display-only (no edit control); `voiceover_slot` / `bgm_slot` future
  (status line only, **no button**).
- **Preserved:** V1/V2 semantics (V1 stays main until explicit confirm), delivery
  follows confirmed main only, `official_publish_ready=false`, no raw-backend leakage,
  A/C/D/E inherited from the Guided Workflow Gate Spec.
- **Acceptance:** A-V2-1..A-V2-18. **Slicing:** PR-1 (queue+panel) → PR-2 (slots+assignment)
  → PR-3 (batch+V1/V2 copy) → PR-4 (closeout). **Forbidden paths:** asset / hot_follow /
  digital_anchor / artifact_storage.py / schemas / docs/contracts / routers.

## Boundary

Docs-only. No runtime, no `gateway/**`, no real templates/services/tests, no
schema/contract, no Gate Spec to v1 changed (v2 is a successor for B区 only), no
implementation authorized, no deferred copy fix.

## Branch note (for the Owner) — MERGE-READY

The preview branch merged as **PR #229** (merge commit `8d7d6d3c`); `main` is synced.
This Gate Spec branch has been **rebased onto the new main** and now carries a single
gate-spec commit; its delta vs `main` is exactly three docs files (Gate Spec + Design
Authority Index pointer + this Owner Summary). The earlier stacking dependency is
resolved — the Gate Spec branch is now independently merge-ready against `main`.
Checks re-run after rebase: `diff --check` clean, docs-only clean, forbidden-path clean.

## Owner decision needed

- **Approve merge** of the Gate Spec (after / together with the preview branch), or
- **Request revision**, or
- **Authorize implementation** — NOT yet: implementation requires the §13 signoff
  (Architect + Reviewer) to be filled and merged first; that is a separate step.

The next allowed action after a §13 signoff merges is **PR-1 only** (compact Shot Queue
+ single active panel), an Owner-gated S5→S6 (L3) decision.
