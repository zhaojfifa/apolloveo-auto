"""Digital Anchor Workbench B — content structure read-view (OWC-DA PR-2 / DA-W4).

Pure presentation-layer projection over the closed Digital Anchor
``task["config"]["entry"]`` payload (built by
:mod:`gateway.app.services.digital_anchor.create_entry`) + the role/
speaker surface projection (read-only). Reads only fields that already
exist on the entry contract; never dereferences ``source_script_ref``
(forbidden by OWC-DA gate spec §4.1 — opaque-ref discipline) and never
authors Phase B truth (forbidden by gate spec §3 DA-W4 + §4.1 — operator
authoring of ``roles[]`` / ``segments[]`` stays out).

Authority:

- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W4 (Workbench B 内容结构面
  read-view: Outline / 段落结构 / 强调点 / 节奏 read-view derived from
  ``source_script_ref``-resolved content + role/speaker surface
  projection; **no operator authoring of ``roles[]`` or ``segments[]``
  enumeration** — Phase B authoring stays forbidden).
- ``docs/product/digital_anchor_product_flow_v1.md`` §6.1B — Outline /
  段落结构 / 强调点 / 节奏控制.

The product flow §6.1B enumerates the structural shape of the read-view.
Today's entry contract carries 主题 (topic) + 脚本来源句柄
(``source_script_ref``) + ``output_intent`` + ``speaker_segment_count_hint``;
fully-authored Outline / Section bodies and 强调点 / 节奏 attributes are
NOT yet authored at the entry layer (the future Outline Contract +
Speaker Plan delta-author would land them). Until then the read-view
exposes the section-skeleton structure with operator-language sentinels
explaining the gating. The panel renders the full structural skeleton so
reviewers walking ENGINEERING_RULES §13 product-flow module presence can
confirm the B 内容结构面 module is operator-visible.

Hard discipline (binding under OWC-DA gate spec §4):

- No Digital Anchor packet truth mutation.
- No ``source_script_ref`` dereference; the value is rendered verbatim
  as an opaque handle.
- No operator-driven ``roles[]`` / ``segments[]`` authoring affordance.
- No new ``panel_kind`` / ``ref_id`` / contract field.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No Hot Follow / Matrix Script surface change; non-digital-anchor
  panels return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "digital_anchor"`` branch.
"""
from __future__ import annotations

from typing import Any, Mapping


# Operator-language section labels per digital_anchor_product_flow §6.1B.
SECTION_OUTLINE = "outline"
SECTION_PARAGRAPH = "paragraphs"
SECTION_EMPHASIS = "emphasis"
SECTION_RHYTHM = "rhythm"

SECTION_LABELS_ZH = {
    SECTION_OUTLINE: "Outline（讲解提纲）",
    SECTION_PARAGRAPH: "段落结构（段落 / 章节）",
    SECTION_EMPHASIS: "强调点（关键论点 / CTA）",
    SECTION_RHYTHM: "节奏（速度 / 停顿 / 起伏）",
}

# Closed status codes for section bodies.
STATUS_RESOLVED = "resolved_from_source_content"
STATUS_RESOLVED_LABEL_ZH_SUFFIX = "（来自 source_script_ref / role-speaker 已派生内容）"

STATUS_UNRESOLVED = "unresolved_pending_outline_contract"
STATUS_UNRESOLVED_LABEL_ZH = "—（此字段在当前真理面尚未提供；待 Outline Contract / Phase B 落地后补齐）"

STATUS_OPAQUE_REF = "opaque_source_script_ref"
STATUS_OPAQUE_REF_LABEL_ZH = (
    "脚本来源是 opaque 句柄；当前阶段不解引用句柄正文，本面板从已派生的 entry / "
    "role-speaker 真理面投射可见字段。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_digital_anchor(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "digital_anchor"


def _resolved(section_id: str, *, body_text: str, evidence: str) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "section_label_zh": SECTION_LABELS_ZH[section_id],
        "body_text": body_text,
        "body_status_code": STATUS_RESOLVED,
        "body_status_label_zh": evidence + STATUS_RESOLVED_LABEL_ZH_SUFFIX,
    }


def _unresolved(section_id: str) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "section_label_zh": SECTION_LABELS_ZH[section_id],
        "body_text": None,
        "body_status_code": STATUS_UNRESOLVED,
        "body_status_label_zh": STATUS_UNRESOLVED_LABEL_ZH,
    }


