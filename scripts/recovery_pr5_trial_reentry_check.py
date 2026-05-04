#!/usr/bin/env python3
"""Recovery PR-5 trial re-entry gate validation script.

Re-asserts the documentation invariants that the post-recovery real
operator trial gate depends on. The script imports nothing from
``gateway.app``; it only opens repository documentation files and
checks for required tokens.

Usage::

    python3 scripts/recovery_pr5_trial_reentry_check.py

Exit codes:
- 0 — all invariants PASS.
- 1 — at least one invariant FAILed; failures listed on stderr.

Authority:
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md``
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parent.parent

# Each invariant is a (description, file path, list of required tokens)
# tuple. The token check is substring-match; tokens are short and
# verbatim-stable so this resists template drift.
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
        "PR-5 trial re-entry gate document exists with §1 evidence map and §10 signoff block",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md",
        [
            "Recovery Wave Acceptance — Evidence Map",
            "Real-Trial Re-Entry Go/No-Go Checklist",
            "Post-Recovery Operator-Eligible Scope",
            "Post-Recovery Operator-Blocked Scope",
            "## 10. Signoff",
            "Stop conditions",
        ],
    ),
    (
        "PR-5 execution log exists with PR-5 forbidden-scope audit",
        REPO_ROOT / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md",
        [
            "## 7. Forbidden-Scope Audit",
            "## 6. Acceptance Mapping",
        ],
    ),
    (
        "Plan A trial brief carries the post-recovery §13 superseder",
        REPO_ROOT / "docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md",
        [
            "## 13. Real Operator Trial Re-Entry",
            "supersedes",
            "Real operator trial readiness",
        ],
    ),
    (
        "Plan A coordinator write-up carries the post-recovery §13 closure",
        REPO_ROOT / "docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md",
        [
            "## 13. Real Operator Trial Re-Entry",
            "static-only era",
        ],
    ),
    (
        "CURRENT_ENGINEERING_FOCUS reflects the post-recovery / re-entry stage",
        REPO_ROOT / "CURRENT_ENGINEERING_FOCUS.md",
        [
            "Real Operator Trial Re-Entry",
            "PR-1 / PR-2 / PR-3 / PR-4",
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
