"""Matrix Script Delivery Center — copy_bundle exposure (OWC-MS PR-3 / MS-W7).

Pure presentation-layer projection over the existing authoritative copy
truth that already reaches the publish-hub payload. Surfaces the four
operator-language fields enumerated by
``docs/product/matrix_script_product_flow_v1.md`` §7.1 标准交付物:

- 标题 (title)
- hashtags
- CTA
- 评论关键词 (comment_keywords)

The OWC-MS gate spec §3 MS-W7 binds this slice to "render `copy_bundle`
(标题 / hashtags / CTA / 评论关键词) as a Delivery Center row backed by
existing `variation_manifest.copy` projection. If the field is not
projection-ready, mark as a tracked gap; do NOT add packet truth in
this wave."

Authoritative copy truth (binding):

The Delivery Center MAY ONLY consume the existing publish-hub
``copy_bundle`` projection emitted by
``gateway/app/services/task_view_helpers.py::_build_copy_bundle(task)``.
That projection is the **single producer** of operator-facing publish
copy in the repo today. Adjacent task-entry hints (``topic`` /
``target_platform`` / ``audience_hint`` / ``tone_hint`` /
``length_hint``) are NOT copy truth — they are Phase A authoring hints
that drive Phase B variation cells, not publish copy. Synthesizing CTA /
评论关键词 / any copy_bundle subfield from those hints would make this
helper a **second copy producer**, which violates gate spec §4.1 ("no
second authoritative producer") and the OWC-MS PR-3 reviewer-fail
correction (Blocker 1 — 2026-05-05).

Each subfield therefore has exactly one authorized source:

- ``title`` → ``base_copy_bundle.caption``
- ``hashtags`` → ``base_copy_bundle.hashtags``
- ``cta`` → ``base_copy_bundle.comment_cta`` (the Hot Follow-shaped
  ``_build_copy_bundle`` emits the CTA line as ``comment_cta``; in the
  Matrix Script Delivery Center surface this label is rendered as 评论
  CTA, with the operator-language tracked-gap label naming the gap
  toward a Matrix-Script-native CTA copy field.)
- ``comment_keywords`` → no authoritative producer today; ALWAYS rendered
  as the closed ``STATUS_UNRESOLVED`` tracked gap.

When the authoritative source is empty (or scrubbed for forbidden
tokens), the subfield falls back to the closed ``STATUS_UNRESOLVED``
sentinel with operator-language explanation citing the future copy
projection contract. The fallback is per-subfield, never panel-wide
(§8.1.1 PR-2 reviewer-fail correction precedent — per-field unresolved
fallback, never panel-wide replacement).

Hard discipline (binding under OWC-MS gate spec §4 + PR-3 §1
reviewer-fail correction Blocker 1):

- No Matrix Script packet truth mutation (§4.1).
- No widening of ``target_language`` / canonical axes / accepted-scheme
  set / closure enums (§4.1).
- **No second authoritative producer for publish copy** (§4.1 +
  Blocker 1 correction). Adjacent entry hints
  (``target_platform`` / ``audience_hint`` / ``tone_hint``) are NOT
  consumed; they are not copy truth.
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
# Each explanation names the gating future contract so reviewers can
# trace the gap to its product-flow / contract anchor without inferring
# the source of truth from adjacent task-entry hints.
UNRESOLVED_EXPLANATIONS_ZH: dict[str, str] = {
    SUBFIELD_TITLE: (
        "当前 publish-hub copy_bundle 不携带 caption；标题暂以 — 占位。"
        "未来 copy 投射契约（matrix_script_product_flow §7.1 + §9.5 Deliverable Contract）"
        "上线后将由 variation_manifest 衍生 publish 标题。"
    ),
    SUBFIELD_HASHTAGS: (
        "当前 publish-hub copy_bundle 不携带 hashtags；先以 — 占位。"
        "未来 copy 投射契约上线后将由 slot_pack / variation_manifest 衍生 hashtags。"
    ),
    SUBFIELD_CTA: (
        "当前 publish-hub copy_bundle 不携带 CTA 文案（comment_cta 字段为空）；"
        "先以 — 占位。CTA 不应从 entry.target_platform / audience_hint / tone_hint "
        "等编辑期 hint 合成，那些不是 publish 文案真值。未来 copy 投射契约上线后由 "
        "variation_manifest 的 publish CTA 字段衍生。"
    ),
    SUBFIELD_COMMENT_KEYWORDS: (
        "当前 publish-hub copy_bundle 不存在评论关键词字段；先以 — 占位。"
        "评论关键词不应从 audience_hint / tone_hint 等编辑期 hint 合成，那些不是 "
        "评论关键词真值。未来 copy 投射契约上线后由 slot_pack 评论关键词聚合衍生。"
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


# ─────────────────────────────────────────────────────────────────────
# Per-subfield resolvers — each subfield has EXACTLY ONE authoritative
# source. Adjacent task-entry hints are NOT consumed (Blocker 1 / 2026-05-05).
# ─────────────────────────────────────────────────────────────────────


def _derive_title(base_copy_bundle: Mapping[str, Any]) -> tuple[str, Optional[str]]:
    caption = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("caption")))
    if caption:
        return caption, "delivery_copy_bundle_caption"
    return "", None


def _derive_hashtags(
    base_copy_bundle: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    hashtags = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("hashtags")))
    if hashtags:
        return hashtags, "delivery_copy_bundle_hashtags"
    return "", None


def _derive_cta(
    base_copy_bundle: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    cta = _scrub_forbidden(_strip_or_empty(base_copy_bundle.get("comment_cta")))
    if cta:
        return cta, "delivery_copy_bundle_comment_cta"
    return "", None


def _derive_comment_keywords() -> tuple[str, Optional[str]]:
    """Comment keywords have no authoritative producer in the publish-hub
    ``copy_bundle`` shape today (no ``comment_keywords`` field exists).
    Always render the tracked gap. The future copy projection contract
    will land the field as part of the broader Matrix Script Delivery
    Contract (product-flow §9.5).
    """

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
      ``category_key`` / ``platform``); otherwise returns ``{}``. The task
      is used **only** for the matrix_script kind check; subfield values
      are NEVER read from the task's ``config.entry`` payload (per
      Blocker 1 — adjacent entry hints are not copy truth).
    - ``base_copy_bundle`` — the existing publish-hub
      ``_build_copy_bundle(task)`` output, the **single authoritative
      copy producer**. Defaults to ``{}``.

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

    base_bundle = _safe_mapping(base_copy_bundle)

    title_value, title_source = _derive_title(base_bundle)
    hashtags_value, hashtags_source = _derive_hashtags(base_bundle)
    cta_value, cta_source = _derive_cta(base_bundle)
    comment_value, comment_source = _derive_comment_keywords()

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
            "CTA / 评论关键词）；只读理解层，仅消费已有 publish-hub copy_bundle 投射，"
            "不作为第二条 copy 真值路径。"
        ),
        "subfields": subfields,
        "unresolved_count": unresolved_count,
    }

    if unresolved_count:
        bundle["tracked_gap_summary_zh"] = (
            f"当前共 {unresolved_count} 项 copy_bundle 字段尚未投射，已按子字段单独标注 "
            "状态；不会以 panel-wide 占位替换已解析字段，亦不会从编辑期 hint 合成 "
            "copy 真值。"
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
