"""OWC-MS PR-2 — Workbench five-panel wiring + isolation tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 + §4 + §5.1 (per-PR file
  isolation contract: matrix_script branch only; Hot Follow / Digital
  Anchor byte-stable).
- ``ENGINEERING_RULES.md`` §13 Product-Flow Module Presence: each
  MS-W3 / MS-W4 / MS-W5 / MS-W6 module must be operator-visible on
  ``task_workbench.html`` matrix_script branch.

Import-light: drives ``build_operator_surfaces_for_workbench`` directly
with hand-built tasks + states. Confirms the four PR-2 panels attach
inside the matrix_script branch and never on Hot Follow / Digital
Anchor / Baseline branches.

What is proved:

1. Matrix Script task: bundle carries
   ``workbench.matrix_script_script_structure`` + ``...preview_compare``
   + ``...review_zone`` + ``...qc_diagnostics`` (PR-U2's
   ``...comprehension`` + ``...variation_surface`` continue to attach).
2. Hot Follow task: bundle carries NONE of the four PR-2 panel keys.
3. Digital Anchor task: bundle carries NONE of the four PR-2 panel keys.
4. Baseline (no line_specific_refs) task: bundle carries NONE of the four
   PR-2 panel keys.
5. ``workbench.matrix_script_qc_diagnostics`` consumes the SAME unified
   ``publish_readiness`` producer the Workbench surface strip consumes
   — head_reason equality across the bundle.
6. The bundle carries no vendor / model / provider / engine identifier
   (validator R3) recursively.
7. The closure read on the workbench path never raises and never
   lazy-creates a closure (read-only).
8. The contract addendum is the only contract change: closure shape
   keys are unchanged after a workbench bundle build.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gateway.app.services.matrix_script import closure_binding
from gateway.app.services.operator_visible_surfaces.wiring import (
    build_operator_surfaces_for_workbench,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "matrix_script"
    / "sample"
    / "matrix_script_packet_v1.sample.json"
)


def _matrix_script_packet() -> dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _matrix_script_task() -> dict[str, Any]:
    packet = _matrix_script_packet()
    return {
        "task_id": "ms_pr2_wiring_001",
        "id": "ms_pr2_wiring_001",
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "current_attempt": {"final_provenance": "current"},
        "packet": packet,
        "line_specific_refs": packet["line_specific_refs"],
        "line_id": "matrix_script",
        "binding": packet.get("binding") or {},
        "config": {
            "line_id": "matrix_script",
            "entry": {
                "topic": "测试主题",
                "source_script_ref": "content://matrix-script/source/mint-aaaa",
                "language_scope": {"source_language": "zh", "target_language": ["mm"]},
                "target_platform": "tiktok",
                "variation_target_count": 2,
                "tone_hint": "casual",
                "audience_hint": "b2c",
                "length_hint": "60",
            },
        },
    }


@pytest.fixture(autouse=True)
def _reset_closure_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


# -- 1. Matrix Script bundle carries all four PR-2 panel keys ----------


def test_matrix_script_bundle_carries_all_four_pr2_panel_keys() -> None:
    task = _matrix_script_task()
    bundle = build_operator_surfaces_for_workbench(
        task=task, authoritative_state={"ready_gate": task["ready_gate"]}
    )
    workbench = bundle.get("workbench") or {}
    # PR-2 panels (MS-W3 / MS-W4 / MS-W5 / MS-W6).
    assert workbench["matrix_script_script_structure"]["is_matrix_script"] is True
    assert workbench["matrix_script_preview_compare"]["is_matrix_script"] is True
    assert workbench["matrix_script_review_zone"]["is_matrix_script"] is True
    assert workbench["matrix_script_qc_diagnostics"]["is_matrix_script"] is True
    # Pre-existing PR-U2 + PR-1 substrate stays attached.
    assert workbench["matrix_script_comprehension"]["is_matrix_script"] is True
    assert "matrix_script_variation_surface" in workbench
    assert workbench["line_specific_panel"]["panel_kind"] == "matrix_script"


# -- 2-4. Non-Matrix-Script bundles carry NONE of the four PR-2 keys ---


def _non_matrix_task(kind: str, packet: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "task_id": f"{kind}_pr2_iso_001",
        "id": f"{kind}_pr2_iso_001",
        "kind": kind,
        "category_key": kind,
        "platform": kind,
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "packet": packet or {"line_id": kind},
        "line_specific_refs": (packet or {}).get("line_specific_refs", []),
        "line_id": kind,
    }


def test_hot_follow_task_bundle_carries_no_pr2_panel_keys() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_non_matrix_task("hot_follow", None),
        authoritative_state={"ready_gate": {"publish_ready": True, "compose_ready": True}},
    )
    workbench = bundle.get("workbench") or {}
    for key in (
        "matrix_script_script_structure",
        "matrix_script_preview_compare",
        "matrix_script_review_zone",
        "matrix_script_qc_diagnostics",
        "matrix_script_comprehension",
        "matrix_script_variation_surface",
    ):
        assert key not in workbench, f"Hot Follow bundle leaked {key}"


def test_digital_anchor_task_bundle_carries_no_pr2_panel_keys() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_non_matrix_task("digital_anchor", None),
        authoritative_state={"ready_gate": {"publish_ready": True, "compose_ready": True}},
    )
    workbench = bundle.get("workbench") or {}
    for key in (
        "matrix_script_script_structure",
        "matrix_script_preview_compare",
        "matrix_script_review_zone",
        "matrix_script_qc_diagnostics",
        "matrix_script_comprehension",
        "matrix_script_variation_surface",
    ):
        assert key not in workbench, f"Digital Anchor bundle leaked {key}"


def test_baseline_task_bundle_carries_no_pr2_panel_keys() -> None:
    # Baseline: no line_specific_refs → resolver yields panel_kind=None.
    bundle = build_operator_surfaces_for_workbench(
        task={"task_id": "baseline_001", "kind": "baseline", "ready_gate": {}},
        authoritative_state={"ready_gate": {}},
    )
    workbench = bundle.get("workbench") or {}
    for key in (
        "matrix_script_script_structure",
        "matrix_script_preview_compare",
        "matrix_script_review_zone",
        "matrix_script_qc_diagnostics",
        "matrix_script_comprehension",
        "matrix_script_variation_surface",
    ):
        assert key not in workbench, f"Baseline bundle leaked {key}"


# -- 5. Cross-surface consistency: head_reason equality ----------------


def test_qc_diagnostics_head_reason_equals_publish_readiness_head_reason() -> None:
    task = _matrix_script_task()
    # Force ready_gate-blocked to exercise non-trivial head_reason.
    task["ready_gate"] = {"publish_ready": False, "compose_ready": True, "blocking": []}
    bundle = build_operator_surfaces_for_workbench(
        task=task, authoritative_state={"ready_gate": task["ready_gate"]}
    )
    workbench = bundle.get("workbench") or {}
    pr_head_reason = bundle["publish_readiness"]["head_reason"]
    qc_head_reason = workbench["matrix_script_qc_diagnostics"][
        "ready_gate_explanation"
    ]["head_reason"]
    assert qc_head_reason == pr_head_reason
    # And Board / Delivery overlays also agree (sanity — covered by the
    # PR-1 surface alignment test, but re-asserted here for the PR-2
    # bundle shape).
    assert bundle["board"]["head_reason"] == pr_head_reason
    assert bundle["delivery"]["publish_gate_head_reason"] == pr_head_reason


# -- 6. Validator R3 recursive sanitize check --------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys_recursively() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_matrix_script_task(),
        authoritative_state={"ready_gate": {"publish_ready": True, "compose_ready": True}},
    )
    forbidden = {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
    }

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value.keys()) & forbidden)
            for v in value.values():
                _walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _walk(v)

    _walk(bundle)


# -- 7. Workbench-side closure read is read-only -----------------------


def test_workbench_bundle_does_not_lazy_create_closure() -> None:
    task = _matrix_script_task()
    # No closure exists yet for this task_id (test fixture wiped the store).
    bundle = build_operator_surfaces_for_workbench(
        task=task, authoritative_state={"ready_gate": task["ready_gate"]}
    )
    # The bundle should attach the review_zone view but the per-variation
    # rows should report no review history (closure absent on read).
    review = bundle["workbench"]["matrix_script_review_zone"]
    for row in review["review_status_rows"]:
        for state in row["per_zone"].values():
            assert state["history_count"] == 0
    # Verify the store still has no closure for this task.
    assert closure_binding.get_closure_view_for_task(task["task_id"]) is None


def test_workbench_bundle_consumes_existing_closure_when_present() -> None:
    task = _matrix_script_task()
    # Pre-create the closure + apply a tagged operator_note.
    closure_binding.get_or_create_for_task(task)
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_note",
            "variation_id": "cell_001",
            "payload": {
                "operator_publish_notes": "字幕需要复核",
                "review_zone": "subtitle",
            },
        },
    )
    bundle = build_operator_surfaces_for_workbench(
        task=task, authoritative_state={"ready_gate": task["ready_gate"]}
    )
    review = bundle["workbench"]["matrix_script_review_zone"]
    cell001 = next(r for r in review["review_status_rows"] if r["variation_id"] == "cell_001")
    assert cell001["per_zone"]["subtitle"]["history_count"] == 1
    assert cell001["per_zone"]["subtitle"]["is_reviewed"] is True


# -- 8. Closure shape keys remain unchanged ----------------------------


def test_workbench_bundle_does_not_widen_closure_envelope_shape() -> None:
    task = _matrix_script_task()
    closure_binding.get_or_create_for_task(task)
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    assert closure is not None
    expected_envelope_keys = {
        "surface",
        "closure_id",
        "line_id",
        "packet_version",
        "variation_feedback",
        "feedback_closure_records",
    }
    # Building the workbench bundle MUST NOT widen the closure envelope.
    build_operator_surfaces_for_workbench(
        task=task, authoritative_state={"ready_gate": task["ready_gate"]}
    )
    closure_after = closure_binding.get_closure_view_for_task(task["task_id"])
    assert closure_after is not None
    assert set(closure_after.keys()) == expected_envelope_keys
