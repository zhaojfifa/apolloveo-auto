"""Hot Follow subtitle and route-state helper cluster.

This module hosts the non-route subtitle/currentness helpers that were
previously embedded inside ``hot_follow_api.py``.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from gateway.app.config import get_settings
from gateway.app.core.workspace import Workspace, task_base_dir
from gateway.app.services.artifact_storage import (
    get_object_bytes,
    object_exists,
    object_head,
    upload_task_artifact,
)
from gateway.app.services.hot_follow_language_profiles import (
    hot_follow_internal_lang,
    hot_follow_subtitle_filename,
    hot_follow_subtitle_txt_filename,
)
from gateway.app.services.hot_follow_subtitle_currentness import (
    compute_hot_follow_target_subtitle_currentness,
    has_semantic_target_subtitle_text,
)
from gateway.app.services.hot_follow_helper_translation import helper_translate_lane_state
from gateway.app.services.media_validation import media_meta_from_head, deliver_key
from gateway.app.services.task_view_helpers import task_key
from gateway.app.services.tts_policy import normalize_target_lang
from gateway.app.steps.subtitles import _parse_srt_to_segments, segments_to_srt
from gateway.app.services.steps_v1 import _srt_to_txt
from gateway.app.providers.gemini_subtitles import translate_segments_with_gemini
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)


def _read_text_file(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _local_target_subtitle_path(task_id: str, target_lang: str | None) -> Path | None:
    try:
        workspace = Workspace(task_id, target_lang=hot_follow_internal_lang(target_lang or "mm"))
        return workspace.mm_srt_path
    except Exception:
        return None


def _local_origin_subtitle_path(task_id: str) -> Path | None:
    try:
        workspace = Workspace(task_id)
        return workspace.origin_srt_path
    except Exception:
        return None


def hf_is_srt_text(text: str) -> bool:
    source = str(text or "").strip()
    if not source or "-->" not in source:
        return False
    try:
        segments = _parse_srt_to_segments(source)
    except Exception:
        return False
    return bool(segments)


def hf_plain_text_to_single_srt(text: str, *, duration_sec: float | None) -> str:
    content_lines = [str(line or "").rstrip() for line in str(text or "").splitlines()]
    content = "\n".join(line for line in content_lines if line.strip()).strip()
    if not content:
        return ""
    try:
        dur = float(duration_sec) if duration_sec is not None else 0.0
    except Exception:
        dur = 0.0
    if dur <= 0:
        dur = 8.0
    dur = max(2.0, min(dur, 60.0))
    seg = {
        "index": 1,
        "start": 0.0,
        "end": dur,
        "mm": content,
        "origin": content,
    }
    return segments_to_srt([seg], "mm")


def hf_normalize_subtitles_save_text(task: dict, raw_text: str) -> tuple[str, str]:
    text = str(raw_text or "").strip()
    if not text:
        return "", "empty"
    if hf_is_srt_text(text):
        return text + ("\n" if not text.endswith("\n") else ""), "srt"
    return hf_plain_text_to_single_srt(text, duration_sec=task.get("duration_sec")) + "\n", "plain_text_wrapped"


def hf_text_for_script_analysis(text: str) -> str:
    source = str(text or "")
    if not source:
        return ""
    lines: list[str] = []
    for raw_line in source.splitlines():
        line = str(raw_line or "").strip()
        if not line:
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def hf_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    normalized_lang = normalize_target_lang(target_lang or "my")
    content = hf_text_for_script_analysis(text)
    if normalized_lang not in {"my", "mm"} or not content:
        return {"allow": True, "reason": None, "message": None}
    myanmar_matches = re.findall(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]", content)
    cjk_matches = re.findall(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]", content)
    latin_matches = re.findall(r"[A-Za-z]", content)
    total = len(myanmar_matches) + len(cjk_matches) + len(latin_matches)
    if total <= 0:
        return {"allow": True, "reason": None, "message": None}
    myanmar_ratio = len(myanmar_matches) / total
    non_myanmar = len(cjk_matches) + len(latin_matches)
    mostly_non_myanmar = non_myanmar >= max(4, len(myanmar_matches))
    if myanmar_ratio < 0.6 and mostly_non_myanmar and non_myanmar > 0:
        return {
            "allow": False,
            "reason": "target_lang_mismatch",
            "message": "当前文本尚未翻译为缅语，不建议直接生成缅语配音。请先翻译为缅语并保存字幕成品，或直接走字幕版合成。",
            "myanmar_ratio": myanmar_ratio,
        }
    return {"allow": True, "reason": None, "message": None, "myanmar_ratio": myanmar_ratio}


def hf_translate_plain_lines(text: str, *, target_lang: str) -> str:
    lines = str(text or "").splitlines()
    segments: list[dict[str, Any]] = []
    mapping: list[int | None] = []
    for line in lines:
        content = str(line or "")
        if content.strip():
            idx = len(segments) + 1
            segments.append({"index": idx, "origin": content.strip()})
            mapping.append(idx)
        else:
            mapping.append(None)
    if not segments:
        return ""
    translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
    out: list[str] = []
    for line, idx in zip(lines, mapping):
        if idx is None:
            out.append("")
        else:
            out.append(str(translations.get(idx) or line or "").strip())
    return "\n".join(out)


def hf_state_from_status(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in {"ready", "done", "success", "completed"}:
        return "done"
    if v in {"running", "processing", "queued"}:
        return "running"
    if v in {"failed", "error"}:
        return "failed"
    return "pending"


def hf_done_like(value: Any) -> bool:
    return str(value or "").strip().lower() in {"done", "ready", "success", "completed"}


def hf_parse_artifact_ready(task: dict) -> bool:
    if not isinstance(task, dict):
        return False

    if task.get("raw_url"):
        return True

    raw_key = task_key(task, "raw_path") or task_key(task, "raw_key")
    if raw_key:
        return True

    source_video = task.get("source_video")
    if isinstance(source_video, dict) and source_video.get("url"):
        return True

    media = task.get("media")
    if isinstance(media, dict) and (media.get("raw_url") or media.get("source_video_url")):
        return True

    deliverables = task.get("deliverables")
    if isinstance(deliverables, dict):
        raw_deliverable = deliverables.get("raw_video") or deliverables.get("raw") or deliverables.get("source_video")
        if isinstance(raw_deliverable, dict) and (
            hf_done_like(raw_deliverable.get("status") or raw_deliverable.get("state"))
            or raw_deliverable.get("url")
            or raw_deliverable.get("key")
        ):
            return True
    elif isinstance(deliverables, list):
        for item in deliverables:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip().lower()
            if kind not in {"raw_video", "raw", "source_video"}:
                continue
            if hf_done_like(item.get("status") or item.get("state")) or item.get("url") or item.get("key"):
                return True

    pipeline = task.get("pipeline")
    parse_row = None
    if isinstance(pipeline, dict):
        parse_row = pipeline.get("parse")
    elif isinstance(pipeline, list):
        parse_row = next(
            (
                item
                for item in pipeline
                if isinstance(item, dict) and str(item.get("key") or "").strip().lower() == "parse"
            ),
            None,
        )
    if isinstance(parse_row, dict):
        message = str(parse_row.get("message") or parse_row.get("summary") or "").strip().lower()
        if "raw=ready" in message:
            return True

    pipeline_legacy = task.get("pipeline_legacy")
    if isinstance(pipeline_legacy, dict):
        parse_legacy = pipeline_legacy.get("parse")
        if isinstance(parse_legacy, dict):
            message = str(parse_legacy.get("message") or parse_legacy.get("summary") or "").strip().lower()
            if "raw=ready" in message:
                return True

    return False


def hf_subtitles_override_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "subtitles" / "subtitles_override.srt"


def hf_expected_subtitle_filename(target_lang: str | None) -> str:
    return hot_follow_subtitle_filename(target_lang or "mm")


def hf_task_target_subtitle_key(task: dict, target_lang: str | None) -> str | None:
    expected_name = hf_expected_subtitle_filename(target_lang)
    lang_norm = hot_follow_internal_lang(target_lang)
    candidates = [
        task_key(task, f"{lang_norm}_srt_path"),
        task_key(task, "mm_srt_path"),
    ]
    for key in candidates:
        if key and Path(str(key)).name == expected_name:
            return str(key)
    return None


def hf_subtitle_content_hash(text: str | None) -> str | None:
    source = "" if text is None else str(text)
    if not source:
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def hf_load_subtitles_text(task_id: str, task: dict) -> str:
    override_path = hf_subtitles_override_path(task_id)
    if override_path.exists():
        return _read_text_file(override_path)

    target_lang = task.get("target_lang") or task.get("content_lang") or "mm"
    mm_key = hf_task_target_subtitle_key(task, target_lang) or task_key(task, "mm_srt_path")
    if mm_key and object_exists(mm_key):
        data = get_object_bytes(mm_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    local_target_path = _local_target_subtitle_path(task_id, target_lang)
    local_text = _read_text_file(local_target_path)
    if local_text:
        return local_text
    return ""


def hf_load_origin_subtitles_text(task: dict) -> str:
    task_id = str(task.get("task_id") or task.get("id") or "")
    origin_key = task_key(task, "origin_srt_path")
    if origin_key and object_exists(origin_key):
        data = get_object_bytes(origin_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    if task_id:
        local_origin_path = _local_origin_subtitle_path(task_id)
        local_text = _read_text_file(local_origin_path)
        if local_text:
            return local_text
    return ""


def hf_subtitle_terminal_success(subtitle_lane: dict[str, Any] | None) -> bool:
    lane = subtitle_lane if isinstance(subtitle_lane, dict) else {}
    return bool(
        lane.get("target_subtitle_authoritative_source")
        and lane.get("target_subtitle_current")
        and lane.get("subtitle_ready")
        and str(lane.get("edited_text") or "").strip()
        and str(lane.get("srt_text") or "").strip()
        and str(lane.get("primary_editable_text") or "").strip()
    )


def hf_load_normalized_source_text(task_id: str, task: dict) -> str:
    try:
        normalized_path = task_base_dir(task_id) / "subs" / "origin_normalized.srt"
    except Exception:
        logger.warning("HF_NORMALIZED_SOURCE_FALLBACK task=%s", task_id)
        return hf_load_origin_subtitles_text(task)
    if normalized_path.exists():
        try:
            return normalized_path.read_text(encoding="utf-8")
        except Exception:
            return normalized_path.read_text(encoding="utf-8", errors="ignore")
    return hf_load_origin_subtitles_text(task)


def hf_dub_input_text(task_id: str, task: dict) -> str:
    edited = hf_load_subtitles_text(task_id, task)
    if has_semantic_target_subtitle_text(edited):
        return edited
    return ""


def hf_target_subtitle_currentness_state(
    task: dict,
    *,
    target_lang: str,
    raw_source_text: str,
    normalized_source_text: str,
    edited_text: str,
    subtitle_artifact_exists: bool,
    expected_key: str | None,
) -> dict[str, object]:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    return compute_hot_follow_target_subtitle_currentness(
        target_lang=target_lang,
        target_text=edited_text,
        source_texts=(normalized_source_text, raw_source_text),
        subtitle_artifact_exists=subtitle_artifact_exists,
        expected_subtitle_source=hf_expected_subtitle_filename(target_lang),
        actual_subtitle_source=(Path(str(expected_key)).name if expected_key else None),
        translation_incomplete=str(pipeline_config.get("translation_incomplete") or "").strip().lower() == "true",
        has_saved_revision=bool(
            str(task.get("subtitles_content_hash") or "").strip()
            or str(task.get("subtitles_override_updated_at") or "").strip()
        ),
    )


def hf_sync_saved_target_subtitle_artifact(task_id: str, task: dict, saved_text: str | None = None) -> str | None:
    text = str(saved_text if saved_text is not None else hf_load_subtitles_text(task_id, task) or "")
    if not has_semantic_target_subtitle_text(text):
        return None
    desired_hash = hf_subtitle_content_hash(text)
    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    current_key = hf_task_target_subtitle_key(task, target_lang) or task_key(task, "mm_srt_path")
    subtitle_filename = hot_follow_subtitle_filename(target_lang)
    subtitle_txt_filename = hot_follow_subtitle_txt_filename(target_lang)
    if current_key and object_exists(str(current_key)):
        head = object_head(str(current_key))
        size, _ = media_meta_from_head(head)
        if int(size or 0) > 0:
            current_bytes = get_object_bytes(str(current_key))
            current_text = None
            if current_bytes:
                try:
                    current_text = current_bytes.decode("utf-8")
                except Exception:
                    current_text = current_bytes.decode("utf-8", errors="ignore")
            current_hash = hf_subtitle_content_hash(current_text)
            if desired_hash and current_hash == desired_hash:
                return str(current_key)
    if not text.strip():
        return str(current_key) if current_key else None

    workspace = Workspace(task_id, target_lang=target_lang)
    workspace.mm_srt_path.parent.mkdir(parents=True, exist_ok=True)
    workspace.mm_srt_path.write_text(text, encoding="utf-8")
    synced_key = upload_task_artifact(task, workspace.mm_srt_path, subtitle_filename, task_id=task_id)
    mm_txt_text = _srt_to_txt(text).strip()
    if mm_txt_text:
        mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
        mm_txt_path.write_text(mm_txt_text + "\n", encoding="utf-8")
        upload_task_artifact(task, mm_txt_path, subtitle_txt_filename, task_id=task_id)
    if synced_key and isinstance(task, dict):
        task["mm_srt_path"] = synced_key
    return str(synced_key) if synced_key else (str(current_key) if current_key else None)


def hf_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    raw_source_text = hf_load_origin_subtitles_text(task)
    normalized_source_text = hf_load_normalized_source_text(task_id, task)
    edited_text = hf_load_subtitles_text(task_id, task)
    srt_text = edited_text or ""
    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    expected_key = hf_task_target_subtitle_key(task, target_lang) or task_key(task, "mm_srt_path")
    composed_key = str(task.get("final_source_subtitle_storage_key") or "").strip() or None
    actual_burn_subtitle_source = (
        Path(composed_key).name
        if composed_key
        else (hf_expected_subtitle_filename(target_lang) if expected_key else None)
    )
    local_target_path = _local_target_subtitle_path(task_id, target_lang)
    subtitle_artifact_physical_exists = bool(
        (expected_key and object_exists(str(expected_key)))
        or (local_target_path and local_target_path.exists())
    )
    target_text_has_semantics = has_semantic_target_subtitle_text(edited_text)
    subtitle_artifact_exists = bool(subtitle_artifact_physical_exists and target_text_has_semantics)
    primary_editable_text = edited_text if target_text_has_semantics else ""
    target_currentness = hf_target_subtitle_currentness_state(
        task,
        target_lang=target_lang,
        raw_source_text=raw_source_text or "",
        normalized_source_text=normalized_source_text or "",
        edited_text=edited_text or "",
        subtitle_artifact_exists=subtitle_artifact_exists,
        expected_key=expected_key,
    )
    subtitle_ready = bool(target_currentness.get("target_subtitle_current"))
    subtitle_ready_reason = str(
        target_currentness.get("target_subtitle_current_reason")
        or ("ready" if subtitle_ready else "subtitle_missing")
    )
    explicit_target_reason = str(task.get("target_subtitle_current_reason") or "").strip()
    translation_waiting = bool(
        not subtitle_ready
        and (
            str(target_currentness.get("target_subtitle_current_reason") or "").strip() == "target_subtitle_translation_incomplete"
            or explicit_target_reason == "target_subtitle_translation_incomplete"
            or str(pipeline_config.get("translation_incomplete") or "").strip().lower() == "true"
        )
        and str(normalized_source_text or raw_source_text or "").strip()
    )
    helper_lane = helper_translate_lane_state(
        task,
        translation_waiting=translation_waiting,
        helper_source_text=normalized_source_text or raw_source_text,
        helper_output_consumed=bool(
            target_currentness.get("target_subtitle_current")
            and target_currentness.get("target_subtitle_authoritative_source")
            and str(task.get("subtitle_helper_translated_text") or "").strip()
        ),
    )
    helper_translate_failed = bool(helper_lane.get("failed"))
    helper_translate_error_reason = helper_lane.get("reason")
    helper_translate_error_message = helper_lane.get("message")
    helper_translate_pending = bool(
        helper_lane.get("output_state") == "helper_output_pending"
        and not subtitle_ready
        and str(normalized_source_text or raw_source_text or "").strip()
    )
    if explicit_target_reason and explicit_target_reason not in {"ready", "unknown"} and not subtitle_ready and not target_text_has_semantics:
        subtitle_ready_reason = (
            "waiting_for_target_subtitle_translation"
            if explicit_target_reason == "target_subtitle_translation_incomplete" and translation_waiting
            else explicit_target_reason
        )
    elif translation_waiting or helper_translate_pending:
        subtitle_ready_reason = "waiting_for_target_subtitle_translation"
    elif helper_translate_failed and not subtitle_ready and not target_text_has_semantics:
        subtitle_ready_reason = helper_translate_error_reason or "helper_translate_failed"
    target_subtitle_current_reason = str(target_currentness.get("target_subtitle_current_reason") or subtitle_ready_reason)
    if explicit_target_reason and explicit_target_reason not in {"ready", "unknown"} and not subtitle_ready and not target_text_has_semantics:
        target_subtitle_current_reason = explicit_target_reason
    elif helper_translate_pending:
        target_subtitle_current_reason = "target_subtitle_translation_incomplete"
    elif helper_translate_failed and not subtitle_ready and not target_text_has_semantics:
        target_subtitle_current_reason = subtitle_ready_reason
    authoritative_burn_subtitle_source = (
        actual_burn_subtitle_source
        if bool(target_currentness.get("target_subtitle_current"))
        and bool(target_currentness.get("target_subtitle_authoritative_source"))
        else None
    )
    dub_input_text = edited_text if subtitle_ready else ""
    helper_source_text = normalized_source_text or raw_source_text
    parse_source_role = (
        str(pipeline_config.get("parse_source_role") or "").strip()
        or ("subtitle_source_helper" if str(helper_source_text or "").strip() else "none")
    )
    parse_source_authoritative_for_target = (
        str(pipeline_config.get("parse_source_authoritative_for_target") or "")
        .strip()
        .lower()
        == "true"
    )
    return {
        "raw_source_text": raw_source_text or "",
        "normalized_source_text": normalized_source_text or "",
        "parse_source_text": helper_source_text or "",
        "parse_source_role": parse_source_role if str(helper_source_text or "").strip() else "none",
        "parse_source_authoritative_for_target": parse_source_authoritative_for_target,
        "edited_text": primary_editable_text,
        "srt_text": primary_editable_text,
        "primary_editable_text": primary_editable_text,
        "primary_editable_format": "srt",
        "dub_input_text": dub_input_text,
        "dub_input_format": "srt" if hf_is_srt_text(dub_input_text) else "plain_text",
        "dub_input_source": "target_subtitle" if dub_input_text else None,
        "actual_burn_subtitle_source": authoritative_burn_subtitle_source,
        "subtitle_artifact_exists": bool(subtitle_artifact_exists),
        "subtitle_ready": bool(subtitle_ready),
        "subtitle_ready_reason": subtitle_ready_reason,
        "target_subtitle_current": bool(target_currentness.get("target_subtitle_current")),
        "target_subtitle_current_reason": target_subtitle_current_reason,
        "target_subtitle_authoritative_source": bool(target_currentness.get("target_subtitle_authoritative_source")),
        "target_subtitle_source_copy": bool(target_currentness.get("target_subtitle_source_copy")),
        "helper_translate_status": helper_lane.get("status"),
        "helper_translate_output_state": helper_lane.get("output_state"),
        "helper_translate_provider_health": helper_lane.get("provider_health"),
        "helper_translate_composite_state": helper_lane.get("composite_state"),
        "helper_translate_failed": helper_translate_failed,
        "helper_translate_error_reason": helper_translate_error_reason,
        "helper_translate_error_message": helper_translate_error_message,
        "helper_translate_provider": helper_lane.get("provider"),
        "helper_translate_visibility": helper_lane.get("visibility"),
        "helper_translate_retryable": bool(helper_lane.get("retryable")),
        "helper_translate_terminal": bool(helper_lane.get("terminal")),
        "helper_translate_warning_only": bool(helper_lane.get("warning_only")),
        "helper_translate_input_text": helper_lane.get("input_text"),
        "helper_translate_translated_text": helper_lane.get("translated_text"),
        "helper_translate_target_lang": helper_lane.get("target_lang"),
    }


def hf_dual_channel_state(
    task_id: str,
    task: dict,
    subtitle_lane: dict[str, Any] | None = None,
    *,
    subtitles_step_done: bool = True,
) -> dict[str, Any]:
    lane = subtitle_lane or hf_subtitle_lane_state(task_id, task)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    raw_text = str(lane.get("raw_source_text") or "")
    normalized_text = str(lane.get("normalized_source_text") or "")
    has_text = bool(normalized_text.strip() or raw_text.strip())
    no_subtitles = pipeline_config.get("no_subtitles") == "true"
    title_hint = str(task.get("title") or "").lower()
    speech_detected = has_text and not no_subtitles
    speech_confidence = "high" if speech_detected else "none"
    subtitle_stream = pipeline_config.get("subtitle_stream") == "true"
    onscreen_text_detected = bool(subtitle_stream or (not speech_detected and has_text))
    onscreen_text_density = "high" if onscreen_text_detected and len(normalized_text.strip() or raw_text.strip()) >= 20 else ("low" if onscreen_text_detected else "none")
    subtitle_still_pending = not subtitles_step_done and not has_text and not no_subtitles
    if speech_detected:
        content_mode = "voice_led"
    elif subtitle_still_pending:
        content_mode = "voice_led"
        speech_detected = True
        speech_confidence = "pending"
    elif onscreen_text_detected:
        content_mode = "subtitle_led"
    else:
        content_mode = "silent_candidate"
    _silent_kw_raw = getattr(get_settings(), "hot_follow_silent_keywords", "") or "asmr,无人声,涂抹音"
    _silent_keywords = [k.strip().lower() for k in _silent_kw_raw.split(",") if k.strip()]
    if any(kw in title_hint for kw in _silent_keywords):
        speech_detected = False
        speech_confidence = "none"
        content_mode = "silent_candidate" if not onscreen_text_detected else "subtitle_led"
    recommended_path = (
        "Voice dubbing"
        if content_mode == "voice_led"
        else ("OCR subtitle translation candidate" if content_mode == "subtitle_led" else "Manual text input required")
    )
    return {
        "speech_detected": bool(speech_detected),
        "speech_confidence": speech_confidence,
        "onscreen_text_detected": bool(onscreen_text_detected),
        "onscreen_text_density": onscreen_text_density,
        "content_mode": content_mode,
        "recommended_path": recommended_path,
    }


def hot_follow_dub_route_state(
    task_id: str,
    task: dict[str, Any],
    *,
    mm_text_override: str | None = None,
    subtitle_lane_loader=None,
    dual_channel_loader=None,
) -> dict[str, Any]:
    subtitle_lane = (subtitle_lane_loader or hf_subtitle_lane_state)(task_id, task)
    route_state = (dual_channel_loader or hf_dual_channel_state)(task_id, task, subtitle_lane)
    lane_text = str(subtitle_lane.get("dub_input_text") or "").strip()
    override_text = str(mm_text_override or "").strip()
    dub_input_text = override_text or lane_text
    no_dub_candidate = (
        route_state.get("content_mode") in {"silent_candidate", "subtitle_led"}
        and not override_text
        and not lane_text
    )
    return {
        "subtitle_lane": subtitle_lane,
        "route_state": route_state,
        "dub_input_text": dub_input_text,
        "no_dub_candidate": no_dub_candidate,
    }


def hot_follow_no_dub_updates(route_state: dict[str, Any]) -> dict[str, Any]:
    reason = str(route_state.get("dub_skip_reason") or "").strip()
    return {
        "last_step": "dub",
        "dub_status": "skipped",
        "dub_error": None,
        "compose_status": "pending",
        "pipeline_config_updates": {
            "no_dub": "true",
            "dub_skip_reason": reason or (
                "subtitle_led"
                if route_state.get("content_mode") == "subtitle_led"
                else "no_speech_detected"
            ),
        },
    }


def hf_allow_subtitle_only_compose(task_id: str, task: dict) -> bool:
    if str(task.get("kind") or "").strip().lower() != "hot_follow":
        return False
    subtitle_lane = hf_subtitle_lane_state(task_id, task)
    route_state = hf_dual_channel_state(task_id, task, subtitle_lane)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    no_dub = pipeline_config.get("no_dub") == "true"
    no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip().lower()
    if no_dub and no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}:
        return True
    no_dub = no_dub or bool(
        str(route_state.get("content_mode") or "").strip().lower() == "silent_candidate"
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    return bool(
        subtitle_lane.get("subtitle_ready")
        and (str(route_state.get("content_mode") or "").strip().lower() == "silent_candidate" or no_dub)
        and (
            not bool(route_state.get("speech_detected"))
            or str(task.get("dub_skip_reason") or "").strip().lower() == "no_speech_detected"
        )
    )


def normalize_compose_target_lang(value: str | None) -> str:
    return hot_follow_internal_lang(value or "mm")


def resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    lang_norm = normalize_compose_target_lang(lang)
    if lang_norm == "vi":
        explicit_current = task_obj.get("target_subtitle_current")
        if explicit_current is False:
            return None
        if explicit_current is not True:
            subtitle_lane = hf_subtitle_lane_state(task_code, task_obj)
            if not bool(subtitle_lane.get("target_subtitle_current")):
                return None
    synced_mm_key = hf_sync_saved_target_subtitle_artifact(task_code, task_obj)
    subtitle_filename = hot_follow_subtitle_filename(lang_norm)
    candidates: list[str] = []
    current_target_key = hf_task_target_subtitle_key(task_obj, lang_norm)
    if current_target_key:
        candidates.append(str(current_target_key))
    if lang_norm == "my":
        if synced_mm_key:
            candidates.append(str(synced_mm_key))
        mm_path = task_key(task_obj, "mm_srt_path")
        if mm_path:
            candidates.append(str(mm_path))
        candidates.append(deliver_key(task_code, subtitle_filename))
    else:
        lang_path = task_key(task_obj, f"{lang_norm}_srt_path")
        if lang_path:
            candidates.append(str(lang_path))
        candidates.append(deliver_key(task_code, subtitle_filename))
        if synced_mm_key:
            candidates.append(str(synced_mm_key))
        mm_path = task_key(task_obj, "mm_srt_path")
        if mm_path:
            candidates.append(str(mm_path))
        candidates.append(deliver_key(task_code, "mm.srt"))
    for key in candidates:
        if key and object_exists(str(key)):
            return str(key)
    return None
