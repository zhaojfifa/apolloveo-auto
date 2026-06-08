"""Matrix Script — Storyboard Control + Shot Workbench wave PR-2.

Prompt Builder (pure, deterministic) + AI 生成要求 / 负面约束 panel projection.
Builds THREE audience-separated outputs; the operator surface shows only the
operator-safe (a) + diagnostic (c); the provider payload (b) is runtime-transient
and NOT surfaced. No provider call, no leak, no vendor, no raw URL/handle.

Import-light (no ``gateway.app.main`` import) — runs on the project ``.venv``.
"""
from __future__ import annotations

from typing import Any, Dict

from gateway.app.services.matrix_script import generation_plan_view as gen_plan
from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import prompt_builder as pb
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

_SHOTS = list(plan_mod.TOMATO_SHOTS)
_PRODUCT_SHOT = _SHOTS[1]   # shot02 小番茄产品特写
_LIFESTYLE_SHOT = _SHOTS[3]  # shot04 品尝爆汁


# --- Determinism ------------------------------------------------------------ #

def test_prompt_builder_is_deterministic() -> None:
    kwargs = dict(
        visual_goal=_PRODUCT_SHOT.visual_intent_zh,
        narration_line=_PRODUCT_SHOT.voiceover_zh,
        motion_instruction="缓慢推近",
        material_role=pb.ROLE_PRODUCT,
        aspect_ratio="9:16",
    )
    a = pb.build_shot_prompt(**kwargs)
    b = pb.build_shot_prompt(**kwargs)
    assert a == b


# --- Tomato product close-up ------------------------------------------------ #

def test_product_close_up_prompt() -> None:
    out = pb.build_shot_prompt(
        visual_goal=_PRODUCT_SHOT.visual_intent_zh,
        motion_instruction="缓慢推近",
        material_role=pb.ROLE_PRODUCT,
        aspect_ratio="9:16",
    )
    # (a) operator-safe AI 生成要求 / 负面约束
    assert _PRODUCT_SHOT.visual_intent_zh in out["operator_requirement_zh"]
    assert "缓慢推近" in out["operator_requirement_zh"]
    assert "保持产品形状、颜色与质感真实" in out["operator_requirement_zh"]
    assert "竖屏 9:16" in out["operator_requirement_zh"]
    assert "变形" in out["operator_negative_zh"] and "水印" in out["operator_negative_zh"]
    # (b) provider payload (runtime-transient)
    assert "slow push-in" in out["provider_prompt"]
    assert "faithful" in out["provider_prompt"] and "cinematic" in out["provider_prompt"]
    assert "distortion" in out["provider_negative_prompt"] and "watermark" in out["provider_negative_prompt"]
    assert out["material_role_resolved"] == pb.ROLE_PRODUCT


# --- Lifestyle eating tomato ------------------------------------------------ #

def test_lifestyle_eating_prompt() -> None:
    out = pb.build_shot_prompt(
        visual_goal=_LIFESTYLE_SHOT.visual_intent_zh,
        material_role=pb.ROLE_CHARACTER,
        aspect_ratio="9:16",
    )
    assert "保持人物自然" in out["operator_requirement_zh"]
    assert "面部扭曲" in out["operator_negative_zh"]
    assert "keep the person natural" in out["provider_prompt"]
    assert "face distortion" in out["provider_negative_prompt"]
    # Distinct from the product prompt.
    assert out["provider_prompt"] != pb.build_shot_prompt(
        visual_goal=_PRODUCT_SHOT.visual_intent_zh, material_role=pb.ROLE_PRODUCT
    )["provider_prompt"]


# --- Material role tolerated (even before PR-3 binding) --------------------- #

def test_material_role_tolerated() -> None:
    # None → role-agnostic but still meaningful.
    none_out = pb.build_shot_prompt(visual_goal="测试镜头", material_role=None)
    assert "保持画面真实自然" in none_out["operator_requirement_zh"]
    assert none_out["material_role_resolved"] is None
    # Unknown role → treated as None (no crash).
    unknown_out = pb.build_shot_prompt(visual_goal="测试镜头", material_role="not_a_role")
    assert unknown_out["material_role_resolved"] is None
    # Each known role is accepted.
    for role in (pb.ROLE_PRODUCT, pb.ROLE_CHARACTER, pb.ROLE_SCENE,
                 pb.ROLE_STYLE, pb.ROLE_REPLACEMENT, pb.ROLE_BROLL):
        out = pb.build_shot_prompt(visual_goal="测试镜头", material_role=role)
        assert out["material_role_resolved"] == role
        assert out["operator_requirement_zh"].endswith("。")


