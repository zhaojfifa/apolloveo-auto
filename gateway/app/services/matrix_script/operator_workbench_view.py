"""Matrix Script Operator Workbench Flow view model (PR-B).

Builds ONE operator-driven view model that links the Main Video Result to the
decisions that produced it — script understanding → storyboard / shot plan →
material & visual assets → character / voice → subtitles / music → variants →
delivery. The Workbench renders this so an operator can see *how the script
produced the video*, instead of isolated contract/technical cards.

This is pure presentation-layer projection (L4):
- Storyboard / materials / script-understanding / variants are derived from the
  fixed tomato plan fixture (PR-A).
- Main result + delivery + per-shot acceptance are derived from the PR-A result
  (the staged candidate / acceptance gate) when present (L2 + L3).
- When no result exists yet, the main result is an honest ``not_generated``
  state — the lower sections still explain the plan that *will* drive it.

Hard boundary: no I/O; no provider/vendor/model/credit; no schema/contract
change; no ``official_publish_ready=true``; the UI invents no truth — every
field is derived from the fixed plan or the result.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping, Optional

from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

LINE_ID = "matrix_script"

STATUS_OPERATOR_USABLE = "operator_usable"
STATUS_TECHNICAL_PREVIEW = "technical_preview"
STATUS_NOT_GENERATED = "not_generated"

_SEMANTIC_PASS = "pass"
_SEMANTIC_PARTIAL = "partial"

# Tokens that must never reach this operator-facing view model.
_FORBIDDEN_TOKENS = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor",
    "model_id", "credit", "provider_task_id", "publish_url", "publish_status",
)


def _truthy(v: Any) -> bool:
    return bool(v) and v not in ("", "false", "False", 0)


def _resolve_result(task: Mapping[str, Any], result: Optional[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    """Result source: explicit arg, else the staged candidate on task config."""
    if isinstance(result, Mapping) and result.get("has_result", True):
        # an explicit result dict (route payload / acceptance) — accept as-is
        if any(k in result for k in ("operator_usable", "delivery_candidate", "visual_semantic_match")):
            return result
    config = task.get("config") if isinstance(task, Mapping) else None
    staged = config.get("matrix_script_staged_candidate") if isinstance(config, Mapping) else None
    if isinstance(staged, Mapping) and staged.get("has_result"):
        return staged
    return None


def _build_main_result(result: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    v1_name = f"V1 {plan_mod.TOMATO_VARIANTS[0]['name']}"
    if not result:
        return {
            "status": STATUS_NOT_GENERATED,
            "status_label_zh": "未生成",
            "current_variant": None,
            "preview_url": None,
            "operator_usable": False,
            "technical_preview": False,
            "visual_semantic_match": None,
            "shot_match_count": 0,
            "shot_count": plan_mod.shot_count(),
            "real_visual_count": 0,
            "delivery_candidate": False,
            "official_publish_ready": False,
            "blocked_reason": None,
            "next_step_zh": "确认脚本、分镜、素材后生成视频",
        }
    operator_usable = _truthy(result.get("operator_usable"))
    technical_preview = _truthy(result.get("technical_preview")) or not operator_usable
    status = STATUS_OPERATOR_USABLE if operator_usable else STATUS_TECHNICAL_PREVIEW
    label = "运营可用" if operator_usable else "技术预览，不可运营"
    return {
        "status": status,
        "status_label_zh": label,
        "current_variant": v1_name if operator_usable else None,
        "preview_url": result.get("preview_url"),
        "operator_usable": operator_usable,
        "technical_preview": technical_preview,
        "visual_semantic_match": result.get("visual_semantic_match"),
        "shot_match_count": int(result.get("shot_match_count", 0) or 0),
        "shot_count": int(result.get("shot_count", plan_mod.shot_count()) or plan_mod.shot_count()),
        "real_visual_count": int(result.get("real_visual_count", 0) or 0),
        "delivery_candidate": _truthy(result.get("delivery_candidate")),
        "official_publish_ready": False,
        "blocked_reason": result.get("blocked_reason") if not operator_usable else None,
        "next_step_zh": None if operator_usable else "补齐真实素材后重新生成",
    }


def _build_storyboard(has_result: bool) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for shot in plan_mod.TOMATO_SHOTS:
        semantic_status = _SEMANTIC_PASS if shot.real_visual else _SEMANTIC_PARTIAL
        cards.append({
            "shot_id": shot.shot_id,
            "order": shot.order,
            "title": shot.title_zh,
            "visual_intent": shot.visual_intent_zh,
            "voiceover": shot.voiceover_zh,
            "subtitle": shot.subtitle_zh,
            "asset_name": shot.asset_filename,
            "source": shot.source,
            "generation_status": "generated" if has_result else "pending",
            "semantic_status": semantic_status,
            "included_in_current_video": bool(has_result),
        })
    return cards


def _build_materials() -> List[Dict[str, Any]]:
    # Group fixed shots by asset file → which shots each asset drives, in first
    # appearance order. All three files are real local photographs (reuse does
    # not change that the underlying material is a real visual asset).
    order: List[str] = []
    by_asset: Dict[str, Dict[str, Any]] = {}
    for shot in plan_mod.TOMATO_SHOTS:
        if shot.asset_filename not in by_asset:
            order.append(shot.asset_filename)
            by_asset[shot.asset_filename] = {
                "asset_name": shot.asset_filename,
                "source": plan_mod.SOURCE_LOCAL_REAL_ASSET,
                "used_by": [],
            }
        by_asset[shot.asset_filename]["used_by"].append(shot.shot_id)
    return [by_asset[name] for name in order]


def _build_voice(env: Optional[Mapping[str, str]]) -> Dict[str, Any]:
    src = env if env is not None else os.environ
    has_azure = bool((src.get("AZURE_SPEECH_KEY") or "").strip()) and bool((src.get("AZURE_SPEECH_REGION") or "").strip())
    if has_azure:
        return {
            "provider": "azure",
            "voice_style": "zh-CN-XiaoxiaoNeural",
            "status": "ready",
            "blocked_reason": None,
            "note_zh": "旁白由 Azure TTS 生成",
        }
    return {
        "provider": "fallback",
        "voice_style": "fallback（静音）",
        "status": "fallback",
        "blocked_reason": "missing_azure_env",
        "note_zh": "旁白状态：待接入 Azure TTS；当前版本字幕承载脚本，音频为 fallback",
    }


def _build_subtitles_music(result: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    caption_mode = (result or {}).get("caption_mode") if isinstance(result, Mapping) else None
    burned = caption_mode != "sidecar_only"  # default burned_in
    return {
        "subtitles": "generated",
        "burned_captions": bool(burned),
        "bgm": "none",
        "music_status": "none/fallback",
    }


def _build_variants(has_result: bool) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for v in plan_mod.TOMATO_VARIANTS:
        status = v["default_status"]
        if v["id"] == "v1":
            status = "generated" if has_result else "ready_to_generate"
        out.append({
            "id": v["id"],
            "name": v["name"],
            "status": status,
            "target_duration": v["target_duration"],
            "shot_strategy": v["shot_strategy"],
            "voice_subtitle_style": v["voice_subtitle_style"],
            "generate_button_state": "regenerate" if (v["id"] == "v1" and has_result)
            else ("generate" if v["id"] == "v1" else "pending"),
            "is_current": v["id"] == "v1" and has_result,
        })
    return out


def _build_script_understanding(task: Mapping[str, Any]) -> Dict[str, Any]:
    # Fixed tomato case fixture; if a task entry carries operator-provided
    # topic/platform, prefer it, else fall back to the fixed case values.
    su = dict(plan_mod.TOMATO_SCRIPT_UNDERSTANDING)
    config = task.get("config") if isinstance(task, Mapping) else None
    entry = config.get("entry") if isinstance(config, Mapping) else None
    if isinstance(entry, Mapping):
        if entry.get("topic"):
            su["topic"] = str(entry["topic"])
        if entry.get("target_platform"):
            su["platform"] = str(entry["target_platform"])
    return su


def _assert_clean(view: Mapping[str, Any]) -> None:
    blob = str(view).lower()
    hits = [t for t in _FORBIDDEN_TOKENS if t in blob]
    if hits:
        raise ValueError(f"operator workbench view leaks forbidden tokens: {hits}")


def build_matrix_script_operator_workbench_view(
    task: Mapping[str, Any],
    *,
    result: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Build the linked operator Workbench view model (script → video)."""
    if not isinstance(task, Mapping):
        task = {}
    resolved = _resolve_result(task, result)
    has_result = resolved is not None
    main_result = _build_main_result(resolved)
    view: Dict[str, Any] = {
        "is_matrix_script": True,
        "case_id": plan_mod.CASE_ID,
        "script_title": plan_mod.SCRIPT_TITLE,
        "main_result": main_result,
        "script_understanding": _build_script_understanding(task),
        "storyboard": _build_storyboard(has_result),
        "materials": _build_materials(),
        "voice": _build_voice(env),
        "subtitles_music": _build_subtitles_music(resolved),
        "variants": _build_variants(has_result),
        "delivery": {
            "candidate_variant": "v1",
            "delivery_candidate": main_result["delivery_candidate"],
            "official_publish_ready": False,
            "preview_url": main_result["preview_url"],
        },
    }
    _assert_clean(view)
    return view
