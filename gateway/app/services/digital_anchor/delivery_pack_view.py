"""Digital Anchor Delivery Pack assembly view (OWC-DA PR-3 / DA-W8).

Pure presentation-layer projection over the contract-frozen Phase C
delivery binding ``digital_anchor_delivery_binding_v1`` (defined in
:mod:`gateway.app.services.digital_anchor.delivery_binding`). Surfaces
the nine standard Delivery Pack lanes enumerated by
``docs/product/digital_anchor_product_flow_v1.md`` §7.1:

- ``final_video``  (主交付; primary)
- ``subtitle``
- ``dubbed_audio``
- ``metadata``
- ``manifest``
- ``pack``
- ``role_usage``
- ``scene_usage``
- ``language_usage``

The OWC-DA gate spec §3 DA-W8 binds this slice to "render existing
``delivery_binding_v1`` rows as a Delivery Pack with ``final_video``
primary + ``subtitle`` / ``dubbed_audio`` / ``metadata`` / ``manifest`` /
``pack`` / ``role_usage`` / ``scene_usage`` / ``language_usage`` lanes
per §7.1. Pure projection-side; no schema widening." This module honors
that contract verbatim:

- All reads pass through the closed projection emitted by
  ``project_delivery_binding(packet)`` plus ``task["config"]["entry"]``
  (the closed eleven-field create-entry contract).
- ``final_video`` is rendered as a primacy lane with a tracked-gap
  explanation. The current Phase C delivery binding does not enumerate
  a row for ``final_video`` per se — the final composed asset surfaces
  through ``media.final_video_url`` on the publish-hub payload (the
  unified ``publish_readiness`` producer is the future cross-row
  convergence point per Recovery PR-1).
- ``subtitle`` / ``dubbed_audio`` / ``pack`` map directly to the
  existing ``delivery_pack.deliverables`` rows (kinds:
  ``subtitle_bundle`` / ``audio_bundle`` / ``scene_pack``). Their
  ``required`` flag is rendered as-is from ``capability_plan``.
- ``metadata`` reads from the existing ``metadata_projection`` block.
- ``manifest`` reads from the existing ``manifest`` block.
- ``role_usage`` reads from
  ``result_packet_binding.role_segment_bindings`` aggregated per role.
- ``scene_usage`` reads from ``entry.scene_binding_hint`` and is
  rendered as an explicit tracked-gap when absent (per the OWC-DA gate
  spec §3 wording "missing subfields must be operator-language tracked
  gaps, not synthesized values").
- ``language_usage`` reads from ``entry.language_scope`` (source +
  target language) cross-joined with per-segment ``language_pick``.

Hard discipline (binding under OWC-DA gate spec §4):

- No Digital Anchor packet truth mutation (§4.1).
- No closed-enum widening on contracts; all reads are over already-
  emitted projection fields (§4.1).
- No second authoritative producer for publishability or
  ``final_provenance``; the projection does not re-derive
  ``publishable`` (§4.1).
- No invented values; absent subfields render as operator-language
  tracked-gap sentinels with a closed status code.
- No Hot Follow / Matrix Script file touched (§4.2). Non-Digital-Anchor
  callers receive ``{}``.
- No avatar platform / role catalog / scene catalog UI (§4.4).
- No provider / model / vendor / engine identifier admitted into any
  field (§4.4 + validator R3).
- No new endpoint; no new contract; no schema widening.

Consumed only by
``gateway/app/services/task_view_helpers.py::publish_hub_payload``
inside the existing ``kind_value == "digital_anchor"`` branch via the
attach seam ``publish_hub_pr3_attach.attach_digital_anchor_delivery_pr3_extras``.
Hot Follow / Matrix Script / Baseline publish hubs never receive the
bundle.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# ─────────────────────────────────────────────────────────────────────
# Closed lane identifiers (operator-readable rendering keys).
# ─────────────────────────────────────────────────────────────────────
LANE_FINAL_VIDEO = "final_video"
LANE_SUBTITLE = "subtitle"
LANE_DUBBED_AUDIO = "dubbed_audio"
LANE_METADATA = "metadata"
LANE_MANIFEST = "manifest"
LANE_PACK = "pack"
LANE_ROLE_USAGE = "role_usage"
LANE_SCENE_USAGE = "scene_usage"
LANE_LANGUAGE_USAGE = "language_usage"

LANE_ORDER = (
    LANE_FINAL_VIDEO,
    LANE_SUBTITLE,
    LANE_DUBBED_AUDIO,
    LANE_METADATA,
    LANE_MANIFEST,
    LANE_PACK,
    LANE_ROLE_USAGE,
    LANE_SCENE_USAGE,
    LANE_LANGUAGE_USAGE,
)

LANE_LABELS_ZH = {
    LANE_FINAL_VIDEO: "最终视频 · final_video（主交付）",
    LANE_SUBTITLE: "字幕（subtitle）",
    LANE_DUBBED_AUDIO: "配音（dubbed_audio）",
    LANE_METADATA: "元数据（metadata）",
    LANE_MANIFEST: "交付清单（manifest）",
    LANE_PACK: "交付包（pack）",
    LANE_ROLE_USAGE: "角色使用记录（role_usage）",
    LANE_SCENE_USAGE: "场景使用记录（scene_usage）",
    LANE_LANGUAGE_USAGE: "语言使用记录（language_usage）",
}

# Closed status codes for per-lane resolution.
STATUS_RESOLVED = "resolved_from_delivery_binding"
STATUS_TRACKED_GAP = "tracked_gap_pending_publish_readiness"
STATUS_TRACKED_GAP_SCENE = "tracked_gap_scene_binding_hint_absent"
STATUS_TRACKED_GAP_LANGUAGE = "tracked_gap_language_scope_absent"
STATUS_TRACKED_GAP_ROLES = "tracked_gap_role_segment_bindings_empty"

STATUS_LABELS_ZH = {
    STATUS_RESOLVED: "已从 delivery_binding 解析",
    STATUS_TRACKED_GAP: "尚未解析（待统一 publish_readiness 上线）",
    STATUS_TRACKED_GAP_SCENE: "尚未解析（entry.scene_binding_hint 未提交）",
    STATUS_TRACKED_GAP_LANGUAGE: "尚未解析（entry.language_scope 未提交）",
    STATUS_TRACKED_GAP_ROLES: "尚未解析（role / segment 绑定为空）",
}

# Closed deliverable-kind labels for the structured pack row.
DELIVERABLE_KIND_LABELS_ZH = {
    "role_manifest": "角色清单（role_manifest）",
    "speaker_segment_bundle": "段落配音绑定（speaker_segment_bundle）",
    "subtitle_bundle": "字幕包（subtitle_bundle）",
    "audio_bundle": "音频包（audio_bundle）",
    "lip_sync_bundle": "对口型包（lip_sync_bundle）",
    "scene_pack": "场景包（scene_pack）",
}

# Closed framing-kind labels for role_usage rendering.
ROLE_FRAMING_LABELS_ZH = {
    "head": "头肩（head）",
    "half_body": "半身（half_body）",
    "full_body": "全身（full_body）",
}

# Forbidden token fragments (validator R3 + design-handoff red line 6)
# scrubbed defensively against accidental upstream leakage.
FORBIDDEN_TOKEN_FRAGMENTS = ("vendor", "model_id", "provider", "engine")


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _strip_or_empty(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _scrub_forbidden(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower()
    for token in FORBIDDEN_TOKEN_FRAGMENTS:
        if token in lowered:
            return ""
    return text


def _is_digital_anchor_binding(delivery_binding: Mapping[str, Any]) -> bool:
    surface = _strip_or_empty(delivery_binding.get("surface"))
    line_id = _strip_or_empty(delivery_binding.get("line_id")).lower()
    return (
        surface == "digital_anchor_delivery_binding_v1"
        or line_id == "digital_anchor"
    )


def _deliverable_by_kind(
    deliverables: Iterable[Mapping[str, Any]], kind: str
) -> Mapping[str, Any]:
    for row in deliverables:
        if isinstance(row, Mapping) and row.get("kind") == kind:
            return row
    return {}


def _build_final_video_lane() -> dict[str, Any]:
    """Render final_video as a primacy lane with a tracked-gap sentinel.

    The Phase C delivery binding does not enumerate a row for the
    composed final asset; the final asset reaches the publish hub via
    ``media.final_video_url`` and will be cross-row collapsed by the
    unified ``publish_readiness`` producer. DA-W8 names final_video as
    the **primary** Delivery Pack lane without inventing a contract row.
    """
    return {
        "lane_id": LANE_FINAL_VIDEO,
        "label_zh": LANE_LABELS_ZH[LANE_FINAL_VIDEO],
        "is_primary": True,
        "status_code": STATUS_TRACKED_GAP,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP],
        "value": "",
        "value_source_id": None,
        "primacy_explanation_zh": (
            "final_video 是发布对象的主体；当前 Phase C delivery binding 仍按结构化 "
            "deliverable 行投射（subtitle_bundle / audio_bundle / lip_sync_bundle / "
            "scene_pack 等），final_video 的可发布性由统一 publish_readiness 上线后跨行收敛。"
        ),
        "tracked_gap_explanation_zh": (
            "final_video 当前不是 delivery_binding 的独立行；DA-W8 仅以 primacy lane "
            "在交付包中突出展示，不在此处合成 url。"
        ),
    }


def _build_capability_lane(
    *,
    lane_id: str,
    deliverable: Mapping[str, Any],
) -> dict[str, Any]:
    """Render a structural deliverable row (subtitle / dubbed_audio / pack)."""
    if not deliverable:
        return {
            "lane_id": lane_id,
            "label_zh": LANE_LABELS_ZH[lane_id],
            "status_code": STATUS_TRACKED_GAP,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP],
            "deliverable_id": "",
            "deliverable_kind": "",
            "deliverable_kind_label_zh": "",
            "required": False,
            "artifact_lookup": None,
            "value_source_id": None,
        }
    deliverable_id = _strip_or_empty(deliverable.get("deliverable_id"))
    kind = _strip_or_empty(deliverable.get("kind"))
    return {
        "lane_id": lane_id,
        "label_zh": LANE_LABELS_ZH[lane_id],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "deliverable_id": deliverable_id,
        "deliverable_kind": kind,
        "deliverable_kind_label_zh": DELIVERABLE_KIND_LABELS_ZH.get(kind, kind),
        "required": bool(deliverable.get("required", False)),
        "artifact_lookup": deliverable.get("artifact_lookup"),
        "value_source_id": (
            "delivery_binding_v1.delivery_pack.deliverables[kind="
            + kind
            + "]"
            if kind
            else None
        ),
    }


def _build_metadata_lane(metadata_projection: Mapping[str, Any]) -> dict[str, Any]:
    """Render metadata projection. The metadata block always exists."""
    metadata = _safe_mapping(metadata_projection.get("metadata"))
    notes = _scrub_forbidden(_strip_or_empty(metadata.get("notes")))
    if not metadata:
        return {
            "lane_id": LANE_METADATA,
            "label_zh": LANE_LABELS_ZH[LANE_METADATA],
            "status_code": STATUS_TRACKED_GAP,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP],
            "line_id": "",
            "packet_version": "",
            "notes": "",
            "display_only": True,
            "value_source_id": None,
        }
    return {
        "lane_id": LANE_METADATA,
        "label_zh": LANE_LABELS_ZH[LANE_METADATA],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "line_id": _strip_or_empty(metadata_projection.get("line_id")),
        "packet_version": _strip_or_empty(metadata_projection.get("packet_version")),
        "notes": notes,
        "display_only": bool(metadata_projection.get("display_only", True)),
        "value_source_id": "delivery_binding_v1.metadata_projection",
    }


def _build_manifest_lane(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Render the manifest block as a Delivery Pack 交付证据 lane."""
    if not manifest:
        return {
            "lane_id": LANE_MANIFEST,
            "label_zh": LANE_LABELS_ZH[LANE_MANIFEST],
            "status_code": STATUS_TRACKED_GAP,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP],
            "manifest_id": "",
            "deliverable_profile_ref": "",
            "asset_sink_profile_ref": "",
            "packet_ready_state": "",
            "validator_report_path": "",
            "write_policy": "",
            "value_source_id": None,
        }
    return {
        "lane_id": LANE_MANIFEST,
        "label_zh": LANE_LABELS_ZH[LANE_MANIFEST],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "manifest_id": _strip_or_empty(manifest.get("manifest_id")),
        "deliverable_profile_ref": _strip_or_empty(
            manifest.get("deliverable_profile_ref")
        ),
        "asset_sink_profile_ref": _strip_or_empty(
            manifest.get("asset_sink_profile_ref")
        ),
        "packet_ready_state": _strip_or_empty(manifest.get("packet_ready_state")),
        "validator_report_path": _strip_or_empty(manifest.get("validator_report_path")),
        "write_policy": _strip_or_empty(manifest.get("write_policy")),
        "value_source_id": "delivery_binding_v1.manifest",
    }


