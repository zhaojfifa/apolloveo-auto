"""Matrix Script — Storyboard Control + Shot Workbench wave PR-1.

Projection-only Storyboard Queue + single Current Shot Work Panel. The overlay
exposes ``generation_plan``; it must render the §7 operator fields as projection
(镜头目标 / 旁白 / 字幕重点 from the fixed shot plan) or honest placeholder
(画面动作 / 素材角色 / AI 生成要求 / 负面约束), with exactly one active shot,
no provider call, no leak, no second source of truth.

Import-light (no ``gateway.app.main`` import) so it runs on Python 3.9 without
the env-coupled config PEP-604 limitation.

Boundary: Matrix-Script-scoped projection only — no Hot Follow / Digital Anchor /
artifact_storage / schema-contract / Akool / route / provider touched.
"""
from __future__ import annotations

from typing import Any, Dict

from gateway.app.services.matrix_script import generation_plan_view as gen_plan
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

_SHOTS = list(plan_mod.TOMATO_SHOTS)
_REQUIRED_PANEL_FIELDS = (
    "visual_goal_zh",        # 镜头目标
    "motion_instruction_zh",  # 画面动作
    "narration_zh",          # 旁白
    "subtitle_focus_zh",     # 字幕重点
    "material_role_zh",      # 素材角色
    "ai_requirement_zh",     # AI 生成要求
    "negative_constraint_zh",  # 负面约束
    "current_generation_status_zh",  # 当前生成状态
)


def _fresh_task() -> Dict[str, Any]:
    return {"task_id": "ms-gp-1", "kind": "matrix_script", "config": {}}


def _plan_from_overlay() -> Dict[str, Any]:
    view = owv.build_matrix_script_operator_workbench_view(_fresh_task())
    assert view["is_matrix_script"] is True
    plan = view.get("generation_plan")
    assert isinstance(plan, dict), "overlay must expose generation_plan"
    return plan


# --- Storyboard queue ------------------------------------------------------- #

def test_fresh_task_has_storyboard_queue() -> None:
    plan = _plan_from_overlay()
    assert plan["is_matrix_script"] is True
    assert plan["plan_status_code"] == gen_plan.PLAN_RESOLVED_PLACEHOLDER
    assert plan["scene_count"] == len(_SHOTS)
    assert len(plan["scenes"]) == len(_SHOTS)
    # Every queue row carries an operator-language status chip + label.
    for row in plan["scenes"]:
        assert row["shot_label_zh"]
        assert row["title_zh"]
        assert row["status_chip_zh"]


def test_exactly_one_active_shot() -> None:
    plan = _plan_from_overlay()
    active_rows = [s for s in plan["scenes"] if s["is_active"]]
    assert len(active_rows) == 1, "exactly one current shot panel"
    assert active_rows[0]["shot_id"] == plan["active_shot_id"] == _SHOTS[0].shot_id


# --- Current shot panel: §7 fields ------------------------------------------ #

def test_current_shot_panel_has_all_section7_fields() -> None:
    plan = _plan_from_overlay()
    cs = plan["current_shot"]
    assert isinstance(cs, dict)
    for field in _REQUIRED_PANEL_FIELDS:
        assert cs.get(field), "missing §7 field: %s" % field


def test_projected_fields_are_real_script_text() -> None:
    plan = _plan_from_overlay()
    cs = plan["current_shot"]
    first = _SHOTS[0]
    assert cs["visual_goal_zh"] == first.visual_intent_zh
    assert cs["narration_zh"] == first.voiceover_zh
    assert cs["subtitle_focus_zh"] == first.subtitle_zh
    assert cs["title_zh"] == first.title_zh


def test_not_wired_fields_are_honest_placeholders() -> None:
    # 画面动作 remains an honest placeholder (later slice). AI 生成要求 / 负面约束 are
    # real (PR-2); 素材角色 is now bound (PR-3, status ROLE_BOUND).
    plan = _plan_from_overlay()
    cs = plan["current_shot"]
    assert cs["motion_status_code"] == gen_plan.MOTION_PENDING
    assert cs["material_role_status_code"] == gen_plan.ROLE_BOUND
    assert cs["ai_requirement_status_code"] == gen_plan.AI_REQUIREMENT_READY
    assert cs["negative_status_code"] == gen_plan.NEGATIVE_READY


def test_followup_actions_are_status_only_no_dead_control() -> None:
    # Gate spec WB-4: not-yet-wired actions render as status text, never a control.
    plan = _plan_from_overlay()
    cs = plan["current_shot"]
    assert cs["pending_actions_zh"], "status-only follow-up actions present"
    joined = "".join(cs["pending_actions_zh"]) + cs["replace_material_hint_zh"]
    assert "后续接入" in joined


# --- No leak / no provider / no fake media ---------------------------------- #

def test_generation_plan_has_no_forbidden_tokens() -> None:
    plan = _plan_from_overlay()
    blob = str(plan).lower()
    hits = [t for t in owv._FORBIDDEN_TOKENS if t in blob]
    assert not hits, "generation_plan leaks forbidden tokens: %s" % hits


def test_generation_plan_has_no_media_url_or_provider() -> None:
    plan = _plan_from_overlay()
    blob = str(plan).lower()
    for needle in ("http", ".mp4", "<video", "azure", "gemini", "seedance", "veo"):
        assert needle not in blob, "unexpected token in generation_plan: %s" % needle


# --- Direct unit calls (no overlay) ----------------------------------------- #

def test_derive_with_no_cards_still_projects_plan() -> None:
    plan = gen_plan.derive_matrix_script_generation_plan_view(shots=[])
    assert plan["scene_count"] == len(_SHOTS)
    assert plan["current_shot"]["current_generation_status_zh"] == "尚未生成"


def test_derive_with_none_shots_is_safe() -> None:
    plan = gen_plan.derive_matrix_script_generation_plan_view(shots=None)
    assert plan["scene_count"] == len(_SHOTS)
    assert plan["active_shot_id"] == _SHOTS[0].shot_id


# --- Invariants: no delivery/publish mutation ------------------------------- #

def test_overlay_invariants_preserved() -> None:
    view = owv.build_matrix_script_operator_workbench_view(_fresh_task())
    # PR-1 is projection-only: it must not flip publish readiness or delivery.
    assert view["delivery"]["official_publish_ready"] is False
    assert view["main_result"]["official_publish_ready"] is False
    # The existing per-shot material cards are untouched (still present).
    assert isinstance(view["shots"], list) and len(view["shots"]) == len(_SHOTS)
