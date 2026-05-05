"""Digital Anchor Workbench D — language output view (OWC-DA PR-2 / DA-W6).

Pure presentation-layer projection over three already-existing surfaces:

- ``task["config"]["entry"]`` — the closed eleven-field entry contract,
  in particular ``language_scope = {source_language, target_language}``
  per :mod:`gateway.app.services.digital_anchor.create_entry`.
- ``digital_anchor_workbench_role_speaker_surface_v1`` from
  :mod:`gateway.app.services.digital_anchor.workbench_role_speaker_surface`
  (per-segment ``language_pick`` already projected).
- ``digital_anchor_delivery_binding_v1`` from
  :mod:`gateway.app.services.digital_anchor.delivery_binding`
  (per-row deliverables — subtitle / audio / lip_sync — exposing the
  per-language artifact rows).

Authority:

- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W6 (Workbench D 语言输出面 +
  multi-language navigator: Target Language / Subtitle Strategy /
  Terminology / 多版本语言切换 read-view bound to ``language_scope``;
  多版本切换 surfaces existing per-language artifact rows).
- ``docs/product/digital_anchor_product_flow_v1.md`` §6.1D — Target
  Language / Subtitle Strategy / Terminology Rules / 多版本语言切换.
- ``docs/product/digital_anchor_product_flow_v1.md`` §7.3 — 展示语言版本
  与音频版本.

Hard discipline (binding under OWC-DA gate spec §4):

- No Digital Anchor packet truth mutation.
- Read-only over ``language_scope`` and per-language artifact rows
  derived from delivery binding; no schema widening.
- No vendor / model / provider / engine identifier in the return value
  (validator R3); no operator selection of TTS provider / subtitle
  engine.
- No new ``panel_kind`` / ``ref_id`` / contract field.
- No Hot Follow / Matrix Script surface change; non-digital-anchor
  panels return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "digital_anchor"`` branch.
"""
from __future__ import annotations

from typing import Any, Mapping


# Operator-language facet labels per digital_anchor_product_flow §6.1D.
LANGUAGE_FACET_TARGET = "target_language"
LANGUAGE_FACET_SUBTITLE = "subtitle_strategy"
LANGUAGE_FACET_TERMINOLOGY = "terminology"
LANGUAGE_FACET_NAVIGATOR = "version_navigator"

LANGUAGE_FACET_ORDER = (
    LANGUAGE_FACET_TARGET,
    LANGUAGE_FACET_SUBTITLE,
    LANGUAGE_FACET_TERMINOLOGY,
    LANGUAGE_FACET_NAVIGATOR,
)

LANGUAGE_FACET_LABELS_ZH = {
    LANGUAGE_FACET_TARGET: "Target Language（目标语言）",
    LANGUAGE_FACET_SUBTITLE: "Subtitle Strategy（字幕策略）",
    LANGUAGE_FACET_TERMINOLOGY: "Terminology（术语）",
    LANGUAGE_FACET_NAVIGATOR: "多版本语言切换",
}

LANGUAGE_FACET_GUIDANCE_ZH = {
    LANGUAGE_FACET_TARGET: "由 entry.language_scope.target_language 决定，本面板不修改语言集合。",
    LANGUAGE_FACET_SUBTITLE: "由 capability_plan.subtitles 与 speaker_plan.segments[].language_pick 决定。",
    LANGUAGE_FACET_TERMINOLOGY: "术语规则待 Language Plan Contract 落地；本面板暂以 entry / metadata 注释展示。",
    LANGUAGE_FACET_NAVIGATOR: "多版本切换浏览 delivery 既有 per-language artifact rows；本面板不触发生成。",
}

# Closed status codes for per-language artifact rows.
STATUS_LANGUAGE_BOUND = "language_artifact_bound"
STATUS_LANGUAGE_BOUND_LABEL_ZH = "已规划该语言版本，待合成 / 字幕产出。"

STATUS_LANGUAGE_UNRESOLVED = "language_artifact_unresolved"
STATUS_LANGUAGE_UNRESOLVED_LABEL_ZH = "—（该语言版本尚未在 delivery binding 出现）"

STATUS_LANGUAGE_NOT_REQUIRED = "language_capability_not_required"
STATUS_LANGUAGE_NOT_REQUIRED_LABEL_ZH = "—（该 capability 未启用，跳过此语言）"

# Closed subtitle-strategy state vocabulary derived from existing
# capability_plan + segments. The values are observable on existing
# truth; no operator selector is offered.
SUBTITLE_STRATEGY_REQUIRED = "subtitle_required"
SUBTITLE_STRATEGY_OPTIONAL = "subtitle_optional"
SUBTITLE_STRATEGY_DISABLED = "subtitle_disabled"
SUBTITLE_STRATEGY_UNKNOWN = "subtitle_unknown"