def _build_role_usage_lane(
    role_segment_bindings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate role_segment_bindings rows into per-role usage entries."""
    bindings = [b for b in role_segment_bindings if isinstance(b, Mapping)]
    if not bindings:
        return {
            "lane_id": LANE_ROLE_USAGE,
            "label_zh": LANE_LABELS_ZH[LANE_ROLE_USAGE],
            "status_code": STATUS_TRACKED_GAP_ROLES,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP_ROLES],
            "roles": [],
            "role_count": 0,
            "value_source_id": None,
        }
    roles_by_id: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        role_id = _strip_or_empty(binding.get("role_id"))
        if not role_id:
            continue
        framing = _strip_or_empty(binding.get("role_framing_kind"))
        existing = roles_by_id.get(role_id)
        if existing is None:
            roles_by_id[role_id] = {
                "role_id": role_id,
                "role_display_name": _strip_or_empty(
                    binding.get("role_display_name")
                ),
                "role_framing_kind": framing,
                "role_framing_label_zh": ROLE_FRAMING_LABELS_ZH.get(framing, framing),
                "appearance_ref": _strip_or_empty(binding.get("appearance_ref")),
                "segment_ids": [_strip_or_empty(binding.get("segment_id"))],
            }
        else:
            seg_id = _strip_or_empty(binding.get("segment_id"))
            if seg_id and seg_id not in existing["segment_ids"]:
                existing["segment_ids"].append(seg_id)
    role_rows = list(roles_by_id.values())
    role_rows.sort(key=lambda r: r["role_id"])
    return {
        "lane_id": LANE_ROLE_USAGE,
        "label_zh": LANE_LABELS_ZH[LANE_ROLE_USAGE],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "roles": role_rows,
        "role_count": len(role_rows),
        "value_source_id": (
            "delivery_binding_v1.result_packet_binding.role_segment_bindings"
        ),
    }


def _build_scene_usage_lane(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Render scene_usage from entry.scene_binding_hint with tracked-gap fallback."""
    scene_hint = _scrub_forbidden(_strip_or_empty(entry.get("scene_binding_hint")))
    if not scene_hint:
        return {
            "lane_id": LANE_SCENE_USAGE,
            "label_zh": LANE_LABELS_ZH[LANE_SCENE_USAGE],
            "status_code": STATUS_TRACKED_GAP_SCENE,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP_SCENE],
            "scene_binding_hint": "",
            "value_source_id": None,
            "tracked_gap_explanation_zh": (
                "operator 在 entry 阶段未提交 scene_binding_hint；DA-W8 仅展示 placeholder。"
                "未来 Scene Plan Contract 落地后会跨行收敛 scene_template_ref。"
            ),
        }
    return {
        "lane_id": LANE_SCENE_USAGE,
        "label_zh": LANE_LABELS_ZH[LANE_SCENE_USAGE],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "scene_binding_hint": scene_hint,
        "value_source_id": "task.config.entry.scene_binding_hint",
    }


