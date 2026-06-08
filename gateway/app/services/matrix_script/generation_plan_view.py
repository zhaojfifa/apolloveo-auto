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
from gateway.app.services.matrix_script import prompt_builder

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
# (PR-2 wires AI 生成要求 / 负面约束 + the 改写 projection, so the rewrite line moves
# out of the status-only set into a dedicated rewrite note below.)
PENDING_ACTIONS_ZH = (
    "重新生成这个镜头：后续接入",
    "接受这个镜头：后续接入",
)
REPLACE_MATERIAL_HINT_ZH = "替换素材：见下方“背景、素材、配乐调整”的逐镜素材区。"

# PR-2: AI 生成要求 / 负面约束 are now built by the Prompt Builder (real, not placeholder).
AI_REQUIREMENT_READY = "ai_requirement_ready"
NEGATIVE_READY = "negative_ready"
# 改写生成要求 — projection / read side only. An additive task.config key holds an
# operator rewrite; the WRITE route is deferred to a later slice (no route/schema/
# contract change here). Same additive-config pattern as the material-intent key.
GENERATION_REQUIREMENT_OVERRIDE_KEY = "matrix_script_generation_requirement_overrides"
AI_REQUIREMENT_SOURCE_SYSTEM = "system_generated"
AI_REQUIREMENT_SOURCE_REWRITE = "operator_rewrite"
_REWRITE_NOTE_SYSTEM_ZH = "改写生成要求：当前为系统生成；改写写入路径将在后续接入。"
_REWRITE_NOTE_OPERATOR_ZH = "改写生成要求：已采用你的改写版本。"
# Defensive: a rewrite override must be leak-clean to be honored (keeps the rendered
# field clean without weakening the view-level _assert_clean scan).
_OVERRIDE_FORBIDDEN = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor", "model_id",
    "credit", "provider_task_id", "publish_url", "publish_status", "://", "http",
)

# PR-3: material-role binding. Each shot gets a deterministic default role (Owner
# tomato binding); an operator override may rebind it via an additive task.config
# key (write route deferred). The resolved role feeds the Prompt Builder and drives
# the role chip + the role-specific AI 生成要求 / 负面约束. Closed role set lives in
# prompt_builder.ROLES; the friendly chip labels in prompt_builder.ROLE_LABEL_ZH.
MATERIAL_ROLE_BINDING_KEY = "matrix_script_material_role_bindings"
ROLE_BOUND = "material_role_bound"
ROLE_SOURCE_SYSTEM = "system_derived"
ROLE_SOURCE_OPERATOR = "operator"
_ROLE_CHIP_FALLBACK_ZH = "通用素材"


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


def _derive_motion_zh(ps: Any) -> str:
    """Deterministic default motion from the shot's Ken-Burns zoom (PR-2 input to the
    Prompt Builder). This is NOT the operator-editable 画面动作 field (a later slice)."""
    zoom = getattr(ps, "zoom", None)
    try:
        start, end = float(zoom[0]), float(zoom[1])
    except (TypeError, ValueError, IndexError):
        return "自然轻微运镜"
    if end > start:
        return "缓慢推近"
    if end < start:
        return "缓慢拉远"
    return "轻微运镜"


def _clean_override_text(value: Any) -> Optional[str]:
    """Return an operator-rewrite string only if present and leak-clean; else None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    low = text.lower()
    if any(tok in low for tok in _OVERRIDE_FORBIDDEN):
        return None
    return text[:600]


def _default_role_for_shot(ps: Any) -> str:
    """Deterministic default material role per shot (Owner tomato binding).

    02_tomato_bowl.png = product_reference; beach / hook = scene_reference; the
    eating/lifestyle shot (shot04) = character_reference; other product shots =
    product_reference. Derived from the fixed shot plan only — no provider, no I/O.
    """
    asset = str(getattr(ps, "asset_filename", "") or "").lower()
    sid = str(getattr(ps, "shot_id", ""))
    if "beach" in asset or "hook" in asset:
        return prompt_builder.ROLE_SCENE
    if sid == "shot04":
        return prompt_builder.ROLE_CHARACTER
    if "tomato" in asset or "pick" in asset:
        return prompt_builder.ROLE_PRODUCT
    return prompt_builder.ROLE_PRODUCT


def _role_bindings(task: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Operator material-role rebindings from task.config (projection / read side)."""
    cfg = task.get("config") if isinstance(task, Mapping) else None
    raw = cfg.get(MATERIAL_ROLE_BINDING_KEY) if isinstance(cfg, Mapping) else None
    return raw if isinstance(raw, Mapping) else {}


def _resolve_role(ps: Any, bindings: Mapping[str, Any]) -> "tuple":
    """Resolve (role, source): a valid operator override wins, else the default."""
    override = bindings.get(ps.shot_id) if isinstance(bindings, Mapping) else None
    if prompt_builder.normalize_role(override):
        return override, ROLE_SOURCE_OPERATOR
    return _default_role_for_shot(ps), ROLE_SOURCE_SYSTEM


