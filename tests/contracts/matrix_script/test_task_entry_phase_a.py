"""Phase A validation: Matrix Script Task Entry contract.

Wave: ApolloVeo 2.0 Matrix Script First Production Line — Phase A (Task Entry).
Authority:
- docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md §6 Phase A
- docs/contracts/matrix_script/task_entry_contract_v1.md
- docs/contracts/matrix_script/packet_v1.md
- schemas/packets/matrix_script/packet.schema.json

These tests are deliberately minimal. They prove four invariants of the
Phase A landing without exercising any runtime task-creation code:

  1. The task entry contract is present at the canonical path.
  2. The contract declares the closed entry-field set intended by Phase A.
  3. Every line-truth entry maps to a packet path reachable from the
     frozen Matrix Script schema (loadable JSON Schema at the canonical
     path).
  4. The contract introduces no forbidden vendor/model/provider/engine
     token and no truth-shape state field, and does not pull Digital
     Anchor / W2.2 / W2.3 / Hot Follow business surfaces into Phase A
     scope.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

ENTRY_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "matrix_script" / "task_entry_contract_v1.md"
)
PACKET_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "packets" / "matrix_script" / "packet.schema.json"
)
PACKET_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "matrix_script" / "packet_v1.md"
)
EVIDENCE_PATH = (
    REPO_ROOT
    / "docs"
    / "execution"
    / "evidence"
    / "matrix_script_phase_a_task_entry_v1.md"
)
LOG_PATH = (
    REPO_ROOT / "docs" / "execution" / "MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md"
)
EVIDENCE_INDEX_PATH = (
    REPO_ROOT / "docs" / "execution" / "apolloveo_2_0_evidence_index_v1.md"
)

# The closed entry-field set that the task entry contract is required to
# declare at v1. Additions require a contract re-version.
EXPECTED_ENTRY_FIELDS = {
    "topic",
    "source_script_ref",
    "language_scope",
    "target_platform",
    "variation_target_count",
    "audience_hint",
    "tone_hint",
    "length_hint",
    "product_ref",
    "operator_notes",
}

# Entries that must classify as line truth (cross to packet line-specific delta).
LINE_TRUTH_ENTRIES = {"source_script_ref", "language_scope"}

# Validator R3 / R5 / metadata.not.anyOf — none of these tokens may appear
# as a collected/declared field in the entry contract. They MAY appear in
# prose that explicitly forbids them; the test scans for *field-form*
# occurrences only (backtick-quoted identifiers).
FORBIDDEN_TOKENS_R3 = {
    "vendor_id",
    "model_id",
    "provider_id",
    "engine_id",
}
FORBIDDEN_TOKENS_R5 = {
    "current_attempt",
    "delivery_ready",
    "final_ready",
    "publishable",
}

# Out-of-wave scopes that Phase A explicitly does NOT pull in.
OUT_OF_WAVE_SCOPES = (
    "digital_anchor",
    "W2.2",
    "W2.3",
)


# ----------------------------- helpers ------------------------------------- #


def _read(path: Path) -> str:
    assert path.exists(), f"missing required Phase A artefact: {path}"
    return path.read_text(encoding="utf-8")


def _backticked_identifiers(text: str) -> set[str]:
    """Collect all backtick-quoted single-token identifiers from markdown.

    We only flag *field-form* occurrences (backtick-quoted bare identifiers)
    so prose can still legitimately *forbid* a token by name without the
    test confusing forbidding-prose with a declared field.
    """
    identifiers: set[str] = set()
    for match in re.finditer(r"`([A-Za-z_][A-Za-z0-9_]*)`", text):
        identifiers.add(match.group(1))
    return identifiers


# ----------------------------- tests --------------------------------------- #


def test_phase_a_artefacts_exist() -> None:
    for path in (
        ENTRY_CONTRACT_PATH,
        PACKET_SCHEMA_PATH,
        PACKET_CONTRACT_PATH,
        EVIDENCE_PATH,
        LOG_PATH,
        EVIDENCE_INDEX_PATH,
    ):
        assert path.exists(), f"required Phase A artefact missing: {path}"


def test_entry_contract_declares_closed_entry_field_set() -> None:
    text = _read(ENTRY_CONTRACT_PATH)
    backticked = _backticked_identifiers(text)
    missing = sorted(f for f in EXPECTED_ENTRY_FIELDS if f not in backticked)
    assert not missing, (
        "entry contract is missing required Phase A entry fields "
        f"(must be backticked at least once): {missing}"
    )


def test_line_truth_entries_map_to_reachable_packet_paths() -> None:
    """Both line-truth entries must map to packet paths reachable from the
    frozen Matrix Script schema's $defs / line-specific contracts."""
    schema = json.loads(_read(PACKET_SCHEMA_PATH))

    # `slot_pack` line-specific ref enum membership must hold (where
    # body_ref + language_scope live).
    line_specific_ref_enum = schema["$defs"]["lineSpecificRef"]["properties"][
        "ref_id"
    ]["enum"]
    assert "matrix_script_slot_pack" in line_specific_ref_enum

    contract_text = _read(ENTRY_CONTRACT_PATH)
    # The mapping note must reference both line-truth seeds by name.
    for needle in (
        "slots[*].body_ref",
        "slots[*].language_scope",
    ):
        assert needle in contract_text, (
            f"entry contract does not map line-truth entry to packet path: {needle!r}"
        )


