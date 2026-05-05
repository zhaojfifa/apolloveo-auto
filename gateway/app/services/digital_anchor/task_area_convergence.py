"""Digital Anchor Task Area workflow convergence projection (OWC-DA PR-1).

Pure operator-language projection over the existing task row + the
read-only Digital Anchor closure view. Implements the OWC-DA PR-1 scope
from ``docs/reviews/owc_da_gate_spec_v1.md`` §3:

- **DA-W1 — Task entry workspace convergence**. Renders the eight
  operator-language task-card fields per
  ``docs/product/digital_anchor_product_flow_v1.md`` §5.2: 任务标题 /
  Role Profile / Scene Template / Target Language / 当前版本状态 / 当前
  阻塞项 / 交付包状态 / 最近更新. The Tasks-Newtasks card → formal
  ``/tasks/digital-anchor/new`` entry chain was shipped by Operator
  Capability Recovery PR-4; this module owns the post-create card body
  on ``tasks.html``.
- **DA-W2 — Task Area eight-stage projection**. Projects existing
  ``roles[]`` / ``segments[]`` skeleton state + L1 step status + L3
  current attempt + closure events into the eight Digital Anchor stages
  per ``digital_anchor_product_flow`` §5.1: 输入已提交 / 内容结构已生成 /
  场景计划已生成 / 角色 / 声音已绑定 / 多语言版本生成中 / 合成完成 /
  可交付 / 已归档. Read-only derivation.

Hard discipline (binding per OWC-DA gate spec §4 + the user's
PR-1 reminders):

- **Reminder #1** — 当前版本状态 consumes existing unified
  ``publish_readiness`` / ``board_bucket`` truth ONLY. No alternative
  producer is consulted.
- **Reminder #2** — 交付包状态 stays coarse / tracked-gap in PR-1; the
  fine-grained Delivery Pack assembly view lands in DA-W8 / PR-3. This
  module renders the field with a ``None`` value plus a closed
  ``delivery_pack_state_gated_by`` sentinel and a tooltip naming the
  future DA-W8 source so the operator block is always present per
  ``ENGINEERING_RULES.md`` §13 product-flow module presence.
- **Reminder #3** — the eight-stage projection degrades gracefully when
  ``closure`` is ``None`` and invents no late-stage truth. Late stages
  derive only from observable signals on the existing four-layer state
  (``board_bucket`` / ``compose_status`` / ``final.exists``) and from
  closed-enum closure records (``feedback_closure_records[].record_kind ==
  "archive_action"`` for ``已归档``). When none of those signals fires
  the projection stays at ``输入已提交``.

Other binding rules (per OWC-DA gate spec §4):

- Reads only existing row truth + the read-only closure view from
  :func:`gateway.app.services.digital_anchor.closure_binding.get_closure_view_for_task`.
  The closure read uses ``get_closure_view_for_task`` (read-only) and
  NEVER calls ``get_or_create_for_task`` — Task Area projection must
  not lazily mutate the in-process closure store.
- No packet mutation; no projection mutation; no closure write-back.
- No contract-shape change; the additive ``review_zone`` enum on the
  D.1 closure event payload is OWC-DA PR-2 / DA-W7 scope.
- No provider / model / vendor / engine identifier ever appears in the
  return value (validator R3 + sanitization at the operator boundary).
- Hot Follow rows / Matrix Script rows / baseline rows MUST NOT receive
  any of the OWC-DA surface objects produced by this module (the helper
  returns the empty dict for non-digital_anchor rows so the caller's
  gating preserves their bytewise-unchanged Task Area rendering).

Authority pointers:

- ``docs/product/digital_anchor_product_flow_v1.md`` §§5.1 / 5.2
- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 (DA-W1 + DA-W2)
- ``docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md``
  (closure event vocabulary; read-only)
- ``ENGINEERING_RULES.md`` §13 Product-Flow Module Presence
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .closure_binding import get_closure_view_for_task

DIGITAL_ANCHOR_LINE_ID = "digital_anchor"
ROLE_PACK_REF_ID = "digital_anchor_role_pack"
SPEAKER_PLAN_REF_ID = "digital_anchor_speaker_plan"

# Eight operator-language stages from digital_anchor_product_flow §5.1.
# Order matters — `stage_index` reads from this tuple and a higher index
# means a later stage in the operator-readable progression.
STAGE_INPUT_SUBMITTED = "input_submitted"
STAGE_STRUCTURE_GENERATED = "structure_generated"
STAGE_SCENE_PLAN_GENERATED = "scene_plan_generated"
STAGE_ROLE_VOICE_BOUND = "role_voice_bound"
STAGE_MULTI_LANGUAGE_GENERATING = "multi_language_generating"
STAGE_COMPOSED = "composed"
STAGE_DELIVERABLE = "deliverable"
STAGE_ARCHIVED = "archived"

EIGHT_STAGES = (
    STAGE_INPUT_SUBMITTED,
    STAGE_STRUCTURE_GENERATED,
    STAGE_SCENE_PLAN_GENERATED,
    STAGE_ROLE_VOICE_BOUND,
    STAGE_MULTI_LANGUAGE_GENERATING,
    STAGE_COMPOSED,
    STAGE_DELIVERABLE,
    STAGE_ARCHIVED,
)

EIGHT_STAGE_LABELS: dict[str, str] = {
    STAGE_INPUT_SUBMITTED: "输入已提交",
    STAGE_STRUCTURE_GENERATED: "内容结构已生成",
    STAGE_SCENE_PLAN_GENERATED: "场景计划已生成",
    STAGE_ROLE_VOICE_BOUND: "角色 / 声音已绑定",
    STAGE_MULTI_LANGUAGE_GENERATING: "多语言版本生成中",
    STAGE_COMPOSED: "合成完成",
    STAGE_DELIVERABLE: "可交付",
    STAGE_ARCHIVED: "已归档",
}

# Operator-language tri-state for "当前版本状态" derived from the unified
# publish_readiness producer's `board_bucket` field (PR-1 reminder #1).
# Distinct from the eight-stage badge wording so the two operator surfaces
# do not collide at the cell level.
CURRENT_VERSION_STATE_LABELS: dict[str, str] = {
    "blocked": "受阻",
    "ready": "进行中",
    "publishable": "可发布",
}

# Operator-language translation of the closed `head_reason` enum from
# `derive_board_publishable`. Mirrors the Matrix Script PR-U1 translation
# table; unknown codes fall through to the raw string so a future
# producer addition surfaces as raw evidence rather than dropping silently.
_BLOCKER_LABEL_MAP = {
    "publish_ready_pending": "等待生成",
    "compose_ready_pending": "合成未就绪",
    "delivery_required_unresolved": "必交付物缺失",
    "scene_pack_blocking_disallowed": "配套素材阻塞被禁止",
    "final_fresh": "终片需重新生成",
    "subtitles_pending": "字幕未就绪",
    "dub_pending": "配音未就绪",
}

# Sentinel + tooltip for the tracked-gap "交付包状态" field. Fine-grained
# Delivery Pack rendering is OWC-DA DA-W8 / PR-3 scope per gate spec §3,
# so PR-1 surfaces the field with a closed gating sentinel.
DELIVERY_PACK_STATE_GATED_BY_DA_W8 = "gated_by_owc_da_w8_delivery_pack_assembly"
DELIVERY_PACK_STATE_TOOLTIP = "交付包状态将在 DA-W8 交付包装配视图上线后开放"

# Closed `feedback_closure_records[].record_kind` enum from
# `digital_anchor_publish_feedback_closure_v1`. Only `archive_action`
# drives a Task Area stage transition in PR-1.
_ARCHIVE_RECORD_KIND = "archive_action"


def _is_digital_anchor_row(row: Mapping[str, Any]) -> bool:
    if not isinstance(row, Mapping):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower() == DIGITAL_ANCHOR_LINE_ID:
            return True
    return False


def _line_specific_refs(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    refs = row.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        packet = row.get("packet")
        if isinstance(packet, Mapping):
            refs = packet.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        return []
    return [item for item in refs if isinstance(item, Mapping)]


def _ref_delta(row: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in _line_specific_refs(row):
        if item.get("ref_id") != ref_id:
            continue
        delta = item.get("delta")
        return delta if isinstance(delta, Mapping) else {}
    return {}


def _entry_view(row: Mapping[str, Any]) -> Mapping[str, Any]:
    config = row.get("config")
    if not isinstance(config, Mapping):
        return {}
    entry = config.get("entry")
    return entry if isinstance(entry, Mapping) else {}


def _role_profile_ref(row: Mapping[str, Any]) -> Optional[str]:
    entry = _entry_view(row)
    value = entry.get("role_profile_ref")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _scene_template_ref(row: Mapping[str, Any]) -> Optional[str]:
    entry = _entry_view(row)
    value = entry.get("scene_binding_hint")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _target_languages(row: Mapping[str, Any]) -> list[str]:
    entry = _entry_view(row)
    scope = entry.get("language_scope")
    if not isinstance(scope, Mapping):
        return []
    targets = scope.get("target_language")
    if isinstance(targets, (list, tuple)):
        return [str(v).strip() for v in targets if isinstance(v, str) and v.strip()]
    if isinstance(targets, str) and targets.strip():
        return [targets.strip()]
    return []


def _has_authored_roles(row: Mapping[str, Any]) -> bool:
    """Whether ``digital_anchor_role_pack.delta.roles[]`` is non-empty.

    Operator Capability Recovery PR-4 seeds the ref skeleton without any
    ``delta``; Phase B authoring (forbidden in OWC-DA per gate spec §4.1)
    is what would populate ``roles[]``. Returns ``False`` whenever the
    skeleton is empty so the projection degrades gracefully (reminder #3).
    """
    delta = _ref_delta(row, ROLE_PACK_REF_ID)
    roles = delta.get("roles") if isinstance(delta, Mapping) else None
    return isinstance(roles, (list, tuple)) and len(roles) > 0


def _has_authored_segments(row: Mapping[str, Any]) -> bool:
    delta = _ref_delta(row, SPEAKER_PLAN_REF_ID)
    segments = delta.get("segments") if isinstance(delta, Mapping) else None
    return isinstance(segments, (list, tuple)) and len(segments) > 0


def _closure_has_archive_record(closure: Optional[Mapping[str, Any]]) -> bool:
    """Closure-driven late-stage signal for ``已归档``.

    Reads the closed ``feedback_closure_records[].record_kind`` enum from
    ``digital_anchor_publish_feedback_closure_v1``. ``archive_action`` is
    the closure-side trigger for the operator's archive intent. When the
    closure is ``None`` (no closure created yet) this returns ``False``
    so the projection degrades gracefully (reminder #3).
    """
    if not isinstance(closure, Mapping):
        return False
    records = closure.get("feedback_closure_records")
    if not isinstance(records, list):
        return False
    for record in records:
        if not isinstance(record, Mapping):
            continue
        if str(record.get("record_kind") or "").strip().lower() == _ARCHIVE_RECORD_KIND:
            return True
    return False


def _last_update_at(row: Mapping[str, Any]) -> Optional[str]:
    """Operator-readable "最近更新".

    Reads ``updated_at`` (preferred) → ``last_generated_at`` → ``created_at``.
    All three are operator-visible timestamps already on the row dict;
    this helper makes no new authority claim.
    """
    for key in ("updated_at", "last_generated_at", "created_at"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _operator_blocker_label(head_reason: Optional[str]) -> Optional[str]:
    if not head_reason:
        return None
    code = str(head_reason).strip()
    if not code:
        return None
    return _BLOCKER_LABEL_MAP.get(code, code)


def _next_surfaces(row: Mapping[str, Any]) -> Mapping[str, Any]:
    config = row.get("config")
    if not isinstance(config, Mapping):
        return {}
    surfaces = config.get("next_surfaces")
    return surfaces if isinstance(surfaces, Mapping) else {}


def _current_version_state(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project 当前版本状态 from the authoritative ``board_bucket`` only.

    Per PR-1 reminder #1: 当前版本状态 must consume existing unified
    ``publish_readiness`` / ``board_bucket`` truth only. No alternative
    producer is consulted; unknown bucket values clamp to ``ready``.
    """
    bucket = str(row.get("board_bucket") or "ready").strip().lower()
    if bucket not in CURRENT_VERSION_STATE_LABELS:
        bucket = "ready"
    return {
        "current_version_state_value": bucket,
        "current_version_state_label_value": CURRENT_VERSION_STATE_LABELS[bucket],
    }


def derive_digital_anchor_eight_stage_state(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the eight Digital Anchor stages for a row.

    Precedence (later stage wins; first match exits):

    1. ``archived`` — explicit ``row["archived"]`` flag OR closure has any
       ``feedback_closure_records[].record_kind == "archive_action"`` event.
    2. ``deliverable`` — ``board_bucket == "publishable"`` (PR-1 unified
       publish_readiness consumed via ``board_bucket``; reminder #1).
    3. ``composed`` — ``final.exists`` is ``True``.
    4. ``multi_language_generating`` — ``compose_status`` ∈
       ``{running, in_progress, queued}``.
    5. ``role_voice_bound`` — both ``roles[]`` and ``segments[]`` populated.
    6. ``scene_plan_generated`` — ``scene_template_ref`` present (operator
       hint from create-entry) AND ``roles[]`` populated. Degrade
       gracefully — do NOT invent late-stage truth (reminder #3) — so a
       scene hint alone (without authored roles) does not bump past
       ``input_submitted``.
    7. ``structure_generated`` — ``roles[]`` populated only.
    8. ``input_submitted`` — fallback after task creation.

    Returns ``{"stage", "stage_label", "stage_index"}``. ``stage_index``
    is the index in :data:`EIGHT_STAGES` for stable ordering on the
    operator surface.
    """
    if not _is_digital_anchor_row(row):
        return {}

    archived = bool(row.get("archived")) or _closure_has_archive_record(closure)
    if archived:
        stage = STAGE_ARCHIVED
    else:
        bucket = str(row.get("board_bucket") or "").strip().lower()
        compose_status = str(row.get("compose_status") or "").strip().lower()
        final_payload = row.get("final") if isinstance(row.get("final"), Mapping) else None
        final_exists = bool(final_payload.get("exists")) if isinstance(final_payload, Mapping) else False
        roles_authored = _has_authored_roles(row)
        segments_authored = _has_authored_segments(row)
        scene_present = _scene_template_ref(row) is not None

        if bucket == "publishable":
            stage = STAGE_DELIVERABLE
        elif final_exists:
            stage = STAGE_COMPOSED
        elif compose_status in {"running", "in_progress", "queued"}:
            stage = STAGE_MULTI_LANGUAGE_GENERATING
        elif roles_authored and segments_authored:
            stage = STAGE_ROLE_VOICE_BOUND
        elif roles_authored and scene_present:
            stage = STAGE_SCENE_PLAN_GENERATED
        elif roles_authored:
            stage = STAGE_STRUCTURE_GENERATED
        else:
            stage = STAGE_INPUT_SUBMITTED

    return {
        "stage": stage,
        "stage_label": EIGHT_STAGE_LABELS[stage],
        "stage_index": EIGHT_STAGES.index(stage),
    }


def derive_digital_anchor_card_summary(
    row: Mapping[str, Any],
    *,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the eight operator-language Task Area card fields per
    ``digital_anchor_product_flow`` §5.2 plus the eight-stage badge per
    §5.1 plus the operator action affordances.

    Returns the empty dict for non-digital-anchor rows so the caller can
    safely attach the result without further gating; the template
    additionally gates rendering on ``data-line == "digital_anchor"``.
    """
    if not _is_digital_anchor_row(row):
        return {}

    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    title = row.get("title") or ""
    role_profile = _role_profile_ref(row)
    scene_template = _scene_template_ref(row)
    target_langs = _target_languages(row)
    head_reason = row.get("head_reason")
    blocker_label = _operator_blocker_label(head_reason if isinstance(head_reason, str) else None)
    last_update = _last_update_at(row)
    eight_stage = derive_digital_anchor_eight_stage_state(row, closure=closure)
    cv_state = _current_version_state(row)

    surfaces = _next_surfaces(row)
    workbench_href = (
        str(surfaces.get("workbench") or "").strip()
        or (f"/tasks/{task_id}" if task_id else "")
    )
    delivery_href = (
        str(surfaces.get("delivery") or "").strip()
        or (f"/tasks/{task_id}/publish" if task_id else "")
    )

    summary: dict[str, Any] = {
        "is_digital_anchor": True,
        "task_id": task_id,
        # Field 1: 任务标题
        "task_title_label": "任务标题",
        "task_title_value": str(title),
        # Field 2: Role Profile (operator hint from create-entry)
        "role_profile_label": "Role Profile",
        "role_profile_value": role_profile,
        # Field 3: Scene Template (operator hint from create-entry)
        "scene_template_label": "Scene Template",
        "scene_template_value": scene_template,
        # Field 4: Target Language (closed list from create-entry language_scope)
        "target_language_label": "Target Language",
        "target_language_value": target_langs,
        # Field 5: 当前版本状态 (board_bucket only — reminder #1)
        "current_version_state_label": "当前版本状态",
        # Field 6: 当前阻塞项 (translated head_reason; raw fallthrough)
        "current_blocker_label": "当前阻塞项",
        "current_blocker_value": blocker_label,
        # Field 7: 交付包状态 (coarse / tracked-gap — reminder #2)
        "delivery_pack_state_label": "交付包状态",
        "delivery_pack_state_value": None,
        "delivery_pack_state_gated_by": DELIVERY_PACK_STATE_GATED_BY_DA_W8,
        "delivery_pack_state_tooltip": DELIVERY_PACK_STATE_TOOLTIP,
        # Field 8: 最近更新
        "last_update_label": "最近更新",
        "last_update_value": last_update,
        # DA-W2 eight-stage badge
        "eight_stage": eight_stage,
        # Operator action affordances (mirror the Matrix Script PR-U1 pattern)
        "workbench_action_label": "进入工作台",
        "workbench_action_href": workbench_href,
        "delivery_action_label": "跳交付中心",
        "delivery_action_href": delivery_href,
    }
    summary.update(cv_state)
    return summary


def derive_digital_anchor_card_summary_for_task(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Convenience wrapper that resolves the closure read-only and
    forwards to :func:`derive_digital_anchor_card_summary`.

    Reads via :func:`closure_binding.get_closure_view_for_task` so the
    Task Area projection NEVER lazily creates a closure on the in-process
    store (mirrors the OWC-MS PR-1 discipline at
    ``gateway.app.services.matrix_script.task_area_convergence``).
    """
    if not _is_digital_anchor_row(row):
        return {}
    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    closure = get_closure_view_for_task(task_id) if task_id else None
    return derive_digital_anchor_card_summary(row, closure=closure)


__all__ = [
    "CURRENT_VERSION_STATE_LABELS",
    "DELIVERY_PACK_STATE_GATED_BY_DA_W8",
    "DELIVERY_PACK_STATE_TOOLTIP",
    "DIGITAL_ANCHOR_LINE_ID",
    "EIGHT_STAGES",
    "EIGHT_STAGE_LABELS",
    "ROLE_PACK_REF_ID",
    "SPEAKER_PLAN_REF_ID",
    "STAGE_ARCHIVED",
    "STAGE_COMPOSED",
    "STAGE_DELIVERABLE",
    "STAGE_INPUT_SUBMITTED",
    "STAGE_MULTI_LANGUAGE_GENERATING",
    "STAGE_ROLE_VOICE_BOUND",
    "STAGE_SCENE_PLAN_GENERATED",
    "STAGE_STRUCTURE_GENERATED",
    "derive_digital_anchor_card_summary",
    "derive_digital_anchor_card_summary_for_task",
    "derive_digital_anchor_eight_stage_state",
]
