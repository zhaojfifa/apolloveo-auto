"""CompositionService — extracted from _hf_compose_final_video (TASK-2.0).

Separates pre-validation, FFmpeg execution, and post-persistence into
distinct methods.  Every subprocess.run call goes through _run_ffmpeg()
which enforces a configurable timeout.

Historical bug-fix preservation:
  - datetime: module-level import only, no local shadowing (bb73f5d)
  - empty SRT: subtitle_only_compose guard ported verbatim (267744a)
  - exception cascade: unchanged in caller tasks.py (76e15a3)
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from gateway.app.services.artifact_storage import object_exists, object_head
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.media_helpers import sha256_file
from gateway.app.services.media_validation import (
    MIN_VIDEO_BYTES,
    assert_artifact_ready,
    assert_local_audio_ok,
    assert_local_video_ok,
    deliver_key,
    media_meta_from_head,
)
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.services.voice_state import DRY_TTS_CONFIG_KEY, collect_voice_execution_state
from gateway.app.services.worker_gateway import WorkerExecutionMode, WorkerRequest
from gateway.app.services.worker_gateway_registry import get_worker_gateway
from gateway.app.services.task_view_helpers import task_endpoint, task_key
from gateway.app.core.constants import COMPOSE_RETRY_AFTER_MS
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)

_CJK_CHAR_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_MYANMAR_CHAR_RE = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]")
_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)
_SOURCE_AUDIO_BED_VOLUME_FLOOR = 0.35

# ---------------------------------------------------------------------------
# Module-level pure helpers (extracted from nested functions)
# ---------------------------------------------------------------------------


def _current_final_is_fresh(
    task: dict,
    *,
    revision: dict[str, str | None],
    final_exists: bool,
    final_size: int,
) -> bool:
    """Return True only if the existing final incorporates the current subtitle + audio.

    When True the compose service may safely skip re-running FFmpeg.
    When False compose must run regardless of whether a file physically exists.
    """
    if not final_exists or final_size < MIN_VIDEO_BYTES:
        return False
    compose_last_status = str(
        task.get("compose_last_status") or task.get("compose_status") or ""
    ).strip().lower()
    if compose_last_status not in {"done", "ready", "success", "completed"}:
        return False

    current_audio_sha = str(revision.get("audio_sha256") or "").strip() or None
    current_sub_hash = str(revision.get("subtitle_content_hash") or "").strip() or None
    current_sub_at = str(revision.get("subtitle_updated_at") or "").strip() or None
    current_render_signature = str(revision.get("render_signature") or "").strip() or None
    current_source_audio_policy = str(revision.get("source_audio_policy") or "mute").strip().lower() or "mute"
    current_dub_at = str(task.get("dub_generated_at") or "").strip() or None
    composed_audio_sha = str(task.get("final_source_audio_sha256") or "").strip() or None
    composed_dub_at = str(task.get("final_source_dub_generated_at") or "").strip() or None
    composed_sub_hash = str(task.get("final_source_subtitles_content_hash") or "").strip() or None
    composed_sub_at = str(task.get("final_source_subtitle_updated_at") or "").strip() or None
    composed_render_signature = str(task.get("final_source_render_signature") or "").strip() or None
    composed_source_audio_policy = str(task.get("final_source_audio_policy") or "").strip().lower() or None
    compose_finished_at = str(task.get("compose_last_finished_at") or task.get("final_updated_at") or "").strip() or None

    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    # No compose snapshot → cannot confirm what was baked into the final → recompose.
    if (
        not composed_audio_sha
        and not composed_sub_hash
        and not composed_dub_at
        and not composed_sub_at
        and not composed_render_signature
        and not composed_source_audio_policy
    ):
        return False

    if composed_audio_sha and current_audio_sha and composed_audio_sha != current_audio_sha:
        return False
    if composed_dub_at and current_dub_at and composed_dub_at != current_dub_at:
        return False
    if current_dub_at and compose_finished_at:
        current_dub_dt = _parse_dt(current_dub_at)
        compose_finished_dt = _parse_dt(compose_finished_at)
        if current_dub_dt is not None and compose_finished_dt is not None and current_dub_dt > compose_finished_dt:
            return False
    if composed_sub_hash and current_sub_hash:
        if composed_sub_hash != current_sub_hash:
            return False
    if composed_sub_at and current_sub_at and composed_sub_at != current_sub_at:
        return False
    if composed_render_signature and current_render_signature and composed_render_signature != current_render_signature:
        return False
    if composed_source_audio_policy and composed_source_audio_policy != current_source_audio_policy:
        return False
    if not composed_source_audio_policy and current_source_audio_policy != "mute":
        return False
    if current_sub_at and compose_finished_at:
        current_sub_dt = _parse_dt(current_sub_at)
        compose_finished_dt = _parse_dt(compose_finished_at)
        if current_sub_dt is not None and compose_finished_dt is not None and current_sub_dt > compose_finished_dt:
            return False
    if not composed_sub_hash and not composed_sub_at and current_sub_hash:
        return False
    if not composed_render_signature and current_render_signature:
        return False
    return True


def _subtitle_content_hash(text: str | None) -> str | None:
    source = "" if text is None else str(text)
    if not source:
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _read_text_compat(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def compose_fail(
    reason: str,
    message: str,
    status_code: int = 409,
    *,
    ffmpeg_cmd: str | None = None,
    stderr_tail: str | None = None,
) -> None:
    """Raise HTTPException with structured compose error detail."""
    detail: dict[str, Any] = {"reason": reason, "message": message}
    if ffmpeg_cmd:
        detail["ffmpeg_cmd"] = ffmpeg_cmd
    if stderr_tail:
        detail["stderr_tail"] = stderr_tail
    raise HTTPException(status_code=status_code, detail=detail)


def escape_subtitles_path(path: Path) -> str:
    """Escape a path for use in FFmpeg subtitles filter expressions."""
    raw = str(path).replace("\\", "/")
    return raw.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _feathered_bottom_band_filter(
    *,
    core_start: float,
    core_height: float,
    core_alpha: float,
    feather_bands: list[tuple[float, float, float]],
) -> str:
    filters = [
        (
            "drawbox="
            f"x=0:y=ih*{core_start:.3f}:w=iw:h=ih*{core_height:.3f}:"
            f"color=black@{core_alpha:.2f}:t=fill"
        )
    ]
    for start, height, alpha in feather_bands:
        filters.append(
            "drawbox="
            f"x=0:y=ih*{start:.3f}:w=iw:h=ih*{height:.3f}:"
            f"color=black@{alpha:.2f}:t=fill"
        )
    return ",".join(filters)


def _normalize_layout_lang(target_lang: str | None) -> str:
    raw = str(target_lang or "").strip().lower()
    if raw == "mm":
        return "my"
    return raw or "my"


def _subtitle_layout_profile(target_lang: str | None) -> dict[str, float | str]:
    lang = _normalize_layout_lang(target_lang)
    if lang == "zh":
        return {"font_name": "Noto Sans Myanmar", "font_size": 13.4, "margin_v": 13, "line_width": 11.5, "scale_y": 92}
    if lang == "en":
        return {"font_name": "Noto Sans Myanmar", "font_size": 12.6, "margin_v": 13, "line_width": 24.0, "scale_y": 92}
    if lang == "vi":
        return {"font_name": "Noto Sans Myanmar", "font_size": 12.6, "margin_v": 13, "line_width": 22.0, "scale_y": 92}
    return {"font_name": "Noto Sans Myanmar", "font_size": 13.4, "margin_v": 13, "line_width": 13.0, "scale_y": 92}


def subtitle_render_signature(*, target_lang: str | None, cleanup_mode: str | None) -> str:
    profile = _subtitle_layout_profile(target_lang)
    lang = _normalize_layout_lang(target_lang)
    cleanup = str(cleanup_mode or "none").strip().lower() or "none"
    return "|".join(
        [
            f"lang={lang}",
            f"cleanup={cleanup}",
            f"font={profile['font_name']}",
            f"size={float(profile['font_size']):.1f}",
            f"margin_v={int(profile['margin_v'])}",
            f"scale_y={int(profile['scale_y'])}",
            f"line_width={float(profile['line_width']):.2f}",
            "align=2",
            "wrap=1",
        ]
    )


def _text_display_width(text: str) -> float:
    width = 0.0
    for ch in str(text or ""):
        if not ch or ch.isspace():
            width += 0.35
        elif _CJK_CHAR_RE.match(ch) or _MYANMAR_CHAR_RE.match(ch):
            width += 1.0
        elif ch.isascii() and ch.isalnum():
            width += 0.58
        else:
            width += 0.72
    return width


def _compact_subtitle_text(text: str) -> str:
    lines = [str(line or "").strip() for line in str(text or "").splitlines() if str(line or "").strip()]
    if not lines:
        return ""
    return " ".join(lines)


def _tokenize_subtitle_text(text: str, target_lang: str | None) -> tuple[list[str], str]:
    compact = _compact_subtitle_text(text)
    if not compact:
        return [], "words"
    lang = _normalize_layout_lang(target_lang)
    if lang == "zh":
        return [ch for ch in compact if ch.strip()], "chars"
    if not re.search(r"\s", compact) and (_CJK_CHAR_RE.search(compact) or _MYANMAR_CHAR_RE.search(compact)):
        return [ch for ch in compact if ch.strip()], "chars"
    return compact.split(), "words"


def _join_subtitle_tokens(tokens: list[str], mode: str) -> str:
    if mode == "chars":
        return "".join(tokens).strip()
    return " ".join(token for token in tokens if token).strip()


def _break_bonus(left: str, right: str, mode: str) -> float:
    bonus = 0.0
    if left.endswith(("。", "！", "？", "，", "、", ".", "!", "?", ",", ";", "；", ":", "：")):
        bonus -= 1.2
    if right.startswith(("，", "。", "！", "？", ",", ".", "!", "?", ";", "；", ":", "：")):
        bonus += 0.8
    if mode == "words" and left.endswith(("-", "/")):
        bonus += 0.4
    return bonus


def _best_two_line_layout(text: str, target_lang: str | None) -> str:
    profile = _subtitle_layout_profile(target_lang)
    max_width = float(profile["line_width"])
    tokens, mode = _tokenize_subtitle_text(text, target_lang)
    if not tokens:
        return ""

    single_line = _join_subtitle_tokens(tokens, mode)
    if _text_display_width(single_line) <= max_width:
        return single_line

    best_lines: tuple[str, str] | None = None
    best_penalty: float | None = None
    total_width = _text_display_width(single_line)
    for idx in range(1, len(tokens)):
        left = _join_subtitle_tokens(tokens[:idx], mode)
        right = _join_subtitle_tokens(tokens[idx:], mode)
        if not left or not right:
            continue
        left_width = _text_display_width(left)
        right_width = _text_display_width(right)
        overflow = max(0.0, left_width - max_width) + max(0.0, right_width - max_width)
        penalty = overflow * 12.0 + abs(left_width - right_width) + _break_bonus(left, right, mode)
        if total_width > max_width * 2:
            penalty += max(0.0, total_width - max_width * 2) * 3.0
        if best_penalty is None or penalty < best_penalty:
            best_penalty = penalty
            best_lines = (left, right)

    if best_lines is None:
        return single_line
    return f"{best_lines[0]}\n{best_lines[1]}"


def optimize_hot_follow_subtitle_layout_srt(srt_text: str, target_lang: str | None) -> str:
    blocks = [block for block in str(srt_text or "").split("\n\n") if block.strip()]
    if not blocks:
        return str(srt_text or "")

    normalized_blocks: list[str] = []
    changed = False
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            normalized_blocks.append(block.strip())
            continue
        has_index = lines[0].strip().isdigit()
        index_line = lines[0].strip() if has_index else None
        time_line = lines[1].strip() if has_index else lines[0].strip()
        if not _SRT_TIME_RE.search(time_line):
            normalized_blocks.append(block.strip())
            continue
        text_lines = lines[2:] if has_index else lines[1:]
        wrapped_text = _best_two_line_layout("\n".join(text_lines), target_lang)
        if wrapped_text and wrapped_text != "\n".join(text_lines).strip():
            changed = True
        out_lines: list[str] = []
        if index_line:
            out_lines.append(index_line)
        out_lines.append(time_line)
        if wrapped_text:
            out_lines.extend(wrapped_text.splitlines())
        normalized_blocks.append("\n".join(out_lines))

    result = "\n\n".join(normalized_blocks).strip()
    if not result:
        return str(srt_text or "")
    return result + "\n" if changed or not str(srt_text or "").endswith("\n") else result + "\n"


def source_subtitle_cover_filter(cleanup_mode: str, target_lang: str | None = None) -> str:
    """Return an FFmpeg drawbox filter for subtitle area masking."""
    mode = str(cleanup_mode or "").strip().lower()
    if mode == "bottom_mask":
        return _feathered_bottom_band_filter(
            core_start=0.850,
            core_height=0.150,
            core_alpha=0.68,
            feather_bands=[
                (0.825, 0.025, 0.22),
                (0.803, 0.022, 0.12),
                (0.785, 0.018, 0.06),
            ],
        )
    if mode == "safe_band":
        return _feathered_bottom_band_filter(
            core_start=0.820,
            core_height=0.180,
            core_alpha=0.56,
            feather_bands=[
                (0.790, 0.030, 0.20),
                (0.765, 0.025, 0.10),
                (0.745, 0.020, 0.05),
            ],
        )
    return ""


def compose_subtitle_vf(
    subtitle_path_obj: Path,
    fontsdir: Path,
    cleanup_mode: str,
    target_lang: str | None = None,
) -> str:
    """Build the complete subtitle video-filter string for FFmpeg."""
    profile = _subtitle_layout_profile(target_lang)
    subtitle_filter = (
        f"subtitles='{escape_subtitles_path(subtitle_path_obj)}':"
        "charenc=UTF-8:"
        f"fontsdir='{escape_subtitles_path(Path(fontsdir))}':"
        "force_style='"
        f"FontName={profile['font_name']},"
        f"FontSize={float(profile['font_size']):.1f},"
        "Outline=2,"
        "Shadow=1,"
        f"ScaleY={int(profile['scale_y'])},"
        "Alignment=2,"
        f"MarginV={int(profile['margin_v'])},"
        "WrapStyle=1'"
    )
    cover_filter = source_subtitle_cover_filter(cleanup_mode, target_lang=target_lang)
    return f"{cover_filter},{subtitle_filter}" if cover_filter else subtitle_filter


def _with_live_hot_follow_subtitle_currentness(task_id: str, task: dict) -> dict:
    live_task = dict(task or {})
    if str(live_task.get("kind") or "").strip().lower() != "hot_follow":
        return live_task
    try:
        from gateway.app.services.hot_follow_runtime_bridge import compat_hot_follow_subtitle_lane_state

        subtitle_lane = compat_hot_follow_subtitle_lane_state(task_id, live_task)
    except Exception:
        logger.exception("HF_COMPOSE_SUBTITLE_CURRENTNESS_REFRESH_FAILED", extra={"task_id": task_id})
        return live_task

    live_task["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    live_task["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    return live_task


def _resolve_compose_video_key(task: dict, source_audio_policy: str) -> tuple[str | None, bool]:
    """Resolve compose video input and whether it can provide preserved source audio."""
    raw_key = task_key(task, "raw_path") or task_key(task, "raw_video_key")
    mute_key = task_key(task, "mute_video_key") or task_key(task, "mute_video_path")
    if str(source_audio_policy or "").strip().lower() == "preserve" and raw_key:
        return str(raw_key), True
    if mute_key:
        return str(mute_key), False
    if raw_key:
        return str(raw_key), str(source_audio_policy or "").strip().lower() == "preserve"
    return None, False


def _resolve_compose_voiceover_key(task: dict, voice_state: dict[str, Any]) -> str | None:
    if not bool(voice_state.get("audio_ready")):
        return None
    config = dict(task.get("config") or {})
    dry_audio_key = str(config.get(DRY_TTS_CONFIG_KEY) or "").strip() or None
    if dry_audio_key:
        return dry_audio_key
    legacy_audio_key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
    if not legacy_audio_key:
        return None
    bgm_key = str((dict(config.get("bgm") or {})).get("bgm_key") or "").strip() or None
    source_audio_keys = {
        str(value).strip()
        for value in (
            bgm_key,
            task_key(task, "raw_path"),
            task_key(task, "raw_video_key"),
            task_key(task, "mute_video_key"),
            task_key(task, "mute_video_path"),
        )
        if str(value or "").strip()
    }
    return None if str(legacy_audio_key).strip() in source_audio_keys else str(legacy_audio_key)


def _source_audio_bed_volume(value: float | None) -> float:
    try:
        mix = float(value if value is not None else _SOURCE_AUDIO_BED_VOLUME_FLOOR)
    except Exception:
        mix = _SOURCE_AUDIO_BED_VOLUME_FLOOR
    if mix <= 0:
        return _SOURCE_AUDIO_BED_VOLUME_FLOOR
    return max(0.0, min(1.0, mix))


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ComposeTimeouts:
    """Timeout values (seconds) for each FFmpeg stage."""

    freeze_tail: int = 120
    compose: int = 600
    probe: int = 30
    clamp: int = 120


@dataclass(frozen=True)
class ComposePlan:
    mute: bool = True
    overlay_subtitles: bool = True
    strip_subtitle_streams: bool = True
    cleanup_mode: str = "none"
    target_lang: str = "mm"
    freeze_tail_enabled: bool = False
    freeze_tail_cap_sec: int = 8
    compose_policy: str = "match_video"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mute": self.mute,
            "overlay_subtitles": self.overlay_subtitles,
            "strip_subtitle_streams": self.strip_subtitle_streams,
            "cleanup_mode": self.cleanup_mode,
            "target_lang": self.target_lang,
            "freeze_tail_enabled": self.freeze_tail_enabled,
            "freeze_tail_cap_sec": self.freeze_tail_cap_sec,
            "compose_policy": self.compose_policy,
        }


@dataclass(frozen=True)
class HotFollowComposeRequestContract:
    bgm_mix: float | None = None
    overlay_subtitles: bool | None = None
    freeze_tail_enabled: bool | None = None
    force: bool = False
    expected_subtitle_updated_at: str | None = None
    expected_audio_sha256: str | None = None


@dataclass(frozen=True)
class HotFollowComposeResponseContract:
    status_code: int
    body: dict[str, Any]


@dataclass(frozen=True)
class ComposeResult:
    updates: dict[str, Any]
    final_key: str
    final_url: str
    compose_status: str


@dataclass
class _ComposeInputs:
    """Validated inputs extracted from task dict."""

    video_key: str
    audio_key: str | None
    subtitle_only_compose: bool
    voice_state: dict
    bgm_key: str | None
    bgm_mix: float
    source_audio_policy: str
    source_audio_available: bool
    overlay_subtitles: bool
    strip_subtitle_streams: bool
    cleanup_mode: str
    target_lang: str
    freeze_tail_enabled: bool
    freeze_tail_cap_sec: float
    compose_policy: str
    ffmpeg: str


@dataclass
class _WorkspaceFiles:
    """Mutable workspace state for the compose pipeline."""

    task_id: str
    tmp: Path
    video_input_path: Path
    voice_path: Path | None
    final_path: Path
    subtitle_path: Path | None
    bgm_path: Path | None
    fontsdir: Path
    ffmpeg: str
    video_duration: float
    voice_duration: float
    compose_policy: str
    subtitle_key: str | None = None
    subtitle_object_etag: str | None = None
    subtitle_content_hash: str | None = None
    subtitle_sha256: str | None = None
    compose_warning: str | None = None
    ffmpeg_cmd_used: str | None = None
    overlay_subtitles: bool = True


# ---------------------------------------------------------------------------
# CompositionService
# ---------------------------------------------------------------------------


class CompositionService:
    """Orchestrates the final-video compose pipeline with timeout protection."""

    def __init__(
        self,
        *,
        storage: Any,
        settings: Any,
        timeouts: ComposeTimeouts | None = None,
    ) -> None:
        self._storage = storage
        self._settings = settings
        self._timeouts = timeouts or ComposeTimeouts()

    # ── Public entry point ────────────────────────────────────────────────

    def compose(
        self,
        task_id: str,
        task: dict,
        *,
        subtitle_resolver: Callable[[dict, str, str], str | None],
        subtitle_only_check: Callable[[str, dict], bool],
    ) -> ComposeResult:
        """Run the full compose pipeline and return structured compose output."""
        live_task = _with_live_hot_follow_subtitle_currentness(task_id, task)
        inputs = self._validate_inputs(task_id, live_task, subtitle_only_check)

        compose_started_at = task.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat()

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = self._prepare_workspace(task_id, live_task, inputs, Path(tmpdir), subtitle_resolver)

            # Dispatch to the correct compose branch
            preserve_source = inputs.source_audio_policy == "preserve" and inputs.source_audio_available
            if inputs.subtitle_only_compose:
                self._compose_subtitle_only(ws, inputs)
            elif preserve_source and ws.bgm_path and ws.bgm_path.exists():
                self._compose_voice_source_audio_bgm(ws, inputs)
            elif preserve_source:
                self._compose_voice_source_audio(ws, inputs)
            elif ws.bgm_path and ws.bgm_path.exists():
                self._compose_voice_bgm(ws, inputs)
            else:
                self._compose_voice_only(ws, inputs)

            # Post-process: validate, probe, clamp, upload
            final_path, final_size, final_duration, clamp_warning = (
                self._validate_and_probe_output(task_id, ws, inputs)
            )
            if clamp_warning:
                ws.compose_warning = clamp_warning

            result = self._upload_and_verify(
                task_id,
                task,
                final_path,
                ws=ws,
                final_size=final_size,
                final_duration=final_duration,
                compose_started_at=compose_started_at,
                compose_policy=ws.compose_policy,
                freeze_tail_cap_sec=inputs.freeze_tail_cap_sec,
                compose_warning=ws.compose_warning,
                ffmpeg_cmd_used=ws.ffmpeg_cmd_used,
            )
            if isinstance(result, ComposeResult):
                return result
            updates = dict(result or {})
            final_key = str(
                updates.get("final_video_key")
                or updates.get("final_video_path")
                or deliver_key(task_id, "final.mp4")
            )
            return ComposeResult(
                updates=updates,
                final_key=final_key,
                final_url=task_endpoint(task_id, "final"),
                compose_status=str(updates.get("compose_status") or "done"),
            )

    def prepare_hot_follow_compose_task(
        self,
        task: dict,
        request: HotFollowComposeRequestContract,
    ) -> tuple[dict[str, Any], dict[str, Any], ComposePlan]:
        current = dict(task or {})
        request_updates: dict[str, Any] = {}
        if request.bgm_mix is not None:
            mix = max(0.0, min(1.0, float(request.bgm_mix)))
            config = dict(current.get("config") or {})
            bgm = dict(config.get("bgm") or {})
            bgm["mix_ratio"] = mix
            config["bgm"] = bgm
            current["config"] = config
            request_updates["config"] = config

        plan_patch: dict[str, Any] = {}
        if request.overlay_subtitles is not None:
            plan_patch["overlay_subtitles"] = bool(request.overlay_subtitles)
        if request.freeze_tail_enabled is not None:
            plan_patch["freeze_tail_enabled"] = bool(request.freeze_tail_enabled)
        if plan_patch:
            plan = dict(current.get("compose_plan") or {})
            if "target_lang" not in plan:
                plan["target_lang"] = current.get("target_lang") or current.get("content_lang") or "mm"
            if "freeze_tail_cap_sec" not in plan:
                plan["freeze_tail_cap_sec"] = 8
            plan.update(plan_patch)
            plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
            current["compose_plan"] = plan
            request_updates["compose_plan"] = plan
        compose_plan = self._build_compose_plan(current)
        return current, request_updates, compose_plan

    def _build_compose_plan(self, task: dict) -> ComposePlan:
        current_plan = dict(task.get("compose_plan") or {})
        freeze_tail_enabled = bool(current_plan.get("freeze_tail_enabled", False))
        return ComposePlan(
            mute=bool(current_plan.get("mute", True)),
            overlay_subtitles=bool(current_plan.get("overlay_subtitles", True)),
            strip_subtitle_streams=bool(current_plan.get("strip_subtitle_streams", True)),
            cleanup_mode=str(current_plan.get("cleanup_mode") or "none"),
            target_lang=str(
                current_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang") or "mm"
            ),
            freeze_tail_enabled=freeze_tail_enabled,
            freeze_tail_cap_sec=int(current_plan.get("freeze_tail_cap_sec") or 8),
            compose_policy="freeze_tail" if freeze_tail_enabled else "match_video",
        )

    @staticmethod
    def compose_lock_active(task: dict) -> bool:
        compose_lock_until = task.get("compose_lock_until")
        if not compose_lock_until:
            return False
        try:
            lock_dt = (
                datetime.fromisoformat(str(compose_lock_until))
                if isinstance(compose_lock_until, str)
                else compose_lock_until
            )
            if lock_dt.tzinfo is None:
                lock_dt = lock_dt.replace(tzinfo=timezone.utc)
            return lock_dt > datetime.now(timezone.utc)
        except Exception:
            return False

    @staticmethod
    def build_compose_running_updates(task: dict, compose_plan: ComposePlan) -> dict[str, Any]:
        return {
            "status": "processing",
            "last_step": "compose",
            "compose_status": "running",
            "compose_error": None,
            "compose_error_reason": None,
            "compose_last_status": "running",
            "compose_last_started_at": datetime.now(timezone.utc).isoformat(),
            "compose_last_finished_at": None,
            "compose_last_error": None,
            "compose_warning": None,
            "compose_plan": compose_plan.to_dict(),
            "scene_outputs": task.get("scene_outputs") or [],
        }

    @staticmethod
    def build_compose_lock_updates(task: dict) -> dict[str, Any]:
        return {
            "compose_status": "running",
            "compose_last_status": "running",
            "compose_last_started_at": task.get("compose_last_started_at")
            or datetime.now(timezone.utc).isoformat(),
            "compose_last_finished_at": None,
        }

    @staticmethod
    def build_compose_lock_body(task_id: str) -> dict[str, Any]:
        return {
            "error": "compose_in_progress",
            "status": "running",
            "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
            "task_id": task_id,
        }

    def resolve_fresh_final_key(
        self,
        task_id: str,
        task: dict,
        *,
        request: HotFollowComposeRequestContract,
        revision_snapshot: Callable[[dict], dict[str, str | None]],
        object_exists_fn: Callable[[str], bool] = object_exists,
        object_head_fn: Callable[[str], dict | None] = object_head,
        media_meta_from_head_fn: Callable[[dict | None], tuple[int, str | None]] = media_meta_from_head,
    ) -> str | None:
        final_key = (
            task_key(task, "final_video_key")
            or task_key(task, "final_video_path")
            or deliver_key(task_id, "final.mp4")
        )
        final_meta = object_head_fn(str(final_key)) if final_key else None
        final_size, _ = media_meta_from_head_fn(final_meta)
        final_physically_exists = bool(
            final_key and object_exists_fn(str(final_key)) and final_size >= MIN_VIDEO_BYTES
        )
        if not final_physically_exists or request.force:
            return None
        revision_for_freshness = revision_snapshot(task)
        if _current_final_is_fresh(
            task,
            revision=revision_for_freshness,
            final_exists=True,
            final_size=final_size,
        ):
            return str(final_key)
        return None

    @staticmethod
    def build_compose_failure_updates(detail: dict[str, Any]) -> dict[str, Any]:
        return {
            "compose_status": "failed",
            "compose_error": detail,
            "compose_error_reason": detail.get("reason"),
            "compose_last_status": "failed",
            "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
            "compose_last_error": detail.get("message"),
            "status": "failed",
            "last_step": "compose",
            "final_video_key": None,
            "final_video_path": None,
        }

    @staticmethod
    def merge_compose_warning(
        updates: dict[str, Any],
        lipsync_warning: str | None,
    ) -> dict[str, Any]:
        merged = dict(updates or {})
        if lipsync_warning:
            current_warning = str(merged.get("compose_warning") or "").strip()
            merged["compose_warning"] = (
                f"{current_warning} {lipsync_warning}".strip() if current_warning else lipsync_warning
            )
        return merged

    @staticmethod
    def build_hot_follow_compose_response(
        task_id: str,
        *,
        final_key: str,
        compose_status: str | None,
        hub: dict[str, Any],
        line: dict[str, Any] | None = None,
    ) -> HotFollowComposeResponseContract:
        return HotFollowComposeResponseContract(
            status_code=200,
            body={
                "task_id": task_id,
                "final_url": task_endpoint(task_id, "final"),
                "final_video_url": task_endpoint(task_id, "final"),
                "final_key": str(final_key or ""),
                "hub": hub,
                "line": dict(line or {}),
                "compose_status": compose_status,
            },
        )

    def validate_expected_revision(
        self,
        task: dict,
        request: HotFollowComposeRequestContract,
        *,
        revision_snapshot: Callable[[dict], dict[str, str | None]],
    ) -> None:
        revision = revision_snapshot(task)
        expected_subtitle_updated_at = str(request.expected_subtitle_updated_at or "").strip() or None
        expected_audio_sha256 = str(request.expected_audio_sha256 or "").strip() or None
        subtitle_mismatch = bool(
            expected_subtitle_updated_at and expected_subtitle_updated_at != revision.get("subtitle_updated_at")
        )
        audio_mismatch = bool(expected_audio_sha256 and expected_audio_sha256 != revision.get("audio_sha256"))
        if subtitle_mismatch or audio_mismatch:
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": "compose_revision_mismatch",
                    "message": "Current subtitles or audio changed; refresh workbench state before composing again.",
                    "current_revision": revision,
                },
            )

    # ── Phase 1: Validation ───────────────────────────────────────────────

    def _validate_inputs(
        self,
        task_id: str,
        task: dict,
        subtitle_only_check: Callable[[str, dict], bool],
    ) -> _ComposeInputs:
        live_task = _with_live_hot_follow_subtitle_currentness(task_id, task)
        voice_state = collect_voice_execution_state(live_task, self._settings)
        subtitle_only_compose = subtitle_only_check(task_id, live_task)

        # Resolve artifact keys
        source_audio_policy = source_audio_policy_from_task(live_task)
        video_key, video_has_source_audio = _resolve_compose_video_key(live_task, source_audio_policy)
        audio_key = _resolve_compose_voiceover_key(live_task, voice_state)

        if not video_key:
            compose_fail("missing_raw", "missing video source for compose")
        if not audio_key and not subtitle_only_compose:
            compose_fail("missing_voiceover", "missing voiceover audio for compose")
        if not bool(voice_state.get("audio_ready")) and not subtitle_only_compose:
            compose_fail(
                "missing_voiceover",
                f"voiceover audio not ready: {voice_state.get('audio_ready_reason') or 'audio_not_ready'}",
            )

        # Validate artifacts in storage
        try:
            assert_artifact_ready(kind="video", key=str(video_key), exists_fn=object_exists, head_fn=object_head)
        except Exception:
            compose_fail("missing_raw", "video source not ready")
        if audio_key and not subtitle_only_compose:
            try:
                assert_artifact_ready(kind="audio", key=str(audio_key), exists_fn=object_exists, head_fn=object_head)
            except Exception:
                compose_fail("missing_voiceover", "voiceover audio invalid")

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            compose_fail("compose_failed", "ffmpeg not found in PATH")

        # Extract compose plan config
        config = dict(live_task.get("config") or {})
        bgm = dict(config.get("bgm") or {})
        bgm_key: str | None = str(bgm.get("bgm_key") or "").strip() or None
        if bgm_key and not object_exists(bgm_key):
            bgm_key = None
        if bgm_key:
            try:
                assert_artifact_ready(kind="audio", key=bgm_key, exists_fn=object_exists, head_fn=object_head)
            except Exception:
                bgm_key = None
        try:
            bgm_mix = float(bgm.get("mix_ratio") if bgm.get("mix_ratio") is not None else 0.3)
        except Exception:
            bgm_mix = 0.3
        bgm_mix = max(0.0, min(1.0, bgm_mix))
        source_has_audio_hint = parse_pipeline_config(live_task.get("pipeline_config")).get("has_audio")
        source_audio_available = bool(
            video_has_source_audio
            and str(source_has_audio_hint or "").strip().lower() != "false"
        )

        compose_plan = dict(live_task.get("compose_plan") or {})
        overlay_subtitles = bool(compose_plan.get("overlay_subtitles"))
        strip_subtitle_streams = bool(compose_plan.get("strip_subtitle_streams", True))
        cleanup_mode = str(compose_plan.get("cleanup_mode") or "none").strip().lower()
        target_lang = str(
            compose_plan.get("target_lang") or live_task.get("target_lang") or live_task.get("content_lang") or "mm"
        )
        freeze_tail_enabled = bool(compose_plan.get("freeze_tail_enabled", False))
        try:
            freeze_tail_cap_sec = max(1.0, min(30.0, float(compose_plan.get("freeze_tail_cap_sec") or 8.0)))
        except Exception:
            freeze_tail_cap_sec = 8.0
        compose_policy = "freeze_tail" if freeze_tail_enabled else "match_video"

        logger.info(
            "COMPOSE_START",
            extra={
                "task_id": task_id,
                "raw_key": str(video_key),
                "audio_key": str(audio_key),
                "bgm_key": str(bgm_key) if bgm_key else None,
                "mix": bgm_mix,
                "source_audio_input_key": str(video_key) if source_audio_available else None,
                "source_audio_mix": _source_audio_bed_volume(bgm_mix) if source_audio_available else None,
                "video_has_source_audio": bool(video_has_source_audio),
                "source_audio_policy": source_audio_policy,
                "source_audio_available": source_audio_available,
                "overlay_subtitles": overlay_subtitles,
                "strip_subtitle_streams": strip_subtitle_streams,
                "target_lang": target_lang,
                "freeze_tail_enabled": freeze_tail_enabled,
                "freeze_tail_cap_sec": freeze_tail_cap_sec,
                "compose_policy": compose_policy,
            },
        )

        return _ComposeInputs(
            video_key=str(video_key),
            audio_key=str(audio_key) if audio_key else None,
            subtitle_only_compose=subtitle_only_compose,
            voice_state=voice_state,
            bgm_key=bgm_key,
            bgm_mix=bgm_mix,
            source_audio_policy=source_audio_policy,
            source_audio_available=source_audio_available,
            overlay_subtitles=overlay_subtitles,
            strip_subtitle_streams=strip_subtitle_streams,
            cleanup_mode=cleanup_mode,
            target_lang=target_lang,
            freeze_tail_enabled=freeze_tail_enabled,
            freeze_tail_cap_sec=freeze_tail_cap_sec,
            compose_policy=compose_policy,
            ffmpeg=str(ffmpeg),
        )

    # ── Phase 2: Workspace preparation ────────────────────────────────────

    def _prepare_workspace(
        self,
        task_id: str,
        task: dict,
        inputs: _ComposeInputs,
        tmp: Path,
        subtitle_resolver: Callable[[dict, str, str], str | None],
    ) -> _WorkspaceFiles:
        video_path = tmp / "video_input.mp4"
        voice_path = tmp / "voice_input.mp3"
        final_path = tmp / "final_compose.mp4"
        subtitle_path = tmp / "subs_target.srt"

        self._storage.download_file(inputs.video_key, str(video_path))
        if inputs.audio_key and not inputs.subtitle_only_compose:
            self._storage.download_file(inputs.audio_key, str(voice_path))

        video_size, video_duration = assert_local_video_ok(video_path)
        voice_duration = 0.0
        if inputs.audio_key and not inputs.subtitle_only_compose:
            try:
                _, voice_duration = assert_local_audio_ok(voice_path)
            except ValueError:
                compose_fail("missing_voiceover", "voiceover audio invalid")

        video_input_path = video_path
        compose_policy = inputs.compose_policy
        compose_warning: str | None = None

        # ── Freeze-tail ──
        hold_sec = 0.0
        if inputs.freeze_tail_enabled and voice_duration > video_duration:
            required_hold = max(0.0, voice_duration - video_duration)
            if required_hold <= inputs.freeze_tail_cap_sec:
                hold_sec = required_hold
            else:
                compose_policy = "match_video"
                compose_warning = (
                    f"freeze tail required {required_hold:.2f}s > cap {inputs.freeze_tail_cap_sec:.2f}s; "
                    "fallback to match_video"
                )
        else:
            compose_policy = "match_video" if not inputs.freeze_tail_enabled else compose_policy

        if hold_sec > 0:
            result_path = self._apply_freeze_tail(task_id, inputs.ffmpeg, video_path, tmp, hold_sec)
            if result_path:
                video_input_path = result_path
                try:
                    _, video_duration = assert_local_video_ok(result_path)
                except ValueError:
                    video_duration = video_duration + hold_sec
                compose_policy = "freeze_tail"
            else:
                compose_policy = "match_video"
                compose_warning = "freeze tail render failed; fallback to match_video"

        # ── Subtitle download & validation ──
        bundled_fonts_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
        bundled_myanmar_ttf = bundled_fonts_dir / "NotoSansMyanmar-Regular.ttf"
        overlay_subtitles = inputs.overlay_subtitles
        requested_overlay_subtitles = overlay_subtitles
        subtitle_key_used: str | None = None
        subtitle_object_etag: str | None = None
        subtitle_content_hash: str | None = None
        subtitle_sha256: str | None = None

        if overlay_subtitles:
            subtitle_key = subtitle_resolver(task, task_id, inputs.target_lang)
            if not subtitle_key:
                if inputs.subtitle_only_compose:
                    overlay_subtitles = False
                else:
                    compose_fail("subtitles_missing", "overlay_subtitles enabled but target subtitle key is missing")
            if overlay_subtitles and (not bundled_myanmar_ttf.exists() or bundled_myanmar_ttf.stat().st_size == 0):
                compose_fail("font_missing", f"bundled Myanmar font missing: {bundled_myanmar_ttf}")
            subtitle_key_used = str(subtitle_key) if subtitle_key else None
        if overlay_subtitles and subtitle_key_used:
            subtitle_meta = object_head(subtitle_key_used)
            subtitle_object_etag = (
                str(subtitle_meta.get("etag") or "").strip() or None
                if isinstance(subtitle_meta, dict)
                else None
            )
            self._storage.download_file(subtitle_key_used, str(subtitle_path))
            if not subtitle_path.exists() or subtitle_path.stat().st_size == 0:
                if inputs.subtitle_only_compose:
                    # Historical fix (267744a): no-speech task with empty subtitle —
                    # skip overlay, compose succeeds without burned-in text.
                    overlay_subtitles = False
                else:
                    compose_fail("subtitles_missing", "overlay_subtitles enabled but subtitle file is empty")
            if overlay_subtitles:
                subtitle_text = _read_text_compat(subtitle_path)
                subtitle_content_hash = _subtitle_content_hash(subtitle_text)
                subtitle_sha256 = sha256_file(subtitle_path)
                expected_subtitle_hash = str(task.get("subtitles_content_hash") or "").strip() or None
                logger.info(
                    "COMPOSE_SUBTITLE_BOUND",
                    extra={
                        "task_id": task_id,
                        "subtitle_key": subtitle_key_used,
                        "subtitle_etag": subtitle_object_etag,
                        "expected_subtitle_hash": expected_subtitle_hash,
                        "downloaded_subtitle_hash": subtitle_content_hash,
                    },
                )
                if expected_subtitle_hash and subtitle_content_hash and expected_subtitle_hash != subtitle_content_hash:
                    compose_fail(
                        "subtitle_revision_mismatch",
                        (
                            "downloaded authoritative subtitle does not match current saved subtitle "
                            f"(expected {expected_subtitle_hash}, got {subtitle_content_hash})"
                        ),
                    )
                normalized_layout_text = optimize_hot_follow_subtitle_layout_srt(
                    subtitle_text,
                    inputs.target_lang,
                )
                if normalized_layout_text and normalized_layout_text != subtitle_text:
                    subtitle_path.write_text(normalized_layout_text, encoding="utf-8")

        # ── BGM download ──
        bgm_path: Path | None = None
        if inputs.bgm_key:
            bgm_path = tmp / "bgm_input.mp3"
            self._storage.download_file(str(inputs.bgm_key), str(bgm_path))

        if requested_overlay_subtitles and not overlay_subtitles and not compose_warning:
            compose_warning = "subtitle_overlay_skipped_empty_no_dub"

        return _WorkspaceFiles(
            task_id=task_id,
            tmp=tmp,
            video_input_path=video_input_path,
            voice_path=voice_path if (inputs.audio_key and not inputs.subtitle_only_compose) else None,
            final_path=final_path,
            subtitle_path=subtitle_path if overlay_subtitles else None,
            bgm_path=bgm_path,
            fontsdir=bundled_fonts_dir,
            ffmpeg=inputs.ffmpeg,
            video_duration=video_duration,
            voice_duration=voice_duration,
            compose_policy=compose_policy,
            subtitle_key=subtitle_key_used,
            subtitle_object_etag=subtitle_object_etag,
            subtitle_content_hash=subtitle_content_hash,
            subtitle_sha256=subtitle_sha256,
            compose_warning=compose_warning,
            overlay_subtitles=overlay_subtitles,
        )

    def _apply_freeze_tail(
        self,
        task_id: str,
        ffmpeg: str,
        video_path: Path,
        tmp: Path,
        hold_sec: float,
    ) -> Path | None:
        """Apply tpad freeze-tail.  Returns new path on success, None on failure."""
        freeze_video_path = tmp / "video_input_freeze_tail.mp4"
        freeze_cmd = [
            ffmpeg, "-y", "-i", str(video_path),
            "-vf", f"tpad=stop_mode=clone:stop_duration={hold_sec:.3f}",
            "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p",
            str(freeze_video_path),
        ]
        try:
            proc = self._run_ffmpeg(freeze_cmd, task_id, "freeze_tail", timeout=self._timeouts.freeze_tail)
        except HTTPException:
            # Timeout or failure — caller will fallback to match_video
            return None
        if proc.returncode == 0 and freeze_video_path.exists() and freeze_video_path.stat().st_size > 0:
            return freeze_video_path
        return None

    # ── Phase 3: FFmpeg execution ─────────────────────────────────────────

    def _run_ffmpeg(
        self,
        cmd: list[str],
        task_id: str,
        purpose: str,
        *,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess:
        """Unified subprocess gateway with timeout protection."""
        effective_timeout = timeout or self._timeouts.compose
        logger.info(
            "COMPOSE_SUBPROCESS_START task=%s purpose=%s timeout=%d",
            task_id,
            purpose,
            effective_timeout,
        )
        binding = get_line_runtime_binding({"kind": "hot_follow"})
        line = binding.line
        request = WorkerRequest(
            request_id=f"{task_id}:{purpose}",
            line_id=str(getattr(line, "line_id", None) or "hot_follow_line"),
            task_id=task_id,
            step_id="compose",
            worker_capability="ffmpeg",
            execution_mode=WorkerExecutionMode.INTERNAL,
            worker_profile_ref=getattr(line, "worker_profile_ref", None),
            input_refs={"task_ref": task_id},
            strategy_hints={"purpose": purpose},
            runtime_config={"timeout_seconds": effective_timeout},
            payload={"cmd": list(cmd)},
        )
        result = get_worker_gateway().execute(request)
        if result.result == "timeout":
            stderr_tail = str((result.raw_output or {}).get("stderr") or "")[-800:]
            compose_fail(
                "compose_timeout",
                f"{purpose} timed out after {effective_timeout}s",
                ffmpeg_cmd=" ".join(cmd),
                stderr_tail=stderr_tail,
            )
        returncode = (result.output_facts or {}).get("returncode")
        if returncode is None:
            returncode = 1
        return subprocess.CompletedProcess(
            list(cmd),
            int(returncode),
            str((result.raw_output or {}).get("stdout") or ""),
            str((result.raw_output or {}).get("stderr") or ""),
        )

    # ── Filter expression helpers (ex-nested, now methods) ────────────────

    def _bgm_filter_expr(self, bgm_mix: float, compose_policy: str, video_duration: float) -> str:
        base = f"[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={bgm_mix}"
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base + "[bgm];"

    def _bgm_only_filter_expr(self, input_index: int, bgm_mix: float, compose_policy: str, video_duration: float) -> str:
        base = f"[{input_index}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={bgm_mix}"
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base + ",alimiter=limit=0.95[mix]"

    def _source_audio_filter_expr(self, source_audio_mix: float, compose_policy: str, video_duration: float) -> str:
        base = (
            "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume={_source_audio_bed_volume(source_audio_mix):.3f}"
        )
        if compose_policy == "match_video":
            base += f",apad,atrim=0:{video_duration:.3f}"
        return base

    def _voice_filter_expr(self, ws: _WorkspaceFiles) -> str:
        base = "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
        if ws.compose_policy != "match_video":
            return base
        if ws.voice_duration > ws.video_duration:
            return (
                base
                + f",atrim=0:{ws.video_duration:.3f}"
                + f",afade=t=out:st={max(ws.video_duration - 0.35, 0.0):.3f}:d=0.35"
            )
        return base + f",apad,atrim=0:{ws.video_duration:.3f}"

    @staticmethod
    def _assert_overlay_cmd(cmd_text: str, overlay_subtitles: bool) -> None:
        if overlay_subtitles and "subtitles=" not in cmd_text:
            compose_fail(
                "compose_failed",
                "overlay_subtitles enabled but ffmpeg cmd missing subtitles filter",
                ffmpeg_cmd=cmd_text,
            )

    # ── Compose branches ──────────────────────────────────────────────────

    def _compose_subtitle_only(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: subtitle-only compose (no voice audio)."""
        preserve_source = inputs.source_audio_policy == "preserve" and inputs.source_audio_available
        if preserve_source and ws.bgm_path and ws.bgm_path.exists():
            self._compose_subtitle_only_source_audio_bgm(ws, inputs)
        elif preserve_source:
            self._compose_subtitle_only_source_audio(ws, inputs)
        elif ws.bgm_path and ws.bgm_path.exists():
            self._compose_subtitle_only_with_bgm(ws, inputs)
        else:
            self._compose_subtitle_only_no_bgm(ws, inputs)

    def _compose_subtitle_only_source_audio(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + ",alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration) + ",alimiter=limit=0.95[mix]"
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_source_audio_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        bgm_filter = self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration).removesuffix(",alimiter=limit=0.95[mix]")
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[source][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[source][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_with_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration)
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = self._bgm_only_filter_expr(1, inputs.bgm_mix, ws.compose_policy, ws.video_duration)
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_subtitle_only_no_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-vf", subtitle_filter,
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "20", "-pix_fmt", "yuv420p",
                "-an",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
        else:
            cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-c:v", "copy",
                "-an",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + BGM compose."""
        voice_filter = self._voice_filter_expr(ws)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + (voice_filter + "[voice];")
                + self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                (voice_filter + "[voice];")
                + self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
                + "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_source_audio(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + preserved source audio bed."""
        voice_filter = self._voice_filter_expr(ws)
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + "[voice][source]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + "[voice][source]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_source_audio_bgm(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice + preserved source audio bed + uploaded BGM."""
        voice_filter = self._voice_filter_expr(ws)
        source_filter = self._source_audio_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration)
        bgm_filter = self._bgm_filter_expr(inputs.bgm_mix, ws.compose_policy, ws.video_duration).removesuffix("[bgm];")
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[voice][source][bgm]amix=inputs=3:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = (
                voice_filter
                + "[voice];"
                + source_filter
                + "[source];"
                + bgm_filter
                + "[bgm];"
                + "[voice][source][bgm]amix=inputs=3:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
            )
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]
        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-i", str(ws.bgm_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        self._execute_compose_cmd(cmd, ws, inputs)

    def _compose_voice_only(self, ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Branch: voice without BGM.  Includes CRF23 fallback retry."""
        voice_filter = self._voice_filter_expr(ws)
        if ws.overlay_subtitles:
            subtitle_filter = compose_subtitle_vf(ws.subtitle_path, ws.fontsdir, inputs.cleanup_mode, inputs.target_lang)
            filter_complex = (
                f"[0:v]{subtitle_filter}[v];"
                + (voice_filter + ",alimiter=limit=0.95[mix]")
            )
            map_video = "[v]"
            video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        else:
            filter_complex = voice_filter + ",alimiter=limit=0.95[mix]"
            map_video = "0:v:0"
            video_codec_args = ["-c:v", "copy"]

        cmd = [
            ws.ffmpeg, "-y",
            "-i", str(ws.video_input_path),
            "-i", str(ws.voice_path),
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", "[mix]",
            *video_codec_args,
            "-c:a", "aac",
            "-movflags", "+faststart",
            *(["-sn"] if inputs.strip_subtitle_streams else []),
            str(ws.final_path),
        ]
        logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd))
        ws.ffmpeg_cmd_used = " ".join(cmd)
        self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
        proc = self._run_ffmpeg(cmd, ws.task_id, "compose_voice_only")

        if proc.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
            # Fallback: retry with CRF 23
            cmd_fallback = [
                ws.ffmpeg, "-y",
                "-i", str(ws.video_input_path),
                "-i", str(ws.voice_path),
                "-filter_complex", filter_complex,
                "-map", map_video,
                "-map", "[mix]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac",
                "-movflags", "+faststart",
                *(["-sn"] if inputs.strip_subtitle_streams else []),
                str(ws.final_path),
            ]
            logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd_fallback))
            ws.ffmpeg_cmd_used = " ".join(cmd_fallback)
            self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
            proc2 = self._run_ffmpeg(cmd_fallback, ws.task_id, "compose_voice_only_fallback")
            if proc2.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
                compose_fail(
                    "compose_failed",
                    "compose ffmpeg failed",
                    ffmpeg_cmd=ws.ffmpeg_cmd_used,
                    stderr_tail=(proc2.stderr or "")[-800:],
                )

    def _execute_compose_cmd(self, cmd: list[str], ws: _WorkspaceFiles, inputs: _ComposeInputs) -> None:
        """Log, assert, run, and check a compose command (shared by non-fallback branches)."""
        logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", ws.task_id, " ".join(cmd))
        ws.ffmpeg_cmd_used = " ".join(cmd)
        self._assert_overlay_cmd(ws.ffmpeg_cmd_used, ws.overlay_subtitles)
        proc = self._run_ffmpeg(cmd, ws.task_id, "compose")
        if proc.returncode != 0 or not ws.final_path.exists() or ws.final_path.stat().st_size == 0:
            compose_fail(
                "compose_failed",
                "compose ffmpeg failed",
                ffmpeg_cmd=ws.ffmpeg_cmd_used,
                stderr_tail=(proc.stderr or "")[-800:],
            )

    # ── Phase 4: Post-process ─────────────────────────────────────────────

    def _validate_and_probe_output(
        self,
        task_id: str,
        ws: _WorkspaceFiles,
        inputs: _ComposeInputs,
    ) -> tuple[Path, int, float, str | None]:
        """Validate output, probe duration, clamp if needed.  Returns (path, size, duration, warning)."""
        try:
            final_size, final_duration = assert_local_video_ok(ws.final_path)
        except ValueError:
            compose_fail("compose_failed", "compose output invalid")
            # compose_fail always raises; this is unreachable but helps type checker
            raise  # pragma: no cover

        # Probe with ffprobe for more accurate duration
        ffprobe = shutil.which("ffprobe")
        if ffprobe:
            probe_cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(ws.final_path),
            ]
            try:
                probe = self._run_ffmpeg(probe_cmd, task_id, "probe_duration", timeout=self._timeouts.probe)
                if probe.returncode == 0:
                    try:
                        final_duration = float((probe.stdout or "").strip() or final_duration)
                    except Exception:
                        pass
            except HTTPException:
                # Probe timeout — non-fatal, use duration from assert_local_video_ok
                pass

        # Duration mismatch clamping
        clamp_warning: str | None = None
        final_path = ws.final_path
        if ws.compose_policy == "match_video" and abs(float(final_duration) - float(ws.video_duration)) > 1.0:
            logger.warning(
                "COMPOSE_DURATION_MISMATCH",
                extra={
                    "task_id": task_id,
                    "source_duration": ws.video_duration,
                    "final_duration": final_duration,
                },
            )
            clamp_path = ws.tmp / "final_compose_clamped.mp4"
            clamp_cmd = [
                ws.ffmpeg, "-y",
                "-i", str(ws.final_path),
                "-t", f"{ws.video_duration:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac",
                "-movflags", "+faststart",
                str(clamp_path),
            ]
            try:
                clamp_proc = self._run_ffmpeg(clamp_cmd, task_id, "duration_clamp", timeout=self._timeouts.clamp)
                if clamp_proc.returncode == 0 and clamp_path.exists() and clamp_path.stat().st_size > 0:
                    final_path = clamp_path
                    final_size, final_duration = assert_local_video_ok(final_path)
                    clamp_warning = "Duration mismatch detected; output was clamped to source duration."
            except HTTPException:
                # Clamp timeout — non-fatal, keep unclamped version
                clamp_warning = "Duration mismatch detected; clamp timed out, keeping original output."

        logger.info(
            "COMPOSE_OUTPUT_READY",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "output_path": str(final_path),
            },
        )
        return final_path, final_size, final_duration, clamp_warning

    def _upload_and_verify(
        self,
        task_id: str,
        task: dict,
        final_path: Path,
        *,
        ws: _WorkspaceFiles,
        final_size: int,
        final_duration: float,
        compose_started_at: str,
        compose_policy: str,
        freeze_tail_cap_sec: float,
        compose_warning: str | None,
        ffmpeg_cmd_used: str | None,
    ) -> ComposeResult:
        """Upload final video, verify, and build the structured compose result."""
        final_key = deliver_key(task_id, "final.mp4")
        logger.info(
            "COMPOSE_UPLOAD_START",
            extra={"task_id": task_id, "final_key": final_key, "content_type": "video/mp4"},
        )
        uploaded_key = self._storage.upload_file(str(final_path), final_key, content_type="video/mp4")
        if not uploaded_key:
            compose_fail("compose_failed", "compose upload failed")
        if not object_exists(final_key):
            compose_fail("compose_failed", "compose upload verify failed: missing final object")
        uploaded_meta = object_head(final_key)
        uploaded_size, _ = media_meta_from_head(uploaded_meta)
        final_etag = uploaded_meta.get("etag") if isinstance(uploaded_meta, dict) else None
        if uploaded_size < MIN_VIDEO_BYTES:
            compose_fail("compose_failed", "compose upload verify failed: invalid final object")

        logger.info(
            "COMPOSE_DONE",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "uploaded_key": final_key,
                "uploaded_size": uploaded_size,
            },
        )

        compose_finished_at = datetime.now(timezone.utc).isoformat()
        updates = {
            "final_video_key": final_key,
            "final_video_path": final_key,
            "final_video_sha256": sha256_file(final_path),
            "final_asset_version": str(final_etag or sha256_file(final_path) or compose_finished_at),
            "final_updated_at": compose_finished_at,
            "final_mime": "video/mp4",
            "final_duration_ms": int(final_duration * 1000),
            "final_video_bytes": int(uploaded_size),
            # Compose snapshot: record which inputs were baked into this final.
            # Used by _current_final_is_fresh() and compute_final_staleness() to
            # detect when subtitle or audio changed after the last compose ran.
            "final_source_audio_sha256": str(task.get("audio_sha256") or "").strip() or None,
            "final_source_dub_generated_at": str(task.get("dub_generated_at") or "").strip() or None,
            "final_source_audio_policy": source_audio_policy_from_task(task),
            "final_source_subtitles_content_hash": ws.subtitle_content_hash
            or str(task.get("subtitles_content_hash") or "").strip()
            or None,
            "final_source_subtitle_updated_at": str(task.get("subtitles_override_updated_at") or "").strip() or None,
            "final_source_subtitle_storage_key": ws.subtitle_key,
            "final_source_subtitle_storage_etag": ws.subtitle_object_etag,
            "final_source_subtitle_sha256": ws.subtitle_sha256,
            "final_source_render_signature": subtitle_render_signature(
                target_lang=(task.get("compose_plan") or {}).get("target_lang")
                or task.get("target_lang")
                or task.get("content_lang"),
                cleanup_mode=(task.get("compose_plan") or {}).get("cleanup_mode"),
            ),
            "compose_provider": "ffmpeg",
            "compose_version": int(task.get("compose_version") or 0) + 1,
            "compose_status": "done",
            "compose_error": None,
            "compose_error_reason": None,
            "compose_last_status": "done",
            "compose_last_started_at": compose_started_at,
            "compose_last_finished_at": compose_finished_at,
            "compose_last_ffmpeg_cmd": ffmpeg_cmd_used,
            "compose_last_error": None,
            "compose_policy": compose_policy,
            "freeze_tail_enabled": bool(compose_policy == "freeze_tail"),
            "freeze_tail_cap_sec": int(freeze_tail_cap_sec),
            "compose_warning": compose_warning,
            "last_step": "compose",
            "status": "ready",
            "error_message": None,
            "error_reason": None,
        }
        return ComposeResult(
            updates=updates,
            final_key=final_key,
            final_url=task_endpoint(task_id, "final"),
            compose_status=str(updates.get("compose_status") or "done"),
        )
