"""OWC-MS PR-2 — Matrix Script Workbench E 质检与诊断区 view tests (MS-W6).

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W6 (render PR-1 L4
  advisory_emitter output; pure presentation; no advisory rule change).
- ``docs/contracts/publish_readiness_contract_v1.md`` (closed
  ``head_reason`` enum; ``blocking_advisories[]`` from L4 emitter).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1E.

Import-light: exercises the pure helper
``derive_matrix_script_qc_diagnostics_view`` over hand-built unified
``publish_readiness`` outputs, ``delivery_comprehension`` outputs, and
variation surface slot length hints.

What is proved:

1. Returns ``{}`` for non-Matrix-Script panels.
2. ``ready_gate_explanation`` reads ``publishable``,
   ``head_reason`` (closed enum), ``consumed_inputs.first_blocking_reason``,
   ``ready_gate_publish_ready`` / ``compose_ready`` / ``final_fresh`` /
   ``final_provenance`` / ``blocking_count`` from publish_readiness ONLY.
3. ``head_reason`` translation covers the closed enum; unknown codes
   fall through verbatim.
4. ``risk_items`` mirror ``publish_readiness.blocking_advisories[]``
   verbatim — no new advisory id / hint / evidence_field.
5. ``compliance_items`` enumerate the operator-visible surface red lines
   (no provider controls; no Phase B authoring).
6. ``quality_items`` always emit three rows (duration / clarity /
   subtitle_readability); duration observed from slot.length_hint;
   the other two render the ``unobservable_pending_upstream`` sentinel
   with operator-language explanation.
7. ``artifact_status_items`` flatten delivery_comprehension lanes into
   operator-language rows; no new contract field invented.
8. ``publish_blocking_explanation`` is the same shape Delivery Center
   emits — cross-surface consistency.
9. Validator R3 alignment.
10. Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from gateway.app.services.matrix_script.qc_diagnostics_view import (
    HEAD_REASON_LABELS_ZH,
    QUALITY_STATUS_OBSERVED,
    QUALITY_STATUS_UNOBSERVABLE,
    derive_matrix_script_qc_diagnostics_view,
)


def _matrix_script_panel() -> dict[str, Any]:
    return {"panel_kind": "matrix_script"}


def _publish_readiness(
    *,
    publishable: bool = True,
    head_reason: str = "publishable_ok",
    blocking_advisories: list[dict[str, Any]] | None = None,
    publish_ready: bool = True,
    compose_ready: bool = True,
    final_fresh: bool = True,
    final_provenance: str | None = "current",
    blocking_count: int = 0,
    first_blocking_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "publishable": publishable,
        "head_reason": head_reason,
        "blocking_advisories": list(blocking_advisories or []),
        "consumed_inputs": {
            "ready_gate_publish_ready": publish_ready,
            "ready_gate_compose_ready": compose_ready,
            "final_fresh": final_fresh,
            "final_provenance": final_provenance,
            "blocking_count": blocking_count,
            "first_blocking_reason": first_blocking_reason,
        },
    }


def _delivery_comprehension(
    *,
    rows_required_blocking: list[dict[str, Any]] | None = None,
    rows_optional_non_blocking: list[dict[str, Any]] | None = None,
    publish_blocking: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "is_matrix_script": True,
        "lanes": {
            "required_blocking": {
                "lane_label_zh": "必交付 · 阻塞发布",
                "rows": rows_required_blocking
                or [
                    {
                        "deliverable_id": "matrix_script_variation_manifest",
                        "kind": "variation_manifest",
                        "kind_label_zh": "变体清单",
                        "required": True,
                        "blocking_publish": True,
                        "artifact_status_code": "current_fresh",
                        "artifact_status_label_zh": "当前 · 最新",
                        "artifact_status_explanation_zh": "当前尝试的产出，可发布。",
                    }
                ],
            },
            "required_non_blocking": {
                "lane_label_zh": "必交付 · 不阻塞发布",
                "rows": [],
            },
            "optional_non_blocking": {
                "lane_label_zh": "可选 · 不阻塞发布",
                "rows": rows_optional_non_blocking or [],
            },
        },
        "publish_blocking_explanation": publish_blocking
        or {
            "is_blocked": False,
            "reason_label_zh": "所有必交付物均已就绪，发布按钮可启用。",
            "blocking_rows": [],
        },
    }


def _variation_surface(*, slots: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if slots is None:
        slots = [
            {"slot_id": "slot_001", "length_hint": 30},
            {"slot_id": "slot_002", "length_hint": 60},
            {"slot_id": "slot_003", "length_hint": 120},
        ]
    return {"copy_bundle": {"slots": slots}}


# -- 1. Non-Matrix-Script panel returns empty ---------------------------


@pytest.mark.parametrize("panel_kind", ["hot_follow", "digital_anchor", "baseline", "", None])
def test_non_matrix_script_panel_returns_empty(panel_kind: Any) -> None:
    panel = {"panel_kind": panel_kind}
    assert (
        derive_matrix_script_qc_diagnostics_view(
            _publish_readiness(),
            _delivery_comprehension(),
            _variation_surface(),
            panel,
        )
        == {}
    )


# -- 2. ready_gate_explanation reads from publish_readiness only --------


def test_ready_gate_explanation_passes_through_publish_readiness_inputs() -> None:
    pr = _publish_readiness(
        publishable=False,
        head_reason="required_deliverable_missing",
        publish_ready=False,
        compose_ready=True,
        final_fresh=True,
        final_provenance="current",
        blocking_count=2,
        first_blocking_reason="voiceover_missing",
    )
    bundle = derive_matrix_script_qc_diagnostics_view(
        pr, _delivery_comprehension(), _variation_surface(), _matrix_script_panel()
    )
    rg = bundle["ready_gate_explanation"]
    assert rg["publishable"] is False
    assert rg["head_reason"] == "required_deliverable_missing"
    assert rg["publish_ready"] is False
    assert rg["compose_ready"] is True
    assert rg["final_fresh"] is True
    assert rg["final_provenance"] == "current"
    assert rg["blocking_count"] == 2
    assert rg["first_blocking_reason_raw"] == "voiceover_missing"


# -- 3. head_reason translation -----------------------------------------


@pytest.mark.parametrize("code", sorted(HEAD_REASON_LABELS_ZH.keys()))
def test_head_reason_known_codes_translate(code: str) -> None:
    pr = _publish_readiness(head_reason=code, publishable=(code == "publishable_ok"))
    bundle = derive_matrix_script_qc_diagnostics_view(
        pr, _delivery_comprehension(), _variation_surface(), _matrix_script_panel()
    )
    assert (
        bundle["ready_gate_explanation"]["head_reason_label_zh"]
        == HEAD_REASON_LABELS_ZH[code]
    )


def test_head_reason_unknown_falls_through_verbatim() -> None:
    pr = _publish_readiness(head_reason="some_future_code", publishable=False)
    bundle = derive_matrix_script_qc_diagnostics_view(
        pr, _delivery_comprehension(), _variation_surface(), _matrix_script_panel()
    )
    assert (
        bundle["ready_gate_explanation"]["head_reason_label_zh"] == "some_future_code"
    )


# -- 4. risk_items mirror blocking_advisories verbatim ------------------


def test_risk_items_mirror_publish_readiness_blocking_advisories() -> None:
    advisories = [
        {
            "id": "hf_advisory_translation_waiting_retryable",
            "kind": "operator_guidance",
            "level": "info",
            "operator_hint": "subtitle translation still pending",
            "explanation": "等待翻译返回",
            "recommended_next_action": "wait_or_retry_translation",
        }
    ]
    pr = _publish_readiness(
        publishable=False,
        head_reason="publish_not_ready",
        blocking_advisories=advisories,
    )
    bundle = derive_matrix_script_qc_diagnostics_view(
        pr, _delivery_comprehension(), _variation_surface(), _matrix_script_panel()
    )
    assert len(bundle["risk_items"]) == 1
    item = bundle["risk_items"][0]
    assert item["advisory_id"] == "hf_advisory_translation_waiting_retryable"
    assert item["operator_hint"] == "subtitle translation still pending"
    assert item["recommended_next_action"] == "wait_or_retry_translation"


def test_risk_items_empty_when_no_advisories() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(),
        _matrix_script_panel(),
    )
    assert bundle["risk_items"] == []


# -- 5. compliance_items enumerate the closed reminders ----------------


def test_compliance_items_enumerate_no_provider_and_no_phase_b_reminders() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(),
        _matrix_script_panel(),
    )
    ids = [c["compliance_id"] for c in bundle["compliance_items"]]
    assert "no_provider_controls" in ids
    assert "no_phase_b_authoring" in ids


# -- 6. quality_items always three; duration observed; others gated ----


def test_quality_items_always_three_rows() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(),
        _matrix_script_panel(),
    )
    ids = [q["quality_id"] for q in bundle["quality_items"]]
    assert ids == ["duration", "clarity", "subtitle_readability"]


def test_quality_items_duration_observed_from_slot_length_hint() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(
            slots=[
                {"slot_id": "s1", "length_hint": 30},
                {"slot_id": "s2", "length_hint": 60},
                {"slot_id": "s3", "length_hint": 90},
            ]
        ),
        _matrix_script_panel(),
    )
    duration = next(q for q in bundle["quality_items"] if q["quality_id"] == "duration")
    assert duration["status_code"] == QUALITY_STATUS_OBSERVED
    assert duration["value"] == {
        "min_seconds": 30,
        "max_seconds": 90,
        "average_seconds": 60.0,
        "sample_count": 3,
    }


def test_quality_items_duration_unobservable_when_no_slots_with_length_hint() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(slots=[]),
        _matrix_script_panel(),
    )
    duration = next(q for q in bundle["quality_items"] if q["quality_id"] == "duration")
    assert duration["status_code"] == QUALITY_STATUS_UNOBSERVABLE
    assert duration["value"] is None


def test_quality_items_clarity_and_subtitle_readability_unobservable() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(),
        _matrix_script_panel(),
    )
    for q_id in ("clarity", "subtitle_readability"):
        item = next(q for q in bundle["quality_items"] if q["quality_id"] == q_id)
        assert item["status_code"] == QUALITY_STATUS_UNOBSERVABLE
        assert item["value"] is None


# -- 7. artifact_status_items flatten delivery_comprehension lanes -----


def test_artifact_status_items_flatten_lanes_into_rows() -> None:
    comprehension = _delivery_comprehension(
        rows_required_blocking=[
            {
                "deliverable_id": "matrix_script_variation_manifest",
                "kind": "variation_manifest",
                "kind_label_zh": "变体清单",
                "required": True,
                "blocking_publish": True,
                "artifact_status_code": "current_fresh",
                "artifact_status_label_zh": "当前 · 最新",
                "artifact_status_explanation_zh": "当前尝试的产出。",
            },
            {
                "deliverable_id": "matrix_script_slot_bundle",
                "kind": "script_slot_bundle",
                "kind_label_zh": "脚本 slot 包",
                "required": True,
                "blocking_publish": True,
                "artifact_status_code": "unresolved",
                "artifact_status_label_zh": "尚未解析",
                "artifact_status_explanation_zh": "未在 L2 找到匹配工件。",
            },
        ],
        rows_optional_non_blocking=[
            {
                "deliverable_id": "matrix_script_scene_pack",
                "kind": "scene_pack",
                "kind_label_zh": "配套素材包（场景）",
                "required": False,
                "blocking_publish": False,
                "artifact_status_code": "unresolved",
                "artifact_status_label_zh": "尚未解析",
                "artifact_status_explanation_zh": "—",
            }
        ],
    )
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        comprehension,
        _variation_surface(),
        _matrix_script_panel(),
    )
    items = bundle["artifact_status_items"]
    assert {it["deliverable_id"] for it in items} == {
        "matrix_script_variation_manifest",
        "matrix_script_slot_bundle",
        "matrix_script_scene_pack",
    }
    scene = next(
        it for it in items if it["deliverable_id"] == "matrix_script_scene_pack"
    )
    assert scene["lane_id"] == "optional_non_blocking"
    assert scene["required"] is False


# -- 8. publish_blocking_explanation passthrough ------------------------


def test_publish_blocking_explanation_passes_through_from_comprehension() -> None:
    comprehension = _delivery_comprehension(
        publish_blocking={
            "is_blocked": True,
            "reason_label_zh": "必交付物未就绪。",
            "blocking_rows": [
                {
                    "deliverable_id": "matrix_script_slot_bundle",
                    "kind_label_zh": "脚本 slot 包",
                    "artifact_status_label_zh": "尚未解析",
                }
            ],
        }
    )
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        comprehension,
        _variation_surface(),
        _matrix_script_panel(),
    )
    assert bundle["publish_blocking_explanation"]["is_blocked"] is True
    assert (
        bundle["publish_blocking_explanation"]["blocking_rows"][0]["deliverable_id"]
        == "matrix_script_slot_bundle"
    )


# -- 9. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_qc_diagnostics_view(
        _publish_readiness(),
        _delivery_comprehension(),
        _variation_surface(),
        _matrix_script_panel(),
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


# -- 10. Helper does not mutate inputs ---------------------------------


def test_helper_does_not_mutate_inputs() -> None:
    pr = _publish_readiness()
    comprehension = _delivery_comprehension()
    surface = _variation_surface()
    snap_pr = deepcopy(pr)
    snap_comprehension = deepcopy(comprehension)
    snap_surface = deepcopy(surface)
    derive_matrix_script_qc_diagnostics_view(
        pr, comprehension, surface, _matrix_script_panel()
    )
    assert pr == snap_pr
    assert comprehension == snap_comprehension
    assert surface == snap_surface
