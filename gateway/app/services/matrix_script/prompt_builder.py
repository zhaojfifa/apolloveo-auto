"""Matrix Script — Prompt Builder (Storyboard Control wave PR-2).

PURE, DETERMINISTIC. Turns one shot's script-derived intent + (optional) material
role into THREE audience-separated outputs:

  (a) operator-safe **AI 生成要求** + **负面约束** (operator language; no vendor /
      secret / raw provider URL / raw handle) — what the Current Shot Panel renders.
  (b) **provider payload** prompt + negative prompt — runtime-transient, returned
      for a future slice (PR-4) to feed the provider; **never surfaced to the
      operator** by this module's callers.
  (c) operator-language **diagnostic summary** one-liner (queue / J).

PR-2 builds (a) and (c) for the panel and RETURNS (b); it makes **NO provider
call** and surfaces NO (b). No network, no secret, no clock, no randomness —
same inputs → same outputs (Owner test: determinism). The ``material_role`` input
is tolerated (recognized roles add role-specific preservation + negatives; an
unknown / absent role falls back to role-agnostic, still-meaningful clauses).

Authority: ``MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_20260608`` §8;
alignment §10. NO Akool, NO route, NO schema/contract change.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Closed material-role set (mirrors generation_plan_view §9; PR-3 binds them).
ROLE_PRODUCT = "product_reference"
ROLE_CHARACTER = "character_reference"
ROLE_SCENE = "scene_reference"
ROLE_STYLE = "style_reference"
ROLE_REPLACEMENT = "replacement_image"
ROLE_BROLL = "broll_candidate"
_ROLES = (ROLE_PRODUCT, ROLE_CHARACTER, ROLE_SCENE, ROLE_STYLE, ROLE_REPLACEMENT, ROLE_BROLL)

_ROLE_LABEL_ZH = {
    ROLE_PRODUCT: "产品素材",
    ROLE_CHARACTER: "人物素材",
    ROLE_SCENE: "场景素材",
    ROLE_STYLE: "风格参考",
    ROLE_REPLACEMENT: "替换图",
    ROLE_BROLL: "空镜",
}
_ROLE_PRESERVE_ZH = {
    ROLE_PRODUCT: "保持产品形状、颜色与质感真实，不变形",
    ROLE_CHARACTER: "保持人物自然，手部与面部正常",
    ROLE_SCENE: "保持场景与背景的环境连续性",
    ROLE_STYLE: "沿用参考的画面风格与色调",
    ROLE_REPLACEMENT: "依据替换图生成，尊重其构图",
    ROLE_BROLL: "作为补充空镜，非主体",
}
_ROLE_PRESERVE_EN = {
    ROLE_PRODUCT: "keep the product's shape, color and texture faithful, no distortion",
    ROLE_CHARACTER: "keep the person natural, normal hands and face",
    ROLE_SCENE: "preserve scene and background environment continuity",
    ROLE_STYLE: "match the reference visual style and palette",
    ROLE_REPLACEMENT: "animate per the replacement image, honor its framing",
    ROLE_BROLL: "supplemental cutaway b-roll, not the hero subject",
}
_ROLE_NEGATIVE_ZH = {
    ROLE_PRODUCT: ["变形", "扭曲", "改变标签"],
    ROLE_CHARACTER: ["面部扭曲", "多指"],
    ROLE_SCENE: ["场景错乱"],
    ROLE_STYLE: ["风格漂移"],
    ROLE_REPLACEMENT: ["偏离原图构图"],
    ROLE_BROLL: ["喧宾夺主"],
}
_ROLE_NEGATIVE_EN = {
    ROLE_PRODUCT: ["distortion", "warping", "label change"],
    ROLE_CHARACTER: ["face distortion", "extra fingers"],
    ROLE_SCENE: ["scene inconsistency"],
    ROLE_STYLE: ["style drift"],
    ROLE_REPLACEMENT: ["framing deviation"],
    ROLE_BROLL: ["overpowering the subject"],
}

# Role-agnostic fallback (PR-2 live panel: no role bound until PR-3).
_DEFAULT_PRESERVE_ZH = "保持画面真实自然、光线真实"
_DEFAULT_PRESERVE_EN = "keep the scene natural and realistic, realistic lighting"
_DEFAULT_LABEL_ZH = "通用"

# Global negatives (always appended).
_GLOBAL_NEGATIVE_ZH = ["文字", "水印", "标志", "过曝"]
_GLOBAL_NEGATIVE_EN = ["text", "watermark", "logo", "oversaturation"]

# Motion zh → en (the few derived / common values). Unknown falls back honestly.
_MOTION_DEFAULT_ZH = "自然轻微运镜"
_MOTION_EN = {
    "缓慢推近": "slow push-in",
    "缓慢拉远": "slow pull-out",
    "轻微运镜": "subtle camera motion",
    "自然轻微运镜": "subtle natural camera motion",
}

_DEFAULT_ASPECT = "9:16"


def _norm_role(material_role: Optional[str]) -> Optional[str]:
    return material_role if material_role in _ROLES else None


def _aspect(value: Optional[str]) -> str:
    v = (value or "").strip()
    return v or _DEFAULT_ASPECT


def _aspect_zh(aspect: str) -> str:
    return "竖屏 9:16" if aspect == "9:16" else ("画幅 " + aspect)


def _aspect_en(aspect: str) -> str:
    return "vertical 9:16" if aspect == "9:16" else (aspect + " aspect")


def _short(text: str, limit: int = 12) -> str:
    t = (text or "").strip()
    return t if len(t) <= limit else (t[:limit] + "…")


def build_shot_prompt(
    *,
    visual_goal: str,
    narration_line: str = "",
    script_segment: str = "",
    motion_instruction: str = "",
    material_role: Optional[str] = None,
    selected_material_label: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    aspect_ratio: str = _DEFAULT_ASPECT,
) -> Dict[str, Any]:
    """Build the three audience-separated prompt outputs for one shot (pure)."""
    role = _norm_role(material_role)
    goal = (visual_goal or "").strip()
    motion_zh = (motion_instruction or "").strip() or _MOTION_DEFAULT_ZH
    motion_en = _MOTION_EN.get(motion_zh, "subtle camera motion")
    aspect = _aspect(aspect_ratio)
    preserve_zh = _ROLE_PRESERVE_ZH[role] if role else _DEFAULT_PRESERVE_ZH
    preserve_en = _ROLE_PRESERVE_EN[role] if role else _DEFAULT_PRESERVE_EN
    role_label = _ROLE_LABEL_ZH[role] if role else _DEFAULT_LABEL_ZH

    # (a) operator-safe AI 生成要求 / 负面约束 (operator language only).
    req_parts = [p for p in (goal, motion_zh, preserve_zh, _aspect_zh(aspect)) if p]
    operator_requirement_zh = "；".join(req_parts) + "。"
    neg_zh: List[str] = list(_ROLE_NEGATIVE_ZH.get(role, [])) + _GLOBAL_NEGATIVE_ZH
    operator_negative_zh = "、".join(neg_zh)

    # (b) provider payload (runtime-transient; NOT surfaced to the operator).
    provider_parts = [p for p in (goal, motion_en, preserve_en, "cinematic, realistic lighting", _aspect_en(aspect)) if p]
    provider_prompt = ", ".join(provider_parts)
    provider_negative_prompt = ", ".join(list(_ROLE_NEGATIVE_EN.get(role, [])) + _GLOBAL_NEGATIVE_EN)

    # (c) operator-language diagnostic one-liner.
    diagnostic_summary_zh = " · ".join([_short(goal), role_label, motion_zh])

    return {
        "operator_requirement_zh": operator_requirement_zh,
        "operator_negative_zh": operator_negative_zh,
        "provider_prompt": provider_prompt,
        "provider_negative_prompt": provider_negative_prompt,
        "diagnostic_summary_zh": diagnostic_summary_zh,
        "material_role_resolved": role,
        "aspect_ratio": aspect,
    }
