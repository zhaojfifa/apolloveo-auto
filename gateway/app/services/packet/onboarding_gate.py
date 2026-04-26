"""Factory packet onboarding gate skeleton.

Consumes a `PacketValidationReport` and the envelope's onboarding evidence,
emits an `OnboardingGateResult`. Read-only: no L1/L2/L3/L4 truth writes,
no runtime orchestration, no donor coupling.

Authority:
- ``docs/contracts/factory_packet_envelope_contract_v1.md`` (E4 ready_state lifecycle,
  OnboardingGateResult shape)
- ``docs/contracts/factory_packet_validator_rules_v1.md`` (R1..R5 violation surface)
- ``docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md`` (Packet gate)

Decision matrix (envelope.evidence.ready_state -> validator outcome -> gate_status):

    draft               -> pending  (packet not yet submitted for validation)
    validating          -> pending  (validator run not concluded for this version)
    gated               -> blocked  (prior validator/onboarding cycle blocked)
    ready  + ok=False   -> blocked  (validator violations still outstanding)
    ready  + ok=True    -> passed   (eligible for P3 runtime onboarding)
    frozen + ok=True    -> passed   (already onboarded; gate is a no-op confirm)
    frozen + ok=False   -> blocked  (truth drift; reopen)

Reference evidence rules:
- ``evidence.reference_evidence_path`` MUST resolve to a file in the working tree.
  A missing reference evidence path turns gate_status into ``blocked`` regardless
  of the validator outcome, because the onboarding gate has nothing to anchor
  the packet's reference green baseline to.
- ``evidence.validator_report_path`` is informational; if absent the gate falls
  back to the in-process ``PacketValidationReport`` argument and records that
  in ``evidence_links`` so reviewers can replay.

This module has no side effects; ``evaluate_onboarding`` returns a frozen
``OnboardingGateResult`` and never mutates the envelope or the report.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .envelope import (
    PacketEnvelope,
    PacketValidationReport,
    PERMITTED_READY_STATES,
)

GATE_PASSED = "passed"
GATE_BLOCKED = "blocked"
GATE_PENDING = "pending"

GATE_STATUSES: frozenset = frozenset({GATE_PASSED, GATE_BLOCKED, GATE_PENDING})

GATE_RULE_VERSION = "v1"


@dataclass(frozen=True)
class OnboardingGateResult:
    """Output of the onboarding gate.

    Mirrors the shape declared in factory_packet_envelope_contract_v1
    "Allowed Outputs". Carries gate status, blocked reasons (one per
    distinct cause), and evidence links for reviewer replay.
    """
    gate_status: str  # one of GATE_STATUSES
    blocked_reasons: List[str] = field(default_factory=list)
    evidence_links: List[str] = field(default_factory=list)
    rule_versions: dict = field(default_factory=dict)


def _evidence_links(
    envelope: PacketEnvelope,
    report: PacketValidationReport,
) -> List[str]:
    links: List[str] = []
    ev = envelope.evidence
    if ev.reference_evidence_path:
        links.append(f"reference_evidence:{ev.reference_evidence_path}")
    if ev.validator_report_path:
        links.append(f"validator_report:{ev.validator_report_path}")
    else:
        links.append("validator_report:in-process")
    links.append(
        "rule_versions:"
        + ",".join(f"{k}={v}" for k, v in sorted(report.rule_versions.items()))
    )
    return links


def _check_reference_evidence(
    envelope: PacketEnvelope, repo_root: Path
) -> Optional[str]:
    """Return a blocked reason when reference evidence is unusable, else None."""
    ev = envelope.evidence
    if not ev.reference_evidence_path:
        return "evidence.reference_evidence_path is empty"
    full = repo_root / ev.reference_evidence_path
    if not full.is_file():
        return (
            f"evidence.reference_evidence_path does not resolve to a file: "
            f"{ev.reference_evidence_path}"
        )
    return None


def _validator_reasons(report: PacketValidationReport) -> List[str]:
    reasons: List[str] = []
    for v in report.violations:
        reasons.append(f"{v.rule_id} @ {v.field.path}: {v.reason}")
    for m in report.missing:
        reasons.append(f"missing field: {m.path}")
    return reasons


def _classify(
    envelope: PacketEnvelope,
    report: PacketValidationReport,
    reference_reason: Optional[str],
) -> Tuple[str, List[str]]:
    rs = envelope.evidence.ready_state
    if rs not in PERMITTED_READY_STATES:
        return GATE_BLOCKED, [
            f"evidence.ready_state '{rs}' outside permitted set "
            f"{sorted(PERMITTED_READY_STATES)}"
        ]

    if reference_reason is not None:
        return GATE_BLOCKED, [reference_reason]

    if rs in ("draft", "validating"):
        return GATE_PENDING, []

    if rs == "gated":
        return GATE_BLOCKED, _validator_reasons(report) or [
            "packet is gated by a prior validator/onboarding cycle"
        ]

    # ready / frozen require a clean validator report.
    if not report.ok:
        return GATE_BLOCKED, _validator_reasons(report)

    return GATE_PASSED, []


def evaluate_onboarding(
    envelope: PacketEnvelope,
    report: PacketValidationReport,
    repo_root: Optional[os.PathLike] = None,
) -> OnboardingGateResult:
    """Decide onboarding gate outcome from envelope + validator report.

    The gate consumes validator output only; it never re-runs validation,
    never mutates state, and never reaches into runtime task readiness.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
    reference_reason = _check_reference_evidence(envelope, root)
    status, reasons = _classify(envelope, report, reference_reason)
    return OnboardingGateResult(
        gate_status=status,
        blocked_reasons=list(reasons),
        evidence_links=_evidence_links(envelope, report),
        rule_versions={
            **report.rule_versions,
            "onboarding_gate": GATE_RULE_VERSION,
        },
    )


__all__ = [
    "OnboardingGateResult",
    "GATE_PASSED",
    "GATE_BLOCKED",
    "GATE_PENDING",
    "GATE_STATUSES",
    "GATE_RULE_VERSION",
    "evaluate_onboarding",
]
