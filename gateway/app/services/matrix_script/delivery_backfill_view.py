"""Matrix Script Delivery Center — multi-channel 回填 rendering (OWC-MS PR-3 / MS-W8).

Pure presentation-layer projection over the contract-frozen Matrix Script
publish-feedback closure surface
``matrix_script_publish_feedback_closure_v1`` (defined in
:mod:`gateway.app.services.matrix_script.publish_feedback_closure`).
Surfaces the six per-row 回填 fields enumerated by
``docs/product/matrix_script_product_flow_v1.md`` §7.3:

- 发布渠道 (channel)
- 账号 ID (account)
- 发布时间 (publish_time)
- 发布链接 (publish_url)
- 发布状态 (publish_status)
- 指标入口 / metrics snapshot

The OWC-MS gate spec §3 MS-W8 binds this slice to "render closure
``variation_feedback`` per-row publish events as a multi-channel 回填 lane
(channel / account / publish_time / publish_url / publish_status /
metrics_snapshot). Entirely projection-side; no closure schema widening."
This module honors that contract verbatim:

- All reads pass through the closure view returned by
  ``closure_binding.get_closure_view_for_task(task_id)`` (read-only;
  never lazy-creates a closure).
- ``channel`` reads from ``channel_metrics[].channel_id`` only.
- ``publish_time`` reads from ``feedback_closure_records[].recorded_at``
  for the most recent ``operator_publish`` / ``platform_callback`` event
  on the variation row, and falls back to
  ``channel_metrics[].captured_at`` only if no such event exists.
- ``publish_url`` reads from ``variation_feedback[].publish_url``.
- ``publish_status`` reads from ``variation_feedback[].publish_status``
  (closed enum: ``pending`` / ``published`` / ``failed`` / ``retracted``).
- ``metrics_snapshot`` reads the latest entry of ``channel_metrics[]``
  (closed keys: ``channel_id`` / ``captured_at`` / ``impressions`` /
  ``views`` / ``engagement_rate`` / ``completion_rate`` /
  ``raw_payload_ref``).
- ``account`` is **NOT** in the contract today. Per gate spec §3 MS-W8
  ("no closure schema widening") and the user mission's MS-W8 rule
  ("no schema widening unless an extremely narrow additive field is
  strictly required and already allowed by approved OWC scope" —
  ``account_id`` is NOT in approved OWC scope), ``account`` is rendered
  with an explicit operator-language tracked-gap label so reviewers
  can see the gap without the schema being silently widened.

Hard discipline (binding under OWC-MS gate spec §4):

- No closure schema widening (§4.1). ``EVENT_KINDS`` / ``ACTOR_KINDS`` /
  ``PUBLISH_STATUS_VALUES`` / ``CHANNEL_METRICS_KEYS`` /
  ``REVIEW_ZONE_VALUES`` are read-only.
- No second authoritative producer for publishability /
  final_provenance / advisories (§4.1). The 回填 lane reads only what
  the closure carries; it does not re-derive ``publishable``.
- No invented publish state (§4.1). When the closure carries no
  matching event, the row falls back to operator-language sentinels;
  it does not synthesize a state not on the contract.
- No Hot Follow / Digital Anchor file touched (§4.2). Non-matrix_script
  callers receive ``{}``.
- No cross-cutting wiring change outside the existing
  ``kind == "matrix_script"`` branch in
  ``task_view_helpers.publish_hub_payload`` (§4.2).
- No provider / model / vendor / engine identifier admitted into any
  field (§4.4 + validator R3).
- No new endpoint; no new contract; no new ``panel_kind``.

Account-level semantics:

The closure binds to a Matrix Script packet at creation time; one
``task_id`` resolves to one ``closure_id``. Multiple accounts publishing
the same variation today land as separate ``operator_publish`` events on
the same ``variation_feedback`` row (last-write-wins per the contract).
A future cross-account fanout would land additional rows on a per-
account dimension; until then, the per-row single-account rendering is
the correct projection and the 账号 ID gap is surfaced explicitly.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

# ─────────────────────────────────────────────────────────────────────
# Closed subfield identifiers (operator-readable rendering keys).
# ─────────────────────────────────────────────────────────────────────
FIELD_CHANNEL = "channel"
FIELD_ACCOUNT = "account"
FIELD_PUBLISH_TIME = "publish_time"
FIELD_PUBLISH_URL = "publish_url"
FIELD_PUBLISH_STATUS = "publish_status"
FIELD_METRICS_SNAPSHOT = "metrics_snapshot"

FIELD_LABELS_ZH = {
    FIELD_CHANNEL: "发布渠道",
    FIELD_ACCOUNT: "账号 ID",
    FIELD_PUBLISH_TIME: "发布时间",
    FIELD_PUBLISH_URL: "发布链接",
    FIELD_PUBLISH_STATUS: "发布状态",
    FIELD_METRICS_SNAPSHOT: "指标入口（snapshot）",
}

# Closed status codes per row.
STATUS_RESOLVED = "resolved_from_closure"
STATUS_NOT_PUBLISHED = "not_published_yet"
STATUS_NO_METRICS = "no_metrics_snapshot_yet"
STATUS_UNSOURCED = "unsourced_pending_capture_capability"

STATUS_LABELS_ZH = {
    STATUS_RESOLVED: "已从 closure 解析",
    STATUS_NOT_PUBLISHED: "尚未发布",
    STATUS_NO_METRICS: "尚无指标 snapshot",
    STATUS_UNSOURCED: "尚未采集",
}

# Operator-language explanation strings keyed by status code.
ACCOUNT_TRACKED_GAP_EXPLANATION_ZH = (
    "publish 账号采集能力尚未上线；当前 closure 不携带 account_id，"
    "回填行按 variation_id 单账号渲染；待后续 OWC scope 覆盖账号粒度。"
)

# Operator-language label per closed publish_status enum value.
PUBLISH_STATUS_LABELS_ZH = {
    "pending": "待发布",
    "published": "已发布",
    "failed": "发布失败",
    "retracted": "已撤回",
}

# Closed metric snapshot keys per CHANNEL_METRICS_KEYS in the closure
# contract. Operator-language labels for each so the 指标入口 row can
# render compact summaries.
METRIC_KEY_LABELS_ZH = {
    "channel_id": "channel_id",
    "captured_at": "采集时间",
    "impressions": "曝光量",
    "views": "播放量",
    "engagement_rate": "互动率",
    "completion_rate": "完播率",
    "raw_payload_ref": "原始数据引用",
}

# Forbidden token fragments (validator R3 + design-handoff red line 6)
# scrubbed defensively against accidental upstream leakage.
FORBIDDEN_TOKEN_FRAGMENTS = ("vendor", "model_id", "provider", "engine")


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _strip_or_empty(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _scrub_forbidden(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower()
    for token in FORBIDDEN_TOKEN_FRAGMENTS:
        if token in lowered:
            return ""
    return text


def _is_matrix_script_closure(closure: Mapping[str, Any]) -> bool:
    surface = _strip_or_empty(closure.get("surface"))
    line_id = _strip_or_empty(closure.get("line_id")).lower()
    return surface == "matrix_script_publish_feedback_closure_v1" or line_id == "matrix_script"


def _records_for_variation(
    records: Iterable[Mapping[str, Any]], variation_id: str
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in records
        if isinstance(record, Mapping)
        and record.get("variation_id") == variation_id
    ]


def _latest_publish_time(
    variation_records: Iterable[Mapping[str, Any]],
    channel_metrics: Iterable[Mapping[str, Any]],
) -> tuple[str, str, Optional[str]]:
    """Resolve operator-readable publish time + status_code + source_id.

    Most recent ``operator_publish`` or ``platform_callback`` event on the
    variation row wins. Falls back to the most recent
    ``channel_metrics.captured_at`` if no publish event exists. If still
    unresolved, returns ``("", STATUS_NOT_PUBLISHED, None)``.

    NOTE: the closure contract carries ``recorded_at`` as an opaque
    string; sort order is the natural string order (lexicographic). For
    ISO-8601 timestamps that matches chronological order; for non-ISO
    inputs the projection still degrades gracefully because the
    ``channel_metrics`` fallback is independently sourced.
    """

    publish_event_kinds = ("operator_publish", "platform_callback")
    publish_records = [
        record
        for record in variation_records
        if record.get("event_kind") in publish_event_kinds
        and isinstance(record.get("recorded_at"), str)
        and record.get("recorded_at")
    ]
    if publish_records:
        publish_records.sort(key=lambda r: str(r.get("recorded_at")))
        latest = publish_records[-1]
        recorded_at = _scrub_forbidden(_strip_or_empty(latest.get("recorded_at")))
        if recorded_at:
            return recorded_at, STATUS_RESOLVED, "closure_publish_event_recorded_at"

    metrics_with_time = [
        snapshot
        for snapshot in channel_metrics
        if isinstance(snapshot, Mapping)
        and isinstance(snapshot.get("captured_at"), str)
        and snapshot.get("captured_at")
    ]
    if metrics_with_time:
        metrics_with_time.sort(key=lambda s: str(s.get("captured_at")))
        latest = metrics_with_time[-1]
        captured_at = _scrub_forbidden(_strip_or_empty(latest.get("captured_at")))
        if captured_at:
            return captured_at, STATUS_RESOLVED, "closure_channel_metrics_captured_at"

    return "", STATUS_NOT_PUBLISHED, None


def _derive_channel(
    channel_metrics: Iterable[Mapping[str, Any]],
) -> tuple[str, str, Optional[str]]:
    """Resolve channel from the most recent ``channel_metrics.channel_id``.

    When no metric snapshot has been recorded yet, falls back to the
    ``not_published_yet`` operator-language sentinel.
    """

    metrics_with_channel = [
        snapshot
        for snapshot in channel_metrics
        if isinstance(snapshot, Mapping)
        and isinstance(snapshot.get("channel_id"), str)
        and snapshot.get("channel_id")
    ]
    if not metrics_with_channel:
        return "", STATUS_NOT_PUBLISHED, None

    metrics_with_channel.sort(key=lambda s: str(s.get("captured_at") or ""))
    latest = metrics_with_channel[-1]
    channel_id = _scrub_forbidden(_strip_or_empty(latest.get("channel_id")))
    if not channel_id:
        return "", STATUS_NOT_PUBLISHED, None
    return channel_id, STATUS_RESOLVED, "closure_channel_metrics_channel_id"


def _derive_metrics_snapshot(
    channel_metrics: list[Mapping[str, Any]],
) -> tuple[dict[str, Any], str, Optional[str]]:
    """Build the metrics_snapshot summary row.

    Reads the most recent entry from ``channel_metrics[]`` (closed keys
    only). Returns ``(snapshot_map, status_code, source_id)``. The
    ``snapshot_map`` is operator-language: each metric label paired with
    its value; absent keys are omitted (no synthesized zeroes).
    """

    if not channel_metrics:
        return {}, STATUS_NO_METRICS, None

    metrics_sorted = sorted(
        channel_metrics, key=lambda s: str(s.get("captured_at") or "")
    )
    latest = metrics_sorted[-1] if isinstance(metrics_sorted[-1], Mapping) else {}
    summary: dict[str, Any] = {}
    for key in (
        "captured_at",
        "impressions",
        "views",
        "engagement_rate",
        "completion_rate",
    ):
        if key not in latest:
            continue
        value = latest.get(key)
        if isinstance(value, str):
            scrubbed = _scrub_forbidden(value)
            if not scrubbed:
                continue
            summary[key] = scrubbed
        else:
            summary[key] = value
    if not summary:
        return {}, STATUS_NO_METRICS, None
    return summary, STATUS_RESOLVED, "closure_channel_metrics_latest"


def _build_publish_time_row(
    variation_records: list[Mapping[str, Any]],
    channel_metrics: list[Mapping[str, Any]],
) -> dict[str, Any]:
    value, status_code, source_id = _latest_publish_time(
        variation_records, channel_metrics
    )
    return {
        "field_id": FIELD_PUBLISH_TIME,
        "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_TIME],
        "status_code": status_code,
        "status_label_zh": STATUS_LABELS_ZH[status_code],
        "value": value,
        "value_source_id": source_id,
    }


def _build_channel_row(
    channel_metrics: list[Mapping[str, Any]],
) -> dict[str, Any]:
    value, status_code, source_id = _derive_channel(channel_metrics)
    return {
        "field_id": FIELD_CHANNEL,
        "label_zh": FIELD_LABELS_ZH[FIELD_CHANNEL],
        "status_code": status_code,
        "status_label_zh": STATUS_LABELS_ZH[status_code],
        "value": value,
        "value_source_id": source_id,
    }


def _build_account_row() -> dict[str, Any]:
    """Build the tracked-gap account row.

    The closure has no ``account_id`` field; per gate spec §4.1 + §3
    MS-W8 ("no closure schema widening") and the user mission's MS-W8
    rule (no widening except inside approved OWC scope), this row is
    rendered as an explicit operator-language tracked gap. The label is
    closed and the explanation cites the gap's anchor.
    """

    return {
        "field_id": FIELD_ACCOUNT,
        "label_zh": FIELD_LABELS_ZH[FIELD_ACCOUNT],
        "status_code": STATUS_UNSOURCED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_UNSOURCED],
        "value": "",
        "value_source_id": None,
        "tracked_gap_explanation_zh": ACCOUNT_TRACKED_GAP_EXPLANATION_ZH,
    }


def _build_publish_url_row(
    variation_row: Mapping[str, Any],
) -> dict[str, Any]:
    publish_url = _scrub_forbidden(_strip_or_empty(variation_row.get("publish_url")))
    if publish_url:
        return {
            "field_id": FIELD_PUBLISH_URL,
            "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_URL],
            "status_code": STATUS_RESOLVED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
            "value": publish_url,
            "value_source_id": "closure_variation_feedback_publish_url",
        }
    return {
        "field_id": FIELD_PUBLISH_URL,
        "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_URL],
        "status_code": STATUS_NOT_PUBLISHED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_NOT_PUBLISHED],
        "value": "",
        "value_source_id": None,
    }


def _build_publish_status_row(
    variation_row: Mapping[str, Any],
) -> dict[str, Any]:
    raw_status = _strip_or_empty(variation_row.get("publish_status"))
    if raw_status in PUBLISH_STATUS_LABELS_ZH:
        return {
            "field_id": FIELD_PUBLISH_STATUS,
            "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_STATUS],
            "status_code": STATUS_RESOLVED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
            "value": raw_status,
            "value_label_zh": PUBLISH_STATUS_LABELS_ZH[raw_status],
            "value_source_id": "closure_variation_feedback_publish_status",
        }
    # Defensive: a closure that drops to an out-of-enum value should not
    # crash the publish hub. Render as not_published_yet with an explicit
    # value_source_id so reviewers can trace the violation.
    return {
        "field_id": FIELD_PUBLISH_STATUS,
        "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_STATUS],
        "status_code": STATUS_NOT_PUBLISHED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_NOT_PUBLISHED],
        "value": "",
        "value_label_zh": PUBLISH_STATUS_LABELS_ZH["pending"],
        "value_source_id": None,
    }


def _build_metrics_row(
    channel_metrics: list[Mapping[str, Any]],
) -> dict[str, Any]:
    snapshot, status_code, source_id = _derive_metrics_snapshot(channel_metrics)
    metrics_pairs = []
    for key in (
        "captured_at",
        "impressions",
        "views",
        "engagement_rate",
        "completion_rate",
    ):
        if key in snapshot:
            metrics_pairs.append(
                {
                    "metric_id": key,
                    "label_zh": METRIC_KEY_LABELS_ZH[key],
                    "value": snapshot[key],
                }
            )
    return {
        "field_id": FIELD_METRICS_SNAPSHOT,
        "label_zh": FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
        "status_code": status_code,
        "status_label_zh": STATUS_LABELS_ZH[status_code],
        "value": "",
        "value_source_id": source_id,
        "metrics_pairs": metrics_pairs,
    }


def _build_lane_for_variation(
    variation_row: Mapping[str, Any],
    closure_records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    variation_id = _strip_or_empty(variation_row.get("variation_id"))
    channel_metrics = _safe_list(variation_row.get("channel_metrics"))
    variation_records = _records_for_variation(closure_records, variation_id)

    fields = [
        _build_channel_row(channel_metrics),
        _build_account_row(),
        _build_publish_time_row(variation_records, channel_metrics),
        _build_publish_url_row(variation_row),
        _build_publish_status_row(variation_row),
        _build_metrics_row(channel_metrics),
    ]

    return {
        "variation_id": variation_id,
        "lane_label_zh": f"variation_id · {variation_id}",
        "fields": fields,
        "channel_metrics_count": len(channel_metrics),
        "publish_event_count": sum(
            1
            for record in variation_records
            if record.get("event_kind") in ("operator_publish", "platform_callback")
        ),
    }


def derive_matrix_script_delivery_backfill(
    closure: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Matrix Script Delivery Center 回填 multi-channel view.

    Input: the matrix_script publish-feedback closure view returned by
    ``closure_binding.get_closure_view_for_task(task_id)``. Returns
    ``{}`` for ``None`` / non-matrix_script closures so the caller can
    attach the result without further gating.

    Returns the closed comprehension shape:

    .. code-block:: python

        {
            "is_matrix_script": True,
            "panel_title_zh": "Matrix Script · 交付中心 · 多渠道回填",
            "panel_subtitle_zh": "...",
            "field_legend_zh": ["发布渠道", "账号 ID", "发布时间", ...],
            "lanes": [
                {
                    "variation_id": "...",
                    "lane_label_zh": "...",
                    "fields": [
                        {"field_id": "channel", "label_zh": "发布渠道", "status_code": ..., "value": ..., ...},
                        {"field_id": "account", ...},
                        {"field_id": "publish_time", ...},
                        {"field_id": "publish_url", ...},
                        {"field_id": "publish_status", ...},
                        {"field_id": "metrics_snapshot", ...},
                    ],
                    "channel_metrics_count": ...,
                    "publish_event_count": ...,
                },
                ...
            ],
            "lane_count": ...,
            "tracked_gap_summary_zh": "...",
        }
    """

    closure_view = _safe_mapping(closure)
    if not closure_view or not _is_matrix_script_closure(closure_view):
        return {}

    variation_feedback = _safe_list(closure_view.get("variation_feedback"))
    closure_records = _safe_list(closure_view.get("feedback_closure_records"))

    lanes = [
        _build_lane_for_variation(row, closure_records)
        for row in variation_feedback
        if isinstance(row, Mapping)
    ]

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Matrix Script · 交付中心 · 多渠道回填",
        "panel_subtitle_zh": (
            "按 product-flow §7.3 的回填对象投射六项 operator 字段（发布渠道 / "
            "账号 ID / 发布时间 / 发布链接 / 发布状态 / 指标入口）；只读理解层，"
            "不发明事实，不改 closure 契约，不引入第二条真值路径。"
        ),
        "field_legend_zh": [
            FIELD_LABELS_ZH[FIELD_CHANNEL],
            FIELD_LABELS_ZH[FIELD_ACCOUNT],
            FIELD_LABELS_ZH[FIELD_PUBLISH_TIME],
            FIELD_LABELS_ZH[FIELD_PUBLISH_URL],
            FIELD_LABELS_ZH[FIELD_PUBLISH_STATUS],
            FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
        ],
        "lanes": lanes,
        "lane_count": len(lanes),
        "tracked_gap_summary_zh": (
            "账号 ID 字段对应的 closure 字段尚未上线（见每行 account_id 行的 "
            "`tracked_gap_explanation_zh`）；其余字段均为只读投射。"
        ),
    }


__all__ = [
    "ACCOUNT_TRACKED_GAP_EXPLANATION_ZH",
    "FIELD_ACCOUNT",
    "FIELD_CHANNEL",
    "FIELD_LABELS_ZH",
    "FIELD_METRICS_SNAPSHOT",
    "FIELD_PUBLISH_STATUS",
    "FIELD_PUBLISH_TIME",
    "FIELD_PUBLISH_URL",
    "METRIC_KEY_LABELS_ZH",
    "PUBLISH_STATUS_LABELS_ZH",
    "STATUS_LABELS_ZH",
    "STATUS_NOT_PUBLISHED",
    "STATUS_NO_METRICS",
    "STATUS_RESOLVED",
    "STATUS_UNSOURCED",
    "derive_matrix_script_delivery_backfill",
]
