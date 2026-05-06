"""Matrix Script Result-Capability Recovery — RC PR-4 helper (RC-R5 + RC-R8).

Pure presentation-layer projection that surfaces, per variation, an
operator-language **delivery-ready copy/script package** classification.
The package is never a media artifact: it is the readable bundle of
fields that already exist on Matrix Script truth — script body
availability + copy_bundle subfield resolution + per-deliverable lane
status — re-presented so the operator can take a single readable
package to a downstream channel without consulting the engineering log.

Authority: ``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R5 + §3 RC-R8 + §5 RC PR-4.

Hard discipline (binding per recovery amendment §7 + recovery gate
spec §4):

- **No second authoritative truth source.** Inputs are the existing
  RC PR-2 ``readable_variants`` payload, the OWC-MS PR-3
  ``delivery_comprehension`` lanes, the OWC-MS PR-3 Delivery Center
  ``copy_bundle`` projection, and the unified ``publish_readiness``
  producer output. The helper never re-derives publishability or
  re-classifies a deliverable lane.
- **No fake ``final_video`` (RC-R8).** The helper renders no media URL,
  no ``http(s)://`` substring, no ``.mp4`` / ``.mov`` substring, no
  ``final_video_url`` / ``preview_url`` / ``publish_url`` substring.
  When the underlying delivery comprehension reports an unresolved
  artifact, the package row is rendered as an explicit tracked-gap
  with an operator-language next action — never as a synthesised
  deliverable.
- **No closed-enum widening.** The helper only consumes values from the
  existing closed enums (``artifact_status_code``,
  ``RECOMMENDED_BUCKET_*``, copy_bundle ``status_code``).
- **No raw internal handles.** No ``script_slot_ref`` /
  ``slot_body_ref`` / ``content://`` substring leakage.
- Hot Follow / Digital Anchor / baseline panels MUST NOT receive any
  of these objects — the public helper returns ``{}`` for non-MS
  panels so the caller's gating preserves bytewise-unchanged surfaces.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

# Closed package-status enum.
PACKAGE_READY = "ready_package"
PACKAGE_PARTIAL = "partial_package"
PACKAGE_BLOCKED = "blocked_package"
PACKAGE_UNAVAILABLE = "unavailable_tracked_gap"

PACKAGE_STATUS_LABELS_ZH = {
    PACKAGE_READY: "成片包就绪",
    PACKAGE_PARTIAL: "成片包部分就绪",
    PACKAGE_BLOCKED: "成片包被阻塞",
    PACKAGE_UNAVAILABLE: "成片包暂不可用 · 跟踪缺口",
}

PACKAGE_HEADLINE_ZH = {
    PACKAGE_READY: "可交付的脚本/文案包已就绪",
    PACKAGE_PARTIAL: "脚本/文案包部分就绪 · 仍有可选/非阻塞缺口",
    PACKAGE_BLOCKED: "脚本/文案包被阻塞 · 解除前置项后再尝试",
    PACKAGE_UNAVAILABLE: "脚本/文案包暂不可用 · 上游真值尚未到达",
}

PACKAGE_NEXT_ACTION_ZH = {
    PACKAGE_READY: (
        "可前往 Delivery Center 取走脚本/文案包；本面板不展示 final_video / "
        "媒体链接，发布动作仍由 Delivery Center + publish_readiness 承担。"
    ),
    PACKAGE_PARTIAL: (
        "可参考已就绪字段先行启动文案准备；剩余字段按下方逐项缺口逐一补齐，"
        "其中标记为「可选 / 不阻塞发布」的缺口不阻塞 publish_readiness 收敛。"
    ),
    PACKAGE_BLOCKED: (
        "解除 publish_readiness 阻塞前置项（见 head_reason）+ 必交付分区中标"
        "记为非当前/未决议的产物后，再回到本面板查看包状态。"
    ),
    PACKAGE_UNAVAILABLE: (
        "等待 Phase B / 脚本投射/ copy 投射上线；本面板会随上游真值补齐重新出现。"
    ),
}

# Forbidden token fragments scrubbed defensively against accidental
# upstream leakage (validator R3 + design-handoff red line 6).
FORBIDDEN_TOKEN_FRAGMENTS = ("vendor", "model_id", "provider", "engine")
FORBIDDEN_URL_FRAGMENTS = (
    "http://",
    "https://",
    ".mp4",
    ".mov",
    "final_video_url",
    "preview_url",
    "publish_url",
    "content://",
)

NO_FAKE_FINAL_VIDEO_NOTE_ZH = (
    "本面板不合成 final_video / 媒体链接 / 任何外部 URL；当存在缺口时仅以 "
    "operator-language 的 tracked-gap 文案告知，不会以占位 URL 顶替。"
)

NO_PUBLISH_CLAIM_NOTE_ZH = (
    "本面板的「就绪」仅指脚本/文案 readable bundle；"
    "publish_readiness 发布门禁仍由 RC PR-1 统一 producer 单一决定。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script_panel(panel: Mapping[str, Any]) -> bool:
    if not isinstance(panel, Mapping):
        return False
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _scrub(value: Any) -> str:
    """Return ``value`` as a string only if it is forbidden-token-clean.

    Defensive: even when an upstream projection accidentally pulls a
    vendor / model identifier or a media URL, this scrub returns the
    empty string so the operator never sees the leak. Used at every
    string echo point in the package projection.
    """
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


def _copy_bundle_resolved_count(copy_bundle_view: Mapping[str, Any]) -> tuple[int, int]:
    subfields = _safe_list(copy_bundle_view.get("subfields"))
    total = 0
    resolved = 0
    for entry in subfields:
        if not isinstance(entry, Mapping):
            continue
        total += 1
        if str(entry.get("status_code") or "") == "resolved_from_existing_projection":
            resolved += 1
    return resolved, total


def _required_blocking_status(delivery_comprehension: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Inspect the OWC-MS PR-3 lanes for required+blocking artifact status.

    Returns ``(all_current, gap_kinds)`` where ``all_current`` is True
    when every required+blocking row reports ``current_fresh`` and
    ``gap_kinds`` is the operator-language list of kind labels whose
    artifact is not current.
    """
    lanes = _safe_mapping(delivery_comprehension.get("lanes"))
    required_blocking = _safe_mapping(lanes.get("required_blocking"))
    rows = _safe_list(required_blocking.get("rows"))
    if not rows:
        return False, []
    gap_kinds: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        status_code = str(row.get("artifact_status_code") or "")
        if status_code != "current_fresh":
            label = _scrub(row.get("kind_label_zh")) or _scrub(row.get("kind"))
            if label:
                gap_kinds.append(label)
    return (len(gap_kinds) == 0), gap_kinds