# --- No leakage ------------------------------------------------------------- #

_LEAK_TOKENS = ("akool", "azure", "gemini", "seedance", "veo", "://", "http",
                "x-api-key", "bearer ", "msmaterial://", "asset://", "local_path",
                "provider_url", "vendor", "model_id", "credit")


def test_operator_outputs_have_no_leak() -> None:
    out = pb.build_shot_prompt(
        visual_goal=_PRODUCT_SHOT.visual_intent_zh,
        material_role=pb.ROLE_PRODUCT,
        selected_material_label="圣女果碗",
    )
    for field in ("operator_requirement_zh", "operator_negative_zh", "diagnostic_summary_zh"):
        blob = out[field].lower()
        for tok in _LEAK_TOKENS:
            assert tok not in blob, "leak %r in %s" % (tok, field)


def test_provider_payload_has_no_secret_or_url() -> None:
    out = pb.build_shot_prompt(visual_goal="测试镜头", material_role=pb.ROLE_PRODUCT)
    for field in ("provider_prompt", "provider_negative_prompt"):
        blob = out[field].lower()
        for tok in ("://", "http", "x-api-key", "bearer ", "akool", "azure", "gho_"):
            assert tok not in blob, "leak %r in %s" % (tok, field)


# --- Panel render shows operator-safe text (provider payload NOT surfaced) --- #

def _overlay_plan(task: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(task)["generation_plan"]


def test_panel_shows_real_ai_requirement_and_negative() -> None:
    plan = _overlay_plan({"task_id": "ms-pb-1", "kind": "matrix_script", "config": {}})
    cs = plan["current_shot"]
    first = _SHOTS[0]
    assert cs["ai_requirement_status_code"] == gen_plan.AI_REQUIREMENT_READY
    assert cs["negative_status_code"] == gen_plan.NEGATIVE_READY
    assert first.visual_intent_zh in cs["ai_requirement_zh"]
    assert "竖屏 9:16" in cs["ai_requirement_zh"]
    assert "水印" in cs["negative_constraint_zh"]
    assert cs["ai_requirement_source"] == gen_plan.AI_REQUIREMENT_SOURCE_SYSTEM


def test_provider_payload_not_surfaced_in_view() -> None:
    plan = _overlay_plan({"task_id": "ms-pb-2", "kind": "matrix_script", "config": {}})
    cs = plan["current_shot"]
    assert "provider_prompt" not in cs and "provider_negative_prompt" not in cs
    # Provider-only English tokens must not appear anywhere in the rendered plan.
    blob = str(plan).lower()
    for tok in ("cinematic", "realistic lighting", "://", "http"):
        assert tok not in blob, "provider payload leaked into view: %r" % tok


# --- 改写生成要求 (projection / read side) ---------------------------------- #

def test_operator_rewrite_override_is_honored() -> None:
    task = {
        "task_id": "ms-pb-3", "kind": "matrix_script",
        "config": {gen_plan.GENERATION_REQUIREMENT_OVERRIDE_KEY: {
            _SHOTS[0].shot_id: {"requirement_zh": "运营自定义生成要求：更暖的色调。",
                                 "negative_zh": "避免冷色调"},
        }},
    }
    cs = _overlay_plan(task)["current_shot"]
    assert cs["ai_requirement_source"] == gen_plan.AI_REQUIREMENT_SOURCE_REWRITE
    assert cs["ai_requirement_zh"] == "运营自定义生成要求：更暖的色调。"
    assert cs["negative_constraint_zh"] == "避免冷色调"


def test_dirty_override_is_ignored_falls_back_to_system() -> None:
    task = {
        "task_id": "ms-pb-4", "kind": "matrix_script",
        "config": {gen_plan.GENERATION_REQUIREMENT_OVERRIDE_KEY: {
            _SHOTS[0].shot_id: {"requirement_zh": "see http://evil.example/leak akool"},
        }},
    }
    cs = _overlay_plan(task)["current_shot"]
    # Unsafe override dropped → system-generated text used; no leak surfaced.
    assert cs["ai_requirement_source"] == gen_plan.AI_REQUIREMENT_SOURCE_SYSTEM
    assert "http" not in cs["ai_requirement_zh"].lower()
    assert "akool" not in cs["ai_requirement_zh"].lower()
