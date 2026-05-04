"""Regression tests for the unified publish_readiness producer
(Operator Capability Recovery, PR-1).

Authority:
- ``docs/contracts/publish_readiness_contract_v1.md``
- ``docs/contracts/factory_delivery_contract_v1.md``
  §"Per-Deliverable Required / Blocking Fields (Plan D Amendment)"
  §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)"
- ``docs/contracts/l4_advisory_producer_output_contract_v1.md``
- ``docs/contracts/hot_follow_current_attempt_contract_v1.md``
  §"`final_provenance` Field (Plan D Amendment)"
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §4

Discipline:
- Pure-projection tests; no FastAPI app instantiation.
- Closed `head_reason` enum is exhaustively tested.
- Single-source consistency: legacy `derive_board_publishable` and
  `derive_delivery_publish_gate` agree with the producer for the same inputs.
- Vendor / model / provider keys never appear in producer output.
"""
from __future__ import annotations

import pytest

from gateway.app.services.operator_visible_surfaces import (
    CLOSED_HEAD_REASON_ENUM,
    compute_publish_readiness,
    derive_board_publishable,
    derive_delivery_publish_gate,
    emit_advisories,
)
from gateway.app.services.operator_visible_surfaces.publish_readiness import (
    HEAD_REASON_COMPOSE_NOT_READY,
    HEAD_REASON_FINAL_MISSING,
    HEAD_REASON_FINAL_PROVENANCE_HISTORICAL,
    HEAD_REASON_FINAL_STALE,
    HEAD_REASON_PUBLISHABLE_OK,
    HEAD_REASON_PUBLISH_NOT_READY,
    HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING,
    HEAD_REASON_REQUIRED_DELIVERABLE_MISSING,
)


# ---------- Output shape conformance --------------------------------------


def test_output_shape_is_closed_per_contract() -> None:
    result = compute_publish_readiness(ready_gate={}, l2_facts={})
    assert set(result.keys()) == {
        "publishable",
        "head_reason",
        "blocking_advisories",
        "consumed_inputs",
    }
    assert isinstance(result["publishable"], bool)
    assert isinstance(result["blocking_advisories"], list)
    consumed = result["consumed_inputs"]
    assert set(consumed.keys()) == {
        "ready_gate_publish_ready",
        "ready_gate_compose_ready",
        "final_fresh",
        "final_provenance",
        "blocking_count",
    }


def test_head_reason_is_always_in_closed_enum() -> None:
    inputs = [
        ({}, {}),
        ({"publish_ready": True, "compose_ready": True}, {"final": {"exists": True}}),
        ({"blocking": ["voiceover_missing"]}, {}),
        ({"publish_ready": False, "compose_ready": True}, {"final": {"exists": True}}),
        ({"publish_ready": True, "compose_ready": False}, {"final": {"exists": True}}),
        ({"publish_ready": True, "compose_ready": True}, {"final": {"exists": False}}),
        (
            {"publish_ready": True, "compose_ready": True},
            {"final": {"exists": True}, "final_stale_reason": "subtitle_changed"},
        ),
    ]
    for ready_gate, l2_facts in inputs:
        result = compute_publish_readiness(ready_gate=ready_gate, l2_facts=l2_facts)
        if result["head_reason"] is not None:
            assert result["head_reason"] in CLOSED_HEAD_REASON_ENUM or (
                # The producer copies the first ready_gate.blocking[] entry
                # verbatim per contract; that string is the head reason.
                ready_gate.get("blocking")
                and result["head_reason"] == ready_gate["blocking"][0]
            )


# ---------- publishable=true happy path -----------------------------------


def test_publishable_true_when_gate_green_and_final_fresh() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True, "blocking": []},
        l2_facts={"final": {"exists": True}, "final_stale_reason": None},
    )
    assert result["publishable"] is True
    assert result["head_reason"] == HEAD_REASON_PUBLISHABLE_OK


# ---------- ready_gate.blocking dominates ----------------------------------


