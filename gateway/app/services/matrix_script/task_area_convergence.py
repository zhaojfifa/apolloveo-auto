"""Matrix Script Task Area workflow convergence projection (OWC-MS PR-1).

Pure operator-language projection over the existing task row + closure
view. Implements the OWC-MS PR-1 scope from
``docs/reviews/owc_ms_gate_spec_v1.md`` §3:

- **MS-W1 — Task Area three-tier projection**. Renders the existing
  Matrix Script packet + variation cells + closure publish events as a
  logical *脚本任务 → 变体任务 → 发布任务* lane view. Pure projection
  over existing truth; no schema change; no packet mutation.
- **MS-W2 — Task Area state vocabulary + 8-field card**. Projects the
  existing four-layer state (L1 step status / L2 artifact facts / L3
  current attempt / L4 ready gate) into the eight operator-language
  stages (``已创建 / 待配置 / 生成中 / 待校对 / 成片完成 / 可发布 /
  已回填 / 已归档``); renders the eight task-card fields (主题 / 核心脚本
  名称 / 当前变体数 / 可发布版本数 / 已发布账号数 / 当前最佳版本 / 最近
  一次生成时间 / 当前阻塞项).

Hard discipline (binding per OWC-MS gate spec §4):

- Reads only existing row truth + the read-only closure view from
  ``gateway.app.services.matrix_script.closure_binding.get_closure_view_for_task``.
- The closure read uses ``get_closure_view_for_task`` (read-only) and
  NEVER calls ``get_or_create_for_task`` — task area projection must
  not lazily mutate the in-process closure store.
- No packet mutation; no projection mutation; no closure write-back.
- No contract-shape change; ``review_zone`` enum and other OWC-MS
  PR-2 / PR-3 surfaces are explicitly out of scope.
- The "publishable variation count" reads ``variation_feedback[]``
  rows whose ``publish_status == "published"`` (Plan D.0 closure shape
  field, frozen in
  ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``).
  When no closure exists yet the count is 0.
- The "published channel count" reads distinct ``platform`` values
  from ``variation_feedback[].channel_metrics[]``. The channel metrics
  shape is the Phase D.0 contract; ``platform`` is bound by closed
  taxonomy already enforced at ``apply_event``.
- "当前最佳版本" stays ``None`` in OWC-MS PR-1 — operator best-version
  selection lands in OWC-MS PR-2 (workbench D 校对区 with the additive
  ``review_zone`` enum on ``operator_note`` events). The template
  renders ``None`` as ``—`` with an operator-language tooltip.
- No provider / model / vendor / engine identifier ever appears in the
  return value (validator R3 + sanitization at the operator boundary).
- Hot Follow rows / Digital Anchor rows / baseline rows MUST NOT
  receive any of the OWC-MS surface objects produced by this module
  (the helper returns the empty dict for non-matrix_script rows so the
  caller's gating preserves their bytewise-unchanged Task Area
  rendering).
- Composes ``derive_matrix_script_task_card_summary`` (PR-U1) verbatim
  — every existing PR-U1 output key is preserved on the result so the
  template's PR-U1 spans render unchanged.

Authority pointers:

- ``docs/product/matrix_script_product_flow_v1.md`` §§5.1 / 5.2 / 5.3
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 (MS-W1 + MS-W2)
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
- ``ENGINEERING_RULES.md`` §13 Product-Flow Module Presence
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .closure_binding import get_closure_view_for_task
from .task_card_summary import (
    MATRIX_SCRIPT_LINE_ID,
    VARIATION_REF_ID,
    derive_matrix_script_task_card_summary,
)

# Operator-language stage enum from matrix_script_product_flow §5.2.
# Order matters — higher precedence wins in `derive_matrix_script_eight_stage_state`.
STAGE_CREATED = "created"
STAGE_PENDING_CONFIG = "pending_config"
STAGE_GENERATING = "generating"
STAGE_AWAITING_REVIEW = "awaiting_review"
STAGE_FINAL_READY = "final_ready"
STAGE_PUBLISHABLE = "publishable"
STAGE_BACKFILLED = "backfilled"
STAGE_ARCHIVED = "archived"

EIGHT_STAGES = (
    STAGE_CREATED,
    STAGE_PENDING_CONFIG,
    STAGE_GENERATING,
    STAGE_AWAITING_REVIEW,
    STAGE_FINAL_READY,
    STAGE_PUBLISHABLE,
    STAGE_BACKFILLED,
    STAGE_ARCHIVED,
)

EIGHT_STAGE_LABELS: dict[str, str] = {
    STAGE_CREATED: "已创建",
    STAGE_PENDING_CONFIG: "待配置",
    STAGE_GENERATING: "生成中",
    STAGE_AWAITING_REVIEW: "待校对",
    STAGE_FINAL_READY: "成片完成",
    STAGE_PUBLISHABLE: "可发布",
    STAGE_BACKFILLED: "已回填",
    STAGE_ARCHIVED: "已归档",
}

# Three-tier lane keys per matrix_script_product_flow §5.1.
LANE_SCRIPT = "script_task"
LANE_VARIATION = "variation_task"
LANE_PUBLISH = "publish_task"

LANE_LABELS = {
    LANE_SCRIPT: "脚本任务",
    LANE_VARIATION: "变体任务",
    LANE_PUBLISH: "发布任务",
}

# Tooltip strings exposed on optional fields (OWC-MS PR-2 backfill notes).
BEST_VERSION_TOOLTIP = "当前最佳版本将在工作台校对区上线后开放"


def _is_matrix_script_row(row: Mapping[str, Any]) -> bool:
    if not isinstance(row, Mapping):
        return False
    kind = str(
        row.get("kind") or row.get("category_key") or row.get("platform") or ""
    ).strip().lower()
    return kind in {MATRIX_SCRIPT_LINE_ID, "matrix-script"}


def _variation_cells(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    refs = row.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        packet = row.get("packet")
        if isinstance(packet, Mapping):
            refs = packet.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        return []
    for item in refs:
        if not isinstance(item, Mapping):
            continue
        if item.get("ref_id") != VARIATION_REF_ID:
            continue
        delta = item.get("delta")
        if not isinstance(delta, Mapping):
            return []
        cells = delta.get("cells")
        return [c for c in cells if isinstance(c, Mapping)] if isinstance(cells, (list, tuple)) else []
    return []


def _source_script_ref_value(row: Mapping[str, Any]) -> Optional[str]:
    """Read ``source_script_ref`` from the entry payload if present.

    The Matrix Script create-entry payload stores ``source_script_ref``
    inside ``line_specific_refs[matrix_script_task_entry].delta`` per
    ``docs/contracts/matrix_script/task_entry_contract_v1.md``. We
    surface the bare ref string for the operator-language "核心脚本名称"
    field. No dereference; no opaque-token decoding.
    """
    refs = row.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        packet = row.get("packet")
        if isinstance(packet, Mapping):
            refs = packet.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        return None
    for item in refs:
        if not isinstance(item, Mapping):
            continue
        delta = item.get("delta")
        if not isinstance(delta, Mapping):
            continue
        ref = delta.get("source_script_ref")
        if isinstance(ref, str) and ref.strip():
            return ref.strip()
    return None


def _published_variation_count(closure: Optional[Mapping[str, Any]]) -> int:
    if not isinstance(closure, Mapping):
        return 0
    rows = closure.get("variation_feedback")
    if not isinstance(rows, list):
        return 0
    count = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("publish_status") or "").strip().lower() == "published":
            count += 1
    return count


def _published_channel_count(closure: Optional[Mapping[str, Any]]) -> int:
    if not isinstance(closure, Mapping):
        return 0
    rows = closure.get("variation_feedback")
    if not isinstance(rows, list):
        return 0
    channels: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        metrics = row.get("channel_metrics")
        if not isinstance(metrics, list):
            continue
        for snapshot in metrics:
            if not isinstance(snapshot, Mapping):
                continue
            platform = snapshot.get("platform")
            if isinstance(platform, str) and platform.strip():
                channels.add(platform.strip())
    return len(channels)


def _last_generation_at(row: Mapping[str, Any]) -> Optional[str]:
    """Operator-readable "最近一次生成时间".

    Reads the row's ``updated_at`` (preferred) then ``created_at`` as
    fallback. Both are already operator-visible timestamps already on
    the row dict; this helper makes no new authority claim.
    """
    for key in ("updated_at", "last_generated_at", "created_at"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def derive_matrix_script_eight_stage_state(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the eight operator-language stages for a Matrix Script row.

    Precedence (operator-readable from "earliest" to "latest"):

    1. ``archived`` — explicit ``row["archived"]`` flag.
    2. ``backfilled`` — closure has any ``publish_status == "published"`` row.
    3. ``publishable`` — board bucket is ``publishable`` (PR-1 unified
       publish_readiness consumed via ``board_bucket``).
    4. ``final_ready`` — final exists + no stale reason.
    5. ``awaiting_review`` — compose_ready true but final not present /
       not fresh.
    6. ``generating`` — compose status ``running`` / generation
       underway.
    7. ``pending_config`` — variation cells empty (Phase B authoring
       pending).
    8. ``created`` — fallback when nothing above asserts.

    Returns ``{"stage", "stage_label", "stage_index"}``. ``stage_index``
    is the index in :data:`EIGHT_STAGES` for stable ordering on the
    operator surface.
    """
    if not _is_matrix_script_row(row):
        return {}

    archived = bool(row.get("archived"))
    if archived:
        stage = STAGE_ARCHIVED
    elif _published_variation_count(closure) > 0:
        stage = STAGE_BACKFILLED
    else:
        bucket = str(row.get("board_bucket") or "").strip().lower()
        if bucket == "publishable":
            stage = STAGE_PUBLISHABLE
        else:
            ready_gate = row.get("ready_gate") if isinstance(row.get("ready_gate"), Mapping) else {}
            compose_ready = bool(ready_gate.get("compose_ready")) if isinstance(ready_gate, Mapping) else False
            compose_status = str(row.get("compose_status") or "").strip().lower()
            final_payload = row.get("final") if isinstance(row.get("final"), Mapping) else None
            final_exists = bool(final_payload.get("exists")) if isinstance(final_payload, Mapping) else False
            cells = _variation_cells(row)
            if final_exists:
                stage = STAGE_FINAL_READY
            elif compose_ready:
                stage = STAGE_AWAITING_REVIEW
            elif compose_status in {"running", "in_progress", "queued"}:
                stage = STAGE_GENERATING
            elif not cells:
                stage = STAGE_PENDING_CONFIG
            else:
                stage = STAGE_CREATED

    return {
        "stage": stage,
        "stage_label": EIGHT_STAGE_LABELS[stage],
        "stage_index": EIGHT_STAGES.index(stage),
    }