def _outline_section(
    *,
    topic: str,
    output_intent: str,
    role_count: int,
    segment_count: int,
) -> dict[str, Any]:
    """Derive the Outline section from already-resolved entry + role/speaker truth.

    Outline in digital_anchor_product_flow §6.1B is the speaker-driven
    讲解提纲. The entry contract carries ``topic`` + ``output_intent``
    which describe the high-level intent; the role/speaker surface
    contributes the role / segment counts so the Outline can preview the
    coverage. This is real read-view content from the existing truth
    surfaces, not a placeholder. When ``topic`` is missing the section
    falls back to the per-field unresolved sentinel.
    """
    if not topic:
        return _unresolved(SECTION_OUTLINE)
    parts = [f"主题：{topic}"]
    if output_intent:
        parts.append(f"目标输出：{output_intent}")
    if role_count:
        parts.append(f"绑定角色数：{role_count}")
    if segment_count:
        parts.append(f"段落规划数：{segment_count}")
    body_text = " · ".join(parts)
    return _resolved(
        SECTION_OUTLINE,
        body_text=body_text,
        evidence="entry.topic / output_intent + role_pack.roles + speaker_plan.segments",
    )


def _paragraph_section(
    *,
    segments: list[Mapping[str, Any]],
    speaker_segment_count_hint: int | None,
) -> dict[str, Any]:
    """Derive the 段落结构 section from already-resolved speaker_plan segments.

    Real content (segment count + per-segment script_ref + binds_role_id)
    is rendered as the operator-readable 段落结构 line. When no segments
    are authored yet, fall back to the entry hint
    ``speaker_segment_count_hint`` so the operator sees a planned count.
    """
    if segments:
        binds = sorted(
            {
                str(segment.get("binds_role_id"))
                for segment in segments
                if isinstance(segment, Mapping) and segment.get("binds_role_id")
            }
        )
        body_text = (
            f"已规划 {len(segments)} 段；绑定角色：{', '.join(binds) if binds else '—'}"
        )
        return _resolved(
            SECTION_PARAGRAPH,
            body_text=body_text,
            evidence="line_specific_refs.digital_anchor_speaker_plan.delta.segments",
        )
    if isinstance(speaker_segment_count_hint, int) and speaker_segment_count_hint > 0:
        body_text = f"计划段数：{speaker_segment_count_hint}（来自 entry.speaker_segment_count_hint，待 Phase B 派生）"
        return _resolved(
            SECTION_PARAGRAPH,
            body_text=body_text,
            evidence="entry.speaker_segment_count_hint",
        )
    return _unresolved(SECTION_PARAGRAPH)


def _emphasis_section(
    *,
    output_intent: str,
    operator_notes: str,
    target_languages: list[str],
) -> dict[str, Any]:
    """Derive 强调点 from already-resolved entry signals.

    Real content (output_intent + operator_notes + the target-language
    coverage) is rendered as the operator-readable 强调点 line. When
    nothing is authored yet, fall back to the unresolved sentinel.
    """
    parts: list[str] = []
    if output_intent:
        parts.append(f"output_intent={output_intent}")
    if operator_notes:
        parts.append(f"operator_notes={operator_notes}")
    if target_languages:
        parts.append(f"target_languages={', '.join(target_languages)}")
    if not parts:
        return _unresolved(SECTION_EMPHASIS)
    return _resolved(
        SECTION_EMPHASIS,
        body_text=" · ".join(parts),
        evidence="entry.output_intent / operator_notes / language_scope.target_language",
    )


def _rhythm_section(
    *,
    role_framing_hint: str,
    dub_kind_hint: str,
    lip_sync_kind_hint: str,
) -> dict[str, Any]:
    """Derive 节奏 from already-resolved entry hints.

    Real content (the operator-supplied role_framing / dub / lip_sync
    hints) is rendered as the operator-readable 节奏 line. When nothing
    is provided, fall back to the unresolved sentinel.
    """
    parts: list[str] = []
    if role_framing_hint:
        parts.append(f"role_framing={role_framing_hint}")
    if dub_kind_hint:
        parts.append(f"dub_kind={dub_kind_hint}")
    if lip_sync_kind_hint:
        parts.append(f"lip_sync_kind={lip_sync_kind_hint}")
    if not parts:
        return _unresolved(SECTION_RHYTHM)
    return _resolved(
        SECTION_RHYTHM,
        body_text=" · ".join(parts),
        evidence="entry.role_framing_hint / dub_kind_hint / lip_sync_kind_hint",
    )


