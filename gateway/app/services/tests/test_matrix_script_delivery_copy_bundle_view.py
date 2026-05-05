"""OWC-MS PR-3 / MS-W7 — Matrix Script Delivery Center copy_bundle exposure tests.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W7 (binding scope) + §4.1
  (no second authoritative producer).
- ``docs/product/matrix_script_product_flow_v1.md`` §7.1 (标准交付物).
- ``gateway/app/services/matrix_script/delivery_copy_bundle_view.py`` (helper under test).
- OWC-MS PR-3 reviewer-fail correction Blocker 1 (2026-05-05): copy_bundle
  must not synthesize subfields from adjacent task-entry hints
  (``target_platform`` / ``audience_hint`` / ``tone_hint``); it may only
  consume the existing publish-hub ``copy_bundle`` projection.

Import-light: exercises the pure helper
``derive_matrix_script_delivery_copy_bundle`` over hand-built inputs
mirroring the publish-hub ``copy_bundle`` shape.

What is proved:

1. Returns ``{}`` for non-Matrix-Script tasks (Hot Follow / Digital Anchor / unknown).
2. The four operator-language subfields render in the closed order
   ``title / hashtags / cta / comment_keywords`` per product-flow §7.1.
3. Each subfield has EXACTLY ONE authorized source — the existing
   publish-hub ``copy_bundle`` projection. Adjacent entry hints
   (``target_platform`` / ``audience_hint`` / ``tone_hint`` / ``topic``)
   are NEVER consumed.
4. ``title`` resolves from ``base_copy_bundle.caption``; UNRESOLVED otherwise.
5. ``hashtags`` resolves from ``base_copy_bundle.hashtags``; UNRESOLVED otherwise.
6. ``cta`` resolves from ``base_copy_bundle.comment_cta``; UNRESOLVED otherwise.
7. ``comment_keywords`` is ALWAYS UNRESOLVED — no authoritative producer
   exists in the publish-hub ``copy_bundle`` shape today.
8. Per-subfield UNRESOLVED fallback is independent — a panel-wide
   replacement is forbidden.
9. Forbidden tokens (vendor / model_id / provider / engine) anywhere in
   any source field cause that subfield to fall back to UNRESOLVED
   without leaking the identifier.
10. Validator R3 alignment — no vendor / model / provider / engine
    identifier anywhere in the bundle (recursive walk).
11. Helper does not mutate inputs.
12. NEW (Blocker 1 invariant): synthesizing copy_bundle from adjacent
    entry hints alone produces ALL UNRESOLVED subfields. The hints are
    not a fallback source.
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


# 2. Four subfields in stable order.
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
    assert "publish-hub copy_bundle 投射" in bundle["panel_subtitle_zh"]


def test_subfield_label_zh_matches_product_flow_section_7_1():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(), base_copy_bundle=_base_copy_bundle()
    )
    label_map = {sub["subfield_id"]: sub["label_zh"] for sub in bundle["subfields"]}
    assert label_map[SUBFIELD_TITLE] == "标题"
    assert label_map[SUBFIELD_HASHTAGS] == "Hashtags"
    assert label_map[SUBFIELD_CTA] == "CTA"
    assert label_map[SUBFIELD_COMMENT_KEYWORDS] == "评论关键词"


# 3. title — single source from base_copy_bundle.caption.
def test_title_resolves_from_caption_when_present():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(caption="上头条 · 9.9 高端面霜实测"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_RESOLVED
    assert title["value"] == "上头条 · 9.9 高端面霜实测"
    assert title["value_source_id"] == "delivery_copy_bundle_caption"


def test_title_unresolved_when_caption_empty_even_if_topic_present():
    """Blocker 1 invariant: ``entry.topic`` MUST NOT be a fallback source.

    Even when ``topic`` is non-empty, an empty ``caption`` renders the
    title as UNRESOLVED — the helper is not a second copy producer."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic="国货高端面霜矩阵"),
        base_copy_bundle=_base_copy_bundle(caption=""),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    assert title["status_code"] == STATUS_UNRESOLVED
    assert title["value"] == ""
    assert title["value_source_id"] is None
    # Explanation cites the future copy projection contract, not the
    # missing entry hint.
    assert "copy 投射契约" in title["unresolved_explanation_zh"]