def test_ready_gate_blocking_first_entry_becomes_head_reason() -> None:
    result = compute_publish_readiness(
        ready_gate={
            "publish_ready": True,
            "compose_ready": True,
            "blocking": ["voiceover_missing", "compose_not_done"],
        },
        l2_facts={"final": {"exists": True}},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == "voiceover_missing"
    assert result["consumed_inputs"]["blocking_count"] == 2


# ---------- final_missing / final_stale ------------------------------------


def test_final_missing_when_l2_provided_with_no_final() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": False}},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_FINAL_MISSING


def test_final_stale_when_stale_reason_present() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}, "final_stale_reason": "subtitle_changed"},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_FINAL_STALE


# ---------- publish_not_ready / compose_not_ready --------------------------


def test_publish_not_ready_when_publish_ready_false() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": False, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_PUBLISH_NOT_READY


def test_compose_not_ready_when_only_compose_false() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": False},
        l2_facts={"final": {"exists": True}},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_COMPOSE_NOT_READY


# ---------- final_provenance_historical ------------------------------------


def test_final_provenance_historical_blocks_publish() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        l3_current_attempt={"final_provenance": "historical"},
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_FINAL_PROVENANCE_HISTORICAL
    assert result["consumed_inputs"]["final_provenance"] == "historical"


def test_final_provenance_current_does_not_block() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        l3_current_attempt={"final_provenance": "current"},
    )
    assert result["publishable"] is True
    assert result["consumed_inputs"]["final_provenance"] == "current"


# ---------- delivery_rows: required / blocking_publish ---------------------


def test_required_deliverable_missing_blocks_publish() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        delivery_rows=[
            {
                "kind": "variation_manifest",
                "required": True,
                "blocking_publish": True,
                "artifact_lookup": {"status": "unresolved"},
            }
        ],
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_REQUIRED_DELIVERABLE_MISSING


def test_blocking_publish_unresolved_blocks_publish() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        delivery_rows=[
            {
                "kind": "subtitle_bundle",
                "required": False,
                "blocking_publish": True,  # Will be clamped only when scene_pack
                "artifact_lookup": {"status": "unresolved"},
            }
        ],
    )
    assert result["publishable"] is False
    assert result["head_reason"] == HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING


def test_resolved_required_row_does_not_block() -> None:
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        delivery_rows=[
            {
                "kind": "variation_manifest",
                "required": True,
                "blocking_publish": True,
                "artifact_lookup": {"status": "resolved"},
            }
        ],
    )
    assert result["publishable"] is True


# ---------- scene_pack non-blocking rule (defensive clamp) -----------------


def test_scene_pack_blocking_publish_true_is_clamped_off() -> None:
    """A malformed scene_pack row asserting blocking_publish=true must NOT
    reach the producer's blocking decision per
    `factory_delivery_contract_v1.md` §"Scene-Pack Non-Blocking Rule".
    """
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        delivery_rows=[
            {
                "kind": "scene_pack",
                "required": True,
                "blocking_publish": True,
                "artifact_lookup": {"status": "unresolved"},
            }
        ],
    )
    assert result["publishable"] is True
    assert result["head_reason"] == HEAD_REASON_PUBLISHABLE_OK


# ---------- Single-producer rule: legacy wrappers agree -------------------


def test_legacy_board_wrapper_agrees_with_producer() -> None:
    gate = {"publish_ready": True, "compose_ready": True}
    legacy = derive_board_publishable(gate)
    direct = compute_publish_readiness(ready_gate=gate, l2_facts=None)
    assert legacy["publishable"] == direct["publishable"]
    assert legacy["head_reason"] == direct["head_reason"]


def test_legacy_delivery_wrapper_agrees_with_producer() -> None:
    gate = {"publish_ready": True, "compose_ready": True}
    l2 = {"final": {"exists": True}}
    legacy = derive_delivery_publish_gate(gate, l2)
    direct = compute_publish_readiness(ready_gate=gate, l2_facts=l2)
    assert legacy["publish_gate"] == direct["publishable"]
    assert legacy["publish_gate_head_reason"] == direct["head_reason"]


