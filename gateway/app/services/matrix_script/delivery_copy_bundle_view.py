"""Matrix Script Delivery Center — copy_bundle exposure (OWC-MS PR-3 / MS-W7).

Pure presentation-layer projection over the existing Matrix Script truth
that already reaches the publish-hub payload. Surfaces the four
operator-language fields enumerated by ``docs/product/matrix_script_product_flow_v1.md``
§7.1 标准交付物:

- 标题 (title)
- hashtags
- CTA
- 评论关键词 (comment_keywords)

The OWC-MS gate spec §3 MS-W7 binds this slice to "render `copy_bundle`
(标题 / hashtags / CTA / 评论关键词) as a Delivery Center row backed by
existing `variation_manifest.copy` projection. If the field is not
projection-ready, mark as a tracked gap; do NOT add packet truth in
this wave." This module honors that contract verbatim:

- Each subfield is sourced from existing closed truth (entry payload +
  the publish-hub `_build_copy_bundle(task)` projection that has shipped
  on `gateway/app/services/task_view_helpers.py` since pre-OWC). When the
  source carries a non-empty value, the subfield carries
  ``STATUS_RESOLVED`` + the value verbatim.
- When the specific source is empty, the subfield falls back to the
  closed ``STATUS_UNRESOLVED`` sentinel — operator-language explanation
  names the gating future contract (Outline Contract per product-flow
  §9.2 for 标题; future copy_pack contract for hashtags / 评论关键词).
  The fallback is per-subfield and never panel-wide (§8.1.1 PR-2
  reviewer-fail correction precedent: per-field unresolved fallback,
  never panel-wide replacement).
- No new packet field, no schema widening, no contract authoring. The
  Delivery Center copy_bundle is a presentation row, not a truth source.

Hard discipline (binding under OWC-MS gate spec §4):

- No Matrix Script packet truth mutation (§4.1).
- No widening of ``target_language`` / canonical axes / accepted-scheme
  set / closure enums (§4.1).
- No second authoritative producer for publishability / final_provenance
  / advisories (§4.1).
- No Hot Follow / Digital Anchor file touched (§4.2). Non-matrix_script
  callers receive ``{}``.
- No cross-cutting wiring change outside the existing
  ``kind == "matrix_script"`` branch in
  ``task_view_helpers.publish_hub_payload`` (§4.2).
- No provider / model / vendor / engine identifier admitted into any
  field (§4.4 + validator R3).
- No new endpoint; no new contract; no new ``panel_kind``.
- Output is a deep-copy-safe primitive bundle so the caller can attach
  it to the JSON response without further deep-copying.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

# ─────────────────────────────────────────────────────────────────────
# Closed subfield identifiers (operator-readable rendering keys).
# ─────────────────────────────────────────────────────────────────────
SUBFIELD_TITLE = "title"
SUBFIELD_HASHTAGS = "hashtags"
SUBFIELD_CTA = "cta"
SUBFIELD_COMMENT_KEYWORDS = "comment_keywords"

SUBFIELD_LABELS_ZH = {
    SUBFIELD_TITLE: "标题",
    SUBFIELD_HASHTAGS: "Hashtags",
    SUBFIELD_CTA: "CTA",
    SUBFIELD_COMMENT_KEYWORDS: "评论关键词",
}

# Closed status codes per subfield. Values mirror the MS-W3 read-view's
# STATUS_RESOLVED / STATUS_UNRESOLVED discipline: a per-subfield label
# tells the operator whether the value reflects current truth or whether
# the future contract gap has not yet been closed.
STATUS_RESOLVED = "resolved_from_existing_projection"
STATUS_UNRESOLVED = "unresolved_pending_copy_projection_contract"

STATUS_LABELS_ZH = {
    STATUS_RESOLVED: "已从现有投射解析",
    STATUS_UNRESOLVED: "尚未投射 · 待 copy 投射契约上线",
}

# Operator-language explanation strings per subfield's unresolved gating.
# Authority pointers for each gating are encoded in the explanation so a
# reviewer reading the rendered card can trace the gap to its anchor.
UNRESOLVED_EXPLANATIONS_ZH: dict[str, str] = {
    SUBFIELD_TITLE: (
        "当前 entry 未提供 topic；标题暂以 — 占位。"
        "未来 Outline Contract（product-flow §9.2）上线后将由结构化 hook + topic 衍生。"
    ),
    SUBFIELD_HASHTAGS: (
        "当前 task 投射的 copy_bundle 不携带 hashtags；先以 — 占位。"
        "未来 copy 投射契约上线后将由 slot_pack / variation_manifest 衍生 hashtags。"
    ),
    SUBFIELD_CTA: (
        "当前 entry 未提供 target_platform；CTA 暂以 — 占位。"
        "Phase A 入口要求 target_platform 必填，正常路径下不应触发此分支。"
    ),
    SUBFIELD_COMMENT_KEYWORDS: (
        "当前 task 投射的 copy_bundle 不携带 comment_cta；先以 — 占位。"
        "未来 copy 投射契约上线后将由 slot_pack 关键词聚合衍生评论关键词。"
    ),
}

# Forbidden token fragments scrubbed from any rendered subfield value to
# defend against accidental leakage (validator R3 + design-handoff red
# line 6). Mirrors the MS-W3 / MS-W6 forbidden token policy. Matched
# case-insensitively as substrings.
FORBIDDEN_TOKEN_FRAGMENTS = ("vendor", "model_id", "provider", "engine")


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strip_or_empty(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _scrub_forbidden(text: str) -> str:
    """Return ``text`` if no forbidden fragment is detected, else ``""``.

    Defensive: matches the operator-visible-surface §2.5 red lines so a
    helper that accidentally pulls a vendor/model identifier through an
    upstream projection still emits an empty (and therefore unresolved)
    subfield instead of leaking the identifier to the operator.
    """

    if not text:
        return ""
    lowered = text.lower()
    for token in FORBIDDEN_TOKEN_FRAGMENTS:
        if token in lowered:
            return ""
    return text


def _is_matrix_script_task(task: Mapping[str, Any]) -> bool:
    if not isinstance(task, Mapping):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return True
    return False


def _entry_payload(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the closed Matrix Script entry payload from the task config."""

    config = task.get("config")
    if not isinstance(config, Mapping):
        return {}
    entry = config.get("entry")
    return entry if isinstance(entry, Mapping) else {}


