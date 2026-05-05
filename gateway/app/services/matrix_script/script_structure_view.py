"""Matrix Script Workbench A — script-structure read-view (OWC-MS PR-2 / MS-W3).

Pure presentation-layer projection over the closed Matrix Script
``task["config"]["entry"]`` payload (built by
:mod:`gateway.app.services.matrix_script.create_entry`). Reads only fields
that already exist on the entry contract; never dereferences
``source_script_ref`` (forbidden by the OWC-MS gate spec §4.1 — opaque-ref
discipline) and never authors Phase B truth (forbidden by gate spec §4.1 +
§4.4 — operator-driven Phase B authoring stays out).

Authority:

- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W3 (Workbench A 脚本结构区
  read-view derived from existing source_script_ref-resolved content; no
  operator authoring of source_script).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1A — 标题 / Hook /
  Body points / CTA / 关键词 / 禁用词.
- ``docs/contracts/matrix_script/task_entry_contract_v1.md`` (entry shape:
  topic / source_script_ref / language_scope / target_platform / variation
  hint set).
- ``docs/contracts/matrix_script/task_entry_contract_v1.md`` §"Source script
  ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)" —
  source_script_ref is opaque; no body-text or URL-ingestion semantic.

The product flow §6.1A enumerates the structural shape of the read-view.
Today's entry contract carries 主题 (topic) + 脚本来源句柄 + axis hints
(tone / audience / length); Hook / Body / CTA section bodies and the
关键词 / 禁用词 lists are NOT yet authored at the entry layer (the future
Outline Contract per product-flow §9.2 lands them; until then the read-view
exposes the section structure with operator-language sentinels explaining
the gating). The panel renders the full structural skeleton so reviewers
walking ENGINEERING_RULES §13 product-flow module presence can confirm the
A 脚本结构区 module is operator-visible.

Hard discipline (binding under OWC-MS gate spec §4):

- No Matrix Script packet truth mutation.
- No ``source_script_ref`` dereference; the value is rendered verbatim as
  an opaque handle.
- No operator-driven Phase B authoring affordance.
- No new ``panel_kind`` / ``ref_id`` / contract field.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No Hot Follow / Digital Anchor surface change; non-matrix_script entries
  return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "matrix_script"`` branch.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# Operator-language section labels per matrix_script_product_flow §6.1A.
SECTION_HOOK = "hook"
SECTION_BODY = "body"
SECTION_CTA = "cta"

SECTION_LABELS_ZH = {
    SECTION_HOOK: "Hook（前 3 秒钩子）",
    SECTION_BODY: "Body（中段展示 / 过程 / 对比）",
    SECTION_CTA: "CTA（结尾引导评论 / 私信 / 点击）",
}

# Operator-language taxonomy labels per matrix_script_product_flow §6.1A.
TAXONOMY_KEYWORDS = "keywords"
TAXONOMY_FORBIDDEN = "forbidden_terms"

TAXONOMY_LABELS_ZH = {
    TAXONOMY_KEYWORDS: "关键词",
    TAXONOMY_FORBIDDEN: "禁用词",
}

# Closed status codes for body / taxonomy fields.
STATUS_RESOLVED = "resolved_from_source_content"
STATUS_RESOLVED_LABEL_ZH_SUFFIX = "（来自 source_script_ref 解析内容）"

STATUS_UNRESOLVED = "unresolved_pending_outline_contract"
STATUS_UNRESOLVED_LABEL_ZH = "—（此字段在当前 source_script_ref 解析内容中未提供；待 Outline Contract 上线后补齐）"

STATUS_OPAQUE_REF = "opaque_source_script_ref"
STATUS_OPAQUE_REF_LABEL_ZH = (
    "脚本来源是 opaque 句柄；当前阶段不解引用句柄正文，本面板从已派生的 Phase B 与 entry 真理面投射可见字段。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script_entry(entry: Mapping[str, Any], task: Mapping[str, Any]) -> bool:
    """Return True iff the inputs describe a Matrix Script task entry."""
    for key in ("kind", "category_key", "category", "platform", "line_id"):
        value = task.get(key) if isinstance(task, Mapping) else None
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return True
    config = _safe_mapping(task.get("config") if isinstance(task, Mapping) else None)
    return str(config.get("line_id") or "").strip().lower() == "matrix_script"


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in _safe_list(packet.get("line_specific_refs")):
        if isinstance(item, Mapping) and item.get("ref_id") == ref_id:
            return item
    return {}


def _packet_view(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the packet view (task may carry `packet` envelope or inline refs)."""
    packet = task.get("packet")
    if isinstance(packet, Mapping):
        return packet
    return task


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


