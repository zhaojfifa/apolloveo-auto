"""Matrix Script Result-Capability Recovery — RC PR-1 helper (RC-R6).

Pure operator-language projection over already-existing truth that
restates the Matrix Script Task Area card and Workbench summary header
as one of two operator statements:

- ``ready: do X next`` — operator can act now; the helper provides the
  concrete next action.
- ``blocked: missing Y`` — the surface names exactly what is missing
  before the next action can happen.

Authority: ``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R6 + §5 RC PR-1 slice.

Hard discipline (binding per recovery amendment §7 + recovery gate spec §4):

- No new contract / schema / closed-enum widening. The helper consumes
  ``board_bucket`` + ``head_reason`` + the existing eight-stage state
  + the existing publish_readiness producer's output verbatim.
- No second authoritative truth source. Recommended-version reasoning
  remains in :mod:`derive_matrix_script_full_card_summary` /
  :mod:`qc_diagnostics_view`; this module only restates already-decided
  state.
- No fake ``final_video``. Where the underlying state would have shown
  an artifact gap, this helper renders a tracked-gap-shaped operator
  statement; it never synthesises a placeholder URL.
- Hot Follow / Digital Anchor / baseline rows MUST NOT receive any
  result-status object — the public helpers return ``{}`` for non-MS
  rows / non-MS panels so the caller's gating preserves bytewise-
  unchanged surfaces.
- Read-only over closure. The Task Area helper does NOT lazy-create
  the in-process closure store; it accepts ``closure`` as kwarg or
  resolves it through the existing read-only closure binding view.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .closure_binding import get_closure_view_for_task
from .qc_diagnostics_view import HEAD_REASON_LABELS_ZH
from .task_area_convergence import (
    STAGE_ARCHIVED,
    STAGE_AWAITING_REVIEW,
    STAGE_BACKFILLED,
    STAGE_CREATED,
    STAGE_FINAL_READY,
    STAGE_GENERATING,
    STAGE_PENDING_CONFIG,
    STAGE_PUBLISHABLE,
    derive_matrix_script_eight_stage_state,
)

# RC-R6 status_kind closed-enum. The two operator-visible buckets are
# ``ready`` and ``blocked``; ``completed`` covers archived / backfilled
# closeout states that no longer require operator action but should not
# be misread as "blocked: missing Y".
STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"
STATUS_COMPLETED = "completed"

STATUS_KINDS = (STATUS_READY, STATUS_BLOCKED, STATUS_COMPLETED)

STATUS_LABELS_ZH: dict[str, str] = {
    STATUS_READY: "就绪",
    STATUS_BLOCKED: "阻塞",
    STATUS_COMPLETED: "已完成",
}

# Per-stage operator-language framing. Each entry returns the binary
# RC-R6 statement plus a concrete next-action sentence and an explicit
# missing-items list. The strings are operator-language only; no
# vendor / model / provider / engine identifiers ever leak through.
STAGE_TO_RESULT: dict[str, dict[str, Any]] = {
    STAGE_PUBLISHABLE: {
        "status_kind": STATUS_READY,
        "headline_zh": "可发布 · 前往交付中心发布",
        "next_action_zh": "在交付中心选择渠道与账号完成发布。",
        "missing_items": [],
    },
    STAGE_FINAL_READY: {
        "status_kind": STATUS_READY,
        "headline_zh": "成片完成 · 进入工作台 D 校对",
        "next_action_zh": "在工作台 D 校对区完成字幕 / 配音 / 文案 / CTA 复核后，再回到交付中心发布。",
        "missing_items": [],
    },
    STAGE_AWAITING_REVIEW: {
        "status_kind": STATUS_BLOCKED,
        "headline_zh": "待校对 · 等待成片产出",
        "next_action_zh": "成片尚未生成，请等待 compose 完成后再进入校对区。",
        "missing_items": ["final_video_pending"],
    },
    STAGE_GENERATING: {
        "status_kind": STATUS_BLOCKED,
        "headline_zh": "生成中 · 等待 compose 完成",
        "next_action_zh": "生成任务进行中，待 compose 完成后系统会自动推进到待校对。",
        "missing_items": ["compose_in_progress"],
    },
    STAGE_PENDING_CONFIG: {
        "status_kind": STATUS_BLOCKED,
        "headline_zh": "待配置 · 缺少变体配置",
        "next_action_zh": "前往工作台完成 Phase B 选型（tone / audience / length 三轴 × 变体目标数），再触发生成。",
        "missing_items": ["variation_cells_empty"],
    },
    STAGE_CREATED: {
        "status_kind": STATUS_BLOCKED,
        "headline_zh": "已创建 · 待配置脚本与变体",
        "next_action_zh": "进入工作台确认脚本结构并完成变体配置。",
        "missing_items": ["script_structure_pending", "variation_cells_empty"],
    },
    STAGE_BACKFILLED: {
        "status_kind": STATUS_COMPLETED,
        "headline_zh": "已回填 · 进入下一轮迭代或归档",
        "next_action_zh": "已有发布回填记录；可在 Delivery Center 复盘指标，或进入下一轮变体迭代。",
        "missing_items": [],
    },
    STAGE_ARCHIVED: {
        "status_kind": STATUS_COMPLETED,
        "headline_zh": "已归档 · 无后续动作",
        "next_action_zh": "任务已归档，无需进一步操作。",
        "missing_items": [],
    },
}

# Workbench summary headline phrasing for the head_reason closed enum.
# The Workbench helper does NOT have access to row truth (the wiring
# layer builds the bundle from packet view + publish_readiness); it
# therefore frames the summary directly off the unified producer's
# `publishable` boolean + `head_reason` rather than the eight-stage
# state. This keeps the producer single-source.
WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH: dict[str, str] = {
    "publishable_ok": "前往 Delivery Center 选择渠道与账号完成发布。",
    "ready_gate_blocking": "ready gate 仍在阻塞，请按下方阻塞建议先解除前置项。",
    "publish_not_ready": "发布前置项尚未满足，请检查必交付物与发布配置。",
    "compose_not_ready": "合成前置项未就绪，请等待生成或前往 Workbench 处理阻塞。",
    "final_missing": "成片缺失，等待生成产出后再进入校对。",
    "final_stale": "当前成片已过期，需要重新生成最新版本。",
    "final_provenance_historical": "当前 provenance 仍为历史尝试，需要推进到当前 attempt。",
    "required_deliverable_missing": "存在缺失的必交付物，需补齐后才可发布。",
    "required_deliverable_blocking": "存在阻塞发布的必交付物，需先解除阻塞。",
    "unresolved": "状态尚未解析，刷新或检查上游 provenance 后重试。",
}


def _is_matrix_script_row(row: Mapping[str, Any]) -> bool:
    if not isinstance(row, Mapping):
        return False
    kind = str(row.get("kind") or row.get("category_key") or "").strip().lower()
    return kind == "matrix_script"


def _is_matrix_script_panel(panel: Mapping[str, Any]) -> bool:
    if not isinstance(panel, Mapping):
        return False
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _head_reason_label(head_reason: Any) -> str:
    if head_reason is None:
        return "—"
    label = HEAD_REASON_LABELS_ZH.get(str(head_reason))
    return label or str(head_reason)


def derive_matrix_script_task_area_result_status(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the RC-R6 Task Area card result-oriented status block.

    Returns one of:

    - ``{}`` for non-Matrix-Script rows (caller's gate keeps surface
      bytewise unchanged).
    - ``{"is_matrix_script": True, "status_kind", "status_label_zh",
      "headline_zh", "next_action_zh", "missing_items": [...],
      "head_reason", "head_reason_label_zh", "stage", "stage_label_zh"}``
      for Matrix Script rows.

    The helper restates already-decided state — it does not introduce a
    new authority on publishability or recommended version. The
    eight-stage state is the carrier; ``head_reason`` is surfaced
    verbatim so the operator can correlate the card status with the
    Workbench summary and the Workbench E diagnostics row.
    """
    if not _is_matrix_script_row(row):
        return {}

    eight_stage = derive_matrix_script_eight_stage_state(row, closure=closure)
    stage = str(eight_stage.get("stage") or "").strip()
    if stage not in STAGE_TO_RESULT:
        # Defensive: if the upstream stage projector returns an unknown
        # stage, render the safest blocked statement.
        stage = STAGE_CREATED
    framing = STAGE_TO_RESULT[stage]

    head_reason = row.get("head_reason")
    head_reason_label = _head_reason_label(head_reason)

    return {
        "is_matrix_script": True,
        "status_kind": framing["status_kind"],
        "status_label_zh": STATUS_LABELS_ZH[framing["status_kind"]],
        "headline_zh": framing["headline_zh"],
        "next_action_zh": framing["next_action_zh"],
        "missing_items": list(framing["missing_items"]),
        "head_reason": head_reason,
        "head_reason_label_zh": head_reason_label,
        "stage": stage,
        "stage_label_zh": eight_stage.get("stage_label") or "—",
    }


