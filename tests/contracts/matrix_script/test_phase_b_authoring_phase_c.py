"""Phase B deterministic authoring — Matrix Script §8.C contract conformance.

Authority:
- ``docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md`` §8.C
- ``docs/contracts/matrix_script/task_entry_contract_v1.md``
  §"Phase B deterministic authoring (addendum, 2026-05-03)"
- ``docs/contracts/matrix_script/variation_matrix_contract_v1.md``
- ``docs/contracts/matrix_script/slot_pack_contract_v1.md``
- ``docs/contracts/matrix_script/packet_v1.md``
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import replace

import pytest

from gateway.app.services.matrix_script.create_entry import (
    MatrixScriptCreateEntry,
)
from gateway.app.services.matrix_script.phase_b_authoring import (
    AUDIENCES,
    AXIS_KIND_SET,
    LENGTH_PICKS,
    LENGTH_RANGE,
    SLOT_KIND_SET,
    TONES,
    derive_phase_b_deltas,
)


TASK_ID = "abc123def456"


def _entry(
    *,
    variation_target_count: int = 4,
    target_language: str = "mm",
    source_language: str = "zh",
) -> MatrixScriptCreateEntry:
    return MatrixScriptCreateEntry(
        topic="trial topic",
        source_script_ref="content://matrix-script/source/trial-001",
        source_language=source_language,
        target_language=target_language,
        target_platform="TikTok",
        variation_target_count=variation_target_count,
    )


# --- §1. Axes -----------------------------------------------------------


def test_axes_emitted_match_contract_canonical_set():
    variation_delta, _ = derive_phase_b_deltas(_entry(), TASK_ID)
    axes = variation_delta["axes"]
    assert len(axes) == 3

    by_id = {axis["axis_id"]: axis for axis in axes}
    assert set(by_id) == {"tone", "audience", "length"}

    assert by_id["tone"] == {
        "axis_id": "tone",
        "kind": "categorical",
        "values": list(TONES),
        "is_required": True,
    }
    assert by_id["audience"] == {
        "axis_id": "audience",
        "kind": "enum",
        "values": list(AUDIENCES),
        "is_required": True,
    }
    assert by_id["length"] == {
        "axis_id": "length",
        "kind": "range",
        "values": dict(LENGTH_RANGE),
        "is_required": False,
    }


def test_axis_kind_set_is_closed_contract_set():
    variation_delta, _ = derive_phase_b_deltas(_entry(), TASK_ID)
    assert variation_delta["axis_kind_set"] == list(AXIS_KIND_SET)
    assert set(variation_delta["axis_kind_set"]) == {"categorical", "range", "enum"}


def test_slot_kind_set_is_closed_contract_set():
    _, slot_delta = derive_phase_b_deltas(_entry(), TASK_ID)
    assert slot_delta["slot_kind_set"] == list(SLOT_KIND_SET)
    assert set(slot_delta["slot_kind_set"]) == {"primary", "alternate", "fallback"}


# --- §2. Cardinality and round-trip ------------------------------------


@pytest.mark.parametrize("k", [1, 2, 4, 9, 12])
def test_cells_cardinality_matches_variation_target_count(k: int):
    variation_delta, slot_delta = derive_phase_b_deltas(
        _entry(variation_target_count=k), TASK_ID
    )
    assert len(variation_delta["cells"]) == k
    assert len(slot_delta["slots"]) == k


@pytest.mark.parametrize("k", [1, 4, 12])
def test_round_trip_cells_to_slots(k: int):
    variation_delta, slot_delta = derive_phase_b_deltas(
        _entry(variation_target_count=k), TASK_ID
    )
    cells = variation_delta["cells"]
    slots = slot_delta["slots"]
    assert len(cells) == len(slots) == k

    slot_ids = [slot["slot_id"] for slot in slots]
    cell_ids = [cell["cell_id"] for cell in cells]
    # Index-aligned 1-to-1 pairing for any k.
    for i in range(k):
        assert cells[i]["script_slot_ref"] == slots[i]["slot_id"]
        assert slots[i]["binds_cell_id"] == cells[i]["cell_id"]
    # No slot referenced by more than one cell — `slot_pack_contract_v1:59`.
    assert len(slot_ids) == len(set(slot_ids))
    assert len(cell_ids) == len(set(cell_ids))


def test_cell_and_slot_ids_use_zero_padded_three_digit_format():
    variation_delta, slot_delta = derive_phase_b_deltas(
        _entry(variation_target_count=4), TASK_ID
    )
    assert [c["cell_id"] for c in variation_delta["cells"]] == [
        "cell_001",
        "cell_002",
        "cell_003",
        "cell_004",
    ]
    assert [s["slot_id"] for s in slot_delta["slots"]] == [
        "slot_001",
        "slot_002",
        "slot_003",
        "slot_004",
    ]


# --- §3. Axis selection conformance ------------------------------------


def test_cell_axis_selections_drawn_from_axis_values():
    variation_delta, _ = derive_phase_b_deltas(
        _entry(variation_target_count=12), TASK_ID
    )
    for cell in variation_delta["cells"]:
        sel = cell["axis_selections"]
        assert sel["tone"] in TONES
        assert sel["audience"] in AUDIENCES
        assert sel["length"] in LENGTH_PICKS
        assert (
            LENGTH_RANGE["min"]
            <= sel["length"]
            <= LENGTH_RANGE["max"]
        )
        # Step-aligned: length is on the closed walk min..max step step.
        assert (sel["length"] - LENGTH_RANGE["min"]) % LENGTH_RANGE["step"] == 0


def test_axis_selections_distinct_for_max_k():
    """At k=12 every cell still has a distinct (tone, audience, length) tuple.

    The rotation has 9 × 7 = 63 unique tuples; collisions are not expected
    until k > 63.
    """
    variation_delta, _ = derive_phase_b_deltas(
        _entry(variation_target_count=12), TASK_ID
    )
    tuples = [
        (
            cell["axis_selections"]["tone"],
            cell["axis_selections"]["audience"],
            cell["axis_selections"]["length"],
        )
        for cell in variation_delta["cells"]
    ]
    assert len(set(tuples)) == 12


# --- §4. Body ref opacity ---------------------------------------------


_BODY_REF_PATTERN = re.compile(
    r"^content://matrix-script/[A-Za-z0-9._\-]+/slot/slot_\d{3}$"
)


def test_body_ref_is_opaque_and_carries_no_body_text():
    entry = _entry(variation_target_count=4)
    _, slot_delta = derive_phase_b_deltas(entry, TASK_ID)
    for slot in slot_delta["slots"]:
        ref = slot["body_ref"]
        assert _BODY_REF_PATTERN.match(ref), ref
        assert " " not in ref and "\n" not in ref and "\t" not in ref
        # Body ref MUST NOT be the operator-supplied source_script_ref —
        # bodies must be referenced opaquely by their own handle, not by
        # piggybacking on the source ref (see slot_pack_contract_v1
        # §"Forbidden": no embedded body text, body_ref opaque).
        assert ref != entry.source_script_ref
        assert entry.topic not in ref


def test_body_ref_includes_task_id_and_slot_id():
    _, slot_delta = derive_phase_b_deltas(_entry(), TASK_ID)
    for slot in slot_delta["slots"]:
        assert TASK_ID in slot["body_ref"]
        assert slot["slot_id"] in slot["body_ref"]


# --- §5. Slot defaults / language scope -------------------------------


def test_slot_kind_default_is_primary_member():
    _, slot_delta = derive_phase_b_deltas(_entry(), TASK_ID)
    for slot in slot_delta["slots"]:
        assert slot["slot_kind"] == "primary"
        assert slot["slot_kind"] in SLOT_KIND_SET


@pytest.mark.parametrize("target_language", ["mm", "vi"])
def test_slot_language_scope_carries_entry_target_language(target_language: str):
    entry = _entry(target_language=target_language)
    _, slot_delta = derive_phase_b_deltas(entry, TASK_ID)
    for slot in slot_delta["slots"]:
        assert slot["language_scope"] == {
            "source_language": entry.source_language,
            "target_language": [entry.target_language],
        }


def test_slot_length_hint_matches_cell_length_pick():
    variation_delta, slot_delta = derive_phase_b_deltas(
        _entry(variation_target_count=12), TASK_ID
    )
    for cell, slot in zip(variation_delta["cells"], slot_delta["slots"]):
        assert slot["length_hint"] == cell["axis_selections"]["length"]


# --- §6. Forbidden tokens (validator R3 / R5) -------------------------


_FORBIDDEN_TOKENS = (
    "vendor_id",
    "model_id",
    "provider_id",
    "engine_id",
    "delivery_ready",
    "final_ready",
    "publishable",
    "current_attempt",
    # The following must not appear as field names; substring matches are
    # fine (the value `"publishable"` is the field-name guard above).
)
_FORBIDDEN_FIELD_NAMES = (
    "status",
    "ready",
    "done",
    "phase",
    "vendor_id",
    "model_id",
    "provider_id",
    "engine_id",
    "delivery_ready",
    "final_ready",
    "publishable",
    "current_attempt",
)


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item)


def test_no_state_or_vendor_field_in_either_delta():
    variation_delta, slot_delta = derive_phase_b_deltas(_entry(), TASK_ID)
    text = json.dumps([variation_delta, slot_delta], sort_keys=True)
    for token in _FORBIDDEN_TOKENS:
        assert token not in text, f"forbidden token {token!r} present in delta"
    keys = set(_walk_keys({"v": variation_delta, "s": slot_delta}))
    for name in _FORBIDDEN_FIELD_NAMES:
        assert name not in keys, f"forbidden field name {name!r} present"


def test_no_donor_or_cross_line_concept_in_delta():
    variation_delta, slot_delta = derive_phase_b_deltas(_entry(), TASK_ID)
    text = json.dumps([variation_delta, slot_delta], sort_keys=True)
    for token in (
        "donor_",
        "swiftcraft",
        "digital_anchor",
        "hot_follow_business",
        "avatar",
    ):
        assert token not in text


# --- §7. Determinism / purity ----------------------------------------


def test_planner_is_deterministic_same_inputs():
    e = _entry()
    a = derive_phase_b_deltas(e, TASK_ID)
    b = derive_phase_b_deltas(e, TASK_ID)
    assert a == b


def test_planner_does_not_mutate_entry():
    entry = _entry()
    snapshot = replace(entry)
    derive_phase_b_deltas(entry, TASK_ID)
    assert entry == snapshot


def test_planner_outputs_are_independent_calls_share_no_aliasing():
    """Two calls return independent dict trees — mutating one MUST not
    bleed into another. Defends against accidentally returning shared
    constants.
    """
    a_var, a_slot = derive_phase_b_deltas(_entry(), TASK_ID)
    b_var, b_slot = derive_phase_b_deltas(_entry(), TASK_ID)
    a_var["axes"][0]["values"].append("MUTATED")
    a_slot["slots"][0]["language_scope"]["target_language"].append("MUTATED")
    assert "MUTATED" not in b_var["axes"][0]["values"]
    assert "MUTATED" not in b_slot["slots"][0]["language_scope"]["target_language"]


def test_different_task_ids_produce_different_body_refs():
    _, a = derive_phase_b_deltas(_entry(), "task-aaa-001")
    _, b = derive_phase_b_deltas(_entry(), "task-bbb-002")
    assert a["slots"][0]["body_ref"] != b["slots"][0]["body_ref"]


# --- §8. Projector consumption ---------------------------------------


def test_projector_consumes_authored_delta_via_packet_envelope():
    """Build a packet envelope that mirrors what `build_matrix_script_task_payload`
    persists, run the Phase B projector against it, and assert the
    projected variation_plan / copy_bundle are non-empty and match the
    authored deltas exactly. This is the load-bearing assertion linking
    `derive_phase_b_deltas` to the workbench surface.
    """
    from gateway.app.services.matrix_script.workbench_variation_surface import (
        project_workbench_variation_surface,
    )

    entry = _entry(variation_target_count=4)
    variation_delta, slot_delta = derive_phase_b_deltas(entry, TASK_ID)
    packet = {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "path": "docs/contracts/matrix_script/variation_matrix_contract_v1.md",
                "version": "v1",
                "binds_to": ["factory_input_contract_v1"],
                "delta": deepcopy(variation_delta),
            },
            {
                "ref_id": "matrix_script_slot_pack",
                "path": "docs/contracts/matrix_script/slot_pack_contract_v1.md",
                "version": "v1",
                "binds_to": ["factory_language_plan_contract_v1"],
                "delta": deepcopy(slot_delta),
            },
        ],
    }
    projected = project_workbench_variation_surface(packet)
    assert projected["variation_plan"]["axes"] == variation_delta["axes"]
    assert projected["variation_plan"]["cells"] == variation_delta["cells"]
    assert projected["copy_bundle"]["slots"] == slot_delta["slots"]
    assert projected["slot_detail_surface"]["slots"] == slot_delta["slots"]
    # Round-trip through the projector: every cell's script_slot_ref
    # resolves to a slot id the projector also surfaces.
    slot_ids = {s["slot_id"] for s in projected["copy_bundle"]["slots"]}
    for cell in projected["variation_plan"]["cells"]:
        assert cell["script_slot_ref"] in slot_ids
