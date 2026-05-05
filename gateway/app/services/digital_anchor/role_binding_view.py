"""Digital Anchor Workbench A — role binding view (OWC-DA PR-2 / DA-W3).

Pure presentation-layer projection over two already-existing surfaces:

- ``digital_anchor_workbench_role_speaker_surface_v1`` from
  :mod:`gateway.app.services.digital_anchor.workbench_role_speaker_surface`
  (role / speaker / role-segment binding deltas projected from packet
  truth).
- ``task["config"]["entry"]`` from
  :mod:`gateway.app.services.digital_anchor.create_entry`
  (the closed eleven-field entry contract: ``role_profile_ref`` /
  ``role_framing_hint`` / ``dub_kind_hint`` / ``lip_sync_kind_hint`` /
  operator hints).

Authority:

- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W3 (Workbench A 角色绑定面:
  Role Profile select + 形象风格 + 声音 preset + 表达风格 + 情绪 read-view
  bound to existing ``role_pack_ref`` and ``speaker_plan_ref`` line-specific
  objects; operator action: select an existing ``role_pack`` from PR-2
  Asset Supply — **not** authoring).
- ``docs/product/digital_anchor_product_flow_v1.md`` §6.1A — 选择 Role
  Profile / 选择形象风格 / 选择声音 preset / 表达风格 / 情绪控制.

Hard discipline (binding under OWC-DA gate spec §4):

- No Digital Anchor packet truth mutation.
- No ``roles[]`` / ``segments[]`` operator authoring.
- No ``framing_kind_set`` / ``dub_kind_set`` / ``lip_sync_kind_set``
  widening; this view consumes the closed sets read-only.
- No vendor / model / provider / engine / avatar-engine / TTS-provider
  identifier in the return value (validator R3).
- No avatar platform / role catalog / scene catalog UI; the operator
  selection affordance is a read-only browse pointer back to PR-2 Asset
  Supply.
- No Hot Follow / Matrix Script surface change; non-digital-anchor
  panels return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "digital_anchor"`` branch.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .create_entry import (
    DUB_KIND_SET,
    LIP_SYNC_KIND_SET,
    ROLE_FRAMING_KIND_SET,
)


# Operator-language labels per digital_anchor_product_flow §6.1A. The
# closed-set order is intentionally fixed for stable rendering across
# templates and tests.
ROLE_FACET_ORDER = (
    "role_profile",
    "appearance_style",
    "voice_preset",
    "expression_style",
    "emotion",
)

ROLE_FACET_LABELS_ZH = {
    "role_profile": "Role Profile（角色档案）",
    "appearance_style": "形象风格",
    "voice_preset": "声音 preset",
    "expression_style": "表达风格",
    "emotion": "情绪",
}

ROLE_FACET_GUIDANCE_ZH = {
    "role_profile": "通过 PR-2 Asset Supply 选择已存在的 role_pack；本面板不创作角色资产。",
    "appearance_style": "由 role_pack 绑定的 framing_kind 决定；闭枚举：head / half_body / full_body。",
    "voice_preset": "由 speaker_plan 绑定的 dub_kind 决定；闭枚举：tts_neutral / tts_role_voice / source_passthrough。",
    "expression_style": "由 speaker_plan 绑定的 lip_sync_kind 决定；闭枚举：tight / loose / none。",
    "emotion": "由 entry.role_framing_hint + speaker_plan 段落选择共同表达；本面板只展示，不修改。",
}

ROLE_FRAMING_LABELS_ZH = {
    "head": "头肩（head）",
    "half_body": "半身（half_body）",
    "full_body": "全身（full_body）",
}

DUB_KIND_LABELS_ZH = {
    "tts_neutral": "中性 TTS（tts_neutral）",
    "tts_role_voice": "角色 TTS（tts_role_voice）",
    "source_passthrough": "源音透传（source_passthrough）",
}

LIP_SYNC_LABELS_ZH = {
    "tight": "强对位（tight）",
    "loose": "弱对位（loose）",
    "none": "不对位（none）",
}

# Operator action affordance — read-only pointer back to the PR-2 Asset
# Supply browse surface. The actual selection happens at the create
# stage; the workbench view never authors a new role_pack / speaker_plan.
ASSET_SUPPLY_BROWSE_ROLE_PACK_HINT = (
    "通过 Asset Supply（B-roll / 角色资产）浏览既有 role_pack；本工作台不创建或编辑角色。"
)
ASSET_SUPPLY_BROWSE_SPEAKER_HINT = (
    "声音 preset / 表达对位由 speaker_plan 已绑定的能力供给；本工作台不切换 provider。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_digital_anchor(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "digital_anchor"


def _role_facet(
    facet_id: str,
    *,
    value: Any,
    value_label_zh: str | None,
) -> dict[str, Any]:
    has_value = bool(value)
    return {
        "facet_id": facet_id,
        "label_zh": ROLE_FACET_LABELS_ZH[facet_id],
        "guidance_zh": ROLE_FACET_GUIDANCE_ZH[facet_id],
        "value": value if has_value else None,
        "value_label_zh": value_label_zh
        if value_label_zh is not None
        else (str(value) if has_value else None),
        "is_resolved": has_value,
    }


def _role_summary_rows(
    roles: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Render one operator-language row per role surfaced by the role pack."""
    rows: list[dict[str, Any]] = []
    for role in roles:
        if not isinstance(role, Mapping):
            continue
        framing = role.get("framing_kind")
        rows.append(
            {
                "role_id": role.get("role_id"),
                "display_name": role.get("display_name"),
                "framing_kind": framing,
                "framing_kind_label_zh": ROLE_FRAMING_LABELS_ZH.get(
                    str(framing) if framing else "",
                    str(framing) if framing else "—",
                ),
                "appearance_ref": role.get("appearance_ref"),
            }
        )
    return rows