def derive_matrix_script_three_tier_lanes(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the 脚本任务 / 变体任务 / 发布任务 lane view for a row.

    All three lanes are read-only projections; no authoring affordance
    is exposed. The variation lane reads cells from
    ``line_specific_refs[matrix_script_variation_matrix].delta.cells``
    and joins each cell to its closure ``variation_feedback`` row by
    ``cell_id`` / ``variation_id`` when the closure exists. The publish
    lane flattens ``variation_feedback[].channel_metrics[]`` into per-
    channel entries.

    Returns:
        {
            "is_matrix_script": True,
            "lanes": [
                {"key": "script_task", "label": "脚本任务", "rows": [...]},
                {"key": "variation_task", "label": "变体任务", "rows": [...]},
                {"key": "publish_task", "label": "发布任务", "rows": [...]},
            ],
        }
    """
    if not _is_matrix_script_row(row):
        return {}

    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    subject = row.get("title") or ""
    source_script_ref = _source_script_ref_value(row)

    script_lane_rows = [
        {
            "task_id": task_id,
            "subject": str(subject),
            "source_script_ref": source_script_ref,
        }
    ]

    cells = _variation_cells(row)
    feedback_by_id: dict[str, Mapping[str, Any]] = {}
    if isinstance(closure, Mapping):
        rows_iter = closure.get("variation_feedback")
        if isinstance(rows_iter, list):
            for fb in rows_iter:
                if not isinstance(fb, Mapping):
                    continue
                vid = fb.get("variation_id")
                if isinstance(vid, str) and vid:
                    feedback_by_id[vid] = fb

    variation_rows: list[dict[str, Any]] = []
    for cell in cells:
        cell_id = cell.get("cell_id")
        cell_id_str = str(cell_id) if isinstance(cell_id, str) and cell_id else ""
        fb = feedback_by_id.get(cell_id_str) if cell_id_str else None
        publish_status = (
            str(fb.get("publish_status") or "").strip().lower()
            if isinstance(fb, Mapping)
            else "pending"
        )
        variation_rows.append(
            {
                "variation_id": cell_id_str,
                "axis_tuple": cell.get("axis_tuple"),
                "publish_status": publish_status or "pending",
            }
        )

    publish_rows: list[dict[str, Any]] = []
    for fb in feedback_by_id.values():
        vid = str(fb.get("variation_id") or "")
        publish_url = fb.get("publish_url") if isinstance(fb.get("publish_url"), str) else None
        publish_status = str(fb.get("publish_status") or "").strip().lower() or "pending"
        metrics = fb.get("channel_metrics")
        if not isinstance(metrics, list) or not metrics:
            continue
        for snapshot in metrics:
            if not isinstance(snapshot, Mapping):
                continue
            platform = snapshot.get("platform")
            account = snapshot.get("account_id")
            published_at = snapshot.get("published_at")
            publish_rows.append(
                {
                    "variation_id": vid,
                    "platform": str(platform) if isinstance(platform, str) else None,
                    "account_id": str(account) if isinstance(account, str) else None,
                    "published_at": str(published_at) if isinstance(published_at, str) else None,
                    "publish_url": publish_url,
                    "publish_status": publish_status,
                }
            )

    return {
        "is_matrix_script": True,
        "lanes": [
            {"key": LANE_SCRIPT, "label": LANE_LABELS[LANE_SCRIPT], "rows": script_lane_rows},
            {"key": LANE_VARIATION, "label": LANE_LABELS[LANE_VARIATION], "rows": variation_rows},
            {"key": LANE_PUBLISH, "label": LANE_LABELS[LANE_PUBLISH], "rows": publish_rows},
        ],
    }


def derive_matrix_script_full_card_summary(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the eight-field operator-language Task Area card summary
    plus the eight-stage state plus the three-tier lanes.

    Returns the union of:

    - PR-U1 ``derive_matrix_script_task_card_summary`` (subject /
      current_variation_count / publishable_variation_count tri-state /
      blocker / tri-state badge / action hrefs) — unchanged keys.
    - The four newly-converged fields (核心脚本名称 / 已发布账号数 /
      当前最佳版本 / 最近一次生成时间).
    - The eight-stage projection.
    - The three-tier lanes.

    Hot Follow / Digital Anchor / baseline rows return ``{}`` so the
    template can safely call this without further gating; the template
    additionally gates rendering on ``data-line == "matrix_script"``.
    """
    pr_u1 = derive_matrix_script_task_card_summary(row)
    if not pr_u1:
        return {}

    # OWC-MS PR-1 rebinds publishable_variation_count from the gated-by-D1
    # sentinel to the contract-frozen closure-derived count. The PR-1
    # unified publish_readiness producer is now live; the count of
    # variation_feedback rows in publish_status == "published" is the
    # operator-truthful answer.
    published_count = _published_variation_count(closure)
    pr_u1["publishable_variation_count_value"] = published_count
    pr_u1["publishable_variation_count_gated_by"] = None
    pr_u1["publishable_variation_count_tooltip"] = None

    source_script_ref = _source_script_ref_value(row)
    published_channel_count = _published_channel_count(closure)
    last_gen = _last_generation_at(row)
    eight_stage = derive_matrix_script_eight_stage_state(row, closure=closure)
    lanes = derive_matrix_script_three_tier_lanes(row, closure=closure)

    pr_u1.update(
        {
            "core_script_name_label": "核心脚本名称",
            "core_script_name_value": source_script_ref,
            "published_channel_count_label": "已发布账号数",
            "published_channel_count_value": published_channel_count,
            "best_version_label": "当前最佳版本",
            "best_version_value": None,
            "best_version_tooltip": BEST_VERSION_TOOLTIP,
            "last_generated_at_label": "最近一次生成时间",
            "last_generated_at_value": last_gen,
            "eight_stage": eight_stage,
            "lanes_view": lanes,
        }
    )
    return pr_u1


def derive_matrix_script_full_card_summary_for_task(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Convenience wrapper that resolves the closure via task_id and
    forwards to :func:`derive_matrix_script_full_card_summary`.

    Reads the closure read-only via
    :func:`closure_binding.get_closure_view_for_task` so the projection
    NEVER lazily creates a closure on the in-process store.
    """
    if not _is_matrix_script_row(row):
        return {}
    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    closure = get_closure_view_for_task(task_id) if task_id else None
    return derive_matrix_script_full_card_summary(row, closure=closure)


__all__ = [
    "BEST_VERSION_TOOLTIP",
    "EIGHT_STAGES",
    "EIGHT_STAGE_LABELS",
    "LANE_LABELS",
    "LANE_PUBLISH",
    "LANE_SCRIPT",
    "LANE_VARIATION",
    "STAGE_ARCHIVED",
    "STAGE_AWAITING_REVIEW",
    "STAGE_BACKFILLED",
    "STAGE_CREATED",
    "STAGE_FINAL_READY",
    "STAGE_GENERATING",
    "STAGE_PENDING_CONFIG",
    "STAGE_PUBLISHABLE",
    "derive_matrix_script_eight_stage_state",
    "derive_matrix_script_full_card_summary",
    "derive_matrix_script_full_card_summary_for_task",
    "derive_matrix_script_three_tier_lanes",
]
