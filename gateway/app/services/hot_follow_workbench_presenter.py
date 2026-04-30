from __future__ import annotations

import logging
from typing import Any, Callable

from gateway.app.services.hot_follow_route_state import (
    build_hot_follow_artifact_facts as _build_hot_follow_artifact_facts,
    build_hot_follow_current_attempt_summary as _build_hot_follow_current_attempt_summary,
)


logger = logging.getLogger(__name__)


def build_hot_follow_artifact_facts(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
    deliverable_url: Callable[[str, dict, str], str | None],
) -> dict[str, Any]:
    return _build_hot_follow_artifact_facts(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        deliverable_url=deliverable_url,
    )


def build_hot_follow_current_attempt_summary(
    *,
    voice_state: dict[str, Any],
    subtitle_lane: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    final_stale_reason: str | None = None,
    artifact_facts: dict[str, Any] | None = None,
    no_dub: bool = False,
    no_dub_compose_allowed: bool = False,
) -> dict[str, Any]:
    return _build_hot_follow_current_attempt_summary(
        voice_state=voice_state,
        subtitle_lane=subtitle_lane,
        dub_status=dub_status,
        compose_status=compose_status,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
        artifact_facts=artifact_facts,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )


def build_hot_follow_operator_summary(
    *,
    artifact_facts: dict[str, Any],
    current_attempt: dict[str, Any],
    no_dub: bool,
    subtitle_ready: bool = False,
) -> dict[str, Any]:
    last_successful_output_available = bool(artifact_facts.get("final_exists"))
    dub_status = str(current_attempt.get("dub_status") or "").strip().lower()
    compose_status = str(current_attempt.get("compose_status") or "").strip().lower()
    subtitle_translation_waiting_retryable = bool(current_attempt.get("subtitle_translation_waiting_retryable"))
    current_attempt_failed = (
        not subtitle_translation_waiting_retryable
        and (dub_status in {"failed", "error"} or compose_status in {"failed", "error"})
    )
    show_previous_final_as_primary = bool(
        last_successful_output_available
        and not bool(current_attempt.get("audio_ready"))
        and not no_dub
    )
    if subtitle_translation_waiting_retryable:
        recommended_next_action = "目标字幕翻译尚未就绪，当前处于等待/可重试状态；请等待翻译返回或重试字幕步骤后再继续配音。"
    elif current_attempt.get("helper_translate_failed"):
        recommended_next_action = current_attempt.get("helper_translate_error_message") or "翻译助手暂时失败，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。"
    elif current_attempt.get("compose_input_derive_failed_terminal"):
        recommended_next_action = f"当前合成输入派生失败：{current_attempt.get('compose_reason') or 'compose_input_derive_failed'}。请先修复素材或转码配置后再重试合成。"
    elif current_attempt.get("compose_blocked_terminal") or current_attempt.get("compose_input_blocked_terminal"):
        recommended_next_action = f"当前合成输入已被线路策略阻断：{current_attempt.get('compose_reason') or 'compose_input_blocked'}。请调整素材后再尝试合成。"
    elif current_attempt.get("no_dub_route_terminal"):
        recommended_next_action = "当前素材已进入无 TTS 合成路径，可继续合成保留原音或背景音版本。"
    elif no_dub and not subtitle_ready:
        recommended_next_action = "当前素材无可提取字幕，正在等待自动检测完成；也可直接在下方字幕编辑区手工输入缅语文字，保存后即可合成字幕版。"
    elif no_dub:
        recommended_next_action = "当前素材适合字幕驱动路径，可先保存字幕并直接合成字幕版。"
    elif current_attempt.get("requires_redub"):
        recommended_next_action = "当前目标字幕已更新，需重新配音后才能继续合成最新成片。"
    elif current_attempt.get("requires_recompose"):
        recommended_next_action = "当前配音已更新，建议重新合成最终视频以生成最新版本。"
    elif show_previous_final_as_primary and current_attempt_failed:
        recommended_next_action = "当前重配音失败，但上一次成片仍可查看；请先修复当前配音后再重新合成。"
    elif show_previous_final_as_primary:
        recommended_next_action = "当前重配音未完成，上一次成片仍可查看；如需更新版本，请在当前配音完成后重新合成。"
    elif last_successful_output_available:
        recommended_next_action = "当前已有可用成片，可按需继续校对字幕、配音或重新合成。"
    else:
        recommended_next_action = "当前尚无可用成片，请先确保字幕和配音链路完成后再合成。"
    return {
        "last_successful_output_available": last_successful_output_available,
        "current_attempt_failed": current_attempt_failed,
        "show_previous_final_as_primary": show_previous_final_as_primary,
        "recommended_next_action": recommended_next_action,
    }