def _segment_summary_rows(
    segments: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Render one operator-language row per segment surfaced by speaker plan."""
    rows: list[dict[str, Any]] = []
    for segment in segments:
        if not isinstance(segment, Mapping):
            continue
        dub_kind = segment.get("dub_kind")
        lip_sync_kind = segment.get("lip_sync_kind")
        rows.append(
            {
                "segment_id": segment.get("segment_id"),
                "binds_role_id": segment.get("binds_role_id"),
                "dub_kind": dub_kind,
                "dub_kind_label_zh": DUB_KIND_LABELS_ZH.get(
                    str(dub_kind) if dub_kind else "",
                    str(dub_kind) if dub_kind else "—",
                ),
                "lip_sync_kind": lip_sync_kind,
                "lip_sync_kind_label_zh": LIP_SYNC_LABELS_ZH.get(
                    str(lip_sync_kind) if lip_sync_kind else "",
                    str(lip_sync_kind) if lip_sync_kind else "—",
                ),
                "language_pick": segment.get("language_pick"),
            }
        )
    return rows


def _appearance_style_value(roles: list[Mapping[str, Any]]) -> tuple[Any, str | None]:
    """Aggregate framing kinds across roles into an operator label."""
    framings = [
        str(role.get("framing_kind"))
        for role in roles
        if isinstance(role, Mapping) and role.get("framing_kind")
    ]
    if not framings:
        return None, None
    distinct = sorted(set(framings))
    if len(distinct) == 1:
        framing = distinct[0]
        return framing, ROLE_FRAMING_LABELS_ZH.get(framing, framing)
    labels = [ROLE_FRAMING_LABELS_ZH.get(f, f) for f in distinct]
    return distinct, " / ".join(labels)


def _voice_preset_value(
    segments: list[Mapping[str, Any]], entry: Mapping[str, Any]
) -> tuple[Any, str | None]:
    """Aggregate dub kinds across segments; fall back to entry hint."""
    dubs = [
        str(segment.get("dub_kind"))
        for segment in segments
        if isinstance(segment, Mapping) and segment.get("dub_kind")
    ]
    if dubs:
        distinct = sorted(set(dubs))
        if len(distinct) == 1:
            dub = distinct[0]
            return dub, DUB_KIND_LABELS_ZH.get(dub, dub)
        labels = [DUB_KIND_LABELS_ZH.get(d, d) for d in distinct]
        return distinct, " / ".join(labels)
    hint = str(entry.get("dub_kind_hint") or "").strip()
    if hint:
        return hint, DUB_KIND_LABELS_ZH.get(hint, hint) + "（来自 entry.dub_kind_hint，待 Phase B 派生）"
    return None, None


def _expression_style_value(
    segments: list[Mapping[str, Any]], entry: Mapping[str, Any]
) -> tuple[Any, str | None]:
    """Aggregate lip_sync kinds across segments; fall back to entry hint."""
    lips = [
        str(segment.get("lip_sync_kind"))
        for segment in segments
        if isinstance(segment, Mapping) and segment.get("lip_sync_kind")
    ]
    if lips:
        distinct = sorted(set(lips))
        if len(distinct) == 1:
            lip = distinct[0]
            return lip, LIP_SYNC_LABELS_ZH.get(lip, lip)
        labels = [LIP_SYNC_LABELS_ZH.get(l, l) for l in distinct]
        return distinct, " / ".join(labels)
    hint = str(entry.get("lip_sync_kind_hint") or "").strip()
    if hint:
        return hint, LIP_SYNC_LABELS_ZH.get(hint, hint) + "（来自 entry.lip_sync_kind_hint，待 Phase B 派生）"
    return None, None


def _emotion_value(
    entry: Mapping[str, Any], roles: list[Mapping[str, Any]]
) -> tuple[Any, str | None]:
    """Operator-readable 情绪 line.

    No new contract field; the read-view re-states the operator-supplied
    role_framing_hint + the appearance distribution as a 情绪 line. When
    neither is available the facet stays unresolved.
    """
    role_framing_hint = str(entry.get("role_framing_hint") or "").strip()
    output_intent = str(entry.get("output_intent") or "").strip()
    if not role_framing_hint and not output_intent:
        return None, None
    parts: list[str] = []
    if role_framing_hint:
        parts.append(
            f"role_framing_hint={ROLE_FRAMING_LABELS_ZH.get(role_framing_hint, role_framing_hint)}"
        )
    if output_intent:
        parts.append(f"output_intent={output_intent}")
    if roles:
        parts.append(f"角色数={len(roles)}")
    label = " · ".join(parts)
    return {
        "role_framing_hint": role_framing_hint or None,
        "output_intent": output_intent or None,
        "role_count": len(roles),
    }, label


def derive_digital_anchor_role_binding_view(
    task: Mapping[str, Any] | None,
    role_speaker_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Workbench A 角色绑定面 read-view bundle.

    Returns ``{}`` when the panel is not Digital Anchor, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_digital_anchor(panel):
        return {}

    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))

    surface = _safe_mapping(role_speaker_surface)
    role_surface = _safe_mapping(surface.get("role_surface"))
    speaker_surface = _safe_mapping(surface.get("speaker_surface"))
    roles = _safe_list(role_surface.get("roles"))
    segments = _safe_list(speaker_surface.get("segments"))

    role_profile_ref = str(entry.get("role_profile_ref") or "").strip()
    appearance_value, appearance_label = _appearance_style_value(roles)
    voice_value, voice_label = _voice_preset_value(segments, entry)
    expression_value, expression_label = _expression_style_value(segments, entry)
    emotion_value, emotion_label = _emotion_value(entry, roles)

    facets = [
        _role_facet(
            "role_profile",
            value=role_profile_ref or None,
            value_label_zh=role_profile_ref or None,
        ),
        _role_facet(
            "appearance_style",
            value=appearance_value,
            value_label_zh=appearance_label,
        ),
        _role_facet(
            "voice_preset",
            value=voice_value,
            value_label_zh=voice_label,
        ),
        _role_facet(
            "expression_style",
            value=expression_value,
            value_label_zh=expression_label,
        ),
        _role_facet(
            "emotion",
            value=emotion_value,
            value_label_zh=emotion_label,
        ),
    ]

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Workbench A · 角色绑定面",
        "panel_subtitle_zh": (
            "只读视图；Role Profile / 形象 / 声音 / 表达 / 情绪 由已绑定的 role_pack + "
            "speaker_plan 投射，本面板不创作角色资产，不切换 provider。"
        ),
        "role_facets_label_zh": "角色五要素",
        "role_facets": facets,
        "role_summary_label_zh": "已绑定角色",
        "role_summary_rows": _role_summary_rows(roles),
        "speaker_summary_label_zh": "已绑定声音 / 对位段落",
        "speaker_summary_rows": _segment_summary_rows(segments),
        "asset_supply_browse_label_zh": "Asset Supply（资产浏览）",
        "asset_supply_browse_role_pack_hint_zh": ASSET_SUPPLY_BROWSE_ROLE_PACK_HINT,
        "asset_supply_browse_speaker_hint_zh": ASSET_SUPPLY_BROWSE_SPEAKER_HINT,
        "closed_set_explanation_zh": (
            "framing_kind ∈ {head, half_body, full_body}；"
            "dub_kind ∈ {tts_neutral, tts_role_voice, source_passthrough}；"
            "lip_sync_kind ∈ {tight, loose, none}。"
            "本面板只读，不可在工作台层扩展闭集。"
        ),
        "framing_kind_set": list(ROLE_FRAMING_KIND_SET),
        "dub_kind_set": list(DUB_KIND_SET),
        "lip_sync_kind_set": list(LIP_SYNC_KIND_SET),
        "phase_b_authoring_forbidden_label_zh": (
            "本面板不授权 roles[] / segments[] 创作（OWC-DA gate spec §4.1）。"
        ),
    }


__all__ = [
    "ASSET_SUPPLY_BROWSE_ROLE_PACK_HINT",
    "ASSET_SUPPLY_BROWSE_SPEAKER_HINT",
    "DUB_KIND_LABELS_ZH",
    "LIP_SYNC_LABELS_ZH",
    "ROLE_FACET_GUIDANCE_ZH",
    "ROLE_FACET_LABELS_ZH",
    "ROLE_FACET_ORDER",
    "ROLE_FRAMING_LABELS_ZH",
    "derive_digital_anchor_role_binding_view",
]