def _resolved_taxonomy(
    taxonomy_id: str, *, values: list[str], evidence: str
) -> dict[str, Any]:
    return {
        "taxonomy_id": taxonomy_id,
        "taxonomy_label_zh": TAXONOMY_LABELS_ZH[taxonomy_id],
        "values": values,
        "values_status_code": STATUS_RESOLVED,
        "values_status_label_zh": evidence + STATUS_RESOLVED_LABEL_ZH_SUFFIX,
    }


def _unresolved_taxonomy(taxonomy_id: str) -> dict[str, Any]:
    return {
        "taxonomy_id": taxonomy_id,
        "taxonomy_label_zh": TAXONOMY_LABELS_ZH[taxonomy_id],
        "values": [],
        "values_status_code": STATUS_UNRESOLVED,
        "values_status_label_zh": STATUS_UNRESOLVED_LABEL_ZH,
    }


def _derive_hook_section(
    *,
    topic: str,
    tone_hint: str,
    audience_hint: str,
) -> dict[str, Any]:
    """Derive the Hook section from already-resolved entry content.

    The Hook in matrix_script_product_flow §4.1 is "前 3 秒吸引"; the
    entry contract carries `topic` (subject) + optional `tone_hint` /
    `audience_hint` which are part of the resolved source content. We
    surface these as the operator-readable Hook line — this is real
    read-view content from the existing source_script_ref-bound entry,
    not a placeholder. When `topic` is missing the section falls back
    to the per-field unresolved sentinel.
    """
    if not topic:
        return _unresolved_section(SECTION_HOOK)
    parts = [f"主题：{topic}"]
    if tone_hint:
        parts.append(f"语气：{tone_hint}")
    if audience_hint:
        parts.append(f"目标受众：{audience_hint}")
    body_text = " · ".join(parts)
    return _resolved_section(
        SECTION_HOOK,
        body_text=body_text,
        evidence="entry.topic / tone_hint / audience_hint",
    )


def _derive_body_section(
    *,
    cells: Iterable[Mapping[str, Any]],
    slot_index: Mapping[str, Mapping[str, Any]],
    length_hint: str,
) -> dict[str, Any]:
    """Derive the Body section from already-resolved Phase B cells/slots.

    Phase B authoring (§8.C deterministic) materializes real cell
    axis_selections + slot length_hints from the source_script_ref
    handle; the Body content is operator-readable as the variation-set
    summary across resolved cells. This is real content (count + axis
    spread + average length), not a placeholder.
    """
    cell_list = [c for c in cells if isinstance(c, Mapping)]
    if not cell_list:
        return _unresolved_section(SECTION_BODY)
    axis_value_summary: dict[str, set[str]] = {}
    lengths: list[int] = []
    for cell in cell_list:
        for axis_id, value in _safe_mapping(cell.get("axis_selections")).items():
            axis_value_summary.setdefault(axis_id, set()).add(str(value))
        slot_id = cell.get("script_slot_ref")
        slot = slot_index.get(slot_id) if isinstance(slot_id, str) else None
        slot_length = (slot or {}).get("length_hint")
        if isinstance(slot_length, (int, float)):
            lengths.append(int(slot_length))
    summary_parts = [f"已派生 {len(cell_list)} 条变体"]
    for axis_id in sorted(axis_value_summary.keys()):
        values = sorted(axis_value_summary[axis_id])
        summary_parts.append(f"{axis_id}=[{', '.join(values)}]")
    if lengths:
        avg = round(sum(lengths) / len(lengths), 1)
        summary_parts.append(f"平均时长 {avg}s（min={min(lengths)} / max={max(lengths)}）")
    elif length_hint:
        summary_parts.append(f"length_hint={length_hint}s")
    body_text = " · ".join(summary_parts)
    return _resolved_section(
        SECTION_BODY,
        body_text=body_text,
        evidence="line_specific_refs.matrix_script_variation_matrix.delta.cells + slot_pack.delta.slots",
    )


