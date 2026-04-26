"""Reusable envelope fixtures for packet validator tests."""
from __future__ import annotations

from gateway.app.services.packet.envelope import (
    Binding,
    CapabilityPlanItem,
    Evidence,
    GenericRef,
    LineSpecificRef,
    PacketEnvelope,
)


def hot_follow_reference_envelope() -> PacketEnvelope:
    """Minimal envelope shaped after the Hot Follow reference baseline.

    Uses real generic-contract paths so R1 resolves; uses closed-set capability
    kinds so R3/E5 pass; declares a `binds_to` for the line-specific scene_plan
    increment so R2 / E3 pass.
    """
    return PacketEnvelope(
        line_id="hot_follow",
        packet_version="v1",
        generic_refs=[
            GenericRef(
                ref_id="g_input",
                path="docs/contracts/factory_input_contract_v1.md",
                version="v1",
            ),
            GenericRef(
                ref_id="g_scene_plan",
                path="docs/contracts/factory_scene_plan_contract_v1.md",
                version="v1",
            ),
            GenericRef(
                ref_id="g_audio_plan",
                path="docs/contracts/factory_audio_plan_contract_v1.md",
                version="v1",
            ),
            GenericRef(
                ref_id="g_language_plan",
                path="docs/contracts/factory_language_plan_contract_v1.md",
                version="v1",
            ),
            GenericRef(
                ref_id="g_delivery",
                path="docs/contracts/factory_delivery_contract_v1.md",
                version="v1",
            ),
        ],
        line_specific_refs=[
            LineSpecificRef(
                ref_id="hot_follow_scene_plan",
                path="docs/contracts/hot_follow_line_contract.md",
                version="v1",
                binds_to=("g_scene_plan",),
            ),
        ],
        binding=Binding(
            worker_profile_ref="hot_follow_worker_v1",
            deliverable_profile_ref="hot_follow_delivery_v1",
            asset_sink_profile_ref="hot_follow_assets_v1",
            capability_plan=(
                CapabilityPlanItem(kind="understanding"),
                CapabilityPlanItem(kind="subtitles", language_hint="en"),
                CapabilityPlanItem(kind="dub", language_hint="en"),
                CapabilityPlanItem(kind="pack"),
            ),
        ),
        evidence=Evidence(
            reference_line="hot_follow",
            reference_evidence_path="docs/contracts/hot_follow_line_contract.md",
            validator_report_path=None,
            ready_state="ready",
        ),
        metadata={"created_at": "2026-04-25", "created_by": "fixture"},
        line_specific_objects={
            "hot_follow_scene_plan": {"camera_lock": True, "delta_only": True},
        },
    )