def test_legacy_delivery_wrapper_passes_l3_and_rows() -> None:
    legacy = derive_delivery_publish_gate(
        {"publish_ready": True, "compose_ready": True},
        {"final": {"exists": True}},
        l3_current_attempt={"final_provenance": "historical"},
        delivery_rows=None,
    )
    assert legacy["publish_gate"] is False
    assert legacy["publish_gate_head_reason"] == HEAD_REASON_FINAL_PROVENANCE_HISTORICAL


# ---------- No vendor/model/provider keys leak ----------------------------


def test_no_forbidden_operator_keys_in_output() -> None:
    forbidden = {"vendor_id", "model_id", "provider", "provider_id", "engine_id"}
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True, "vendor_id": "x"},
        l2_facts={"final": {"exists": True, "model_id": "y"}, "provider_id": "z"},
        l3_current_attempt={"final_provenance": "current", "engine_id": "e"},
    )

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in forbidden, f"forbidden key leaked: {k}"
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(result)


# ---------- Advisory emitter ----------------------------------------------


def test_advisory_emitter_returns_empty_when_no_input() -> None:
    assert emit_advisories({}, {}) == []


def test_advisory_emitter_final_ready_when_gate_green_and_final_fresh() -> None:
    advisories = emit_advisories(
        {"final_fresh": True},
        {"publish_ready": True, "compose_ready": True},
    )
    assert len(advisories) == 1
    assert advisories[0]["id"] == "hf_advisory_final_ready"
    assert advisories[0]["kind"] == "operator_guidance"


def test_advisory_emitter_translation_waiting() -> None:
    advisories = emit_advisories(
        {"subtitle_translation_waiting_retryable": True},
        {"publish_ready": False, "compose_ready": False},
    )
    ids = [a["id"] for a in advisories]
    assert "hf_advisory_translation_waiting_retryable" in ids


def test_advisory_emitter_no_dub_route_terminal() -> None:
    advisories = emit_advisories(
        {
            "no_dub_route_terminal": True,
            "selected_compose_route": "preserve_source_route",
        },
        {"publish_ready": False, "compose_ready": False},
    )
    ids = [a["id"] for a in advisories]
    assert "hf_advisory_no_dub_route_terminal" in ids


def test_advisory_emitter_only_emits_closed_taxonomy_ids() -> None:
    closed = {
        "hf_advisory_translation_waiting_retryable",
        "hf_advisory_final_ready",
        "hf_advisory_retriable_dub_failure",
        "hf_advisory_no_dub_route_terminal",
    }
    cases = [
        ({}, {}),
        ({"final_fresh": True}, {"publish_ready": True, "compose_ready": True}),
        ({"subtitle_translation_waiting_retryable": True}, {}),
        ({"retriable_dub_failure": True}, {}),
        (
            {"no_dub_route_terminal": True, "selected_compose_route": "bgm_only_route"},
            {},
        ),
    ]
    for l3, gate in cases:
        for advisory in emit_advisories(l3, gate):
            assert advisory["id"] in closed


# ---------- Producer purity: no input mutation ----------------------------


def test_producer_does_not_mutate_inputs() -> None:
    gate = {"publish_ready": True, "compose_ready": True, "blocking": []}
    facts = {"final": {"exists": True}}
    l3 = {"final_provenance": "current"}
    rows = [{"kind": "variation_manifest", "required": True, "blocking_publish": True, "artifact_lookup": {"status": "resolved"}}]
    snapshot_gate = dict(gate)
    snapshot_facts = dict(facts)
    snapshot_l3 = dict(l3)
    snapshot_rows = [dict(r) for r in rows]

    compute_publish_readiness(ready_gate=gate, l2_facts=facts, l3_current_attempt=l3, delivery_rows=rows)

    assert gate == snapshot_gate
    assert facts == snapshot_facts
    assert l3 == snapshot_l3
    assert rows == snapshot_rows
