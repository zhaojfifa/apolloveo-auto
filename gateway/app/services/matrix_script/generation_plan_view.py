"""Matrix Script — Generation Plan / Storyboard projection (Storyboard Control wave PR-1).

PROJECTION ONLY. Projects the already-built per-shot overlay cards (from
``operator_workbench_view._build_shots`` + ``_enrich_shot_observability``) plus
the fixed shot plan's script-derived fields into a Slot-Workflow-v2-conformant
**Storyboard Queue** (compact, one row per shot, exactly one active) + a single
active **Current Shot Work Panel** carrying the §7 operator fields:

    镜头目标 / 画面动作 / 旁白 / 字幕重点 / 素材角色 / AI 生成要求 / 负面约束 / 当前生成状态

Honest placeholders for not-yet-wired capabilities (gate spec WB-4 — status text
only, NEVER a dead/disabled control):
- 画面动作 (motion) → later slice
- 素材角色 (material role binding) → PR-3
- AI 生成要求 / 负面约束 (Prompt Builder) → PR-2
- 改写生成要求 / 重新生成这个镜头 / 接受这个镜头 → status-only (PR-2/PR-3/PR-4)

NO provider call, NO Prompt Builder, NO Akool, NO route, NO schema/contract
change, NO new producer / second source of truth. Status codes are closed
presenter-layer constants (presenter alignment §6.2 + contract alignment §5).

Authority:
``docs/design/MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_20260608.md``
§5 (projection-first) / §6 (workbench re-home) / §7 (operator fields) / §15 (PR-1).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

# Closed plan status codes (presenter alignment §6.2 + contract alignment §5).
PLAN_PENDING_UPSTREAM = "plan_pending_upstream"
PLAN_RESOLVED_PLACEHOLDER = "plan_resolved_placeholder"
PLAN_RESOLVED_REAL = "plan_resolved_real"
_PLAN_STATUS_LABEL = {
    PLAN_PENDING_UPSTREAM: "当前尚未生成视频方案。",
    PLAN_RESOLVED_PLACEHOLDER: "视频方案（分镜）已就绪；脚本派生的生成要求将在后续接入。",
    PLAN_RESOLVED_REAL: "视频方案已就绪。",
}

# Honest placeholder copy + closed status codes for not-yet-wired §7 fields.
MOTION_PENDING = "motion_pending_builder"
ROLE_PENDING = "material_role_pending_binding"
AI_REQUIREMENT_PENDING = "ai_requirement_pending_builder"
NEGATIVE_PENDING = "negative_pending_builder"
_PLACEHOLDER_ZH = {
    MOTION_PENDING: "脚本派生的镜头动作将在后续接入。",
    ROLE_PENDING: "角色绑定（产品 / 场景 / 人物等）将在后续接入。",
    AI_REQUIREMENT_PENDING: "脚本派生的生成要求将在后续接入（届时可改写）。",
    NEGATIVE_PENDING: "负面约束将随生成要求一并接入。",
}

# Follow-up actions are status-only (no actionable control yet) — gate spec §7 / WB-4.
PENDING_ACTIONS_ZH = (
    "改写生成要求：后续接入",
    "重新生成这个镜头：后续接入",
    "接受这个镜头：后续接入",
)
REPLACE_MATERIAL_HINT_ZH = "替换素材：见下方“背景、素材、配乐调整”的逐镜素材区。"


def _shot_label(shot_id: str) -> str:
    sid = str(shot_id)
    if sid.startswith("shot") and sid[4:].isdigit():
        return "Shot %02d" % int(sid[4:])
    return sid


def _current_generation_status_zh(card: Mapping[str, Any]) -> str:
    """当前生成状态 — projected from the existing per-shot overlay card."""
    obs = card.get("shot_observability_status_zh")
    if obs:
        return str(obs)
    if card.get("included_in_current_video"):
        src = card.get("visual_source_label_zh") or "已进入当前主视频"
        return "已进入当前主视频 · " + str(src)
    return "尚未生成"


def _build_current_shot(ps: Any, card: Mapping[str, Any], status_zh: str) -> Dict[str, Any]:
    """The single active shot's §7 panel — projection where available, else placeholder."""
    return {
        "shot_id": ps.shot_id,
        "shot_label_zh": _shot_label(ps.shot_id),
        "scene_index": ps.order,
        "title_zh": ps.title_zh,
        # 镜头目标 / 旁白 / 字幕重点 — projection of the script-derived shot fields.
        "visual_goal_zh": ps.visual_intent_zh,
        "narration_zh": ps.voiceover_zh,
        "subtitle_focus_zh": ps.subtitle_zh,
        # 画面动作 / 素材角色 / AI 生成要求 / 负面约束 — honest placeholders (later slices).
        "motion_instruction_zh": _PLACEHOLDER_ZH[MOTION_PENDING],
        "motion_status_code": MOTION_PENDING,
        "material_role_zh": _PLACEHOLDER_ZH[ROLE_PENDING],
        "material_role_status_code": ROLE_PENDING,
        "ai_requirement_zh": _PLACEHOLDER_ZH[AI_REQUIREMENT_PENDING],
        "ai_requirement_status_code": AI_REQUIREMENT_PENDING,
        "negative_constraint_zh": _PLACEHOLDER_ZH[NEGATIVE_PENDING],
        "negative_status_code": NEGATIVE_PENDING,
        # 当前生成状态 — projection of the existing per-shot status.
        "current_generation_status_zh": status_zh,
        # Status-only follow-up actions (no dead control, gate spec WB-4).
        "pending_actions_zh": list(PENDING_ACTIONS_ZH),
        "replace_material_hint_zh": REPLACE_MATERIAL_HINT_ZH,
    }


