"""CI invariants for the Recovery PR-5 trial re-entry gate.

Mirrors the documentation invariants enforced by
``scripts/recovery_pr5_trial_reentry_check.py``. Imports nothing from
``gateway.app`` so the test runs even on environments where the
gateway runtime cannot be imported (e.g. Python 3.9 + the
pre-existing ``gateway/app/config.py`` PEP 604 incompatibility noted
in PR-1 / PR-2 / PR-3 / PR-4 execution logs).

Authority:
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md``
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]


def _read(path: Path) -> str:
    assert path.exists(), f"required gate evidence missing: {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


def test_pr1_execution_log_records_merged_status() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md"
    )
    assert "MERGED to `main`" in text
    assert "4c317c4" in text


def test_pr2_execution_log_records_merged_status() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md"
    )
    assert "MERGED to `main`" in text
    assert "4343bec" in text


def test_pr3_execution_log_records_merged_status() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md"
    )
    assert "MERGED to `main`" in text
    assert "d53da0f" in text


def test_pr4_execution_log_records_merged_status_with_correction_pass() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md"
    )
    assert "MERGED to `main`" in text
    assert "0549ee0" in text
    # The PR-4 reviewer-fail correction pass §9.1 is part of the gate
    # evidence (route shape + closed-set rejection + D.1 active path).
    assert "9.1 Reviewer-Fail Correction Pass" in text


def test_pr5_trial_reentry_gate_document_exists_with_required_sections() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md"
    )
    for required in (
        "Recovery Wave Acceptance — Evidence Map",
        "Real-Trial Re-Entry Go/No-Go Checklist",
        "Post-Recovery Operator-Eligible Scope",
        "Post-Recovery Operator-Blocked Scope",
        "## 10. Signoff",
        "Stop conditions",
    ):
        assert required in text, f"PR-5 gate missing section: {required!r}"


def test_plan_a_trial_brief_carries_post_recovery_section() -> None:
    text = _read(
        REPO_ROOT / "docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md"
    )
    # Plan A pre-recovery §12 must be preserved verbatim for audit.
    assert "## 12. Final Readiness Conclusion" in text
    # ...and the post-recovery §13 must supersede it.
    assert "## 13. Real Operator Trial Re-Entry" in text
    assert "supersedes" in text


def test_plan_a_writeup_carries_post_recovery_section() -> None:
    text = _read(
        REPO_ROOT / "docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md"
    )
    assert "## 13. Real Operator Trial Re-Entry" in text
    assert "static-only era" in text


def test_current_engineering_focus_reflects_post_recovery_stage() -> None:
    text = _read(REPO_ROOT / "CURRENT_ENGINEERING_FOCUS.md")
    assert "Real Operator Trial Re-Entry" in text
    assert "PR-1 / PR-2 / PR-3 / PR-4" in text
