"""Phase D.0 validation: Digital Anchor publish feedback closure contract."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md"
)
LOG_PATH = REPO_ROOT / "docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md"
EVIDENCE_INDEX_PATH = REPO_ROOT / "docs/execution/apolloveo_2_0_evidence_index_v1.md"
EVIDENCE_PATH = (
    REPO_ROOT
    / "docs/execution/evidence/digital_anchor_phase_d0_publish_feedback_closure_contract_v1.md"
)


def _contract_text() -> str:
    assert CONTRACT.exists(), f"missing contract: {CONTRACT}"
    return CONTRACT.read_text(encoding="utf-8")


def test_phase_d0_contract_defines_required_feedback_closure_fields():
    text = _contract_text()
    for token in (
        "digital_anchor_publish_feedback_closure_v1",
        "role_feedback[]",
        "segment_feedback[]",
        "publish_url",
        "publish_status",
        "channel_metrics",
        "operator_publish_notes",
        "feedback_closure_records[]",
    ):
        assert token in text


def test_role_and_segment_feedback_are_joined_to_packet_truth():
    text = _contract_text()
    for token in (
        "role_pack.delta.roles[].role_id",
        "speaker_plan.delta.segments[].segment_id",
        "speaker_plan.delta.segments[].binds_role_id == role_pack.delta.roles[].role_id",
        "must not mutate role declarations",
        "must not mutate segment declarations",
    ):
        assert token in text


def test_phase_c_boundary_and_projection_only_surfaces_are_preserved():
    text = _contract_text()
    for token in (
        "Phase C delivery binding remains read-only",
        "manifest.*",
        "metadata_projection.*",
        "Projection-only",
        "Phase C `delivery_pack`",
        "Phase C `result_packet_binding`",
    ):
        assert token in text


def test_schema_impact_is_explicitly_no_packet_schema_change():
    text = _contract_text()
    assert "No packet/schema change is needed in Phase D.0." in text
    assert "external to the packet schema" in text
    assert "must not replace existing A/B/C frozen sections" in text


def test_forbidden_scope_and_no_writeback_implementation_are_recorded():
    text = _contract_text()
    for token in (
        "does not implement write-back code",
        "provider/model/vendor/avatar-engine/TTS/lip-sync controls",
        "Matrix Script",
        "Hot Follow",
        "W2.2 / W2.3",
        "packet schema redesign",
    ):
        assert token in text


def test_log_evidence_and_index_record_phase_d0_rows():
    assert EVIDENCE_PATH.exists(), f"missing evidence: {EVIDENCE_PATH}"
    log_text = LOG_PATH.read_text(encoding="utf-8")
    index_text = EVIDENCE_INDEX_PATH.read_text(encoding="utf-8")
    for needle in (
        "docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md",
        "docs/execution/evidence/digital_anchor_phase_d0_publish_feedback_closure_contract_v1.md",
        "tests/contracts/digital_anchor/test_publish_feedback_closure_phase_d0.py",
    ):
        assert needle in log_text or needle in index_text
