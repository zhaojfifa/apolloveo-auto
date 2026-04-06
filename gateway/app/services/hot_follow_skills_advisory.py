from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from gateway.app.lines.base import ProductionLine
from gateway.app.services.hot_follow_language_profiles import hot_follow_subtitle_filename
from gateway.app.services.line_binding_service import get_line_runtime_binding


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HotFollowSkillsBundle:
    bundle_id: str
    line_id: str
    bundle_ref: str
    hook_kind: str


HOT_FOLLOW_ADVISORY_BUNDLE = HotFollowSkillsBundle(
    bundle_id="hot_follow_advisory_v0",
    line_id="hot_follow_line",
    bundle_ref="docs/skills/",
    hook_kind="advisory",
)


def resolve_hot_follow_skills_bundle(line: ProductionLine | None) -> HotFollowSkillsBundle | None:
    if line is None:
        return None
    if line.line_id != HOT_FOLLOW_ADVISORY_BUNDLE.line_id:
        return None
    if str(line.skills_bundle_ref or "").strip() != HOT_FOLLOW_ADVISORY_BUNDLE.bundle_ref:
        return None
    return HOT_FOLLOW_ADVISORY_BUNDLE


def build_hot_follow_advisory_input(
    task: dict[str, Any],
    payload: dict[str, Any],
    *,
    line: ProductionLine | None,
) -> dict[str, Any]:
    line_metadata: dict[str, Any] | None = None
    if line is not None:
        line_metadata = {
            "line_id": line.line_id,
            "line_name": line.line_name,
            "line_version": line.line_version,
            "task_kind": line.task_kind,
            "skills_bundle_ref": line.skills_bundle_ref,
        }
    return {
        "task": dict(task or {}),
        "line": line_metadata,
        "ready_gate": dict(payload.get("ready_gate") or {}),
        "pipeline": payload.get("pipeline") or [],
        "pipeline_legacy": dict(payload.get("pipeline_legacy") or {}),
        "deliverables": payload.get("deliverables") or [],
        "media": dict(payload.get("media") or {}),
        "source_video": dict(payload.get("source_video") or {}),
        "artifact_facts": dict(payload.get("artifact_facts") or {}),
        "current_attempt": dict(payload.get("current_attempt") or {}),
        "operator_summary": dict(payload.get("operator_summary") or {}),
    }


def _evidence(**kwargs: Any) -> dict[str, Any]:
    evidence = {}
    for key, value in kwargs.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        evidence[key] = value
    return evidence


