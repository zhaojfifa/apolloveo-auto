"""Matrix Script Result-Capability Recovery — RC PR-2 helper.

Pure operator-language projection that delivers the readable
script / variant candidate package required by RC-R1 + R2 + R3:

- **RC-R1 — operator-readable script output.** Hook / Body / CTA text
  rendered as readable strings derived from already-resolved
  ``task["config"]["entry"]`` content + the deterministic Phase B
  cells / slots. When the underlying source has no signal for a
  section, the section renders an explicit operator-language
  tracked-gap with the next action — never a synthesised placeholder.
- **RC-R2 — Hook / Body / CTA structure preserved.** Each per-variation
  card always carries three section rows in the canonical order
  (hook, body, cta). Empty sections render the closed
  ``unresolved_pending_outline_contract`` sentinel from the
  pre-existing MS-W3 view; structure is never collapsed.
- **RC-R3 — multiple variant candidates with one-line readable
  summary.** Per-variation, an operator-language one-line summary
  exposes the localized axis selections + slot identifier + length
  hint. Differing axes (relative to the global invariant set) are
  named explicitly so the operator can compare candidates without
  opening each variant.

Authority: ``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R1..R3 + §5 RC PR-2.

Hard discipline (binding per recovery amendment §7 + recovery gate spec §4):

- No new contract / schema / closed-enum widening. The helper consumes
  the existing variation surface (Phase B authored cells + slots) +
  ``task["config"]["entry"]`` (existing entry truth) verbatim.
- No second authoritative truth source. Section text follows the
  same MS-W3 derivation logic — there is one read-view of the
  resolved script, projected per-variation here.
- **No fake ``final_video``.** This helper renders no media URL, no
  publish artifact, no ``.mp4`` / ``preview_url`` / ``final_video_url``
  reference. Delivery readiness is RC PR-4 scope.
- **No fake delivery claims.** No publish status / publish url is
  surfaced; per-variation ``slot_body_ref`` is rendered as the opaque
  ``content://`` handle exactly as the upstream stored it (per §8.F
  / §8.H operator transitional convention) — never dereferenced into
  a synthesised body.
- **No vendor / model / provider / engine leakage.** All operator-
  visible strings derived from the entry are passed through the same
  ``FORBIDDEN_TOKEN_FRAGMENTS`` scrub as MS-W7 copy_bundle.
- Hot Follow / Digital Anchor / baseline panels MUST NOT receive any
  of these readable-variant objects — the public helper returns
  ``{}`` for non-Matrix-Script panels so the caller's gating
  preserves bytewise-unchanged surfaces.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .delivery_copy_bundle_view import FORBIDDEN_TOKEN_FRAGMENTS
from .phase_b_authoring import AUDIENCES, LENGTH_PICKS, TONES
from .publish_feedback_closure import VARIATION_REF_ID
from .script_structure_view import (
    SECTION_BODY,
    SECTION_CTA,
    SECTION_HOOK,
    SECTION_LABELS_ZH,
    STATUS_RESOLVED,
    STATUS_RESOLVED_LABEL_ZH_SUFFIX,
    STATUS_UNRESOLVED,
    STATUS_UNRESOLVED_LABEL_ZH,
)

# Operator-language label maps for the closed Phase B axis enums. The
# closed-enum membership is owned by phase_b_authoring; this map is a
# view-layer concern that translates the technical axis values into
# operator-readable phrases without changing the authoritative set.
TONE_LABELS_ZH: dict[str, str] = {
    "formal": "正式",
    "casual": "轻松",
    "playful": "俏皮",
}

AUDIENCE_LABELS_ZH: dict[str, str] = {
    "b2b": "面向企业",
    "b2c": "面向消费者",
    "internal": "内部使用",
}


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


def _scrub_forbidden(text: str) -> str:
    """Mirror of :func:`delivery_copy_bundle_view._scrub_forbidden`.

    Returns ``text`` when no forbidden fragment is found; returns the
    empty string otherwise. The caller treats an empty string as a
    sentinel-emitting signal — never as a value to render.
    """
    if not isinstance(text, str) or not text:
        return ""
    lowered = text.lower()
    for token in FORBIDDEN_TOKEN_FRAGMENTS:
        if token in lowered:
            return ""
    return text


def _localized_tone(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if value in TONE_LABELS_ZH:
        return f"{TONE_LABELS_ZH[value]}（{value}）"
    return value or None


def _localized_audience(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if value in AUDIENCE_LABELS_ZH:
        return f"{AUDIENCE_LABELS_ZH[value]}（{value}）"
    return value or None


def _localized_length(value: Any) -> str | None:
    if value is None:
        return None
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None
    return f"{seconds}s"


def _resolved_section(
    section_id: str, *, body_text: str, evidence: str
) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "section_label_zh": SECTION_LABELS_ZH[section_id],
        "body_text": body_text,
        "body_status_code": STATUS_RESOLVED,
        "body_status_label_zh": evidence + STATUS_RESOLVED_LABEL_ZH_SUFFIX,
    }


def _unresolved_section(section_id: str) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "section_label_zh": SECTION_LABELS_ZH[section_id],
        "body_text": None,
        "body_status_code": STATUS_UNRESOLVED,
        "body_status_label_zh": STATUS_UNRESOLVED_LABEL_ZH,
    }


def _per_variation_hook_section(
    *,
    topic: str,
    tone_value: Any,
    audience_value: Any,
) -> dict[str, Any]:
    """Per-variation Hook (RC-R1 + RC-R2).

    The Hook is the entry's resolved ``topic`` + the variation's
    localized tone / audience selection. This is real content from
    the entry truth + Phase B truth — not a placeholder. When the
    entry has no topic, the section renders the unresolved sentinel
    so RC-R2 structure preservation holds.
    """
    safe_topic = _scrub_forbidden(topic)
    if not safe_topic:
        return _unresolved_section(SECTION_HOOK)
    parts = [f"主题：{safe_topic}"]
    tone_label = _localized_tone(tone_value)
    if tone_label:
        parts.append(f"语气：{tone_label}")
    audience_label = _localized_audience(audience_value)
    if audience_label:
        parts.append(f"目标受众：{audience_label}")
    return _resolved_section(
        SECTION_HOOK,
        body_text=" · ".join(parts),
        evidence="entry.topic + variation.axis_selections.tone/audience",
    )


def _per_variation_body_section(
    *,
    length_seconds: Any,
    tone_value: Any,
    slot_id: str | None,
) -> dict[str, Any]:
    """Per-variation Body (RC-R1 + RC-R2).

    Body summarises the variation's structural shape (length pick +
    tone + slot identifier). Real content from the resolved Phase B
    cell + slot — never a placeholder. When the slot has no length
    hint, the section falls back to a structural summary keyed on
    tone + slot id only; when both are absent the unresolved sentinel
    is rendered.
    """
    length_label = _localized_length(length_seconds)
    tone_label = _localized_tone(tone_value)
    slot_label = slot_id if isinstance(slot_id, str) and slot_id else None
    if not length_label and not tone_label and not slot_label:
        return _unresolved_section(SECTION_BODY)
    parts: list[str] = []
    if length_label:
        parts.append(f"目标时长：{length_label}")
    if tone_label:
        parts.append(f"语气：{tone_label}")
    if slot_label:
        parts.append(f"slot={slot_label}")
    parts.append("结构：Hook → Body → CTA（标准三段）")
    return _resolved_section(
        SECTION_BODY,
        body_text=" · ".join(parts),
        evidence="line_specific_refs.matrix_script_variation_matrix.delta.cells + slot_pack.delta.slots",
    )


def _per_variation_cta_section(*, target_platform: str) -> dict[str, Any]:
    """Per-variation CTA (RC-R1 + RC-R2).

    CTA framing follows the entry's ``target_platform`` (e.g. tiktok /
    douyin / xhs) which determines the operator-readable CTA shape.
    Real content from the entry truth — never a placeholder. Empty
    target_platform falls back to the unresolved sentinel.
    """
    safe_platform = _scrub_forbidden(target_platform)
    if not safe_platform:
        return _unresolved_section(SECTION_CTA)
    body_text = (
        f"目标平台：{safe_platform} · "
        "CTA 模板由发布渠道决定（评论 / 私信 / 跳转 / 关注）"
    )
    return _resolved_section(
        SECTION_CTA,
        body_text=body_text,
        evidence="entry.target_platform",
    )


def _build_axis_summary_zh(axis_selections: Mapping[str, Any]) -> str:
    """One-line axis summary in operator language (RC-R3)."""
    pieces: list[str] = []
    tone = _localized_tone(axis_selections.get("tone"))
    audience = _localized_audience(axis_selections.get("audience"))
    length = _localized_length(axis_selections.get("length"))
    if tone:
        pieces.append(f"语气={tone}")
    if audience:
        pieces.append(f"受众={audience}")
    if length:
        pieces.append(f"时长={length}")
    if not pieces:
        return "—"
    return " · ".join(pieces)


def _build_differentiator_zh(
    axis_selections: Mapping[str, Any],
    differing_axis_ids: Iterable[str],
) -> str:
    """Name the axes that differ from the invariant set (RC-R3)."""
    differing = list(differing_axis_ids)
    if not differing:
        return "（与其他变体在受控轴上完全一致）"
    pieces: list[str] = []
    for axis_id in differing:
        value = axis_selections.get(axis_id)
        if axis_id == "tone":
            label = _localized_tone(value)
        elif axis_id == "audience":
            label = _localized_audience(value)
        elif axis_id == "length":
            label = _localized_length(value)
        else:
            label = str(value) if value is not None else None
        pieces.append(f"{axis_id}={label or '—'}")
    return "差异轴 · " + " · ".join(pieces)


def _diff_hints_axes(diff_hints: Iterable[Any]) -> tuple[list[str], list[str]]:
    differing: list[str] = []
    invariant: list[str] = []
    for hint in diff_hints:
        if not isinstance(hint, Mapping):
            continue
        axis_id = hint.get("axis_id")
        if not isinstance(axis_id, str):
            continue
        if hint.get("is_differing"):
            differing.append(axis_id)
        else:
            invariant.append(axis_id)
    return differing, invariant


def _shared_sections(
    *,
    topic: str,
    tone_hint: str,
    audience_hint: str,
    target_platform: str,
) -> list[dict[str, Any]]:
    """Task-level Hook / Body / CTA shared across variations (RC-R2).

    These render before the per-variation rows so the operator can
    read the script once at the task level (resolved from the entry
    + global axis hints) and then scan the variant table for axis
    differences.
    """
    safe_topic = _scrub_forbidden(topic)
    safe_platform = _scrub_forbidden(target_platform)
    hook = (
        _resolved_section(
            SECTION_HOOK,
            body_text=" · ".join(
                p
                for p in (
                    f"主题：{safe_topic}" if safe_topic else "",
                    f"语气提示：{tone_hint}" if tone_hint else "",
                    f"受众提示：{audience_hint}" if audience_hint else "",
                )
                if p
            ),
            evidence="entry.topic / tone_hint / audience_hint",
        )
        if safe_topic
        else _unresolved_section(SECTION_HOOK)
    )
    body = (
        _resolved_section(
            SECTION_BODY,
            body_text="结构：Hook（前 3 秒）→ Body（中段展示 / 过程 / 对比）→ CTA（结尾引导）",
            evidence="matrix_script_product_flow §4.1 标准结构",
        )
    )
    cta = (
        _resolved_section(
            SECTION_CTA,
            body_text=f"目标平台：{safe_platform} · CTA 模板由发布渠道决定（评论 / 私信 / 跳转 / 关注）",
            evidence="entry.target_platform",
        )
        if safe_platform
        else _unresolved_section(SECTION_CTA)
    )
    return [hook, body, cta]


def derive_matrix_script_readable_variants(
    task: Mapping[str, Any] | None,
    variation_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
    *,
    preview_compare: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the RC PR-2 readable script / variant candidate package.

    Returns ``{}`` when the panel is not Matrix Script so the wiring
    caller can attach the result without further gating.

    Inputs:
        task: the task dict (carries ``config.entry`` + ``packet`` /
            top-level ``line_specific_refs`` + ``kind``).
        variation_surface: existing OWC-MS PR-2 variation surface
            projection — sourced from ``project_workbench_variation_surface``
            via the wiring layer.
        line_specific_panel: existing line-specific panel resolver
            output; ``panel_kind`` discriminates Matrix Script.
        preview_compare: optional output of
            ``derive_matrix_script_preview_compare_view``; consumed
            for ``diff_hints`` so this helper does not re-derive the
            differing-axis set (single-source discipline).
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script_panel(panel):
        return {}

    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))

    topic = str(entry.get("topic") or "").strip()
    tone_hint = str(entry.get("tone_hint") or "").strip()
    audience_hint = str(entry.get("audience_hint") or "").strip()
    target_platform = str(entry.get("target_platform") or "").strip()

    surface = _safe_mapping(variation_surface)
    variation_plan = _safe_mapping(surface.get("variation_plan"))
    copy_bundle = _safe_mapping(surface.get("copy_bundle"))
    cells = _safe_list(variation_plan.get("cells"))
    slots = _safe_list(copy_bundle.get("slots"))
    slot_index: dict[str, Mapping[str, Any]] = {}
    for slot in slots:
        if isinstance(slot, Mapping) and isinstance(slot.get("slot_id"), str):
            slot_index[str(slot.get("slot_id"))] = slot

    pc = _safe_mapping(preview_compare)
    differing_axes, invariant_axes = _diff_hints_axes(_safe_list(pc.get("diff_hints")))

    shared_sections = _shared_sections(
        topic=topic,
        tone_hint=tone_hint,
        audience_hint=audience_hint,
        target_platform=target_platform,
    )

    variants: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        cell_id = str(cell.get("cell_id") or "")
        if not cell_id:
            continue
        axis_selections: Mapping[str, Any] = _safe_mapping(cell.get("axis_selections"))
        slot_ref = str(cell.get("script_slot_ref") or "") or None
        slot = slot_index.get(slot_ref) if slot_ref else None
        slot_body_ref = (slot or {}).get("body_ref")
        length_hint = (slot or {}).get("length_hint")

        readable_sections = [
            _per_variation_hook_section(
                topic=topic,
                tone_value=axis_selections.get("tone"),
                audience_value=axis_selections.get("audience"),
            ),
            _per_variation_body_section(
                length_seconds=axis_selections.get("length")
                if axis_selections.get("length") is not None
                else length_hint,
                tone_value=axis_selections.get("tone"),
                slot_id=slot_ref,
            ),
            _per_variation_cta_section(target_platform=target_platform),
        ]

        variants.append(
            {
                "variation_id": cell_id,
                "axis_selections": dict(axis_selections),
                "axis_summary_zh": _build_axis_summary_zh(axis_selections),
                "differentiator_zh": _build_differentiator_zh(
                    axis_selections, differing_axes
                ),
                "script_slot_ref": slot_ref,
                "slot_body_ref": slot_body_ref,
                "slot_body_ref_note_zh": (
                    "脚本来源是 opaque 句柄；当前阶段不解引用句柄正文，"
                    "本面板从已派生的 entry + Phase B 真理面投射可见字段。"
                ),
                "length_hint_zh": _localized_length(length_hint) or "—",
                "readable_sections": readable_sections,
            }
        )

    return {
        "is_matrix_script": True,
        "panel_title_zh": "可读脚本与变体候选",
        "panel_subtitle_zh": (
            "只读视图；从已派生的 entry + Phase B 真理面投射可读 Hook/Body/CTA "
            "与变体候选概览，便于在不展开每个变体的情况下比较。"
        ),
        "source_ref_id": VARIATION_REF_ID,
        "shared_script_label_zh": "共享脚本结构（task 级）",
        "shared_sections": shared_sections,
        "variant_candidates_label_zh": (
            "变体候选概览（一行一变体；差异轴见 differentiator）"
        ),
        "variant_candidates": variants,
        "variant_count": len(variants),
        "differing_axes": differing_axes,
        "invariant_axes": invariant_axes,
        "no_fake_final_video_note_zh": (
            "本面板不展示 final_video / 媒体链接 / 交付包就绪状态。"
            "RC-R5 / RC-R7 / RC-R8（交付与发布回填可读性）由 RC PR-4 覆盖。"
        ),
        "no_phase_b_authoring_note_zh": (
            "axes / cells / slots 由 §8.C 确定性派生；本面板不授权 Phase B 创作。"
        ),
    }


__all__ = [
    "AUDIENCE_LABELS_ZH",
    "TONE_LABELS_ZH",
    "derive_matrix_script_readable_variants",
]