def _build_current_shot(
    ps: Any,
    card: Mapping[str, Any],
    status_zh: str,
    *,
    resolved_role: str,
    role_source: str,
    override: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """The single active shot's §7 panel.

    PR-3: the resolved material role (system-derived default or a clean operator
    rebinding) feeds the Prompt Builder, so AI 生成要求 / 负面约束 are role-specific; a
    clean operator rewrite still overrides the text (改写生成要求 read side). 画面动作
    remains an honest placeholder (later slice). The provider payload (b) is built
    but is NOT placed on the view (runtime-transient; never surfaced) — no provider
    call here.
    """
    built = prompt_builder.build_shot_prompt(
        visual_goal=ps.visual_intent_zh,
        narration_line=ps.voiceover_zh,
        script_segment=ps.subtitle_zh,
        motion_instruction=_derive_motion_zh(ps),
        material_role=resolved_role,
        aspect_ratio="9:16",
    )
    ov = override if isinstance(override, Mapping) else {}
    req_override = _clean_override_text(ov.get("requirement_zh"))
    neg_override = _clean_override_text(ov.get("negative_zh"))
    requirement_zh = req_override or built["operator_requirement_zh"]
    negative_zh = neg_override or built["operator_negative_zh"]
    is_rewrite = bool(req_override or neg_override)
    source = AI_REQUIREMENT_SOURCE_REWRITE if is_rewrite else AI_REQUIREMENT_SOURCE_SYSTEM
    rewrite_note = _REWRITE_NOTE_OPERATOR_ZH if is_rewrite else _REWRITE_NOTE_SYSTEM_ZH
    return {
        "shot_id": ps.shot_id,
        "shot_label_zh": _shot_label(ps.shot_id),
        "scene_index": ps.order,
        "title_zh": ps.title_zh,
        # 镜头目标 / 旁白 / 字幕重点 — projection of the script-derived shot fields.
        "visual_goal_zh": ps.visual_intent_zh,
        "narration_zh": ps.voiceover_zh,
        "subtitle_focus_zh": ps.subtitle_zh,
        # 画面动作 — still an honest placeholder (later slice).
        "motion_instruction_zh": _PLACEHOLDER_ZH[MOTION_PENDING],
        "motion_status_code": MOTION_PENDING,
        # 素材角色 — PR-3: bound (system-derived default or a clean operator rebinding).
        "material_role_zh": prompt_builder.ROLE_LABEL_ZH.get(resolved_role, _ROLE_CHIP_FALLBACK_ZH),
        "material_role_code": resolved_role,
        "material_role_status_code": ROLE_BOUND,
        "material_role_source": role_source,
        # AI 生成要求 / 负面约束 — PR-2: real Prompt Builder output (or a clean rewrite).
        "ai_requirement_zh": requirement_zh,
        "ai_requirement_status_code": AI_REQUIREMENT_READY,
        "ai_requirement_source": source,
        "negative_constraint_zh": negative_zh,
        "negative_status_code": NEGATIVE_READY,
        "rewrite_requirement_note_zh": rewrite_note,
        "generation_diagnostic_zh": built["diagnostic_summary_zh"],
        # 当前生成状态 — projection of the existing per-shot status.
        "current_generation_status_zh": status_zh,
        # Status-only follow-up actions (no dead control, gate spec WB-4).
        "pending_actions_zh": list(PENDING_ACTIONS_ZH),
        "replace_material_hint_zh": REPLACE_MATERIAL_HINT_ZH,
    }


def _requirement_overrides(task: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Operator generation-requirement rewrites from task.config (projection / read)."""
    cfg = task.get("config") if isinstance(task, Mapping) else None
    raw = cfg.get(GENERATION_REQUIREMENT_OVERRIDE_KEY) if isinstance(cfg, Mapping) else None
    return raw if isinstance(raw, Mapping) else {}


def derive_matrix_script_generation_plan_view(
    *,
    shots: Optional[Sequence[Mapping[str, Any]]] = None,
    task: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Project the storyboard queue + single active Current Shot Work Panel.

    ``shots`` are the already-built overlay cards. Script-derived intent fields
    are read from the fixed shot plan (``plan_mod.TOMATO_SHOTS``) by shot id; the
    active shot's AI 生成要求 / 负面约束 are built by the Prompt Builder (PR-2), with
    a clean operator rewrite from ``task.config`` honored when present. Projection
    only — no provider call, no new truth. The active shot is the first shot
    (order 1); exactly one shot is active.
    """
    card_by_id: Dict[str, Mapping[str, Any]] = {
        str(c.get("shot_id")): c for c in (shots or []) if isinstance(c, Mapping)
    }
    overrides = _requirement_overrides(task)
    role_bindings = _role_bindings(task)
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
        resolved_role, role_source = _resolve_role(ps, role_bindings)
        scenes.append({
            "scene_index": ps.order,
            "shot_id": ps.shot_id,
            "shot_label_zh": _shot_label(ps.shot_id),
            "title_zh": ps.title_zh,
            "status_chip_zh": status_zh,
            "is_active": is_active,
            "flagged": bool(card.get("suggested_for_handling")),
            # PR-3: friendly material-role chip on each queue row.
            "role_chip_zh": prompt_builder.ROLE_LABEL_ZH.get(resolved_role, _ROLE_CHIP_FALLBACK_ZH),
            "material_role_code": resolved_role,
        })
        if is_active:
            current_shot = _build_current_shot(
                ps, card, status_zh,
                resolved_role=resolved_role, role_source=role_source,
                override=overrides.get(ps.shot_id),
            )

    return {
        "is_matrix_script": True,
        "plan_status_code": PLAN_RESOLVED_PLACEHOLDER,
        "plan_status_label_zh": _PLAN_STATUS_LABEL[PLAN_RESOLVED_PLACEHOLDER],
        "scene_count": len(scenes),
        "scenes": scenes,
        "active_shot_id": active_id,
        "current_shot": current_shot,
    }