# 4. hashtags — single source from base_copy_bundle.hashtags.
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


# 5. cta — single source from base_copy_bundle.comment_cta. (Blocker 1: NOT
# synthesized from entry.target_platform.)
def test_cta_resolves_from_base_copy_bundle_comment_cta():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(comment_cta="点击主页查看更多 · 私信领取试用装"),
    )
    cta = _subfield(bundle, SUBFIELD_CTA)
    assert cta["status_code"] == STATUS_RESOLVED
    assert cta["value"] == "点击主页查看更多 · 私信领取试用装"
    assert cta["value_source_id"] == "delivery_copy_bundle_comment_cta"


def test_cta_unresolved_when_target_platform_present_but_comment_cta_empty():
    """Blocker 1 invariant: ``entry.target_platform`` MUST NOT be a CTA
    fallback source. Even with ``target_platform == "douyin"``, an empty
    ``comment_cta`` renders the CTA subfield as UNRESOLVED."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(target_platform="douyin"),
        base_copy_bundle=_base_copy_bundle(comment_cta=""),
    )
    cta = _subfield(bundle, SUBFIELD_CTA)
    assert cta["status_code"] == STATUS_UNRESOLVED
    assert cta["value"] == ""
    assert cta["value_source_id"] is None
    # The explanation must explicitly name the prohibition on hint
    # synthesis so reviewers can trace the discipline.
    assert "target_platform" in cta["unresolved_explanation_zh"]


# 6. comment_keywords — ALWAYS UNRESOLVED (no producer in copy_bundle today).
def test_comment_keywords_always_unresolved_regardless_of_inputs():
    """Blocker 1 invariant: ``audience_hint`` / ``tone_hint`` are not
    评论关键词 truth. Even when both hints are populated the subfield
    renders as UNRESOLVED."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(audience_hint="26-35 都市女性", tone_hint="理性 · 信赖"),
        base_copy_bundle=_base_copy_bundle(comment_cta="some-cta"),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_UNRESOLVED
    assert comment["value"] == ""
    assert comment["value_source_id"] is None
    assert (
        "audience_hint" in comment["unresolved_explanation_zh"]
        and "tone_hint" in comment["unresolved_explanation_zh"]
    )


def test_comment_keywords_unresolved_even_when_all_other_subfields_resolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(
            caption="标题", hashtags="#tag", comment_cta="cta"
        ),
    )
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert comment["status_code"] == STATUS_UNRESOLVED


# 7. Per-subfield unresolved fallback is independent — never panel-wide.
def test_per_subfield_unresolved_fallback_does_not_replace_resolved_subfields():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(caption="标题文案", hashtags="", comment_cta=""),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    cta = _subfield(bundle, SUBFIELD_CTA)
    comment = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)
    assert title["status_code"] == STATUS_RESOLVED and title["value"] == "标题文案"
    assert hashtags["status_code"] == STATUS_UNRESOLVED
    assert cta["status_code"] == STATUS_UNRESOLVED
    assert comment["status_code"] == STATUS_UNRESOLVED


def test_unresolved_count_when_only_caption_resolves():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(caption="标题"),
    )
    # title resolved, hashtags/cta/comment_keywords unresolved → 3.
    assert bundle["unresolved_count"] == 3
    assert bundle["tracked_gap_summary_zh"] != ""
    assert "panel-wide" in bundle["tracked_gap_summary_zh"]
    assert "编辑期 hint" in bundle["tracked_gap_summary_zh"]


def test_unresolved_count_three_when_only_three_resolve_due_to_comment_keywords_gap():
    """All three publish-hub copy_bundle producers populated; only
    ``comment_keywords`` remains structurally UNRESOLVED."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(
            caption="标题", hashtags="#tag", comment_cta="评论 CTA"
        ),
    )
    assert bundle["unresolved_count"] == 1
    assert bundle["tracked_gap_summary_zh"] != ""


def test_unresolved_count_four_when_all_subfields_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(),
    )
    assert bundle["unresolved_count"] == 4
    assert bundle["tracked_gap_summary_zh"] != ""


# 8. Forbidden token scrub (validator R3).
@pytest.mark.parametrize("token", FORBIDDEN_TOKEN_FRAGMENTS)
def test_forbidden_token_in_caption_renders_unresolved(token):
    """Blocker 1 invariant + Blocker 1 corollary: when the only
    authoritative source is scrubbed, the subfield falls back to
    UNRESOLVED rather than synthesizing from the entry payload."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(topic="安全主题"),
        base_copy_bundle=_base_copy_bundle(caption=f"poison {token} value"),
    )
    title = _subfield(bundle, SUBFIELD_TITLE)
    # Caption scrubbed, no entry-hint fallback → UNRESOLVED.
    assert title["status_code"] == STATUS_UNRESOLVED
    assert title["value"] == ""


