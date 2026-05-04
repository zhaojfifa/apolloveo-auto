#!/usr/bin/env python3
"""Recovery PR-5 trial re-entry gate validation script (NOT-READY rewrite).

Re-asserts the documentation invariants of the rewritten PR-5 gate:
real operator trial is NOT READY, the two product-flow design
documents are line-specific execution authority, and the next
mandatory wave is the Operator Workflow Convergence Wave (Matrix
Script first, Digital Anchor second).

The script imports nothing from ``gateway.app``; it only opens
repository documentation files and checks for required tokens.

Usage::

    python3 scripts/recovery_pr5_trial_reentry_check.py

Exit codes:
- 0 — all invariants PASS.
- 1 — at least one invariant FAILed; failures listed on stderr.

Authority:
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md``
- ``docs/product/matrix_script_product_flow_v1.md``
- ``docs/product/digital_anchor_product_flow_v1.md``
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parent.parent

INVARIANTS: List[tuple[str, Path, List[str]]] = [
    (
        "PR-1 execution log MERGED with squash commit 4c317c4",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md",
        ["MERGED to `main`", "4c317c4"],
    ),
    (
        "PR-2 execution log MERGED with squash commit 4343bec",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md",
        ["MERGED to `main`", "4343bec"],
    ),
    (
        "PR-3 execution log MERGED with squash commit d53da0f",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md",
        ["MERGED to `main`", "d53da0f"],
    ),
    (
        "PR-4 execution log MERGED with squash commit 0549ee0 + reviewer-fail correction §9.1",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md",
        ["MERGED to `main`", "0549ee0", "9.1 Reviewer-Fail Correction Pass"],
    ),
    (
        "PR-5 trial re-entry gate document records the NOT-READY verdict + Product-Flow Enforcement Order",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md",
        [
            "## 0. Verdict",
            "Real operator trial is NOT READY",
            "Product-Flow Enforcement Order",
            "Operator Workflow Convergence Wave",
            "W7..W12",
            "Matrix Script first",
            "Digital Anchor second",
            "## 11. Signoff",
            "Stop conditions",
        ],
    ),
    (
        "PR-5 execution log records the NOT-READY rewrite",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md",
        [
            "rewritten from a GO gate to a NOT-READY decision",
            "Product-Flow Enforcement Order",
            "Operator Workflow Convergence Wave",
            "## 7. Forbidden-Scope Audit",
            "## 6. Acceptance Mapping",
        ],
    ),
    (
        "Matrix Script product-flow document is in repo with the line-specific execution authority preamble",
        REPO_ROOT / "docs/product/matrix_script_product_flow_v1.md",
        [
            "Matrix Script Product-Flow Design v1",
            "line-specific execution authority",
            "Recovery PR-5",
            "Operator-ready",
        ],
    ),
    (
        "Digital Anchor product-flow document is in repo with the line-specific execution authority preamble",
        REPO_ROOT / "docs/product/digital_anchor_product_flow_v1.md",
        [
            "Digital Anchor Product-Flow Design v1",
            "line-specific execution authority",
            "Recovery PR-5",
            "Operator-ready",
        ],
    ),
    (
        "Plan A trial brief carries the post-recovery §13 with NOT-READY verdict",
        REPO_ROOT / "docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md",
        [
            "## 13. Real Operator Trial Re-Entry — NOT READY",
            "Real operator trial readiness:** **NOT READY",
            "Operator Workflow Convergence Wave",
        ],
    ),
    (
        "Plan A coordinator write-up §13 records BLOCKED + Convergence Wave",
        REPO_ROOT / "docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md",
        [
            "## 13. Real Operator Trial Re-Entry — NOT READY",
            "BLOCKED until",
            "Operator Workflow Convergence Wave",
        ],
    ),
    (
        "CURRENT_ENGINEERING_FOCUS records NOT READY + the Convergence Wave",
        REPO_ROOT / "CURRENT_ENGINEERING_FOCUS.md",
        [
            "Operator Workflow Convergence Wave",
            "NOT READY",
            "Matrix Script first",
            "Digital Anchor second",
        ],
    ),
]


def main() -> int:
    failures: List[str] = []
    for description, path, tokens in INVARIANTS:
        if not path.exists():
            failures.append(f"FAIL [{description}]: file missing: {path.relative_to(REPO_ROOT)}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"FAIL [{description}]: cannot read {path.relative_to(REPO_ROOT)}: {exc}")
            continue
        for token in tokens:
            if token not in text:
                failures.append(
                    f"FAIL [{description}]: token not found in "
                    f"{path.relative_to(REPO_ROOT)}: {token!r}"
                )

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        print(
            f"\nrecovery_pr5_trial_reentry_check: {len(failures)} invariant(s) failed",
            file=sys.stderr,
        )
        return 1

    print(f"recovery_pr5_trial_reentry_check: {len(INVARIANTS)} invariant(s) PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
