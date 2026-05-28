"""Matrix Script Result-Capability Recovery — RC PR-3 helper (RC-R4).

Pure operator-language projection that promotes the existing MS-W4
``recommended`` marker from a passive badge on every variation row
into a single **actionable decision lane**:

- **RC-R4 — recommended-version + next-action lane.** The operator
  sees, per task, exactly one of three operator-language statements:
  - "推荐 · 可发布候选 → 前往 Delivery Center 发布" (a single
    recommended variant id is named).
  - "暂不推荐 · 发布门禁阻塞 → 解除前置项后再尝试" (the head_reason
    label tells the operator why; no variant id is "the recommended
    one" because none qualifies).
  - "—（待校对完成 / publish_readiness 上线后收敛）" (the producer
    has not yet decided; operator waits or completes review first).

Authority: ``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R4 + §5 RC PR-3.

Hard discipline (binding per recovery amendment §7 + recovery gate
spec §4):

- **No second authoritative truth source.** This helper consumes the
  pre-existing MS-W4 ``preview_compare.variations[*].recommended_*``
  fields verbatim and the RC PR-2 ``readable_variants`` axis-summary
  / differentiator strings verbatim. It does NOT call
  ``compute_publish_readiness`` and does NOT re-derive the
  recommended marker.
- **No fake publish-readiness or delivery claims.** When no variant
  is in the ``publishable_candidate`` bucket, the lane explicitly
  reports the blocked / undetermined state — never elevates a
  blocked variant into a "publishable" claim. The lane also surfaces
  no ``final_video`` URL, no media reference, no delivery-pack
  artifact identifier (delivery readiness is RC PR-4 scope).
- **No closed-enum widening.** The lane reuses the existing
  ``RECOMMENDED_BUCKET_*`` closed enum from
  :mod:`preview_compare_view`. No new contract / schema mutation.
- **No raw internal handles.** The lane never surfaces
  ``script_slot_ref``, ``slot_body_ref``, or any
  ``content://`` handle string (mirrors the RC PR-2
  conditional-pass corrections).
- Hot Follow / Digital Anchor / baseline panels MUST NOT receive any
  of these objects — the public helper returns ``{}`` for non-MS
  panels so the caller's gating preserves bytewise-unchanged
  surfaces.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .preview_compare_view import (
    RECOMMENDED_BUCKET_BLOCKED,
    RECOMMENDED_BUCKET_PUBLISHABLE,
    RECOMMENDED_BUCKET_UNDETERMINED,
)
from .qc_diagnostics_view import HEAD_REASON_LABELS_ZH

# Operator-language next-action sentence per recommended-bucket. The
# bucket set is closed by the existing MS-W4 enum; the next-action map
# is a presentation-layer view-table (not a contract enum).
NEXT_ACTION_PUBLISHABLE_ZH = (
    "前往 Delivery Center 选择渠道与账号完成发布；发布完成后回到本面板复盘指标。"
)
NEXT_ACTION_BLOCKED_ZH = (
    "先解除发布门禁的阻塞项再继续；阻塞原因显示在「主视频结果」面板中。"
)
NEXT_ACTION_UNDETERMINED_ZH = (
    "等待第一次成片产出并完成校对；发布条件就绪后系统会自动推进推荐。"
)

# Operator-language headline per recommended-bucket. Mirrors the gate
# spec §3 RC-R4 wording: a single line that the operator can read at
# a glance to know whether to act, wait, or unblock.
HEADLINE_PUBLISHABLE_ZH = "推荐 · 可发布候选已锁定"
HEADLINE_BLOCKED_ZH = "暂不推荐 · 发布门禁阻塞"
HEADLINE_UNDETERMINED_ZH = "暂无推荐 · 待 publish_readiness 收敛"


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


def _head_reason_label(head_reason: Any) -> str | None:
    if head_reason is None:
        return None
    label = HEAD_REASON_LABELS_ZH.get(str(head_reason))
    return label or str(head_reason)


def _readable_summary_for_variant(
    variant_id: str,
    readable_variants: Mapping[str, Any],
) -> dict[str, Any]:
    """Look up the operator-language axis summary + differentiator for
    a variant id from the RC PR-2 ``readable_variants`` payload.

    Returns ``{}`` when the variant is not present (defensive — should
    never happen in practice because both helpers consume the same
    variation_surface). The lookup never exposes raw internal handles.
    """
    candidates = _safe_list(readable_variants.get("variant_candidates"))
    for entry in candidates:
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("variation_id") or "") == variant_id:
            return {
                "axis_summary_zh": entry.get("axis_summary_zh") or "—",
                "differentiator_zh": entry.get("differentiator_zh") or "",
                "length_hint_zh": entry.get("length_hint_zh") or "—",
                "has_bound_slot": bool(entry.get("has_bound_slot")),
            }
    return {}


def _pick_recommended_variant(variations: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Pick the first ``publishable_candidate`` variant.

    The selection is intentionally simple: take the first variation
    row whose pre-decided ``recommended_bucket`` is
    ``publishable_candidate``. This preserves the existing MS-W4
    ordering as the "first decided" semantic; it does NOT introduce
    a new ranking or scoring authority. Returns ``None`` when no
    variant is in the publishable bucket.
    """
    for entry in variations:
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("recommended_bucket") or "") == RECOMMENDED_BUCKET_PUBLISHABLE:
            return entry
    return None