def test_forbidden_token_in_hashtags_renders_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(hashtags="#vendor_x #ok"),
    )
    hashtags = _subfield(bundle, SUBFIELD_HASHTAGS)
    assert hashtags["status_code"] == STATUS_UNRESOLVED
    assert hashtags["value"] == ""


def test_forbidden_token_in_comment_cta_renders_cta_unresolved():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(comment_cta="provider_x app cta"),
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
            caption="标题", hashtags="#tag", comment_cta="评论 CTA"
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


# 11. Closed-shape invariants.
def test_each_subfield_carries_closed_keys_only():
    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
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
        _matrix_script_task(),
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


# 12. Blocker 1 — adjacent task-entry hints alone produce ALL UNRESOLVED.
def test_adjacent_entry_hints_alone_produce_all_unresolved_subfields():
    """Even when every entry hint is populated (topic, target_platform,
    audience_hint, tone_hint) but the publish-hub copy_bundle is empty,
    every subfield renders UNRESOLVED. Adjacent entry hints are NOT
    copy truth and MUST NOT be a fallback source."""

    task_with_full_entry = _matrix_script_task(
        topic="国货高端面霜矩阵",
        target_platform="douyin",
        audience_hint="26-35 都市女性",
        tone_hint="理性 · 信赖",
    )
    bundle = derive_matrix_script_delivery_copy_bundle(
        task_with_full_entry,
        base_copy_bundle=_base_copy_bundle(),  # all empty
    )
    for sub in bundle["subfields"]:
        assert sub["status_code"] == STATUS_UNRESOLVED, sub
        assert sub["value"] == ""
    assert bundle["unresolved_count"] == 4


@pytest.mark.parametrize(
    "hint_field,hint_value",
    [
        ("topic", "国货高端面霜矩阵"),
        ("target_platform", "douyin"),
        ("audience_hint", "26-35 都市女性"),
        ("tone_hint", "理性 · 信赖"),
        ("length_hint", "30-45s"),
    ],
)
def test_individual_entry_hint_does_not_resolve_any_subfield(hint_field, hint_value):
    """Each entry hint, alone, must not flip any subfield to RESOLVED."""

    task = {"task_id": "t", "kind": "matrix_script", "config": {"entry": {hint_field: hint_value}}}
    bundle = derive_matrix_script_delivery_copy_bundle(
        task, base_copy_bundle=_base_copy_bundle()
    )
    for sub in bundle["subfields"]:
        assert sub["status_code"] == STATUS_UNRESOLVED, (hint_field, sub)


def test_blocker_1_explanations_explicitly_name_hint_prohibition():
    """The CTA + comment_keywords UNRESOLVED explanations must explicitly
    name the prohibition on synthesizing from entry hints — so a future
    reader can trace the Blocker 1 discipline from the rendered card."""

    bundle = derive_matrix_script_delivery_copy_bundle(
        _matrix_script_task(),
        base_copy_bundle=_base_copy_bundle(),
    )
    cta_explanation = _subfield(bundle, SUBFIELD_CTA)["unresolved_explanation_zh"]
    comment_explanation = _subfield(bundle, SUBFIELD_COMMENT_KEYWORDS)["unresolved_explanation_zh"]
    # CTA explanation calls out target_platform / audience_hint / tone_hint as
    # explicitly forbidden synthesis sources.
    assert "target_platform" in cta_explanation
    assert "audience_hint" in cta_explanation
    assert "tone_hint" in cta_explanation
    assert "不应" in cta_explanation
    # comment_keywords explanation calls out audience_hint / tone_hint.
    assert "audience_hint" in comment_explanation
    assert "tone_hint" in comment_explanation
    assert "不应" in comment_explanation
