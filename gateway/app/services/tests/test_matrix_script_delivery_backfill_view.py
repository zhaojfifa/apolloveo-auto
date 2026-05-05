"""OWC-MS PR-3 / MS-W8 — Matrix Script Delivery Center 多渠道回填 tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W8 (binding scope).
- ``docs/product/matrix_script_product_flow_v1.md`` §7.3 (回填对象).
- ``gateway/app/services/matrix_script/delivery_backfill_view.py`` (helper under test).
- ``gateway/app/services/matrix_script/publish_feedback_closure.py`` (closure
  shape consumed read-only).

Import-light: exercises the pure helper
``derive_matrix_script_delivery_backfill`` over hand-built closure views
that mirror the shape produced by ``InMemoryClosureStore.get(...)``.

What is proved:

1. Returns ``{}`` for ``None`` / non-Matrix-Script closures.
2. Each ``variation_feedback[]`` row produces exactly one lane in the
   closed order; lane labels carry the ``variation_id``.
3. Every lane carries the six fields enumerated in product-flow §7.3 in
   the closed order ``channel / account / publish_time / publish_url /
   publish_status / metrics_snapshot``.
4. ``channel`` resolves from ``channel_metrics[].channel_id`` only;
   absent metric snapshots → ``not_published_yet``.
5. ``account`` is ALWAYS rendered as the tracked-gap row
   (``unsourced_pending_capture_capability``) regardless of any other
   field's resolution state — the closure has no ``account_id`` field
   and the gate spec forbids widening.
6. ``publish_time`` resolves from ``feedback_closure_records[].recorded_at``
   on the most recent ``operator_publish`` / ``platform_callback`` event;
   falls back to ``channel_metrics[].captured_at`` when no publish event
   exists; falls back to ``not_published_yet`` when neither exists.
7. ``publish_url`` resolves from ``variation_feedback[].publish_url``;
   ``not_published_yet`` when empty.
8. ``publish_status`` reads from ``variation_feedback[].publish_status``
   inside the closed enum ``{pending, published, failed, retracted}``;
   the operator-language ``value_label_zh`` is closed too. Out-of-enum
   values degrade gracefully without raising.
9. ``metrics_snapshot`` is rendered from the latest entry of
   ``channel_metrics[]`` with operator-language metric labels;
   ``no_metrics_snapshot_yet`` when empty.
10. Validator R3 alignment — no vendor / model / provider / engine
    identifier anywhere in the bundle (recursive walk).
11. Helper does not mutate inputs.
12. No closure schema widening — ``EVENT_KINDS`` / ``ACTOR_KINDS`` /
    ``PUBLISH_STATUS_VALUES`` / ``CHANNEL_METRICS_KEYS`` are read-only.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_backfill_view import (
    ACCOUNT_TRACKED_GAP_EXPLANATION_ZH,
    FIELD_ACCOUNT,
    FIELD_CHANNEL,
    FIELD_LABELS_ZH,
    FIELD_METRICS_SNAPSHOT,
    FIELD_PUBLISH_STATUS,
    FIELD_PUBLISH_TIME,
    FIELD_PUBLISH_URL,
    FORBIDDEN_TOKEN_FRAGMENTS,
    PUBLISH_STATUS_LABELS_ZH,
    STATUS_NOT_PUBLISHED,
    STATUS_NO_METRICS,
    STATUS_RESOLVED,
    STATUS_UNSOURCED,
    derive_matrix_script_delivery_backfill,
)


def _empty_closure(variation_ids: list[str]) -> dict[str, Any]:
    return {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "closure_id": "closure_test",
        "line_id": "matrix_script",
        "packet_version": "v1",
        "variation_feedback": [
            {
                "variation_id": vid,
                "publish_url": None,
                "publish_status": "pending",
                "channel_metrics": [],
                "operator_publish_notes": None,
                "last_event_id": None,
            }
            for vid in variation_ids
        ],
        "feedback_closure_records": [],
    }


def _published_closure() -> dict[str, Any]:
    return {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "closure_id": "closure_test",
        "line_id": "matrix_script",
        "packet_version": "v1",
        "variation_feedback": [
            {
                "variation_id": "cell_1",
                "publish_url": "https://www.douyin.com/video/abc",
                "publish_status": "published",
                "channel_metrics": [
                    {
                        "channel_id": "douyin",
                        "captured_at": "2026-05-05T08:30:00Z",
                        "impressions": 12000,
                        "views": 9000,
                        "engagement_rate": 0.12,
                        "completion_rate": 0.55,
                    },
                    {
                        "channel_id": "douyin",
                        "captured_at": "2026-05-05T10:00:00Z",
                        "impressions": 15000,
                        "views": 12000,
                    },
                ],
                "operator_publish_notes": None,
                "last_event_id": "evt_1",
            },
            {
                "variation_id": "cell_2",
                "publish_url": None,
                "publish_status": "pending",
                "channel_metrics": [],
                "operator_publish_notes": None,
                "last_event_id": None,
            },
        ],
        "feedback_closure_records": [
            {
                "event_id": "evt_1",
                "variation_id": "cell_1",
                "event_kind": "platform_callback",
                "recorded_at": "2026-05-05T08:00:00Z",
                "actor_kind": "platform",
                "payload_ref": None,
            },
            {
                "event_id": "evt_2",
                "variation_id": "cell_1",
                "event_kind": "metrics_snapshot",
                "recorded_at": "2026-05-05T10:00:00Z",
                "actor_kind": "system",
                "payload_ref": None,
            },
        ],
    }


def _lane(bundle: Mapping[str, Any], variation_id: str) -> Mapping[str, Any]:
    for lane in bundle.get("lanes", []):
        if lane.get("variation_id") == variation_id:
            return lane
    raise AssertionError(f"variation_id {variation_id!r} not in bundle lanes")


def _field(lane: Mapping[str, Any], field_id: str) -> Mapping[str, Any]:
    for field in lane.get("fields", []):
        if field.get("field_id") == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not in lane {lane.get('variation_id')!r}")


# 1. No-closure-yet path emits the matrix_script-shaped panel with zero
# lanes (Codex P1 review on PR #125, 2026-05-05). The operator sees the
# empty-state message instead of a hidden card.
def test_returns_zero_lanes_panel_for_none_closure():
    bundle = derive_matrix_script_delivery_backfill(None)
    assert bundle["is_matrix_script"] is True
    assert bundle["lane_count"] == 0
    assert bundle["lanes"] == []
    assert "尚未生成 closure" in bundle["tracked_gap_summary_zh"]


def test_returns_zero_lanes_panel_for_empty_mapping():
    bundle = derive_matrix_script_delivery_backfill({})
    assert bundle["is_matrix_script"] is True
    assert bundle["lane_count"] == 0
    assert bundle["lanes"] == []


def test_no_closure_panel_carries_documented_keys_so_template_renders():
    """Documented bundle shape (is_matrix_script / panel_title_zh /
    panel_subtitle_zh / field_legend_zh / lanes / lane_count /
    tracked_gap_summary_zh) is intact so the JS renderer + the
    ``data-role="ms-delivery-backfill-empty"`` empty-state message
    show. Codex P1 fix invariant."""

    bundle = derive_matrix_script_delivery_backfill(None)
    expected = {
        "is_matrix_script",
        "panel_title_zh",
        "panel_subtitle_zh",
        "field_legend_zh",
        "lanes",
        "lane_count",
        "tracked_gap_summary_zh",
    }
    assert expected.issubset(bundle.keys())
    assert bundle["panel_title_zh"]
    assert bundle["panel_subtitle_zh"]
    assert len(bundle["field_legend_zh"]) == 6


# Cross-line isolation: a non-matrix_script closure (wiring bug at the
# caller side) still returns {} so the cross-line render stays untouched.
@pytest.mark.parametrize("surface", ["hot_follow_publish_feedback_v1", "digital_anchor_publish_feedback_closure_v1"])
def test_returns_empty_for_non_matrix_script_surface(surface):
    closure = {
        "surface": surface,
        "line_id": "hot_follow",
        "variation_feedback": [],
        "feedback_closure_records": [],
    }
    assert derive_matrix_script_delivery_backfill(closure) == {}


def test_recognises_matrix_script_by_line_id_alone():
    closure = {
        "line_id": "matrix_script",
        "variation_feedback": [],
        "feedback_closure_records": [],
    }
    bundle = derive_matrix_script_delivery_backfill(closure)
    assert bundle["is_matrix_script"] is True


# 2. One lane per variation_feedback row.
def test_lane_count_matches_variation_feedback_rows():
    closure = _empty_closure(["a", "b", "c"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    assert bundle["lane_count"] == 3
    assert len(bundle["lanes"]) == 3
    assert [lane["variation_id"] for lane in bundle["lanes"]] == ["a", "b", "c"]


def test_lane_label_zh_carries_variation_id():
    closure = _empty_closure(["cell_42"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = bundle["lanes"][0]
    assert lane["lane_label_zh"] == "variation_id · cell_42"


# 3. Six fields in closed order.
def test_each_lane_emits_six_fields_in_stable_order():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = bundle["lanes"][0]
    assert [field["field_id"] for field in lane["fields"]] == [
        FIELD_CHANNEL,
        FIELD_ACCOUNT,
        FIELD_PUBLISH_TIME,
        FIELD_PUBLISH_URL,
        FIELD_PUBLISH_STATUS,
        FIELD_METRICS_SNAPSHOT,
    ]


def test_field_legend_zh_emits_six_labels_in_stable_order():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    assert bundle["field_legend_zh"] == [
        "发布渠道",
        "账号 ID",
        "发布时间",
        "发布链接",
        "发布状态",
        "指标入口（snapshot）",
    ]


# 4. Channel resolves from channel_metrics.channel_id.
def test_channel_resolves_from_channel_metrics_channel_id():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    channel = _field(lane, FIELD_CHANNEL)
    assert channel["status_code"] == STATUS_RESOLVED
    assert channel["value"] == "douyin"
    assert channel["value_source_id"] == "closure_channel_metrics_channel_id"


def test_channel_unresolved_when_no_channel_metrics():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    channel = _field(lane, FIELD_CHANNEL)
    assert channel["status_code"] == STATUS_NOT_PUBLISHED
    assert channel["value"] == ""


# 5. Account is ALWAYS the tracked gap.
def test_account_field_is_always_tracked_gap_even_when_published():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    for variation_id in ("cell_1", "cell_2"):
        lane = _lane(bundle, variation_id)
        account = _field(lane, FIELD_ACCOUNT)
        assert account["status_code"] == STATUS_UNSOURCED
        assert account["value"] == ""
        assert account["value_source_id"] is None
        assert account["tracked_gap_explanation_zh"] == ACCOUNT_TRACKED_GAP_EXPLANATION_ZH


def test_account_tracked_gap_summary_present_at_panel_level():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    assert "账号 ID" in bundle["tracked_gap_summary_zh"]


# 6. Publish time precedence.
def test_publish_time_resolves_from_publish_event_recorded_at():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    pub_time = _field(lane, FIELD_PUBLISH_TIME)
    # The platform_callback record at 08:00 is the only publish-event record;
    # the metrics_snapshot at 10:00 is NOT a publish event so the publish_time
    # comes from the platform_callback recorded_at. The captured_at fallback
    # is only used when no publish event exists.
    assert pub_time["status_code"] == STATUS_RESOLVED
    assert pub_time["value"] == "2026-05-05T08:00:00Z"
    assert pub_time["value_source_id"] == "closure_publish_event_recorded_at"


def test_publish_time_falls_back_to_captured_at_when_no_publish_event():
    closure = {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "line_id": "matrix_script",
        "variation_feedback": [
            {
                "variation_id": "cell_1",
                "publish_url": None,
                "publish_status": "pending",
                "channel_metrics": [
                    {"channel_id": "douyin", "captured_at": "2026-05-05T11:00:00Z"}
                ],
                "operator_publish_notes": None,
                "last_event_id": None,
            }
        ],
        "feedback_closure_records": [],
    }
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    pub_time = _field(lane, FIELD_PUBLISH_TIME)
    assert pub_time["status_code"] == STATUS_RESOLVED
    assert pub_time["value"] == "2026-05-05T11:00:00Z"
    assert pub_time["value_source_id"] == "closure_channel_metrics_captured_at"


def test_publish_time_unresolved_when_neither_event_nor_metrics():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    pub_time = _field(lane, FIELD_PUBLISH_TIME)
    assert pub_time["status_code"] == STATUS_NOT_PUBLISHED
    assert pub_time["value"] == ""


def test_publish_time_picks_latest_publish_event():
    closure = {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "line_id": "matrix_script",
        "variation_feedback": [
            {
                "variation_id": "cell_1",
                "publish_url": "https://x",
                "publish_status": "published",
                "channel_metrics": [],
                "operator_publish_notes": None,
                "last_event_id": "evt_2",
            }
        ],
        "feedback_closure_records": [
            {"event_id": "evt_1", "variation_id": "cell_1", "event_kind": "operator_publish", "recorded_at": "2026-05-04T10:00:00Z", "actor_kind": "operator"},
            {"event_id": "evt_2", "variation_id": "cell_1", "event_kind": "platform_callback", "recorded_at": "2026-05-05T12:00:00Z", "actor_kind": "platform"},
        ],
    }
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    pub_time = _field(lane, FIELD_PUBLISH_TIME)
    assert pub_time["value"] == "2026-05-05T12:00:00Z"


# 7. Publish URL.
def test_publish_url_resolves_from_variation_feedback():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    pub_url = _field(lane, FIELD_PUBLISH_URL)
    assert pub_url["status_code"] == STATUS_RESOLVED
    assert pub_url["value"] == "https://www.douyin.com/video/abc"


def test_publish_url_unresolved_when_empty():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    pub_url = _field(lane, FIELD_PUBLISH_URL)
    assert pub_url["status_code"] == STATUS_NOT_PUBLISHED
    assert pub_url["value"] == ""


# 8. Publish status closed enum.
@pytest.mark.parametrize(
    "raw_status,expected_label_zh",
    [
        ("pending", "待发布"),
        ("published", "已发布"),
        ("failed", "发布失败"),
        ("retracted", "已撤回"),
    ],
)
def test_publish_status_renders_closed_enum(raw_status, expected_label_zh):
    closure = _empty_closure(["x"])
    closure["variation_feedback"][0]["publish_status"] = raw_status
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    status = _field(lane, FIELD_PUBLISH_STATUS)
    assert status["status_code"] == STATUS_RESOLVED
    assert status["value"] == raw_status
    assert status["value_label_zh"] == expected_label_zh


def test_publish_status_out_of_enum_degrades_gracefully():
    closure = _empty_closure(["x"])
    closure["variation_feedback"][0]["publish_status"] = "garbage_value"
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    status = _field(lane, FIELD_PUBLISH_STATUS)
    assert status["status_code"] == STATUS_NOT_PUBLISHED
    assert status["value"] == ""


def test_publish_status_labels_zh_keys_match_closure_publish_status_values():
    # Sanity check that the helper's closed enum mirror agrees with the
    # closure contract's PUBLISH_STATUS_VALUES exactly.
    from gateway.app.services.matrix_script.publish_feedback_closure import (
        PUBLISH_STATUS_VALUES,
    )

    assert set(PUBLISH_STATUS_LABELS_ZH.keys()) == set(PUBLISH_STATUS_VALUES)


# 9. Metrics snapshot.
def test_metrics_snapshot_renders_latest_channel_metrics_entry():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    metrics = _field(lane, FIELD_METRICS_SNAPSHOT)
    assert metrics["status_code"] == STATUS_RESOLVED
    pairs = {pair["metric_id"]: pair["value"] for pair in metrics["metrics_pairs"]}
    # The 10:00 snapshot is the latest (impressions 15000 / views 12000),
    # without engagement_rate / completion_rate (those exist only on the
    # 08:30 snapshot). Per-key omission, no synthesized zeros.
    assert pairs["captured_at"] == "2026-05-05T10:00:00Z"
    assert pairs["impressions"] == 15000
    assert pairs["views"] == 12000
    assert "engagement_rate" not in pairs
    assert "completion_rate" not in pairs


def test_metrics_snapshot_no_metrics_when_channel_metrics_empty():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    metrics = _field(lane, FIELD_METRICS_SNAPSHOT)
    assert metrics["status_code"] == STATUS_NO_METRICS
    assert metrics["metrics_pairs"] == []


def test_metrics_pairs_carry_operator_language_metric_labels():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "cell_1")
    metrics = _field(lane, FIELD_METRICS_SNAPSHOT)
    label_map = {pair["metric_id"]: pair["label_zh"] for pair in metrics["metrics_pairs"]}
    assert label_map["impressions"] == "曝光量"
    assert label_map["views"] == "播放量"
    assert label_map["captured_at"] == "采集时间"


def test_metrics_pairs_omit_keys_outside_closed_set():
    closure = _empty_closure(["x"])
    closure["variation_feedback"][0]["channel_metrics"] = [
        {
            "channel_id": "douyin",
            "captured_at": "2026-05-05T10:00:00Z",
            "impressions": 100,
            "stranger_field": "should_not_render",
        }
    ]
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    metrics = _field(lane, FIELD_METRICS_SNAPSHOT)
    metric_ids = {pair["metric_id"] for pair in metrics["metrics_pairs"]}
    assert "stranger_field" not in metric_ids
    assert metric_ids.issubset({"captured_at", "impressions", "views", "engagement_rate", "completion_rate"})


# 10. Validator R3 — no forbidden token leaks.
def _walk_strings(value: Any):
    if isinstance(value, Mapping):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


@pytest.mark.parametrize("token", FORBIDDEN_TOKEN_FRAGMENTS)
def test_bundle_carries_no_forbidden_token_recursively(token):
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    for s in _walk_strings(bundle):
        assert token not in s.lower(), f"forbidden token {token!r} leaked into {s!r}"


def test_forbidden_channel_id_falls_back_to_not_published():
    closure = _empty_closure(["x"])
    closure["variation_feedback"][0]["channel_metrics"] = [
        {"channel_id": "vendor_x_app", "captured_at": "2026-05-05T10:00:00Z"}
    ]
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    channel = _field(lane, FIELD_CHANNEL)
    assert channel["status_code"] == STATUS_NOT_PUBLISHED
    assert channel["value"] == ""


def test_forbidden_publish_url_falls_back_to_not_published():
    closure = _empty_closure(["x"])
    closure["variation_feedback"][0]["publish_url"] = "https://provider.example.com/abc"
    closure["variation_feedback"][0]["publish_status"] = "pending"
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = _lane(bundle, "x")
    pub_url = _field(lane, FIELD_PUBLISH_URL)
    assert pub_url["status_code"] == STATUS_NOT_PUBLISHED
    assert pub_url["value"] == ""


# 11. No input mutation.
def test_helper_does_not_mutate_closure():
    closure = _published_closure()
    snapshot = deepcopy(closure)
    derive_matrix_script_delivery_backfill(closure)
    assert closure == snapshot


# 12. No closure schema widening (read-only contract invariant).
def test_helper_never_touches_event_kinds_or_actor_kinds_or_channel_metrics_keys():
    from gateway.app.services.matrix_script.publish_feedback_closure import (
        ACTOR_KINDS,
        CHANNEL_METRICS_KEYS,
        EVENT_KINDS,
    )

    # Snapshot the closed sets, run the helper, confirm they're unchanged.
    event_kinds_snapshot = frozenset(EVENT_KINDS)
    actor_kinds_snapshot = frozenset(ACTOR_KINDS)
    channel_metrics_snapshot = frozenset(CHANNEL_METRICS_KEYS)
    derive_matrix_script_delivery_backfill(_published_closure())
    assert frozenset(EVENT_KINDS) == event_kinds_snapshot
    assert frozenset(ACTOR_KINDS) == actor_kinds_snapshot
    assert frozenset(CHANNEL_METRICS_KEYS) == channel_metrics_snapshot


# Closed-shape invariants.
def test_each_lane_field_carries_closed_keys_only():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    base_keys = {"field_id", "label_zh", "status_code", "status_label_zh", "value", "value_source_id"}
    for lane in bundle["lanes"]:
        for field in lane["fields"]:
            assert base_keys.issubset(field.keys()), field
            # Field-specific extra keys are allowed but enumerated.
            extra = set(field.keys()) - base_keys
            assert extra.issubset(
                {"tracked_gap_explanation_zh", "metrics_pairs", "value_label_zh"}
            ), extra


def test_field_labels_match_module_constants():
    closure = _empty_closure(["x"])
    bundle = derive_matrix_script_delivery_backfill(closure)
    lane = bundle["lanes"][0]
    for field in lane["fields"]:
        assert field["label_zh"] == FIELD_LABELS_ZH[field["field_id"]]


def test_lane_carries_publish_event_count_and_channel_metrics_count():
    closure = _published_closure()
    bundle = derive_matrix_script_delivery_backfill(closure)
    cell_1 = _lane(bundle, "cell_1")
    cell_2 = _lane(bundle, "cell_2")
    assert cell_1["channel_metrics_count"] == 2
    assert cell_1["publish_event_count"] == 1  # only platform_callback in records
    assert cell_2["channel_metrics_count"] == 0
    assert cell_2["publish_event_count"] == 0
