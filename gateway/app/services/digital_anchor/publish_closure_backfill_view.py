"""Digital Anchor Publish Closure multi-channel 回填 rendering (OWC-DA PR-3 / DA-W9).

Pure presentation-layer projection over the contract-frozen Digital
Anchor publish-feedback closure surface
``digital_anchor_publish_feedback_closure_v1`` (defined in
:mod:`gateway.app.services.digital_anchor.publish_feedback_closure`).
Surfaces the six per-row 回填 fields enumerated by
``docs/product/digital_anchor_product_flow_v1.md`` §7.3:

- 发布渠道 (channel)
- 账号 ID (account)
- 发布时间 (publish_time)
- 发布链接 (publish_url)
- 发布状态 (publish_status)
- 指标入口 / metrics snapshot

The OWC-DA gate spec §3 DA-W9 binds this slice to "render closure
``role_feedback[]`` and ``segment_feedback[]`` per-row publish events
as 回填 lanes (channel / account / publish_time / publish_url /
publish_status / metrics_snapshot per row). Use D.1 ``publish_status``
enum (``pending / published / failed / retracted``) directly." This
module honors that contract verbatim:

- All reads pass through the closure view returned by
  ``closure_binding.get_closure_view_for_task(task_id)`` (read-only;
  never lazy-creates a closure).
- ``channel`` reads from ``row.channel_metrics[].channel_id`` only —
  the field is **NOT** enumerated on the closure contract today (see
  ``publish_feedback_closure.CHANNEL_METRICS_KEYS`` =
  ``{views, likes, shares, comments, watch_seconds, captured_at}``).
  Per gate spec §3 DA-W9 ("no closure envelope redesign"; "additive
  field changes are forbidden unless strictly proven necessary and
  explicitly justified"), ``channel`` is rendered as an explicit
  operator-language tracked-gap mirroring the OWC-MS MS-W8 precedent.
- ``account`` is **NOT** in the closure contract today. Same gate-
  spec discipline applies; rendered as an explicit tracked-gap.
- ``publish_time`` reads from ``feedback_closure_records[].recorded_at``
  for the most recent D.1 publish event on the row (events with
  ``event_kind`` ∈ ``{publish_attempted, publish_accepted,
  publish_rejected, publish_retracted}``), with fallback to
  ``row.last_event_recorded_at``; further fallback to the latest
  ``row.channel_metrics[].captured_at``.
- ``publish_url`` reads from ``row.publish_url``.
- ``publish_status`` reads from ``row.publish_status`` (D.1 closed
  enum: ``pending`` / ``published`` / ``failed`` / ``retracted``).
- ``metrics_snapshot`` reads the latest entry of
  ``row.channel_metrics[]`` (closed keys per
  ``CHANNEL_METRICS_KEYS``).

Hard discipline (binding under OWC-DA gate spec §4):

- No closure schema widening (§4.1). ``D1_EVENT_KINDS`` /
  ``D1_PUBLISH_STATUS_VALUES`` / ``D1_ROW_SCOPES`` /
  ``CHANNEL_METRICS_KEYS`` / ``RECORD_KINDS`` / ``REVIEW_ZONE_VALUES``
  are read-only.
- No second authoritative producer for publishability /
  ``final_provenance`` / advisories (§4.1). The 回填 lane reads only
  what the closure carries; it does not re-derive ``publishable``.
- No invented publish state (§4.1). When the closure carries no
  matching event, the row falls back to operator-language sentinels;
  it does not synthesize a state not on the contract.
- No Hot Follow / Matrix Script file touched (§4.2). Non-Digital-Anchor
  callers receive ``{}``.
- No cross-cutting wiring change outside the existing
  ``kind == "digital_anchor"`` branch in
  ``task_view_helpers.publish_hub_payload`` (§4.2).
- No provider / model / vendor / engine identifier admitted into any
  field (§4.4 + validator R3).
- No new endpoint; no new contract; no new ``panel_kind``.

Account-level / channel-level semantics:

The Digital Anchor closure binds to a single ``task_id``; one task
resolves to one closure with one ``role_feedback[]`` row per role and
one ``segment_feedback[]`` row per segment. Multiple accounts /
channels publishing the same role or segment today land as separate
``publish_*`` D.1 events on the same row (last-write-wins per the
contract) or as separate ``metrics_snapshot`` events appending to the
row's ``channel_metrics[]``. A future cross-account / cross-channel
fanout would require contract additions to either (a) add an
``account_id`` / ``channel_id`` field at the row level, or (b)
introduce a new lane enumeration. Until then the per-row single-channel
rendering is the correct projection and the 账号 ID + 渠道 ID gaps are
surfaced explicitly.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

# Closed lane scope enums (mirror ``D1_ROW_SCOPES`` in publish_feedback_closure).
LANE_SCOPE_ROLE = "role"
LANE_SCOPE_SEGMENT = "segment"

LANE_SCOPE_LABELS_ZH = {
    LANE_SCOPE_ROLE: "role · 角色级回填",
    LANE_SCOPE_SEGMENT: "segment · 段落级回填",
}

# Closed subfield identifiers (operator-readable rendering keys).
FIELD_CHANNEL = "channel"
FIELD_ACCOUNT = "account"
FIELD_PUBLISH_TIME = "publish_time"
FIELD_PUBLISH_URL = "publish_url"
FIELD_PUBLISH_STATUS = "publish_status"
FIELD_METRICS_SNAPSHOT = "metrics_snapshot"

FIELD_ORDER = (
    FIELD_CHANNEL,
    FIELD_ACCOUNT,
    FIELD_PUBLISH_TIME,
    FIELD_PUBLISH_URL,
    FIELD_PUBLISH_STATUS,
    FIELD_METRICS_SNAPSHOT,
)

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

# Operator-language tracked-gap explanations.
ACCOUNT_TRACKED_GAP_EXPLANATION_ZH = (
    "publish 账号采集能力尚未上线；当前 closure 不携带 account_id，"
    "回填行按 row_id（role_id / segment_id）单账号渲染；待后续 OWC scope 覆盖账号粒度。"
)
CHANNEL_TRACKED_GAP_EXPLANATION_ZH = (
    "channel_id 不在 closure 顶层契约（CHANNEL_METRICS_KEYS 不含 channel_id）；"
    "当 row 上未触发 metrics_snapshot 事件时按 unsourced 兜底，不在此处合成 channel_id。"
)

# Operator-language label per closed D.1 publish_status enum value.
PUBLISH_STATUS_LABELS_ZH = {
    "pending": "待发布",
    "published": "已发布",
    "failed": "发布失败",
    "retracted": "已撤回",
}

# Closed D.1 publish-event kinds (mirror ``D1_EVENT_KINDS``); only the
# four publish-state-mutating events feed the publish_time projection.
PUBLISH_TIME_EVENT_KINDS = (
    "publish_attempted",
    "publish_accepted",
    "publish_rejected",
    "publish_retracted",
)

# Closed metric snapshot keys per CHANNEL_METRICS_KEYS in the closure
# contract. Operator-language labels for each so the 指标入口 row can
# render compact summaries.
METRIC_KEY_LABELS_ZH = {
    "captured_at": "采集时间",
    "views": "播放量",
    "likes": "点赞数",
    "shares": "分享数",
    "comments": "评论数",
    "watch_seconds": "总观看秒数",
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


def _is_digital_anchor_closure(closure: Mapping[str, Any]) -> bool:
    surface = _strip_or_empty(closure.get("surface"))
    line_id = _strip_or_empty(closure.get("line_id")).lower()
    return (
        surface == "digital_anchor_publish_feedback_closure_v1"
        or line_id == "digital_anchor"
    )


def _records_for_row(
    records: Iterable[Mapping[str, Any]],
    row_scope: str,
    row_id: str,
) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        record_scope = _strip_or_empty(record.get("row_scope"))
        record_row_id = _strip_or_empty(record.get("row_id"))
        if record_scope == row_scope and record_row_id == row_id:
            out.append(record)
    return out


def _latest_publish_time(
    *,
    row: Mapping[str, Any],
    row_records: Iterable[Mapping[str, Any]],
) -> tuple[str, str, Optional[str]]:
    """Resolve operator-readable publish time + status_code + source_id.

    Order of preference:
    1. Most recent publish-state-mutating event on the row records
       (events whose ``event_kind`` ∈ ``PUBLISH_TIME_EVENT_KINDS``).
    2. Row-level ``last_event_recorded_at`` (recorded by
       ``apply_writeback_event``).
    3. Most recent ``row.channel_metrics[].captured_at`` (metrics
       snapshot fallback).
    4. ``("", STATUS_NOT_PUBLISHED, None)``.

    Sort order is the natural string order; ISO-8601 timestamps sort
    chronologically.
    """
    publish_records = [
        record
        for record in row_records
        if _strip_or_empty(record.get("event_kind")) in PUBLISH_TIME_EVENT_KINDS
        and isinstance(record.get("recorded_at"), str)
        and record.get("recorded_at")
    ]
    if publish_records:
        publish_records.sort(key=lambda r: str(r.get("recorded_at")))
        recorded_at = _scrub_forbidden(
            _strip_or_empty(publish_records[-1].get("recorded_at"))
        )
        if recorded_at:
            return (
                recorded_at,
                STATUS_RESOLVED,
                "closure_records.publish_event.recorded_at",
            )

    last_event_recorded_at = _scrub_forbidden(
        _strip_or_empty(row.get("last_event_recorded_at"))
    )
    if last_event_recorded_at:
        return (
            last_event_recorded_at,
            STATUS_RESOLVED,
            "row.last_event_recorded_at",
        )

    metrics_with_time = [
        snapshot
        for snapshot in _safe_list(row.get("channel_metrics"))
        if isinstance(snapshot, Mapping)
        and isinstance(snapshot.get("captured_at"), str)
        and snapshot.get("captured_at")
    ]
    if metrics_with_time:
        metrics_with_time.sort(key=lambda s: str(s.get("captured_at")))
        captured_at = _scrub_forbidden(
            _strip_or_empty(metrics_with_time[-1].get("captured_at"))
        )
        if captured_at:
            return (
                captured_at,
                STATUS_RESOLVED,
                "row.channel_metrics.captured_at",
            )

    return "", STATUS_NOT_PUBLISHED, None


def _build_channel_row(
    channel_metrics: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Render the channel row.

    The closure contract today has no ``channel_id`` field; the
    ``CHANNEL_METRICS_KEYS`` set explicitly excludes it. When upstream
    integrations later land an ``id``-bearing snapshot through
    ``metrics_snapshot``, the latest non-forbidden string would surface
    here. Until then, render as an operator-language tracked-gap.
    """
    if not channel_metrics:
        return {
            "field_id": FIELD_CHANNEL,
            "label_zh": FIELD_LABELS_ZH[FIELD_CHANNEL],
            "status_code": STATUS_UNSOURCED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_UNSOURCED],
            "value": "",
            "value_source_id": None,
            "tracked_gap_explanation_zh": CHANNEL_TRACKED_GAP_EXPLANATION_ZH,
        }
    # Defensive: if a future snapshot carried an opaque non-forbidden
    # channel identifier, render it. Today no key in CHANNEL_METRICS_KEYS
    # holds that semantic, so this branch is reachable only via deliberate
    # forward-compatibility seeding.
    metrics_with_channel = [
        snapshot
        for snapshot in channel_metrics
        if isinstance(snapshot, Mapping)
        and isinstance(snapshot.get("channel_id"), str)
        and snapshot.get("channel_id")
    ]
    if not metrics_with_channel:
        return {
            "field_id": FIELD_CHANNEL,
            "label_zh": FIELD_LABELS_ZH[FIELD_CHANNEL],
            "status_code": STATUS_UNSOURCED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_UNSOURCED],
            "value": "",
            "value_source_id": None,
            "tracked_gap_explanation_zh": CHANNEL_TRACKED_GAP_EXPLANATION_ZH,
        }
    metrics_with_channel.sort(key=lambda s: str(s.get("captured_at") or ""))
    latest = metrics_with_channel[-1]
    channel_id = _scrub_forbidden(_strip_or_empty(latest.get("channel_id")))
    if not channel_id:
        return {
            "field_id": FIELD_CHANNEL,
            "label_zh": FIELD_LABELS_ZH[FIELD_CHANNEL],
            "status_code": STATUS_UNSOURCED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_UNSOURCED],
            "value": "",
            "value_source_id": None,
            "tracked_gap_explanation_zh": CHANNEL_TRACKED_GAP_EXPLANATION_ZH,
        }
    return {
        "field_id": FIELD_CHANNEL,
        "label_zh": FIELD_LABELS_ZH[FIELD_CHANNEL],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "value": channel_id,
        "value_source_id": "row.channel_metrics.channel_id",
    }