def _derive_title(
    entry: Mapping[str, Any], base_copy_bundle: Mapping[str, Any]
) -> tuple[str, Optional[str]]:
    """Operator-language title.

    Order of precedence (read-only over existing closed truth):

    1. ``base_copy_bundle.caption`` if non-empty (the existing publish-hub
       projection already builds caption from `mm.txt` / task title).
    2. ``entry.topic`` (closed Phase A field — operator-supplied content
       that maps to "主题/目标" per product-flow §5.3).
    3. ``""`` (triggers per-subfield unresolved fallback).
    """

    caption = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("caption")))
    if caption:
        return caption, "delivery_copy_bundle_caption"

    topic = _scrub_forbidden(_strip_or_empty(entry.get("topic")))
    if topic:
        # Title is the operator-readable rendering of topic; product-flow
        # §5.3 task-card field "主题 / 目标". Hint annotations such as
        # tone_hint / audience_hint are NOT concatenated here — those
        # are properly the Hook section of the Outline Contract, not the
        # Delivery Center title.
        return topic, "matrix_script_entry_topic"
    return "", None


def _derive_hashtags(
    base_copy_bundle: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    """Operator-language hashtags.

    Sources, in order:

    1. ``base_copy_bundle.hashtags`` if non-empty.
    2. Empty (unresolved fallback).
    """

    hashtags = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("hashtags")))
    if hashtags:
        return hashtags, "delivery_copy_bundle_hashtags"
    return "", None


def _derive_cta(
    entry: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    """Operator-language CTA.

    Source: ``entry.target_platform`` per the MS-W3 read-view precedent
    (PR-2 derived CTA from `entry.target_platform`). Operator-language
    rendering is "在 ``<target_platform>`` 完成发布并引导互动 / 评论 /
    私信。" so the operator sees a real call-to-action, not just a
    bare platform identifier.
    """

    platform = _scrub_forbidden(_strip_or_empty(entry.get("target_platform")))
    if platform:
        cta_text = (
            f"在 {platform} 完成发布并引导互动 / 评论 / 私信"
            "（请按平台规范替换为账号级 CTA 文案）"
        )
        return cta_text, "matrix_script_entry_target_platform"
    return "", None


def _derive_comment_keywords(
    base_copy_bundle: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    """Operator-language comment_keywords.

    Sources, in order:

    1. ``base_copy_bundle.comment_cta`` if non-empty (the publish-hub
       projection's pre-existing field; semantically the same shape as
       evaluated comment-keyword guidance).
    2. ``entry.audience_hint`` + ``entry.tone_hint`` joined when both are
       non-empty (operator-readable audience-and-tone hint that doubles
       as a comment-keyword seed; never minted as a value of its own).
    3. Empty (unresolved fallback).
    """

    comment_cta = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("comment_cta")))
    if comment_cta:
        return comment_cta, "delivery_copy_bundle_comment_cta"

    audience = _scrub_forbidden(_strip_or_empty(entry.get("audience_hint")))
    tone = _scrub_forbidden(_strip_or_empty(entry.get("tone_hint")))
    if audience and tone:
        return f"{audience} · {tone}", "matrix_script_entry_audience_tone_hint"
    if audience:
        return audience, "matrix_script_entry_audience_hint"
    if tone:
        return tone, "matrix_script_entry_tone_hint"
    return "", None


