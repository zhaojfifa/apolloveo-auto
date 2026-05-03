"""B4 artifact-lookup tests for the Matrix Script delivery binding (Plan E PR-1, Item E.MS.1).

Authority:
- ``docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md``
- ``docs/contracts/matrix_script/delivery_binding_contract_v1.md``
- ``docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md`` §3.1 / §5.1 / §5.4 / §6 / §7

Scope: this test file covers Item E.MS.1 (Matrix Script ``result_packet_binding.artifact_lookup``)
end-to-end against the contract — closed (ref_id, locator) pair set, packet-truth-only resolution,
explicit ``artifact_lookup_unresolved`` sentinel on absence, no exception on malformed packet,
no packet mutation, retirement of the ``not_implemented_phase_c`` placeholder strings, and the
backward-compatible projection shape so no other code site needs to change.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_binding import (
    ARTIFACT_LOOKUP_UNRESOLVED,
    CAPABILITY_DUB_REF_ID,
    CAPABILITY_PACK_REF_ID,
    CAPABILITY_SUBTITLES_REF_ID,
    SLOT_PACK_REF_ID,
    VARIATION_REF_ID,
    artifact_lookup,
    project_delivery_binding,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[3]
    / "../schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json"
).resolve()


@pytest.fixture
def sample_packet() -> dict[str, Any]:
    raw = json.loads(SAMPLE_PACKET_PATH.read_text())
    assert raw["line_id"] == "matrix_script", "fixture must be the Matrix Script sample packet"
    return raw


@pytest.fixture
def sample_packet_with_l3(sample_packet: dict[str, Any]) -> dict[str, Any]:
    """A future-state packet that simulates what a Plan E phase containing D2 + L2 would emit.

    This fixture lets the B4 lookup demonstrate a real ArtifactHandle return path without
    introducing D2 implementation here. The fields ``final_provenance`` and ``final_fresh``
    are read-only inputs to the lookup; this test never asks B4 to write them.
    """
    packet = copy.deepcopy(sample_packet)
    packet["final_provenance"] = {
        VARIATION_REF_ID: {"cell_001": "current", "cell_002": "historical"},
        SLOT_PACK_REF_ID: {"slot_001": "current"},
        CAPABILITY_SUBTITLES_REF_ID: "current",
        CAPABILITY_DUB_REF_ID: "historical",
    }
    packet["final_fresh"] = {
        VARIATION_REF_ID: {"cell_001": True, "cell_002": False},
        SLOT_PACK_REF_ID: {"slot_001": True},
        CAPABILITY_SUBTITLES_REF_ID: True,
        CAPABILITY_DUB_REF_ID: False,
    }
    return packet


# ---------------------------------------------------------------------------
# Closed (ref_id, locator) pair set + sentinel discipline
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref_id,locator",
    [
        ("not_a_real_ref_id", None),
        ("matrix_script_variation_matrix", None),  # variation requires cell_id locator
        ("matrix_script_slot_pack", None),  # slot_pack requires slot_id locator
        ("capability:subtitles", "should-be-null"),  # capability:* requires None
        ("capability:dub", "x"),
        ("capability:pack", 42),
        ("matrix_script_variation_matrix", ""),
        ("matrix_script_variation_matrix", 123),
    ],
)
def test_invalid_pair_returns_sentinel(sample_packet: dict[str, Any], ref_id: str, locator: Any) -> None:
    assert artifact_lookup(sample_packet, ref_id, locator) == ARTIFACT_LOOKUP_UNRESOLVED


def test_valid_pair_with_unknown_cell_returns_sentinel(sample_packet: dict[str, Any]) -> None:
    assert (
        artifact_lookup(sample_packet, VARIATION_REF_ID, "cell_does_not_exist")
        == ARTIFACT_LOOKUP_UNRESOLVED
    )


def test_valid_pair_with_unknown_slot_returns_sentinel(sample_packet: dict[str, Any]) -> None:
    assert (
        artifact_lookup(sample_packet, SLOT_PACK_REF_ID, "slot_does_not_exist")
        == ARTIFACT_LOOKUP_UNRESOLVED
    )


# ---------------------------------------------------------------------------
# Provenance discipline (mirrors L3 final_provenance per contract §6)
# ---------------------------------------------------------------------------


def test_known_cell_without_l3_provenance_returns_sentinel(sample_packet: dict[str, Any]) -> None:
    """Per contract §6: if L3 has not promoted ``final_provenance`` for the row, return sentinel."""
    assert artifact_lookup(sample_packet, VARIATION_REF_ID, "cell_001") == ARTIFACT_LOOKUP_UNRESOLVED


def test_known_slot_without_l3_provenance_returns_sentinel(sample_packet: dict[str, Any]) -> None:
    assert artifact_lookup(sample_packet, SLOT_PACK_REF_ID, "slot_001") == ARTIFACT_LOOKUP_UNRESOLVED


@pytest.mark.parametrize(
    "ref_id",
    [CAPABILITY_SUBTITLES_REF_ID, CAPABILITY_DUB_REF_ID, CAPABILITY_PACK_REF_ID],
)
def test_capability_without_l3_provenance_returns_sentinel(
    sample_packet: dict[str, Any], ref_id: str
) -> None:
    assert artifact_lookup(sample_packet, ref_id, None) == ARTIFACT_LOOKUP_UNRESOLVED


# ---------------------------------------------------------------------------
# Positive resolution paths (when L3 + L2 are populated by a future Plan E phase)
# ---------------------------------------------------------------------------


def test_resolved_handle_for_variation_cell(sample_packet_with_l3: dict[str, Any]) -> None:
    handle = artifact_lookup(sample_packet_with_l3, VARIATION_REF_ID, "cell_001")
    assert isinstance(handle, Mapping)
    assert handle == {
        "artifact_ref": "slot_001",
        "freshness": "fresh",
        "provenance": "current",
    }


def test_resolved_handle_for_variation_cell_stale_historical(
    sample_packet_with_l3: dict[str, Any],
) -> None:
    handle = artifact_lookup(sample_packet_with_l3, VARIATION_REF_ID, "cell_002")
    assert handle == {
        "artifact_ref": "slot_002",
        "freshness": "stale",
        "provenance": "historical",
    }


def test_resolved_handle_for_slot(sample_packet_with_l3: dict[str, Any]) -> None:
    handle = artifact_lookup(sample_packet_with_l3, SLOT_PACK_REF_ID, "slot_001")
    assert handle == {
        "artifact_ref": "content://matrix_script/v1/slot_001",
        "freshness": "fresh",
        "provenance": "current",
    }


def test_resolved_handle_for_capability_subtitles(sample_packet_with_l3: dict[str, Any]) -> None:
    handle = artifact_lookup(sample_packet_with_l3, CAPABILITY_SUBTITLES_REF_ID, None)
    assert handle == {
        "artifact_ref": "deliverable_profile_matrix_script_v1::capability:subtitles",
        "freshness": "fresh",
        "provenance": "current",
    }


def test_resolved_handle_for_capability_dub_stale_historical(
    sample_packet_with_l3: dict[str, Any],
) -> None:
    handle = artifact_lookup(sample_packet_with_l3, CAPABILITY_DUB_REF_ID, None)
    assert handle == {
        "artifact_ref": "deliverable_profile_matrix_script_v1::capability:dub",
        "freshness": "stale",
        "provenance": "historical",
    }


# ---------------------------------------------------------------------------
# Failure-mode discipline (contract §"Failure-mode discipline")
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_packet",
    [
        None,
        "not-a-packet",
        42,
        [],
    ],
)
def test_lookup_never_raises_on_malformed_packet(bad_packet: Any) -> None:
    assert artifact_lookup(bad_packet, VARIATION_REF_ID, "cell_001") == ARTIFACT_LOOKUP_UNRESOLVED


def test_lookup_never_mutates_packet(sample_packet_with_l3: dict[str, Any]) -> None:
    snapshot = copy.deepcopy(sample_packet_with_l3)
    for ref_id, locator in [
        (VARIATION_REF_ID, "cell_001"),
        (SLOT_PACK_REF_ID, "slot_001"),
        (CAPABILITY_SUBTITLES_REF_ID, None),
        (CAPABILITY_DUB_REF_ID, None),
        (CAPABILITY_PACK_REF_ID, None),
    ]:
        artifact_lookup(sample_packet_with_l3, ref_id, locator)
    assert sample_packet_with_l3 == snapshot, "artifact_lookup must not mutate the packet"


# ---------------------------------------------------------------------------
# Projection integration: not_implemented_phase_c retired across all five rows
# ---------------------------------------------------------------------------


def test_projection_retires_not_implemented_phase_c_placeholder(sample_packet: dict[str, Any]) -> None:
    surface = project_delivery_binding(sample_packet)
    rendered = json.dumps(surface)
    assert "not_implemented_phase_c" not in rendered, (
        "Plan E Item E.MS.1 must replace every not_implemented_phase_c placeholder in the "
        "Matrix Script delivery projection."
    )


def test_projection_emits_artifact_lookup_per_row(sample_packet: dict[str, Any]) -> None:
    surface = project_delivery_binding(sample_packet)
    rows = surface["delivery_pack"]["deliverables"]
    assert len(rows) == 5, "five deliverable rows must remain (delivery_binding_contract_v1)"
    expected_ids = {
        "matrix_script_variation_manifest",
        "matrix_script_slot_bundle",
        "matrix_script_subtitle_bundle",
        "matrix_script_audio_preview",
        "matrix_script_scene_pack",
    }
    assert {row["deliverable_id"] for row in rows} == expected_ids
    # Every row must carry an artifact_lookup field whose value is either the closed sentinel
    # string or an ArtifactHandle mapping with the contract-pinned closed key set.
    for row in rows:
        value = row["artifact_lookup"]
        if isinstance(value, str):
            assert value == ARTIFACT_LOOKUP_UNRESOLVED
        else:
            assert isinstance(value, Mapping)
            assert set(value.keys()) == {"artifact_ref", "freshness", "provenance"}
            assert value["freshness"] in {"fresh", "stale", "absent"}
            assert value["provenance"] in {"current", "historical"}


def test_projection_shape_unchanged_aside_from_lookup_value(sample_packet: dict[str, Any]) -> None:
    """Acceptance §5: ``no other code site changes``. The top-level projection shape and
    every row's non-``artifact_lookup`` fields must be byte-for-byte identical to the
    pre-PR behavior of the delivery surface (which is what consumers downstream expect).
    """
    surface = project_delivery_binding(sample_packet)
    rows = surface["delivery_pack"]["deliverables"]
    for row in rows:
        assert {"deliverable_id", "kind", "required", "source_ref_id", "profile_ref", "artifact_lookup"} == set(
            row.keys()
        ), f"row {row['deliverable_id']} must keep the existing closed key set"
    # Top-level keys preserved.
    assert set(surface.keys()) == {
        "line_id",
        "packet_version",
        "surface",
        "delivery_pack",
        "result_packet_binding",
        "manifest",
        "metadata_projection",
        "phase_d_deferred",
    }


def test_projection_rows_resolve_when_l3_present(sample_packet_with_l3: dict[str, Any]) -> None:
    surface = project_delivery_binding(sample_packet_with_l3)
    rows = {row["deliverable_id"]: row for row in surface["delivery_pack"]["deliverables"]}
    # Aggregate manifest/bundle rows pass ``locator=None`` against ref_ids that require a
    # cell_id / slot_id locator, so they remain ``artifact_lookup_unresolved``. This is the
    # documented one-for-one replacement (contract §"Acceptance" item 5).
    assert rows["matrix_script_variation_manifest"]["artifact_lookup"] == ARTIFACT_LOOKUP_UNRESOLVED
    assert rows["matrix_script_slot_bundle"]["artifact_lookup"] == ARTIFACT_LOOKUP_UNRESOLVED
    # capability:* rows resolve under the future-state fixture.
    assert rows["matrix_script_subtitle_bundle"]["artifact_lookup"] == {
        "artifact_ref": "deliverable_profile_matrix_script_v1::capability:subtitles",
        "freshness": "fresh",
        "provenance": "current",
    }
    assert rows["matrix_script_audio_preview"]["artifact_lookup"] == {
        "artifact_ref": "deliverable_profile_matrix_script_v1::capability:dub",
        "freshness": "stale",
        "provenance": "historical",
    }
    # capability:pack has no provenance entry in the fixture, so it remains unresolved.
    assert rows["matrix_script_scene_pack"]["artifact_lookup"] == ARTIFACT_LOOKUP_UNRESOLVED


# ---------------------------------------------------------------------------
# Forbidden-content check: validator R3 (no vendor/model/provider/engine in output)
# ---------------------------------------------------------------------------


def test_artifact_lookup_output_has_no_vendor_model_provider_engine(
    sample_packet_with_l3: dict[str, Any],
) -> None:
    handle = artifact_lookup(sample_packet_with_l3, VARIATION_REF_ID, "cell_001")
    rendered = json.dumps(handle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert forbidden not in rendered
