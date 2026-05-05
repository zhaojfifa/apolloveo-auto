"""Service-layer tests for the Digital Anchor publish closure backfill view (OWC-DA PR-3 / DA-W9).

Authority:
- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W9
- ``docs/product/digital_anchor_product_flow_v1.md`` §7.3
- ``docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md``
- ``docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md``

Scope: six-field per-row 回填 projection over the existing
``digital_anchor_publish_feedback_closure_v1`` closure surface +
``feedback_closure_records[]`` D.1 publish events. Verifies the
operator-language status sentinels for absent channel / account, the
D.1 publish_status enum passthrough, the metrics_snapshot rendering,
and the no-closure-yet path emitting the digital-anchor-shaped bundle
with zero lanes.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.digital_anchor import closure_binding
from gateway.app.services.digital_anchor.publish_closure_backfill_view import (
    ACCOUNT_TRACKED_GAP_EXPLANATION_ZH,
    CHANNEL_TRACKED_GAP_EXPLANATION_ZH,
    FIELD_ACCOUNT,
    FIELD_CHANNEL,
    FIELD_LABELS_ZH,
    FIELD_METRICS_SNAPSHOT,
    FIELD_ORDER,
    FIELD_PUBLISH_STATUS,
    FIELD_PUBLISH_TIME,
    FIELD_PUBLISH_URL,
    LANE_SCOPE_ROLE,
    LANE_SCOPE_SEGMENT,
    PUBLISH_STATUS_LABELS_ZH,
    STATUS_NO_METRICS,
    STATUS_NOT_PUBLISHED,
    STATUS_RESOLVED,
    STATUS_UNSOURCED,
    derive_digital_anchor_publish_closure_backfill,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "digital_anchor"
    / "sample"
    / "digital_anchor_packet_v1.sample.json"
)


def _packet_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _digital_anchor_task(task_id: str = "da_backfill_task_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "packet": _packet_sample(),
    }


def _role_ids(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "digital_anchor_role_pack":
            return [r["role_id"] for r in ref["delta"]["roles"]]
    raise AssertionError("role_pack missing in sample")


def _segment_ids(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "digital_anchor_speaker_plan":
            return [s["segment_id"] for s in ref["delta"]["segments"]]
    raise AssertionError("speaker_plan missing in sample")


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


# ─────────────────────────────────────────────────────────────────────
# Empty / non-DA / no-closure paths
# ─────────────────────────────────────────────────────────────────────


def test_none_input_emits_digital_anchor_shaped_empty_bundle():
    bundle = derive_digital_anchor_publish_closure_backfill(None)
    assert bundle["is_digital_anchor"] is True
    assert bundle["panel_title_zh"] == "Digital Anchor · 交付中心 · 多渠道回填"
    assert bundle["lanes"] == []
    assert bundle["lane_count"] == 0
    assert bundle["field_legend_zh"] == [FIELD_LABELS_ZH[fid] for fid in FIELD_ORDER]


def test_empty_dict_input_emits_digital_anchor_shaped_empty_bundle():
    bundle = derive_digital_anchor_publish_closure_backfill({})
    assert bundle["is_digital_anchor"] is True
    assert bundle["lane_count"] == 0


def test_non_digital_anchor_closure_returns_empty_bundle():
    foreign = {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "line_id": "matrix_script",
        "role_feedback": [],
        "segment_feedback": [],
    }
    assert derive_digital_anchor_publish_closure_backfill(foreign) == {}


def test_freshly_initialised_closure_emits_zero_lanes():
    """A closure created via get_or_create_for_task but with zero D.1
    events still has empty role_feedback / segment_feedback rows. The
    backfill bundle therefore has zero lanes."""
    task = _digital_anchor_task()
    closure_binding.get_or_create_for_task(task)
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    assert bundle["is_digital_anchor"] is True
    assert bundle["lane_count"] == 0


# ─────────────────────────────────────────────────────────────────────
# Role lane after D.1 publish_attempted
# ─────────────────────────────────────────────────────────────────────


def test_role_lane_after_publish_attempted_renders_pending():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
        recorded_at="2026-05-05T13:00:00Z",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    assert bundle["lane_count"] == 1
    lane = bundle["lanes"][0]
    assert lane["row_scope"] == LANE_SCOPE_ROLE
    assert lane["row_id"] == role_id
    fields = {f["field_id"]: f for f in lane["fields"]}
    assert fields[FIELD_PUBLISH_STATUS]["value"] == "pending"
    assert (
        fields[FIELD_PUBLISH_STATUS]["value_label_zh"]
        == PUBLISH_STATUS_LABELS_ZH["pending"]
    )


def test_role_lane_after_publish_accepted_renders_published_with_url():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
        recorded_at="2026-05-05T13:00:00Z",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_accepted",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={"publish_url": "https://example.test/da/role/anchor_a"},
        recorded_at="2026-05-05T13:05:00Z",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = next(
        l for l in bundle["lanes"]
        if l["row_scope"] == LANE_SCOPE_ROLE and l["row_id"] == role_id
    )
    fields = {f["field_id"]: f for f in lane["fields"]}
    assert fields[FIELD_PUBLISH_STATUS]["value"] == "published"
    assert (
        fields[FIELD_PUBLISH_URL]["value"]
        == "https://example.test/da/role/anchor_a"
    )
    assert fields[FIELD_PUBLISH_TIME]["status_code"] == STATUS_RESOLVED
    assert fields[FIELD_PUBLISH_TIME]["value"] == "2026-05-05T13:05:00Z"


def test_segment_lane_after_publish_rejected_renders_failed():
    task = _digital_anchor_task()
    seg_id = _segment_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="segment",
        row_id=seg_id,
        actor_kind="operator",
        recorded_at="2026-05-05T13:00:00Z",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_rejected",
        row_scope="segment",
        row_id=seg_id,
        actor_kind="platform",
        recorded_at="2026-05-05T13:10:00Z",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = next(
        l for l in bundle["lanes"]
        if l["row_scope"] == LANE_SCOPE_SEGMENT and l["row_id"] == seg_id
    )
    fields = {f["field_id"]: f for f in lane["fields"]}
    assert fields[FIELD_PUBLISH_STATUS]["value"] == "failed"


def test_role_lane_after_publish_retracted_renders_retracted():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
        recorded_at="2026-05-05T13:00:00Z",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_retracted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
        recorded_at="2026-05-05T14:00:00Z",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = next(l for l in bundle["lanes"] if l["row_id"] == role_id)
    fields = {f["field_id"]: f for f in lane["fields"]}
    assert fields[FIELD_PUBLISH_STATUS]["value"] == "retracted"


# ─────────────────────────────────────────────────────────────────────
# Channel + account tracked-gap discipline
# ─────────────────────────────────────────────────────────────────────


def test_channel_field_tracked_gap_when_no_metrics_snapshot():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = bundle["lanes"][0]
    fields = {f["field_id"]: f for f in lane["fields"]}
    channel = fields[FIELD_CHANNEL]
    assert channel["status_code"] == STATUS_UNSOURCED
    assert channel["value"] == ""
    assert channel["tracked_gap_explanation_zh"] == CHANNEL_TRACKED_GAP_EXPLANATION_ZH


def test_account_field_always_tracked_gap_per_gate_spec():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_accepted",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={"publish_url": "https://example.test/x"},
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = bundle["lanes"][0]
    fields = {f["field_id"]: f for f in lane["fields"]}
    account = fields[FIELD_ACCOUNT]
    assert account["status_code"] == STATUS_UNSOURCED
    assert account["value"] == ""
    assert account["tracked_gap_explanation_zh"] == ACCOUNT_TRACKED_GAP_EXPLANATION_ZH


# ─────────────────────────────────────────────────────────────────────
# metrics_snapshot rendering
# ─────────────────────────────────────────────────────────────────────


def test_metrics_snapshot_renders_when_event_applied():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="metrics_snapshot",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={
            "views": 1000,
            "likes": 80,
            "shares": 12,
            "captured_at": "2026-05-05T15:00:00Z",
        },
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    lane = bundle["lanes"][0]
    fields = {f["field_id"]: f for f in lane["fields"]}
    metrics = fields[FIELD_METRICS_SNAPSHOT]
    assert metrics["status_code"] == STATUS_RESOLVED
    pairs = {p["metric_id"]: p["value"] for p in metrics["metrics_pairs"]}
    assert pairs["views"] == 1000
    assert pairs["likes"] == 80
    assert pairs["shares"] == 12
    assert pairs["captured_at"] == "2026-05-05T15:00:00Z"
    assert lane["channel_metrics_count"] == 1


def test_metrics_snapshot_no_metrics_status_when_not_emitted():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    metrics = fields[FIELD_METRICS_SNAPSHOT]
    assert metrics["status_code"] == STATUS_NO_METRICS
    assert metrics["metrics_pairs"] == []


def test_metrics_snapshot_picks_latest_by_captured_at():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="metrics_snapshot",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={"views": 100, "captured_at": "2026-05-05T15:00:00Z"},
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="metrics_snapshot",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={"views": 5000, "captured_at": "2026-05-05T17:00:00Z"},
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    pairs = {p["metric_id"]: p["value"] for p in fields[FIELD_METRICS_SNAPSHOT]["metrics_pairs"]}
    assert pairs["views"] == 5000  # latest wins
    assert bundle["lanes"][0]["channel_metrics_count"] == 2


# ─────────────────────────────────────────────────────────────────────
# publish_time fallback ordering
# ─────────────────────────────────────────────────────────────────────


def test_publish_time_falls_back_to_metrics_captured_at_when_no_publish_event():
    """Synthesise a closure where channel_metrics carries a captured_at
    but no publish_* event has fired. Metrics fallback must engage."""
    closure = {
        "surface": "digital_anchor_publish_feedback_closure_v1",
        "line_id": "digital_anchor",
        "role_feedback": [
            {
                "role_id": "role_x",
                "role_display_name": "X",
                "publish_status": "pending",
                "publish_url": None,
                "channel_metrics": [
                    {"captured_at": "2026-05-05T20:00:00Z", "views": 50}
                ],
                "last_event_id": None,
            }
        ],
        "segment_feedback": [],
        "feedback_closure_records": [],
    }
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    pt = fields[FIELD_PUBLISH_TIME]
    assert pt["status_code"] == STATUS_RESOLVED
    assert pt["value"] == "2026-05-05T20:00:00Z"
    assert pt["value_source_id"] == "row.channel_metrics.captured_at"


def test_publish_time_not_published_when_nothing_is_recorded():
    closure = {
        "surface": "digital_anchor_publish_feedback_closure_v1",
        "line_id": "digital_anchor",
        "role_feedback": [
            {
                "role_id": "role_x",
                "publish_status": "pending",
                "publish_url": None,
                "channel_metrics": [],
                "last_event_id": None,
            }
        ],
        "segment_feedback": [],
        "feedback_closure_records": [],
    }
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    pt = fields[FIELD_PUBLISH_TIME]
    assert pt["status_code"] == STATUS_NOT_PUBLISHED
    assert pt["value"] == ""


def test_publish_time_uses_last_event_recorded_at_when_records_lack_event_kind():
    """Defense-in-depth: if an audit record is missing event_kind (legacy
    pre-D.1 shape) but the row has last_event_recorded_at, that fallback
    is used."""
    closure = {
        "surface": "digital_anchor_publish_feedback_closure_v1",
        "line_id": "digital_anchor",
        "role_feedback": [
            {
                "role_id": "role_x",
                "publish_status": "published",
                "publish_url": "https://x.test",
                "channel_metrics": [],
                "last_event_id": "rec_legacy",
                "last_event_recorded_at": "2026-05-05T14:30:00Z",
            }
        ],
        "segment_feedback": [],
        "feedback_closure_records": [
            {"record_kind": "operator_review", "row_scope": "role", "row_id": "role_x"}
        ],
    }
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    pt = fields[FIELD_PUBLISH_TIME]
    assert pt["status_code"] == STATUS_RESOLVED
    assert pt["value"] == "2026-05-05T14:30:00Z"
    assert pt["value_source_id"] == "row.last_event_recorded_at"


# ─────────────────────────────────────────────────────────────────────
# Multiple lanes / cross-row
# ─────────────────────────────────────────────────────────────────────


def test_multiple_role_and_segment_lanes_after_mixed_events():
    task = _digital_anchor_task()
    roles = _role_ids(task["packet"])
    segments = _segment_ids(task["packet"])
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=roles[0],
        actor_kind="operator",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="segment",
        row_id=segments[0],
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    assert bundle["lane_count"] == 2
    scopes = sorted(l["row_scope"] for l in bundle["lanes"])
    assert scopes == [LANE_SCOPE_ROLE, LANE_SCOPE_SEGMENT]


def test_lane_count_matches_role_plus_segment_rows():
    task = _digital_anchor_task()
    roles = _role_ids(task["packet"])
    for role_id in roles:
        closure_binding.apply_writeback_event_for_task(
            task,
            event_kind="publish_attempted",
            row_scope="role",
            row_id=role_id,
            actor_kind="operator",
        )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    assert bundle["lane_count"] == len(roles)


# ─────────────────────────────────────────────────────────────────────
# Field shape + ordering invariants
# ─────────────────────────────────────────────────────────────────────


def test_lane_fields_follow_field_order():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    field_ids = [f["field_id"] for f in bundle["lanes"][0]["fields"]]
    assert field_ids == list(FIELD_ORDER)


def test_field_legend_zh_matches_field_order():
    bundle = derive_digital_anchor_publish_closure_backfill(None)
    legend = bundle["field_legend_zh"]
    assert legend == [FIELD_LABELS_ZH[fid] for fid in FIELD_ORDER]


def test_publish_status_out_of_enum_renders_not_published_defensively():
    closure = {
        "surface": "digital_anchor_publish_feedback_closure_v1",
        "line_id": "digital_anchor",
        "role_feedback": [
            {
                "role_id": "role_x",
                "publish_status": "weird_state",
                "publish_url": None,
                "channel_metrics": [],
                "last_event_id": None,
            }
        ],
        "segment_feedback": [],
        "feedback_closure_records": [],
    }
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    fields = {f["field_id"]: f for f in bundle["lanes"][0]["fields"]}
    ps = fields[FIELD_PUBLISH_STATUS]
    assert ps["status_code"] == STATUS_NOT_PUBLISHED
    assert ps["value"] == ""


# ─────────────────────────────────────────────────────────────────────
# Cross-line preservation
# ─────────────────────────────────────────────────────────────────────


def test_matrix_script_closure_review_zone_values_unchanged_by_da_addition():
    """OWC-DA PR-3 must NOT touch matrix_script closure constants. The
    Matrix Script REVIEW_ZONE_VALUES (shipped under MS-W5; MS-specific
    set ``{copy, cta, dub, subtitle}``) is enforced byte-stable across
    DA additions. The DA REVIEW_ZONE_VALUES (shipped under DA-W7;
    DA-specific set) is intentionally different per gate spec §3 wording
    that each line owns its own closed review-zone set."""
    from gateway.app.services.matrix_script.publish_feedback_closure import (
        REVIEW_ZONE_VALUES as MS_REVIEW_ZONE_VALUES,
    )

    assert MS_REVIEW_ZONE_VALUES == frozenset({"subtitle", "dub", "copy", "cta"})


def test_da_review_zone_values_unchanged_by_pr3():
    """OWC-DA PR-3 must NOT widen the DA REVIEW_ZONE_VALUES enum shipped
    by PR-2 (DA-W7). The closed five-zone set is binding."""
    from gateway.app.services.digital_anchor.publish_feedback_closure import (
        REVIEW_ZONE_VALUES as DA_REVIEW_ZONE_VALUES,
    )

    assert DA_REVIEW_ZONE_VALUES == frozenset(
        {"audition", "video_preview", "subtitle", "cadence", "qc"}
    )


# ─────────────────────────────────────────────────────────────────────
# Read-only discipline
# ─────────────────────────────────────────────────────────────────────


def test_projection_does_not_mutate_input_closure():
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    snapshot = deepcopy(closure)
    derive_digital_anchor_publish_closure_backfill(closure)
    assert closure == snapshot


def test_no_provider_model_vendor_engine_in_field_values():
    """validator R3 + design-handoff red line 6: scrub any forbidden
    token fragments out of the field value path. Tracked-gap
    explanations may legitimately mention 'engine' for narrative
    purposes (this is operator-language, not a value); the `value` and
    `value_source_id` paths must be clean."""
    task = _digital_anchor_task()
    role_id = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role_id,
        actor_kind="operator",
    )
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_accepted",
        row_scope="role",
        row_id=role_id,
        actor_kind="platform",
        payload={"publish_url": "https://example.test/clean"},
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = derive_digital_anchor_publish_closure_backfill(closure)
    forbidden = ("vendor", "model_id", "provider", "engine_id")
    for lane in bundle["lanes"]:
        for fld in lane["fields"]:
            for key in ("value", "value_source_id"):
                v = fld.get(key)
                if isinstance(v, str):
                    for token in forbidden:
                        assert token not in v.lower(), (
                            f"field {fld.get('field_id')!r} key {key!r} carries "
                            f"forbidden token {token!r}: {v!r}"
                        )