def _subfield(
    *,
    subfield_id: str,
    value: str,
    source_id: Optional[str],
) -> dict[str, Any]:
    """Build a closed-shape subfield row.

    Closed keys: ``subfield_id`` / ``label_zh`` / ``status_code`` /
    ``status_label_zh`` / ``value`` / ``value_source_id`` /
    ``unresolved_explanation_zh``. Reviewers walking ENGINEERING_RULES §13
    product-flow module presence can read the four subfields off the
    rendered Delivery Center card.
    """

    if value:
        return {
            "subfield_id": subfield_id,
            "label_zh": SUBFIELD_LABELS_ZH[subfield_id],
            "status_code": STATUS_RESOLVED,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
            "value": value,
            "value_source_id": source_id,
            "unresolved_explanation_zh": "",
        }
    return {
        "subfield_id": subfield_id,
        "label_zh": SUBFIELD_LABELS_ZH[subfield_id],
        "status_code": STATUS_UNRESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_UNRESOLVED],
        "value": "",
        "value_source_id": None,
        "unresolved_explanation_zh": UNRESOLVED_EXPLANATIONS_ZH[subfield_id],
    }


def derive_matrix_script_delivery_copy_bundle(
    task: Mapping[str, Any] | None,
    *,
    base_copy_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project the Matrix Script Delivery Center copy_bundle exposure.

    Inputs:

    - ``task`` — the in-memory task dict reaching ``publish_hub_payload``.
      Must carry ``kind == "matrix_script"`` (or equivalent under
      ``category_key`` / ``platform``); otherwise returns ``{}``.
    - ``base_copy_bundle`` — the existing publish-hub
      ``_build_copy_bundle(task)`` output, passed in by the wiring layer
      so we re-use its caption / hashtags / comment_cta projection
      without re-implementing it. Defaults to ``{}``.

    Returns the closed comprehension shape:

    .. code-block:: python

        {
            "is_matrix_script": True,
            "panel_title_zh": "Matrix Script · 交付中心 · copy_bundle",
            "panel_subtitle_zh": "...",
            "subfields": [
                {"subfield_id": "title", "label_zh": "标题", "status_code": ..., "value": ..., ...},
                {"subfield_id": "hashtags", ...},
                {"subfield_id": "cta", ...},
                {"subfield_id": "comment_keywords", ...},
            ],
            "tracked_gap_summary_zh": "...",  # only when at least one subfield is unresolved
        }

    For non-matrix_script tasks, returns ``{}``.
    """

    if not _is_matrix_script_task(_safe_mapping(task)):
        return {}

    entry = _entry_payload(_safe_mapping(task))
    base_bundle = _safe_mapping(base_copy_bundle)

    title_value, title_source = _derive_title(entry, base_bundle)
    hashtags_value, hashtags_source = _derive_hashtags(base_bundle)
    cta_value, cta_source = _derive_cta(entry)
    comment_value, comment_source = _derive_comment_keywords(base_bundle, entry)

    subfields = [
        _subfield(
            subfield_id=SUBFIELD_TITLE, value=title_value, source_id=title_source
        ),
        _subfield(
            subfield_id=SUBFIELD_HASHTAGS,
            value=hashtags_value,
            source_id=hashtags_source,
        ),
        _subfield(
            subfield_id=SUBFIELD_CTA, value=cta_value, source_id=cta_source
        ),
        _subfield(
            subfield_id=SUBFIELD_COMMENT_KEYWORDS,
            value=comment_value,
            source_id=comment_source,
        ),
    ]

    unresolved_count = sum(
        1 for sub in subfields if sub["status_code"] == STATUS_UNRESOLVED
    )

    bundle: dict[str, Any] = {
        "is_matrix_script": True,
        "panel_title_zh": "Matrix Script · 交付中心 · copy_bundle",
        "panel_subtitle_zh": (
            "按 product-flow §7.1 的标准交付物投射四项 operator 文案字段（标题 / hashtags / "
            "CTA / 评论关键词）；只读理解层，不发明事实，不改契约。"
        ),
        "subfields": subfields,
        "unresolved_count": unresolved_count,
    }

    if unresolved_count:
        bundle["tracked_gap_summary_zh"] = (
            f"当前共 {unresolved_count} 项 copy_bundle 字段尚未投射，已按子字段单独标注 "
            "状态；不会以 panel-wide 占位替换已解析字段。"
        )
    else:
        bundle["tracked_gap_summary_zh"] = ""

    return bundle


__all__ = [
    "FORBIDDEN_TOKEN_FRAGMENTS",
    "STATUS_LABELS_ZH",
    "STATUS_RESOLVED",
    "STATUS_UNRESOLVED",
    "SUBFIELD_CTA",
    "SUBFIELD_COMMENT_KEYWORDS",
    "SUBFIELD_HASHTAGS",
    "SUBFIELD_LABELS_ZH",
    "SUBFIELD_TITLE",
    "UNRESOLVED_EXPLANATIONS_ZH",
    "derive_matrix_script_delivery_copy_bundle",
]
