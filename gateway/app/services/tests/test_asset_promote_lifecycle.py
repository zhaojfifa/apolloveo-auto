"""Promote intent + closure lifecycle tests
(Operator Capability Recovery, PR-2).

Authority:
- ``docs/contracts/promote_request_contract_v1.md``
- ``docs/contracts/promote_feedback_closure_contract_v1.md``

Discipline: import-light. Service-level only; no FastAPI app.
"""
from __future__ import annotations

import pytest

from gateway.app.services.asset import (
    EVENT_KIND_ENUM,
    PromoteRequestRejected,
    REJECTION_REASON_ENUM,
    REQUEST_STATE_ENUM,
    approve_request,
    get_closure,
    list_closures,
    reject_request,
    reset_store_for_tests,
    submit_promote_request,
    withdraw_request,
)


@pytest.fixture(autouse=True)
def _reset_store():
    reset_store_for_tests()
    yield
    reset_store_for_tests()


_VALID_PAYLOAD: dict = {
    "artifact_ref": "artifact://hot_follow/task-001/final.mp4",
    "target_kind": "broll",
    "target_tags": [
        {"facet": "line", "value": "hot_follow"},
        {"facet": "scene", "value": "outdoor"},
    ],
    "target_line_availability": ["hot_follow"],
    "license_metadata": {
        "license": "owned",
        "reuse_policy": "reuse_allowed",
        "source": "task_artifact_promote",
        "source_label": "Hot Follow task 001",
    },
    "proposed_title": "City Outdoor B-roll",
    "requested_by": "operator:demo",
    "operator_notes": "Looks reusable across HF tasks.",
}


# ---------- Submit happy path --------------------------------------------


def test_submit_returns_request_id_and_initial_requested_state() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    assert "request_id" in result
    assert result["request_state"] == "requested"
    assert result["request_state"] in REQUEST_STATE_ENUM
    # Per request contract: asset_id MUST NOT be returned synchronously.
    assert "asset_id" not in result
    assert "resulting_asset_id" not in result


def test_submit_creates_closure_with_submitted_event() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    closure = get_closure(result["request_id"])
    assert closure is not None
    assert closure["request_state"] == "requested"
    assert closure["request_id"] == result["request_id"]
    assert closure["artifact_ref"] == _VALID_PAYLOAD["artifact_ref"]
    assert closure["resulting_asset_id"] is None
    assert closure["rejection_reason"] is None
    assert closure["resolved_timestamp_utc"] is None
    records = closure["closure_records"]
    assert len(records) == 1
    assert records[0]["event_kind"] == "submitted"
    assert records[0]["event_kind"] in EVENT_KIND_ENUM
    assert records[0]["actor_kind"] == "operator"


# ---------- Closed-schema rejections -------------------------------------


def test_unknown_target_kind_rejected() -> None:
    payload = {**_VALID_PAYLOAD, "target_kind": "not_a_real_kind"}
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert "closed_enum_violation:target_kind" in exc.value.error_code


def test_unknown_target_facet_rejected() -> None:
    payload = {
        **_VALID_PAYLOAD,
        "target_tags": [{"facet": "not_a_facet", "value": "x"}],
    }
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert "target_tags_facet" in exc.value.error_code


def test_unknown_line_availability_rejected() -> None:
    payload = {**_VALID_PAYLOAD, "target_line_availability": ["not_a_line"]}
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "target_line_availability_value"


def test_vendor_key_in_payload_rejected() -> None:
    payload = {**_VALID_PAYLOAD, "vendor_id": "leaked"}
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "forbidden_field"


def test_truth_state_field_in_payload_rejected() -> None:
    payload = {**_VALID_PAYLOAD, "ready": True}
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "forbidden_field"


def test_missing_artifact_ref_rejected() -> None:
    payload = {**_VALID_PAYLOAD}
    payload.pop("artifact_ref")
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "artifact_ref_required"


def test_missing_proposed_title_rejected() -> None:
    payload = {**_VALID_PAYLOAD, "proposed_title": ""}
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "proposed_title_required"


def test_missing_requested_by_rejected() -> None:
    payload = {**_VALID_PAYLOAD}
    payload.pop("requested_by")
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert exc.value.error_code == "requested_by_required"


