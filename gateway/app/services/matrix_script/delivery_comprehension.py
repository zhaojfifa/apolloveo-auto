"""Matrix Script Delivery Center comprehension projection (PR-U3).

Pure presentation-layer projection over the existing
``project_delivery_binding(packet)`` output (the
``matrix_script_delivery_binding_v1`` projection in
``gateway/app/services/matrix_script/delivery_binding.py``). Reads only
fields already projected by that contract surface; emits operator-language
comprehension strings for the Matrix Script Delivery Center per the
user-mandated PR-U3 narrowing of the signed gate spec at
``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``:

- ``final_video`` is highlighted as the **primary** deliverable —
  conceptually distinct from the structural deliverables that the
  delivery binding enumerates today (``variation_manifest`` /
  ``slot_bundle`` / ``subtitle_bundle`` / ``audio_preview`` /
  ``scene_pack``). In the current Plan E phase, the line emits a
  derived/composed final per task; this projection surfaces that
  primacy at the comprehension layer without inventing a contract field
  on the per-deliverable rows.
- ``required_deliverables`` vs ``scene_pack``-style derivatives are
  visibly zoned per the Plan C amendment to
  ``factory_delivery_contract_v1.md`` §"Per-Deliverable Required /
  Blocking Fields" + the §"Scene-Pack Non-Blocking Rule" that pins
  ``matrix_script_scene_pack`` to ``required=False, blocking_publish=False``
  independent of the per-task ``pack`` capability.
- Publish-blocking is explained in operator language for the closed
  enumerated reasons emitted by the projection (``required`` /
  ``blocking_publish`` per row + ``artifact_lookup`` sentinel
  ``artifact_lookup_unresolved``).
- Historical-success vs current-attempt artifacts are kept as separate
  comprehension lanes — never collapsed into a single "exists" boolean.
  This mirrors the existing ``provenance`` and ``freshness`` fields on
  the contract-pinned ``ArtifactHandle`` shape.

Hard discipline (binding under gate spec §4):

- No projection mutation; no packet write-back; no contract mutation.
- No D1 unified ``publish_readiness`` producer; no D2 L3
  ``final_provenance`` emitter; no D3 panel dispatch contract object
  conversion; no D4 L4 advisory producer / emitter.
- No Hot Follow Delivery Center change; no Digital Anchor Delivery Center
  change. Bundle returns ``{}`` for non-Matrix-Script delivery bindings.
- No provider / model / vendor / engine identifier in the return value
  (validator R3).
- No new ``deliverable_id`` enumerated; no ``required`` / ``blocking_publish``
  field re-shape; no row added to or removed from the underlying
  delivery binding.

Consumed only by ``gateway/app/services/task_view_helpers.py::publish_hub_payload``
when ``task.kind == "matrix_script"``. Hot Follow / Digital Anchor /
Baseline publish hubs never receive the comprehension bundle.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# The Matrix Script delivery binding emits a closed five-row deliverable
# set per `gateway/app/services/matrix_script/delivery_binding.py`. The
# kind-to-zone mapping below is read-only translation — no new contract.
DELIVERABLE_KIND_LABELS_ZH = {
    "variation_manifest": "变体清单",
    "script_slot_bundle": "脚本 slot 包",
    "subtitle_bundle": "字幕包",
    "audio_preview": "音频预览",
    "scene_pack": "配套素材包（场景）",
}

# Operator-language zoning per (required, blocking_publish) tuple.
# This is the operator-readable rendering of the Plan C amendment fields;
# no new contract field is introduced.
def _zoning_label_zh(*, required: bool, blocking_publish: bool) -> str:
    if required and blocking_publish:
        return "必交付 · 阻塞发布"
    if required and not blocking_publish:
        return "必交付 · 不阻塞发布"
    if not required and blocking_publish:
        # Defensive — should not occur because `_clamp_blocking_publish`
        # in the binding enforces the validator invariant
        # `required=false ⇒ blocking_publish=false`. Render verbatim so
        # any future violation is visibly flagged.
        return "可选 · 但被标记为阻塞（请检查契约不变式）"
    return "可选 · 不阻塞发布"


# Operator-language interpretation of the `artifact_lookup` sentinel +
# real ArtifactHandle states. Reads only fields already on the contract.
def _artifact_status_label_zh(artifact_lookup: Any) -> dict[str, str]:
    """Return `{status_code, status_label_zh, status_explanation_zh}`.

    Codes:
    - ``unresolved``: the contract sentinel ``artifact_lookup_unresolved``
      (PR-1 retired ``not_implemented_phase_c`` to this code).
    - ``current_fresh``: ArtifactHandle with ``freshness == "fresh"``.
    - ``historical``: ArtifactHandle with ``freshness == "historical"``
      or with a non-empty ``provenance.attempt_id`` that differs from
      the current attempt — the comprehension layer keeps the historical
      lane visibly separate from the current lane.
    - ``unknown``: anything else (degrade gracefully).
    """
    if artifact_lookup == "artifact_lookup_unresolved" or artifact_lookup is None:
        return {
            "status_code": "unresolved",
            "status_label_zh": "尚未解析",
            "status_explanation_zh": "未在 L2 找到匹配工件；统一 publish_readiness 上线后会自动解析。",
        }
    if isinstance(artifact_lookup, Mapping):
        freshness = str(artifact_lookup.get("freshness") or "").strip().lower()
        provenance = artifact_lookup.get("provenance")
        if freshness == "fresh":
            return {
                "status_code": "current_fresh",
                "status_label_zh": "当前 · 最新",
                "status_explanation_zh": "当前尝试的产出，可发布。",
            }
        if freshness == "historical":
            return {
                "status_code": "historical",
                "status_label_zh": "历史成功 · 非当前",
                "status_explanation_zh": "历史尝试的成功产出，与当前尝试分开展示，不会折叠为同一含义。",
            }
        if isinstance(provenance, Mapping) and provenance.get("attempt_id"):
            return {
                "status_code": "historical",
                "status_label_zh": "历史成功 · 非当前",
                "status_explanation_zh": "历史尝试的成功产出，与当前尝试分开展示，不会折叠为同一含义。",
            }
    return {
        "status_code": "unknown",
        "status_label_zh": "—",
        "status_explanation_zh": "状态未知；请查看上游 artifact_lookup 投射。",
    }


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _is_matrix_script_binding(delivery_binding: Mapping[str, Any]) -> bool:
    surface = str(delivery_binding.get("surface") or "").strip()
    line_id = str(delivery_binding.get("line_id") or "").strip().lower()
    return surface == "matrix_script_delivery_binding_v1" or line_id == "matrix_script"


def _classify_deliverables(
    deliverables: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group rows into operator-readable lanes:

    - ``required_blocking``: required AND blocking_publish — these gate publish
    - ``required_non_blocking``: required AND NOT blocking_publish (rare)
    - ``optional_non_blocking``: not required (e.g. ``scene_pack``)
    """
    lanes: dict[str, list[dict[str, Any]]] = {
        "required_blocking": [],
        "required_non_blocking": [],
        "optional_non_blocking": [],
    }
    for row in deliverables:
        if not isinstance(row, Mapping):
            continue
        required = bool(row.get("required"))
        blocking = bool(row.get("blocking_publish"))
        kind = str(row.get("kind") or "")
        artifact_status = _artifact_status_label_zh(row.get("artifact_lookup"))
        enriched = {
            "deliverable_id": str(row.get("deliverable_id") or ""),
            "kind": kind,
            "kind_label_zh": DELIVERABLE_KIND_LABELS_ZH.get(kind, kind),
            "required": required,
            "blocking_publish": blocking,
            "zoning_label_zh": _zoning_label_zh(required=required, blocking_publish=blocking),
            "artifact_status_code": artifact_status["status_code"],
            "artifact_status_label_zh": artifact_status["status_label_zh"],
            "artifact_status_explanation_zh": artifact_status["status_explanation_zh"],
        }
        if required and blocking:
            lanes["required_blocking"].append(enriched)
        elif required and not blocking:
            lanes["required_non_blocking"].append(enriched)
        else:
            lanes["optional_non_blocking"].append(enriched)
    return lanes