def _classify_package_status(
    *,
    has_bound_slot: bool,
    publishable: bool,
    head_reason: Optional[str],
    all_required_current: bool,
    required_gap_kinds: list[str],
    copy_resolved: int,
    copy_total: int,
) -> str:
    """Decide the closed package status code.

    Logic:

    - ``unavailable_tracked_gap``: no bound script slot AND no copy
      subfield resolved — the upstream Phase B / copy projections have
      not produced anything for this variant yet.
    - ``blocked_package``: publish_readiness reports not publishable
      (any head_reason) — the package cannot move forward until the
      gate clears, regardless of copy state.
    - ``ready_package``: bound slot present AND all required+blocking
      artifact rows current AND publish_readiness publishable.
    - ``partial_package``: anything else (bound slot present and
      publishable but not all required artifacts current, OR resolved
      copy without a bound slot, etc.). The partial bucket is the
      "some readable content exists but not everything is in place"
      lane that lets the operator move forward incrementally.
    """
    if not has_bound_slot and copy_resolved == 0:
        return PACKAGE_UNAVAILABLE
    if not publishable:
        return PACKAGE_BLOCKED
    if has_bound_slot and all_required_current and copy_resolved == copy_total and copy_total > 0:
        return PACKAGE_READY
    return PACKAGE_PARTIAL