def test_unknown_license_rejected() -> None:
    payload = {
        **_VALID_PAYLOAD,
        "license_metadata": {**_VALID_PAYLOAD["license_metadata"], "license": "not_real"},
    }
    with pytest.raises(PromoteRequestRejected) as exc:
        submit_promote_request(payload)
    assert "closed_enum_violation:license_metadata.license" in exc.value.error_code


# ---------- Closure transitions ------------------------------------------


def test_withdraw_transitions_to_rejected_with_null_reason() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    closure = withdraw_request(result["request_id"], actor_ref="operator:demo")
    assert closure["request_state"] == "rejected"
    assert closure["rejection_reason"] is None  # Operator withdrawal carries no reviewer reason
    assert closure["reviewer_ref"] is None
    assert closure["resolved_timestamp_utc"] is not None
    last_event = closure["closure_records"][-1]
    assert last_event["event_kind"] == "withdrawn"


def test_withdraw_after_terminal_rejected() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    withdraw_request(result["request_id"], actor_ref="operator:demo")
    with pytest.raises(PromoteRequestRejected) as exc:
        withdraw_request(result["request_id"], actor_ref="operator:demo")
    assert exc.value.error_code == "closure_terminal"


def test_approve_transitions_to_approved_with_resulting_asset_id() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    closure = approve_request(
        result["request_id"],
        reviewer_ref="reviewer:admin1",
        resulting_asset_id="asset_promoted_001",
        reviewer_notes="Looks good.",
    )
    assert closure["request_state"] == "approved"
    assert closure["resulting_asset_id"] == "asset_promoted_001"
    assert closure["reviewer_ref"] == "reviewer:admin1"
    assert closure["resolved_timestamp_utc"] is not None
    event_kinds = [r["event_kind"] for r in closure["closure_records"]]
    assert event_kinds == ["submitted", "review_started", "approved"]


def test_reject_with_closed_reason_enum_only() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    closure = reject_request(
        result["request_id"],
        reviewer_ref="reviewer:admin1",
        rejection_reason="quality_below_threshold",
        reviewer_notes="Resolution too low.",
    )
    assert closure["request_state"] == "rejected"
    assert closure["rejection_reason"] in REJECTION_REASON_ENUM
    assert closure["rejection_reason"] == "quality_below_threshold"


def test_reject_with_unknown_reason_rejected() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    with pytest.raises(PromoteRequestRejected) as exc:
        reject_request(
            result["request_id"],
            reviewer_ref="reviewer:admin1",
            rejection_reason="not_a_real_reason",
        )
    assert exc.value.error_code == "rejection_reason_closed_enum"


def test_approve_after_terminal_rejected() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    reject_request(
        result["request_id"],
        reviewer_ref="reviewer:admin1",
        rejection_reason="reviewer_discretion",
    )
    with pytest.raises(PromoteRequestRejected):
        approve_request(
            result["request_id"],
            reviewer_ref="reviewer:admin1",
            resulting_asset_id="asset_should_not_exist",
        )


# ---------- Closure mirror integrity --------------------------------------


def test_closure_records_are_append_only() -> None:
    result = submit_promote_request(_VALID_PAYLOAD)
    closure = get_closure(result["request_id"])
    assert closure is not None
    closure["closure_records"].append({"event_kind": "tampered"})
    fresh = get_closure(result["request_id"])
    assert fresh is not None
    # Mutations to the deep-copy MUST NOT persist back to the store.
    assert len(fresh["closure_records"]) == 1


def test_list_closures_filters_by_requesting_operator() -> None:
    submit_promote_request(_VALID_PAYLOAD)
    payload2 = {**_VALID_PAYLOAD, "requested_by": "operator:other"}
    submit_promote_request(payload2)
    only_demo = list_closures(requested_by="operator:demo")
    assert len(only_demo) == 1
    only_other = list_closures(requested_by="operator:other")
    assert len(only_other) == 1


def test_unknown_request_id_returns_none_for_get_closure() -> None:
    assert get_closure("nope") is None


def test_withdraw_unknown_request_raises_not_found() -> None:
    with pytest.raises(PromoteRequestRejected) as exc:
        withdraw_request("nope", actor_ref="operator:demo")
    assert exc.value.error_code == "closure_not_found"