def derive_matrix_script_generation_plan_view(
    *,
    shots: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Project the storyboard queue + single active Current Shot Work Panel.

    ``shots`` are the already-built overlay cards. Script-derived intent fields
    are read from the fixed shot plan (``plan_mod.TOMATO_SHOTS``) by shot id.
    Projection only — no provider call, no new truth. The active shot is the
    first shot (order 1); exactly one shot is active.
    """
    card_by_id: Dict[str, Mapping[str, Any]] = {
        str(c.get("shot_id")): c for c in (shots or []) if isinstance(c, Mapping)
    }
    plan_shots = list(plan_mod.TOMATO_SHOTS)
    if not plan_shots:
        return {
            "is_matrix_script": True,
            "plan_status_code": PLAN_PENDING_UPSTREAM,
            "plan_status_label_zh": _PLAN_STATUS_LABEL[PLAN_PENDING_UPSTREAM],
            "scene_count": 0,
            "scenes": [],
            "active_shot_id": None,
            "current_shot": None,
        }

    active_id = plan_shots[0].shot_id
    scenes: List[Dict[str, Any]] = []
    current_shot: Optional[Dict[str, Any]] = None
    for ps in plan_shots:
        card = card_by_id.get(ps.shot_id, {})
        status_zh = _current_generation_status_zh(card)
        is_active = ps.shot_id == active_id
        scenes.append({
            "scene_index": ps.order,
            "shot_id": ps.shot_id,
            "shot_label_zh": _shot_label(ps.shot_id),
            "title_zh": ps.title_zh,
            "status_chip_zh": status_zh,
            "is_active": is_active,
            "flagged": bool(card.get("suggested_for_handling")),
        })
        if is_active:
            current_shot = _build_current_shot(ps, card, status_zh)

    return {
        "is_matrix_script": True,
        "plan_status_code": PLAN_RESOLVED_PLACEHOLDER,
        "plan_status_label_zh": _PLAN_STATUS_LABEL[PLAN_RESOLVED_PLACEHOLDER],
        "scene_count": len(scenes),
        "scenes": scenes,
        "active_shot_id": active_id,
        "current_shot": current_shot,
    }
