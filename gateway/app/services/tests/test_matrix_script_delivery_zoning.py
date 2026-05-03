"""Per-deliverable required / blocking_publish zoning tests for Matrix Script Delivery Center
(Plan E PR-3, Item E.MS.3).

Authority:
- ``docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md`` §3.3 / §5.3 / §5.4 / §6 row A3
- ``docs/contracts/factory_delivery_contract_v1.md``
  §"Per-Deliverable Required / Blocking Fields (Plan D Amendment)"
  §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)"
- ``docs/contracts/matrix_script/delivery_binding_contract_v1.md``

Discipline (per gate spec §5.4 PR-3 regression scope):
- Matrix Script Delivery Center renders ``required`` / ``blocking_publish`` zoning
  correctly per row kind on a fresh contract-clean sample.
- Scene-pack-style derivative is rendered as ``optional, never blocks publish``,
  even when the underlying line capability would suggest otherwise.
- Hot Follow Delivery Center unchanged — verified at the file-fence level (no
  Hot Follow file in PR-3 diff; outside the test process; recorded in the
  execution log).
- Validator invariant from the contract — ``required=false ⇒ blocking_publish=false``
  — holds across every row.

Import-light by design: calls ``project_delivery_binding`` directly without
instantiating the FastAPI app, so it runs cleanly on both Python 3.9 and 3.10+.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from gateway.app.services.matrix_script.delivery_binding import (
    SCENE_PACK_BLOCKING_ALLOWED,
    _clamp_blocking_publish,
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


# ---------------------------------------------------------------------------
# Per-row zoning on the canonical Matrix Script sample
# ---------------------------------------------------------------------------


def _rows_by_id(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surface = project_delivery_binding(packet)
    return {row["deliverable_id"]: row for row in surface["delivery_pack"]["deliverables"]}


def test_variation_manifest_is_required_and_blocks_publish(sample_packet: dict[str, Any]) -> None:
    row = _rows_by_id(sample_packet)["matrix_script_variation_manifest"]
    assert row["required"] is True
    assert row["blocking_publish"] is True


def test_slot_bundle_is_required_and_blocks_publish(sample_packet: dict[str, Any]) -> None:
    row = _rows_by_id(sample_packet)["matrix_script_slot_bundle"]
    assert row["required"] is True
    assert row["blocking_publish"] is True


def test_subtitle_bundle_zoning_follows_subtitles_capability_required_flag(
    sample_packet: dict[str, Any],
) -> None:
    """Matrix Script line policy: subtitle_bundle.required mirrors the line capability;
    blocking_publish mirrors required."""
    rows = _rows_by_id(sample_packet)
    subtitle = rows["matrix_script_subtitle_bundle"]
    # The canonical sample asserts subtitles.required=True.
    assert subtitle["required"] is True
    assert subtitle["blocking_publish"] is True


def test_audio_preview_zoning_follows_dub_capability_required_flag(
    sample_packet: dict[str, Any],
) -> None:
    """Matrix Script line policy: audio_preview.required mirrors the line capability;
    blocking_publish mirrors required (clamps to False if required is False)."""
    rows = _rows_by_id(sample_packet)
    audio = rows["matrix_script_audio_preview"]
    # The canonical sample asserts dub.required=False.
    assert audio["required"] is False
    assert audio["blocking_publish"] is False


def test_scene_pack_is_optional_and_never_blocks_publish(sample_packet: dict[str, Any]) -> None:
    """Per ``factory_delivery_contract_v1.md`` §"Scene-Pack Non-Blocking Rule":
    every line MUST emit scene_pack as required=False AND blocking_publish=False,
    independent of any per-task capability flag."""
    rows = _rows_by_id(sample_packet)
    scene_pack = rows["matrix_script_scene_pack"]
    assert scene_pack["kind"] == "scene_pack"
    assert scene_pack["required"] is False
    assert scene_pack["blocking_publish"] is False


# ---------------------------------------------------------------------------
# Validator invariant: required=false ⇒ blocking_publish=false (every row)
# ---------------------------------------------------------------------------


def test_no_row_violates_required_false_implies_blocking_publish_false(
    sample_packet: dict[str, Any],
) -> None:
    rows = _rows_by_id(sample_packet)
    for row in rows.values():
        if row["required"] is False:
            assert row["blocking_publish"] is False, (
                f"row {row['deliverable_id']} violates "
                f"`required=false ⇒ blocking_publish=false` invariant"
            )


def test_clamp_blocking_publish_returns_false_when_required_is_false() -> None:
    assert _clamp_blocking_publish(required=False, blocking_publish=True) is False
    assert _clamp_blocking_publish(required=False, blocking_publish=False) is False


def test_clamp_blocking_publish_passes_through_when_required_is_true() -> None:
    assert _clamp_blocking_publish(required=True, blocking_publish=True) is True
    assert _clamp_blocking_publish(required=True, blocking_publish=False) is False


# ---------------------------------------------------------------------------
# Scene-pack contract enforcement is independent of capability flags
# ---------------------------------------------------------------------------


def test_scene_pack_stays_optional_even_if_pack_capability_marks_required(
    sample_packet: dict[str, Any],
) -> None:
    """Adversarial: even if a malformed packet asserts pack capability required=True,
    the scene_pack delivery row MUST still emit required=False AND blocking_publish=False
    per the Scene-Pack Non-Blocking Rule. The contract is line-uniform."""
    adversarial = copy.deepcopy(sample_packet)
    capability_plan = adversarial["binding"]["capability_plan"]
    pack_seen = False
    for entry in capability_plan:
        if entry.get("kind") == "pack":
            entry["required"] = True
            pack_seen = True
    if not pack_seen:
        capability_plan.append({"kind": "pack", "mode": "bundle", "required": True})

    row = _rows_by_id(adversarial)["matrix_script_scene_pack"]
    assert row["required"] is False
    assert row["blocking_publish"] is False


def test_scene_pack_blocking_allowed_constant_is_false() -> None:
    """The module-level constant pinning the contract rule MUST stay False.
    Any future widening requires a contract amendment, not a flip here."""
    assert SCENE_PACK_BLOCKING_ALLOWED is False


# ---------------------------------------------------------------------------
# Subtitles + dub capability flag negative-path zoning
# ---------------------------------------------------------------------------


def test_subtitle_bundle_collapses_to_optional_when_capability_marks_not_required(
    sample_packet: dict[str, Any],
) -> None:
    flipped = copy.deepcopy(sample_packet)
    for entry in flipped["binding"]["capability_plan"]:
        if entry.get("kind") == "subtitles":
            entry["required"] = False
    row = _rows_by_id(flipped)["matrix_script_subtitle_bundle"]
    assert row["required"] is False
    assert row["blocking_publish"] is False


def test_audio_preview_promotes_to_required_when_capability_marks_required(
    sample_packet: dict[str, Any],
) -> None:
    flipped = copy.deepcopy(sample_packet)
    dub_seen = False
    for entry in flipped["binding"]["capability_plan"]:
        if entry.get("kind") == "dub":
            entry["required"] = True
            dub_seen = True
    if not dub_seen:
        flipped["binding"]["capability_plan"].append({"kind": "dub", "mode": "tts", "required": True})
    row = _rows_by_id(flipped)["matrix_script_audio_preview"]
    assert row["required"] is True
    assert row["blocking_publish"] is True


# ---------------------------------------------------------------------------
# Surface integration: zoning is observable on the JSON-rendered Matrix Script payload
# ---------------------------------------------------------------------------


def test_rendered_surface_carries_blocking_publish_on_every_row(sample_packet: dict[str, Any]) -> None:
    surface = project_delivery_binding(sample_packet)
    rendered = json.dumps(surface)
    # Every row must carry the additive zoning field; sentinel keys still present
    # from PR-1 (artifact_lookup) remain present too.
    for row in surface["delivery_pack"]["deliverables"]:
        assert "blocking_publish" in row
        assert isinstance(row["blocking_publish"], bool)
    assert '"blocking_publish":' in rendered


def test_rendered_surface_does_not_introduce_provider_vendor_keys(sample_packet: dict[str, Any]) -> None:
    """Validator R3 alignment: the new zoning fields are pure scalar booleans;
    no vendor / model / provider / engine identifier creeps into the row shape."""
    rendered = json.dumps(project_delivery_binding(sample_packet)).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert forbidden not in rendered


def test_rendered_surface_preserves_PR1_artifact_lookup_field(sample_packet: dict[str, Any]) -> None:
    """Cross-PR sanity: PR-3 must not regress PR-1's `not_implemented_phase_c` retirement.
    The `artifact_lookup` field on every row must still be either the contract sentinel
    string or a real ArtifactHandle mapping — never the legacy phase-C placeholder."""
    rendered = json.dumps(project_delivery_binding(sample_packet))
    assert "not_implemented_phase_c" not in rendered
    for row in project_delivery_binding(sample_packet)["delivery_pack"]["deliverables"]:
        assert "artifact_lookup" in row


def test_top_level_surface_shape_unchanged(sample_packet: dict[str, Any]) -> None:
    """PR-3 only extends row shape; the top-level projection key set is unchanged."""
    surface = project_delivery_binding(sample_packet)
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
