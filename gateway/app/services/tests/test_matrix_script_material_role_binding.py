"""Matrix Script — Storyboard Control + Shot Workbench wave PR-3.

Material role binding: each shot gets a deterministic default role (Owner tomato
binding), an operator may rebind via an additive task.config key, and the resolved
role feeds the Prompt Builder so AI 生成要求 / 负面约束 become role-specific. A
friendly role chip shows in the queue + Current Shot Panel. No raw handle / URL /
local path; no provider call.

Import-light (no ``gateway.app.main`` import) — runs on the project ``.venv``.
"""
from __future__ import annotations

from typing import Any, Dict

from gateway.app.services.matrix_script import generation_plan_view as gen_plan
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import prompt_builder as pb
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

_SHOTS = list(plan_mod.TOMATO_SHOTS)
_BY_ID = {s.shot_id: s for s in _SHOTS}


def _overlay_plan(config: Dict[str, Any] = None) -> Dict[str, Any]:
    task = {"task_id": "ms-role-1", "kind": "matrix_script", "config": config or {}}
    return owv.build_matrix_script_operator_workbench_view(task)["generation_plan"]


def _scene(plan: Dict[str, Any], shot_id: str) -> Dict[str, Any]:
    return next(s for s in plan["scenes"] if s["shot_id"] == shot_id)


# --- Deterministic default role per shot (Owner tomato binding) ------------- #

def test_default_role_for_each_shot() -> None:
    assert gen_plan._default_role_for_shot(_BY_ID["shot01"]) == pb.ROLE_SCENE      # beach hook
    assert gen_plan._default_role_for_shot(_BY_ID["shot02"]) == pb.ROLE_PRODUCT    # 02_tomato_bowl
    assert gen_plan._default_role_for_shot(_BY_ID["shot03"]) == pb.ROLE_PRODUCT    # pick tomato
    assert gen_plan._default_role_for_shot(_BY_ID["shot04"]) == pb.ROLE_CHARACTER  # eating/lifestyle
    assert gen_plan._default_role_for_shot(_BY_ID["shot05"]) == pb.ROLE_PRODUCT    # 02_tomato_bowl reuse


def test_tomato_bowl_is_product_reference() -> None:
    # Owner mandate: 02_tomato_bowl.png = product_reference (shot02 + shot05 reuse).
    for sid in ("shot02", "shot05"):
        assert _BY_ID[sid].asset_filename == "02_tomato_bowl.png"
        assert gen_plan._default_role_for_shot(_BY_ID[sid]) == pb.ROLE_PRODUCT


# --- Prompt Builder role behavior (each role its own preserve + negative) --- #

def test_each_role_drives_distinct_preserve_and_negative() -> None:
    expect = {
        pb.ROLE_PRODUCT: ("保持产品形状", "变形"),
        pb.ROLE_CHARACTER: ("保持人物自然", "面部扭曲"),
        pb.ROLE_SCENE: ("保持场景与背景的环境连续性", "场景错乱"),
        pb.ROLE_STYLE: ("沿用参考的画面风格", "风格漂移"),
        pb.ROLE_REPLACEMENT: ("依据替换图生成", "偏离原图构图"),
        pb.ROLE_BROLL: ("作为补充空镜", "喧宾夺主"),
    }
    for role, (preserve, neg) in expect.items():
        out = pb.build_shot_prompt(visual_goal="测试镜头", material_role=role)
        assert preserve in out["operator_requirement_zh"], role
        assert neg in out["operator_negative_zh"], role


# --- generation_plan_view: role bound + chip + role-driven requirement ------ #

def test_active_shot_role_is_bound_with_chip() -> None:
    plan = _overlay_plan()
    cs = plan["current_shot"]  # active = shot01 → scene_reference
    assert cs["material_role_status_code"] == gen_plan.ROLE_BOUND
    assert cs["material_role_code"] == pb.ROLE_SCENE
    assert cs["material_role_zh"] == pb.ROLE_LABEL_ZH[pb.ROLE_SCENE] == "场景素材"
    assert cs["material_role_source"] == gen_plan.ROLE_SOURCE_SYSTEM
    # Role drives the operator-safe AI 生成要求 / 负面约束.
    assert "保持场景与背景的环境连续性" in cs["ai_requirement_zh"]
    assert "场景错乱" in cs["negative_constraint_zh"]


def test_queue_rows_carry_role_chip() -> None:
    plan = _overlay_plan()
    assert _scene(plan, "shot02")["role_chip_zh"] == "产品素材"
    assert _scene(plan, "shot02")["material_role_code"] == pb.ROLE_PRODUCT
    assert _scene(plan, "shot01")["role_chip_zh"] == "场景素材"
    assert _scene(plan, "shot04")["material_role_code"] == pb.ROLE_CHARACTER


# --- Operator rebinding (projection / read side) ---------------------------- #

def test_operator_role_override_rebinds() -> None:
    cfg = {gen_plan.MATERIAL_ROLE_BINDING_KEY: {"shot01": pb.ROLE_PRODUCT}}
    cs = _overlay_plan(cfg)["current_shot"]
    assert cs["material_role_code"] == pb.ROLE_PRODUCT
    assert cs["material_role_source"] == gen_plan.ROLE_SOURCE_OPERATOR
    assert "保持产品形状" in cs["ai_requirement_zh"]
    assert "变形" in cs["negative_constraint_zh"]


def test_invalid_role_override_falls_back_to_default() -> None:
    cfg = {gen_plan.MATERIAL_ROLE_BINDING_KEY: {"shot01": "not_a_role"}}
    cs = _overlay_plan(cfg)["current_shot"]
    assert cs["material_role_code"] == pb.ROLE_SCENE  # default for shot01
    assert cs["material_role_source"] == gen_plan.ROLE_SOURCE_SYSTEM


# --- No leak / provider payload still not surfaced -------------------------- #

def test_role_binding_has_no_leak_and_no_provider_payload() -> None:
    plan = _overlay_plan({gen_plan.MATERIAL_ROLE_BINDING_KEY: {"shot01": pb.ROLE_PRODUCT}})
    blob = str(plan).lower()
    for tok in owv._FORBIDDEN_TOKENS:
        assert tok not in blob, "forbidden token %r in plan" % tok
    for tok in ("://", "http", "msmaterial://", "asset://", "local_path",
                "cinematic", "realistic lighting", "azure", "gemini"):
        assert tok not in blob, "unexpected token %r in plan" % tok
    cs = plan["current_shot"]
    assert "provider_prompt" not in cs and "provider_negative_prompt" not in cs


# --- PR-1 / PR-2 behavior preserved ----------------------------------------- #

def test_pr1_pr2_behavior_preserved() -> None:
    plan = _overlay_plan()
    cs = plan["current_shot"]
    # PR-1: queue + single active panel; PR-2: AI 生成要求 / 负面约束 READY.
    assert plan["scene_count"] == len(_SHOTS)
    assert len([s for s in plan["scenes"] if s["is_active"]]) == 1
    assert cs["ai_requirement_status_code"] == gen_plan.AI_REQUIREMENT_READY
    assert cs["negative_status_code"] == gen_plan.NEGATIVE_READY
    # 画面动作 still a placeholder (later slice).
    assert cs["motion_status_code"] == gen_plan.MOTION_PENDING
    # Invariants.
    view = owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-role-2", "kind": "matrix_script", "config": {}}
    )
    assert view["delivery"]["official_publish_ready"] is False