def _build_language_usage_lane(
    entry: Mapping[str, Any],
    role_segment_bindings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Render language_usage from entry.language_scope + segment language_pick."""
    language_scope = _safe_mapping(entry.get("language_scope"))
    source_language = _strip_or_empty(language_scope.get("source_language"))
    target_raw = language_scope.get("target_language")
    if isinstance(target_raw, list):
        target_languages = [
            _strip_or_empty(item) for item in target_raw if _strip_or_empty(item)
        ]
    elif isinstance(target_raw, str) and target_raw:
        target_languages = [_strip_or_empty(target_raw)]
    else:
        target_languages = []

    segment_picks: dict[str, list[str]] = {}
    for binding in role_segment_bindings:
        if not isinstance(binding, Mapping):
            continue
        pick = _strip_or_empty(binding.get("language_pick"))
        seg_id = _strip_or_empty(binding.get("segment_id"))
        if not pick or not seg_id:
            continue
        segment_picks.setdefault(pick, []).append(seg_id)

    if not source_language and not target_languages and not segment_picks:
        return {
            "lane_id": LANE_LANGUAGE_USAGE,
            "label_zh": LANE_LABELS_ZH[LANE_LANGUAGE_USAGE],
            "status_code": STATUS_TRACKED_GAP_LANGUAGE,
            "status_label_zh": STATUS_LABELS_ZH[STATUS_TRACKED_GAP_LANGUAGE],
            "source_language": "",
            "target_languages": [],
            "language_rows": [],
            "value_source_id": None,
        }

    # Codex P2 (PR #135 review at delivery_pack_view.py:447-453): the
    # language_usage lane MUST keep ``source_language`` operator-visible
    # in the rendered union, even when it is not among ``target_languages``
    # and not present in ``segment_picks`` (e.g. source ``en-US`` with
    # target-only ``zh-CN``). Otherwise the Delivery Pack language panel
    # is incomplete on a real entry and operators see a misleading
    # coverage view. Read-only over the existing entry / delivery-binding
    # substrate; no new truth is synthesised — the source_language value
    # was already projected at the lane level above, this just keeps it
    # in the per-language row union.
    union_languages: list[str] = []
    if source_language and source_language not in union_languages:
        union_languages.append(source_language)
    for lang in target_languages:
        if lang and lang not in union_languages:
            union_languages.append(lang)
    for lang in segment_picks:
        if lang and lang not in union_languages:
            union_languages.append(lang)

    rows: list[dict[str, Any]] = []
    for lang in union_languages:
        seg_ids = segment_picks.get(lang, [])
        rows.append(
            {
                "language": lang,
                "is_source_language": lang == source_language,
                "is_target_language": lang in target_languages,
                "segment_count": len(seg_ids),
                "segment_ids": seg_ids,
            }
        )

    return {
        "lane_id": LANE_LANGUAGE_USAGE,
        "label_zh": LANE_LABELS_ZH[LANE_LANGUAGE_USAGE],
        "status_code": STATUS_RESOLVED,
        "status_label_zh": STATUS_LABELS_ZH[STATUS_RESOLVED],
        "source_language": source_language,
        "target_languages": target_languages,
        "language_rows": rows,
        "value_source_id": (
            "task.config.entry.language_scope + "
            "delivery_binding_v1.result_packet_binding.role_segment_bindings"
        ),
    }


def derive_digital_anchor_delivery_pack(
    *,
    delivery_binding: Mapping[str, Any] | None,
    task: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Delivery Pack assembly view bundle.

    Inputs:

    - ``delivery_binding`` — the ``digital_anchor_delivery_binding_v1``
      projection emitted by ``project_delivery_binding(packet)``.
    - ``task`` — the task mapping carrying ``config.entry`` (the closed
      eleven-field create-entry contract).

    Returns ``{}`` for non-Digital-Anchor inputs / empty inputs so the
    caller can attach the result without further gating.

    Returns the closed comprehension shape:

    .. code-block:: python

        {
            "is_digital_anchor": True,
            "panel_title_zh": "Digital Anchor · 交付中心 · Delivery Pack",
            "panel_subtitle_zh": "...",
            "lane_legend_zh": ["最终视频", "字幕", ...],
            "lanes": {
                "final_video": {...},
                "subtitle": {...},
                "dubbed_audio": {...},
                "metadata": {...},
                "manifest": {...},
                "pack": {...},
                "role_usage": {...},
                "scene_usage": {...},
                "language_usage": {...},
            },
            "lane_order": [...],
            "tracked_gap_summary_zh": "...",
        }
    """
    binding = _safe_mapping(delivery_binding)
    if not binding or not _is_digital_anchor_binding(binding):
        return {}
    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))

    delivery_pack = _safe_mapping(binding.get("delivery_pack"))
    deliverables = _safe_list(delivery_pack.get("deliverables"))
    metadata_projection = _safe_mapping(binding.get("metadata_projection"))
    manifest = _safe_mapping(binding.get("manifest"))
    result_packet_binding = _safe_mapping(binding.get("result_packet_binding"))
    role_segment_bindings = _safe_list(
        result_packet_binding.get("role_segment_bindings")
    )

    lanes = {
        LANE_FINAL_VIDEO: _build_final_video_lane(),
        LANE_SUBTITLE: _build_capability_lane(
            lane_id=LANE_SUBTITLE,
            deliverable=_deliverable_by_kind(deliverables, "subtitle_bundle"),
        ),
        LANE_DUBBED_AUDIO: _build_capability_lane(
            lane_id=LANE_DUBBED_AUDIO,
            deliverable=_deliverable_by_kind(deliverables, "audio_bundle"),
        ),
        LANE_METADATA: _build_metadata_lane(metadata_projection),
        LANE_MANIFEST: _build_manifest_lane(manifest),
        LANE_PACK: _build_capability_lane(
            lane_id=LANE_PACK,
            deliverable=_deliverable_by_kind(deliverables, "scene_pack"),
        ),
        LANE_ROLE_USAGE: _build_role_usage_lane(role_segment_bindings),
        LANE_SCENE_USAGE: _build_scene_usage_lane(entry),
        LANE_LANGUAGE_USAGE: _build_language_usage_lane(entry, role_segment_bindings),
    }

    tracked_gap_lane_ids = sorted(
        lane["lane_id"]
        for lane in lanes.values()
        if str(lane.get("status_code") or "").startswith("tracked_gap")
    )
    tracked_gap_summary_zh = (
        "以下 lane 仍为 tracked_gap，等待统一 publish_readiness 上线 / "
        "scene_binding_hint 提交 / language_scope 提交 / role-segment 绑定填充："
        + "、".join(tracked_gap_lane_ids)
        if tracked_gap_lane_ids
        else "全部 lane 已从 delivery_binding / entry 解析完毕。"
    )

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Digital Anchor · 交付中心 · Delivery Pack",
        "panel_subtitle_zh": (
            "按 product-flow §7.1 的九项 Delivery Pack lane 投射；只读理解层，"
            "不发明事实，不改 delivery_binding 契约，不引入 vendor / model / provider / engine 控件。"
        ),
        "lane_legend_zh": [LANE_LABELS_ZH[lid] for lid in LANE_ORDER],
        "lanes": lanes,
        "lane_order": list(LANE_ORDER),
        "tracked_gap_summary_zh": tracked_gap_summary_zh,
    }


__all__ = [
    "DELIVERABLE_KIND_LABELS_ZH",
    "LANE_DUBBED_AUDIO",
    "LANE_FINAL_VIDEO",
    "LANE_LABELS_ZH",
    "LANE_LANGUAGE_USAGE",
    "LANE_MANIFEST",
    "LANE_METADATA",
    "LANE_ORDER",
    "LANE_PACK",
    "LANE_ROLE_USAGE",
    "LANE_SCENE_USAGE",
    "LANE_SUBTITLE",
    "ROLE_FRAMING_LABELS_ZH",
    "STATUS_LABELS_ZH",
    "STATUS_RESOLVED",
    "STATUS_TRACKED_GAP",
    "STATUS_TRACKED_GAP_LANGUAGE",
    "STATUS_TRACKED_GAP_ROLES",
    "STATUS_TRACKED_GAP_SCENE",
    "derive_digital_anchor_delivery_pack",
]