SUBTITLE_STRATEGY_LABELS_ZH = {
    SUBTITLE_STRATEGY_REQUIRED: "必交付字幕（capability_plan.subtitles.required=true）",
    SUBTITLE_STRATEGY_OPTIONAL: "可选字幕（capability_plan.subtitles.required=false）",
    SUBTITLE_STRATEGY_DISABLED: "无字幕能力（capability_plan 未声明 subtitles）",
    SUBTITLE_STRATEGY_UNKNOWN: "—（capability_plan 不可读）",
}


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_digital_anchor(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "digital_anchor"


def _derive_subtitle_strategy(
    capability_plan: list[Mapping[str, Any]],
) -> tuple[str, str]:
    """Map subtitles capability presence + required flag to the closed enum."""
    for cap in capability_plan:
        if not isinstance(cap, Mapping):
            continue
        if cap.get("kind") != "subtitles":
            continue
        if bool(cap.get("required", False)):
            return SUBTITLE_STRATEGY_REQUIRED, SUBTITLE_STRATEGY_LABELS_ZH[
                SUBTITLE_STRATEGY_REQUIRED
            ]
        return SUBTITLE_STRATEGY_OPTIONAL, SUBTITLE_STRATEGY_LABELS_ZH[
            SUBTITLE_STRATEGY_OPTIONAL
        ]
    if capability_plan is None:
        return SUBTITLE_STRATEGY_UNKNOWN, SUBTITLE_STRATEGY_LABELS_ZH[
            SUBTITLE_STRATEGY_UNKNOWN
        ]
    return SUBTITLE_STRATEGY_DISABLED, SUBTITLE_STRATEGY_LABELS_ZH[
        SUBTITLE_STRATEGY_DISABLED
    ]


def _segment_language_picks(
    segments: list[Mapping[str, Any]],
) -> set[str]:
    picks: set[str] = set()
    for segment in segments:
        if not isinstance(segment, Mapping):
            continue
        pick = segment.get("language_pick")
        if isinstance(pick, str) and pick:
            picks.add(pick)
    return picks


def _per_language_rows(
    *,
    target_languages: list[str],
    source_language: str | None,
    segment_picks: set[str],
    capability_plan: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Render one operator-readable lane per target language.

    Each lane reports whether segments + capabilities cover the language;
    no synthesised artifact url, no provider hint.
    """
    subtitles_required = any(
        isinstance(cap, Mapping)
        and cap.get("kind") == "subtitles"
        and bool(cap.get("required", False))
        for cap in capability_plan
    )
    dub_required = any(
        isinstance(cap, Mapping)
        and cap.get("kind") == "dub"
        and bool(cap.get("required", False))
        for cap in capability_plan
    )
    rows: list[dict[str, Any]] = []
    for language in target_languages:
        has_segment_pick = language in segment_picks
        if has_segment_pick:
            status_code = STATUS_LANGUAGE_BOUND
            status_label_zh = STATUS_LANGUAGE_BOUND_LABEL_ZH
        elif not segment_picks:
            status_code = STATUS_LANGUAGE_UNRESOLVED
            status_label_zh = STATUS_LANGUAGE_UNRESOLVED_LABEL_ZH
        else:
            status_code = STATUS_LANGUAGE_UNRESOLVED
            status_label_zh = STATUS_LANGUAGE_UNRESOLVED_LABEL_ZH
        rows.append(
            {
                "language": language,
                "is_source_language": language == source_language,
                "has_segment_pick": has_segment_pick,
                "subtitle_required": subtitles_required,
                "dub_required": dub_required,
                "status_code": status_code,
                "status_label_zh": status_label_zh,
            }
        )
    return rows


def _navigator_artifacts_per_language(
    delivery_binding: Mapping[str, Any],
    target_languages: list[str],
) -> list[dict[str, Any]]:
    """Surface existing per-language artifact rows from delivery binding.

    Reads only the existing deliverable kinds on the Phase C delivery
    projection (`subtitle_bundle` / `audio_bundle` / `lip_sync_bundle`)
    and renders one row per language × kind. ``artifact_lookup`` is
    rendered verbatim — when Phase C placeholder
    ``"not_implemented_phase_c"`` is in effect the row still surfaces in
    operator language so the navigator stays observable.
    """
    delivery_pack = _safe_mapping(delivery_binding.get("delivery_pack"))
    deliverables = _safe_list(delivery_pack.get("deliverables"))
    relevant_kinds = {"subtitle_bundle", "audio_bundle", "lip_sync_bundle"}
    relevant_rows = [
        row
        for row in deliverables
        if isinstance(row, Mapping) and row.get("kind") in relevant_kinds
    ]
    nav_rows: list[dict[str, Any]] = []
    for language in target_languages:
        per_kind: dict[str, Any] = {}
        for row in relevant_rows:
            kind = row.get("kind")
            per_kind[str(kind)] = {
                "deliverable_id": row.get("deliverable_id"),
                "required": bool(row.get("required", False)),
                "artifact_lookup": row.get("artifact_lookup"),
                "source_ref_id": row.get("source_ref_id"),
            }
        nav_rows.append(
            {
                "language": language,
                "per_kind": per_kind,
            }
        )
    return nav_rows


def derive_digital_anchor_language_output_view(
    task: Mapping[str, Any] | None,
    role_speaker_surface: Mapping[str, Any] | None,
    delivery_binding: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Workbench D 语言输出面 + multi-language
    navigator read-view bundle.

    Returns ``{}`` when the panel is not Digital Anchor, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_digital_anchor(panel):
        return {}

    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))
    language_scope = _safe_mapping(entry.get("language_scope"))
    source_language = str(language_scope.get("source_language") or "").strip() or None
    target_language_raw = language_scope.get("target_language")
    if isinstance(target_language_raw, list):
        target_languages = [
            str(item) for item in target_language_raw if isinstance(item, str)
        ]
    elif isinstance(target_language_raw, str) and target_language_raw:
        target_languages = [target_language_raw]
    else:
        target_languages = []

    surface = _safe_mapping(role_speaker_surface)
    speaker_surface = _safe_mapping(surface.get("speaker_surface"))
    segments = _safe_list(speaker_surface.get("segments"))
    segment_picks = _segment_language_picks(segments)

    binding = _safe_mapping(delivery_binding)
    capability_plan = _safe_list(
        _safe_mapping(binding.get("result_packet_binding")).get("capability_plan")
    )
    subtitle_strategy_code, subtitle_strategy_label_zh = _derive_subtitle_strategy(
        capability_plan
    )

    operator_terminology = str(entry.get("operator_notes") or "").strip()

    per_language_rows = _per_language_rows(
        target_languages=target_languages,
        source_language=source_language,
        segment_picks=segment_picks,
        capability_plan=capability_plan,
    )

    navigator_rows = _navigator_artifacts_per_language(binding, target_languages)

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Workbench D · 语言输出面",
        "panel_subtitle_zh": (
            "只读视图；目标语言 / 字幕策略 / 多版本切换 由 language_scope + "
            "speaker_plan + delivery_binding 投射；本面板不切换 provider。"
        ),
        "language_scope_label_zh": "语言范围",
        "language_scope": {
            "source_language": source_language,
            "target_language": target_languages,
        },
        "subtitle_strategy_label_zh": "字幕策略",
        "subtitle_strategy_code": subtitle_strategy_code,
        "subtitle_strategy_label_value_zh": subtitle_strategy_label_zh,
        "terminology_label_zh": "术语 / 运营备注",
        "terminology_value": operator_terminology or None,
        "terminology_status_label_zh": (
            "Terminology 规则待 Language Plan Contract 落地；当前以 entry.operator_notes 兜底。"
        ),
        "per_language_label_zh": "目标语言覆盖（按段落 language_pick 派生）",
        "per_language_rows": per_language_rows,
        "navigator_label_zh": "多版本语言切换（按目标语言浏览 delivery 行）",
        "navigator_rows": navigator_rows,
        "facets_label_zh": "语言输出四要素",
        "facets": [
            {
                "facet_id": facet_id,
                "label_zh": LANGUAGE_FACET_LABELS_ZH[facet_id],
                "guidance_zh": LANGUAGE_FACET_GUIDANCE_ZH[facet_id],
            }
            for facet_id in LANGUAGE_FACET_ORDER
        ],
        "phase_b_authoring_forbidden_label_zh": (
            "本面板为只读视图；OWC-DA gate spec §4.1 / §3 DA-W6 禁止运营修改 "
            "language_scope 或新增 provider 控件。"
        ),
    }


__all__ = [
    "LANGUAGE_FACET_GUIDANCE_ZH",
    "LANGUAGE_FACET_LABELS_ZH",
    "LANGUAGE_FACET_NAVIGATOR",
    "LANGUAGE_FACET_ORDER",
    "LANGUAGE_FACET_SUBTITLE",
    "LANGUAGE_FACET_TARGET",
    "LANGUAGE_FACET_TERMINOLOGY",
    "STATUS_LANGUAGE_BOUND",
    "STATUS_LANGUAGE_BOUND_LABEL_ZH",
    "STATUS_LANGUAGE_NOT_REQUIRED",
    "STATUS_LANGUAGE_NOT_REQUIRED_LABEL_ZH",
    "STATUS_LANGUAGE_UNRESOLVED",
    "STATUS_LANGUAGE_UNRESOLVED_LABEL_ZH",
    "SUBTITLE_STRATEGY_DISABLED",
    "SUBTITLE_STRATEGY_LABELS_ZH",
    "SUBTITLE_STRATEGY_OPTIONAL",
    "SUBTITLE_STRATEGY_REQUIRED",
    "SUBTITLE_STRATEGY_UNKNOWN",
    "derive_digital_anchor_language_output_view",
]