def _build_account_row() -> dict[str, Any]:
    """Build the tracked-gap account row.

    The closure has no ``account_id`` field today; per gate spec §4.1 +
    §3 DA-W9 ("no closure envelope redesign"; "additive field changes
    are forbidden unless strictly proven necessary and explicitly
    justified"), this row is rendered as an explicit operator-language
    tracked gap. The label is closed and the explanation cites the gap
    anchor.
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


def _build_publish_time_row(
    *,
    row: Mapping[str, Any],
    row_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    value, status_code, source_id = _latest_publish_time(
        row=row, row_records=row_records
    )
    return {
        "field_id": FIELD_PUBLISH_TIME,
        "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_TIME],
        "status_code": status_code,
        "status_label_zh": STATUS_LABELS_ZH[status_code],
        "value": value,
        "value_source_id": source_id,
    }


def _build_publish_url_row(row: Mapping[str, Any]) -> dict[str, Any]:
    publish_url = _scrub_forbidden(_strip_or_empty(row.get("publish_url")))
    if publish_url:
        return {
            "field_id": FIELD_PUBLISH_URL,
            "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_URL],
            "status_code": STATUS_RESOLVED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
            "value": publish_url,
            "value_source_id": "row.publish_url",
        }
    return {
        "field_id": FIELD_PUBLISH_URL,
        "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_URL],
        "status_code": STATUS_NOT_PUBLISHED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_NOT_PUBLISHED],
        "value": "",
        "value_source_id": None,
    }


def _build_publish_status_row(row: Mapping[str, Any]) -> dict[str, Any]:
    raw_status = _strip_or_empty(row.get("publish_status"))
    if raw_status in PUBLISH_STATUS_LABELS_ZH:
        return {
            "field_id": FIELD_PUBLISH_STATUS,
            "label_zh": FIELD_LABELS_ZH[FIELD_PUBLISH_STATUS],
            "status_code": STATUS_RESOLVED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
            "value": raw_status,
            "value_label_zh": PUBLISH_STATUS_LABELS_ZH[raw_status],
            "value_source_id": "row.publish_status",
        }
    # Defensive: a closure that drops to an out-of-enum value should not
    # crash the publish hub. Render as not_published_yet with no source id
    # so reviewers can trace the violation.
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
    if not channel_metrics:
        return {
            "field_id": FIELD_METRICS_SNAPSHOT,
            "label_zh": FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
            "status_code": STATUS_NO_METRICS,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_NO_METRICS],
            "value": "",
            "value_source_id": None,
            "metrics_pairs": [],
        }
    metrics_sorted = sorted(
        [s for s in channel_metrics if isinstance(s, Mapping)],
        key=lambda s: str(s.get("captured_at") or ""),
    )
    if not metrics_sorted:
        return {
            "field_id": FIELD_METRICS_SNAPSHOT,
            "label_zh": FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
            "status_code": STATUS_NO_METRICS,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_NO_METRICS],
            "value": "",
            "value_source_id": None,
            "metrics_pairs": [],
        }
    latest = metrics_sorted[-1]
    metrics_pairs: list[dict[str, Any]] = []
    for key in (
        "captured_at",
        "views",
        "likes",
        "shares",
        "comments",
        "watch_seconds",
    ):
        if key not in latest:
            continue
        value = latest.get(key)
        if isinstance(value, str):
            scrubbed = _scrub_forbidden(value)
            if not scrubbed:
                continue
            metrics_pairs.append(
                {
                    "metric_id": key,
                    "label_zh": METRIC_KEY_LABELS_ZH[key],
                    "value": scrubbed,
                }
            )
        else:
            metrics_pairs.append(
                {
                    "metric_id": key,
                    "label_zh": METRIC_KEY_LABELS_ZH[key],
                    "value": value,
                }
            )
    if not metrics_pairs:
        return {
            "field_id": FIELD_METRICS_SNAPSHOT,
            "label_zh": FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
            "status_code": STATUS_NO_METRICS,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_NO_METRICS],
            "value": "",
            "value_source_id": None,
            "metrics_pairs": [],
        }
    return {
        "field_id": FIELD_METRICS_SNAPSHOT,
        "label_zh": FIELD_LABELS_ZH[FIELD_METRICS_SNAPSHOT],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "value": "",
        "value_source_id": "row.channel_metrics.latest",
        "metrics_pairs": metrics_pairs,
    }


def _build_lane_for_row(
    *,
    row_scope: str,
    row: Mapping[str, Any],
    row_id: str,
    row_id_label_zh: str,
    closure_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    channel_metrics = _safe_list(row.get("channel_metrics"))
    row_records = _records_for_row(closure_records, row_scope, row_id)

    fields = [
        _build_channel_row(channel_metrics),
        _build_account_row(),
        _build_publish_time_row(row=row, row_records=row_records),
        _build_publish_url_row(row),
        _build_publish_status_row(row),
        _build_metrics_row(channel_metrics),
    ]

    lane_label_zh = (
        LANE_SCOPE_LABELS_ZH[row_scope] + " · " + row_id
        if row_id_label_zh == row_id
        else f"{LANE_SCOPE_LABELS_ZH[row_scope]} · {row_id}（{row_id_label_zh}）"
    )

    return {
        "row_scope": row_scope,
        "row_id": row_id,
        "row_id_label_zh": row_id_label_zh,
        "lane_label_zh": lane_label_zh,
        "fields": fields,
        "channel_metrics_count": len(channel_metrics),
        "publish_event_count": sum(
            1
            for record in row_records
            if _strip_or_empty(record.get("event_kind"))
            in PUBLISH_TIME_EVENT_KINDS
        ),
    }


def _empty_bundle(*, panel_subtitle_zh_override: Optional[str] = None) -> dict[str, Any]:
    """Render the digital_anchor-shaped bundle with zero lanes.

    Mirrors the OWC-MS PR-3 P1 fix at
    ``matrix_script/delivery_backfill_view.py::derive_matrix_script_delivery_backfill``
    where the no-closure-yet path emits the panel + an empty-state
    message instead of hiding the card. Reviewers and operators see the
    panel exists and what it's for.
    """
    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Digital Anchor · 交付中心 · 多渠道回填",
        "panel_subtitle_zh": (
            panel_subtitle_zh_override
            or (
                "按 product-flow §7.3 的回填对象投射六项 operator 字段（发布渠道 / "
                "账号 ID / 发布时间 / 发布链接 / 发布状态 / 指标入口）；只读理解层，"
                "不发明事实，不改 closure 契约，不引入第二条真值路径。"
            )
        ),
        "field_legend_zh": [FIELD_LABELS_ZH[fid] for fid in FIELD_ORDER],
        "lanes": [],
        "lane_count": 0,
        "tracked_gap_summary_zh": (
            "尚未生成 closure；点击发布反馈闭环面板的“初始化 closure”可基于当前 "
            "packet 创建，回填行将按 row_scope（role / segment）出现。"
        ),
    }


def derive_digital_anchor_publish_closure_backfill(
    closure: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Delivery Center 多渠道回填 view.

    Input: the digital_anchor publish-feedback closure view returned by
    ``closure_binding.get_closure_view_for_task(task_id)``. Returns
    ``{}`` for non-Digital-Anchor closures so the caller can attach the
    result without further gating.

    For ``None`` input the function emits the digital-anchor-shaped
    bundle with zero lanes (mirror of MS-W8 P1 fix).

    Returns the closed comprehension shape:

    .. code-block:: python

        {
            "is_digital_anchor": True,
            "panel_title_zh": "Digital Anchor · 交付中心 · 多渠道回填",
            "panel_subtitle_zh": "...",
            "field_legend_zh": ["发布渠道", "账号 ID", ...],
            "lanes": [
                {
                    "row_scope": "role",
                    "row_id": "role_anchor_a",
                    "row_id_label_zh": "Anchor A",
                    "lane_label_zh": "...",
                    "fields": [...],  # six fields per FIELD_ORDER
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
    if not closure_view:
        return _empty_bundle()
    if not _is_digital_anchor_closure(closure_view):
        return {}

    role_feedback = _safe_list(closure_view.get("role_feedback"))
    segment_feedback = _safe_list(closure_view.get("segment_feedback"))
    closure_records = _safe_list(closure_view.get("feedback_closure_records"))

    lanes: list[dict[str, Any]] = []
    for row in role_feedback:
        if not isinstance(row, Mapping):
            continue
        row_id = _strip_or_empty(row.get("role_id"))
        if not row_id:
            continue
        display_name = _scrub_forbidden(
            _strip_or_empty(row.get("role_display_name"))
        ) or row_id
        lanes.append(
            _build_lane_for_row(
                row_scope=LANE_SCOPE_ROLE,
                row=row,
                row_id=row_id,
                row_id_label_zh=display_name,
                closure_records=closure_records,
            )
        )
    for row in segment_feedback:
        if not isinstance(row, Mapping):
            continue
        row_id = _strip_or_empty(row.get("segment_id"))
        if not row_id:
            continue
        binds_role_id = _scrub_forbidden(
            _strip_or_empty(row.get("binds_role_id"))
        ) or row_id
        lanes.append(
            _build_lane_for_row(
                row_scope=LANE_SCOPE_SEGMENT,
                row=row,
                row_id=row_id,
                row_id_label_zh=binds_role_id,
                closure_records=closure_records,
            )
        )

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Digital Anchor · 交付中心 · 多渠道回填",
        "panel_subtitle_zh": (
            "按 product-flow §7.3 的回填对象投射六项 operator 字段（发布渠道 / "
            "账号 ID / 发布时间 / 发布链接 / 发布状态 / 指标入口）；只读理解层，"
            "不发明事实，不改 closure 契约，不引入第二条真值路径。"
        ),
        "field_legend_zh": [FIELD_LABELS_ZH[fid] for fid in FIELD_ORDER],
        "lanes": lanes,
        "lane_count": len(lanes),
        "tracked_gap_summary_zh": (
            "发布渠道 / 账号 ID 字段对应的 closure 字段尚未上线（见每行 "
            "`tracked_gap_explanation_zh`）；其余字段均为只读投射。"
        ),
    }


__all__ = [
    "ACCOUNT_TRACKED_GAP_EXPLANATION_ZH",
    "CHANNEL_TRACKED_GAP_EXPLANATION_ZH",
    "FIELD_ACCOUNT",
    "FIELD_CHANNEL",
    "FIELD_LABELS_ZH",
    "FIELD_METRICS_SNAPSHOT",
    "FIELD_ORDER",
    "FIELD_PUBLISH_STATUS",
    "FIELD_PUBLISH_TIME",
    "FIELD_PUBLISH_URL",
    "LANE_SCOPE_LABELS_ZH",
    "LANE_SCOPE_ROLE",
    "LANE_SCOPE_SEGMENT",
    "METRIC_KEY_LABELS_ZH",
    "PUBLISH_STATUS_LABELS_ZH",
    "PUBLISH_TIME_EVENT_KINDS",
    "STATUS_LABELS_ZH",
    "STATUS_NOT_PUBLISHED",
    "STATUS_NO_METRICS",
    "STATUS_RESOLVED",
    "STATUS_UNSOURCED",
    "derive_digital_anchor_publish_closure_backfill",
]