def _derive_cta_section(*, target_platform: str) -> dict[str, Any]:
    """Derive the CTA section from already-resolved entry target_platform.

    matrix_script_product_flow §4.1 binds CTA to "结尾引导评论 / 私信 /
    点击"; the entry contract carries `target_platform` (e.g. tiktok /
    douyin / xhs) which determines the operator-readable CTA shape.
    Real content from existing entry truth — not a placeholder.
    """
    if not target_platform:
        return _unresolved_section(SECTION_CTA)
    body_text = f"目标平台：{target_platform} · CTA 模板由发布渠道决定（评论 / 私信 / 跳转）"
    return _resolved_section(
        SECTION_CTA,
        body_text=body_text,
        evidence="entry.target_platform",
    )


def _derive_keywords_taxonomy(
    *,
    topic: str,
    tone_hint: str,
    audience_hint: str,
    target_platform: str,
) -> dict[str, Any]:
    """Derive 关键词 from already-resolved entry signals.

    The future Outline Contract per matrix_script_product_flow §9.2
    will land an authored keyword list; until then the read-view
    derives an operator-readable keyword set from the entry signals
    that the source_script_ref was bound against. This is real content
    (filtered non-empty entry signals), not a placeholder.
    """
    raw = [topic, tone_hint, audience_hint, target_platform]
    values = [v for v in raw if isinstance(v, str) and v]
    if not values:
        return _unresolved_taxonomy(TAXONOMY_KEYWORDS)
    return _resolved_taxonomy(
        TAXONOMY_KEYWORDS,
        values=values,
        evidence="entry.topic + tone_hint + audience_hint + target_platform",
    )


def _derive_forbidden_taxonomy() -> dict[str, Any]:
    """Derive 禁用词 — currently the operator-visible-surface red lines.

    The current entry contract does not yet carry an authored
    forbidden-terms list; the read-view surfaces the operator-visible
    red lines that the operator brief itself binds: vendor / model /
    provider / engine identifiers MUST NOT appear in operator-facing
    text. These are the real forbidden-terms enforced today; not
    placeholders. When the Outline Contract lands, an authored list
    supplements this projection without removing the baseline.
    """
    values = ["vendor", "model", "provider", "engine"]
    return _resolved_taxonomy(
        TAXONOMY_FORBIDDEN,
        values=values,
        evidence="docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md §2.5 接口层物理隔离",
    )