def derive_matrix_script_task_area_result_status_for_task(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Convenience wrapper that resolves the closure read-only by task_id.

    Mirrors :func:`task_area_convergence.derive_matrix_script_full_card_summary_for_task`
    so the presenter can call this helper without threading the closure
    view itself.
    """
    if not _is_matrix_script_row(row):
        return {}
    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    closure = get_closure_view_for_task(task_id) if task_id else None
    return derive_matrix_script_task_area_result_status(row, closure=closure)


def derive_matrix_script_workbench_result_summary(
    publish_readiness: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the RC-R6 Workbench summary header.

    Returns ``{}`` when the panel is not Matrix Script; the wiring
    caller can attach the result without further gating.

    The helper consumes the same unified ``publish_readiness`` producer
    output that ``qc_diagnostics_view`` reads; it does NOT create a
    second producer. ``head_reason`` is surfaced verbatim and the next
    action is a one-line operator-language sentence keyed off the
    closed ``head_reason`` enum. Unknown enum values fall back to the
    head_reason string + a generic "请联系架构师确认状态语义" prompt
    so future enum additions degrade gracefully without silent skips.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script_panel(panel):
        return {}

    pr = _safe_mapping(publish_readiness)
    publishable = bool(pr.get("publishable"))
    head_reason = pr.get("head_reason")
    head_reason_label = _head_reason_label(head_reason)

    inputs = _safe_mapping(pr.get("consumed_inputs"))
    blocking_count = int(inputs.get("blocking_count") or 0)

    if publishable:
        status_kind = STATUS_READY
        headline_zh = "可发布 · 前往交付中心发布"
        next_action_zh = WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH.get(
            "publishable_ok",
            "前往 Delivery Center 选择渠道与账号完成发布。",
        )
        missing_items: list[str] = []
    elif head_reason is None:
        # Producer returned no head_reason and not publishable — this
        # is the "ready bucket" case (per task_router_presenters
        # `board_bucket` derivation: `ready` when publishable is False
        # but head_reason is also empty). Operator action is to author
        # / configure variants; we name it as a blocked state and the
        # missing item is the variant configuration prerequisite.
        status_kind = STATUS_BLOCKED
        headline_zh = "阻塞 · 待配置变体"
        next_action_zh = "先在工作台完成 Phase B 选型，待生成产出后再进入校对。"
        missing_items = ["variation_cells_empty"]
    else:
        status_kind = STATUS_BLOCKED
        headline_zh = f"阻塞 · {head_reason_label}"
        next_action_zh = WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH.get(
            str(head_reason),
            "请联系架构师确认状态语义后再决定下一步。",
        )
        missing_items = [str(head_reason)]

    blocking_advisories = _safe_list(pr.get("blocking_advisories"))

    return {
        "is_matrix_script": True,
        "status_kind": status_kind,
        "status_label_zh": STATUS_LABELS_ZH[status_kind],
        "headline_zh": headline_zh,
        "next_action_zh": next_action_zh,
        "missing_items": missing_items,
        "head_reason": head_reason,
        "head_reason_label_zh": head_reason_label,
        "publishable": publishable,
        "blocking_count": blocking_count,
        "blocking_advisory_count": len(blocking_advisories),
    }


__all__ = [
    "STATUS_BLOCKED",
    "STATUS_COMPLETED",
    "STATUS_KINDS",
    "STATUS_LABELS_ZH",
    "STATUS_READY",
    "STAGE_TO_RESULT",
    "WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH",
    "derive_matrix_script_task_area_result_status",
    "derive_matrix_script_task_area_result_status_for_task",
    "derive_matrix_script_workbench_result_summary",
]