def _build_hot_follow_advisory_v0(advisory_input: dict[str, Any]) -> dict[str, Any] | None:
    ready_gate = dict(advisory_input.get("ready_gate") or {})
    artifact_facts = dict(advisory_input.get("artifact_facts") or {})
    current_attempt = dict(advisory_input.get("current_attempt") or {})
    operator_summary = dict(advisory_input.get("operator_summary") or {})

    subtitle_ready = bool(ready_gate.get("subtitle_ready"))
    subtitle_ready_reason = str(ready_gate.get("subtitle_ready_reason") or "").strip() or None
    audio_ready = bool(current_attempt.get("audio_ready") or ready_gate.get("audio_ready"))
    audio_ready_reason = str(
        current_attempt.get("audio_ready_reason") or ready_gate.get("audio_ready_reason") or ""
    ).strip() or None
    compose_ready = bool(ready_gate.get("compose_ready"))
    publish_ready = bool(ready_gate.get("publish_ready"))
    blocking = list(ready_gate.get("blocking") or [])
    final_exists = bool(artifact_facts.get("final_exists"))
    subtitle_exists = bool(artifact_facts.get("subtitle_exists"))
    audio_exists = bool(artifact_facts.get("audio_exists"))
    requires_recompose = bool(current_attempt.get("requires_recompose"))
    compose_status = str(current_attempt.get("compose_status") or "").strip().lower() or None
    final_stale_reason = str(current_attempt.get("final_stale_reason") or "").strip() or None
    current_subtitle_source = str(current_attempt.get("current_subtitle_source") or "").strip() or None
    expected_subtitle_source = hot_follow_subtitle_filename(
        advisory_input.get("task", {}).get("target_lang") or advisory_input.get("task", {}).get("content_lang") or "mm"
    )

    if current_subtitle_source and current_subtitle_source != expected_subtitle_source:
        return {
            "id": "hf_advisory_subtitle_source_mismatch",
            "kind": "operator_guidance",
            "level": "warning",
            "recommended_next_action": "review_subtitles",
            "operator_hint": "subtitle review recommended",
            "explanation": f"当前烧录字幕来源不是主可编辑字幕 {expected_subtitle_source}，建议先确认主字幕对象再继续当前链路。",
            "evidence": _evidence(
                current_subtitle_source=current_subtitle_source,
                expected_subtitle_source=expected_subtitle_source,
                subtitle_exists=subtitle_exists,
                subtitle_ready=subtitle_ready,
            ),
        }

    if requires_recompose:
        return {
            "id": "hf_advisory_recompose_required",
            "kind": "operator_guidance",
            "level": "warning",
            "recommended_next_action": "recompose_final",
            "operator_hint": "recompose recommended",
            "explanation": "当前字幕或配音已更新，建议重新合成最终视频以生成最新版本。",
            "evidence": _evidence(
                final_exists=final_exists,
                compose_status=compose_status,
                final_stale_reason=final_stale_reason,
                blocking=blocking,
            ),
        }

    if subtitle_ready and audio_ready and not final_exists:
        return {
            "id": "hf_advisory_compose_missing_final",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "recompose_final",
            "operator_hint": "recompose recommended",
            "explanation": "当前字幕和配音都已就绪，但还没有可用成片，建议执行重新合成。",
            "evidence": _evidence(
                subtitle_ready=subtitle_ready,
                audio_ready=audio_ready,
                final_exists=final_exists,
                blocking=blocking,
            ),
        }

    if subtitle_ready and not audio_ready:
        return {
            "id": "hf_advisory_refresh_dub",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "refresh_dub",
            "operator_hint": "dub refresh recommended",
            "explanation": "当前主字幕已具备，但配音尚未准备完成，建议先刷新当前配音。",
            "evidence": _evidence(
                subtitle_ready=subtitle_ready,
                audio_ready=audio_ready,
                audio_ready_reason=audio_ready_reason,
                audio_exists=audio_exists,
                compose_status=compose_status,
            ),
        }

    if not subtitle_ready:
        return {
            "id": "hf_advisory_review_subtitles",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "review_subtitles",
            "operator_hint": "subtitle review recommended",
            "explanation": f"当前主字幕还未准备完成，建议先检查并保存 {expected_subtitle_source} 后再继续后续链路。",
            "evidence": _evidence(
                subtitle_ready=subtitle_ready,
                subtitle_ready_reason=subtitle_ready_reason,
                subtitle_exists=subtitle_exists,
            ),
        }

    if publish_ready and compose_ready and final_exists:
        return {
            "id": "hf_advisory_final_ready",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "continue_qa",
            "operator_hint": "no further action currently required",
            "explanation": "当前成片已可用，可继续做字幕、配音或成片 QA 复核。",
            "evidence": _evidence(
                final_exists=final_exists,
                compose_ready=compose_ready,
                publish_ready=publish_ready,
                last_successful_output_available=operator_summary.get("last_successful_output_available"),
            ),
        }

    return None


def _noop_hot_follow_advisory(_advisory_input: dict[str, Any]) -> dict[str, Any] | None:
    return None


_HOT_FOLLOW_ADVISORY_HOOK: Callable[[dict[str, Any]], dict[str, Any] | None] = _build_hot_follow_advisory_v0


def _normalize_advisory_output(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    advisory = {
        "id": str(value.get("id") or "").strip() or None,
        "kind": str(value.get("kind") or "").strip() or None,
        "level": str(value.get("level") or "").strip() or None,
        "recommended_next_action": value.get("recommended_next_action"),
        "operator_hint": value.get("operator_hint"),
        "explanation": value.get("explanation"),
        "evidence": value.get("evidence"),
    }
    if not any(v is not None and v != "" for v in advisory.values()):
        return None
    return advisory


def maybe_build_hot_follow_advisory(
    task: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    binding = get_line_runtime_binding(task or payload)
    line = binding.line
    bundle = resolve_hot_follow_skills_bundle(line)
    if bundle is None:
        return None
    advisory_input = build_hot_follow_advisory_input(task, payload, line=line)
    try:
        return _normalize_advisory_output(_HOT_FOLLOW_ADVISORY_HOOK(advisory_input))
    except Exception:
        logger.exception(
            "HF_SKILLS_ADVISORY_SAFE_FALLBACK task=%s bundle=%s",
            (task or {}).get("task_id") or (task or {}).get("id"),
            bundle.bundle_id,
        )
        return None