def _gap_explanation_zh(
    *,
    status: str,
    has_bound_slot: bool,
    head_reason_label: Optional[str],
    required_gap_kinds: list[str],
    copy_resolved: int,
    copy_total: int,
) -> str:
    bits: list[str] = []
    if not has_bound_slot:
        bits.append("脚本片段未绑定（脚本 body 不可读）")
    if copy_total and copy_resolved < copy_total:
        bits.append(f"copy_bundle 字段就绪 {copy_resolved}/{copy_total}")
    if required_gap_kinds:
        bits.append("必交付分区缺口：" + " / ".join(required_gap_kinds))
    if status == PACKAGE_BLOCKED and head_reason_label:
        bits.append(f"publish_readiness 阻塞：{head_reason_label}")
    if not bits:
        return ""
    return "；".join(bits) + "。"


def _build_per_variant_row(
    *,
    variant: Mapping[str, Any],
    delivery_comprehension: Mapping[str, Any],
    copy_bundle_view: Mapping[str, Any],
    publish_readiness: Mapping[str, Any],
    head_reason_label_lookup,
) -> dict[str, Any]:
    variation_id = _scrub(variant.get("variation_id"))
    if not variation_id:
        variation_id = ""
    has_bound_slot = bool(variant.get("has_bound_slot"))
    axis_summary = _scrub(variant.get("axis_summary_zh")) or "—"
    differentiator = _scrub(variant.get("differentiator_zh")) or ""
    length_hint = _scrub(variant.get("length_hint_zh")) or "—"

    publishable = bool(publish_readiness.get("publishable"))
    head_reason = publish_readiness.get("head_reason")
    head_reason_label = head_reason_label_lookup(head_reason) if head_reason else None

    all_required_current, required_gap_kinds = _required_blocking_status(
        delivery_comprehension
    )
    copy_resolved, copy_total = _copy_bundle_resolved_count(copy_bundle_view)

    status = _classify_package_status(
        has_bound_slot=has_bound_slot,
        publishable=publishable,
        head_reason=head_reason,
        all_required_current=all_required_current,
        required_gap_kinds=required_gap_kinds,
        copy_resolved=copy_resolved,
        copy_total=copy_total,
    )

    return {
        "variation_id": variation_id,
        "axis_summary_zh": axis_summary,
        "differentiator_zh": differentiator,
        "length_hint_zh": length_hint,
        "has_bound_slot": has_bound_slot,
        "package_status_kind": status,
        "package_status_label_zh": PACKAGE_STATUS_LABELS_ZH[status],
        "headline_zh": PACKAGE_HEADLINE_ZH[status],
        "next_action_zh": PACKAGE_NEXT_ACTION_ZH[status],
        "gap_explanation_zh": _gap_explanation_zh(
            status=status,
            has_bound_slot=has_bound_slot,
            head_reason_label=head_reason_label,
            required_gap_kinds=required_gap_kinds,
            copy_resolved=copy_resolved,
            copy_total=copy_total,
        ),
        "copy_bundle_resolved_count": copy_resolved,
        "copy_bundle_total_count": copy_total,
        "required_artifact_gap_kinds_zh": list(required_gap_kinds),
        "head_reason": head_reason if not publishable else None,
        "head_reason_label_zh": head_reason_label if not publishable else None,
        "no_final_video_url_note_zh": NO_FAKE_FINAL_VIDEO_NOTE_ZH,
        "no_publish_claim_note_zh": NO_PUBLISH_CLAIM_NOTE_ZH,
    }


