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

from typing import Any, Mapping

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

# Closed status codes for body / taxonomy fields. The "unauthored_pending_outline_contract"
# status names the gate that lands the future Outline Contract per
# matrix_script_product_flow §9.2; until then the read-view explains the gap
# in operator language instead of inventing body content.
STATUS_UNAUTHORED = "unauthored_pending_outline_contract"
STATUS_UNAUTHORED_LABEL_ZH = "—（待 Outline Contract 授权后逐节呈现）"

STATUS_OPAQUE_REF = "opaque_source_script_ref"
STATUS_OPAQUE_REF_LABEL_ZH = (
    "脚本来源是 opaque 句柄；当前阶段不解引用，后续 Plan E F3 上线后展示 Hook / Body / CTA 正文。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _is_matrix_script_entry(entry: Mapping[str, Any], task: Mapping[str, Any]) -> bool:
    """Return True iff the inputs describe a Matrix Script task entry.

    The entry sub-dict is matrix_script-flavoured iff the parent task
    declares ``kind == "matrix_script"`` (or one of the equivalent line
    aliases used by the create-entry payload). Hot Follow / Digital
    Anchor / Baseline tasks never receive this read-view.
    """
    for key in ("kind", "category_key", "category", "platform", "line_id"):
        value = task.get(key) if isinstance(task, Mapping) else None
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return True
    config = _safe_mapping(task.get("config") if isinstance(task, Mapping) else None)
    return str(config.get("line_id") or "").strip().lower() == "matrix_script"


def _section(section_id: str) -> dict[str, Any]:
    """Return one structural section (Hook / Body / CTA) with sentinel body.

    The gate spec MS-W3 binds the read-view shape to "Hook / Body / CTA /
    关键词 / 禁用词 derived from existing source_script_ref-resolved
    content"; today's `source_script_ref` is opaque-by-construction (per
    §0.2 product-meaning) and is not dereferenced in this PR scope, so
    the body text falls through to the operator-language sentinel below.
    """
    return {
        "section_id": section_id,
        "section_label_zh": SECTION_LABELS_ZH[section_id],
        "body_text": None,
        "body_status_code": STATUS_UNAUTHORED,
        "body_status_label_zh": STATUS_UNAUTHORED_LABEL_ZH,
    }


def _taxonomy(taxonomy_id: str) -> dict[str, Any]:
    return {
        "taxonomy_id": taxonomy_id,
        "taxonomy_label_zh": TAXONOMY_LABELS_ZH[taxonomy_id],
        "values": [],
        "values_status_code": STATUS_UNAUTHORED,
        "values_status_label_zh": STATUS_UNAUTHORED_LABEL_ZH,
    }


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
    target_platform = str(entry.get("target_platform") or "").strip() or None
    variation_target_count_raw = entry.get("variation_target_count")
    try:
        variation_target_count = (
            int(variation_target_count_raw)
            if variation_target_count_raw is not None and variation_target_count_raw != ""
            else None
        )
    except (TypeError, ValueError):
        variation_target_count = None

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Workbench A · 脚本结构区",
        "panel_subtitle_zh": (
            "只读视图；本面板不编辑脚本正文，源脚本 source_script_ref 保持 opaque 句柄。"
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
        "target_platform_value": target_platform,
        "variation_target_count_label_zh": "变体目标数（variation_target_count）",
        "variation_target_count_value": variation_target_count,
        "sections_label_zh": "脚本结构（Hook / Body / CTA）",
        "sections": [_section(SECTION_HOOK), _section(SECTION_BODY), _section(SECTION_CTA)],
        "taxonomy_label_zh": "关键词 / 禁用词",
        "taxonomy": [_taxonomy(TAXONOMY_KEYWORDS), _taxonomy(TAXONOMY_FORBIDDEN)],
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
    "STATUS_UNAUTHORED",
    "STATUS_UNAUTHORED_LABEL_ZH",
    "TAXONOMY_FORBIDDEN",
    "TAXONOMY_KEYWORDS",
    "TAXONOMY_LABELS_ZH",
    "derive_matrix_script_script_structure_view",
]
