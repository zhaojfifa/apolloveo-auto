"""OWC-MS PR-2 — Matrix Script Workbench A 脚本结构区 read-view tests (MS-W3).

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W3 (Workbench A read-view derived
  from existing ``source_script_ref``-resolved content; no operator authoring of
  ``source_script``).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1A.

Import-light: exercises the pure helper
``derive_matrix_script_script_structure_view`` over hand-built tasks that
mirror the shape produced by
``gateway/app/services/matrix_script/create_entry.py::build_matrix_script_task_payload``.

What is proved:

1. Returns ``{}`` for non-Matrix-Script tasks (Hot Follow / Digital Anchor /
   Baseline / empty / missing config) so the bundle attachment path is
   safe across line kinds.
2. Reads operator-language fields from ``task.config.entry`` (topic /
   source_script_ref / language_scope / target_platform /
   variation_target_count / tone_hint / audience_hint / length_hint).
3. ``source_script_ref`` rendering is opaque-by-construction; never
   dereferenced. Status code names the §0.2 product-meaning gating.
4. Hook / Body / CTA sections render with the structure skeleton +
   ``unauthored_pending_outline_contract`` sentinel + operator-language
   explanation pointing at the future Outline Contract per §9.2.
5. 关键词 / 禁用词 taxonomy renders with the same sentinel pattern.
6. Phase B authoring forbidden notice cites OWC-MS gate spec §4.1.
7. Validator R3 alignment — no vendor / model / provider / engine
   identifier in the return value.
8. Helper does not mutate the input task.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from gateway.app.services.matrix_script.script_structure_view import (
    SECTION_BODY,
    SECTION_CTA,
    SECTION_HOOK,
    STATUS_OPAQUE_REF,
    STATUS_UNAUTHORED,
    TAXONOMY_FORBIDDEN,
    TAXONOMY_KEYWORDS,
    derive_matrix_script_script_structure_view,
)


def _matrix_script_task(
    *,
    topic: str = "新季节促销",
    source_script_ref: str = "content://matrix-script/source/mint-deadbeef",
    source_language: str = "zh",
    target_language: list[str] | str = ("mm",),
    target_platform: str = "tiktok",
    variation_target_count: int = 6,
    tone_hint: str = "casual",
    audience_hint: str = "b2c",
    length_hint: str = "60",
) -> dict[str, Any]:
    return {
        "task_id": "ms_ms_w3_001",
        "id": "ms_ms_w3_001",
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "category": "matrix_script",
        "platform": "matrix_script",
        "config": {
            "line_id": "matrix_script",
            "entry_contract": "matrix_script_task_entry_v1",
            "entry": {
                "topic": topic,
                "source_script_ref": source_script_ref,
                "language_scope": {
                    "source_language": source_language,
                    "target_language": list(target_language)
                    if isinstance(target_language, (list, tuple))
                    else [target_language],
                },
                "target_platform": target_platform,
                "variation_target_count": variation_target_count,
                "tone_hint": tone_hint,
                "audience_hint": audience_hint,
                "length_hint": length_hint,
            },
        },
    }


# -- 1. Non-Matrix-Script tasks return empty bundle ----------------------


@pytest.mark.parametrize(
    "kind", ["hot_follow", "digital_anchor", "apollo_avatar", "baseline", "", None]
)
def test_non_matrix_script_kind_returns_empty(kind: str | None) -> None:
    task = _matrix_script_task()
    task["kind"] = kind
    task["category_key"] = kind
    task["category"] = kind
    task["platform"] = kind
    task["config"]["line_id"] = kind
    assert derive_matrix_script_script_structure_view(task) == {}


def test_empty_input_returns_empty() -> None:
    assert derive_matrix_script_script_structure_view(None) == {}
    assert derive_matrix_script_script_structure_view({}) == {}
    assert derive_matrix_script_script_structure_view({"kind": "matrix_script"}) == {}


# -- 2. Entry-derived operator-language fields --------------------------


def test_title_value_reads_entry_topic() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(topic="春节短视频")
    )
    assert bundle["title_value"] == "春节短视频"
    assert bundle["title_status_code"] == "from_entry_topic"


def test_title_value_marks_missing_when_topic_blank() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task(topic=""))
    assert bundle["title_value"] == ""
    assert bundle["title_status_code"] == "missing"


def test_target_platform_and_variation_target_count_render() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(target_platform="douyin", variation_target_count=9)
    )
    assert bundle["target_platform_value"] == "douyin"
    assert bundle["variation_target_count_value"] == 9


def test_axis_hints_passthrough() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(tone_hint="formal", audience_hint="b2b", length_hint="90")
    )
    hints = bundle["axis_hints"]
    assert hints["tone_hint"] == "formal"
    assert hints["audience_hint"] == "b2b"
    assert hints["length_hint"] == "90"


def test_axis_hints_normalize_blank_to_none() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(tone_hint="", audience_hint="", length_hint="")
    )
    hints = bundle["axis_hints"]
    assert hints["tone_hint"] is None
    assert hints["audience_hint"] is None
    assert hints["length_hint"] is None


def test_language_scope_renders_source_and_target() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(source_language="zh", target_language=["mm", "vi"])
    )
    scope = bundle["language_scope"]
    assert scope["source_language"] == "zh"
    assert scope["target_language"] == ["mm", "vi"]


def test_variation_target_count_invalid_string_collapses_to_none() -> None:
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(variation_target_count="oops")  # type: ignore[arg-type]
    )
    assert bundle["variation_target_count_value"] is None


# -- 3. source_script_ref is opaque-by-construction ---------------------


def test_source_script_ref_renders_verbatim() -> None:
    ref = "content://matrix-script/source/mint-cafebabe"
    bundle = derive_matrix_script_script_structure_view(
        _matrix_script_task(source_script_ref=ref)
    )
    assert bundle["source_script_ref_value"] == ref
    assert bundle["source_script_ref_status_code"] == STATUS_OPAQUE_REF


def test_source_script_ref_status_label_explains_opaque_handle() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    label = bundle["source_script_ref_status_label_zh"]
    assert "opaque" in label
    assert "Plan E F3" in label


# -- 4. Hook / Body / CTA section structure -----------------------------


def test_sections_render_three_in_order() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    assert [s["section_id"] for s in bundle["sections"]] == [
        SECTION_HOOK,
        SECTION_BODY,
        SECTION_CTA,
    ]


def test_section_bodies_render_unauthored_sentinel() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    for section in bundle["sections"]:
        assert section["body_text"] is None
        assert section["body_status_code"] == STATUS_UNAUTHORED
        assert "Outline Contract" in section["body_status_label_zh"]


def test_section_labels_use_operator_language() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    labels = {s["section_id"]: s["section_label_zh"] for s in bundle["sections"]}
    assert "Hook" in labels[SECTION_HOOK]
    assert "Body" in labels[SECTION_BODY]
    assert "CTA" in labels[SECTION_CTA]


# -- 5. 关键词 / 禁用词 taxonomy structure -------------------------------


def test_taxonomy_renders_two_in_order() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    assert [t["taxonomy_id"] for t in bundle["taxonomy"]] == [
        TAXONOMY_KEYWORDS,
        TAXONOMY_FORBIDDEN,
    ]


def test_taxonomy_renders_unauthored_sentinel() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    for tax in bundle["taxonomy"]:
        assert tax["values"] == []
        assert tax["values_status_code"] == STATUS_UNAUTHORED


def test_taxonomy_labels_use_operator_language() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    labels = {t["taxonomy_id"]: t["taxonomy_label_zh"] for t in bundle["taxonomy"]}
    assert labels[TAXONOMY_KEYWORDS] == "关键词"
    assert labels[TAXONOMY_FORBIDDEN] == "禁用词"


# -- 6. Phase B authoring forbidden notice ------------------------------


def test_phase_b_authoring_notice_cites_owc_ms_gate_spec_section_4_1() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    notice = bundle["phase_b_authoring_forbidden_label_zh"]
    assert "OWC-MS gate spec §4.1" in notice
    assert "source_script" in notice


# -- 7. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_script_structure_view(_matrix_script_task())
    forbidden = {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
    }

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value.keys()) & forbidden)
            for v in value.values():
                _walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _walk(v)

    _walk(bundle)


# -- 8. Helper does not mutate the input task ---------------------------


def test_helper_does_not_mutate_input() -> None:
    task = _matrix_script_task()
    snapshot = deepcopy(task)
    derive_matrix_script_script_structure_view(task)
    assert task == snapshot


def test_kind_alias_via_line_id_field_recognized() -> None:
    task = _matrix_script_task()
    task["kind"] = ""
    task["category_key"] = ""
    task["category"] = ""
    task["platform"] = ""
    # Recognized via task.config.line_id even when top-level kind aliases are blank.
    assert task["config"]["line_id"] == "matrix_script"
    bundle = derive_matrix_script_script_structure_view(task)
    assert bundle.get("is_matrix_script") is True