def derive_digital_anchor_content_structure_view(
    task: Mapping[str, Any] | None,
    role_speaker_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Workbench B 内容结构面 read-view bundle.

    Returns ``{}`` when the panel is not Digital Anchor, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_digital_anchor(panel):
        return {}

    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))

    topic_value = str(entry.get("topic") or "").strip()
    source_script_ref = str(entry.get("source_script_ref") or "").strip()
    output_intent = str(entry.get("output_intent") or "").strip()
    operator_notes = str(entry.get("operator_notes") or "").strip()
    role_framing_hint = str(entry.get("role_framing_hint") or "").strip()
    dub_kind_hint = str(entry.get("dub_kind_hint") or "").strip()
    lip_sync_kind_hint = str(entry.get("lip_sync_kind_hint") or "").strip()
    speaker_segment_count_hint_raw = entry.get("speaker_segment_count_hint")
    try:
        speaker_segment_count_hint = (
            int(speaker_segment_count_hint_raw)
            if speaker_segment_count_hint_raw is not None
            else None
        )
    except (TypeError, ValueError):
        speaker_segment_count_hint = None

    language_scope = _safe_mapping(entry.get("language_scope"))
    source_language = str(language_scope.get("source_language") or "").strip() or None
    target_language_raw = language_scope.get("target_language")
    if isinstance(target_language_raw, list):
        target_languages = [str(item) for item in target_language_raw if isinstance(item, str)]
    elif isinstance(target_language_raw, str) and target_language_raw:
        target_languages = [target_language_raw]
    else:
        target_languages = []

    surface = _safe_mapping(role_speaker_surface)
    role_surface = _safe_mapping(surface.get("role_surface"))
    speaker_surface = _safe_mapping(surface.get("speaker_surface"))
    roles = _safe_list(role_surface.get("roles"))
    segments = _safe_list(speaker_surface.get("segments"))

    sections = [
        _outline_section(
            topic=topic_value,
            output_intent=output_intent,
            role_count=len(roles),
            segment_count=len(segments),
        ),
        _paragraph_section(
            segments=segments,
            speaker_segment_count_hint=speaker_segment_count_hint,
        ),
        _emphasis_section(
            output_intent=output_intent,
            operator_notes=operator_notes,
            target_languages=target_languages,
        ),
        _rhythm_section(
            role_framing_hint=role_framing_hint,
            dub_kind_hint=dub_kind_hint,
            lip_sync_kind_hint=lip_sync_kind_hint,
        ),
    ]

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Workbench B · 内容结构面",
        "panel_subtitle_zh": (
            "只读视图；本面板不编辑脚本正文 / 段落 / 角色，仅从已派生的 entry / "
            "role-speaker 真理面投射结构骨架。"
        ),
        "title_label_zh": "标题 / 主题",
        "title_value": topic_value or None,
        "title_status_code": "from_entry_topic" if topic_value else "missing",
        "title_status_label_zh": (
            "来自创建表单 entry.topic" if topic_value else "—（未提供 entry.topic）"
        ),
        "source_script_ref_label_zh": "脚本来源句柄（source_script_ref）",
        "source_script_ref_value": source_script_ref or None,
        "source_script_ref_status_code": STATUS_OPAQUE_REF,
        "source_script_ref_status_label_zh": STATUS_OPAQUE_REF_LABEL_ZH,
        "language_scope_label_zh": "语言范围",
        "language_scope": {
            "source_language": source_language,
            "target_language": target_languages,
        },
        "output_intent_label_zh": "输出目标（output_intent）",
        "output_intent_value": output_intent or None,
        "operator_notes_label_zh": "运营备注（operator_notes）",
        "operator_notes_value": operator_notes or None,
        "speaker_segment_count_hint_label_zh": "段落规划数（speaker_segment_count_hint）",
        "speaker_segment_count_hint_value": speaker_segment_count_hint,
        "sections_label_zh": "内容结构（Outline / 段落 / 强调点 / 节奏）",
        "sections": sections,
        "phase_b_authoring_forbidden_label_zh": (
            "本面板为只读视图；OWC-DA gate spec §4.1 / §3 DA-W4 禁止运营在工作台层"
            "创作 roles[] / segments[] 枚举。"
        ),
    }


__all__ = [
    "SECTION_EMPHASIS",
    "SECTION_LABELS_ZH",
    "SECTION_OUTLINE",
    "SECTION_PARAGRAPH",
    "SECTION_RHYTHM",
    "STATUS_OPAQUE_REF",
    "STATUS_OPAQUE_REF_LABEL_ZH",
    "STATUS_RESOLVED",
    "STATUS_UNRESOLVED",
    "STATUS_UNRESOLVED_LABEL_ZH",
    "derive_digital_anchor_content_structure_view",
]