def _publish_blocking_explanation_zh(lanes: Mapping[str, list[Mapping[str, Any]]]) -> dict[str, Any]:
    """Compute operator-language publish-blocking explanation.

    Reads only the already-classified `required_blocking` lane: a publish is
    blocked iff any required+blocking row has an unresolved or non-current
    artifact. Returns `{is_blocked, reason_label_zh, blocking_rows[]}`.
    """
    blocking_rows: list[dict[str, str]] = []
    for row in lanes.get("required_blocking", []):
        if row.get("artifact_status_code") not in ("current_fresh",):
            blocking_rows.append(
                {
                    "deliverable_id": row.get("deliverable_id", ""),
                    "kind_label_zh": row.get("kind_label_zh", ""),
                    "artifact_status_label_zh": row.get("artifact_status_label_zh", ""),
                }
            )
    if blocking_rows:
        return {
            "is_blocked": True,
            "reason_label_zh": "以下必交付物尚未达到当前可发布状态，发布按钮应保持禁用。",
            "blocking_rows": blocking_rows,
        }
    return {
        "is_blocked": False,
        "reason_label_zh": "所有必交付物均已就绪，发布按钮可启用。",
        "blocking_rows": [],
    }


def derive_matrix_script_delivery_comprehension(
    delivery_binding: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Matrix Script Delivery Center comprehension bundle.

    Input: the ``matrix_script_delivery_binding_v1`` projection emitted by
    ``project_delivery_binding(packet)``. Returns ``{}`` for non-Matrix
    Script bindings or empty input so the caller can attach the result
    without further gating.
    """
    binding = _safe_mapping(delivery_binding)
    if not binding or not _is_matrix_script_binding(binding):
        return {}

    delivery_pack = _safe_mapping(binding.get("delivery_pack"))
    deliverables = _safe_list(delivery_pack.get("deliverables"))
    lanes = _classify_deliverables(deliverables)
    blocking = _publish_blocking_explanation_zh(lanes)

    # final_video primacy block. The current Matrix Script delivery
    # binding does not enumerate a row for `final_video` per se — the
    # final composed asset is currently produced/inferred at compose time
    # and surfaces through `media.final_video_url` on the publish hub
    # payload. The comprehension projection names final_video as the
    # PRIMARY operator-visible deliverable so the Delivery Center
    # template can render it with visual primacy WITHOUT inventing a
    # new contract row on the binding.
    final_video_primary = {
        "is_primary": True,
        "title_zh": "最终视频 · final_video",
        "subtitle_zh": "本任务的核心交付，单独突出展示；其余结构化交付物按必交付/可选分区。",
        "primacy_explanation_zh": (
            "final_video 是发布对象的主体；当前 Plan E 阶段的 delivery binding 仍按 "
            "结构化 deliverable 行投射（variation_manifest / slot_bundle / subtitle_bundle / "
            "audio_preview / scene_pack），final_video 的可发布性由统一 publish_readiness "
            "上线后跨行收敛。"
        ),
    }

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Matrix Script · 交付中心理解",
        "panel_subtitle_zh": (
            "只读理解层；不发明事实，不改契约，不引入 vendor / model / provider / engine 控件。"
        ),
        "final_video_primary": final_video_primary,
        "lanes_label_zh": "交付分区",
        "lanes": {
            "required_blocking": {
                "lane_label_zh": "必交付 · 阻塞发布",
                "lane_explanation_zh": "这些产物缺失 / 非当前 → 发布按钮保持禁用。",
                "rows": lanes["required_blocking"],
                "row_count": len(lanes["required_blocking"]),
            },
            "required_non_blocking": {
                "lane_label_zh": "必交付 · 不阻塞发布",
                "lane_explanation_zh": "必须产出，但缺失时不阻塞发布；记录在档以便后续补齐。",
                "rows": lanes["required_non_blocking"],
                "row_count": len(lanes["required_non_blocking"]),
            },
            "optional_non_blocking": {
                "lane_label_zh": "可选 · 不阻塞发布",
                "lane_explanation_zh": (
                    "scene_pack / 配套素材类衍生品，按 §\"Scene-Pack Non-Blocking Rule\" 始终非阻塞。"
                ),
                "rows": lanes["optional_non_blocking"],
                "row_count": len(lanes["optional_non_blocking"]),
            },
        },
        "publish_blocking_explanation_label_zh": "发布阻塞解释",
        "publish_blocking_explanation": blocking,
        "history_vs_current_label_zh": "历史成功 vs 当前尝试",
        "history_vs_current_explanation_zh": (
            "每行的 artifact_status 严格区分『当前 · 最新』与『历史成功 · 非当前』，"
            "不会把两者折叠为单一 exists 布尔。统一 publish_readiness 上线后将进一步收敛。"
        ),
    }


__all__ = [
    "DELIVERABLE_KIND_LABELS_ZH",
    "derive_matrix_script_delivery_comprehension",
]
