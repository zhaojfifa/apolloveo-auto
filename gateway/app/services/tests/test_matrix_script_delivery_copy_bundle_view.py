"""OWC-MS PR-3 / MS-W7 — Matrix Script Delivery Center copy_bundle exposure tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W7 (binding scope).
- ``docs/product/matrix_script_product_flow_v1.md`` §7.1 (标准交付物).
- ``gateway/app/services/matrix_script/delivery_copy_bundle_view.py`` (helper under test).

Import-light: exercises the pure helper
``derive_matrix_script_delivery_copy_bundle`` over hand-built inputs that
mirror the shapes reaching ``publish_hub_payload``.

What is proved:

1. Returns ``{}`` for non-Matrix-Script tasks (Hot Follow / Digital Anchor / unknown).
2. The four operator-language subfields render in the closed order
   ``title / hashtags / cta / comment_keywords`` per product-flow §7.1.
3. ``title`` resolves from ``base_copy_bundle.caption`` first, falls back
   to ``entry.topic`` when caption is empty, falls back to UNRESOLVED
   when both are empty.
4. ``hashtags`` resolves from ``base_copy_bundle.hashtags`` only, falls
   back to UNRESOLVED otherwise.
5. ``cta`` resolves from ``entry.target_platform`` and renders the
   operator-language CTA template; falls back to UNRESOLVED when missing.
6. ``comment_keywords`` resolves from ``base_copy_bundle.comment_cta``
   first, then ``audience_hint + tone_hint``, then UNRESOLVED.
7. Per-subfield UNRESOLVED fallback is independent — a panel-wide
   replacement is forbidden (PR-2 §8.1.1 reviewer-fail correction
   precedent).
8. Forbidden tokens (vendor / model_id / provider / engine) anywhere in
   any source field cause that subfield to fall back to UNRESOLVED
   without leaking the identifier.
9. Validator R3 alignment — no vendor / model / provider / engine
   identifier anywhere in the bundle (recursive walk).
10. Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
    FORBIDDEN_TOKEN_FRAGMENTS,
    STATUS_RESOLVED,
    STATUS_UNRESOLVED,
    SUBFIELD_CTA,
    SUBFIELD_COMMENT_KEYWORDS,
    SUBFIELD_HASHTAGS,
    SUBFIELD_LABELS_ZH,
    SUBFIELD_TITLE,
    derive_matrix_script_delivery_copy_bundle,
)


def _matrix_script_task(
    *,
    topic: str = "国货高端面霜矩阵",
    target_platform: str = "douyin",
    audience_hint: str = "26-35 都市女性",
    tone_hint: str = "理性 · 信赖",
) -> dict[str, Any]:
    return {
        "task_id": "task_ms_pr3_demo",
        "kind": "matrix_script",
        "config": {
            "entry": {
                "topic": topic,
                "target_platform": target_platform,
                "audience_hint": audience_hint,
                "tone_hint": tone_hint,
                "length_hint": "30-45s",
                "operator_notes": "",
            }
        },
    }


def _base_copy_bundle(
    *,
    caption: str = "",
    hashtags: str = "",
    comment_cta: str = "",
) -> dict[str, str]:
    return {
        "caption": caption,
        "hashtags": hashtags,
        "comment_cta": comment_cta,
        "link_text": "",
        "publish_time_suggestion": "",
    }


def _subfield(bundle: Mapping[str, Any], subfield_id: str) -> Mapping[str, Any]:
    for sub in bundle.get("subfields", []):
        if sub.get("subfield_id") == subfield_id:
            return sub
    raise AssertionError(
        f"subfield {subfield_id!r} missing from bundle subfields {bundle.get('subfields')!r}"
    )


# 1. Non-matrix_script callers receive {} (cross-line isolation).
@pytest.mark.parametrize("kind", ["hot_follow", "digital_anchor", "", "unknown"])
def test_returns_empty_for_non_matrix_script_kind(kind):
    task = {"task_id": "task_other", "kind": kind, "config": {"entry": {"topic": "X", "target_platform": "Y"}}}
    assert derive_matrix_script_delivery_copy_bundle(task) == {}


def test_returns_empty_for_none_task():
    assert derive_matrix_script_delivery_copy_bundle(None) == {}


def test_returns_empty_for_non_mapping_task():
    assert derive_matrix_script_delivery_copy_bundle("not-a-mapping") == {}


# 2. The four operator-language subfields render in the closed order.
def test_subfields_emit_four_in_stable_order():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(), base_copy_bundle=_base_copy_bundle()
    )
    ids = [sub["subfield_id"] for sub in bundle["subfields"]]
    assert ids == [
        SUBFIELD_TITLE,
        SUBFIELD_HASHTAGS,
        SUBFIELD_CTA,
        SUBFIELD_COMMENT_KEYWORDS,
    ]


def test_panel_title_and_subtitle_render():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(), base_copy_bundle=_base_copy_bundle()
    )
    assert bundle["is_matrix_script"] is True
    assert "copy_bundle" in bundle["panel_title_zh"]
    assert "product-flow §7.1" in bundle["panel_subtitle_zh"]


def test_subfield_label_zh_matches_product_flow_section_7_1():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(), base_copy_bundle=_base_copy_bundle()
    )
    label_map = {sub["subfield_id"]: sub["label_zh"] for sub in bundle["subfields"]}
    assert label_map[SUBFIELD_TITLE] == "标题"
    assert label_map[SUBFIELD_HASHTAGS] == "Hashtags"
    assert label_map[SUBFIELD_CTA] == "CTA"
    assert label_map[SUBFIELD_COMMENT_KEYWORDS] == "评论关键词"


# 3. title precedence: caption > entry.topic > unresolved.
def test_title_resolves_from_caption_when_present():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(caption="上头条 · 9.9 高端面霜实测"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_RESOLVED
    assert title["value"] == "上头条 · 9.9 高端面霜实测"
    assert title["value_source_id"] == "delivery_copy_bundle_caption"


def test_title_falls_back_to_topic_when_caption_empty():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic="国货高端面霜矩阵"),
        base_copy_bundle=_base_copy_bundle(caption=""),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_RESOLVED
    assert title["value"] == "国货高端面霜矩阵"
    assert title["value_source_id"] == "matrix_script_entry_topic"


def test_title_unresolved_when_both_caption_and_topic_empty():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic=""),
        base_copy_bundle=_base_copy_bundle(caption=""),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_UNRESOLVED
    assert title["value"] == ""
    assert title["value_source_id"] is None
    assert "Outline Contract" in title["unresolved_explanation_zh"]


# 4. hashtags precedence: hashtags > unresolved.
def test_hashtags_resolves_from_base_copy_bundle():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(hashtags="#国货 #面霜测评"),
    )
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    assert hashtags["status_code"] == STATUS_RESOLVED
    assert hashtags["value"] == "#国货 #面霜测评"
    assert hashtags["value_source_id"] == "delivery_copy_bundle_hashtags"


def test_hashtags_unresolved_when_empty():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(hashtags=""),
    )
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    assert hashtags["status_code"] == STATUS_UNRESOLVED
    assert hashtags["value"] == ""
    assert "copy 投射契约" in hashtags["unresolved_explanation_zh"]


# 5. cta from target_platform.
def test_cta_resolves_from_entry_target_platform():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(target_platform="douyin"),
        base_copy_bundle=_base_copy_bundle(),
    )
    cta = _subfield(bundle, SUBFIELD_CTA)
    assert cta["status_code"] == STATUS_RESOLVED
    assert "douyin" in cta["value"]
    assert "评论 / 私信" in cta["value"]
    assert cta["value_source_id"] == "matrix_script_entry_target_platform"


def test_cta_unresolved_when_target_platform_blank():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(target_platform=""),
        base_copy_bundle=_base_copy_bundle(),
    )
    cta = _subfield(bundle, SUBFIELD_CTA)
    assert cta["status_code"] == STATUS_UNRESOLVED
    assert cta["value"] == ""


# 6. comment_keywords precedence: comment_cta > audience+tone > audience > tone > unresolved.
def test_comment_keywords_resolves_from_comment_cta_first():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="A", tone_hint="B"),
        base_copy_bundle=_base_copy_bundle(comment_cta="评论关键词 · 复购"),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_RESOLVED
    assert comment["value"] == "评论关键词 · 复购"
    assert comment["value_source_id"] == "delivery_copy_bundle_comment_cta"


def test_comment_keywords_falls_back_to_audience_and_tone_combined():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="26-35 都市女性", tone_hint="理性 · 信赖"),
        base_copy_bundle=_base_copy_bundle(comment_cta=""),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_RESOLVED
    assert comment["value"] == "26-35 都市女性 · 理性 · 信赖"
    assert comment["value_source_id"] == "matrix_script_entry_audience_tone_hint"


def test_comment_keywords_falls_back_to_audience_only():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="26-35 都市女性", tone_hint=""),
        base_copy_bundle=_base_copy_bundle(comment_cta=""),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_RESOLVED
    assert comment["value"] == "26-35 都市女性"
    assert comment["value_source_id"] == "matrix_script_entry_audience_hint"


def test_comment_keywords_unresolved_when_all_sources_blank():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="", tone_hint=""),
        base_copy_bundle=_base_copy_bundle(comment_cta=""),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_UNRESOLVED
    assert comment["value"] == ""


# 7. Per-subfield unresolved fallback is independent — never panel-wide.
def test_per_subfield_unresolved_fallback_does_not_replace_resolved_subfields():
    # Title resolved from caption; hashtags unresolved; cta resolved from
    # platform; comment_keywords unresolved. The unresolved subfields must
    # not poison the resolved ones.
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="", tone_hint=""),
        base_copy_bundle=_base_copy_bundle(caption="标题文案"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    cta = _subfield(bundle, SUBFIELD_CTA)
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert title["status_code"] == STATUS_RESOLVED and title["value"] == "标题文案"
    assert hashtags["status_code"] == STATUS_UNRESOLVED
    assert cta["status_code"] == STATUS_RESOLVED and "douyin" in cta["value"]
    assert comment["status_code"] == STATUS_UNRESOLVED


def test_unresolved_count_and_tracked_gap_summary_emit_when_any_subfield_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic="", audience_hint="", tone_hint=""),
        base_copy_bundle=_base_copy_bundle(),
    )
    # title (caption empty, topic empty) + hashtags + comment_keywords all
    # unresolved; only CTA resolves via target_platform = "douyin".
    assert bundle["unresolved_count"] == 3
    assert bundle["tracked_gap_summary_zh"] != ""
    assert "panel-wide" in bundle["tracked_gap_summary_zh"]


def test_unresolved_count_zero_when_all_subfields_resolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(
            caption="标题", hashtags="#tag", comment_cta="评论关键词"
        ),
    )
    assert bundle["unresolved_count"] == 0
    assert bundle["tracked_gap_summary_zh"] == ""


# 8. Forbidden token scrub (validator R3).
@pytest.mark.parametrize("token", FORBIDDEN_TOKEN_FRAGMENTS)
def test_forbidden_token_in_caption_falls_back_to_topic(token):
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic="安全主题"),
        base_copy_bundle=_base_copy_bundle(caption=f"poison {token} value"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    # Caption is scrubbed, so title falls back to entry.topic source.
    assert title["status_code"] == STATUS_RESOLVED
    assert title["value"] == "安全主题"
    assert title["value_source_id"] == "matrix_script_entry_topic"


def test_forbidden_token_in_hashtags_renders_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(hashtags="#vendor_x #ok"),
    )
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    assert hashtags["status_code"] == STATUS_UNRESOLVED
    assert hashtags["value"] == ""


def test_forbidden_token_in_target_platform_falls_back_to_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(target_platform="provider_x_app"),
        base_copy_bundle=_base_copy_bundle(),
    )
    cta = _subfield(bundle, SUBFIELD_CTA)
    assert cta["status_code"] == STATUS_UNRESOLVED
    assert cta["value"] == ""


# 9. Validator R3 alignment — no vendor / model / provider / engine anywhere.
def _walk_strings(value: Any):
    if isinstance(value, Mapping):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


@pytest.mark.parametrize("token", FORBIDDEN_TOKEN_FRAGMENTS)
def test_bundle_carries_no_forbidden_token_recursively(token):
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(
            caption="标题", hashtags="#tag", comment_cta="评论关键词"
        ),
    )
    for s in _walk_strings(bundle):
        assert token not in s.lower(), f"forbidden token {token!r} leaked into {s!r}"


# 10. No input mutation.
def test_helper_does_not_mutate_task_or_base_copy_bundle():
    task = _matrix_script_task()
    copy_bundle = _base_copy_bundle(caption="标题", hashtags="#tag")
    task_snapshot = deepcopy(task)
    copy_snapshot = deepcopy(copy_bundle)
    derive_matrix_script_delivery_copy_bundle(task, base_copy_bundle=copy_bundle)
    assert task == task_snapshot
    assert copy_bundle == copy_snapshot


# Closed-shape invariants. These keep the rendering JS contract stable.
def test_each_subfield_carries_closed_keys_only():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="", tone_hint=""),
        base_copy_bundle=_base_copy_bundle(),
    )
    expected_keys = {
        "subfield_id",
        "label_zh",
        "status_code",
        "status_label_zh",
        "value",
        "value_source_id",
        "unresolved_explanation_zh",
    }
    for sub in bundle["subfields"]:
        assert set(sub.keys()) == expected_keys, sub


def test_resolved_subfield_carries_empty_unresolved_explanation():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(caption="标题文案"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_RESOLVED
    assert title["unresolved_explanation_zh"] == ""


def test_unresolved_subfield_carries_non_empty_explanation():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic=""),
        base_copy_bundle=_base_copy_bundle(),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_UNRESOLVED
    assert title["unresolved_explanation_zh"] != ""


def test_subfield_labels_match_module_constants():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(),
    )
    for sub in bundle["subfields"]:
        assert sub["label_zh"] == SUBFIELD_LABELS_ZH[sub["subfield_id"]]