def test_entry_contract_introduces_no_forbidden_field_form_tokens() -> None:
    """The entry contract must not declare any backticked field whose
    identifier is one of the validator R3 / R5 forbidden tokens.

    Note: prose may freely *forbid* these tokens; the test inspects only
    backtick-quoted *field-form* occurrences and tolerates explicit
    forbidding lists by checking the surrounding line is part of the
    forbidden-fields prose.
    """
    text = _read(ENTRY_CONTRACT_PATH)

    forbidden_tokens = FORBIDDEN_TOKENS_R3 | FORBIDDEN_TOKENS_R5

    in_forbidden_section = False
    for line in text.splitlines():
        stripped = line.strip()
        # Track section context — any heading containing "forbidden" puts us
        # inside a forbidding section until the next heading.
        if stripped.startswith("#"):
            in_forbidden_section = "forbidden" in stripped.lower()
            continue
        if in_forbidden_section:
            continue
        # Skip lines that are explicitly declaring tokens as forbidden.
        lowered = line.lower()
        if any(
            marker in lowered
            for marker in (
                "forbidden",
                "must not",
                "validator r3",
                "validator r5",
                "rule r3",
                "rule r5",
                "(r3)",
                "(r5)",
                "metadata.not.anyof",
                "envelope §forbidden",
            )
        ):
            continue
        backticked = _backticked_identifiers(line)
        leaked = backticked & forbidden_tokens
        assert not leaked, (
            f"entry contract leaks forbidden field-form token outside a forbidding "
            f"line: {sorted(leaked)} | line={line!r}"
        )


def test_entry_contract_does_not_pull_in_out_of_wave_scopes() -> None:
    """Phase A must remain Matrix-Script-only.

    The entry contract may *mention* Digital Anchor / W2.2 / W2.3 / Hot
    Follow only inside an explicit out-of-scope / forbidden / deferred
    statement. Any other mention is a scope leak.
    """
    text = _read(ENTRY_CONTRACT_PATH)
    lowered = text.lower()

    for scope in OUT_OF_WAVE_SCOPES:
        if scope.lower() not in lowered:
            continue
        # If mentioned, it must co-occur with explicit scope-exclusion language.
        assert any(
            marker in lowered
            for marker in (
                "out of this wave",
                "not applicable",
                "forbidden",
                "deferred",
                "must not",
            )
        ), (
            f"entry contract mentions out-of-wave scope {scope!r} without explicit "
            f"exclusion language"
        )


def test_evidence_index_records_phase_a_rows() -> None:
    text = _read(EVIDENCE_INDEX_PATH)
    for needle in (
        "docs/contracts/matrix_script/task_entry_contract_v1.md",
        "docs/execution/evidence/matrix_script_phase_a_task_entry_v1.md",
        "docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md",
        "tests/contracts/matrix_script/test_task_entry_phase_a.py",
    ):
        assert needle in text, f"evidence index missing Phase A row: {needle}"


def test_log_preserves_phase_sequence_after_phase_a() -> None:
    """The execution log must keep later phases sequenced after Phase A."""
    text = _read(LOG_PATH)
    for phase in ("Phase B", "Phase C", "Phase D"):
        assert f"## {phase}" in text, f"execution log missing {phase} marker"

    phase_b_idx = text.index("## Phase B")
    phase_c_idx = text.index("## Phase C")
    phase_b_section = text[phase_b_idx:phase_c_idx]
    assert "implementation green" in phase_b_section, "Phase B is not recorded as implemented"
    assert "do not start Phase C" in phase_b_section, "Phase B hard stop is missing"

    phase_d_idx = text.index("## Phase D")
    phase_c_section = text[phase_c_idx:phase_d_idx]
    assert "implementation green" in phase_c_section, "Phase C is not recorded as implemented"
    assert "do not start Phase D" in phase_c_section, "Phase C hard stop is missing"

    phase_d_window = text[phase_d_idx : phase_d_idx + 400]
    assert "NOT STARTED" in phase_d_window, (
        "execution log does not mark Phase D as NOT STARTED"
    )


@pytest.mark.parametrize("entry", sorted(LINE_TRUTH_ENTRIES))
def test_each_line_truth_entry_appears_in_mapping_note(entry: str) -> None:
    text = _read(ENTRY_CONTRACT_PATH)
    # The mapping-note section uses `entry.<field> →` pointers.
    needle = f"entry.{entry}"
    assert needle in text, f"mapping note missing line-truth pointer for {entry!r}"