def _earliest_blocked_or_first(variations: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Return the first variation whose ``recommended_bucket`` is
    blocked, falling back to the first variation overall.

    Used to surface a meaningful ``head_reason`` when no variant is
    currently a publishable candidate. The fallback value is operator
    readable by reusing the existing MS-W4 ``recommended_*`` fields.
    """
    for entry in variations:
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("recommended_bucket") or "") == RECOMMENDED_BUCKET_BLOCKED:
            return entry
    for entry in variations:
        if isinstance(entry, Mapping):
            return entry
    return None


def derive_matrix_script_recommended_action(
    preview_compare: Mapping[str, Any] | None,
    readable_variants: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the RC-R4 recommended-version + next-action lane.

    Returns ``{}`` for non-Matrix-Script panels.

    The output dict is operator-language only:

    - ``status_kind``: closed enum mirroring the MS-W4 recommended
      bucket — ``publishable_candidate`` / ``blocked_pending_publish_readiness``
      / ``undetermined_pending_review``.
    - ``headline_zh``: one operator-language line.
    - ``next_action_zh``: a concrete sentence telling the operator
      what to do next.
    - ``recommended_variant`` (only when status is publishable): the
      named variant id + its operator-language axis summary +
      differentiator, sourced from the existing RC PR-2 readable
      variants payload. Never carries raw slot identifiers.
    - ``reason_zh`` (when blocked): operator-language ``head_reason``
      label sourced from the existing closed
      :data:`HEAD_REASON_LABELS_ZH` map.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script_panel(panel):
        return {}

    pc = _safe_mapping(preview_compare)
    rv = _safe_mapping(readable_variants)
    variations = _safe_list(pc.get("variations"))

    candidate = _pick_recommended_variant(variations)
    if candidate is not None:
        variant_id = str(candidate.get("variation_id") or "")
        readable = _readable_summary_for_variant(variant_id, rv)
        head_reason = candidate.get("recommended_head_reason")
        return {
            "is_matrix_script": True,
            "panel_title_zh": "推荐版本与下一步动作",
            "panel_subtitle_zh": (
                "本面板对已决定的推荐结论做单条可执行表述；"
                "推荐结论由统一 publish_readiness 决定，本视图不发明结论也不重算。"
            ),
            "status_kind": RECOMMENDED_BUCKET_PUBLISHABLE,
            "status_label_zh": (
                candidate.get("recommended_label_zh") or HEADLINE_PUBLISHABLE_ZH
            ),
            "headline_zh": HEADLINE_PUBLISHABLE_ZH,
            "next_action_zh": NEXT_ACTION_PUBLISHABLE_ZH,
            "recommended_variant": {
                "variation_id": variant_id,
                "axis_summary_zh": readable.get("axis_summary_zh") or "—",
                "differentiator_zh": readable.get("differentiator_zh") or "",
                "length_hint_zh": readable.get("length_hint_zh") or "—",
                "has_bound_slot": bool(readable.get("has_bound_slot")),
            },
            "reason_zh": (
                candidate.get("recommended_explanation_zh")
                or "publish_readiness=publishable 且未在 closure 中标记为已发布。"
            ),
            "head_reason": head_reason,
            "head_reason_label_zh": _head_reason_label(head_reason),
            "candidate_count": sum(
                1
                for entry in variations
                if isinstance(entry, Mapping)
                and str(entry.get("recommended_bucket") or "")
                == RECOMMENDED_BUCKET_PUBLISHABLE
            ),
            "no_publish_claim_note_zh": (
                "本面板不展示 final_video / 媒体链接 / 交付包就绪状态。"
                "RC-R5 / RC-R7 / RC-R8 由 RC PR-4 覆盖。"
            ),
        }

    fallback = _earliest_blocked_or_first(variations)
    fallback_bucket = (
        str(fallback.get("recommended_bucket") or "")
        if isinstance(fallback, Mapping)
        else ""
    )

    if fallback_bucket == RECOMMENDED_BUCKET_BLOCKED:
        head_reason = fallback.get("recommended_head_reason") if fallback else None
        head_reason_label = _head_reason_label(head_reason)
        return {
            "is_matrix_script": True,
            "panel_title_zh": "推荐版本与下一步动作",
            "panel_subtitle_zh": (
                "本面板对已决定的推荐结论做单条可执行表述；"
                "推荐结论由统一 publish_readiness 决定，本视图不发明结论也不重算。"
            ),
            "status_kind": RECOMMENDED_BUCKET_BLOCKED,
            "status_label_zh": (
                fallback.get("recommended_label_zh") if fallback else None
            )
            or HEADLINE_BLOCKED_ZH,
            "headline_zh": HEADLINE_BLOCKED_ZH,
            "next_action_zh": NEXT_ACTION_BLOCKED_ZH,
            "recommended_variant": None,
            "reason_zh": (
                f"当前发布门禁阻塞 · {head_reason_label or '—'}。"
                "请在「可选变体」区按提示先解除前置项。"
            ),
            "head_reason": head_reason,
            "head_reason_label_zh": head_reason_label,
            "candidate_count": 0,
            "no_publish_claim_note_zh": (
                "本面板不展示 final_video / 媒体链接 / 交付包就绪状态。"
                "RC-R5 / RC-R7 / RC-R8 由 RC PR-4 覆盖。"
            ),
        }

    # Either no variations at all, or all variations are in the
    # `undetermined` bucket. The lane reports "no recommendation yet"
    # and tells the operator what would unblock convergence.
    return {
        "is_matrix_script": True,
        "panel_title_zh": "推荐版本与下一步动作",
        "panel_subtitle_zh": (
            "本面板对已决定的推荐结论做单条可执行表述；"
            "推荐结论由统一 publish_readiness 决定，本视图不发明结论也不重算。"
        ),
        "status_kind": RECOMMENDED_BUCKET_UNDETERMINED,
        "status_label_zh": HEADLINE_UNDETERMINED_ZH,
        "headline_zh": HEADLINE_UNDETERMINED_ZH,
        "next_action_zh": NEXT_ACTION_UNDETERMINED_ZH,
        "recommended_variant": None,
        "reason_zh": (
            "当前没有变体进入 publishable_candidate 桶；"
            "推荐识别在 publish_readiness 下一次收敛时自动出现。"
        ),
        "head_reason": None,
        "head_reason_label_zh": None,
        "candidate_count": 0,
        "no_publish_claim_note_zh": (
            "本面板不展示 final_video / 媒体链接 / 交付包就绪状态。"
            "RC-R5 / RC-R7 / RC-R8 由 RC PR-4 覆盖。"
        ),
    }


__all__ = [
    "HEADLINE_BLOCKED_ZH",
    "HEADLINE_PUBLISHABLE_ZH",
    "HEADLINE_UNDETERMINED_ZH",
    "NEXT_ACTION_BLOCKED_ZH",
    "NEXT_ACTION_PUBLISHABLE_ZH",
    "NEXT_ACTION_UNDETERMINED_ZH",
    "derive_matrix_script_recommended_action",
]
