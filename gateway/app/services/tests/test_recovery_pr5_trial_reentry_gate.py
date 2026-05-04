"""CI invariants for the rewritten Recovery PR-5 trial re-entry gate.

After the 2026-05-04 rewrite, PR-5 records a **NOT-READY** verdict
for real operator trial and a binding **Product-Flow Enforcement
Order** elevating the two product-flow design documents to line-
specific execution authority. This test module mirrors the
documentation invariants enforced by
``scripts/recovery_pr5_trial_reentry_check.py``.

Imports nothing from ``gateway.app`` so the test runs even on
environments where the gateway runtime cannot be imported (Python 3.9
+ the pre-existing ``gateway/app/config.py`` PEP 604 incompatibility
noted in PR-1 / PR-2 / PR-3 / PR-4 execution logs).
"""
from __future__ import annotations

from pathlib import Path


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
    assert "9.1 Reviewer-Fail Correction Pass" in text


def test_pr5_gate_records_not_ready_verdict() -> None:
    """Rewrite invariant: the gate document MUST record a NOT-READY
    verdict for real operator trial. A future commit that flips this
    to GO without an authored 'Trial Re-Entry Gate v2' PR is a
    regression."""
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md"
    )
    assert "## 0. Verdict" in text
    assert "Real operator trial is NOT READY" in text
    # The gate MUST NOT claim real-trial GO subject to coordinator
    # G5..G9 — that was the wrong pre-rewrite conclusion.
    assert "Real operator trial readiness:** **GO" not in text


def test_pr5_gate_carries_product_flow_enforcement_order() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md"
    )
    for required in (
        "Product-Flow Enforcement Order",
        "Top-level flow remains valid as the factory-wide abstract flow",
        "Line-specific product-flow documents are binding inside their\n   line",
        "Future Task Area / Workbench / Delivery implementations MUST map",
        "Operator-ready cannot be claimed",
    ):
        assert required in text, f"PR-5 gate missing PFE order section: {required!r}"


def test_pr5_gate_names_operator_workflow_convergence_wave() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md"
    )
    for required in (
        "Operator Workflow Convergence Wave",
        "Phase OWC-MS",
        "Phase OWC-DA",
        "Matrix Script first",
        "Digital Anchor second",
    ):
        assert required in text, f"PR-5 gate missing OWC wave section: {required!r}"


def test_pr5_gate_carries_w7_w12_unmet_block() -> None:
    text = _read(
        REPO_ROOT
        / "docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md"
    )
    # The W7..W12 section MUST be present and the rows MUST be unchecked.
    for required in ("**W7.**", "**W8.**", "**W9.**", "**W10.**", "**W11.**", "**W12.**"):
        assert required in text, f"PR-5 gate missing W-row: {required!r}"
    # All six W7..W12 rows MUST be unchecked. We assert this by checking
    # each row is preceded by `[ ]` not `[x]` near its label.
    for label in ("**W7.**", "**W8.**", "**W9.**", "**W10.**", "**W11.**", "**W12.**"):
        idx = text.index(label)
        # Look backwards for the nearest `[ ]` or `[x]` checkbox.
        preceding = text[max(0, idx - 80) : idx]
        assert "[ ]" in preceding and "[x]" not in preceding, (
            f"W-row {label!r} appears to be checked; W7..W12 MUST remain "
            f"unchecked until the Convergence Wave closes"
        )


def test_matrix_script_product_flow_doc_is_authority() -> None:
    text = _read(REPO_ROOT / "docs/product/matrix_script_product_flow_v1.md")
    assert "Matrix Script Product-Flow Design v1" in text
    assert "line-specific execution authority" in text
    assert "Recovery PR-5" in text
    assert "Operator-ready" in text


def test_digital_anchor_product_flow_doc_is_authority() -> None:
    text = _read(REPO_ROOT / "docs/product/digital_anchor_product_flow_v1.md")
    assert "Digital Anchor Product-Flow Design v1" in text
    assert "line-specific execution authority" in text
    assert "Recovery PR-5" in text
    assert "Operator-ready" in text


def test_plan_a_trial_brief_records_not_ready() -> None:
    text = _read(
        REPO_ROOT / "docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md"
    )
    assert "## 12. Final Readiness Conclusion" in text  # pre-recovery preserved
    assert "## 13. Real Operator Trial Re-Entry — NOT READY" in text
    assert "**NOT READY**" in text
    assert "Operator Workflow Convergence Wave" in text


def test_plan_a_writeup_records_blocked_until_convergence() -> None:
    text = _read(REPO_ROOT / "docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md")
    assert "## 13. Real Operator Trial Re-Entry — NOT READY" in text
    assert "BLOCKED until" in text
    assert "Operator Workflow Convergence Wave" in text


def test_current_engineering_focus_records_not_ready_plus_convergence_wave() -> None:
    text = _read(REPO_ROOT / "CURRENT_ENGINEERING_FOCUS.md")
    assert "Operator Workflow Convergence Wave" in text
    assert "NOT READY" in text
    assert "Matrix Script first" in text
    assert "Digital Anchor second" in text
