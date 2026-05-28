"""Matrix Script Result-Capability Recovery — RC PR-4 helper (RC-R7 + RC-R8).

Pure presentation-layer projection that explains, per variation, the
**publish / backfill readiness** in operator language. Reads only the
unified ``publish_readiness`` producer output, the Matrix Script
``delivery_comprehension`` lanes, and the publish-feedback closure
view (read-only). Never widens any closure schema and never invents
publish state.

Authority: ``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R7 + §3 RC-R8 + §5 RC PR-4.

Hard discipline (binding per recovery amendment §7 + recovery gate
spec §4):

- **No second authoritative truth source.** Publishability comes from
  the unified PR-1 ``publish_readiness`` producer; delivery lane
  classification comes from OWC-MS PR-3 ``delivery_comprehension``;
  closure publish events are read-only via
  ``matrix_script_publish_feedback_closure``.
- **No fake ``final_video`` (RC-R8).** No media URL, no
  ``http(s)://`` substring, no ``.mp4`` / ``.mov`` substring, no
  ``final_video_url`` / ``preview_url`` substring is admitted to the
  payload. The closure ``publish_url`` is consumed read-only — it is
  the operator's own published link, not a synthesized deliverable —
  and it is never rendered until the closure ``publish_status`` is
  one of the closed-enum non-pending values.
- **No closed-enum widening.** Reads only ``publish_status`` /
  ``publish_url`` from ``variation_feedback[]``; reads only
  ``head_reason`` from publish_readiness.
- **No raw internal handles.** No ``script_slot_ref`` /
  ``slot_body_ref`` / ``content://`` substring leakage.
- Hot Follow / Digital Anchor / baseline publish hubs MUST NOT
  receive any of these objects — the public helper returns ``{}``
  when the publish-feedback closure is not Matrix Script (or when
  there is no readable variants payload yet).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

# Closed readiness enum.
READINESS_PUBLISHABLE_NOW = "publishable_now"
READINESS_GATED = "gated_pending_publish_readiness"
READINESS_ALREADY_PUBLISHED = "already_published_backfill_pending_metrics"
READINESS_ALREADY_FAILED = "already_failed_pending_retry"
READINESS_TRACKED_GAP = "tracked_gap_no_artifact"

READINESS_LABELS_ZH = {
    READINESS_PUBLISHABLE_NOW: "可发布 · 现在即可发布",
    READINESS_GATED: "暂不可发布 · 发布门禁阻塞",
    READINESS_ALREADY_PUBLISHED: "已发布 · 等待回填指标",
    READINESS_ALREADY_FAILED: "上次发布失败 · 待重试",
    READINESS_TRACKED_GAP: "暂无可发布对象 · 跟踪缺口",
}

READINESS_NEXT_INPUT_ZH = {
    READINESS_PUBLISHABLE_NOW: (
        "在交付页面选择渠道与账号执行发布；本面板不展示完整成片或外部链接，"
        "操作后回到本面板查看回填状态。"
    ),
    READINESS_GATED: (
        "先解除发布门禁的阻塞项再继续；阻塞原因显示在「主视频结果」面板，"
        "未就绪的必交付分区缺口可在交付页面查看。"
    ),
    READINESS_ALREADY_PUBLISHED: (
        "回到交付页面的多渠道回填面板补齐渠道、时间、指标快照；"
        "本面板不重复展示发布链接。"
    ),
    READINESS_ALREADY_FAILED: (
        "查看该变体最近一次发布失败的原因；纠正后再次发布即可，"
        "发布条件由统一上游决定可发性。"
    ),
    READINESS_TRACKED_GAP: (
        "等待 Phase B / 脚本投射 / 必交付物到位；本面板会随上游真值补齐重新出现。"
    ),
}

# Forbidden token fragments (validator R3 + design-handoff red line 6).
FORBIDDEN_TOKEN_FRAGMENTS = ("vendor", "model_id", "provider", "engine")
FORBIDDEN_URL_FRAGMENTS = (
    "http://",
    "https://",
    ".mp4",
    ".mov",
    "final_video_url",
    "preview_url",
    "content://",
)

NO_FAKE_FINAL_VIDEO_NOTE_ZH = (
    "本面板不合成 final_video / 媒体链接 / 任何外部 URL；"
    "若上游已存在 closure publish_url，会引导前往多渠道回填面板查看，"
    "本面板不直接展示该 URL 字符串。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _scrub(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if not text:
        return ""
    lowered = text.lower()
    for token in FORBIDDEN_TOKEN_FRAGMENTS:
        if token in lowered:
            return ""
    for token in FORBIDDEN_URL_FRAGMENTS:
        if token in lowered:
            return ""
    return text


def _is_matrix_script_closure(closure: Mapping[str, Any]) -> bool:
    surface = str(closure.get("surface") or "").strip()
    line_id = str(closure.get("line_id") or "").strip().lower()
    return (
        surface == "matrix_script_publish_feedback_closure_v1"
        or line_id == "matrix_script"
    )


def _publish_status_for_variation(
    closure: Mapping[str, Any], variation_id: str
) -> str | None:
    """Return the closed-enum ``publish_status`` for ``variation_id``.

    Reads only ``variation_feedback[].publish_status`` (closed enum:
    ``pending`` / ``published`` / ``failed`` / ``retracted``). Returns
    ``None`` when the closure does not carry a row for the variation
    or when the value is out of enum.
    """
    if not variation_id:
        return None
    rows = _safe_list(closure.get("variation_feedback"))
    closed_values = ("pending", "published", "failed", "retracted")
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("variation_id") != variation_id:
            continue
        status = str(row.get("publish_status") or "").strip().lower()
        if status in closed_values:
            return status
        return None
    return None


def _has_required_blocking_lane(delivery_comprehension: Mapping[str, Any]) -> bool:
    lanes = _safe_mapping(delivery_comprehension.get("lanes"))
    required_blocking = _safe_mapping(lanes.get("required_blocking"))
    rows = _safe_list(required_blocking.get("rows"))
    return any(isinstance(row, Mapping) for row in rows)


def _classify_readiness(
    *,
    publishable: bool,
    head_reason: Optional[str],
    closure_status: Optional[str],
    has_bound_slot: bool,
    has_required_lane: bool,
) -> str:
    if closure_status == "published" or closure_status == "retracted":
        return READINESS_ALREADY_PUBLISHED
    if closure_status == "failed":
        return READINESS_ALREADY_FAILED
    if not has_bound_slot and not has_required_lane:
        return READINESS_TRACKED_GAP
    if publishable:
        return READINESS_PUBLISHABLE_NOW
    return READINESS_GATED


def _gap_summary_zh(
    *,
    readiness: str,
    has_bound_slot: bool,
    head_reason_label: Optional[str],
    required_blocking_gap_kinds: list[str],
) -> str:
    bits: list[str] = []
    if readiness == READINESS_GATED:
        if head_reason_label:
            bits.append(f"publish_readiness head_reason：{head_reason_label}")
        if required_blocking_gap_kinds:
            bits.append("必交付分区缺口：" + " / ".join(required_blocking_gap_kinds))
    elif readiness == READINESS_TRACKED_GAP:
        if not has_bound_slot:
            bits.append("尚未绑定脚本片段（脚本 body 不可读）")
    if not bits:
        return ""
    return "；".join(bits) + "。"


def _required_blocking_gap_kinds(
    delivery_comprehension: Mapping[str, Any],
) -> list[str]:
    lanes = _safe_mapping(delivery_comprehension.get("lanes"))
    required_blocking = _safe_mapping(lanes.get("required_blocking"))
    rows = _safe_list(required_blocking.get("rows"))
    gaps: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("artifact_status_code") or "") == "current_fresh":
            continue
        label = _scrub(row.get("kind_label_zh")) or _scrub(row.get("kind"))
        if label:
            gaps.append(label)
    return gaps


def _build_per_variant_row(
    *,
    variant: Mapping[str, Any],
    delivery_comprehension: Mapping[str, Any],
    publish_readiness: Mapping[str, Any],
    closure: Mapping[str, Any],
    head_reason_label_lookup,
) -> dict[str, Any]:
    variation_id = _scrub(variant.get("variation_id")) or ""
    has_bound_slot = bool(variant.get("has_bound_slot"))
    axis_summary = _scrub(variant.get("axis_summary_zh")) or "—"

    publishable = bool(publish_readiness.get("publishable"))
    head_reason = publish_readiness.get("head_reason")
    head_reason_label = head_reason_label_lookup(head_reason) if head_reason else None

    closure_status = _publish_status_for_variation(closure, variation_id)
    required_lane_present = _has_required_blocking_lane(delivery_comprehension)
    required_gap_kinds = _required_blocking_gap_kinds(delivery_comprehension)

    readiness = _classify_readiness(
        publishable=publishable,
        head_reason=head_reason,
        closure_status=closure_status,
        has_bound_slot=has_bound_slot,
        has_required_lane=required_lane_present,
    )

    closure_status_label = None
    if closure_status:
        closure_status_label = {
            "pending": "待发布",
            "published": "已发布",
            "failed": "发布失败",
            "retracted": "已撤回",
        }.get(closure_status)

    return {
        "variation_id": variation_id,
        "axis_summary_zh": axis_summary,
        "has_bound_slot": has_bound_slot,
        "readiness_kind": readiness,
        "readiness_label_zh": READINESS_LABELS_ZH[readiness],
        "next_input_zh": READINESS_NEXT_INPUT_ZH[readiness],
        "gap_summary_zh": _gap_summary_zh(
            readiness=readiness,
            has_bound_slot=has_bound_slot,
            head_reason_label=head_reason_label,
            required_blocking_gap_kinds=required_gap_kinds,
        ),
        "closure_publish_status": closure_status,
        "closure_publish_status_label_zh": closure_status_label,
        "head_reason": head_reason if not publishable else None,
        "head_reason_label_zh": head_reason_label if not publishable else None,
        "required_artifact_gap_kinds_zh": list(required_gap_kinds),
        "no_final_video_url_note_zh": NO_FAKE_FINAL_VIDEO_NOTE_ZH,
    }


def derive_matrix_script_publish_backfill_readiness(
    readable_variants: Mapping[str, Any] | None,
    delivery_comprehension: Mapping[str, Any] | None,
    publish_readiness: Mapping[str, Any] | None,
    closure: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the RC-R7 + RC-R8 publish/backfill readiness explanation.

    Returns ``{}`` when the inputs are not Matrix-Script-shaped (i.e.
    when ``readable_variants`` is empty or the closure surface is not
    matrix_script). Hot Follow / Digital Anchor / baseline publish hubs
    never receive this bundle.

    Output shape:

    .. code-block:: python

        {
            "is_matrix_script": True,
            "panel_title_zh": "发布 / 回填就绪解释",
            "panel_subtitle_zh": "...",
            "readiness_legend_zh": ["...", "...", "..."],
            "rows": [
                {"variation_id": ..., "readiness_kind": ..., ...},
                ...
            ],
            "row_count": int,
            "publishable_now_count": int,
            "gated_count": int,
            "already_published_count": int,
            "already_failed_count": int,
            "tracked_gap_count": int,
            "no_final_video_url_note_zh": "...",
        }
    """
    rv = _safe_mapping(readable_variants)
    if not rv.get("is_matrix_script"):
        return {}
    closure_view = _safe_mapping(closure)
    if closure_view and not _is_matrix_script_closure(closure_view):
        return {}

    dc = _safe_mapping(delivery_comprehension)
    pr = _safe_mapping(publish_readiness)

    def _head_reason_label_lookup(value: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            from .qc_diagnostics_view import HEAD_REASON_LABELS_ZH

            label = HEAD_REASON_LABELS_ZH.get(str(value))
            return label or str(value)
        except Exception:
            return str(value) if value else None

    variants = _safe_list(rv.get("variant_candidates"))
    rows = [
        _build_per_variant_row(
            variant=v if isinstance(v, Mapping) else {},
            delivery_comprehension=dc,
            publish_readiness=pr,
            closure=closure_view,
            head_reason_label_lookup=_head_reason_label_lookup,
        )
        for v in variants
        if isinstance(v, Mapping)
    ]

    publishable_now = sum(
        1 for r in rows if r["readiness_kind"] == READINESS_PUBLISHABLE_NOW
    )
    gated = sum(1 for r in rows if r["readiness_kind"] == READINESS_GATED)
    already_published = sum(
        1 for r in rows if r["readiness_kind"] == READINESS_ALREADY_PUBLISHED
    )
    already_failed = sum(
        1 for r in rows if r["readiness_kind"] == READINESS_ALREADY_FAILED
    )
    tracked_gap = sum(1 for r in rows if r["readiness_kind"] == READINESS_TRACKED_GAP)

    return {
        "is_matrix_script": True,
        "panel_title_zh": "发布 / 回填就绪解释",
        "panel_subtitle_zh": (
            "对每个 variation 给出发布/回填的可发性分级（可发 / 阻塞 / 已发布 / 失败 / "
            "跟踪缺口）；只读视图，单一 publish_readiness producer 决定可发性，"
            "不展示 final_video 媒体链接，已发布行的 publish_url 也不在此面板渲染。"
        ),
        "readiness_legend_zh": [
            READINESS_LABELS_ZH[READINESS_PUBLISHABLE_NOW],
            READINESS_LABELS_ZH[READINESS_GATED],
            READINESS_LABELS_ZH[READINESS_ALREADY_PUBLISHED],
            READINESS_LABELS_ZH[READINESS_ALREADY_FAILED],
            READINESS_LABELS_ZH[READINESS_TRACKED_GAP],
        ],
        "rows": rows,
        "row_count": len(rows),
        "publishable_now_count": publishable_now,
        "gated_count": gated,
        "already_published_count": already_published,
        "already_failed_count": already_failed,
        "tracked_gap_count": tracked_gap,
        "no_final_video_url_note_zh": NO_FAKE_FINAL_VIDEO_NOTE_ZH,
    }


__all__ = [
    "FORBIDDEN_TOKEN_FRAGMENTS",
    "FORBIDDEN_URL_FRAGMENTS",
    "NO_FAKE_FINAL_VIDEO_NOTE_ZH",
    "READINESS_ALREADY_FAILED",
    "READINESS_ALREADY_PUBLISHED",
    "READINESS_GATED",
    "READINESS_LABELS_ZH",
    "READINESS_NEXT_INPUT_ZH",
    "READINESS_PUBLISHABLE_NOW",
    "READINESS_TRACKED_GAP",
    "derive_matrix_script_publish_backfill_readiness",
]