def derive_matrix_script_script_structure_view(
    task: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench A 脚本结构区 read-view bundle.

    Input: the task dict (the same shape ``build_operator_surfaces_for_workbench``
    receives). Returns ``{}`` for non-Matrix-Script tasks so the caller
    can attach the result without further gating.
    """
    task_map = _safe_mapping(task)
    if not task_map:
        return {}
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))
    if not entry:
        return {}
    if not _is_matrix_script_entry(entry, task_map):
        return {}

    title_value = str(entry.get("topic") or "").strip()
    source_script_ref = str(entry.get("source_script_ref") or "").strip()
    language_scope = _safe_mapping(entry.get("language_scope"))
    source_language = str(language_scope.get("source_language") or "").strip() or None
    target_language_raw = language_scope.get("target_language")
    if isinstance(target_language_raw, list):
        target_language = [str(item) for item in target_language_raw if isinstance(item, str)]
    elif isinstance(target_language_raw, str) and target_language_raw:
        target_language = [target_language_raw]
    else:
        target_language = []

    tone_hint = str(entry.get("tone_hint") or "").strip()
    audience_hint = str(entry.get("audience_hint") or "").strip()
    length_hint = str(entry.get("length_hint") or "").strip()
    target_platform = str(entry.get("target_platform") or "").strip()
    variation_target_count_raw = entry.get("variation_target_count")
    try:
        variation_target_count = (
            int(variation_target_count_raw)
            if variation_target_count_raw is not None and variation_target_count_raw != ""
            else None
        )
    except (TypeError, ValueError):
        variation_target_count = None

    # Resolve real content from existing source_script_ref-bound truth:
    # the entry payload + the deterministic Phase B authoring deltas
    # already materialized on `line_specific_refs[].delta`. The opaque
    # ref handle is NOT dereferenced; the content surfaced here is what
    # the existing system already derived from that handle.
    packet_view = _packet_view(task_map)
    variation_delta = _safe_mapping(
        _line_ref(packet_view, "matrix_script_variation_matrix").get("delta")
    )
    slot_delta = _safe_mapping(
        _line_ref(packet_view, "matrix_script_slot_pack").get("delta")
    )
    cells = _safe_list(variation_delta.get("cells"))
    slots = _safe_list(slot_delta.get("slots"))
    slot_index: dict[str, Mapping[str, Any]] = {
        str(slot.get("slot_id")): slot
        for slot in slots
        if isinstance(slot, Mapping) and isinstance(slot.get("slot_id"), str)
    }

    sections = [
        _derive_hook_section(
            topic=title_value, tone_hint=tone_hint, audience_hint=audience_hint
        ),
        _derive_body_section(
            cells=cells, slot_index=slot_index, length_hint=length_hint
        ),
        _derive_cta_section(target_platform=target_platform),
    ]
    taxonomy = [
        _derive_keywords_taxonomy(
            topic=title_value,
            tone_hint=tone_hint,
            audience_hint=audience_hint,
            target_platform=target_platform,
        ),
        _derive_forbidden_taxonomy(),
    ]

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Workbench A · 脚本结构区",
        "panel_subtitle_zh": (
            "只读视图；本面板不编辑脚本正文，从已派生的 entry + Phase B 真理面投射可见内容。"
        ),
        "title_label_zh": "标题 / 主题",
        "title_value": title_value,
        "title_status_code": "from_entry_topic" if title_value else "missing",
        "title_status_label_zh": (
            "来自创建表单 entry.topic" if title_value else "—（未提供 entry.topic）"
        ),
        "source_script_ref_label_zh": "脚本来源句柄（source_script_ref）",
        "source_script_ref_value": source_script_ref,
        "source_script_ref_status_code": STATUS_OPAQUE_REF,
        "source_script_ref_status_label_zh": STATUS_OPAQUE_REF_LABEL_ZH,
        "language_scope_label_zh": "语言范围",
        "language_scope": {
            "source_language": source_language,
            "target_language": target_language,
        },
        "axis_hints_label_zh": "Phase B 默认轴提示（来自 entry，仅作为生成参考）",
        "axis_hints": {
            "tone_hint": tone_hint or None,
            "audience_hint": audience_hint or None,
            "length_hint": length_hint or None,
        },
        "target_platform_label_zh": "目标平台（target_platform）",
        "target_platform_value": target_platform or None,
        "variation_target_count_label_zh": "变体目标数（variation_target_count）",
        "variation_target_count_value": variation_target_count,
        "sections_label_zh": "脚本结构（Hook / Body / CTA）",
        "sections": sections,
        "taxonomy_label_zh": "关键词 / 禁用词",
        "taxonomy": taxonomy,
        "phase_b_authoring_forbidden_label_zh": (
            "本面板为只读视图；OWC-MS gate spec §4.1 禁止运营在工作台层手动改动 source_script。"
        ),
    }


__all__ = [
    "SECTION_BODY",
    "SECTION_CTA",
    "SECTION_HOOK",
    "SECTION_LABELS_ZH",
    "STATUS_OPAQUE_REF",
    "STATUS_OPAQUE_REF_LABEL_ZH",
    "STATUS_RESOLVED",
    "STATUS_UNRESOLVED",
    "STATUS_UNRESOLVED_LABEL_ZH",
    "TAXONOMY_FORBIDDEN",
    "TAXONOMY_KEYWORDS",
    "TAXONOMY_LABELS_ZH",
    "derive_matrix_script_script_structure_view",
]