def derive_matrix_script_delivery_ready_package(
    readable_variants: Mapping[str, Any] | None,
    delivery_comprehension: Mapping[str, Any] | None,
    copy_bundle_view: Mapping[str, Any] | None,
    publish_readiness: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the RC-R5 + RC-R8 delivery-ready package per variation.

    Returns ``{}`` for non-Matrix-Script panels so callers preserve
    Hot Follow / Digital Anchor / baseline bytewise unchanged.

    Output shape:

    .. code-block:: python

        {
            "is_matrix_script": True,
            "panel_title_zh": "成片包（脚本/文案）就绪状态",
            "panel_subtitle_zh": "...",
            "package_status_legend_zh": ["成片包就绪", "成片包部分就绪", "成片包被阻塞", "成片包暂不可用 · 跟踪缺口"],
            "rows": [
                {"variation_id": ..., "package_status_kind": ..., ...},
                ...
            ],
            "row_count": int,
            "ready_count": int,
            "partial_count": int,
            "blocked_count": int,
            "unavailable_count": int,
            "no_final_video_url_note_zh": "...",
            "no_publish_claim_note_zh": "...",
        }
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script_panel(panel):
        return {}

    rv = _safe_mapping(readable_variants)
    dc = _safe_mapping(delivery_comprehension)
    cb = _safe_mapping(copy_bundle_view)
    pr = _safe_mapping(publish_readiness)

    # Defer the head-reason label lookup so the helper does not import
    # qc_diagnostics at module import time (keeps the test's import-light
    # surface narrow). The lookup is opaque to non-MS callers.
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
            copy_bundle_view=cb,
            publish_readiness=pr,
            head_reason_label_lookup=_head_reason_label_lookup,
        )
        for v in variants
        if isinstance(v, Mapping)
    ]

    ready = sum(1 for row in rows if row["package_status_kind"] == PACKAGE_READY)
    partial = sum(1 for row in rows if row["package_status_kind"] == PACKAGE_PARTIAL)
    blocked = sum(1 for row in rows if row["package_status_kind"] == PACKAGE_BLOCKED)
    unavailable = sum(
        1 for row in rows if row["package_status_kind"] == PACKAGE_UNAVAILABLE
    )

    return {
        "is_matrix_script": True,
        "panel_title_zh": "成片包（脚本/文案）就绪状态",
        "panel_subtitle_zh": (
            "对每个 variation 给出脚本/文案包的可交付分级（就绪 / 部分就绪 / 阻塞 / "
            "跟踪缺口）；只读视图，不发明事实，不展示 final_video 媒体链接，发布门禁仍由 "
            "RC PR-1 统一 publish_readiness 决定。"
        ),
        "package_status_legend_zh": [
            PACKAGE_STATUS_LABELS_ZH[PACKAGE_READY],
            PACKAGE_STATUS_LABELS_ZH[PACKAGE_PARTIAL],
            PACKAGE_STATUS_LABELS_ZH[PACKAGE_BLOCKED],
            PACKAGE_STATUS_LABELS_ZH[PACKAGE_UNAVAILABLE],
        ],
        "rows": rows,
        "row_count": len(rows),
        "ready_count": ready,
        "partial_count": partial,
        "blocked_count": blocked,
        "unavailable_count": unavailable,
        "no_final_video_url_note_zh": NO_FAKE_FINAL_VIDEO_NOTE_ZH,
        "no_publish_claim_note_zh": NO_PUBLISH_CLAIM_NOTE_ZH,
    }


__all__ = [
    "FORBIDDEN_TOKEN_FRAGMENTS",
    "FORBIDDEN_URL_FRAGMENTS",
    "NO_FAKE_FINAL_VIDEO_NOTE_ZH",
    "NO_PUBLISH_CLAIM_NOTE_ZH",
    "PACKAGE_BLOCKED",
    "PACKAGE_HEADLINE_ZH",
    "PACKAGE_NEXT_ACTION_ZH",
    "PACKAGE_PARTIAL",
    "PACKAGE_READY",
    "PACKAGE_STATUS_LABELS_ZH",
    "PACKAGE_UNAVAILABLE",
    "derive_matrix_script_delivery_ready_package",
]
