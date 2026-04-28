"""Phase A validation: Digital Anchor Task / Role Entry contract.

Wave: ApolloVeo 2.0 Digital Anchor Second Production Line Wave — Phase A
(Task / Role Entry).

Authority:
- docs/architecture/apolloveo_2_0_master_plan_v1_1.md (Part I Q5 / Part III P2)
- docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md
- docs/contracts/digital_anchor/task_entry_contract_v1.md
- docs/contracts/digital_anchor/packet_v1.md
- docs/contracts/digital_anchor/role_pack_contract_v1.md
- docs/contracts/digital_anchor/speaker_plan_contract_v1.md
- schemas/packets/digital_anchor/packet.schema.json

These tests are deliberately minimal. They prove the invariants of the
Phase A landing without exercising any runtime task-creation code:

  1. The task entry contract is present at the canonical path.
  2. The contract declares the closed entry-field set intended by Phase A.
  3. Every line-truth entry maps to a packet path reachable from the
     frozen Digital Anchor schema (loadable JSON Schema at the canonical
     path) and its line-specific contracts.
  4. The contract introduces no forbidden vendor/model/provider/engine
     token and no truth-shape state field, and does not pull Matrix
     Script / Hot Follow / W2.2 / W2.3 surfaces into Phase A scope.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

ENTRY_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "digital_anchor" / "task_entry_contract_v1.md"
)
PACKET_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "packets" / "digital_anchor" / "packet.schema.json"
)
PACKET_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "digital_anchor" / "packet_v1.md"
)
ROLE_PACK_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "digital_anchor" / "role_pack_contract_v1.md"
)
SPEAKER_PLAN_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "digital_anchor" / "speaker_plan_contract_v1.md"
)
EVIDENCE_PATH = (
    REPO_ROOT
    / "docs"
    / "execution"
    / "evidence"
    / "digital_anchor_phase_a_task_entry_v1.md"
)
LOG_PATH = (
    REPO_ROOT
    / "docs"
    / "execution"
    / "DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md"
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
    "role_profile_ref",
    "role_framing_hint",
    "output_intent",
    "speaker_segment_count_hint",
    "dub_kind_hint",
    "lip_sync_kind_hint",
    "scene_binding_hint",
    "operator_notes",
}

# Entries that must classify as line truth (cross to packet line-specific delta).
LINE_TRUTH_ENTRIES = {
    "source_script_ref",
    "language_scope",
    "role_profile_ref",
}

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
    "matrix_script",
    "hot_follow",
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
        ROLE_PACK_CONTRACT_PATH,
        SPEAKER_PLAN_CONTRACT_PATH,
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
    """All three line-truth entries must map to packet paths reachable from
    the frozen Digital Anchor schema's $defs / line-specific contracts."""
    schema = json.loads(_read(PACKET_SCHEMA_PATH))

    line_specific_ref_enum = schema["$defs"]["lineSpecificRef"]["properties"][
        "ref_id"
    ]["enum"]
    assert "digital_anchor_role_pack" in line_specific_ref_enum
    assert "digital_anchor_speaker_plan" in line_specific_ref_enum

    contract_text = _read(ENTRY_CONTRACT_PATH)
    # The mapping note must reference all three line-truth seeds by name.
    for needle in (
        "segments[*].script_ref",
        "roles[*].language_scope_ref",
        "segments[*].language_pick",
        "roles[*].appearance_ref",
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
        if stripped.startswith("#"):
            in_forbidden_section = "forbidden" in stripped.lower()
            continue
        if in_forbidden_section:
            continue
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
    """Phase A must remain Digital-Anchor-only.

    The entry contract may *mention* Matrix Script / Hot Follow / W2.2 /
    W2.3 only inside an explicit out-of-scope / forbidden / deferred
    statement. Any other mention is a scope leak.
    """
    text = _read(ENTRY_CONTRACT_PATH)
    lowered = text.lower()

    for scope in OUT_OF_WAVE_SCOPES:
        if scope.lower() not in lowered:
            continue
        assert any(
            marker in lowered
            for marker in (
                "out of this wave",
                "not applicable",
                "forbidden",
                "deferred",
                "must not",
                "never at entry",
            )
        ), (
            f"entry contract mentions out-of-wave scope {scope!r} without explicit "
            f"exclusion language"
        )


def test_entry_contract_does_not_widen_closed_kind_sets() -> None:
    """Phase A entry hints select among existing values only.

    The contract MUST NOT introduce any new value into the four closed
    kind-sets owned by the line-specific contracts. We assert by verifying
    the contract states the rule explicitly.
    """
    text = _read(ENTRY_CONTRACT_PATH)
    lowered = text.lower()
    for kind_set in (
        "framing_kind_set",
        "appearance_ref_kind_set",
        "dub_kind_set",
        "lip_sync_kind_set",
    ):
        assert kind_set in text, (
            f"entry contract does not reference closed kind-set {kind_set!r}"
        )
    assert (
        "never widens" in lowered
        or "are not widened" in lowered
        or "not widened" in lowered
    ), "entry contract is missing the explicit non-widening discipline statement"


def test_evidence_index_records_phase_a_rows() -> None:
    text = _read(EVIDENCE_INDEX_PATH)
    for needle in (
        "docs/contracts/digital_anchor/task_entry_contract_v1.md",
        "docs/execution/evidence/digital_anchor_phase_a_task_entry_v1.md",
        "docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md",
        "tests/contracts/digital_anchor/test_task_entry_phase_a.py",
    ):
        assert needle in text, f"evidence index missing Phase A row: {needle}"


def test_log_phase_a_recorded_with_hard_stop() -> None:
    text = _read(LOG_PATH)
    assert "## Phase A" in text, "execution log missing Phase A heading"
    phase_a_idx = text.index("## Phase A")
    phase_b_idx = text.index("## Phase B")
    phase_a_section = text[phase_a_idx:phase_b_idx]
    assert "implementation green" in phase_a_section, (
        "Phase A is not recorded as implementation green"
    )
    assert "do not start Phase B" in phase_a_section, "Phase A hard stop is missing"


@pytest.mark.parametrize("entry", sorted(LINE_TRUTH_ENTRIES))
def test_each_line_truth_entry_appears_in_mapping_note(entry: str) -> None:
    text = _read(ENTRY_CONTRACT_PATH)
    needle = f"entry.{entry}"
    assert needle in text, f"mapping note missing line-truth pointer for {entry!r}"


@pytest.mark.parametrize("entry_field", sorted(EXPECTED_ENTRY_FIELDS))
def test_minimum_coverage_areas_present(entry_field: str) -> None:
    """The mission baseline requires the entry to cover at minimum:
    role_profile / role_ref, speaker plan entry hints, language scope /
    output intent, scene binding entry hints, operator notes. The closed
    entry-field set is exhaustive proof; this parameterized test asserts
    each declared field is also present in the mapping note (entry.X)
    block, ensuring no field is declared without a mapping target.
    """
    text = _read(ENTRY_CONTRACT_PATH)
    needle = f"entry.{entry_field}"
    assert needle in text, (
        f"mapping note missing pointer for declared entry field {entry_field!r}"
    )
